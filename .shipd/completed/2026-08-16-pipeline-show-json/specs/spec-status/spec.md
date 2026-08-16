## MODIFIED Requirements

### Requirement: Pipeline-show verb
id: pipeline-show-verb
base: c4dabe41d418

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

The verb SHALL additionally accept `--json` as its machine contract: when
resolving the repo's pipeline it SHALL emit exactly one JSON object on
stdout and nothing else, with `source` holding the raw provenance value
(`default`, the supplying config file path, or `preset:<name>
(<config-path>)`) and `entries` holding the resolved entries as the
validated dicts, carrying exactly the keys each entry declared; when
combined with `--expand <preset>` it SHALL emit the same entry-list JSON
array the flagless expand prints. Without the flag, the text output SHALL
stay byte-identical to its pre-flag behavior, and error handling (stderr
`Error:` lines, exit codes) SHALL be unchanged in both modes.

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

#### Scenario: Resolved pipeline is machine-readable
- **GIVEN** a repo config declaring `{"autonomous-pipeline": "eco"}` and
  pydantic importable
- **WHEN** `pipeline-show --json` runs
- **THEN** stdout parses as one JSON object whose `source` names
  `preset:eco` with the repo config path and whose `entries` hold the
  validated entry dicts, the build entry carrying `subagent_model`
  `tier-two-below`, `validator` false, and `telemetry` false

#### Scenario: Default resolution is machine-readable without pydantic
- **GIVEN** pydantic is not importable and no layer declares the key
- **WHEN** `pipeline-show --json` runs
- **THEN** stdout parses as one JSON object with `source` `default` and
  `entries` holding the six bare registry stages in canonical order, and
  the exit code is zero

#### Scenario: Expand with the JSON flag keeps the array contract
- **WHEN** `pipeline-show --expand default --json` runs
- **THEN** stdout parses as the same JSON entry-list array the flagless
  expand prints

#### Scenario: Text mode is unchanged without the flag
- **WHEN** `pipeline-show` runs without `--json`
- **THEN** the output is byte-identical to the pre-flag text rendering

#### Scenario: Invalid pipeline errors identically under the flag
- **WHEN** `pipeline-show --json` runs against a declared entry with an
  unknown stage name
- **THEN** the verb prints the validation error to stderr and exits
  non-zero exactly as the flagless form does

### Requirement: Interactive status skill
id: interactive-status-skill
base: 696c6d61c930

An `am:status` skill SHALL expose four commands over the status CLI —
`status` (report the selected or named change's status), `validate` (report
structural validity or the errors), `set-status <status>` (guarded
transition), and `pipeline` (report the effective autonomous pipeline).
When invoked with no argument, the skill SHALL run `show`
alone and relay its output — the selected change's one-liner when a
selection exists, else the CLI's workspace board report — never surfacing
the bare `status` verb's no-selection error as the answer. When the
`status` command's argument names an epic rather than
a change, the skill SHALL relay the CLI's board-shaped epic report and point
epic transitions at the epic verbs rather than `set-status`. When
`set-status` is refused by a guard (exit code 3), the skill
SHALL surface the refusal reason and ask the user whether to override,
re-running with `--force` only after explicit consent; it SHALL never pass
`--force` uninvited, and on decline SHALL leave the status unchanged. The
`pipeline` command SHALL run `pipeline-show` and relay its output verbatim;
with a preset-name argument it SHALL instead run `pipeline-show --expand
<preset>` and relay that output, so an unknown preset relays the CLI's
error listing the known preset names.

#### Scenario: Refusal asks before forcing
- **WHEN** the skill's `set-status complete` is refused because tickets are
  open
- **THEN** the skill shows the reason, asks the user, and only re-runs with
  `--force` if the user chooses to override

#### Scenario: Decline leaves the status untouched
- **WHEN** the user declines the override question
- **THEN** the proposal's status line is unchanged and the skill reports the
  refusal

#### Scenario: An epic argument reports the epic
- **WHEN** the skill's `status` command is invoked with an epic's slug
- **THEN** the skill relays the board-shaped epic report instead of a
  change status

#### Scenario: A bare invocation reports the workspace
- **GIVEN** no spec selected
- **WHEN** the skill is invoked with no argument
- **THEN** the skill relays the CLI's workspace board report rather than
  the no-selection error

#### Scenario: The pipeline command relays the resolved pipeline
- **WHEN** the skill is invoked as `/s:status pipeline`
- **THEN** it runs the CLI's `pipeline-show` and relays the printed
  pipeline and provenance verbatim

#### Scenario: A preset argument expands the preset
- **WHEN** the skill is invoked as `/s:status pipeline eco`
- **THEN** it runs `pipeline-show --expand eco` and relays the printed
  entry list, and an unknown preset name relays the CLI's known-preset
  listing
