## ADDED Requirements

### Requirement: Named plugin agent types
id: named-agent-types

The plugin SHALL define its worker roles as named agent types under
`plugins/s/agents/`: `sub-agent.md` (execution, registering as
`s:sub-agent`) and `validator.md` (validation, registering as `s:validator`),
each a frontmatter (`name`, `description`) plus a self-sufficient system-prompt
body carrying that role's full contract. Neither definition SHALL pin a
`model:` in frontmatter — the orchestrator passes the tier-below model per
spawn. Build SHALL spawn workers with these agent types, with a spawn
description of `builder <n> · <change>` for executors and
`validator · <change>` for the validator, so the session's agent list shows
the am role rather than a generic type.

#### Scenario: Agents pane shows the am role
- **WHEN** a build spawns an execution sub-agent
- **THEN** it is spawned with agent type `s:sub-agent` and a description of
  the form `builder <n> · <change>`

#### Scenario: Validator spawns under its own type
- **WHEN** Phase 5 spawns the validator
- **THEN** it is spawned with agent type `s:validator` and description
  `validator · <change>`

#### Scenario: Tier policy survives the definitions
- **WHEN** either agent definition is read
- **THEN** its frontmatter contains no `model:` pin, and the spawn-time model
  parameter alone selects the tier

## MODIFIED Requirements

### Requirement: Artifact-compiled context handoff
id: artifact-compiled-context-handoff
base: 64ca8e397a96

When spawning an execution sub-agent, the orchestrator SHALL deliver context
through the change artifacts — the sub-agent reads the named artifact set
(`plan.md`, delta specs, `tasks.md`, `am/constitution.md` when present, and
relevant masters) directly — and SHALL NOT pass conversational history,
planning transcript, or exploratory research into the sub-agent's prompt. The
role contract lives in the `s:sub-agent` agent definition, so the spawn
message SHALL carry only the change name, the coordinator script path, and any
Orchestrator addenda. The handoff SHALL NOT restate global baseline rules that
the sub-agent already inherits or reads (project instructions, the
constitution); the spec on disk remains the single compiled source of context.

#### Scenario: Sub-agent starts clean
- **WHEN** the orchestrator spawns an execution sub-agent
- **THEN** the spawn message contains the change name, coordinator path, and
  addenda only — no conversation history, no duplicated global rules, no
  copied role prompt — and the sub-agent obtains change context by reading the
  artifacts

#### Scenario: Rationale stays available through the artifacts
- **WHEN** a sub-agent needs to know why a binding decision was made
- **THEN** it finds the short rationale in `plan.md`'s `## Implementation`
  section rather than in inherited conversation

### Requirement: Orchestrator addenda slot
id: orchestrator-addenda-slot
base: 8f13f7b62fd4

The spawn message contract SHALL provide an explicit, optional **Orchestrator
addenda** section where the orchestrator places build-specific binding
context — sequencing hazards, environment caveats, task-ordering constraints —
when a build needs them, and the `s:sub-agent` definition SHALL instruct the
agent to treat such addenda as binding. Where no build-specific context
exists, the orchestrator SHALL omit the section rather than invent content.

#### Scenario: Hazard rides the addenda slot
- **WHEN** a build has a hazard the artifacts cannot express (e.g. a task
  renames the coordination tooling mid-build)
- **THEN** the orchestrator states it in the addenda section of the spawn
  message, alongside the change name and coordinator path

#### Scenario: Quiet build omits the slot
- **WHEN** a build has no build-specific hazards
- **THEN** the spawn message carries no addenda section
