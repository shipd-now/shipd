## ADDED Requirements

### Requirement: Copilot update refreshes every installed set
id: copilot-update

When invoked as `copilot update`, the `copilot` verb SHALL refresh the four gate files exactly as `copilot add` does, and SHALL also refresh the room wake set where its "room-wake.yml" carries the shipd-copilot ownership marker (reported `installed` or `stale`). Where the wake workflow is absent or carries no marker, the verb SHALL leave every wake path untouched and print one line saying the wake set was left as is, without changing the exit code. The verb SHALL prepare every payload it will write before the first write. If any of the four gate files is foreign, then `update` SHALL refuse with exit `1` naming it and write nothing, unless `--force` is given; `--force` SHALL NOT cause a wake path to be written. If `--room` is given with `update`, then the verb SHALL exit `2` with a usage error and write nothing. `copilot add`, with or without `--room`, SHALL keep its behaviour unchanged.

#### Scenario: Update refreshes an installed stale wake set
- **WHEN** `shipd copilot update --root <dir>` runs on a directory holding a stale gate install and a wake set whose workflow marker names an older version and whose bundled room runtime has drifted
- **THEN** the four gate files and all six wake files are written at the running version, the bare report shows all ten `installed`, and the exit code is `0`

#### Scenario: Update never installs the wake set fresh
- **WHEN** `update` runs on a directory with a gate install and no wake files
- **THEN** the four gate files are written, no wake path exists afterwards, the output says the wake set was left as is, and the exit code is `0`

#### Scenario: A foreign wake workflow is skipped, not refused
- **WHEN** `update` runs and "room-wake.yml" exists without the marker
- **THEN** the gate files are written, the wake workflow is byte-unchanged, and the exit code is `0`

#### Scenario: A foreign gate file refuses the whole update
- **WHEN** `update` runs on a directory holding a stale wake set and a foreign gate workflow
- **THEN** the verb exits `1` naming the gate workflow and every file is byte-unchanged

#### Scenario: Room flag is a usage error
- **WHEN** `shipd copilot update --room` runs
- **THEN** the exit code is `2` and nothing is written
