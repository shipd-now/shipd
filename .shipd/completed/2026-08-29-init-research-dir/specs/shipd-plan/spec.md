## MODIFIED Requirements

### Requirement: Missing-layout guard
id: missing-layout-guard
base: c301919d451e

When the repository lacks the resolved content-directory layout, the skill
SHALL stop before any questioning, report the missing layout, and ask via
one AskUserQuestion whether to scaffold the minimal layout (`verified/`,
`planned/`, `completed/`, and `research/` under the resolved content
directory, default `.shipd/`) and continue, or stop; it SHALL NOT continue
planning as though the layout existed. When the user accepts the scaffold,
the skill SHALL create the layout by running the engine's `spec_status.py
init` verb — the same function behind `shipd init` — never by creating the
directories by hand.

#### Scenario: Missing layout stops the flow
- **WHEN** `/s:plan` runs in a repository with no resolved content
  directory
- **THEN** the skill reports the missing layout and asks scaffold-or-stop
  before any planning question is posed

#### Scenario: Accepted scaffold proceeds through the engine
- **WHEN** the user accepts the scaffold option
- **THEN** the skill runs `spec_status.py init`, which creates the four
  directories and reports `all shipd directories are ready`, and the normal
  flow continues
