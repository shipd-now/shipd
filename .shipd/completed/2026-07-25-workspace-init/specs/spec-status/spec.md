## ADDED Requirements

### Requirement: Workspace init verb
id: workspace-init-verb

The status CLI SHALL provide `workspace-init <path>` which initializes a
workspace at the given directory through the engine's workspace
initialization and prints the created workspace root on success. If
initialization refuses or errors (a workspace already discoverable from the
target, or a missing target directory), then the CLI SHALL exit non-zero
with that error. Unlike the other workspace verbs, `workspace-init` SHALL
NOT require a discoverable workspace to run.

#### Scenario: Init verb creates and prints the root
- **GIVEN** an existing directory with no discoverable workspace
- **WHEN** `workspace-init <path>` runs against it
- **THEN** the marker is created, the created root is printed, and the exit
  code is zero

#### Scenario: Init verb refuses under an existing workspace
- **WHEN** `workspace-init <path>` runs where a workspace root is already
  discoverable from `<path>`
- **THEN** the CLI exits non-zero with an error naming the existing root
