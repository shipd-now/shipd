## ADDED Requirements

### Requirement: Copilot review-gate workflow template
id: gate-workflow-template

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
map the review body onto the same status context: a body containing
`<!-- shipd-verdict: fix-required -->` posts state `failure`; a body
containing `<!-- shipd-verdict: ship-it -->` posts state `success`; a body
containing neither marker posts state `success` with a description stating
that no verdict was parsed. The workflow SHALL authenticate only with the
workflow's own `github.token`, SHALL NOT reference any other secret, and
SHALL NOT request Copilot as a reviewer.

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

#### Scenario: Fix-required blocks, ship-it passes
- **WHEN** the verdict mapping is read
- **THEN** `<!-- shipd-verdict: fix-required -->` maps to state `failure`
  and `<!-- shipd-verdict: ship-it -->` maps to state `success`

#### Scenario: A verdict-less review passes fail-open
- **WHEN** the verdict mapping is read
- **THEN** a body with neither marker maps to state `success` with a
  description stating that no verdict was parsed

#### Scenario: Only the default token, and no reviewer request
- **WHEN** the template is read
- **THEN** it references no secret other than the workflow's own
  `github.token` and contains no step requesting Copilot as a reviewer

## MODIFIED Requirements

### Requirement: Copilot review skill template
id: skill-template
base: 16bf65e2d738

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
`<!-- shipd-verdict: fix-required -->` — on its own line; a statement that
the engine is read-only and degrades to its text engine when `difft` is
unavailable; and documentation that the Copilot code-review surface exposes
no repository-side model selection and that, where the repository's
`copilot-review-gate.yml` workflow is installed, the review's verdict
marker drives the required `semantic-review` commit status — a review
without a marker passes fail-open — while the review stays advisory where
no gate workflow is installed.

#### Scenario: Template exists with the placeholder marker
- **WHEN** `plugins/s/integrations/copilot/SKILL.md` is read
- **THEN** it contains the literal line `<!-- shipd-copilot v{version} -->`
  and frontmatter `name` and `description` fields

#### Scenario: Template directs the agent to the bundled engine
- **WHEN** the template body is read
- **THEN** it names the `files`, `diff`, and `context` subcommands of the
  bundled `semdiff.py`, the high/medium/low rubric, and the no-model-pin
  documentation

#### Scenario: Template mandates the verdict marker
- **WHEN** the template's report instructions are read
- **THEN** they require the review body to end with a verdict line and the
  matching `<!-- shipd-verdict: ship-it -->` or
  `<!-- shipd-verdict: fix-required -->` marker, and describe the gate
  workflow's fail-open bridging of that marker into the `semantic-review`
  status
