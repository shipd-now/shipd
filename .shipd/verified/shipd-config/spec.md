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
key, defaulting to `.shipd` when no layer declares it. The value SHALL be a
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

### Requirement: Spec-library path notation
id: spec-library-path-notation

Literal `.shipd/` path prefixes appearing in master-library requirement text
SHALL be read as denoting the configured content directory (default `.shipd`),
so requirements that reference canonical locations incidentally remain
correct when the directory is renamed. The retired `am/` prefix notation
SHALL no longer appear in master-library requirement text.

#### Scenario: Notation follows the configured name
- **GIVEN** a repo whose config declares `dir: "specs"`
- **WHEN** a requirement elsewhere references `.shipd/planned/<change>/`
- **THEN** tooling and readers resolve it as `specs/planned/<change>/`

#### Scenario: No retired prefix survives in the library
- **WHEN** the master library's requirement texts are scanned for the
  retired `am/` path prefix
- **THEN** no occurrence remains outside the `shipd-port` capability's
  deliberate legacy examples

### Requirement: Autonomous-pipeline config key
id: autonomous-pipeline-key

The resolved configuration MAY carry an `autonomous-pipeline` key holding
either an ordered JSON list that defines the delivery pipeline or a string
naming a built-in preset. Each list entry SHALL be exactly one of:
`{"stage": "<name>"}` running a registry stage as built in;
`{"stage": "<name>", "skip": true}` explicitly skipping it;
`{"stage": "<name>", "tools": [...]}` binding additional tools to it;
`{"stage": "<name>", "replace": {...}}` substituting its implementation; or
`{"custom": "<kebab-name>", "command": "<command>"}` inserting a custom
step at that list position. A stage entry MAY additionally carry the typed
per-stage options defined by the pipeline stage options requirement, and
any stage or custom entry MAY carry an `autopilot` options object. A
declared list is wholesale — stages absent from it do not run, and
such omission SHALL be valid, including for gates (declaring the key is the
required explicitness). A string value SHALL resolve through the named
pipeline presets requirement; a preset name and an entry list SHALL never
combine — the key holds one or the other. If the key's value is neither a
list nor a string, then resolution SHALL fail with an error naming the key
and the accepted forms. When no layer declares the key, the pipeline SHALL
be the built-in default: every registry stage in canonical order with no
skips, replacements, or bindings — resolved without importing any
third-party package. The key SHALL merge nearest-wins-wholesale like every
top-level key.

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

#### Scenario: Typed options ride a declared entry
- **WHEN** a declared pipeline carries
  `{"stage": "build", "validator": false, "subagent_model": "tier-below"}`
- **THEN** the pipeline resolves and the effective build entry carries
  exactly those declared option keys

#### Scenario: Non-list non-string value is rejected
- **WHEN** a config layer declares `"autonomous-pipeline": 7`
- **THEN** resolution fails with an error naming the key and stating the
  value must be a JSON list or a preset name string

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

`resolve_pipeline(root)` SHALL validate every declared entry against
pydantic models defined in the engine's `pipeline_schema` module, imported
lazily and only when a layer declares the `autonomous-pipeline` key — the
no-key default resolution SHALL never import the module. If a pipeline is
declared and pydantic is not importable, then resolution SHALL fail with an
error naming pydantic, the supplying config file, and the
`pip install -r requirements.txt` remedy — never falling back to weaker
validation. Validation SHALL reject, naming the offending entry by index
and content and reporting every offending entry (not only the first): an
unknown `stage` name; an entry matching none of the declared forms; any
key not defined for its entry form (unknown keys are forbidden); `tools`
or `replace` structures missing a `fallback` or carrying one other than
`builtin` or `skip`; a `replace` lacking both `command` and `tool`; a
`custom` entry whose name is not a kebab-case slug or whose `command` is
missing; `skip` combined with any other field beyond `stage`; and
option values outside their declared types and bounds. On success it SHALL
return the ordered effective entries as plain dicts carrying exactly the
keys each entry declared, together with the provenance of the key (the
supplying config file path, or the default), preserving the canonical
relative order check for built-in stages.

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

