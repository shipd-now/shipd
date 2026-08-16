## MODIFIED Requirements

### Requirement: Interactive pipeline resolution
id: interactive-pipeline-resolution
base: b5c8eb7f8439

When the interactive `/s:build` flow starts, it SHALL resolve the
effective autonomous pipeline exactly once by running the status CLI's
`pipeline-show --json` verb and SHALL read each entry's declared options
from the emitted JSON object's `entries` dicts and the provenance from its
`source` field, never re-deriving them from configuration files and never
parsing the human-rendered label lines, which carry no contract status. If
the resolution exits non-zero (a validation error or missing pydantic),
then the flow SHALL report the engine's error text and stop before any
spec work — a declared pipeline never half-runs. Where the resolved
`build` entry declares `subagent_model`, build SHALL spawn `s:sub-agent`
and `s:validator` workers with the Agent tool's model parameter set to
the tier resolved relative to the session's own model — `session` omits
the parameter; `tier-below`/`tier-two-below` step one/two below the
session's model on the ladder `fable`, `opus`, `sonnet`, `haiku`,
clamped at the bottom; any other value passes verbatim as a concrete id.
Where the resolved `build` entry declares `parallelism`, that value SHALL
cap concurrent execution sub-agents, taking precedence over the
`parallelism` configuration key and the default of three. Where the
resolved `build` entry declares `telemetry` false, build SHALL NOT
persist the per-tool token breakdown into the change's `tasks.md`. The
interactive flow SHALL ignore `autopilot` blocks, `replace` bindings,
custom steps, the build entry's own `model` option, and a `skip` on the
stage the user explicitly invoked — an explicit invocation always runs.
When a driving invoker's prompt conveys stage-option instructions, those
SHALL supersede self-resolution.

#### Scenario: Eco build options are honored interactively
- **GIVEN** a repo whose resolved pipeline is the `eco` preset
- **WHEN** a user runs `/s:build` on a planned change
- **THEN** execution sub-agents spawn on the tier two below the session,
  no validator is spawned, and no per-tool token breakdown is persisted

#### Scenario: Options are read from the JSON entries
- **GIVEN** a resolved build entry declaring `subagent_model` and
  `parallelism`
- **WHEN** `/s:build` resolves the pipeline at flow start
- **THEN** the options are taken from the `--json` object's entry dicts,
  not parsed out of rendered label lines

#### Scenario: Malformed pipeline stops the build before spec work
- **GIVEN** a declared pipeline entry carrying an unknown key
- **WHEN** `/s:build` resolves the pipeline at flow start
- **THEN** the flow reports the resolution error naming the entry and
  field and stops without authoring artifacts or spawning sub-agents

#### Scenario: Autopilot blocks are ignored interactively
- **GIVEN** a resolved build entry carrying `autopilot.attempts` 1
- **WHEN** an interactive build stage fails
- **THEN** no retry budget is enforced from it — the flow stops and asks
  the user exactly as before

#### Scenario: Conveyed options supersede self-resolution
- **GIVEN** a driving session's prompt conveying a concrete sub-agent
  model resolved against a detached anchor
- **WHEN** the interactive flow's self-resolved tier would differ
- **THEN** the conveyed concrete value is used for the spawns
