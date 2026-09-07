## ADDED Requirements

### Requirement: Completed-retention key
id: completed-retention-key

The configuration MAY declare `completed_retention_days`, resolved through the
standard layered per-key merge (nearest layer wins the key wholesale). The
engine SHALL seed the key with a built-in default of `30`, so resolution
always yields an effective value and `config-show` reports the undeclared key
with `default` provenance. The engine SHALL expose an accessor interpreting
the resolved value as a retention window: a positive integer N SHALL yield a
window of N days; `0` or `null` SHALL yield a disabled window (consumers never
hide). If the declared value is anything else — a boolean, a negative number,
a non-integer — then the accessor SHALL treat the key as undeclared and yield
the default rather than erroring.

#### Scenario: Undeclared key defaults to 30
- **GIVEN** a repo whose layers declare no `completed_retention_days`
- **WHEN** the configuration is resolved and the accessor is consulted
- **THEN** the window is 30 days and `config-show` lists the key with
  `default` provenance

#### Scenario: Zero disables retention
- **GIVEN** a layer declaring `"completed_retention_days": 0`
- **WHEN** the accessor is consulted
- **THEN** it reports a disabled window

#### Scenario: Null disables retention
- **GIVEN** a layer declaring `"completed_retention_days": null`
- **WHEN** the accessor is consulted
- **THEN** it reports a disabled window

#### Scenario: A malformed value is treated as undeclared
- **GIVEN** a layer declaring `"completed_retention_days": "forever"`
- **WHEN** the accessor is consulted
- **THEN** it yields the default 30-day window and no error is raised

#### Scenario: Nearest layer wins the key
- **GIVEN** the repo layer declares `7` and the home layer declares `90`
- **WHEN** the configuration is resolved from the repo
- **THEN** the effective window is 7 days