#### Scenario: Unknown keys are rejected
- **WHEN** a declared entry reads `{"stage": "plan", "retries": 2}`
- **THEN** resolution fails naming entry 0 and the unknown `retries` key

#### Scenario: Declared pipeline without pydantic fails closed
- **GIVEN** pydantic is not importable
- **WHEN** a config layer declares any `autonomous-pipeline` list
- **THEN** resolution fails with an error naming pydantic and
  `pip install -r requirements.txt`, and no partial validation runs

#### Scenario: Default resolution needs no pydantic
- **GIVEN** pydantic is not importable
- **WHEN** no layer declares the key and the pipeline is resolved
- **THEN** the full default resolves successfully

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

### Requirement: Pipeline stage options
id: pipeline-stage-options

The pipeline entry schema SHALL define these typed options. Every stage
entry MAY carry `model`: a non-empty string that is either a symbolic tier
— `session`, `tier-below`, or `tier-two-below`, exported by the schema
module as the symbolic-tier constant — or a concrete model id (any other
non-empty string; the set of concrete ids is open). The `build` stage
additionally accepts `subagent_model` (same tier type), `validator`
(boolean, default true), `telemetry` (boolean, default true), and
`parallelism` (integer >= 1). The `review` stage additionally accepts
`disposition`: one of `all`, `high-only`, or `none`, default `all`. Any
stage or custom entry MAY carry `autopilot`: an object accepting
`attempts` (integer >= 1, default 3), `timeout` (integer > 0), and
`max_resumes` (integer >= 0), with unknown keys forbidden. Defaults SHALL
be schema-declared, not injected into resolved entries: a resolved entry
carries exactly the keys the user declared. If `skip` is true, then the
entry SHALL carry no other field beyond `stage` — options on a skipped
stage are an error.

#### Scenario: Build options are accepted and carried
- **WHEN** a declared pipeline carries `{"stage": "build",
  "validator": false, "telemetry": false, "parallelism": 2,
  "subagent_model": "tier-two-below"}`
- **THEN** the pipeline resolves and the effective entry carries exactly
  those declared keys and values

#### Scenario: Undeclared defaults are not injected
- **WHEN** a declared pipeline carries the bare entry `{"stage": "build"}`
- **THEN** the resolved entry is exactly `{"stage": "build"}` with no
  `validator`, `telemetry`, or other default keys added

#### Scenario: Disposition outside the closed set is rejected
- **WHEN** a declared review entry carries `"disposition": "medium-up"`
- **THEN** resolution fails naming the entry and the invalid value

#### Scenario: Autopilot options are bounded
- **WHEN** a declared entry carries `"autopilot": {"attempts": 0}`
- **THEN** resolution fails naming the entry and the out-of-range value

#### Scenario: Options on a skipped stage are an error
- **WHEN** a declared entry reads `{"stage": "review", "skip": true,
  "model": "tier-below"}`
- **THEN** resolution fails naming the entry and the skip exclusivity rule

### Requirement: Named pipeline presets
id: pipeline-presets

The engine SHALL define the preset names `default`, `eco`, and `basic` in a
stdlib names constant, with the preset entry table shipped as data in the
`pipeline_schema` module keyed by exactly those names. When the
`autonomous-pipeline` value is a string, resolution SHALL first check it
against the names constant — an unknown name SHALL fail naming the value,
the supplying config file, and the known preset names, without requiring
pydantic. The name `default` SHALL resolve to the same entries as the
absent key — every registry stage bare, in canonical order — without
importing any third-party package. Every other known name SHALL expand its
table entries through the same pydantic validation as a user-declared list,
including its fail-closed behavior when pydantic is not importable. The
provenance of a preset-resolved pipeline SHALL be
`preset:<name> (<supplying-config-path>)`. The `eco` preset SHALL be:
research and epic skipped, plan `model` `session`, gate
`autopilot.attempts` 1, build `validator` false with `subagent_model`
`tier-two-below` and `telemetry` false, review `model` `tier-below` with
`disposition` `high-only`. The `basic` preset SHALL be: research and epic
skipped, plan `model` `session`, gate skipped, build `validator` false with
`subagent_model` `tier-below`, review `model` `tier-below` with
`disposition` `high-only`. Every shipped preset SHALL keep the plan stage
on `session` and SHALL include an unskipped review stage.

