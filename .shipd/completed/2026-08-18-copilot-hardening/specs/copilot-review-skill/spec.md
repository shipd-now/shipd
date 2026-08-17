## MODIFIED Requirements

### Requirement: Copilot review-gate workflow template
id: gate-workflow-template
base: 461cac333607

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
skill file as the instructions to follow, name the base and head to diff,
forbid the CLI from posting anything itself, and require the verdict
marker as the output's last line — capturing the output to a workspace
file, classifying it as below, posting the resulting status, and posting
the review text as a pull-request comment — the comment SHALL post
whenever CLI output was captured, including a strict-mode marker-less
outcome that posts no status; if the CLI run exits nonzero or times out,
the workflow SHALL post no further status so `pending` stands.
Where the secret is empty, the workflow SHALL poll the pull request's
reviews through the GitHub REST API every 20 seconds for up to 15 minutes
for the newest review authored by `copilot-pull-request-reviewer[bot]`
whose `commit_id` equals the triggering head SHA — classifying that
review's body when found, exiting without a further status post on
timeout, and exiting without a further status post when the pull request's
current head no longer equals the triggering head. When a
`pull_request_review` event fires, the workflow SHALL act only if the
review author's login is `copilot-pull-request-reviewer[bot]` and the
review's `commit_id` equals the pull request's current head SHA,
classifying that review's body. Classification SHALL be by the text's
**last non-empty line** — extracted with pure-bash parameter expansion
using a bounded windowed trailing trim (never by piping the text into an
external matcher), with carriage returns and surrounding whitespace
tolerated — compared for equality against the markers:
`<!-- shipd-verdict: fix-required -->` posts state `failure`;
`<!-- shipd-verdict: ship-it -->` posts state `success`; for any other
last line the outcome SHALL follow the repository Actions variable
`SHIPD_GATE_FAIL_OPEN`, read into the job's environment — unset or any
value other than `false` posts state `success` with a description stating
that no verdict was parsed, while `false` logs that no verdict was parsed
and exits without a further status post so `pending` stands, on every
classify path. On the polling and CLI paths the classified text SHALL
reach the classifier through a workspace file read with bash redirection,
never through an environment variable. The workflow SHALL reference no
secret other than the workflow's own `github.token` and the optional
`COPILOT_GITHUB_TOKEN`, SHALL pass `COPILOT_GITHUB_TOKEN` only to the
Copilot CLI and never to `gh`, and SHALL NOT request Copilot as a
reviewer.

#### Scenario: Template carries the marker, triggers, permissions, and concurrency
- **WHEN** `plugins/s/integrations/copilot/copilot-review-gate.yml` is read
- **THEN** it contains the marker line `# shipd-copilot v{version}`, both
  triggers, the `statuses: write` / `pull-requests: write` /
  `contents: read` permissions, and the per-PR `concurrency` group with
  `cancel-in-progress: true`

#### Scenario: The default keeps fail-open on every path
- **WHEN** a classified text's last non-empty line equals neither marker
  and `SHIPD_GATE_FAIL_OPEN` is unset
- **THEN** state `success` posts with a description stating that no
  verdict was parsed, on the CLI, poll, and review-event paths alike

#### Scenario: Strict mode leaves pending on a marker-less outcome
- **WHEN** a classified text's last non-empty line equals neither marker
  and the `SHIPD_GATE_FAIL_OPEN` variable is `false`
- **THEN** no further status posts on any classify path — the `pending`
  status stands — the run logs that no verdict was parsed and exits zero,
  and on the CLI path the captured review text is still posted as the
  pull-request comment so an operator can read what the reviewer wrote

#### Scenario: Strict mode never blocks a real verdict
- **WHEN** `SHIPD_GATE_FAIL_OPEN` is `false` and the last non-empty line
  equals a marker
- **THEN** `fix-required` still posts `failure` and `ship-it` still posts
  `success`

#### Scenario: CLI, poll, and bridge mechanics are unchanged
- **WHEN** the secret-selected CLI path, the no-secret poll path, and the
  review-event bridge run with marker-carrying inputs
- **THEN** their behavior is exactly the pre-knob contract: pending first
  on pull-request events, bounded CLI run with the comment post,
  newest-matching-review polling with quiet timeout and moved-head exits,
  and the reviewer/head guards on the bridge

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

### Requirement: Copilot review setup workflow template
id: setup-workflow-template
base: f6cfd9ded738

The plugin SHALL carry a Copilot code-review environment workflow template
at `integrations/copilot/copilot-code-review.yml` containing: the
ownership marker line `# shipd-copilot v{version}` with the literal
`{version}` placeholder; a single job named `copilot-setup-steps` running
on `ubuntu-latest`; a repository checkout step that is marked
`continue-on-error: true` and carries a step `id`, so a checkout the
runner's token cannot perform (a private repository) never fails the
setup job; and steps that install the prebuilt `difft` release binary
onto the runner's `PATH` (the same release-tarball source `semdiff.py`'s
own installer uses) and install `ripgrep`, each conditioned on the
checkout step's outcome being `success`. If the extracted release archive
contains no `difft` binary, then the difftastic step SHALL fail with a
message naming the problem rather than invoking `install` with an empty
path. The template SHALL NOT reference any secret or
organization-specific value.

#### Scenario: Workflow defines the setup job
- **WHEN** `plugins/s/integrations/copilot/copilot-code-review.yml` is read
- **THEN** it contains the marker line `# shipd-copilot v{version}` and
  exactly one job, named `copilot-setup-steps`, on `ubuntu-latest`

#### Scenario: The checkout is fail-soft and gates the installs
- **WHEN** the template's steps are read
- **THEN** the checkout step carries `continue-on-error: true` and an
  `id`, and the difftastic and ripgrep steps each run only when that
  step's outcome is `success`

#### Scenario: A binary-less archive fails loudly
- **WHEN** the difftastic step's script is read
- **THEN** it tests the located binary path for emptiness and fails with
  a clear message when the archive held no `difft`, never invoking
  `install` with an empty path

#### Scenario: Workflow provisions the diff tooling
- **WHEN** the template's steps are read
- **THEN** one step installs the `difft` release binary onto `PATH` and one
  installs `ripgrep`
