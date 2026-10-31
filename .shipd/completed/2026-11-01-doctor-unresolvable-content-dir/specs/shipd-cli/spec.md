## MODIFIED Requirements

### Requirement: Doctor schema check
id: doctor-schema-check
base: f840eaa6ec94

The doctor preflight SHALL include a `schema` check reporting the repo's
schema version against the engine's `SCHEMA_VERSION`: `ok` naming the
version (and whether it was read from the marker or assumed) when the
majors match and the repo's minor is not ahead, `warn` when the repo's
minor is ahead of the engine's, and `fail` naming both versions and the
remedy on a major mismatch. The check SHALL report rather than raise, so a
mismatched repo still completes its preflight. If the configuration fails to
resolve a content directory, then the check SHALL report `ok` carrying the
error as its detail and stating that the check was skipped, so the check never
double-fails what the `config` check owns. A marker that resolves but cannot
be read or parsed SHALL still report `fail` naming the marker file.

#### Scenario: Healthy repo reports ok
- **GIVEN** a repo whose marker equals the engine's version
- **WHEN** `shipd doctor` runs
- **THEN** the output carries `ok schema` naming the version

#### Scenario: Major mismatch is a fail line, not a crash
- **GIVEN** a repo whose marker carries a different major
- **WHEN** `shipd doctor` runs
- **THEN** the output carries `fail schema` naming both versions and the
  preflight still completes its remaining checks

#### Scenario: Unresolvable content directory is skipped, not double-failed
- **GIVEN** a repo whose configuration declares `dir: "../specs"`
- **WHEN** `shipd doctor` runs
- **THEN** the `schema` line begins `ok`, its detail names `../specs` and says
  the check was skipped, and only the `config` check fails for that value

### Requirement: Doctor local-state check
id: doctor-local-state-check
base: d562a844eaca

The `doctor` verb SHALL additionally report a `local-state` check, directly
after `store-sync` and before `gh`, covering the two local-state paths the engine writes but
never commits: `<content-dir>/state.json` and `<content-dir>/autopilot/`.
The check SHALL report `warn` when either path is tracked by git at the
working directory, naming the tracked paths, and `warn` when the root's
`.gitignore` lacks either rule, naming the missing rules; either detail SHALL
name `shipd init` as the remedy. When both rules are present and neither path
is tracked, the check SHALL report `ok` naming the rules. If the content
directory resolves outside the repository, or the working directory is not a
git checkout, then the check SHALL report `ok` with a note naming why it was
skipped. If the configuration fails to resolve a content directory, then the
check SHALL report `ok` carrying the error as its detail and stating that the
check was skipped, so the check never double-fails what the `config` check
owns and the preflight still completes. The check SHALL be report-only: it
SHALL mutate nothing, and under
`--fix` it SHALL stay report-only, naming the surface its finding affects
and `shipd init` as the manual remedy, so the automated remedy set is
unchanged.

#### Scenario: Tracked state file warns
- **GIVEN** a git checkout whose committed tree tracks `.shipd/state.json`
- **WHEN** `shipd doctor` runs
- **THEN** a `warn local-state — ` line names `.shipd/state.json` and
  `shipd init`, and the exit code is `0`

#### Scenario: Missing ignore rule warns
- **GIVEN** a git checkout tracking neither path whose `.gitignore` lacks
  `.shipd/autopilot/`
- **WHEN** `shipd doctor` runs
- **THEN** a `warn local-state — ` line names the missing rule and
  `shipd init`

#### Scenario: Ignored and untracked reports ok
- **GIVEN** a git checkout whose `.gitignore` carries both rules and tracks
  neither path
- **WHEN** `shipd doctor` runs
- **THEN** the `local-state` line begins `ok`

#### Scenario: Not a checkout is skipped
- **WHEN** `shipd doctor` runs in a directory with no `.git` entry
- **THEN** the `local-state` line begins `ok` and its detail says the check
  was skipped

#### Scenario: Check order follows store-sync
- **WHEN** `shipd doctor` runs
- **THEN** the `local-state` line is printed directly after the `store-sync` line and before the `gh` line

#### Scenario: Stays report-only under fix
- **WHEN** `shipd doctor --fix` runs with `local-state` warning
- **THEN** no remedy runs for it, and the report-only line names `shipd init`

#### Scenario: Unresolvable content directory is skipped, not raised
- **GIVEN** a git checkout whose configuration declares `dir: "../specs"`
- **WHEN** `shipd doctor` runs
- **THEN** the `local-state` line begins `ok`, its detail names `../specs` and
  says the check was skipped, and every later check still prints its line
