## ADDED Requirements

### Requirement: Artifact-compiled context handoff
id: artifact-compiled-context-handoff

When spawning an execution sub-agent, the orchestrator SHALL deliver context
through the change artifacts — the sub-agent reads the named artifact set
(`plan.md`, delta specs, `tasks.md`, `am/constitution.md` when present, and
relevant masters) directly — and SHALL NOT pass conversational history,
planning transcript, or exploratory research into the sub-agent's prompt. The
handoff SHALL NOT restate global baseline rules that the sub-agent already
inherits or reads (project instructions, the constitution); the spec on disk
remains the single compiled source of context.

#### Scenario: Sub-agent starts clean
- **WHEN** the orchestrator spawns an execution sub-agent
- **THEN** the sub-agent's prompt contains the handoff template and addenda
  only — no conversation history and no duplicated global rules — and the
  sub-agent obtains change context by reading the artifacts

#### Scenario: Rationale stays available through the artifacts
- **WHEN** a sub-agent needs to know why a binding decision was made
- **THEN** it finds the short rationale in `plan.md`'s `## Implementation`
  section rather than in inherited conversation

### Requirement: Orchestrator addenda slot
id: orchestrator-addenda-slot

The sub-agent prompt template SHALL provide an explicit, optional
**Orchestrator addenda** section where the orchestrator places build-specific
binding context — sequencing hazards, environment caveats, task-ordering
constraints — when a build needs them. Where no build-specific context exists,
the orchestrator SHALL omit the section rather than invent content.

#### Scenario: Hazard rides the addenda slot
- **WHEN** a build has a hazard the artifacts cannot express (e.g. a task
  renames the coordination tooling mid-build)
- **THEN** the orchestrator states it in the addenda section of the spawn
  prompt, and the rest of the template is passed verbatim

#### Scenario: Quiet build omits the slot
- **WHEN** a build has no build-specific hazards
- **THEN** the spawn prompt carries no addenda section
