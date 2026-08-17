## MODIFIED Requirements

### Requirement: Copilot review-gate workflow template
id: gate-workflow-template
base: 67c05ef83e3c

The plugin SHALL carry a Copilot review-gate workflow template at
`integrations/copilot/copilot-review-gate.yml` containing: the ownership
marker line `# shipd-copilot v{version}` with the literal `{version}`
placeholder; triggers on `pull_request` (types `opened`, `synchronize`,
`reopened`) and `pull_request_review` (type `submitted`); a `permissions`
block granting `statuses: write`, `pull-requests: write`, and
`contents: read`; and a `concurrency` group keyed on the pull request
number with `cancel-in-progress: true`. When a `pull_request` event fires,
the workflow SHALL post the commit status context `semantic-review` with
state `pending` on the pull request's head SHA and then branch on the
`COPILOT_GITHUB_TOKEN` secret. Where the secret is non-empty, the workflow
SHALL run the review itself: check out the pull request head with full
history, install difftastic and ripgrep, install the `@github/copilot`
CLI, and run it non-interactively under a bounded timeout with the secret
as its `COPILOT_GITHUB_TOKEN` — the prompt SHALL name the installed
`.github/skills/code-review/SKILL.md` as the instructions to follow, name
the base and head to diff, forbid the CLI from posting anything itself,
and require the verdict marker as the output's last line — capturing the
output to a workspace file, classifying it as below, posting the resulting
status, and posting the review text as a pull-request comment; if the CLI
run exits nonzero or times out, the workflow SHALL post no further status
so `pending` stands. Where the secret is empty, the workflow SHALL poll
the pull request's reviews through the GitHub REST API every 20 seconds
for up to 15 minutes for the newest review authored by
`copilot-pull-request-reviewer[bot]` whose `commit_id` equals the
triggering head SHA — classifying that review's body when found, exiting
without a further status post on timeout, and exiting without a further
status post when the pull request's current head no longer equals the
triggering head. When a `pull_request_review` event fires, the workflow
SHALL act only if the review author's login is
`copilot-pull-request-reviewer[bot]` and the review's `commit_id` equals
the pull request's current head SHA, classifying that review's body.
Classification SHALL be by the text's **last non-empty line** — extracted
with pure-bash parameter expansion using a bounded windowed trailing trim
(never by piping the text into an external matcher), with carriage returns
and surrounding whitespace tolerated — compared for equality against the
markers: `<!-- shipd-verdict: fix-required -->` posts state `failure`;
`<!-- shipd-verdict: ship-it -->` posts state `success`; any other last
line posts state `success` with a description stating that no verdict was
parsed. On the polling and CLI paths the classified text SHALL reach the
classifier through a workspace file read with bash redirection, never
through an environment variable. The workflow SHALL reference no secret
other than the workflow's own `github.token` and the optional
`COPILOT_GITHUB_TOKEN`, SHALL pass `COPILOT_GITHUB_TOKEN` only to the
Copilot CLI and never to `gh`, and SHALL NOT request Copilot as a
reviewer.

#### Scenario: Template carries the marker, triggers, permissions, and concurrency
- **WHEN** `plugins/s/integrations/copilot/copilot-review-gate.yml` is read
- **THEN** it contains the marker line `# shipd-copilot v{version}`, both
  triggers, a `permissions` block granting `statuses: write`,
  `pull-requests: write`, and `contents: read`, and the per-PR
  `concurrency` group with `cancel-in-progress: true`

#### Scenario: A configured secret selects the CLI reviewer path
- **WHEN** the `pull_request` path runs with a non-empty
  `COPILOT_GITHUB_TOKEN` and the CLI writes a review ending in a marker
- **THEN** `pending` posts first, the CLI is invoked non-interactively
  under a timeout with the SKILL.md named in its prompt, the marker
  classifies the output, the matching terminal status posts on the head
  SHA, and the review text is posted as a pull-request comment

#### Scenario: A failed or timed-out CLI run leaves pending
- **WHEN** the CLI path's run exits nonzero or exceeds its timeout
- **THEN** no terminal status is posted and the `pending` status stands

