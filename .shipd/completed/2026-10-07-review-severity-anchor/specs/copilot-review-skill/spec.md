## MODIFIED Requirements

### Requirement: Copilot review skill template
id: skill-template
base: 0adcdaf6fe74

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

The template's `low` severity SHALL be a real defect whose impact is contained,
never pure style, naming preference, or formatting, which SHALL NOT be reported
as a finding at any severity. The template SHALL state beside that rubric that
severity follows what a defect does rather than the kind of defect it is, so
data loss, data corruption, a security exposure, or a broken guarantee is
`medium` or `high`.

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

#### Scenario: The template's low rubric excludes pure style
- **WHEN** the template's severity rubric is read
- **THEN** `low` names a real defect whose impact is contained, pure style is
  excluded from findings at any severity, and the rule that impact outranks
  the kind of defect appears beside it
