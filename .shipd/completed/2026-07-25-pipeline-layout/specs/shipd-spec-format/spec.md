## MODIFIED Requirements

### Requirement: Master spec library layout
id: master-spec-library-layout
base: e33ed1d554e9

The system SHALL store canonical specifications at
`am/verified/<capability>/spec.md`, one file per capability. Each file SHALL
contain zero or more requirement blocks, each introduced by a
`### Requirement: <title>` header, and this location SHALL be the single source
of truth that the merge engine reads and writes.

#### Scenario: Locating a capability's canonical spec
- **WHEN** a tool needs the current definition of the `enforce-sso-timeout`
  requirement in the `auth` capability
- **THEN** it reads `am/verified/auth/spec.md` and finds the requirement block
  whose `id` is `enforce-sso-timeout`

### Requirement: Per-change artifact layout
id: per-change-artifact-layout
base: ddf90806da8f

A change SHALL live at `am/planned/<change>/` and SHALL always contain
the lean artifact set: a single `plan.md` holding the change's idea and
implementation decisions, a delta spec at `specs/<capability>/spec.md` for
each affected capability, and `tasks.md` as a separate executor-owned
checklist. This artifact set SHALL be produced for every change regardless of
size.

#### Scenario: A change carries the lean artifact set
- **WHEN** a change `dark-mode-toggle` is authored
- **THEN** `am/planned/dark-mode-toggle/` contains `plan.md`, at least
  one `specs/<capability>/spec.md`, and `tasks.md`

#### Scenario: Tasks stay out of the plan document
- **WHEN** an executor marks tasks done during a build
- **THEN** only `tasks.md` checkboxes change and `plan.md` is not rewritten

### Requirement: Applied changes move to completed
id: archive-of-applied-changes
base: a2723257cc84

After a change's delta is merged into the master library, the change directory
SHALL be moved to `am/completed/<date>-<change>/` so the applied change is
retained immutably for auditability and never re-merged. `am/completed/` SHALL
be a sibling of `am/planned/`, so `am/planned/` contains only live changes.

#### Scenario: Applied change is retained under completed
- **WHEN** the merge engine finishes applying change `dark-mode-toggle`
- **THEN** `am/planned/dark-mode-toggle/` no longer exists and
  `am/completed/<date>-dark-mode-toggle/` contains its artifacts

### Requirement: EARS-recommended normative statements
id: ears-recommended-statements
base: a7c2d6a32603

The format documentation SHALL present the five EARS patterns — ubiquitous
("The system shall ..."), event-driven ("When ..."), state-driven
("While ..."), unwanted-behavior ("If ..., then ..."), and optional-feature
("Where ...") — as the recommended shape for requirement SHALL/MUST
statements, and authoring guidance SHALL recommend them when emitting delta
specs. Tooling SHALL NOT reject a requirement solely for not matching an EARS
template; the normative-statement check remains the presence of SHALL or MUST.

#### Scenario: Guidance documents the patterns
- **WHEN** an author consults `am/README.md` for how to phrase a
  requirement
- **THEN** the five EARS patterns are documented with their sentence templates

#### Scenario: Non-EARS phrasing still lints
- **WHEN** a requirement carries a SHALL statement that matches no EARS
  template
- **THEN** the linter reports no error for its phrasing

### Requirement: Constitution steering document
id: constitution-steering-document
base: 3b9a4a76f848

The system SHALL reserve `am/constitution.md` as an optional global
steering document holding the repository's non-negotiable engineering rules
(technology constraints, testing standards, anti-patterns). When the file is
present, the planning and build flows SHALL load it and treat its rules as
binding constraints on designs, emitted artifacts, and implementations. When
it is absent, all tooling SHALL behave exactly as before.

#### Scenario: Constitution grounds planning
- **GIVEN** a repo whose `am/constitution.md` forbids third-party Python
  dependencies in engine scripts
- **WHEN** the plan flow authors a design that would add such a dependency
- **THEN** the constitution rule is honored and the design stays within the
  constraint

#### Scenario: Absent constitution changes nothing
- **WHEN** a repo has no `am/constitution.md`
- **THEN** lint, status, merge, plan, and build behave with no errors or
  warnings about the missing file
