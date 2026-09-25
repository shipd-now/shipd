## MODIFIED Requirements

### Requirement: Plan document sections
id: plan-document-sections
base: 59f42054f660

A change's `plan.md` SHALL, after the status header, carry a level-2
`## Idea` section followed by a level-2 `## Implementation` section. A
single gate-owned `## Context insufficient` section MAY precede `## Idea` —
written and removed only by the context-sufficiency gate, holding a
paragraph on the missing context followed by dot-point findings. The
`## Idea` section SHALL open with a one-sentence summary of the change,
SHALL then carry a level-3 `### Motivation` subsection of at most two
sentences stating why the change is being made — naming who is blocked and
what they cannot do, grounded in the planning context and never a guess —
SHALL then carry a level-3 `### Details` subsection stating the concrete
changes and naming the affected capabilities and impact, and SHALL close
with a level-3 `### Non-goals` subsection explicitly listing the scope
exclusions. A motivation MAY cite repository state as evidence for the
claim it makes, but SHALL NOT offer repository state as the claim itself:
that a file is a placeholder, is absent, or holds particular content is
never on its own a statement of why the change is wanted. The
`## Implementation` section SHALL hold the binding technical decisions —
each with a rationale and, where useful, the rejected alternative — and the
risks. No section named "Goals" SHALL be required anywhere. Additional
sections MAY follow the two required ones. Where a `## Questions and
answers` section is present, it SHALL hold one or more
`### Q<n>: <one-line question summary>` entries numbered sequentially from
`Q1`, each carrying a `**Question:**` field (the full compact question), a
`**Verdict:**` field (`ANSWER` or `INSUFFICIENT`), an `**Answered by:**`
field (`ORACLE` or `USER`) directly above the answer, and an `**Answer:**`
field (the position or resolution in full); an `ANSWER` entry additionally
carries a `**Cited:**` field and an `INSUFFICIENT` entry a `**Queued:**`
field naming the filed `q-<slug>`.

#### Scenario: Plan carries both sections
- **WHEN** a change `dark-mode-toggle` is authored
- **THEN** its `plan.md` contains a `## Idea` section and a
  `## Implementation` section after the header

#### Scenario: Idea carries the ordered subsections
- **WHEN** a change `dark-mode-toggle` is authored
- **THEN** its `## Idea` opens with a one-sentence summary and carries
  `### Motivation`, `### Details`, and `### Non-goals` subsections in that
  order

#### Scenario: Gate section may precede the Idea
- **WHEN** a rejected plan carries `## Context insufficient` between the
  header and `## Idea`
- **THEN** the plan remains structurally valid

#### Scenario: Questions-and-answers entries follow the grammar
- **WHEN** a plan carries a `## Questions and answers` section with an entry
  `### Q1: Which store holds the toggle?` carrying `**Question:**`,
  `**Verdict:** ANSWER`, `**Answered by:** ORACLE`, `**Answer:**`, and
  `**Cited:**` fields in that order
- **THEN** the plan remains structurally valid

#### Scenario: Motivation names a blocked party, not a file's state
- **WHEN** the authoring surfaces that state the `### Motivation` rule are
  read — the harness long-form reference, the plan skill's emission guide and
  readiness checklist, and the content directory's format-authority README
- **THEN** each requires the motivation to name who is blocked and what they
  cannot do, and each states that repository state is admissible as evidence
  for that claim but is never the claim itself

#### Scenario: The anti-invention rule survives the amendment
- **WHEN** the same four authoring surfaces are read
- **THEN** each still forbids an invented or guessed motivation, and the
  readiness checklist still directs a planner who cannot ground one to put it
  to the user rather than invent it
