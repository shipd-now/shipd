## ADDED Requirements

### Requirement: Doctor pipeline check defers an unloadable configuration
id: doctor-pipeline-unloadable-config

If the layered configuration at the working directory cannot load — a layer
holds invalid JSON or the configuration fails to resolve — then the doctor's
`pipeline` check SHALL report `ok` carrying the error as its detail and stating
that the check was skipped, so the check never double-fails what the `config`
check owns. Where the configuration loads, the check SHALL resolve the declared
pipeline as before, and a declared pipeline with malformed entries or an
unknown preset SHALL still report `fail` carrying the resolver's error.

#### Scenario: Malformed config is skipped, not double-failed
- **GIVEN** a repo whose `.shipd-config.json` holds invalid JSON
- **WHEN** `shipd doctor` runs
- **THEN** the `pipeline` line begins `ok`, its detail says the check was
  skipped and carries the JSON error, and `config` is the only check that
  fails for that file

#### Scenario: An unknown preset in a loaded config still fails
- **GIVEN** a repo whose `.shipd-config.json` is valid JSON declaring
  `"autonomous-pipeline": "nope"`
- **WHEN** `shipd doctor` runs
- **THEN** a `fail pipeline — ` line names the unknown preset `nope`
