## MODIFIED Requirements

### Requirement: Evidenced readiness attestation
id: readiness-attestation
base: e0857c8e1b9d

Before proceeding from investigation to emission, the `am:plan` skill SHALL
print the user-visible readiness attestation as a markdown table with one
cited row per checklist item, each row carrying the item's name and its
concrete evidence: the rows for items 1–3 (problem and motivation, bounded
scope and non-goals, affected capabilities and files) SHALL each cite a
capability name, a `file:line` reference, or a requirement id, and item 4's
row SHALL either name every task-shaping decision with how it was settled
(investigation, personal memory, the oracle, or the user) or state explicitly
that none remain. If an item cannot be discharged by such evidence, then the
skill SHALL treat it as unmet and SHALL NOT proceed to emission. Internal
reasoning SHALL NOT substitute for the printed attestation.

#### Scenario: Attestation precedes emission
- **WHEN** investigation satisfies the readiness checklist
- **THEN** the skill prints a markdown table with one cited row per checklist
  item before authoring any artifact

#### Scenario: An uncitable item blocks the auto-proceed
- **WHEN** the affected files cannot be named concretely
- **THEN** the skill treats item 3 as unmet, does not emit, and resolves it by
  investigation or by a question round

#### Scenario: Item four names how each decision was settled
- **WHEN** the oracle settled one decision and the user settled another
- **THEN** the attestation's fourth row names both decisions and their
  settling rung rather than asserting that nothing is open
