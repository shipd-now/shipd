## ADDED Requirements

### Requirement: Initiative status verbs
id: initiative-status-verbs

The status CLI SHALL provide `initiative-show <slug>` printing a brief's
status, metadata, requirement progress (`done/total`), and each requirement
line; `initiative-sync <slug>` re-deriving the status from the requirement
checkboxes — `achieved` when at least one requirement exists and all are
ticked, `open` otherwise, never changing a `dropped` brief; and
`initiative-set-status <status> <slug>` writing a validated status from
`open`, `achieved`, `dropped`. All three SHALL resolve the workspace from
the repository root and SHALL exit non-zero with a clear error when no
workspace is discoverable.

#### Scenario: Show reports requirement progress
- **GIVEN** a brief with three requirements, one ticked
- **WHEN** `initiative-show` runs
- **THEN** the output includes the status and a `1/3` progress count

#### Scenario: Sync derives achieved
- **GIVEN** an `open` brief whose every requirement checkbox is ticked
- **WHEN** `initiative-sync` runs
- **THEN** the brief's status line becomes `achieved`

#### Scenario: Sync never touches dropped
- **WHEN** `initiative-sync` runs on a `dropped` brief with all requirements
  ticked
- **THEN** the status line is left unchanged

#### Scenario: Verbs require a workspace
- **WHEN** `initiative-show` runs in a checkout with no discoverable
  workspace
- **THEN** the CLI exits non-zero saying no workspace was found

#### Scenario: Set-status validates the value
- **WHEN** `initiative-set-status pending` runs
- **THEN** nothing is written and the CLI errors non-zero
