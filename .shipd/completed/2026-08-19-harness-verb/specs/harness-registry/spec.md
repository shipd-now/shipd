## MODIFIED Requirements

### Requirement: Harness read verbs
id: harness-read-verbs
base: 30b01ba69905

The `shipd` binary SHALL provide a `harness` verb whose read actions are
read-only: bare or with `list` it SHALL print one line per registry entry;
with `show <id>` it SHALL print every field of that entry; with `--json` it
SHALL instead emit one machine-readable JSON document (the entry list, or
the single entry for `show`). If `show` names an unknown id, then the
binary SHALL print a single `Error: <reason>` line on stderr and exit
nonzero. The `list` and `show` actions SHALL create or modify no files;
the verb's writing actions (`add`, `remove`) are governed by the
`harness-verb` capability.

#### Scenario: List names every harness
- **WHEN** `shipd harness` runs
- **THEN** stdout contains all twelve registry ids and the exit code is 0

#### Scenario: Show prints one entry's data
- **WHEN** `shipd harness show cursor` runs
- **THEN** stdout contains `.cursor/commands/shipd-{command}.md` and the
  entry's dialect, and the exit code is 0

#### Scenario: JSON is machine-readable
- **WHEN** `shipd harness --json` runs
- **THEN** stdout parses as JSON with twelve entries whose ids match `ids()`

#### Scenario: Unknown id is a single-line error
- **WHEN** `shipd harness show no-such-harness` runs
- **THEN** stderr carries a single line beginning `Error: ` and the exit
  code is nonzero

#### Scenario: The read actions write nothing
- **WHEN** `shipd harness` and `shipd harness show cursor` run in a
  temporary directory
- **THEN** the directory's contents are unchanged afterwards
