# shipd-config

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

### Requirement: Autonomous-pipeline config key
id: autonomous-pipeline-key

The resolved configuration MAY carry an `autonomous-pipeline` key holding an
ordered JSON list that defines the delivery pipeline. Each entry SHALL be
exactly one of: `{"stage": "<name>"}` running a registry stage as built in;
`{"stage": "<name>", "skip": true}` explicitly skipping it;
`{"stage": "<name>", "tools": [...]}` binding additional tools to it;
`{"stage": "<name>", "replace": {...}}` substituting its implementation; or
`{"custom": "<kebab-name>", "command": "<command>"}` inserting a custom
step at that list position. A declared list SHALL be wholesale — stages
absent from it do not run, and such omission SHALL be valid, including for
gates (declaring the key is the required explicitness). When no layer
declares the key, the pipeline SHALL be the built-in default: every
registry stage in canonical order with no skips, replacements, or
bindings. The key SHALL merge nearest-wins-wholesale like every top-level
key.

#### Scenario: Declared pipeline is wholesale
- **GIVEN** a config layer declaring the key with only `plan`, `gate`, and
  `build` entries
- **WHEN** the pipeline is resolved
- **THEN** exactly those three stages are effective and the omission of
  `review` is not an error

#### Scenario: Absent key yields the full default
- **WHEN** no config layer declares `autonomous-pipeline`
- **THEN** the resolved pipeline is every registry stage in canonical
  order, unskipped and unbound

#### Scenario: Explicit gate skip is legal
- **WHEN** a declared pipeline carries `{"stage": "gate", "skip": true}`
- **THEN** the pipeline resolves with the gate skipped and no error

### Requirement: Pipeline stage registry
id: pipeline-stage-registry

The engine SHALL define the pipeline stage registry as the ordered names
`research`, `epic`, `plan`, `gate`, `build`, `review` in a single data
definition that the resolver and every consumer import. Built-in stages
included in a declared pipeline SHALL preserve this canonical relative
order; `custom` entries MAY appear at any position.

#### Scenario: Canonical order is enforced for built-ins
- **WHEN** a declared pipeline lists `build` before `plan`
- **THEN** resolution fails with an error naming the misordered stages

#### Scenario: Custom steps go anywhere
- **WHEN** a `custom` entry sits between `build` and `review`
- **THEN** resolution succeeds with the custom step at that position

### Requirement: Pipeline entry validation
id: pipeline-entry-validation

`resolve_pipeline(root)` SHALL validate every entry against the closed
grammar and SHALL fail — naming the offending entry by index and content —
on: an unknown `stage` name; an entry matching none of the five forms;
`tools` or `replace` structures missing a `fallback` or carrying one other
than `builtin` or `skip`; a `replace` lacking both `command` and `tool`; a
`custom` entry whose name is not a kebab-case slug or whose `command` is
missing; or `skip` combined with `tools` or `replace`. On success it SHALL
return the ordered effective entries together with the provenance of the
key (the supplying config file path, or the default).

#### Scenario: Missing fallback is an error
- **WHEN** an entry binds `{"name": "mcp:sourcebot"}` with no `fallback`
- **THEN** resolution fails naming that entry and the missing fallback

#### Scenario: Unknown stage is an error
- **WHEN** an entry reads `{"stage": "deploy"}`
- **THEN** resolution fails naming `deploy` and the known registry names

#### Scenario: Valid bindings resolve with provenance
- **GIVEN** a repo-layer pipeline binding Sourcebot to `plan` with
  `"fallback": "builtin"`
- **WHEN** the pipeline is resolved
- **THEN** the effective entries carry the binding and the provenance
  names the repo's config file

### Requirement: Clone sources key
id: clone-sources-key

The configuration MAY declare `clone_sources`: a list of directory path
strings (with `~` expansion) naming where the sync planner probes for local
candidate clones, resolved through the standard layered per-key merge.
When the key is undeclared, the candidate set SHALL be empty — the planner
SHALL never fall back to implicit discovery. If the declared value is not a
list of non-empty strings, then the consuming verb SHALL exit non-zero with
an error naming the key.

#### Scenario: Declared sources feed the planner
- **GIVEN** `clone_sources` declaring a directory that contains a clone
  matching a manifest url
- **WHEN** the sync plan is computed
- **THEN** that clone is used as the member's materialization source

#### Scenario: Undeclared key means no probing
- **GIVEN** no layer declares `clone_sources`
- **WHEN** the sync plan is computed for an absent member with a url
- **THEN** the member's action is `clone` (no local candidate is
  discovered)

#### Scenario: Malformed value errors
- **WHEN** `clone_sources` is declared as a string rather than a list and
  the sync verb runs
- **THEN** the verb exits non-zero naming `clone_sources`

### Requirement: Wiki base store key
id: wiki-base-key

The configuration MAY declare `wiki_base`: a non-empty string path (with `~`
expansion) naming the durable base wiki store directory layered beneath a
workspace's own wiki store, resolved through the standard layered per-key
merge. The expanded value SHALL be an absolute path; if the declared value is
not a non-empty string or does not expand to an absolute path, then the
consuming verb SHALL exit non-zero with an error naming `wiki_base`. When the
key is undeclared, there SHALL be no base layer. When the resolved base equals
the consuming workspace's own store directory, consumers SHALL treat the base
as undeclared.

#### Scenario: Declared key resolves expanded
- **GIVEN** a config layer declaring `wiki_base: "~/projects/.shipd/wiki"`
- **WHEN** the key is resolved
- **THEN** the result is the absolute expanded path to that directory

#### Scenario: Undeclared key means no base layer
- **WHEN** no layer declares `wiki_base`
- **THEN** resolution yields no base store and no error is raised

#### Scenario: Malformed value errors
- **WHEN** `wiki_base` is declared as a relative path, an empty string, or a
  non-string and a consuming verb runs
- **THEN** the verb exits non-zero with an error naming `wiki_base`

#### Scenario: Self-referential base is no base
- **GIVEN** `wiki_base` resolving to the workspace's own store directory
- **WHEN** a consumer resolves the base layer
- **THEN** it behaves as though the key were undeclared

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
