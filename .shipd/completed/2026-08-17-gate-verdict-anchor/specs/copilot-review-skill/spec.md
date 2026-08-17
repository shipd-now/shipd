## MODIFIED Requirements

### Requirement: Copilot review-gate workflow template
id: gate-workflow-template
base: afc317fce7d7

The plugin SHALL carry a Copilot review-gate workflow template at
`integrations/copilot/copilot-review-gate.yml` containing: the ownership
marker line `# shipd-copilot v{version}` with the literal `{version}`
placeholder; triggers on `pull_request` (types `opened`, `synchronize`,
`reopened`) and `pull_request_review` (type `submitted`); and a
`permissions` block granting `statuses: write`. When a `pull_request`
event fires, the workflow SHALL post the commit status context
`semantic-review` with state `pending` on the pull request's head SHA.
When a `pull_request_review` event fires, the workflow SHALL act only if
the review author's login is `copilot-pull-request-reviewer[bot]` and the
review's `commit_id` equals the pull request's current head SHA, and SHALL
classify the review by its body's **last non-empty line** — extracted with
pure-bash parameter expansion (never by piping the body into an external
matcher), with carriage returns and surrounding whitespace tolerated —
compared for equality against the markers: a last line equal to
`<!-- shipd-verdict: fix-required -->` posts state `failure`; a last line
equal to `<!-- shipd-verdict: ship-it -->` posts state `success`; any
other last line — including a body whose markers appear only mid-text, and
an empty body — posts state `success` with a description stating that no
verdict was parsed. A marker appearing anywhere other than the last
non-empty line SHALL NOT affect classification. The workflow SHALL
authenticate only with the workflow's own `github.token`, SHALL NOT
reference any other secret, and SHALL NOT request Copilot as a reviewer.

#### Scenario: Template carries the marker, triggers, and permissions
- **WHEN** `plugins/s/integrations/copilot/copilot-review-gate.yml` is read
- **THEN** it contains the marker line `# shipd-copilot v{version}`,
  triggers on `pull_request` (`opened`, `synchronize`, `reopened`) and
  `pull_request_review` (`submitted`), and a `permissions` block granting
  `statuses: write`

#### Scenario: Pull-request events post pending
- **WHEN** the template's `pull_request` handling is read
- **THEN** it posts the `semantic-review` status with state `pending` on
  the pull request's head SHA

#### Scenario: The bridge guards reviewer and head commit
- **WHEN** the template's `pull_request_review` handling is read
- **THEN** it acts only when the review author login is
  `copilot-pull-request-reviewer[bot]` and the review `commit_id` equals
  the pull request's current head SHA

#### Scenario: A verdict is only the last non-empty line
- **WHEN** a review body quotes both markers mid-text and ends with the
  `<!-- shipd-verdict: ship-it -->` line
- **THEN** the classification is `success` via the ship-it branch, never
  `failure` from the quoted `fix-required` text

#### Scenario: Fix-required blocks, ship-it passes
- **WHEN** the review body's last non-empty line equals a verdict marker
- **THEN** `<!-- shipd-verdict: fix-required -->` maps to state `failure`
  and `<!-- shipd-verdict: ship-it -->` maps to state `success`

#### Scenario: A verdict-less review passes fail-open
- **WHEN** the review body's last non-empty line equals neither marker —
  including when markers appear only mid-text, and when the body is empty
- **THEN** the classification is state `success` with a description
  stating that no verdict was parsed

#### Scenario: The body is never piped into a matcher
- **WHEN** the bridge job's script is read
- **THEN** the last-line extraction and both comparisons use pure-bash
  parameter expansion and `[[ ]]` tests, and no non-comment line
  referencing the review body contains a pipe

#### Scenario: Only the default token, and no reviewer request
- **WHEN** the template is read
- **THEN** it references no secret other than the workflow's own
  `github.token` and contains no step requesting Copilot as a reviewer
