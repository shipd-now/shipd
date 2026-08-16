## ADDED Requirements

### Requirement: Copilot review skill template
id: skill-template

The plugin SHALL carry a Copilot code-review skill template at
`integrations/copilot/SKILL.md` containing: YAML frontmatter with `name` and
`description` fields; the ownership marker line `<!-- shipd-copilot
v{version} -->` with the literal `{version}` placeholder; instructions that
direct the reviewing agent to run the bundled engine
(`python3 .github/skills/code-review/scripts/semdiff.py`) with its `files`,
`diff`, and `context` subcommands and to reason from that structural JSON
rather than raw file dumps; the severity rubric (`high`/`medium`/`low`) with
the ship-it/fix-required verdict rule (any high or medium finding blocks);
a statement that the engine is read-only and degrades to its text engine
when `difft` is unavailable; and documentation that the Copilot code-review
surface exposes no repository-side model selection and that this review is
advisory alongside any required merge gate.

#### Scenario: Template exists with the placeholder marker
- **WHEN** `plugins/s/integrations/copilot/SKILL.md` is read
- **THEN** it contains the literal line `<!-- shipd-copilot v{version} -->`
  and frontmatter `name` and `description` fields

#### Scenario: Template directs the agent to the bundled engine
- **WHEN** the template body is read
- **THEN** it names the `files`, `diff`, and `context` subcommands of the
  bundled `semdiff.py`, the high/medium/low rubric, and the no-model-pin
  documentation

### Requirement: Copilot review setup workflow template
id: setup-workflow-template

The plugin SHALL carry a Copilot code-review environment workflow template at
`integrations/copilot/copilot-code-review.yml` containing: the ownership
marker line `# shipd-copilot v{version}` with the literal `{version}`
placeholder; a single job named `copilot-setup-steps` running on
`ubuntu-latest`; and steps that install the prebuilt `difft` release binary
onto the runner's `PATH` (the same release-tarball source `semdiff.py`'s own
installer uses) and install `ripgrep`. The template SHALL NOT reference any
secret or organization-specific value.

#### Scenario: Workflow defines the setup job
- **WHEN** `plugins/s/integrations/copilot/copilot-code-review.yml` is read
- **THEN** it contains the marker line `# shipd-copilot v{version}` and
  exactly one job, named `copilot-setup-steps`, on `ubuntu-latest`

#### Scenario: Workflow provisions the diff tooling
- **WHEN** the template's steps are read
- **THEN** one step installs the `difft` release binary onto `PATH` and one
  installs `ripgrep`
