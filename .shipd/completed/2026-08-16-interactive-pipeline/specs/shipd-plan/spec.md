## ADDED Requirements

### Requirement: Plan-side pipeline resolution
id: plan-pipeline-resolution

When the plan flow starts, it SHALL resolve the effective autonomous
pipeline by running the status CLI's `pipeline-show` verb. If the
resolution exits non-zero (a validation error or missing pydantic), then
the flow SHALL report the engine's error text and stop before
investigation or any question round — a declared pipeline never
half-runs. Where a configuration layer declares the pipeline (list or
preset), the flow SHALL name the resolved provenance in its first
user-visible status text alongside the version announcement; a default
pipeline (`[default]` provenance) SHALL add no announcement. The flow
SHALL ignore the plan entry's `model` option and every `autopilot` block
— interactively the session's model is the user's choice and the human
is the retry loop — and SHALL run its ending's context-gate promotion
unchanged regardless of the pipeline's gate entry: a gate `skip` or
`autopilot.attempts` value SHALL neither bypass the gate nor permit a
forced status.

#### Scenario: Malformed pipeline stops planning
- **GIVEN** a declared pipeline entry carrying a misspelled option key
- **WHEN** `/s:plan` starts
- **THEN** the flow reports the resolution error naming the entry and
  field and stops without investigating or emitting

#### Scenario: Declared provenance is announced
- **GIVEN** a repo whose config declares `{"autonomous-pipeline": "eco"}`
- **WHEN** `/s:plan` starts
- **THEN** the first status text names the `preset:eco` provenance with
  its supplying config path, alongside the version announcement

#### Scenario: Gate skip never skips the internal gate
- **GIVEN** a resolved pipeline whose gate entry is skipped
- **WHEN** a planned change reaches the plan flow's ending
- **THEN** the context gate still runs and its verdict remains the only
  path to `ready`

#### Scenario: Default pipeline changes nothing
- **GIVEN** no configuration layer declares `autonomous-pipeline`
- **WHEN** `/s:plan` starts
- **THEN** no pipeline provenance is announced and the flow proceeds
  exactly as before
