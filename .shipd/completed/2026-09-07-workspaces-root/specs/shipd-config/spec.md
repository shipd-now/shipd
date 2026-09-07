## ADDED Requirements

### Requirement: Workspaces root key
id: workspaces-root-key

The configuration MAY declare `workspaces_root`: a non-empty string path (with
`~` expansion) naming the mandated parent directory under which job workspaces
are created and cloned, resolved through the standard layered per-key merge.
The expanded value SHALL be an absolute path; if the declared value is not a
non-empty string or does not expand to an absolute path, then the consuming
verb SHALL exit non-zero with an error naming `workspaces_root`. When the key
is undeclared, there SHALL be no mandated root and every consuming surface
SHALL behave exactly as it does without the key.

#### Scenario: Declared key resolves expanded
- **GIVEN** a config layer declaring `workspaces_root: "~/workflows"`
- **WHEN** the key is resolved
- **THEN** the result is the absolute expanded path to that directory

#### Scenario: Undeclared key means no mandated root
- **WHEN** no layer declares `workspaces_root`
- **THEN** resolution yields no root and no error is raised

#### Scenario: Malformed value errors
- **WHEN** `workspaces_root` is declared as a relative path, an empty string,
  or a non-string and a consuming verb runs
- **THEN** the verb exits non-zero with an error naming `workspaces_root`

## MODIFIED Requirements

### Requirement: Config sample coverage
id: config-sample-coverage
base: ad382ded1b64

The engine SHALL define the recognized top-level configuration keys in a
single registry constant in `spec_common.py`
(`autonomous-pipeline`, `build`, `clone_sources`, `completed_retention_days`,
`dir`, `guardrails`, `memory_dir`, `post-worktree-scripts`, `pr-mode`,
`store_root`, `valid_themes`, `wiki_base`, `workspace`, `workspaces_root`).
The copyable config
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
