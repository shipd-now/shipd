## MODIFIED Requirements

### Requirement: Pipeline entry validation
id: pipeline-entry-validation
base: 4daa17c24558

`resolve_pipeline(root)` SHALL validate every declared entry against the
stdlib-only, table-driven schema in the engine's `pipeline_schema` module,
imported lazily and only when a layer declares the `autonomous-pipeline`
key — the no-key default resolution SHALL never import the module. The
module SHALL import no third-party package, so resolution SHALL never
depend on one and SHALL never emit an install hint. Validation SHALL
reject, naming the offending entry by index
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

#### Scenario: Validation runs with no third-party package installed
- **GIVEN** every third-party distribution is unimportable
- **WHEN** a config layer declares any `autonomous-pipeline` list
- **THEN** validation runs in full and resolution succeeds or fails on the
  entries' own merits, and no error names a package or an install hint

#### Scenario: Strict types are rejected without coercion
- **WHEN** a declared entry reads `{"stage": "build", "parallelism": "2"}`
  and another reads `{"stage": "plan", "skip": 1}`
- **THEN** resolution fails naming each offending entry by index and its
  offending key, coercing neither value

### Requirement: Named pipeline presets
id: pipeline-presets
base: a64a81cf0fec

The engine SHALL define the preset names `default`, `eco`, and `basic` in a
stdlib names constant, with the preset entry table shipped as data in the
`pipeline_schema` module keyed by exactly those names. When the
`autonomous-pipeline` value is a string, resolution SHALL first check it
against the names constant — an unknown name SHALL fail naming the value,
the supplying config file, and the known preset names. The name `default`
SHALL resolve to the same entries as the
absent key — every registry stage bare, in canonical order — without
importing any third-party package. Every other known name SHALL expand its
table entries through the same validation as a user-declared list. The
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
- **GIVEN** a repo config declaring `{"autonomous-pipeline": "eco"}`
- **WHEN** the pipeline is resolved
- **THEN** the effective entries are the eco table — research and epic
  skipped, plan on `session`, gate with `autopilot.attempts` 1, build with
  `validator` false, `subagent_model` `tier-two-below`, `telemetry` false,
  review with `model` `tier-below` and `disposition` `high-only` — and the
  provenance reads `preset:eco` plus the repo config path

#### Scenario: Default preset needs no third-party package
- **WHEN** a config layer declares `{"autonomous-pipeline": "default"}`
- **THEN** resolution succeeds with every registry stage bare in canonical
  order and provenance `preset:default` plus the config path

#### Scenario: Unknown preset lists the known names
- **WHEN** a config layer declares `{"autonomous-pipeline": "ecoo"}`
- **THEN** resolution fails naming `ecoo`, the supplying config file, and
  the known presets `basic`, `default`, and `eco`, naming no package

#### Scenario: Every preset expands without a third-party package
- **GIVEN** every third-party distribution is unimportable
- **WHEN** a config layer declares `{"autonomous-pipeline": "eco"}`
- **THEN** resolution succeeds with the eco table and provenance
  `preset:eco` plus the config path

#### Scenario: Preset table stays valid against the schema
- **WHEN** the engine test suite runs
- **THEN** every preset's entry list passes entry validation and the
  canonical-order check, and the table's keys equal the stdlib names
  constant

### Requirement: Pipeline grammar documentation
id: pipeline-grammar-docs
base: 11f78f4d1d71

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
resolved entries); and the rule that validation is stdlib-only, so a
declared entry list and every preset resolve with no third-party package
installed. The copyable config example JSON shipped in
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
