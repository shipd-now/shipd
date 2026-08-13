## ADDED Requirements

### Requirement: Config file discovery
id: config-file-discovery

The engine SHALL resolve configuration from files named exactly
`.shipd-config.json`, collected by walking from a start directory
parent-by-parent to the filesystem root, appending `~/.shipd-config.json` as the
outermost layer when the home directory is not already in the walked chain,
with built-in defaults beneath all files. A directory with no config file
SHALL be skipped silently. If a config file exists but is not parseable JSON
or its top level is not a JSON object, then the engine SHALL raise an error
naming that file's path.

#### Scenario: Repo and workspace layers both load
- **GIVEN** `.shipd-config.json` files at `/ws/repo/` and `/ws/`
- **WHEN** configuration is resolved from `/ws/repo`
- **THEN** both files participate as layers, `/ws/repo`'s nearest

#### Scenario: No config files means defaults
- **WHEN** configuration is resolved where no ancestor and not the home
  directory carries `.shipd-config.json`
- **THEN** built-in defaults apply and no error is raised

#### Scenario: Malformed config errors with its path
- **WHEN** a `.shipd-config.json` in the chain contains invalid JSON
- **THEN** resolution fails with an error naming that file's path

### Requirement: Layered per-key merge
id: layered-key-merge

When more than one config file participates in resolution, the engine SHALL
merge them at the top level per key: the nearest layer declaring a key wins
that key wholesale, values SHALL NOT be deep-merged across layers, and
unrecognized keys SHALL be tolerated and preserved.

#### Scenario: Nearest layer wins a contested key
- **GIVEN** the repo layer declares `dir: "specs"` and the workspace layer
  declares `dir: ".shipd"`
- **WHEN** configuration is resolved from the repo
- **THEN** the effective `dir` is `specs`

#### Scenario: Distinct keys combine across layers
- **GIVEN** the repo layer declares only `valid_themes` and the home layer
  declares only `build`
- **WHEN** configuration is resolved from the repo
- **THEN** the effective config carries both keys

#### Scenario: Unknown keys are preserved
- **WHEN** a layer declares an unrecognized `future-key`
- **THEN** resolution succeeds and the key is present in the result

### Requirement: Configurable content directory
id: content-dir-key

The engine SHALL resolve the content directory name from the resolved `dir`
key, defaulting to `.am` when no layer declares it. The value SHALL be a
single path component (no path separators); a violating value SHALL be an
error. The config filename `.shipd-config.json` itself SHALL NOT be
configurable or affected by `dir`.

#### Scenario: Default content directory
- **WHEN** no layer declares `dir`
- **THEN** repo content resolves under `.shipd/` (e.g. `.shipd/planned/<change>/`)

#### Scenario: Renamed content directory
- **GIVEN** the repo's config declares `dir: "specs"`
- **WHEN** a change's directory is resolved
- **THEN** it resolves under `specs/planned/<change>/`

#### Scenario: Separator in dir is rejected
- **WHEN** a layer declares `dir: "nested/specs"`
- **THEN** resolution fails with an error naming the invalid value

### Requirement: Spec library path notation
id: spec-library-path-notation

Literal `am/` path prefixes appearing in master-library requirement text
SHALL be read as denoting the configured content directory (default `.am`),
so requirements that reference canonical locations incidentally remain
correct when the directory is renamed.

#### Scenario: Notation follows the configured name
- **GIVEN** a repo whose config declares `dir: "specs"`
- **WHEN** a requirement elsewhere references `am/planned/<change>/`
- **THEN** tooling and readers resolve it as `specs/planned/<change>/`
