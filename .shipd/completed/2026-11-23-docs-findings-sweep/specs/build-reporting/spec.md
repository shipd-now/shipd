## MODIFIED Requirements

### Requirement: User configuration file
id: user-configuration-file
base: aa10f1f4482f

`/s:build` SHALL read optional settings from the resolved layered
configuration's `build` key — typically declared in `~/.shipd-config.json` —
applying documented defaults when no layer declares it or a key is missing.
A committed example config SHALL document the available keys.
`build_report.py` SHALL only read that configuration: it SHALL never create
or write a configuration file, and `plugins/s/skills/build/SKILL.md` SHALL
describe the report step as reading the file, never as creating it.

#### Scenario: Config is optional
- **WHEN** no config layer declares a `build` key
- **THEN** the build proceeds using documented defaults

#### Scenario: Config controls logging
- **WHEN** the resolved `build` object disables logging
- **THEN** no build log entry is written and the build still succeeds

#### Scenario: The report never creates the config
- **WHEN** `build_report.py` runs where no layer declares a `build` key
- **THEN** it creates no configuration file, and the build skill's report
  step says the script reads `~/.shipd-config.json` and never creates it
