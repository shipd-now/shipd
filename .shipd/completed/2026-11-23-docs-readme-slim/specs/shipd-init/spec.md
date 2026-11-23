## MODIFIED Requirements

### Requirement: The /s:init skill and its sections
id: init-skill-sections
base: 374ffe175c31

The plugin SHALL ship a skill named `init` with a harness body
`harness/bodies/init.md`. Bare `/s:init` SHALL run the full wizard;
`/s:init <section>` SHALL run one section alone, where the sections are
`layout`, `config`, `workspace`, `wiki`, `memory`, `hooks`, and `gate`. If the
section is not one of these, then the skill SHALL list the sections and stop
without writing. `docs/cheatsheet.md` and `AGENTS.md` SHALL list `/s:init`.

#### Scenario: Unknown section writes nothing
- **WHEN** `/s:init colours` runs
- **THEN** the skill lists the seven sections and no file changes

#### Scenario: Registry files list the command
- **WHEN** `docs/cheatsheet.md` and `AGENTS.md` are read
- **THEN** each names `/s:init`
