## MODIFIED Requirements

### Requirement: Pipeline-show verb
id: pipeline-show-verb
base: 07d431b033a8

The status CLI SHALL provide `pipeline-show` printing the effective
autonomous pipeline: one line per resolved entry stating its form (stage,
skipped, tool-bound, replaced, or custom) and any bindings with their
fallbacks, plus the provenance of the `autonomous-pipeline` key — the
supplying config file path, `preset:<name>` with the supplying path for a
preset-resolved pipeline, or `[default]` when no layer declares it. Where a
resolved entry carries declared per-stage options, the verb SHALL append
them to that entry's line as `key=value` pairs (booleans rendered
`true`/`false`, `autopilot` sub-keys rendered `autopilot.<key>=<value>`);
an entry with no declared options SHALL render exactly as it does without
options. On a pipeline that fails validation the verb SHALL print every
validation error and exit non-zero. The verb SHALL NOT require a
discoverable workspace or a selected change, and a defaults-only resolution
SHALL exit zero. The verb SHALL additionally accept `--expand <preset>`,
printing the named preset's entry list as indented JSON — the exact value a
config may declare as a custom list — without resolving the repo's own
pipeline; expanding `default` SHALL require no third-party package, an
unknown preset SHALL exit non-zero listing the known preset names, and
expanding any other preset without pydantic importable SHALL exit non-zero
with the install-hint error.

#### Scenario: Default pipeline prints with default provenance
- **WHEN** `pipeline-show` runs where no layer declares the key
- **THEN** all six registry stages print in canonical order marked
  `[default]` and the exit code is zero

#### Scenario: Declared pipeline prints entries and provenance
- **GIVEN** a repo config declaring a pipeline with a skipped gate and a
  replaced review carrying `"fallback": "builtin"`
- **WHEN** `pipeline-show` runs
- **THEN** the output shows the gate as skipped, the review as replaced
  with its fallback, and names the repo's config file

#### Scenario: Invalid pipeline errors with findings
- **WHEN** `pipeline-show` runs against a declared entry with an unknown
  stage name
- **THEN** the validation error is printed naming the entry and the exit
  code is non-zero

#### Scenario: Preset pipeline prints options and preset provenance
- **GIVEN** a repo config declaring `{"autonomous-pipeline": "eco"}` and
  pydantic importable
- **WHEN** `pipeline-show` runs
- **THEN** the source line names `preset:eco` with the repo config path,
  the build line carries `validator=false`,
  `subagent_model=tier-two-below`, and `telemetry=false`, the gate line
  carries `autopilot.attempts=1`, and the review line carries
  `model=tier-below` and `disposition=high-only`

#### Scenario: Expand prints a fork-ready entry list
- **WHEN** `pipeline-show --expand eco` runs with pydantic importable
- **THEN** the output is indented JSON parsing to the eco preset's entry
  list, valid as a declared `autonomous-pipeline` list, and the exit code
  is zero

#### Scenario: Expanding default needs no pydantic
- **GIVEN** pydantic is not importable
- **WHEN** `pipeline-show --expand default` runs
- **THEN** the output is JSON parsing to the six bare registry stages in
  canonical order and the exit code is zero

#### Scenario: Expanding an unknown preset errors
- **WHEN** `pipeline-show --expand turbo` runs
- **THEN** the verb exits non-zero naming `turbo` and listing the known
  presets `basic`, `default`, and `eco`
