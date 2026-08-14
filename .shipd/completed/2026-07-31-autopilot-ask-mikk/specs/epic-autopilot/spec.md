## ADDED Requirements

### Requirement: Oracle-backed gate enrichment
id: oracle-gate-enrichment

When the built-in gate stage rejects a member (exit 2), the autopilot SHALL
drive exactly one headless enrichment session before parking. The session's
prompt SHALL direct running `/s:plan <member>` — which locates the rejected
change and enters enrichment mode — resolving repository-answerable findings
by editing the artifacts, consulting the ask-mikk oracle (agent `s:oracle`,
one compact question carrying the decision, options, and recommendation per
gap) for decisions the repository cannot answer instead of any human, and
exiting through the re-gate; the session SHALL be graded on the member change
sitting at `ready` lint-clean. After a successful enrichment session the
autopilot SHALL re-run the gate engine and let its verdict decide: a pass
SHALL continue the pipeline; a second rejection SHALL park the member as
`rejected` with a reason naming the failed enrichment and with the enrichment
session id recorded. If the enrichment session fails or its grade stays
unmet, then the member SHALL park as `rejected` with the failure appended to
the reason and the session id recorded — unless the member's worktree
vanished, in which case the vanished-worktree resolution applies. The
autopilot SHALL NOT drive a second enrichment session for the same member in
the same run.

#### Scenario: Enrichment pass continues the pipeline
- **GIVEN** a member whose gate exits 2 and, after the enrichment session,
  exits 0
- **WHEN** the autopilot drives it
- **THEN** exactly one enrichment session runs, the gate runs twice, and the
  pipeline continues into build

#### Scenario: Second rejection parks with the session id
- **GIVEN** a member whose gate exits 2 both before and after the enrichment
  session
- **WHEN** the autopilot drives it
- **THEN** the member parks as rejected with a reason naming the enrichment
  and the enrichment session id, and no second enrichment session runs

#### Scenario: Enrichment failure parks rejected, not needs-human
- **WHEN** the enrichment session errors or its grade stays unmet while the
  worktree still exists
- **THEN** the member parks as rejected with the failure in the reason and
  the session id recorded

### Requirement: Oracle-aware driven sessions
id: oracle-aware-driven-sessions

The canned resume reply the autopilot sends to every driven session SHALL
direct the session to shape any undecided point into a compact question
(decision, options, recommendation), consult the ask-mikk oracle by spawning
agent `s:oracle`, adopt an `ANSWER` verdict, and fall back to its own
recommendation on `INSUFFICIENT` or an unavailable oracle — never waiting
for a human. The build stage prompt SHALL direct the coordinator to route
sub-agent `QUESTION:` escalations that the spec artifacts and code cannot
answer through the same oracle before answering on its own authority.

#### Scenario: Canned reply names the oracle rung
- **WHEN** the autopilot's canned resume reply is inspected
- **THEN** it directs compact-question consultation of agent `s:oracle`,
  adopting `ANSWER` and self-recommending on `INSUFFICIENT`

#### Scenario: Build prompt routes QUESTION escalations
- **WHEN** the build stage prompt is rendered
- **THEN** it directs consulting agent `s:oracle` for sub-agent `QUESTION:`
  escalations the artifacts and code cannot answer

## MODIFIED Requirements

### Requirement: Pipeline-honoring stage execution
id: pipeline-stage-execution
base: 4175fc8c09f0

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

### Requirement: Run report and controls
id: run-report-and-controls
base: 9352511343e6

The autopilot SHALL accept `--max-members`, `--dry-run`, `--timeout`, and
`--max-resumes`; `--dry-run` SHALL print the member order and the
resolved pipeline and drive nothing. Every run SHALL end with a report
listing shipped members with PR URLs, parked members split into rejected
and needs-human — needs-human entries with their session ids, rejected
entries with the enrichment session id when an enrichment session ran —
skipped members with their states, and members unreached due to
`--max-members`; the report SHALL be written machine-readably and
summarized for humans, the summary printing a `claude --resume` pointer
for any parked member whose entry carries a session id. When at least one
member PR merged during the run, the autopilot SHALL finish with the
epic-sync close-out in a fresh worktree.

#### Scenario: Dry run drives nothing
- **WHEN** a run executes with `--dry-run`
- **THEN** the member order and resolved pipeline print and no session,
  gate, or worktree action occurs

#### Scenario: Report accounts for every member
- **GIVEN** a run with one shipped, one rejected (whose enrichment session
  ran), one needs-human, and one unreached member
- **WHEN** the run ends
- **THEN** the report lists each under its outcome, with a PR URL for
  the shipped member and a session id for both the needs-human and the
  rejected member

### Requirement: Deliver skill
id: deliver-skill
base: ad2346d26d2a

An `/s:deliver <epic>` skill SHALL preflight the run — verifying the
epic exists at `ready` or `active`, showing the member roster and the
resolved pipeline, and confirming the run controls with the user — then
run the autopilot driver in the foreground, relay its report, and point
at `claude --resume <session-id>` for each needs-human member. For each
rejected member the relay SHALL note that the automatic oracle-backed
enrichment attempt already failed, point at `/s:plan <member>` as the
manual enrichment entry point, and print `claude --resume <session-id>`
when the report carries the member's enrichment session id. Before
launching the run, the skill SHALL name the dashboard TUI command
(`dashboard.py tui --epic <epic>`) as the live view for watching the run
from another terminal. The skill SHALL NOT plan, build, or answer a
driven session's questions itself.

#### Scenario: Preflight blocks a draft epic
- **WHEN** the skill is invoked for an epic at `draft`
- **THEN** it reports the epic is not approved and drives nothing

#### Scenario: Preflight names the live board
- **WHEN** the skill confirms the run controls before launching
- **THEN** its output names the dashboard TUI command for watching the
  run live

#### Scenario: Report is relayed with HITL pointers
- **WHEN** a run ends with a needs-human member
- **THEN** the skill's summary includes the resume command for that
  member's session

#### Scenario: Rejected member points at plan enrichment
- **WHEN** a run ends with a gate-rejected member
- **THEN** the skill's summary notes the failed automatic enrichment,
  points at `/s:plan <member>` for that member's recovery, and includes
  the resume command when the report carries an enrichment session id
