# shipd-spec-format — delta

## MODIFIED Requirements

### Requirement: Plan document sections
id: plan-document-sections
base: ef09eeba9ad3

Every change's `plan.md` SHALL contain, after its title and status header, a
level-2 `## Idea` section followed by a level-2 `## Implementation` section.
The `## Idea` section SHALL open with the problem and its motivation (the why)
before any list of changes, SHALL then state the concrete changes, SHALL
include a level-3 `### Non-goals` subsection explicitly listing the scope
exclusions, and SHALL name the affected capabilities and impact. The
`## Implementation` section SHALL hold the binding technical decisions —
each with a rationale and, where useful, the rejected alternative — and the
risks. No section named "Goals" SHALL be required anywhere: the Idea carries
the goals, and how-level negative space belongs to the per-decision rejected
alternatives. Additional sections MAY follow the two required ones.

#### Scenario: Plan carries both sections
- **WHEN** a change `dark-mode-toggle` is authored
- **THEN** its `plan.md` contains a `## Idea` section and a `## Implementation`
  section after the `# dark-mode-toggle` / `Status:` header

#### Scenario: Missing section is invalid
- **WHEN** a `plan.md` has an `## Idea` section but no `## Implementation`
  section
- **THEN** tooling treats the plan document as structurally invalid

#### Scenario: Idea leads with the why and bounds the scope
- **WHEN** a reader opens a conforming `plan.md`
- **THEN** the `## Idea` section states the problem before the change list and
  contains a `### Non-goals` subsection listing what is out of scope

#### Scenario: Missing non-goals is invalid
- **WHEN** a `plan.md` has both required sections but no `### Non-goals`
  subsection
- **THEN** tooling treats the plan document as structurally invalid
