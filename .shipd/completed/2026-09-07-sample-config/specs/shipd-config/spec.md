## ADDED Requirements

### Requirement: Config sample coverage
id: config-sample-coverage

The engine SHALL define the recognized top-level configuration keys in a
single registry constant in `spec_common.py`
(`autonomous-pipeline`, `build`, `clone_sources`, `completed_retention_days`,
`dir`, `guardrails`, `memory_dir`, `post-worktree-scripts`, `pr-mode`,
`store_root`, `valid_themes`, `wiki_base`, `workspace`). The copyable config
example JSON shipped in the plugin's build references SHALL be strict JSON
parseable by the stdlib `json` module and SHALL document every registry key —
as a declared key or as a `// <key>` comment entry — each with a comment
stating what the key does and its default, and SHALL document no top-level
key outside the registry (the bare `//` header entry excepted). Copying the
file verbatim as `.shipd-config.json` SHALL declare no effective value that
differs from the engine's built-in defaults.

#### Scenario: Every recognized key is documented
- **WHEN** the test suite compares the registry constant against the keys the
  example documents (declared keys plus the names parsed from `// <key>`
  comment entries)
- **THEN** every registry key is documented in the example

#### Scenario: No unrecognized key is documented
- **WHEN** the same comparison runs in the other direction
- **THEN** the example documents no top-level key absent from the registry,
  the bare `//` header entry excepted

#### Scenario: The sample stays strict JSON
- **WHEN** the example file is parsed with the stdlib `json` module
- **THEN** parsing succeeds and yields a JSON object

#### Scenario: Key constants stay in the registry
- **WHEN** the test suite inspects every module-level `*_KEY` string constant
  in `spec_common`
- **THEN** each constant's value is a member of the registry constant

#### Scenario: Copying the sample changes no behavior
- **WHEN** the example file's declared (non-comment) keys are compared against
  the engine's built-in defaults
- **THEN** every declared value equals its documented default
