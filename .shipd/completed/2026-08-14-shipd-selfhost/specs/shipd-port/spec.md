## ADDED Requirements

### Requirement: A change completes the full lifecycle inside shipd
id: selfhost-full-lifecycle

A change SHALL be planned, built, verified, merged, and archived entirely with
the shipd plugin's own skills and engine scripts, in a worktree created by
shipd's own worktree script, without invoking any shipd skill or script.

#### Scenario: The change is planned and built under the s namespace
- **WHEN** a change is planned and built in the shipd repository using the shipd
  plugin's own artifacts and engine scripts
- **THEN** the change directory is created under shipd's content directory and
  its tasks are completed

#### Scenario: The merge updates the master library and the archive
- **WHEN** the change is merged with shipd's merge engine
- **THEN** its delta requirement appears in shipd's master library and its change
  directory appears under the archive with a dated name

#### Scenario: No shipd script is invoked
- **WHEN** the commands run during the lifecycle are reviewed
- **THEN** none of them resolves to a path inside the shipd repository or to
  an `/s:` skill

#### Scenario: The epic re-derives from shipd's own library
- **WHEN** the `shipd-port` epic's status is re-derived in shipd with the ported
  status CLI
- **THEN** the derivation reads shipd's own library and reports a status
  consistent with the members archived there
