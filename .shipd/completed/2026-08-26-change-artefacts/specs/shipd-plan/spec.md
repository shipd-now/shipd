## ADDED Requirements

### Requirement: Planning artefacts are stored with the change
id: plan-artefact-storage

Where planning produces a standalone output that must be preserved exactly —
a policy document, a block of verbatim text, any content the lean artifact set
would have to paraphrase — the skill SHALL stage it under the staging
directory's `artefacts/` subdirectory so it installs with the change, and SHALL
reference it from the artifacts that depend on it: `plan.md` where it informs a
binding decision, `tasks.md` where a task must apply it, and a delta spec where
a requirement is stated in its terms. References SHALL use the change-relative
path `artefacts/<file>`. The skill SHALL NOT paste such content into `plan.md`,
`tasks.md`, or a delta spec, and SHALL NOT stage an artefact it references
nowhere, which the emit engine refuses. Where planning produces no such output,
the skill SHALL stage no `artefacts/` directory and emission is unchanged.

#### Scenario: A drafted policy is staged as an artefact
- **GIVEN** planning drafts a policy document for the change
- **WHEN** the artifacts are emitted
- **THEN** the installed change carries the document under `artefacts/` and
  `plan.md` names it by its change-relative path

#### Scenario: Tasks point at the artefact rather than restating it
- **GIVEN** a task must apply verbatim text the planner drafted
- **WHEN** the task list is emitted
- **THEN** the task names the artefact's change-relative path and the text
  itself is not copied into `tasks.md`

#### Scenario: A change with no standalone output stages no directory
- **WHEN** planning produces nothing beyond the lean artifact set
- **THEN** the staging directory carries no `artefacts/` subdirectory
