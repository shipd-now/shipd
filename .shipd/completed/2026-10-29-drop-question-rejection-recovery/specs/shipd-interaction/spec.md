## ADDED Requirements

### Requirement: No question rejection workaround
id: no-question-rejection-workaround

The markdown under `plugins/s/skills/` and `plugins/s/harness/` SHALL NOT
instruct a session to treat a rejected or interrupted question dialog as a
harness misfire. A stdlib test in the engine suite SHALL scan those files for
the case-insensitive phrases `rejection recovery`, `rejection-recovery`, and
`rejected or interrupted`, and SHALL fail naming each `path:line` it finds.

#### Scenario: A reintroduced rule fails the guard
- **GIVEN** a SKILL.md carrying a "Question rejection recovery" section
- **WHEN** the guard test runs
- **THEN** it fails and names that file and line

#### Scenario: The shipped skills pass the guard
- **WHEN** the guard test runs on the repository
- **THEN** it passes

## REMOVED Requirements

### Requirement: Question rejection recovery
id: question-rejection-recovery
base: 248928f65574
Reason: The harness bug that delivered a question dialog as a tool rejection belonged to an older harness version and no longer occurs.
Migration: None; skills treat a rejected dialog like any other tool result.
