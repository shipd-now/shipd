## MODIFIED Requirements

### Requirement: Copilot review-gate workflow template
id: gate-workflow-template
base: c6f9ba58be71

The plugin SHALL carry a Copilot review-gate workflow template at
`integrations/copilot/copilot-review-gate.yml` containing: the ownership
marker line `# shipd-copilot v{version}` with the literal `{version}`
placeholder; triggers on `pull_request` (types `opened`, `synchronize`,
`reopened`) and `pull_request_review` (type `submitted`); a `permissions`
block granting `statuses: write` and `pull-requests: read`; and a
`concurrency` group keyed on the pull request number with
`cancel-in-progress: true`. When a `pull_request` event fires, the workflow
SHALL post the commit status context `semantic-review` with state `pending`
on the pull request's head SHA and then poll the pull request's reviews
through the GitHub REST API every 20 seconds for up to 15 minutes for the
newest review authored by `copilot-pull-request-reviewer[bot]` whose
`commit_id` equals the triggering head SHA — classifying that review's body
when found, exiting without a further status post when the poll times out,
and exiting without a further status post when the pull request's current
head no longer equals the triggering head. When a `pull_request_review`
event fires, the workflow SHALL act only if the review author's login is
`copilot-pull-request-reviewer[bot]` and the review's `commit_id` equals
the pull request's current head SHA, classifying that review's body.
Classification SHALL be by the body's **last non-empty line** — extracted
with pure-bash parameter expansion using a bounded windowed trailing trim
(never by piping the body into an external matcher), with carriage returns
and surrounding whitespace tolerated — compared for equality against the
markers: a last line equal to `<!-- shipd-verdict: fix-required -->` posts
state `failure`; a last line equal to `<!-- shipd-verdict: ship-it -->`
posts state `success`; any other last line posts state `success` with a
description stating that no verdict was parsed. On the polling path the
body SHALL reach the classifier through a workspace file read with bash
redirection, never through an environment variable. The workflow SHALL
authenticate only with the workflow's own `github.token`, SHALL NOT
reference any other secret, and SHALL NOT request Copilot as a reviewer.

#### Scenario: Template carries the marker, triggers, permissions, and concurrency
- **WHEN** `plugins/s/integrations/copilot/copilot-review-gate.yml` is read
- **THEN** it contains the marker line `# shipd-copilot v{version}`,
  triggers on `pull_request` (`opened`, `synchronize`, `reopened`) and
  `pull_request_review` (`submitted`), a `permissions` block granting
  `statuses: write` and `pull-requests: read`, and a `concurrency` group
  keyed on the pull request number with `cancel-in-progress: true`

#### Scenario: Pull-request events post pending then poll
- **WHEN** the template's `pull_request` handling runs and the reviews API
  returns a Copilot review of the triggering head within the window
- **THEN** `pending` is posted on the head SHA first, and the found
  review's body is classified into a terminal status on the same head

#### Scenario: A timed-out poll leaves pending
- **WHEN** the poll window elapses with no Copilot review of the
  triggering head
- **THEN** no terminal status is posted and the `pending` status stands

#### Scenario: A superseded head stops the poll quietly
- **WHEN** the pull request's current head no longer equals the triggering
  head during the poll
- **THEN** the run exits without posting any further status

#### Scenario: The review-event path still guards reviewer and head commit
- **WHEN** a `pull_request_review` event fires
- **THEN** the workflow classifies only when the review author login is
  `copilot-pull-request-reviewer[bot]` and the review `commit_id` equals
  the pull request's current head SHA

#### Scenario: A verdict is only the last non-empty line
- **WHEN** a classified body quotes both markers mid-text and ends with the
  `<!-- shipd-verdict: ship-it -->` line
- **THEN** the classification is `success` via the ship-it branch, never
  `failure` from the quoted `fix-required` text

#### Scenario: Fix-required blocks, ship-it passes, anything else fails open
- **WHEN** a classified body's last non-empty line equals a marker, or
  equals neither
- **THEN** `<!-- shipd-verdict: fix-required -->` maps to `failure`,
  `<!-- shipd-verdict: ship-it -->` maps to `success`, and any other last
  line — markers mid-text only, an empty body — maps to `success` with a
  description stating that no verdict was parsed

#### Scenario: The body is never piped into a matcher nor env-passed on the poll path
- **WHEN** the gate job's script is read
- **THEN** the polling path lands the review body in a workspace file read
  back with bash redirection (no environment variable carries it), the
  extraction and comparisons are pure-bash parameter expansion and `[[ ]]`
  tests with the bounded windowed trim, and no non-comment line
  referencing the body contains a pipe into a matcher

#### Scenario: Only the default token, and no reviewer request
- **WHEN** the template is read
- **THEN** it references no secret other than the workflow's own
  `github.token` and contains no step requesting Copilot as a reviewer
