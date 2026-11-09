## MODIFIED Requirements

### Requirement: Pipeline stage options
id: pipeline-stage-options
base: 6a0e0b0bcd20

The pipeline entry schema SHALL define these typed options. Every stage entry
MAY carry `model`: a non-empty string that is either a symbolic tier —
`session`, `high`, `medium`, or `low`, exported by the schema module as the
symbolic-tier constant — or a concrete model id (any other non-empty string;
the set of concrete ids is open). The `build` stage additionally accepts
`subagent_model` (same tier type), `validator` (boolean, default true),
`telemetry` (boolean, default true), `teach` (boolean, default true), and
`parallelism` (integer >= 1). The `review` stage additionally accepts
`disposition`: one of `all`, `high-only`, or `none`, default `all`. Any stage
or custom entry MAY carry `autopilot`: an object accepting `attempts`
(integer >= 1, default 3), `timeout` (integer > 0), and `max_resumes`
(integer >= 0), with unknown keys forbidden. Defaults SHALL be
schema-declared, not injected into resolved entries: a resolved entry carries
exactly the keys the user declared. If `skip` is true, then the entry SHALL
carry no other field beyond `stage` — options on a skipped stage are an error.
The `pipeline-show` renderer and the autopilot dry-run label SHALL render a
declared `teach` after `telemetry`, and the autopilot's build addenda SHALL
carry a skip-the-teacher line when `teach` is false.

#### Scenario: Build options are accepted and carried
- **WHEN** a declared pipeline carries `{"stage": "build",
  "validator": false, "telemetry": false, "teach": false, "parallelism": 2,
  "subagent_model": "low"}`
- **THEN** the pipeline resolves and the effective entry carries exactly
  those declared keys and values

#### Scenario: Undeclared defaults are not injected
- **WHEN** a declared pipeline carries the bare entry `{"stage": "build"}`
- **THEN** the resolved entry is exactly `{"stage": "build"}` with no
  `validator`, `telemetry`, `teach`, or other default keys added

#### Scenario: Non-boolean teach is rejected
- **WHEN** a declared build entry carries `"teach": "maybe"`
- **THEN** resolution fails with an error line naming `teach`

#### Scenario: Teach renders in the show and label surfaces
- **GIVEN** a declared build entry carrying `"teach": false`
- **WHEN** `pipeline-show` runs and the autopilot dry-run label renders
- **THEN** the build line carries `teach=false` after its telemetry field and
  the label carries `teach off`

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

### Requirement: Pipeline grammar documentation
id: pipeline-grammar-docs
base: 7a71820a4748

The content directory's `README.md` (the format authority) SHALL document the
full shipped `autonomous-pipeline` grammar: the five entry forms; the typed
per-stage options (`model` as a symbolic tier — `session`, `high`, `medium`,
`low` — or a concrete model id; `build`'s `subagent_model`, `validator`,
`telemetry`, `teach`, and `parallelism`; `review`'s `disposition` with its
closed `all`/`high-only`/`none` set); the `autopilot` options namespace
(`attempts`, `timeout`, `max_resumes`) on any stage or custom entry; the
exclusivity rule that `skip` may only be `true` when present and excludes every
other field on the entry, with `tools` and `replace` mutually exclusive; strict
validation (unknown keys and wrongly typed values rejected, defaults
schema-declared and never injected into resolved entries); and the rule that
validation is stdlib-only, so a declared entry list and every preset resolve
with no third-party package installed. The copyable config example JSON shipped
in the plugin's build references SHALL name the optional `autonomous-pipeline`
key with a pointer to that grammar, without actively declaring a pipeline.

#### Scenario: Eco expansion is hand-authorable from the README alone
- **WHEN** a reader compares `pipeline-show --expand eco`'s entries against
  the format authority's pipeline section
- **THEN** every key those entries carry (`skip`, `model`, `autopilot`,
  `validator`, `subagent_model`, `telemetry`, `disposition`) is documented
  there with its type and allowed values

#### Scenario: Teach is documented with the build options
- **WHEN** a reader consults the format authority's `build` option line
- **THEN** it names `teach` as a boolean defaulting to `true` beside
  `validator` and `telemetry`

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
