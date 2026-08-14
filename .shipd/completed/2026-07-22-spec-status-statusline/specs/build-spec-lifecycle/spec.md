## ADDED Requirements

### Requirement: Build updates spec status at phase boundaries
id: build-updates-spec-status

The build flow SHALL select the change it is building (`use`) when execution
begins, and SHALL update the change's status via the status CLI at phase
boundaries: `active` when teammates are spawned, `complete` when the task
coordinator reports nothing pending or in progress, and `verified` when
verification passes — all before the change is merged and archived.

#### Scenario: Spawning marks the spec active
- **WHEN** build spawns its first execution teammate for a change
- **THEN** the change is the current selection and its status is `active`

#### Scenario: Verification marks the spec verified
- **WHEN** Phase 5 verification passes for a completed change
- **THEN** the proposal's status line reads `Status: verified` before merge
  and archive
