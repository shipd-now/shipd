## MODIFIED Requirements

### Requirement: Pipeline-honoring stage execution
id: pipeline-stage-execution
base: 07a0f14d4b6a

Per member, the autopilot SHALL execute the resolved
`autonomous-pipeline` entries in order, covering the `plan`, `gate`,
`build`, and `review` registry stages and any `custom` entries, while
noting and ignoring `research` and `epic` entries as pre-approval stages.
A skipped entry SHALL be skipped; a replaced entry SHALL run its
replacement command in the member's worktree instead of the built-in
behavior; a `tools` binding SHALL be surfaced to the driven session as
prompt guidance including its fallback. Built-in behavior: `plan` drives a
headless `/s:plan <member>` graded on a lint-clean member change at
`Status: ready`; `gate` runs the gate engine, where a context rejection
(exit 2) parks the member immediately with no retries; `build` drives a
headless `/s:build` graded on the change archived under `completed/` and
a PR existing for the member branch; `review` drives a headless session
that reviews the member branch and posts the verdict through the review
poster, graded on the member PR's head SHA carrying a `semantic-review`
commit status with state `success`. Member worktrees SHALL be created
with the plugin's worktree helper.

#### Scenario: Full pass ships a member
- **GIVEN** a member whose plan gates clean and whose build succeeds
- **WHEN** the autopilot drives it
- **THEN** its worktree came from the plugin helper, the change is
  archived, and an auto-merging PR exists for its branch

#### Scenario: Gate rejection parks without retry
- **WHEN** the gate exits 2 on a member's plan
- **THEN** the member is parked as rejected, no re-drive occurs, and the
  run continues with the next member

#### Scenario: Skipped gate is honored
- **GIVEN** a resolved pipeline whose gate entry carries skip
- **WHEN** a member is driven
- **THEN** no gate runs between plan and build for that member

#### Scenario: Custom step runs at its position
- **GIVEN** a custom entry between build and review
- **WHEN** a member is driven
- **THEN** the custom command runs in the member's worktree after build

#### Scenario: Review stage grades on the posted status
- **GIVEN** a member whose build shipped a PR
- **WHEN** the review stage's driven session posts a `success`
  `semantic-review` status on the PR's head SHA
- **THEN** the stage grade passes and the member proceeds

#### Scenario: Persistent red verdict parks the member
- **WHEN** the review stage fails three attempts with the status not
  `success`
- **THEN** the member is parked as needs-human with the PR left open and
  the posted findings intact
