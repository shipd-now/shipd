## ADDED Requirements

### Requirement: Change-relative artefact references resolve
id: artefact-reference-resolution

Within the gate's task-path check, a backticked token in `tasks.md` that begins
with `artefacts/` SHALL also be resolved against the change's own directory: the
token SHALL produce no finding when it names an existing file or directory
inside `<content-dir>/planned/<change>/`, and SHALL fall through to the check's
existing repository-root resolution otherwise. This change-relative resolution
SHALL apply only to tokens carrying that prefix, so a mistyped repository path
remains a finding, and it SHALL introduce no model call and no network access.

#### Scenario: Change-relative artefact reference resolves
- **GIVEN** the change directory holds `artefacts/policy.md`
- **WHEN** a task names that path change-relatively in backticks
- **THEN** no file-reference finding is produced for it

#### Scenario: Missing artefact reference is still a finding
- **GIVEN** the change directory holds no `artefacts/ghost.md`
- **WHEN** a task names that path change-relatively in backticks
- **THEN** the findings name the token

#### Scenario: A mistyped repository path is unaffected
- **GIVEN** a task names `src/ghost/nested/missing.py` in backticks and neither
  `src/ghost/nested/` nor `src/ghost/` exists
- **WHEN** the gate runs
- **THEN** the findings still name that token
