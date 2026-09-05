## ADDED Requirements

### Requirement: Doctor schema check
id: doctor-schema-check

The doctor preflight SHALL include a `schema` check reporting the repo's
schema version against the engine's `SCHEMA_VERSION`: `ok` naming the
version (and whether it was read from the marker or assumed) when the
majors match and the repo's minor is not ahead, `warn` when the repo's
minor is ahead of the engine's, and `fail` naming both versions and the
remedy on a major mismatch. The check SHALL report rather than raise, so a
mismatched repo still completes its preflight.

#### Scenario: Healthy repo reports ok
- **GIVEN** a repo whose marker equals the engine's version
- **WHEN** `shipd doctor` runs
- **THEN** the output carries `ok schema` naming the version

#### Scenario: Major mismatch is a fail line, not a crash
- **GIVEN** a repo whose marker carries a different major
- **WHEN** `shipd doctor` runs
- **THEN** the output carries `fail schema` naming both versions and the
  preflight still completes its remaining checks
