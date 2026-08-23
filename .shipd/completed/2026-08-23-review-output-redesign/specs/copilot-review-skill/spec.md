## MODIFIED Requirements

### Requirement: Copilot review skill template
id: skill-template
base: 5f511738283d

The plugin SHALL carry a Copilot code-review skill template at
`integrations/copilot/SKILL.md` containing: YAML frontmatter with `name` and
`description` fields; the ownership marker line `<!-- shipd-copilot
v{version} -->` with the literal `{version}` placeholder; instructions that
direct the reviewing agent to run the bundled engine
(`python3 .github/skills/code-review/scripts/semdiff.py`) with its `files`,
`diff`, and `context` subcommands and to reason from that structural JSON
rather than raw file dumps; the severity rubric (`high`/`medium`/`low`) with
the ship-it/fix-required verdict rule (any high or medium finding blocks); an
instruction that the review body ends with a visible verdict line plus the
matching machine-readable marker — `<!-- shipd-verdict: ship-it -->` or
`<!-- shipd-verdict: fix-required -->` — on its own line as the body's last
line, stating that the marker is read from the last non-empty line by exact
equality; a statement that the skill is the review contract for both surfaces
that consume it; a statement that the engine is read-only and degrades to its
text engine when `difft` is unavailable; and documentation that the Copilot
code-review surface exposes no repository-side model selection and that the
verdict marker drives the required `semantic-review` commit status under the
repository's `SHIPD_GATE_FAIL_OPEN` setting.

The template SHALL additionally require the review body to open with a verdict
header and a severity summary table before any per-finding detail, and to keep
each finding's detail brief enough to be read at a glance. It SHALL require the
agent to write a machine-readable findings file beside the body, each finding
carrying its severity, its file path and line range, its prose detail, and —
only where the agent judges the fix confident and expressible as one or more
contiguous whole lines — a replacement for those lines.

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
- **THEN** they require exactly one marker as the body's last line and state
  it is read from the last non-empty line by exact equality

#### Scenario: The report shape is mandated
- **WHEN** the template's report instructions are read
- **THEN** they require a verdict header and a severity summary table ahead of
  any per-finding detail

#### Scenario: The findings file is specified
- **WHEN** the template's report instructions are read
- **THEN** they require a machine-readable findings file whose entries carry
  severity, path, line range, and detail, and carry a replacement only for a
  fix the agent judges confident and expressible as contiguous whole lines

### Requirement: Copilot review-gate workflow template
id: gate-workflow-template
base: 8c2c52395947

The plugin SHALL carry a review-gate workflow template at
`integrations/copilot/copilot-review-gate.yml` that posts a terminal
`semantic-review` commit status for every reviewed head, reads the verdict
from the review text's last non-empty line by exact equality, honours the
repository's `SHIPD_GATE_FAIL_OPEN` setting for a marker-less review, and
keeps the reviewer's credential and the repository credential in separate
steps so the reviewing agent holds no credential able to post a status,
comment, or push.

Where the gate's own reviewer produced the review, the workflow SHALL publish
it as a pull-request review rather than as an issue comment, submitting the
event `COMMENT`, carrying the review body and one anchored inline comment per
finding whose path and line range the workflow itself verifies against the
diff it computed. A finding naming a path or range outside that diff SHALL be
folded into the body as prose rather than anchored. Where such a finding also
carries a replacement, its inline comment SHALL include that replacement as a
committable `suggestion` block.

#### Scenario: The gate's own review is posted as a review
- **WHEN** the workflow's own reviewer produces a review body for a pull
  request
- **THEN** it is published through the pull-request reviews API with the event
  `COMMENT`, not as an issue comment

#### Scenario: A verified finding is anchored
- **WHEN** a finding's path and line range are present in the diff the
  workflow computed
- **THEN** it is posted as an inline comment on that range

#### Scenario: An unverifiable finding is not anchored
- **WHEN** a finding names a path or line range absent from that diff
- **THEN** it is folded into the review body as prose and no inline comment is
  posted for it

#### Scenario: A confident replacement becomes committable
- **WHEN** an anchored finding carries a replacement
- **THEN** its inline comment contains a `suggestion` fenced block carrying
  that replacement

#### Scenario: The credentials stay separated
- **WHEN** the template's steps are read
- **THEN** the reviewer step binds only the reviewer token and the posting
  step binds only the workflow token
