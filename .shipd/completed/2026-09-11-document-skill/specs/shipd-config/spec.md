# shipd-config

## ADDED Requirements

### Requirement: Voice key
id: voice-key

The engine SHALL recognize a top-level `voice` boolean in the layered
configuration, resolved nearest-layer-wins like every other key, defaulting
to true when no layer declares it. The key SHALL gate the plugin's
`SessionStart` voice-digest hook and nothing else.

#### Scenario: The key is a registry member
- **WHEN** `spec_common.py`'s recognized-keys registry constant is read
- **THEN** it contains `voice`

#### Scenario: Nearest layer wins
- **WHEN** an outer layer declares `voice: false` and a nearer layer
  declares `voice: true`
- **THEN** the resolved value is true

## MODIFIED Requirements

### Requirement: Config sample coverage
id: config-sample-coverage
base: ec378bb72368

The engine SHALL define the recognized top-level configuration keys in a
single registry constant in `spec_common.py`
(`autonomous-pipeline`, `build`, `clone_sources`, `completed_retention_days`,
`dir`, `guardrails`, `memory_dir`, `post-worktree-scripts`, `pr-mode`,
`store_root`, `valid_themes`, `voice`, `wiki_base`, `workspace`,
`workspaces_root`).
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
- **THEN** the two sets are equal, and `voice` is among them with a comment
  stating it gates the session-start voice digest and defaults to true

#### Scenario: Verbatim copy changes nothing
- **WHEN** the example file is copied as `.shipd-config.json` and the
  configuration is resolved
- **THEN** every resolved value equals the engine's built-in default
