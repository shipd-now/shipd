## MODIFIED Requirements

### Requirement: Config-show verb
id: config-show-verb
base: b9a5d4b008e6

The status CLI SHALL provide `config-show` printing the resolved layered
configuration: each effective top-level key with the path of the layer that
supplied it (or `default`), the resolved content directory name, and the
workspace root when one is discoverable (or a note that none is). Where the
resolved configuration declares `store_root`, the verb SHALL additionally
print the resolved absolute external content directory path, so a
mis-declared store is inspectable at a glance. Where the resolved workspace
chain carries more than one member, the verb SHALL additionally print the
whole chain in nearest-first order. The verb SHALL additionally print a
`wiki:` line reporting the resolved wiki store: the nearest workspace's
store path when a chain exists, the repo-local fallback path annotated
`(repo-local fallback)` when the chain is empty and the content directory
exists, and `wiki: none` naming the missing prerequisites otherwise.

The verb SHALL always print three further keyed lines carrying the resolved
worktree housekeeping settings — `worktree-sweep:` as `true` or `false`,
`worktree-idle-minutes:`, and `worktree-stale-days:` — whether a layer declared
them or they fell back to their built-in defaults, so the bash worktree helper
reads them through the same seam it already reads `content-dir:` and `store:`
through rather than resolving configuration itself.

The verb SHALL NOT require a discoverable workspace and SHALL exit zero on a
default-only resolution.

#### Scenario: Provenance is printed per key
- **GIVEN** the repo layer declares `valid_themes` and the workspace layer
  declares `workspace`
- **WHEN** `config-show` runs
- **THEN** each key is listed with the config file path that supplied it

#### Scenario: Nested chain is printed
- **GIVEN** nested workspaces enclosing the repository
- **WHEN** `config-show` runs
- **THEN** the workspace root is the nearest one and the chain lists both
  roots, nearest first

#### Scenario: Defaults-only still succeeds
- **WHEN** `config-show` runs where no `.shipd-config.json` exists in any layer
- **THEN** the content directory prints as `.shipd`, keys show `default`, and
  the exit code is zero

#### Scenario: External store path is printed
- **GIVEN** a resolved configuration declaring `store_root`
- **WHEN** `config-show` runs
- **THEN** the output includes the resolved absolute external content
  directory path

#### Scenario: Wiki line reports the resolved store
- **WHEN** `config-show` runs in a workspace repo, in a bare repo with a
  content directory, and in an uninitialized directory
- **THEN** the `wiki:` line names the workspace store, the fallback path
  with `(repo-local fallback)`, and `none`, respectively

#### Scenario: Worktree lines print on a default-only resolution
- **WHEN** `config-show` runs where no layer declares any worktree key
- **THEN** the output carries `worktree-sweep: true`,
  `worktree-idle-minutes: 30`, and `worktree-stale-days: 7`

#### Scenario: Worktree lines carry a declared value
- **GIVEN** a repo layer declaring `worktree_sweep` false and
  `worktree_stale_days` as 14
- **WHEN** `config-show` runs
- **THEN** the output carries `worktree-sweep: false` and
  `worktree-stale-days: 14`
