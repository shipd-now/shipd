## ADDED Requirements

### Requirement: Doctor validates the workspaces root key
id: doctor-workspaces-root-check

The doctor verb's existing `config` check SHALL additionally validate the
`workspaces_root` key by resolving it through the engine's accessor
(shipd-config workspaces-root-key). If the resolved configuration declares a
malformed `workspaces_root` value, then the `config` check SHALL report
`fail` carrying the accessor's own error line, which names the key. If the
resolved value is well-formed but the declared root is not an existing
directory, then the `config` check SHALL report `warn` naming
`workspaces_root` and the missing path — report-only, mutating nothing. A
valid-and-present or undeclared key SHALL leave the check's existing
reporting unchanged, and the doctor check list SHALL NOT grow a new check
name for this validation.

#### Scenario: Malformed value fails the config check
- **GIVEN** a repo whose `.shipd-config.json` declares
  `"workspaces_root": "relative/path"`
- **WHEN** `shipd doctor` runs
- **THEN** the `config` line begins `fail` and its detail names
  `workspaces_root`

#### Scenario: Missing declared root warns
- **GIVEN** a config declaring `workspaces_root` naming a directory that does
  not exist
- **WHEN** `shipd doctor` runs
- **THEN** the `config` line begins `warn` naming `workspaces_root` and the
  missing path, and the exit code reflects no failure from this check

#### Scenario: Declared existing root passes unchanged
- **GIVEN** a config declaring `workspaces_root` naming an existing directory
- **WHEN** `shipd doctor` runs
- **THEN** the `config` check reports `ok` with its usual content-directory
  detail

#### Scenario: Undeclared key changes nothing
- **GIVEN** a repo whose layers declare no `workspaces_root`
- **WHEN** `shipd doctor` runs
- **THEN** the `config` check's reporting is identical to the pre-existing
  behavior
