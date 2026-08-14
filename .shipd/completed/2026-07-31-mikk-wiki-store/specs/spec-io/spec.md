## ADDED Requirements

### Requirement: Staged wiki emission
id: wiki-emission

The emit engine SHALL provide a `wiki` subcommand installing a staged store
subset — `wiki/<slug>.md` pages, `index.md`, `log.md`, `queue.md`, and
`sources/<file>` additions — into the workspace wiki: it SHALL back up the
affected store files, install the staged set (overwriting existing pages and
top-level files), validate the resulting whole store with the wiki lint, and
if any finding is reported, then it SHALL restore the backup and exit non-zero
so an invalid store state never lands. If a staged `sources/` file already
exists in the store, then the emission SHALL be refused before any install
(sources are immutable).

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
