## MODIFIED Requirements

### Requirement: Copilot review skill template
id: skill-template
base: 0e7438ba4ce5
Dropped: The marker instruction states last-line equality

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
line, stating how the gate reads it; `gate-workflow-template` owns the
reader's semantics and this requirement SHALL NOT restate them; a statement that the skill is the review contract for both surfaces
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

The template's severity rubric SHALL state the same `low` definition and the
same impact floor that `semantic-review`'s `review-skill` requirement states
for `SKILL.md`, including the concrete instances that requirement names.
`review-skill` owns that wording; this requirement SHALL NOT restate it, so
the rubric has one source and the template cannot drift from the skill it
mirrors. The template SHALL carry that wording **inline**, because it is
vendored byte-for-byte into a GitHub Actions runner and can read no reference
file.

#### Scenario: Template exists with the placeholder marker
- **WHEN** `plugins/s/integrations/copilot/SKILL.md` is read
- **THEN** it contains the literal line `<!-- shipd-copilot v{version} -->`
  and frontmatter `name` and `description` fields

#### Scenario: Template directs the agent to the bundled engine
- **WHEN** the template body is read
- **THEN** it names the `files`, `diff`, and `context` subcommands of the
  bundled `semdiff.py`, the high/medium/low rubric, and the no-model-pin
  documentation

#### Scenario: The marker instruction matches the reader
- **WHEN** the template's marker instruction is compared with the reader
  semantics `gate-workflow-template` states for the gate workflow
- **THEN** they agree, and this requirement restates neither

#### Scenario: The report shape is mandated
- **WHEN** the template's report instructions are read
- **THEN** they require a verdict header and a severity summary table ahead of
  any per-finding detail

#### Scenario: The findings file is specified
- **WHEN** the template's report instructions are read
- **THEN** they require a machine-readable findings file whose entries carry
  severity, path, line range, and detail, and carry a replacement only for a
  fix the agent judges confident and expressible as contiguous whole lines

#### Scenario: The template's rubric matches the skill's
- **WHEN** the template's severity rubric is compared with the `low` bullet and
  impact floor in `plugins/s/skills/review/SKILL.md`
- **THEN** the template states the same `low` definition, the same floor, and
  the same concrete instances

#### Scenario: This requirement restates no rubric wording
- **WHEN** this requirement's own text is read
- **THEN** it names `review-skill` as the owner of the `low` definition and the
  impact floor rather than reproducing either, so the two cannot disagree
