## MODIFIED Requirements

### Requirement: Pipeline-honoring stage execution
id: pipeline-stage-execution
base: 10909602e618

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
(exit 2) triggers the single oracle-backed enrichment attempt (see
oracle-gate-enrichment) and the member parks as `rejected` only when that
attempt does not end in a gate pass; `build` drives a headless `/s:build`
graded on the change archived under `completed/` and
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

When the pipeline instead completes with the member's worktree still present, the autopilot SHALL resolve the member's outcome from its PR: a merged PR SHALL record the member `shipped` with its URL, while a PR that exists but has not merged SHALL park the member as needs-human at stage `merge` with the PR URL and the most recent session id — never recorded `shipped`. Because the driven build waits for its own PR to merge before returning (build-spec-lifecycle ship-changes-as-prs), the sequential member loop lands each member on a `main` already carrying the prior member, so an unmerged PR at drive end signals a stalled or timed-out ship rather than a success. The run SHALL continue with the next member.

#### Scenario: Full pass ships a member
- **GIVEN** a member whose plan gates clean and whose build succeeds
- **WHEN** the autopilot drives it
- **THEN** its worktree came from the plugin helper, the change is
  archived, and an auto-merging PR exists for its branch

#### Scenario: Gate rejection parks only after the enrichment attempt
- **WHEN** the gate exits 2 on a member's plan and the oracle-backed
  enrichment attempt does not end in a gate pass
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

#### Scenario: Present worktree with an unmerged PR parks the member
- **GIVEN** a member whose pipeline completes with its worktree present but
  whose PR has not merged
- **WHEN** the autopilot resolves the member's outcome
- **THEN** the member parks as needs-human at stage `merge` with the PR URL
  and the most recent session id, is not recorded `shipped`, and the run
  continues with the next member

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

