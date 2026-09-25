## ADDED Requirements

### Requirement: Doctor local-state check
id: doctor-local-state-check

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
skipped. The check SHALL be report-only: it SHALL mutate nothing, and under
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
