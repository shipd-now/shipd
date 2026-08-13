## ADDED Requirements

### Requirement: Personal memory store key
id: memory-store-key

The configuration MAY declare `memory_dir`: a non-empty string path (with `~`
expansion) naming the personal memory store's root directory, resolved through
the standard layered per-key merge. The expanded value SHALL be an absolute
path; if the declared value is not a non-empty string or does not expand to an
absolute path, then the consuming verb SHALL exit non-zero with an error naming
`memory_dir`. Unlike the base store key, `memory_dir` SHALL default to
`~/.shipd-memory` when undeclared, so resolution always yields a store root. The
store directory itself SHALL be `<memory_dir>/wiki`, mirroring the workspace
store's `wiki` directory so the same grammar and engine apply.

#### Scenario: Declared key resolves expanded
- **GIVEN** a config layer declaring `memory_dir: "~/personal/shipd-memory"`
- **WHEN** the key is resolved
- **THEN** the store directory is the absolute expanded path
  `<home>/personal/shipd-memory/wiki`

#### Scenario: Undeclared key defaults
- **WHEN** no layer declares `memory_dir`
- **THEN** resolution yields the store root `~/.shipd-memory` (expanded) and its
  store directory `~/.shipd-memory/wiki`, with no error raised

#### Scenario: Malformed value errors
- **WHEN** `memory_dir` is declared as a relative path, an empty string, or a
  non-string and a consuming verb runs
- **THEN** the verb exits non-zero with an error naming `memory_dir`
