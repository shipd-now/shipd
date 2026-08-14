## ADDED Requirements

### Requirement: Metadata-preserving status writes
id: metadata-preserving-status-writes

The status CLI's `set-status` and `sync` verbs SHALL rewrite only the
`Status:` line, preserving any header metadata lines byte-for-byte, and the
`show` verb SHALL print the plan's recognized metadata lines when present.

#### Scenario: Set-status keeps metadata intact
- **GIVEN** a plan whose header carries `Theme: reliability` after `Status:`
- **WHEN** `set-status ready` runs on the change
- **THEN** the `Status:` line becomes `ready` and the `Theme:` line is
  unchanged

#### Scenario: Show displays metadata
- **WHEN** `show` runs on a change whose plan carries `Profile: lite` and
  `Theme: reliability`
- **THEN** the output includes the profile and theme alongside the status and
  task progress
