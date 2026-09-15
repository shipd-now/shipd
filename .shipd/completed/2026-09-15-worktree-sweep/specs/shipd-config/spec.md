## ADDED Requirements

### Requirement: Worktree sweep config keys
id: worktree-sweep-keys

The engine SHALL recognize three top-level config keys governing worktree
housekeeping, each resolved through the layered loader like every other key and
each carrying a built-in default:

- `worktree_sweep` — a boolean gating whether the engine's worktree create path
  runs the sweep. Default `true`.
- `worktree_idle_minutes` — a non-negative integer supplying the idle window the
  `remove` verb's recent-activity guard uses. Default `30`; `0` disables that
  guard.
- `worktree_stale_days` — a positive integer supplying the window beyond which
  the sweep reports an unmerged worktree as stale. Default `7`.

For each of the two integer keys, the engine SHALL resolve its effective value
in precedence order: the matching environment variable
(`SHIPD_WORKTREE_IDLE_MINUTES`, `SHIPD_WORKTREE_STALE_DAYS`) where it is set to
a valid value, then the resolved config layer, then the built-in default. If a
declared value is not of the key's stated type or violates its stated range,
then the engine SHALL treat the key as undeclared and fall back to the built-in
default rather than raising, mirroring the `completed_retention_days` key's
tolerance.

Each of the three keys SHALL appear in the engine's registry of recognized
top-level keys and SHALL be documented in the plugin's copyable config
reference, so the existing agreement check over the two covers them.

#### Scenario: A config layer supplies the stale window
- **GIVEN** a repo layer declaring `worktree_stale_days` as 14 and no
  `SHIPD_WORKTREE_STALE_DAYS` in the environment
- **WHEN** the sweep resolves its stale window
- **THEN** the effective window is 14 days

#### Scenario: The environment overrides the config layer
- **GIVEN** the same layer and `SHIPD_WORKTREE_STALE_DAYS` set to 2
- **WHEN** the sweep resolves its stale window
- **THEN** the effective window is 2 days

#### Scenario: The idle guard reads its window from a layer
- **GIVEN** a repo layer declaring `worktree_idle_minutes` as 0 and no
  `SHIPD_WORKTREE_IDLE_MINUTES` in the environment
- **WHEN** `remove` runs against a dirty worktree whose files were just written
- **THEN** no reason naming the idle window is printed

#### Scenario: A malformed value falls back to the default
- **GIVEN** a repo layer declaring `worktree_stale_days` as the string "soon"
- **WHEN** the sweep resolves its stale window
- **THEN** the effective window is 7 days and no error is raised

#### Scenario: The sweep gate is declared false
- **GIVEN** a resolved configuration declaring `worktree_sweep` as false
- **WHEN** the engine's worktree create path runs
- **THEN** no sweep runs

#### Scenario: Every key is registered and documented
- **WHEN** the config-sample agreement check runs
- **THEN** `worktree_sweep`, `worktree_idle_minutes`, and `worktree_stale_days`
  each appear in both the recognized-keys registry and the copyable config
  reference
