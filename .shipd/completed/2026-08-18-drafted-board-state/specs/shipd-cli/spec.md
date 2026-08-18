## ADDED Requirements

### Requirement: Doctor validates the PR mode key
id: doctor-pr-mode-check

The doctor verb's existing `config` check SHALL additionally validate the
`pr-mode` key by resolving it through the engine's accessor
(shipd-config pr-mode-key). If the resolved configuration declares an
invalid `pr-mode` value, then the `config` check SHALL report `fail`
carrying the resolver's own error line — which names the key, the
offending value, the accepted values, and the supplying config file. A
valid or undeclared key SHALL leave the check's existing
content-directory reporting unchanged, and the doctor check list SHALL
NOT grow a new check name for this validation.

#### Scenario: Invalid pr-mode fails the config check
- **GIVEN** a repo whose `.shipd-config.json` declares `"pr-mode": "always"`
- **WHEN** `shipd doctor` runs
- **THEN** the `config` line begins `fail` and its detail names `pr-mode`,
  the accepted values, and the supplying config file

#### Scenario: Declared draft mode passes the config check
- **GIVEN** a repo whose config declares `"pr-mode": "draft"`
- **WHEN** `shipd doctor` runs
- **THEN** the `config` check reports `ok` with its usual
  content-directory detail

#### Scenario: Undeclared key changes nothing
- **GIVEN** a repo declaring no `pr-mode`
- **WHEN** `shipd doctor` runs
- **THEN** the `config` check reports exactly what it reported before this
  validation existed