#### Scenario: An absent secret falls back to the poll path
- **WHEN** the `pull_request` path runs with an empty
  `COPILOT_GITHUB_TOKEN` and the reviews API returns a Copilot review of
  the triggering head within the window
- **THEN** the poll classifies that review into a terminal status exactly
  as before, and the timed-out and superseded-head cases exit quietly
  leaving `pending`

#### Scenario: The review-event path still guards reviewer and head commit
- **WHEN** a `pull_request_review` event fires
- **THEN** the workflow classifies only when the review author login is
  `copilot-pull-request-reviewer[bot]` and the review `commit_id` equals
  the pull request's current head SHA

#### Scenario: Classification is anchored last-line equality on every path
- **WHEN** a classified text's last non-empty line equals a marker, or
  equals neither
- **THEN** `fix-required` maps to `failure`, `ship-it` maps to `success`,
  and any other last line — markers quoted mid-text, an empty text — maps
  to `success` with a description stating that no verdict was parsed

#### Scenario: The classified text is never piped nor env-passed
- **WHEN** the gate job's script is read
- **THEN** the CLI output and the polled review body land in workspace
  files read back with bash redirection, the extraction and comparisons
  are pure-bash parameter expansion and `[[ ]]` tests with the bounded
  windowed trim, and no non-comment line referencing that text contains a
  pipe into a matcher

#### Scenario: Exactly one optional secret, scoped to the CLI
- **WHEN** the template is read
- **THEN** the only secret references are the workflow's own
  `github.token` and `${{ secrets.COPILOT_GITHUB_TOKEN }}`, the latter
  reaching only the Copilot CLI's environment and never a `gh` call, and
  no step requests Copilot as a reviewer

### Requirement: Copilot review skill template
id: skill-template
base: 7d2e317ddb67

The plugin SHALL carry a Copilot code-review skill template at
`integrations/copilot/SKILL.md` containing: YAML frontmatter with `name` and
`description` fields; the ownership marker line `<!-- shipd-copilot
v{version} -->` with the literal `{version}` placeholder; instructions that
direct the reviewing agent to run the bundled engine
(`python3 .github/skills/code-review/scripts/semdiff.py`) with its `files`,
`diff`, and `context` subcommands and to reason from that structural JSON
rather than raw file dumps; the severity rubric (`high`/`medium`/`low`) with
the ship-it/fix-required verdict rule (any high or medium finding blocks);
an instruction that the review body ends with a visible verdict line plus
the matching machine-readable marker — `<!-- shipd-verdict: ship-it -->` or
`<!-- shipd-verdict: fix-required -->` — on its own line as the body's last
line, stating that the marker is read from the last non-empty line by
exact equality (never by a substring match elsewhere in the body); a
statement that the skill is the review contract for both surfaces that
consume it — GitHub's Copilot code-review runs and the gate workflow's
headless Copilot CLI reviewer; a statement that the engine is read-only
and degrades to its text engine when `difft` is unavailable; and
documentation that the Copilot code-review surface exposes no
repository-side model selection and that, where the repository's
`copilot-review-gate.yml` workflow is installed, the verdict marker drives
the required `semantic-review` commit status — a review without a marker
passes fail-open — while the review stays advisory where no gate workflow
is installed.

#### Scenario: Template exists with the placeholder marker
- **WHEN** `plugins/s/integrations/copilot/SKILL.md` is read
- **THEN** it contains the literal line `<!-- shipd-copilot v{version} -->`
  and frontmatter `name` and `description` fields

#### Scenario: Template directs the agent to the bundled engine
- **WHEN** the template body is read
- **THEN** it names the `files`, `diff`, and `context` subcommands of the
  bundled `semdiff.py`, the high/medium/low rubric, and the no-model-pin
  documentation

#### Scenario: The marker instruction states last-line equality
- **WHEN** the template's report instructions are read
- **THEN** they require exactly one marker as the body's last line and
  state it is read from the last non-empty line by exact equality, with no
  claim of a substring match anywhere in the body

#### Scenario: The skill names both consuming surfaces
- **WHEN** the template body is read
- **THEN** it states the skill is the contract for GitHub's Copilot
  code-review runs and for the gate workflow's headless Copilot CLI
  reviewer
