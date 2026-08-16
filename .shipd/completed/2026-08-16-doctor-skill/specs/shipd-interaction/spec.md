## MODIFIED Requirements

### Requirement: Question rejection recovery
id: question-rejection-recovery
base: 8fe1f484e527

If an AskUserQuestion call returns a rejection or interruption instead of a
selected answer, then the skill session SHALL treat it as a harness misfire
rather than a user decision: it SHALL NOT record a decline or a stop, and on
the user's next message it SHALL either fold in a typed answer or re-offer
the same choices as a plain-text numbered list and wait. An explicit stop —
a selected Stop option or a typed stop — SHALL still be honored immediately.
Every interactive am skill's SKILL.md (plan, build, epic, initiative,
status, onboard, research, forget, doctor) SHALL carry this recovery rule.

#### Scenario: Rejected question is re-offered, not obeyed
- **WHEN** an AskUserQuestion at a decision point comes back as a tool
  rejection and the user's next message does not answer it
- **THEN** the skill re-offers the same choices as a plain-text numbered
  list and waits, instead of treating the flow as declined or stopped

#### Scenario: Typed answer after a misfire is folded in
- **WHEN** an AskUserQuestion comes back rejected and the user's next
  message states one of the offered choices in plain text
- **THEN** the skill accepts that answer and continues as if the dialog had
  returned it

#### Scenario: Explicit stop still stops
- **WHEN** the user selects a Stop option or types that they want to stop
- **THEN** the skill honors it immediately

#### Scenario: All interactive skills carry the rule
- **WHEN** the nine interactive SKILL.md files are inspected
- **THEN** each contains the question rejection recovery rule