#### Scenario: Eco is a one-line opt-in
- **GIVEN** a repo config declaring `{"autonomous-pipeline": "eco"}` and
  pydantic importable
- **WHEN** the pipeline is resolved
- **THEN** the effective entries are the eco table — research and epic
  skipped, plan on `session`, gate with `autopilot.attempts` 1, build with
  `validator` false, `subagent_model` `tier-two-below`, `telemetry` false,
  review with `model` `tier-below` and `disposition` `high-only` — and the
  provenance reads `preset:eco` plus the repo config path

#### Scenario: Default preset needs no pydantic
- **GIVEN** pydantic is not importable
- **WHEN** a config layer declares `{"autonomous-pipeline": "default"}`
- **THEN** resolution succeeds with every registry stage bare in canonical
  order and provenance `preset:default` plus the config path

#### Scenario: Unknown preset lists the known names
- **GIVEN** pydantic is not importable
- **WHEN** a config layer declares `{"autonomous-pipeline": "ecoo"}`
- **THEN** resolution fails naming `ecoo`, the supplying config file, and
  the known presets `basic`, `default`, and `eco` — not the pydantic
  install hint

#### Scenario: Non-default preset fails closed without pydantic
- **GIVEN** pydantic is not importable
- **WHEN** a config layer declares `{"autonomous-pipeline": "eco"}`
- **THEN** resolution fails with the error naming pydantic and
  `pip install -r requirements.txt`

#### Scenario: Preset table stays valid against the schema
- **WHEN** the pydantic-dependent test suite runs
- **THEN** every preset's entry list passes entry validation and the
  canonical-order check, and the table's keys equal the stdlib names
  constant

### Requirement: Pipeline grammar documentation
id: pipeline-grammar-docs

The content directory's `README.md` (the format authority) SHALL document
the full shipped `autonomous-pipeline` grammar: the five entry forms; the
typed per-stage options (`model` as a symbolic tier — `session`,
`tier-below`, `tier-two-below` — or a concrete model id; `build`'s
`subagent_model`, `validator`, `telemetry`, and `parallelism`; `review`'s
`disposition` with its closed `all`/`high-only`/`none` set); the
`autopilot` options namespace (`attempts`, `timeout`, `max_resumes`) on any
stage or custom entry; the exclusivity rule that `skip` may only be `true`
when present and excludes every other field on the entry, with `tools` and
`replace` mutually exclusive; strict validation (unknown keys and wrongly
typed values rejected, defaults schema-declared and never injected into
resolved entries); and the rule that a declared entry list — and every
preset but `default` — requires pydantic and fails closed with an install
hint when it is not importable. The copyable config example JSON shipped in
the plugin's build references SHALL name the optional `autonomous-pipeline`
key with a pointer to that grammar, without actively declaring a pipeline.

#### Scenario: Eco expansion is hand-authorable from the README alone
- **WHEN** a reader compares `pipeline-show --expand eco`'s entries against
  the format authority's pipeline section
- **THEN** every key those entries carry (`skip`, `model`, `autopilot`,
  `validator`, `subagent_model`, `telemetry`, `disposition`) is documented
  there with its type and allowed values

#### Scenario: Skip exclusivity is stated correctly
- **WHEN** a reader consults the format authority on combining `skip` with
  other entry fields
- **THEN** it states that `skip` may only be `true` and that a skipped
  entry carries no other field, not merely that `skip`, `tools`, and
  `replace` are mutually exclusive

#### Scenario: Config example points at the key
- **WHEN** a reader opens the copyable config example JSON
- **THEN** it mentions the optional `autonomous-pipeline` key and where its
  grammar lives, while copying the file unchanged declares no pipeline
