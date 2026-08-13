## MODIFIED Requirements

### Requirement: Shared session driver
id: shared-session-driver
base: ab0f09a15797

The plugin SHALL ship a stdlib session-driver module exposing a
grade-gated resume loop: drive a headless `claude -p` session in a given
working directory, then, while a supplied grade function has not passed
and fewer than `max_resumes` resumed turns have run, resume the same
session with a supplied reply, returning success, the final session id,
and any failure. If the working directory does not exist when a turn
launches, then the turn SHALL fail with a failure message naming the
missing directory rather than raising. The turn runner SHALL be
injectable so the loop is testable without live sessions, and the eval
runner SHALL consume this module rather than carrying its own copy of
the loop.

#### Scenario: Loop stops when the grade passes
- **GIVEN** an injected runner whose second turn makes the grade pass
- **WHEN** the driver runs with max_resumes 4
- **THEN** exactly two turns run and the result is success

#### Scenario: Exhaustion surfaces the session id
- **GIVEN** an injected runner whose grade never passes
- **WHEN** the driver exhausts max_resumes
- **THEN** the result carries the session id for later interactive resume

#### Scenario: Missing working directory fails the turn, not the process
- **WHEN** a turn launches with a working directory that no longer exists
- **THEN** no exception propagates and the turn result is a failure whose
  message names the missing directory

### Requirement: Pipeline-honoring stage execution
id: pipeline-stage-execution
base: 56428b08874c

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
a PR existing for the member branch; `review` drives a headless
review-post-and-disposition session — its prompt naming the disposition
loop (implement or reply, then resolve) — graded on the head SHA's
`semantic-review` status being `success` **and** the gate's
`resolve --check` reporting zero unresolved threads. Member worktrees
SHALL be created with the plugin's worktree helper. If a member's
worktree no longer exists when a stage starts or after a stage failure —
a driven session may legitimately remove it while shipping the member —
then the autopilot SHALL resolve the member's outcome from the
repository root via the member branch's pull request: a merged PR SHALL
record the member `shipped` with its PR URL and skip the remaining
stages; otherwise the member SHALL park as `needs-human` with a
worktree-vanished reason and the most recent session id. In both cases
the run SHALL continue with the next member.

#### Scenario: Full pass ships a member
- **GIVEN** a member whose plan gates clean and whose build succeeds
- **WHEN** the autopilot drives it
- **THEN** its worktree came from the plugin helper, the change is
  archived, and an auto-merging PR exists for its branch

#### Scenario: Gate rejection parks without retry
- **WHEN** the gate exits 2 on a member's plan
- **THEN** the member is parked as rejected, no re-drive occurs, and the
  run continues with the next member

#### Scenario: Review grade requires disposition, not just green
- **GIVEN** a green `semantic-review` status but one unresolved
  gate-authored thread
- **WHEN** the review stage is graded
- **THEN** the grade does not pass until `resolve --check` reports
  `unresolved=0`

#### Scenario: Skipped gate is honored
- **GIVEN** a resolved pipeline whose gate entry carries skip
- **WHEN** a member is driven
- **THEN** no gate runs between plan and build for that member

#### Scenario: Custom step runs at its position
- **GIVEN** a custom entry between build and review
- **WHEN** a member is driven
- **THEN** the custom command runs in the member's worktree after build

#### Scenario: Vanished worktree with a merged PR records an early ship
- **GIVEN** a build stage whose driven session merged the member's PR and
  removed the member's worktree
- **WHEN** the autopilot's next turn or stage finds the worktree missing
- **THEN** the member is recorded `shipped` with its PR URL, no further
  stages run for it, and the next member is driven

#### Scenario: Vanished worktree without a merged PR parks the member
- **GIVEN** a member whose worktree disappears mid-run while its PR is
  absent or unmerged
- **WHEN** the autopilot resolves the member's outcome
- **THEN** the member parks as needs-human with a worktree-vanished
  reason and the most recent session id, and the run continues
