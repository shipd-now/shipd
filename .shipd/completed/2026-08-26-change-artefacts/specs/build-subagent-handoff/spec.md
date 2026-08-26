## MODIFIED Requirements

### Requirement: Artifact-compiled context handoff
id: artifact-compiled-context-handoff
base: 1a7827098f36

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
