## MODIFIED Requirements

### Requirement: Persistent build log
id: persistent-build-log
base: d867589bc7c0

Each completed build SHALL be recorded under the resolved build log
directory — default `~/.shipd/builds/` — as a structured entry capturing at
least: timestamp, change name, schema, task counts, status, commit hash, the
per-model token breakdown (non-cached and cached), the per-model time
breakdown, and the total build runtime. The directory SHALL be created on
demand. Logging failures SHALL NOT fail the build. No path under
`~/.shipd/` SHALL be read or written.

#### Scenario: A build appends a log entry
- **WHEN** a build completes under default configuration
- **THEN** a structured record for it exists under `~/.shipd/builds/`
  containing the change name, commit hash, status, per-model token and time
  breakdowns, and total runtime

#### Scenario: The log directory is created on demand
- **WHEN** `~/.shipd/builds/` does not yet exist at build time
- **THEN** it is created automatically before the entry is written

### Requirement: User configuration file
id: user-configuration-file
base: 487d51837959

`/s:build` SHALL read optional settings from the resolved layered
configuration's `build` key — typically declared in `~/.shipd-config.json` —
applying documented defaults when no layer declares it or a key is missing.
A committed example config SHALL document the available keys.

#### Scenario: Config is optional
- **WHEN** no config layer declares a `build` key
- **THEN** the build proceeds using documented defaults

#### Scenario: Config controls logging
- **WHEN** the resolved `build` object disables logging
- **THEN** no build log entry is written and the build still succeeds
