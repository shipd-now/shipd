## ADDED Requirements

### Requirement: Emission carries the status header
id: emission-carries-status-header

The plan flow SHALL emit every proposal with the `# <change-name>` title and
`Status: draft` header, and SHALL promote the status to `ready` when the
emitted change is lint-clean and the user has approved the plan.

#### Scenario: Fresh emission is draft
- **WHEN** plan emits a change's artifacts
- **THEN** the proposal begins with the title and `Status: draft`

#### Scenario: Approval promotes to ready
- **WHEN** the emitted change lints clean and the user approves
- **THEN** the proposal's status line reads `Status: ready` before hand-off
  to execution
