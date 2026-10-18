## MODIFIED Requirements

### Requirement: Model ladder key
id: model-ladder-key
base: 0721881bc55e
Dropped: A declared ladder is read
Dropped: An absent key uses the default
Dropped: A malformed ladder is refused

A configuration layer MAY declare two optional keys governing the effort
levels. `models` SHALL be a map from an effort level (`high`, `medium`, `low`)
to a non-empty model id, pinning that level to a concrete model; `model` SHALL
be a non-empty string naming the base model a harness that expresses a level as
a model variant appends it to. An absent key leaves the harness's own
expression in force. A `models` value that is not a map whose keys are effort
levels and whose values are non-empty strings, or a `model` value that is not a
non-empty string, SHALL raise a `ConfigError` naming the key and the offending
value.

#### Scenario: A per-level override is read
- **WHEN** a configuration declares `models` as `{"high": "big-model"}`
- **THEN** the `high` level resolves to `big-model` and the other levels keep
  the harness's own expression

#### Scenario: An absent override leaves the harness in force
- **WHEN** no layer declares `models`
- **THEN** every level keeps the harness's own expression

#### Scenario: A malformed override is refused
- **WHEN** a configuration declares `models` as a list, or a map holding an
  empty value, or `model` as a non-string
- **THEN** reading the configuration raises a `ConfigError` naming the key and
  the offending value

### Requirement: Pipeline stage options
id: pipeline-stage-options
base: c4907d51bf5b

The pipeline entry schema SHALL define these typed options. Every stage entry
MAY carry `model`: a non-empty string that is either a symbolic tier —
`session`, `high`, `medium`, or `low`, exported by the schema module as the
symbolic-tier constant — or a concrete model id (any other non-empty string;
the set of concrete ids is open). The `build` stage additionally accepts
`subagent_model` (same tier type), `validator` (boolean, default true),
`telemetry` (boolean, default true), and `parallelism` (integer >= 1). The
`review` stage additionally accepts `disposition`: one of `all`, `high-only`,
or `none`, default `all`. Any stage or custom entry MAY carry `autopilot`: an
object accepting `attempts` (integer >= 1, default 3), `timeout` (integer > 0),
and `max_resumes` (integer >= 0), with unknown keys forbidden. Defaults SHALL
be schema-declared, not injected into resolved entries: a resolved entry
carries exactly the keys the user declared. If `skip` is true, then the entry
SHALL carry no other field beyond `stage` — options on a skipped stage are an
error.

#### Scenario: Build options are accepted and carried
- **WHEN** a declared pipeline carries `{"stage": "build",
  "validator": false, "telemetry": false, "parallelism": 2,
  "subagent_model": "low"}`
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
  "model": "low"}`
- **THEN** resolution fails naming the entry and the skip exclusivity rule

### Requirement: Named pipeline presets
id: pipeline-presets
base: 26a249eb2d7e

The engine SHALL define the preset names `default`, `eco`, and `basic` in a
stdlib names constant, with the preset entry table shipped as data in the
`pipeline_schema` module keyed by exactly those names. When the
`autonomous-pipeline` value is a string, resolution SHALL first check it
against the names constant — an unknown name SHALL fail naming the value, the
supplying config file, and the known preset names. The name `default` SHALL
resolve to the same entries as the absent key — every registry stage bare, in
canonical order — without importing any third-party package. Every other known
name SHALL expand its table entries through the same validation as a
user-declared list. The provenance of a preset-resolved pipeline SHALL be
`preset:<name> (<supplying-config-path>)`. The `eco` preset SHALL be: research
and epic skipped, plan `model` `session`, gate `autopilot.attempts` 1, build
`validator` false with `subagent_model` `low` and `telemetry` false, review
`model` `low` with `disposition` `high-only`. The `basic` preset SHALL be:
research and epic skipped, plan `model` `session`, gate skipped, build
`validator` false with `subagent_model` `medium`, review `model` `medium` with
`disposition` `high-only`. Every shipped preset SHALL keep the plan stage on
`session` and SHALL include an unskipped review stage.

#### Scenario: Eco is a one-line opt-in
- **GIVEN** a repo config declaring `{"autonomous-pipeline": "eco"}`
- **WHEN** the pipeline is resolved
- **THEN** the effective entries are the eco table — research and epic
  skipped, plan on `session`, gate with `autopilot.attempts` 1, build with
  `validator` false, `subagent_model` `low`, `telemetry` false, review with
  `model` `low` and `disposition` `high-only` — and the provenance reads
  `preset:eco` plus the repo config path

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
base: b272f93e6913

The content directory's `README.md` (the format authority) SHALL document the
full shipped `autonomous-pipeline` grammar: the five entry forms; the typed
per-stage options (`model` as a symbolic tier — `session`, `high`, `medium`,
`low` — or a concrete model id; `build`'s `subagent_model`, `validator`,
`telemetry`, and `parallelism`; `review`'s `disposition` with its closed
`all`/`high-only`/`none` set); the `autopilot` options namespace (`attempts`,
`timeout`, `max_resumes`) on any stage or custom entry; the exclusivity rule
that `skip` may only be `true` when present and excludes every other field on
the entry, with `tools` and `replace` mutually exclusive; strict validation
(unknown keys and wrongly typed values rejected, defaults schema-declared and
never injected into resolved entries); and the rule that validation is
stdlib-only, so a declared entry list and every preset resolve with no
third-party package installed. The copyable config example JSON shipped in the
plugin's build references SHALL name the optional `autonomous-pipeline` key
with a pointer to that grammar, without actively declaring a pipeline.

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
