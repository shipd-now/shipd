## MODIFIED Requirements

### Requirement: Interactive pipeline resolution
id: interactive-pipeline-resolution
base: 839eecfd0dba

When the interactive `/s:build` flow starts, it SHALL resolve the
effective autonomous pipeline exactly once by running the status CLI's
`pipeline-show --json` verb and SHALL read each entry's declared options
from the emitted JSON object's `entries` dicts and the provenance from its
`source` field, never re-deriving them from configuration files and never
parsing the human-rendered label lines, which carry no contract status. If
the resolution exits non-zero (a validation error),
then the flow SHALL report the engine's error text and stop before any
spec work — a declared pipeline never half-runs. Where the resolved
`build` entry declares `subagent_model`, build SHALL spawn `s:sub-agent`
and `s:validator` workers with the Agent tool's model parameter set to
the tier resolved relative to the session's own model — `session` omits
the parameter; `tier-below`/`tier-two-below` select the model the
orchestrator judges one/two capability steps below the session's own
model among the Agent tool's options, falling back to the lowest option
below and omitting the parameter when none sits below; any other value
passes verbatim as a concrete id.
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

#### Scenario: Tier aliases resolve against the available options
- **GIVEN** a resolved build entry declaring `subagent_model: tier-below`
- **WHEN** `/s:build` spawns execution sub-agents
- **THEN** the skill directs the orchestrator to pick the model it judges
  one capability step below its own from the Agent tool's options, and
  the skill text names no fixed model ladder

## ADDED Requirements

### Requirement: Provider-neutral model down
id: provider-neutral-model-down

The build skill SHALL run the orchestrator on the session's model and,
where the resolved `build` entry declares no `subagent_model`, SHALL
direct it to spawn execution sub-agents on the model down — the model the
orchestrator judges one capability step below its own and a decent fit
for the tasks, chosen from the Agent tool's options in that session. If
no option sits below the orchestrator's model, then the skill SHALL
direct it to omit the model parameter so sub-agents inherit the session's
model. The skill SHALL forbid spawning sub-agents on a model stronger
than the orchestrator's. The build skill body, and the autopilot skill's
in-session tier table, SHALL NOT name any provider's models or model
ids.

#### Scenario: The build skill names no provider models
- **GIVEN** the build skill's `SKILL.md`
- **WHEN** it is searched case-insensitively for `fable`, `opus`,
  `sonnet`, and `haiku`
- **THEN** no occurrence is found

#### Scenario: The autopilot in-session table names no ladder
- **GIVEN** the autopilot skill's "declared `model`" table
- **WHEN** its `tier-below` / `tier-two-below` row is read
- **THEN** it describes the orchestrator's judgement among the Agent
  tool's options and names no model

#### Scenario: Default spawns use the orchestrator's own pick
- **GIVEN** a resolved build entry declaring no `subagent_model`
- **WHEN** the build skill's model policy is read
- **THEN** it directs the orchestrator to choose the model down from the
  Agent tool's options, and to omit the parameter when none sits below
