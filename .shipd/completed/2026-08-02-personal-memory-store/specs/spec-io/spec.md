## MODIFIED Requirements

### Requirement: Staged wiki emission
id: wiki-emission
base: c10ed30350d6

The emit engine SHALL provide a `wiki` subcommand installing a staged store
subset — `wiki/<slug>.md` pages, `index.md`, `log.md`, `queue.md`, and
`sources/<file>` additions — into the workspace wiki: it SHALL back up the
affected store files, install the staged set (overwriting existing pages and
top-level files), validate the resulting whole store with the wiki lint, and
if any finding is reported, then it SHALL restore the backup and exit non-zero
so an invalid store state never lands. If a staged `sources/` file already
exists in the store, then the emission SHALL be refused before any install
(sources are immutable). The `wiki` subcommand SHALL accept a `--personal` flag:
when set, it SHALL install into the personal memory store at `<memory_dir>/wiki`
(default `~/.shipd-memory/wiki`), resolved by fixed path and bypassing workspace
discovery, instead of the workspace store, with the identical backup, lint, and
restore semantics.

#### Scenario: Page install with index update
- **WHEN** `spec_emit.py wiki --from <staging>` stages a new page and an
  `index.md` cataloging it
- **THEN** both land in the store and the command reports the install and
  exits zero

#### Scenario: Invalid result rolls back
- **WHEN** the staged set would leave a dead wikilink or an unindexed page
- **THEN** the store's prior content is restored byte-for-byte and the command
  exits non-zero printing the findings

#### Scenario: Source overwrite refused
- **WHEN** the staging dir holds `sources/notes.md` and the store already has
  `sources/notes.md`
- **THEN** nothing is installed and the command exits non-zero citing source
  immutability

#### Scenario: Personal flag installs into the memory store
- **WHEN** `spec_emit.py wiki --from <staging> --personal` runs
- **THEN** the staged set installs into `<memory_dir>/wiki` (default
  `~/.shipd-memory/wiki`) by fixed path, with the same lint and rollback
  guarantees, and the workspace store is untouched
