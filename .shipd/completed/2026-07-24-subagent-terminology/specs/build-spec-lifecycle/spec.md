# build-spec-lifecycle — delta

## MODIFIED Requirements

### Requirement: Lint gates execution
id: lint-gates-execution
base: ff7bb041ba01

`/s:build` SHALL run `spec_lint.py` on the change and require a zero exit
status before spawning any execution sub-agent. Lint errors SHALL be fixed in the
artifacts (not waived) and lint re-run until clean.

#### Scenario: Sub-agents only spawn on clean lint
- **WHEN** `spec_lint.py` exits non-zero for the change
- **THEN** build fixes the artifacts and re-lints; no sub-agent is spawned until
  the exit status is zero

### Requirement: Build updates spec status at phase boundaries
id: build-updates-spec-status
base: dcc2f0f407d5

The build flow SHALL select the change it is building (`use`) when execution
begins, and SHALL update the change's status via the status CLI at phase
boundaries: `active` when sub-agents are spawned, `complete` when the task
coordinator reports nothing pending or in progress, and `verified` when
verification passes — all before the change is merged and archived.

#### Scenario: Spawning marks the spec active
- **WHEN** build spawns its first execution sub-agent for a change
- **THEN** the change is the current selection and its status is `active`

#### Scenario: Verification marks the spec verified
- **WHEN** Phase 5 verification passes for a completed change
- **THEN** the plan's status line reads `Status: verified` before merge
  and archive
