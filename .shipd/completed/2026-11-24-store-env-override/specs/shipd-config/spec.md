## MODIFIED Requirements

### Requirement: Store sync config keys
id: store-sync-keys
base: 84cdc4fb4854

The engine SHALL recognize two top-level config keys governing the store's git
behaviour, each resolved through the layered loader like every other key and
each carrying a built-in default:

- `store_autocommit` — a boolean gating whether an engine write into a
  workspace or external store auto-commits. Default `true`.
- `store_sync` — a boolean gating whether the plugin's session-boundary store
  sync hook runs its networked git. Default `true`.

Two environment variables override both keys over every config layer:
`SHIPD_STORE_AUTOCOMMIT` for `store_autocommit` and `SHIPD_STORE_SYNC` for
`store_sync`. The values `0`, `false`, `no`, and `off`, in any letter case,
SHALL force the key false, and `1`, `true`, `yes`, and `on` SHALL force it
true. If the variable is unset or holds any other value, then the engine
SHALL resolve the key from the configuration as before. The override applies
wherever the engine reads the key, the personal memory store included: the
environment belongs to the process owner, not to a repository, so it is not
what that store's own-tree resolution guards against. The `config-show` verb
SHALL print the effective value of each key and mark it as coming from the
environment when an override decided it.

If a declared value is not a boolean, then the engine SHALL treat the key as
undeclared and fall back to the built-in default rather than raising,
mirroring the `worktree_sweep` key's tolerance. Both keys SHALL appear in the
engine's registry of recognized top-level keys and SHALL be documented in the
plugin's copyable config reference, so the existing agreement check over the
two covers them. `store_autocommit` SHALL resolve from the repository the
engine verb was invoked in, never from the store directory, so a repo layer
governs writes into a shared workspace store and an externally redirected one
alike; the personal memory store is the one exception, resolving from its own
tree so no repository can silence a user's memory commits. Neither key SHALL
change the repo-local fallback store's behaviour: while the content directory
resolves in-repo with no `store_root` declared, engine writes SHALL NOT
auto-commit whatever `store_autocommit` resolves to.

#### Scenario: A repo layer gates a workspace-store write
- **GIVEN** a workspace store and a member repo whose own configuration layer
  declares `store_autocommit` as false
- **WHEN** a queue write runs from that repo
- **THEN** the write exits zero and no commit lands in the workspace store

#### Scenario: Both keys default true when undeclared
- **WHEN** the keys are resolved from a repo whose configuration layers
  declare neither
- **THEN** both `store_autocommit` and `store_sync` resolve true

#### Scenario: A declared false disables the auto-commit
- **GIVEN** a resolved configuration declaring `store_autocommit` as false
- **WHEN** an engine verb writes into a git-backed workspace store
- **THEN** the write exits zero and no commit is attempted

#### Scenario: A malformed value falls back to the default
- **GIVEN** a repo layer declaring `store_sync` as the string "yes"
- **WHEN** the key is resolved from that repo
- **THEN** the effective value is true and no error is raised

#### Scenario: Nearest layer wins
- **GIVEN** a workspace layer declaring `store_autocommit` false and a repo
  layer declaring it true
- **WHEN** the key is resolved from the repo
- **THEN** the effective value is true

#### Scenario: Both keys are registered and documented
- **WHEN** the config-sample agreement check runs
- **THEN** `store_autocommit` and `store_sync` each appear in the
  recognized-keys registry and in the copyable config reference

#### Scenario: The in-repo exception survives the key
- **GIVEN** a git-initialized repo with a content directory, no workspace, no
  `store_root`, and no declared `store_autocommit`
- **WHEN** a queue block is appended to the repo-local fallback store
- **THEN** the write exits zero and no commit is made

#### Scenario: The environment forces a key off
- **GIVEN** a repo layer declaring `store_autocommit` and `store_sync` true
- **WHEN** the keys are resolved with `SHIPD_STORE_AUTOCOMMIT` and
  `SHIPD_STORE_SYNC` set to `0`
- **THEN** both resolve false and no commit or push is scheduled

#### Scenario: The environment forces a key on
- **GIVEN** a repo layer declaring `store_sync` false
- **WHEN** the key is resolved with `SHIPD_STORE_SYNC` set to `Yes`
- **THEN** the effective value is true

#### Scenario: An unrecognised environment value falls back to the config
- **GIVEN** a repo layer declaring `store_autocommit` false
- **WHEN** the key is resolved with `SHIPD_STORE_AUTOCOMMIT` set to `maybe`
  or to an empty string
- **THEN** the effective value is false, from the configuration

#### Scenario: Config-show marks an environment override
- **WHEN** `config-show` runs with `SHIPD_STORE_SYNC` set to `off`
- **THEN** it prints `store-sync: false (environment SHIPD_STORE_SYNC)`

