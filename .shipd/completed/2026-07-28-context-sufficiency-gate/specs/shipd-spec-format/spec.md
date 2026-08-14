## MODIFIED Requirements

### Requirement: Plan document sections
id: plan-document-sections
base: 12c8e9ef9454

Every change's `plan.md` SHALL contain, after its title and status header,
a level-2 `## Idea` section followed by a level-2 `## Implementation`
section. A single gate-owned `## Context insufficient` section MAY precede
`## Idea` — written and removed only by the context-sufficiency gate,
holding a paragraph on the missing context followed by dot-point findings.
The `## Idea` section SHALL open with the problem and its motivation (the
why) before any list of changes, SHALL then state the concrete changes,
SHALL include a level-3 `### Non-goals` subsection explicitly listing the
scope exclusions, and SHALL name the affected capabilities and impact. The
`## Implementation` section SHALL hold the binding technical decisions —
each with a rationale and, where useful, the rejected alternative — and
the risks. No section named "Goals" SHALL be required anywhere. Additional
sections MAY follow the two required ones.

#### Scenario: Plan carries both sections
- **WHEN** a change `dark-mode-toggle` is authored
- **THEN** its `plan.md` contains a `## Idea` section and a
  `## Implementation` section after the header

#### Scenario: Gate section may precede the Idea
- **WHEN** a rejected plan carries `## Context insufficient` between the
  header and `## Idea`
- **THEN** the plan remains structurally valid
