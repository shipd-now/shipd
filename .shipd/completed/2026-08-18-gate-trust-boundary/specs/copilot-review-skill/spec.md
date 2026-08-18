## MODIFIED Requirements

### Requirement: Copilot review-gate workflow template
id: gate-workflow-template
base: ad36ef2ea0ae

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
CLI **pinned to an exact version**, materialize the reviewer instructions
from the **base ref's** installed skill file into a workspace file —
falling back to the head's copy, with a log line saying so, only when the
file is confirmed absent at the base ref; any other materialization
failure SHALL fail the reviewer step so `pending` stands — and run the CLI non-interactively under a
bounded timeout **in a dedicated step whose environment binds the secret
as `COPILOT_GITHUB_TOKEN` and no other credential: the workflow's own
`github.token` SHALL NOT be present in the CLI step's environment**. The
prompt SHALL name the materialized instructions file, name the base and
head to diff, forbid the CLI from posting anything itself, and require
the verdict marker as the output's last line, capturing stdout to a
workspace file. A **separate** step whose environment binds
`github.token` and not the secret SHALL classify the captured output as
below, post the resulting status, and post the review text as a
pull-request comment; that step SHALL be insulated from manipulation by
the CLI step — it SHALL invoke `gh` by absolute path (immune to a
`GITHUB_PATH` shim) and SHALL bind `SHIPD_GATE_FAIL_OPEN` in its own
step-level environment from the `vars` context (immune to a `GITHUB_ENV`
write) — the comment posting whenever CLI output was
captured, including a strict-mode marker-less outcome that posts no
status; if the CLI run exits nonzero or times out, no further status
posts so `pending` stands. Where the secret is empty, the workflow SHALL
poll the pull request's reviews through the GitHub REST API every 20
seconds for up to 15 minutes for the newest review authored by
`copilot-pull-request-reviewer[bot]` whose `commit_id` equals the
triggering head SHA — classifying that review's body when found, exiting
without a further status post on timeout, and exiting without a further
status post when the pull request's current head no longer equals the
triggering head. When a `pull_request_review` event fires, the workflow
SHALL act only if the review author's login is
`copilot-pull-request-reviewer[bot]` and the review's `commit_id` equals
the pull request's current head SHA, classifying that review's body.
Classification SHALL be by the text's last non-empty line — extracted
with pure-bash parameter expansion using a bounded windowed trailing trim
(never by piping the text into an external matcher), with carriage
returns and surrounding whitespace tolerated — compared for equality
against the markers: `<!-- shipd-verdict: fix-required -->` posts state
`failure`; `<!-- shipd-verdict: ship-it -->` posts state `success`; for
any other last line the outcome SHALL follow the repository Actions
variable `SHIPD_GATE_FAIL_OPEN`, read into the job's environment — unset
or any value other than `false` posts state `success` with a description
stating that no verdict marker was parsed, **worded on the CLI path to
name the CLI review as the source**, while `false` logs the condition and
posts no further status so `pending` stands, on every classify path. On
the polling and CLI paths the classified text SHALL reach the classifier
through a workspace file read with bash redirection, never through an
environment variable. The workflow SHALL reference no secret other than
the workflow's own `github.token` and the optional
`COPILOT_GITHUB_TOKEN`, SHALL pass `COPILOT_GITHUB_TOKEN` only to the
Copilot CLI step and never to `gh`, and SHALL NOT request Copilot as a
reviewer.

#### Scenario: Template carries the marker, triggers, permissions, and concurrency
- **WHEN** `plugins/s/integrations/copilot/copilot-review-gate.yml` is read
- **THEN** it contains the marker line `# shipd-copilot v{version}`, both
  triggers, the `statuses: write` / `pull-requests: write` /
  `contents: read` permissions, and the per-PR `concurrency` group with
  `cancel-in-progress: true`

#### Scenario: The CLI step's environment is credential-isolated
- **WHEN** the template's steps are read
- **THEN** the step invoking `copilot` binds `COPILOT_GITHUB_TOKEN` and
  no `GH_TOKEN`/`github.token`, while the step that classifies and posts
  binds `github.token` and not the secret, invokes `gh` by absolute path,
  and re-binds `SHIPD_GATE_FAIL_OPEN` in its own step environment from
  the `vars` context, with the output travelling between the steps as a
  workspace file

#### Scenario: Reviewer instructions come from the base ref
- **WHEN** the CLI path prepares its prompt
- **THEN** the instructions file is materialized from the base ref's
  installed skill and the prompt names that file; only when the file is
  confirmed absent at the base ref is the head's copy used, with a log
  line saying so, and any other materialization failure fails the
  reviewer step leaving `pending`

#### Scenario: The CLI install is pinned
- **WHEN** the CLI provisioning step is read
- **THEN** `@github/copilot` is installed at an exact pinned version,
  never a floating tag

#### Scenario: The CLI fail-open description names its source
- **WHEN** the CLI path classifies a marker-less output with the knob
  unset
- **THEN** the posted `success` description names the CLI review as what
  produced no verdict marker, while the poll and review-event paths keep
  their existing wording

#### Scenario: Strict mode, marker verdicts, and the other paths are unchanged
- **WHEN** the paths run with marker-carrying inputs, with strict mode's
  marker-less case, and with the poll and review-event flows
- **THEN** behavior matches the pre-change contract: strict marker-less
  outcomes post no status but the CLI path still posts its comment,
  `fix-required`/`ship-it` post `failure`/`success` everywhere,
  pending-first on pull-request events, quiet poll timeout and moved-head
  exits, and the bridge's reviewer/head guards

#### Scenario: The classified text is never piped nor env-passed
- **WHEN** the gate job's script is read
- **THEN** the CLI output and the polled review body land in workspace
  files read back with bash redirection, the extraction and comparisons
  are pure-bash parameter expansion and `[[ ]]` tests with the bounded
  windowed trim, and no non-comment line referencing that text contains a
  pipe into a matcher

#### Scenario: Exactly one optional secret, scoped to the CLI step
- **WHEN** the template is read
- **THEN** the only secret references are the workflow's own
  `github.token` and `${{ secrets.COPILOT_GITHUB_TOKEN }}`, the latter
  bound only in the CLI step's environment (plus the job-level
  presence-only boolean), and no step requests Copilot as a reviewer

### Requirement: Copilot review skill template
id: skill-template
base: c713f602cbc6

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
the required `semantic-review` commit status under the repository's
`SHIPD_GATE_FAIL_OPEN` setting — a review without a marker passes
fail-open by default, while `false` leaves the status pending — and the
review stays advisory where no gate workflow is installed.

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

#### Scenario: The gate bullet names the strictness knob
- **WHEN** the template's scope section is read
- **THEN** the merge-gate statement names `SHIPD_GATE_FAIL_OPEN`, the
  fail-open default for marker-less reviews, and that `false` leaves the
  status pending

#### Scenario: The skill names both consuming surfaces
- **WHEN** the template body is read
- **THEN** it states the skill is the contract for GitHub's Copilot
  code-review runs and for the gate workflow's headless Copilot CLI
  reviewer
