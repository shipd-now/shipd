# shipd-spec-format — delta

## ADDED Requirements

### Requirement: Plan document sections
id: plan-document-sections

Every change's `plan.md` SHALL contain, after its title and status header, a
level-2 `## Idea` section holding the change's motivation, scope, affected
capabilities, and impact, followed by a level-2 `## Implementation` section
holding the binding technical decisions and their trade-offs. Additional
sections MAY follow, but these two SHALL be present.

#### Scenario: Plan carries both sections
- **WHEN** a change `dark-mode-toggle` is authored
- **THEN** its `plan.md` contains a `## Idea` section and a `## Implementation`
  section after the `# dark-mode-toggle` / `Status:` header

#### Scenario: Missing section is invalid
- **WHEN** a `plan.md` has an `## Idea` section but no `## Implementation`
  section
- **THEN** tooling treats the plan document as structurally invalid

### Requirement: EARS-recommended normative statements
id: ears-recommended-statements

The format documentation SHALL present the five EARS patterns — ubiquitous
("The system shall ..."), event-driven ("When ..."), state-driven
("While ..."), unwanted-behavior ("If ..., then ..."), and optional-feature
("Where ...") — as the recommended shape for requirement SHALL/MUST
statements, and authoring guidance SHALL recommend them when emitting delta
specs. Tooling SHALL NOT reject a requirement solely for not matching an EARS
template; the normative-statement check remains the presence of SHALL or MUST.

#### Scenario: Guidance documents the patterns
- **WHEN** an author consults `am/spec/README.md` for how to phrase a
  requirement
- **THEN** the five EARS patterns are documented with their sentence templates

#### Scenario: Non-EARS phrasing still lints
- **WHEN** a requirement carries a SHALL statement that matches no EARS
  template
- **THEN** the linter reports no error for its phrasing

### Requirement: Constitution steering document
id: constitution-steering-document

The system SHALL reserve `am/spec/constitution.md` as an optional global
steering document holding the repository's non-negotiable engineering rules
(technology constraints, testing standards, anti-patterns). When the file is
present, the planning and build flows SHALL load it and treat its rules as
binding constraints on designs, emitted artifacts, and implementations. When
it is absent, all tooling SHALL behave exactly as before.

#### Scenario: Constitution grounds planning
- **GIVEN** a repo whose `am/spec/constitution.md` forbids third-party Python
  dependencies in engine scripts
- **WHEN** the plan flow authors a design that would add such a dependency
- **THEN** the constitution rule is honored and the design stays within the
  constraint

#### Scenario: Absent constitution changes nothing
- **WHEN** a repo has no `am/spec/constitution.md`
- **THEN** lint, status, merge, plan, and build behave with no errors or
  warnings about the missing file

## MODIFIED Requirements

### Requirement: Per-change artifact layout
id: per-change-artifact-layout
base: 85d91aab86e5

A change SHALL live at `am/spec/changes/<change>/` and SHALL always contain
the lean artifact set: a single `plan.md` holding the change's idea and
implementation decisions, a delta spec at `specs/<capability>/spec.md` for
each affected capability, and `tasks.md` as a separate executor-owned
checklist. This artifact set SHALL be produced for every change regardless of
size.

#### Scenario: A change carries the lean artifact set
- **WHEN** a change `dark-mode-toggle` is authored
- **THEN** `am/spec/changes/dark-mode-toggle/` contains `plan.md`, at least
  one `specs/<capability>/spec.md`, and `tasks.md`

#### Scenario: Tasks stay out of the plan document
- **WHEN** an executor marks tasks done during a build
- **THEN** only `tasks.md` checkboxes change and `plan.md` is not rewritten
