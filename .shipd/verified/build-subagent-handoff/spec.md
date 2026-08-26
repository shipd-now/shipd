# build-subagent-handoff

### Requirement: Artifact-compiled context handoff
id: artifact-compiled-context-handoff

When spawning an execution sub-agent, the orchestrator SHALL deliver context
through the change artifacts — the sub-agent reads the named artifact set
(`plan.md`, delta specs, `tasks.md`, the change's `artefacts/` directory when
present, `.shipd/constitution.md` when present, and relevant masters)
directly — and SHALL NOT pass conversational history, planning transcript, or
exploratory research into the sub-agent's prompt. Where the change carries an
`artefacts/` directory, the sub-agent and the validator SHALL read the
artefacts the artifacts reference and treat their content as binding, and the
artefacts SHALL travel by their change-relative paths rather than as prose in
the spawn message. When `plan.md`'s `## Implementation` names a design scratch
directory for the change, that directory is part of the named artifact set: the
sub-agent SHALL read it as a read-only reference and build to match it
verbatim, and the design SHALL travel by that plan-named path rather than as
prose in the spawn message, so the handoff stays clean-context. The role
contract lives in the `s:sub-agent` agent definition, so the spawn message SHALL
carry only the change name, the coordinator script path, and any Orchestrator
addenda. The handoff SHALL NOT restate global baseline rules that the sub-agent
already inherits or reads (project instructions, the constitution); the spec on
disk remains the single compiled source of context.

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

#### Scenario: Design reference rides the plan, not the prompt
- **WHEN** a change carries a design and `plan.md` names its scratch directory
- **THEN** the sub-agent discovers the design by reading `plan.md` and then the
  named directory, and the spawn message still carries no design content of its
  own

#### Scenario: Artefacts ride the change, not the prompt
- **WHEN** a change carries an `artefacts/` directory a task references
- **THEN** the sub-agent discovers it by reading the artifacts and then the
  named path, and the spawn message carries no artefact content of its own

### Requirement: Orchestrator addenda slot
id: orchestrator-addenda-slot

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
the shipd role rather than a generic type.

#### Scenario: Agents pane shows the shipd role
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

### Requirement: Sub-agent workspace gate
id: subagent-workspace-gate

The execution sub-agent role contract (`agents/sub-agent.md`) SHALL require
a workspace gate the sub-agent passes **before its first claim or file
edit**: confirm the working directory is the worktree root named in the
spawn message, and confirm `git rev-parse --abbrev-ref HEAD` prints
`change/<change>` for the spawned change; if either check fails, then the
sub-agent SHALL stop and report the mismatch instead of claiming, editing,
or changing directory elsewhere. The contract SHALL also require that every
file path the sub-agent edits or passes to commands stays inside that
worktree root — never an absolute path into another checkout.

#### Scenario: The contract carries the gate
- **WHEN** `agents/sub-agent.md` is read
- **THEN** it contains a workspace-gate section requiring the worktree-root
  and `git rev-parse --abbrev-ref HEAD` checks before the first claim or
  edit, the stop-and-report-on-mismatch rule, and the paths-inside-the-
  worktree rule

#### Scenario: The gate is covered by a stdlib test
- **WHEN** the engine test suite runs without `textual`
- **THEN** a test asserts the contract file carries the gate's required
  elements, so a contract regression fails CI
