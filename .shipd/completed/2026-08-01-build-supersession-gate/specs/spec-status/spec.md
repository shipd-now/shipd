## ADDED Requirements

### Requirement: Check-base verb
id: check-base-verb

The status CLI SHALL provide `check-base [change]` comparing the change's
delta specs against the current master library without writing anything,
reporting one finding line per mismatched entry: `stale-base` when a
MODIFIED/REMOVED entry's `base:` hash differs from the master requirement's
current content hash (computed with the same content-hash function the merge
engine uses, and reporting the expected and actual hashes); `missing-master`
when a MODIFIED/REMOVED entry's id — or the capability's master spec itself —
does not exist; and `id-collision` when an ADDED entry's id already exists in
the master. The verb SHALL print a summary line after the findings, SHALL
exit 0 when no finding exists, and SHALL exit 4 when at least one finding
exists — distinct from general errors and guard refusals. Where `[change]` is
omitted, the verb SHALL default to the currently selected change and SHALL
exit non-zero with an error when none is selected. The verb SHALL NOT invoke
git, a model, or the network.

#### Scenario: Clean change exits zero
- **GIVEN** a planned change whose MODIFIED entries all carry `base:` hashes
  matching the current masters and whose ADDED ids are all new
- **WHEN** `check-base <change>` runs
- **THEN** the summary reports clean, no finding lines print, and the exit
  code is 0

#### Scenario: Stale base is reported
- **GIVEN** a planned change with a MODIFIED entry whose `base:` hash no
  longer matches the master requirement's content hash
- **WHEN** `check-base <change>` runs
- **THEN** a `stale-base` line prints naming the capability, the id, and the
  expected and actual hashes, and the exit code is 4

#### Scenario: Added id collision is reported
- **GIVEN** a planned change with an ADDED entry whose id already exists in
  that capability's master spec
- **WHEN** `check-base <change>` runs
- **THEN** an `id-collision` line prints naming the capability and id, and
  the exit code is 4

#### Scenario: Missing master is reported
- **GIVEN** a planned change with a MODIFIED entry whose id exists in no
  master requirement
- **WHEN** `check-base <change>` runs
- **THEN** a `missing-master` line prints naming the capability and id, and
  the exit code is 4

#### Scenario: The verb never writes
- **WHEN** `check-base <change>` runs with any mix of findings
- **THEN** no file under the content directory or the change directory is
  modified
