## MODIFIED Requirements

### Requirement: Plan document sections
id: plan-document-sections
base: ee9f2fc7c638

A change's `plan.md` SHALL, after the status header, carry a level-2
`## Idea` section followed by a level-2 `## Implementation` section. A
single gate-owned `## Context insufficient` section MAY precede `## Idea` —
written and removed only by the context-sufficiency gate, holding a
paragraph on the missing context followed by dot-point findings. The
`## Idea` section SHALL open with a one-sentence summary of the change,
SHALL then carry a level-3 `### Motivation` subsection of at most two
sentences stating why the change is being made — grounded in the planning
context, never a guess — SHALL then carry a level-3 `### Details`
subsection stating the concrete changes and naming the affected
capabilities and impact, and SHALL close with a level-3 `### Non-goals`
subsection explicitly listing the scope exclusions. The `## Implementation`
section SHALL hold the binding technical decisions — each with a rationale
and, where useful, the rejected alternative — and the risks. No section
named "Goals" SHALL be required anywhere. Additional sections MAY follow
the two required ones.

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
