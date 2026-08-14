## ADDED Requirements

### Requirement: Workspace initialization
id: workspace-initialization

When given an existing target directory, the engine SHALL initialize a
workspace by creating `<target>/.shipd/workspace.json` containing an empty
JSON object and SHALL report the created workspace root. If a workspace root
is already discoverable from the target (nearest-ancestor search, the target
itself included), then initialization SHALL refuse with an error naming the
existing root and SHALL write nothing. If the target directory does not
exist, then initialization SHALL error rather than create it.

#### Scenario: Init creates the minimal marker
- **GIVEN** an existing directory with no discoverable workspace in any
  ancestor
- **WHEN** workspace initialization runs against it
- **THEN** `.shipd/workspace.json` exists under it containing `{}` and the
  directory is reported as the created workspace root

#### Scenario: Init refuses under an existing workspace
- **GIVEN** a directory whose ancestor carries `.shipd/workspace.json`
- **WHEN** workspace initialization runs against it
- **THEN** it errors naming the existing workspace root and writes nothing

#### Scenario: Missing target directory errors
- **WHEN** workspace initialization runs against a path that is not an
  existing directory
- **THEN** it errors rather than creating the directory

### Requirement: Workspace setup skill
id: workspace-setup-skill

An `/s:workspace` skill SHALL provide, selected by argument: `init` — guided
workspace creation that, when a workspace root is already discoverable,
reports that root and stops; otherwise asks the user to choose the target
root (the repository's parent directory offered as the recommended default,
the repository root as the alternative) and drives the status CLI's
`workspace-init` verb, reporting the created root; and `show` — the workspace
roster via the status CLI's `workspace-show` verb, reading only. The skill
SHALL NOT write the marker by hand — creation goes through the CLI verb.

#### Scenario: Init on an existing workspace reports and stops
- **WHEN** the skill's `init` verb runs where a workspace root is discoverable
- **THEN** the skill reports that root, creates nothing, and stops

#### Scenario: Init creates through the CLI verb
- **WHEN** the user confirms a target root during `init` where no workspace is
  discoverable
- **THEN** the skill runs `workspace-init` against that root and reports the
  root the verb printed

#### Scenario: Show reports the roster
- **WHEN** the skill's `show` verb runs in a discoverable workspace
- **THEN** the workspace root, projects, and initiatives are reported and
  nothing is changed
