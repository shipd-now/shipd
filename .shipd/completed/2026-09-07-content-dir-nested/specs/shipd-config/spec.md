## MODIFIED Requirements

### Requirement: Configurable content directory
id: content-dir-key
base: d4bc5df3bccd

The engine SHALL resolve the content directory location from the resolved `dir`
key, defaulting to `.shipd` when no layer declares it. The value SHALL be a
relative path of one or more non-empty `/`-separated components. If the value
is not a non-empty string, is an absolute path, contains a backslash, or
contains a component that is empty, `.`, or `..`, then the engine SHALL raise
an error naming the offending value. The engine SHALL resolve the location by
joining the value's components onto the repository root with native
separators. The config filename `.shipd-config.json` itself SHALL NOT be
configurable or affected by `dir`. Where the resolved configuration declares
`store_root`, the external store-root resolution SHALL govern the content
directory's location instead, and the `dir` key SHALL NOT apply.

#### Scenario: Default content directory
- **WHEN** no layer declares `dir`
- **THEN** repo content resolves under `.shipd/` (e.g. `.shipd/planned/<change>/`)

#### Scenario: Renamed content directory
- **GIVEN** the repo's config declares `dir: "specs"`
- **WHEN** a change's directory is resolved
- **THEN** it resolves under `specs/planned/<change>/`

#### Scenario: Nested content directory
- **GIVEN** the repo's config declares `dir: ".agents/specs/.shipd"`
- **WHEN** a change's directory is resolved and `config-show` runs
- **THEN** the change resolves under `.agents/specs/.shipd/planned/<change>/`
  and `config-show` prints `content-dir: .agents/specs/.shipd`

#### Scenario: Escaping or absolute dir is rejected
- **WHEN** a layer declares `dir: "../specs"` or `dir: "/abs/specs"`
- **THEN** resolution fails with an error naming the invalid value

#### Scenario: Empty component is rejected
- **WHEN** a layer declares `dir: "a//b"`
- **THEN** resolution fails with an error naming the invalid value

#### Scenario: Store root supersedes dir
- **GIVEN** a config declaring both `dir: "specs"` and a `store_root`
- **WHEN** the content directory is resolved
- **THEN** it resolves inside the external store with no `specs` component
