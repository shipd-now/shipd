## ADDED Requirements

### Requirement: Initiative brief artifact
id: initiative-brief-format

An initiative brief SHALL live at
`<workspace-root>/initiatives/<slug>/brief.md`, beginning with a `# <slug>`
title matching its directory and a `Status:` line whose value is one of
`open`, `achieved`, `dropped`. The header MAY carry a metadata block whose
only recognized key is `Project:` with a kebab-case value. The document
SHALL carry a `## Requirements` section holding at least one `- [ ]`
checkbox requirement — outcomes ticked over time, not tasks. Prose stating
the goal MAY precede the Requirements section.

#### Scenario: Conforming brief is valid
- **WHEN** `<ws>/initiatives/mvp-readiness/brief.md` starts with
  `# mvp-readiness`, `Status: open`, and carries a `## Requirements` section
  with two unticked checkboxes
- **THEN** tooling accepts the brief as structurally valid

#### Scenario: Brief without requirements is rejected
- **WHEN** a brief has a valid header but no `## Requirements` section
- **THEN** tooling reports the missing section

#### Scenario: Unknown metadata key is rejected
- **WHEN** a brief's header carries `Theme: reliability`
- **THEN** tooling reports an unrecognized-key error

#### Scenario: Project scope is recognized without registry validation
- **WHEN** a brief carries `Project: alpha` and no registry validation for
  projects exists yet
- **THEN** the brief lints clean on the key and value shape alone

### Requirement: CI-safe initiative reference resolution
id: initiative-reference-resolution

When a workspace root is discoverable from the repository, an `Initiative:`
line on an epic or on a standalone change SHALL resolve to an existing brief
at `<workspace-root>/initiatives/<slug>/brief.md`, and an unresolvable
reference SHALL be an error naming the expected path. When no workspace root
is discoverable, the resolution check SHALL be skipped silently, so a bare
checkout (CI) never depends on files outside the repository.

#### Scenario: Missing brief errors when a workspace exists
- **GIVEN** a discoverable workspace with no `initiatives/mvp-readiness/`
- **WHEN** an epic carrying `Initiative: mvp-readiness` is linted
- **THEN** an error names the expected brief path

#### Scenario: Resolved brief passes
- **GIVEN** a discoverable workspace with
  `initiatives/mvp-readiness/brief.md`
- **WHEN** an epic carrying `Initiative: mvp-readiness` is linted
- **THEN** no initiative-reference error is reported

#### Scenario: No workspace skips silently
- **WHEN** an epic carrying `Initiative: mvp-readiness` is linted in a
  checkout with no discoverable workspace
- **THEN** no initiative-reference error or warning is emitted and the exit
  code is unaffected
