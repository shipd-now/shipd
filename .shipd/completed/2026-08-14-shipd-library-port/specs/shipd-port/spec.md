## ADDED Requirements

### Requirement: Capability directories are renamed exhaustively
id: library-capability-renames

Every capability directory in the source library whose name matches `am-<name>`
SHALL exist in the ported library as `shipd-<name>`, under the master library and
under every archived change's `specs/` directory. No directory named `am-<name>`
SHALL survive anywhere in the ported library.

#### Scenario: Every prefixed capability has a shipd counterpart
- **WHEN** the source's `am-` prefixed capability directories are enumerated and
  each is looked up in the ported master library under its `shipd-` name
- **THEN** every one of them is found

#### Scenario: No am-prefixed capability directory survives
- **WHEN** the ported library is searched for any directory named `am-<name>`
- **THEN** no match is found

#### Scenario: Unprefixed capabilities are untouched
- **WHEN** a source capability without the `am-` prefix, such as `statusline`, is
  looked up in the ported library
- **THEN** it exists under the same name

### Requirement: Ported library lints clean
id: library-lint-clean

The ported spec library SHALL pass the master-library lint with no findings, so
that no rename left a dangling delta path or requirement cross-reference.

#### Scenario: Master library lint passes
- **WHEN** the ported engine's `spec_lint.py` is run with no change argument
  against the shipd repo
- **THEN** it exits `0`

### Requirement: Ported archive preserves delivery metrics
id: library-metrics-parity

The ported archive SHALL yield the same delivery metrics as the source archive
over the same window, so that no archived change was lost in transit.

#### Scenario: Throughput and cycle time match the source
- **WHEN** the metrics engine is run over the same window in both the source and
  the ported repository
- **THEN** the reported throughput and cycle-time figures are equal

### Requirement: Dropped trees are absent from the ported repo
id: library-dropped-trees

The ported repository SHALL contain no `openspec/` directory and no `.shipd/`
directory, and its configuration file SHALL be named `.shipd-config.json`
carrying the source configuration's keys.

#### Scenario: Frozen archive and vestigial marker are absent
- **WHEN** the shipd repository is checked for `openspec/` and `.shipd/`
- **THEN** neither exists

#### Scenario: Config lands under the shipd name with its keys
- **WHEN** the ported `.shipd-config.json` is read
- **THEN** it exists, no `.shipd-config.json` exists beside it, and its
  `valid_themes` entries match the source configuration's
