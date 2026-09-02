## MODIFIED Requirements

### Requirement: Config-show verb
id: config-show-verb
base: 1e8d083d6069

The status CLI SHALL provide `config-show` printing the resolved layered
configuration: each effective top-level key with the path of the layer that
supplied it (or `default`), the resolved content directory name, and the
workspace root when one is discoverable (or a note that none is). Where the
resolved configuration declares `store_root`, the verb SHALL additionally
print the resolved absolute external content directory path, so a
mis-declared store is inspectable at a glance. Where the resolved workspace
chain carries more than one member, the verb SHALL additionally print the
whole chain in nearest-first order. The verb SHALL NOT require a
discoverable workspace and SHALL exit zero on a default-only resolution.

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
