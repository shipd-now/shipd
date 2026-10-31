# epic-autopilot

### Requirement: Shared session driver
id: shared-session-driver

The plugin SHALL ship a stdlib session-driver module exposing a grade-gated
resume loop: drive a headless session in a given working directory through a
**harness runner**, then, while a supplied grade function has not passed and
fewer than `max_resumes` resumed turns have run, resume the same session with a
supplied reply, returning success, the final session id, and any failure. The
runner SHALL be selected by harness id, so the loop is not tied to one
harness's CLI. If the working directory does not exist when a turn launches,
then the turn SHALL fail with a failure message naming the missing directory
rather than raising. The turn runner SHALL be injectable so the loop is testable
without live sessions, and the eval runner SHALL consume this module rather than
carrying its own copy of the loop.

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

#### Scenario: The loop is harness-agnostic
- **WHEN** a turn runs with `harness="opencode"` and a fake binary that prints
  an OpenCode JSONL transcript
- **THEN** the turn's session id and result text are read from that transcript,
  with the same loop and the same return contract as the `claude` runner

### Requirement: Member selection and order
id: member-selection-and-order

Given an epic at `ready` or `active`, the autopilot SHALL drive only stub
members whose derived state is `unplanned`, ordered in dependency layers
over the stub table's `After` column: an edge runs from each unplanned
member to every `After` slug that is itself unplanned (a dependency in any
other state is satisfied); members with no unsatisfied edge form the next
layer, ordered by the Risk rating ascending (`low`, `medium`, `high`), ties
broken by table order, and the layers are concatenated. Where the table has
no `After` column or every cell is empty, that order SHALL be the
risk-ascending order exactly as before. If the `After` column holds a
dependency cycle, then the autopilot SHALL refuse to run, naming the cycle's
slugs in order and the linter's single-epic mode as the remedy, and SHALL
drive nothing. The dry run SHALL print the order under the label
`Member order (After, then risk ascending):`. Members in any other state
SHALL be reported under that state and left untouched — a `rejected` member
SHALL never be re-driven.

#### Scenario: Risk-ascending order
- **GIVEN** unplanned members rated high, low, and medium in table order and
  no `After` column
- **WHEN** a run starts
- **THEN** the driving order is the low, then medium, then high member

#### Scenario: Declared dependencies order the detached drive
- **GIVEN** unplanned members `a` rated high and `b` rated low, with `b`'s
  `After` cell naming `a`
- **WHEN** a run starts
- **THEN** the driving order is `a` then `b`

#### Scenario: A cycle refuses the run
- **GIVEN** `x` after `y` and `y` after `x` in the stub table
- **WHEN** a run or dry run starts
- **THEN** the autopilot exits non-zero with an error naming `x -> y -> x`
  and drives nothing

#### Scenario: In-flight members are skipped
- **GIVEN** a member whose plan sits at `rejected`
- **WHEN** a run executes
- **THEN** that member is reported as rejected and not driven

### Requirement: Pipeline-honoring stage execution
id: pipeline-stage-execution

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
a PR existing for the member branch — where the resolved configuration
declares `pr-mode: draft` (shipd-config pr-mode-key), the build stage's
driving prompt SHALL name the draft-PR ship (a draft PR, no auto-merge
arming) rather than an auto-merging PR; `review` drives a headless
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
worktree-vanished reason and the most recent session id — regardless of
the resolved `pr-mode`, since a draft-mode build leaves its worktree in
place and a vanished one stays an anomaly. In both cases
the run SHALL continue with the next member.

When the pipeline instead completes with the member's worktree still
present, the autopilot SHALL resolve the member's outcome from its PR: a
merged PR SHALL record the member `shipped` with its URL. Where the
resolved configuration declares `pr-mode: draft`, a PR that exists but has
not merged SHALL record the member `drafted` with its PR URL — the
expected terminal state of a draft-mode ship, never parked — while a
member with no PR at all SHALL still park as needs-human at stage `merge`.
Under the default `auto` mode, a PR that exists but has not merged SHALL
park the member as needs-human at stage `merge` with the PR URL and the
most recent session id — never recorded `shipped` — because the driven
build waits for its own PR to merge before returning (build-spec-lifecycle
ship-changes-as-prs), so an unmerged PR at drive end signals a stalled or
timed-out ship rather than a success. In every case the run SHALL continue
with the next member.

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
- **GIVEN** the default `auto` pr-mode and a member whose pipeline
  completes with its worktree present but whose PR has not merged
- **WHEN** the autopilot resolves the member's outcome
- **THEN** the member parks as needs-human at stage `merge` with the PR URL
  and the most recent session id, is not recorded `shipped`, and the run
  continues with the next member

#### Scenario: Draft mode records a drafted member
- **GIVEN** `pr-mode: draft` resolved and a member whose pipeline
  completes with its worktree present and an open unmerged PR
- **WHEN** the autopilot resolves the member's outcome
- **THEN** the member is recorded `drafted` with its PR URL, is not
  parked, and the run continues with the next member

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

### Requirement: Attempt-budget failure handling
id: three-strike-parking

When a driven stage fails for a non-gate reason — session error or timeout,
grade unmet after the resume budget, or a non-zero replacement or custom
command — the autopilot SHALL re-drive that stage with the failure summary
appended to the prompt, up to that entry's fresh-attempt budget: the entry's
`autopilot.attempts` when declared, else three. A stage still failing after
its final attempt SHALL park the member as `needs-human`, recording the
stage, the reason, and the most recent session id so a human can reopen the
exact conversation with `claude --resume <id>`; the member's worktree SHALL
be left intact and the run SHALL continue with the next member.

#### Scenario: Second attempt can succeed
- **GIVEN** a stage that fails once and succeeds on re-drive under the
  default budget
- **WHEN** the autopilot drives it
- **THEN** the member proceeds and no parking occurs

#### Scenario: Final failure parks with the session id
- **WHEN** a stage fails every attempt of its budget
- **THEN** the member is parked as needs-human with stage, reason, and
  session id, its worktree remains, and the next member starts

### Requirement: Run report and controls
id: run-report-and-controls

The autopilot SHALL accept `--max-members`, `--dry-run`, `--timeout`, and
`--max-resumes`; `--dry-run` SHALL print the member order and the
resolved pipeline and drive nothing. Every run SHALL end with a report
listing shipped members with PR URLs, drafted members with their draft PR
URLs (draft-mode runs), parked members split into rejected
and needs-human — needs-human entries with their session ids, rejected
entries with the enrichment session id when an enrichment session ran —
skipped members with their states, and members unreached due to
`--max-members`; the report SHALL be written machine-readably and
summarized for humans, the summary printing a `claude --resume` pointer
for any parked member whose entry carries a session id. If a parked
entry carries no session id, then the summary SHALL omit the resume
pointer entirely rather than print a null value. When at least one
member PR merged during the run, the autopilot SHALL finish with the
epic-sync close-out in a fresh worktree, invoking the status CLI with a
well-formed invocation (the root option before the subcommand) so the
derivation actually runs; drafted members SHALL NOT trigger the
close-out — it runs only on an actual merge. When the close-out
derivation succeeds and
leaves the close-out worktree unchanged, the autopilot SHALL remove that
worktree and its branch; when it wrote a status change, the summary
SHALL name the worktree path so a human can ship it.

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

#### Scenario: Drafted members are reported distinctly and trigger no close-out
- **GIVEN** a draft-mode run where every driven member ends with an open
  draft PR
- **WHEN** the run ends
- **THEN** the report lists each member under `drafted` with its PR URL,
  the summary renders a `drafted:` line per member, and no epic-sync
  close-out runs

#### Scenario: Parked without a session omits the pointer
- **WHEN** the summary renders a needs-human member whose entry has no
  session id (parked before any session started)
- **THEN** the line carries the member, stage, and reason but no
  `claude --resume` fragment

#### Scenario: Close-out derivation runs
- **WHEN** the close-out invokes the status CLI in the fresh worktree
- **THEN** the invocation is accepted and the derived epic status is
  relayed in the run output

#### Scenario: No-op close-out cleans up
- **WHEN** the close-out sync exits zero without writing a status change
- **THEN** the close-out worktree and its branch are removed

#### Scenario: Written close-out is handed to a human
- **WHEN** the close-out sync writes a changed epic status
- **THEN** the summary names the close-out worktree path for a human to
  ship

### Requirement: Autopilot skill
id: deliver-skill

An `/s:autopilot <epic>` skill SHALL preflight the run by running
`autopilot.py <epic> --preflight`, relaying every `ok|warn|fail` line; if any
line is `fail`, then the skill SHALL stop before the run controls are
confirmed, naming the failing lines and their remedies, and drive nothing.
It SHALL then show the member roster and the resolved pipeline, carry every
`warn` line into the confirmation brief, and confirm the run controls with
the user — the last question of the run — before driving the epic and
relaying its report. The skill SHALL default to the **in-session drive**, and
SHALL use the detached `claude -p` driver only when the invocation asks for a
detached run; the confirmation SHALL name which mode the run will use, and
for the in-session drive SHALL include a `--parallel N` control — the number
of members driven concurrently, default 3, where 1 is a serial run — and
SHALL show the waves the driver's `--waves` mode computes for that value.
When the run is detached, the skill SHALL run the driver in the foreground,
point at `claude --resume <session-id>` for each needs-human member, and for
each rejected member note that the automatic oracle-backed enrichment
attempt already failed, point at `/s:plan <member>` as the manual enrichment
entry point, and print `claude --resume <session-id>` when the report
carries the member's enrichment session id. Before launching either mode,
the skill SHALL name the dashboard TUI command (`dashboard.py tui --epic
<epic>`) as the live view. The skill SHALL keep `deliver` among its trigger
phrases so the former `/s:deliver` vocabulary still resolves to it. The
skill SHALL NOT plan or build a member itself in either mode and SHALL NOT
answer a driven session's questions; in the in-session mode a failure parks
the member rather than asking.

#### Scenario: Preflight blocks a draft epic
- **WHEN** the skill is invoked for an epic at `draft`
- **THEN** the preflight's `epic-status` line is `fail`, the skill reports the
  epic is not approved, and drives nothing

#### Scenario: A failing preflight stops before the confirmation
- **GIVEN** a preflight whose `members` line is `fail`
- **WHEN** the skill runs Phase 1
- **THEN** it prints the failing line with its remedy, asks nothing, and
  drives nothing

#### Scenario: Warn lines reach the confirmation
- **GIVEN** a preflight with a `warn drift —` line and no `fail`
- **WHEN** the skill confirms the run controls
- **THEN** the brief carries that line and the run may proceed

#### Scenario: In-session is the default
- **WHEN** the skill is invoked for an approved epic with no detached request
- **THEN** the run confirmed with the user is the in-session drive and no
  headless `claude -p` process is started

#### Scenario: The parallel control is confirmed with its waves
- **WHEN** the skill confirms an in-session run
- **THEN** the controls include `--parallel` with default 3 and the
  confirmation shows the waves computed for that value

#### Scenario: A detached run is opted into
- **WHEN** the invocation asks for a detached run
- **THEN** the skill runs the driver in the foreground as before and relays its
  report

#### Scenario: Preflight names the live board
- **WHEN** the skill confirms the run controls before launching
- **THEN** its output names the dashboard TUI command for watching the run live

#### Scenario: Report is relayed with HITL pointers
- **WHEN** a detached run ends with a needs-human member
- **THEN** the skill's summary includes the resume command for that member's
  session

#### Scenario: Rejected member points at plan enrichment
- **WHEN** a detached run ends with a gate-rejected member
- **THEN** the skill's summary notes the failed automatic enrichment, points at
  `/s:plan <member>` for that member's recovery, and includes the resume command
  when the report carries an enrichment session id

#### Scenario: The deliver vocabulary still resolves
- **WHEN** the user invokes the skill by asking to "deliver" an epic
- **THEN** the `/s:autopilot` skill is the one that answers

### Requirement: Oracle-backed gate enrichment
id: oracle-gate-enrichment

When the built-in gate stage rejects a member (exit 2), the autopilot SHALL
drive one oracle-backed enrichment phase before parking: headless enrichment
sessions retried on session failure or unmet grade up to the gate entry's
fresh-attempt budget (`autopilot.attempts`, default three), each session
using the gate entry's declared model, timeout, and max-resumes. The
session's prompt SHALL direct running `/s:plan <member>` — which locates the
rejected change and enters enrichment mode — resolving repository-answerable
findings by editing the artifacts, consulting the oracle inline (one `spec_status.py oracle-lookup` run per gap's compact question carrying the decision, options, and recommendation, judged per the oracle consultation contract) for decisions the repository cannot answer instead
of any human, and exiting through the re-gate; each session SHALL be graded
on the member change sitting at `ready` lint-clean. After a successful
enrichment session the autopilot SHALL re-run the gate engine and let its
verdict decide: a pass SHALL continue the pipeline; a second rejection SHALL
park the member as `rejected` with a reason naming the failed enrichment and
the enrichment session id recorded. If every enrichment attempt fails or
its grade stays unmet, then the member SHALL park as `rejected` with the
failure appended to the reason and the session id recorded — unless the
member's worktree vanished, in which case the vanished-worktree resolution
applies. The autopilot SHALL NOT drive a second enrichment phase for the
same member in the same run.

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
  and the enrichment session id, and no second enrichment phase runs

#### Scenario: Exhausted enrichment budget parks rejected, not needs-human
- **WHEN** every enrichment attempt of the gate entry's budget errors or
  leaves its grade unmet while the worktree still exists
- **THEN** the member parks as rejected with the failure in the reason and
  the session id recorded

### Requirement: Oracle-aware driven sessions
id: oracle-aware-driven-sessions

The canned resume reply the autopilot sends to every driven session SHALL
direct the session to shape any undecided point into a compact question
(decision, options, recommendation), consult the oracle by running `spec_status.py oracle-lookup`, named by its absolute path, and judging its output per the oracle consultation contract, adopt an `ANSWER` verdict, and fall back to its own
recommendation on `INSUFFICIENT` or an unavailable oracle — never waiting
for a human. The build stage prompt SHALL direct the coordinator to route
sub-agent `QUESTION:` escalations that the spec artifacts and code cannot
answer through the same oracle before answering on its own authority.

#### Scenario: Canned reply names the oracle rung
- **WHEN** the autopilot's canned resume reply is inspected
- **THEN** it directs compact-question consultation through `oracle-lookup`,
  adopting `ANSWER` and self-recommending on `INSUFFICIENT`

#### Scenario: Build prompt routes QUESTION escalations
- **WHEN** the build stage prompt is rendered
- **THEN** it directs consulting `oracle-lookup` for sub-agent `QUESTION:`
  escalations the artifacts and code cannot answer

### Requirement: Targeted single-member drive
id: targeted-member-drive

The autopilot SHALL support driving a single epic member selected by slug —
independent of the epic-level auto-selection — entering the resolved
`autonomous-pipeline` at the stage matching that member's current lifecycle
state: an `unplanned` member from `plan`, a `ready` (planned, lint-clean) member
from `build`, skipping the stages already satisfied. The targeted drive SHALL
reuse the same worktree, graded stage loop, heartbeat, and park/ship semantics as
an epic run, drive exactly the one named member, and back the board's per-card
`run` action. It SHALL leave the epic-level `member-selection-and-order`
auto-selection unchanged.

#### Scenario: A ready member enters at build
- **GIVEN** an epic member whose plan sits at `ready`, lint-clean
- **WHEN** a targeted single-member drive runs for that member
- **THEN** the pipeline starts at `build` — `plan` and `gate` are skipped — and
  the member is driven through to its terminal outcome

#### Scenario: An unplanned member enters at plan
- **GIVEN** an epic member whose derived state is `unplanned`
- **WHEN** a targeted single-member drive runs for that member
- **THEN** the pipeline starts at `plan`, and no other member is driven

#### Scenario: Auto-selection is untouched
- **WHEN** a normal epic run (no targeted member) is driven
- **THEN** members are still selected and ordered over the `unplanned` set
  exactly as `member-selection-and-order` states

### Requirement: Stale worktree reclaim
id: stale-worktree-reclaim

If a member's worktree creation fails and the failure output contains `already
exists`, then the autopilot SHALL attempt a reclaim before parking: remove the
leftover worktree through the guarded `worktree.sh remove` verb invoked with
the activity guard disabled (`SHIPD_WORKTREE_IDLE_MINUTES=0`) and every other
guard in force, delete the leftover `change/<slug>` branch with a merged-only
delete (`git branch -d`), and retry the creation exactly once. If the guarded
remove refuses or the merged-only branch delete fails, the autopilot SHALL
park the member `needs_human` at the `worktree` stage with that command's
output as the reason and SHALL NOT force the removal. A creation failure whose
output does not contain `already exists` SHALL park the member exactly as
before, with no reclaim attempt. Every reclaim command SHALL run through the
autopilot's command seam so the sequence is testable without git.

#### Scenario: Clean leftover is reclaimed and the drive proceeds
- **GIVEN** worktree creation fails with `already exists` and the guarded
  remove, branch delete, and retried creation all succeed
- **WHEN** the autopilot drives the member
- **THEN** the member proceeds into its stage pipeline instead of parking

#### Scenario: Guard refusal parks with the refusal as reason
- **GIVEN** worktree creation fails with `already exists` and the guarded
  remove exits non-zero (e.g. a dirty tree)
- **WHEN** the autopilot drives the member
- **THEN** the member parks `needs_human` at the `worktree` stage with the
  refusal output as its reason, and no forced removal occurs

#### Scenario: Unmerged branch parks instead of losing work
- **GIVEN** the guarded remove succeeds but `git branch -d` fails because the
  branch is not fully merged
- **WHEN** the autopilot drives the member
- **THEN** the member parks `needs_human` with the delete failure as its
  reason and the branch is left in place

#### Scenario: Other creation failures park unchanged
- **GIVEN** worktree creation fails with output not containing `already exists`
- **WHEN** the autopilot drives the member
- **THEN** the member parks `needs_human` at the `worktree` stage as before and
  no reclaim command runs

### Requirement: In-session sub-agent drive
id: in-session-drive

The autopilot skill SHALL provide an in-session drive that runs the epic's
members within the current Claude Code session in waves, walking the
resolved pipeline's entry list per member and spawning one general-purpose
sub-agent per built-in stage entry it runs, with that stage's instruction
and the member's worktree as its working directory. It SHALL take the
member grouping and order from the driver's `--waves` mode, invoked with
the run's confirmed `--parallel` value, and the resolved entry list from
the status CLI's `pipeline-show --json` machine contract, deriving neither
itself. For each wave it SHALL spawn the current entry's sub-agent for
every member of the wave together, in the background, wait for all of them,
grade each from disk, advance each passing member to its next entry, and
repeat until every member of the wave has finished its walk, running the
pre-build drift step before a member's first `build` entry. After each wave
completes it SHALL re-run `--waves`, filtered of parked and held members,
and continue with the first runnable wave returned, until none remains and
no dependency is being waited for. It SHALL enter each member's pipeline at
the first entry whose stage matches the member's state — `unplanned` at
plan, `ready` at build — treating every entry before that point, custom
entries included, as already satisfied and not running it; and SHALL leave
members in any other state undriven, reporting them with their state. With
`--parallel 1` the drive SHALL behave exactly as a one-member-at-a-time walk.

#### Scenario: Ordering comes from the waves mode, entries from the machine contract
- **WHEN** an in-session drive begins
- **THEN** the member grouping and order are the ones `--waves` printed for
  the confirmed cap, the entry list is the one `pipeline-show --json`
  emitted, and the waves mode performed no session, gate, or worktree action

#### Scenario: A wave's members run together
- **GIVEN** a build wave of two members
- **WHEN** the drive runs that wave
- **THEN** both members' build sub-agents are spawned before either is
  graded, and each member's next entry starts only after its own grade
  passes

#### Scenario: Waves are recomputed after each wave
- **GIVEN** a plan wave whose members all reach `ready`
- **WHEN** that wave completes
- **THEN** the drive re-runs `--waves` and those members appear in the
  build waves it runs next

#### Scenario: Entry stage matches the member's state
- **GIVEN** one member at `unplanned` and one at `ready`, and a custom
  entry between the plan and build entries
- **WHEN** the in-session drive reaches each member
- **THEN** the first enters at the plan entry, and the second enters at the
  build entry with the plan entry and the earlier custom entry not run

#### Scenario: A stage runs as a sub-agent in the member's worktree
- **WHEN** a built-in stage entry runs under the in-session drive
- **THEN** a sub-agent is spawned for it whose working directory is that
  member's worktree, and no headless `claude -p` process is started

#### Scenario: Non-drivable members are skipped and reported
- **GIVEN** a member whose state is neither `unplanned` nor `ready`
- **WHEN** the in-session drive selects members
- **THEN** it is left untouched and named in the run's summary with its
  state

#### Scenario: A launched run starts with build waves
- **GIVEN** an epic whose preflight passed
- **WHEN** the drive's first `--waves` call returns
- **THEN** every wave is a build wave, because no member is `unplanned`

#### Scenario: A parked member leaves the waves
- **GIVEN** a member parked during the previous wave that still reads
  `ready` on disk
- **WHEN** the drive re-runs `--waves`
- **THEN** that member is dropped from the returned waves and not started
  again

### Requirement: In-session stages are graded from disk
id: in-session-disk-grading

The in-session drive SHALL decide whether a stage passed by reading the
repository, never by trusting the sub-agent's report: the plan stage passes only
when the change's status is `ready` and it lints clean; the build stage only when
an archived change directory for the member exists and its branch has a pull
request; the review stage only when the pull request head carries a successful
`semantic-review` status and no gate-authored finding thread is unresolved.

#### Scenario: A sub-agent's success claim does not pass the stage
- **GIVEN** a sub-agent that reports the plan stage complete while the change's
  status is still `draft`
- **WHEN** the drive grades that stage
- **THEN** the stage is not treated as passed

#### Scenario: Plan stage passes on status and lint
- **WHEN** the plan stage's sub-agent leaves the change at `ready` and the change
  lints clean
- **THEN** the stage passes and the drive advances to the next stage

#### Scenario: Review stage requires both the status and resolved threads
- **GIVEN** a pull request whose `semantic-review` status is successful but which
  has an unresolved gate-authored finding thread
- **WHEN** the drive grades the review stage
- **THEN** the stage does not pass

### Requirement: In-session runs register as active on the delivery board
id: in-session-board-liveness

The in-session drive SHALL emit the per-change build heartbeat around each member
it drives — starting it when the member begins, stamping the stage as each is
entered, and finishing it with the member's outcome — so the board's activity
indicator reports the run as active rather than idle. A driven member's **card**
SHALL continue to be placed by its on-disk lifecycle state, which the board
already derives; the drive SHALL NOT be required to move a card into the building
lane, because lane placement reads the epic-level run heartbeat that only the
detached driver writes. A heartbeat failure SHALL NOT stop the drive.

#### Scenario: The run registers as active, not idle
- **WHEN** the in-session drive is part-way through a member
- **THEN** the board's activity indicator reports building rather than idle

#### Scenario: A card follows its on-disk state, not the build heartbeat
- **GIVEN** a member driven from `unplanned` whose plan stage has not yet written
  an artifact
- **WHEN** the board places that member's card
- **THEN** the card sits in the lane its on-disk state selects, and the live
  build heartbeat does not move it

#### Scenario: Heartbeat failure does not stop the drive
- **GIVEN** a heartbeat write that fails
- **WHEN** the in-session drive continues
- **THEN** the drive proceeds to the next stage unaffected

### Requirement: Symbolic model-tier resolution
id: stage-model-resolution

The engine SHALL export, stdlib-only in `spec_common`, `EFFORT_LEVELS` —
exactly `high`, `medium`, `low` — and a `STAGE_EFFORT` map giving every
pipeline stage a default level: the planning stages (`plan`, `enrich`,
`replan`, `epic`) `high`, the implementation and judgement stages (`build`,
`review`) `medium`, and every other stage `low`. It SHALL export a pure
`resolve_effort(stage, declared=None)` resolving to the level a stage runs at:
`declared` when it names `session` or an effort level, `declared` verbatim when
it is a concrete model id, else the stage's default level.

The session driver's runners SHALL express a resolved level through the
harness's own knob: the `claude` runner SHALL render `--effort <level>`, the
`opencode` runner SHALL render `--model <base>#<level>` using the optional
config `model` base and SHALL render no model or effort flag when no base is
declared, and both SHALL render a concrete model id as `--model <id>`.
`session` SHALL render no model or effort flag, so the harness's own default
decides.

When a driven stage's resolved pipeline entry declares `model`, the autopilot
SHALL use that value; otherwise it SHALL use the stage's default level. The
autopilot SHALL accept a `--session-model` control naming the model `session`
inherits, SHALL print each stage's resolved level and the acting anchor in its
dry run, and SHALL record both in the run report.

#### Scenario: Session tier inherits the CLI default
- **GIVEN** a plan entry declaring `"model": "session"` and no anchor
- **WHEN** the autopilot drives the plan stage
- **THEN** the driven session is launched without a `--model` or `--effort`
  flag

#### Scenario: Concrete ids pass through verbatim
- **WHEN** an entry declares `"model": "claude-fable-5"`
- **THEN** the driven session is launched with `--model claude-fable-5`

#### Scenario: A stage defaults to its effort level
- **WHEN** the pipeline's `plan`, `build`, and `gate` stages declare no `model`
- **THEN** their levels resolve to `high`, `medium`, and `low`

#### Scenario: An entry overrides its stage's level
- **WHEN** a `build` entry declares `"model": "high"`
- **THEN** its level resolves to `high` rather than the stage default

#### Scenario: The claude runner expresses a level as effort
- **WHEN** the `claude` runner renders the level `high`
- **THEN** its argv carries `--effort high` and no `--model`

#### Scenario: The opencode runner expresses a level as a model variant
- **WHEN** the `opencode` runner renders the level `medium` with the base
  `provider/model` declared
- **THEN** its argv carries `--model provider/model#medium`, and with no base
  declared it carries no model flag

#### Scenario: The dry run prints the stage levels
- **WHEN** the autopilot dry-runs a repository
- **THEN** its output names each stage's resolved level and the acting anchor,
  and the run report records them

### Requirement: Stage options conveyed in stage prompts
id: stage-options-in-prompts

When a resolved build entry declares `validator` false, `telemetry` false,
`parallelism`, or `subagent_model`, the build stage prompt SHALL convey each
declared option to the driven session — the validator phase skipped, the
telemetry reporting skipped, the sub-agent cap, and the sub-agent model as
the concrete value resolved against the build session's own model with its
symbolic form named alongside. When a resolved review entry declares
`disposition` or `model`, the review stage prompt SHALL append the matching
`--disposition` and `--model` options to its poster invocation and SHALL
match the disposition-loop instruction to the scope: `high-only` implements
high-severity findings and runs `review_gate.py autoreply` with that scope
on the rest before `resolve`; `none` posts, autoreplies every finding, and
resolves. An entry declaring none of these options SHALL produce the prompt
unchanged from the optionless behavior, and the review grade SHALL remain
the green `semantic-review` status plus `unresolved=0`. The dry run's entry
labels SHALL render each entry's declared options.

#### Scenario: Build options reach the build prompt
- **GIVEN** a build entry with `validator` false, `telemetry` false,
  `parallelism` 2, and `subagent_model` `tier-two-below`
- **WHEN** the build prompt is rendered
- **THEN** it directs skipping the validator phase and telemetry, caps
  sub-agents at 2, and names the resolved sub-agent model with its
  `tier-two-below` provenance

#### Scenario: Review scope reaches the poster and the loop
- **GIVEN** a review entry with `disposition` `high-only` and `model`
  `tier-below`
- **WHEN** the review prompt is rendered
- **THEN** its poster invocation carries `--disposition high-only` and
  `--model tier-below`, and the loop instruction directs implementing
  high-severity findings and `autoreply` on the rest before `resolve`

#### Scenario: Bare entries keep today's prompts
- **WHEN** the build and review prompts render for entries declaring no
  options
- **THEN** each prompt is unchanged from the optionless rendering

#### Scenario: Dry-run labels show declared options
- **GIVEN** a pipeline whose gate entry declares `autopilot.attempts` 1
- **WHEN** the dry run prints the resolved pipeline
- **THEN** the gate entry's label renders the declared option

### Requirement: Per-stage driver knobs
id: per-stage-driver-knobs

When a resolved stage or custom entry carries an `autopilot` block, the
autopilot SHALL use its `attempts` as that entry's fresh-attempt budget in
place of the fixed three — governing driven-session re-drives, replacement
and custom command retries, and, on the gate entry, both the gate-engine
retry loop and the enrichment-session loop — and SHALL use its `timeout`
and `max_resumes` for that stage's sessions in place of the run-global
values. If an entry carries no `autopilot` block or omits a key, then the
defaults SHALL apply: three attempts and the run-global timeout and
max-resumes.

#### Scenario: A one-attempt build parks on first failure
- **GIVEN** a build entry with `autopilot.attempts` 1 and a failing session
- **WHEN** the autopilot drives the member
- **THEN** exactly one build session runs before the member parks

#### Scenario: Gate attempts govern the enrichment loop
- **GIVEN** a gate entry with `autopilot.attempts` 1 and a gate that rejects
  before and after enrichment
- **WHEN** the autopilot drives the member
- **THEN** exactly one gate-engine call precedes enrichment, at most one
  enrichment session runs, and the member parks rejected

#### Scenario: Per-stage timeout overrides the run-global value
- **GIVEN** a plan entry whose `autopilot.timeout` differs from the run's
  `--timeout`
- **WHEN** the plan session is driven
- **THEN** the session receives the entry's timeout, and stages without an
  override receive the run-global value

### Requirement: In-session stage options
id: in-session-stage-options

The in-session drive SHALL obtain the resolved pipeline entries and each
entry's declared options by running the status CLI's `pipeline-show --json`
verb once per run, reading the validated entry dicts from the emitted
object's `entries` — never by parsing the dry run's rendered entry labels,
which are human-facing only. The dry run remains the sole source of the
member order. Where a resolved entry declares `model`, the in-session drive
SHALL spawn that stage's sub-agent with the Agent tool's model parameter
set to the tier resolved relative to the current session (a concrete ladder
alias passed verbatim). The in-session drive's stage instructions SHALL
mirror the detached driver's prompts, conditional option lines included,
and it SHALL ignore `autopilot` blocks entirely — interactively the human
is the retry loop.

#### Scenario: Options are read from the JSON entries
- **GIVEN** a resolved build entry declaring `subagent_model`
  `tier-two-below` and `validator` false
- **WHEN** the in-session drive prepares that member's build stage
- **THEN** the options come from the `pipeline-show --json` object's entry
  dicts, not from the dry run's rendered labels

#### Scenario: A declared model reaches the Agent spawn
- **GIVEN** a resolved build entry declaring `model` `tier-below`
- **WHEN** the in-session drive spawns the build stage's sub-agent
- **THEN** the spawn's model parameter carries the tier resolved one step
  below the current session

#### Scenario: Autopilot blocks are ignored in-session
- **GIVEN** a resolved entry carrying `autopilot.attempts` 1
- **WHEN** the in-session drive runs that stage
- **THEN** no retry budget is enforced from it — a failed stage stops and
  asks the user exactly as before

### Requirement: Close-out worktree starts from a fresh branch
id: close-out-fresh-branch

When the autopilot runs its epic-sync close-out, it SHALL create the
`epic-close-<slug>` worktree by invoking the worktree helper with its
fresh-branch flag (`--fresh`), so the derivation never adopts a stale local
`change/epic-close-<slug>` branch left over from an earlier run. If that
fresh creation fails (an existing worktree or an unmerged leftover branch),
then the close-out SHALL be skipped with the helper's error relayed in the
run output, exactly as any other close-out worktree failure is.

#### Scenario: Close-out invokes the helper with the fresh flag
- **WHEN** the autopilot's close-out creates its `epic-close-<slug>` worktree
- **THEN** the worktree helper invocation carries the `--fresh` flag

#### Scenario: Refused fresh creation skips the close-out audibly
- **GIVEN** the helper exits non-zero because the leftover
  `change/epic-close-<slug>` branch is unmerged
- **WHEN** the close-out runs
- **THEN** the close-out is skipped and the run output relays the helper's
  error

### Requirement: In-session entry-form fidelity
id: in-session-entry-forms

Per driven member, the in-session drive SHALL execute the resolved
pipeline's entries in order under the same entry contract the detached
driver honors. A `skip: true` entry SHALL be announced and not run. A
`custom` entry SHALL run its `command` via Bash in the member's worktree at
its list position. A `replace` entry declaring a `command` SHALL run that
command via Bash in the member's worktree in place of the built-in stage
behavior, with no stage sub-agent spawned; if a `replace` entry names only
a `tool`, then the drive SHALL announce the entry and skip it. A command
entry (custom or replacement) SHALL pass on exit 0, graded on the exit
code the drive itself observed; if it exits non-zero, then the drive SHALL
stop and put the failure to the user with the member and entry named, per
the in-session failure contract — never parking. Where a stage entry run
as a sub-agent declares `tools`, the stage instruction SHALL end with the
detached driver's verbatim suffix — `Preferred tools for this stage, use
when available: <name> (fallback: <fallback>); ...`. `research` and `epic`
entries SHALL be noted as pre-approval stages and ignored.

#### Scenario: Skipped gate is honored in-session
- **GIVEN** a resolved pipeline whose gate entry carries `skip: true`
- **WHEN** a member is driven in-session
- **THEN** no gate runs between plan and build for that member and the
  skip is announced

#### Scenario: Custom step runs at its position
- **GIVEN** a custom entry between the build and review entries
- **WHEN** a member is driven in-session
- **THEN** the custom command runs via Bash in the member's worktree after
  the build stage and before the review stage

#### Scenario: Replacement runs instead of the built-in
- **GIVEN** a build entry whose `replace` declares a `command`
- **WHEN** the drive reaches that entry
- **THEN** the command runs via Bash in the member's worktree, no build
  sub-agent is spawned, and exit 0 passes the entry

#### Scenario: Tool-only replacement is skipped audibly
- **GIVEN** a stage entry whose `replace` names only a `tool`
- **WHEN** the drive reaches that entry
- **THEN** the entry is announced and skipped and the built-in behavior
  does not run

#### Scenario: Tools reach the stage instruction
- **GIVEN** a plan entry declaring a `tools` binding with a fallback
- **WHEN** that stage's sub-agent is spawned
- **THEN** its instruction ends with the preferred-tools suffix naming the
  tool and its fallback

#### Scenario: Failing command entry stops and asks
- **GIVEN** a custom entry whose command exits non-zero
- **WHEN** the drive observes the exit
- **THEN** the drive stops and tells the user which member and entry
  failed, and no further member starts until they answer

#### Scenario: Pre-approval entries are ignored
- **GIVEN** the default pipeline, whose list opens with `research` and
  `epic` entries
- **WHEN** an unplanned member is driven in-session
- **THEN** neither entry runs and the member's drive proceeds from the
  plan entry

### Requirement: Stage sub-agent reporting contract
id: stage-subagent-reporting

The build and autopilot skills SHALL state the sub-agent → orchestrator
reporting contract: a driven stage sub-agent that cannot message its
parent SHALL end its turn with its report as the turn's final text, and
when the build skill runs as a driven stage sub-agent it SHALL run its PR
watch to a terminal state in the foreground of its own turn rather than
ending the turn with the outcome pending on a background process. The
in-session orchestrator SHALL grade stages from the repository and SHALL
NOT depend on a sub-agent's own background watch completing.

#### Scenario: Report arrives as final turn text
- **WHEN** a driven stage sub-agent finishes its stage
- **THEN** its report is the final text of its turn, and no mid-run
  message to the orchestrator is required for the stage to be graded

#### Scenario: Orchestrator never waits on a sub-agent's watch
- **GIVEN** a build stage sub-agent whose turn has ended
- **WHEN** the orchestrator grades the build stage
- **THEN** the grade reads the archived change and the branch's PR from
  the repository, and no watch left in the sub-agent's context is awaited

#### Scenario: Driven build watches in the foreground
- **WHEN** the build skill runs as a driven stage sub-agent and reaches
  its PR watch
- **THEN** it polls the watch within its own turn and ends the turn with
  the completion report once a terminal state is reached

### Requirement: Member wave scheduling
id: member-wave-scheduling

The autopilot driver SHALL provide a `--waves` mode (`autopilot.py <epic>
--waves [--parallel N] [--json]`) that computes, from on-disk state and the
local git refs alone, the waves of members the in-session drive may run
concurrently, and drives nothing. `--parallel` SHALL be an integer of at
least 1, default 3, and SHALL cap every wave's size. If the stub table's
`After` column holds a dependency cycle, then the mode SHALL exit non-zero
with an error naming the cycle's slugs in order and SHALL print no wave.
The mode SHALL emit plan waves first over the `unplanned` members. Where the
epic's stub table carries an `After` column with at least one non-empty
cell, plan waves SHALL be dependency layers: an edge runs from each unplanned
member to every `After` slug that is itself unplanned (a dependency in any
other state is satisfied); members with no unsatisfied edge form the next
layer, ordered risk-ascending then by table order and chunked into waves of
at most N. Where no non-empty `After` cell exists, plan waves SHALL be every
`unplanned` member in risk-ascending order (ties by table order), chunked
into waves of at most N, exactly as before. Each plan wave SHALL be tagged
stage `plan`. It SHALL then emit build waves over the `ready` members: each
member's capabilities are the capability directory names under its planned
change's `specs/`, read from the root that hosts the change. A `ready`
member whose `After` cell names a dependency not yet merged into the base
branch SHALL join no wave and SHALL be listed as blocked with the unmerged
slugs; a dependency counts as merged exactly when the base branch's tree —
`origin/main` where that ref exists, else `main`, read with `git ls-tree`
from the repository root — holds a `completed/` entry whose name is a
leading digits-and-dashes prefix followed by `-<slug>`, and any git failure
counts as not merged. Walking the remaining members in risk-ascending order,
each member joins the earliest build wave whose members' capabilities are
all disjoint from its own and whose size is below N, else opens a new wave.
Members in any other state SHALL be listed as skipped with their state. With
`--json` the mode SHALL print one object `{"epic", "parallel", "waves":
[{"index", "stage", "members": [{"slug", "risk", "capabilities",
"after"}]}], "blocked": [{"member", "waiting_on"}], "skipped": [{"member",
"state"}]}`, `after` being the member's declared `After` slugs (empty
without the column) and `blocked` always present; without it, one
`wave <index> [<stage>]:` line per wave naming its members and, for build
waves, each member's capabilities, and for plan waves each member's
`after` list when non-empty, then one `blocked: <slug> (waiting on <slugs>)`
line per blocked member. The computation SHALL be deterministic for a given
tree and set of refs.

#### Scenario: Plan waves chunk unplanned members risk-ascending
- **GIVEN** unplanned members rated high, low, low, and medium, no `After`
  column, and `--parallel 2`
- **WHEN** `--waves` runs
- **THEN** the first wave is the two low members and the second is the
  medium then the high member, both tagged `plan`

#### Scenario: Declared dependencies layer the plan waves
- **GIVEN** an `After` column making `b` after `a`, and `c`, `d`, `e` after
  `b`, all unplanned, with `--parallel 3`
- **WHEN** `--waves` runs
- **THEN** the plan waves are `[a]`, `[b]`, `[c, d, e]`, and each member
  entry carries its `after` list

#### Scenario: A satisfied dependency does not block
- **GIVEN** `b` after `a` where `a` is already `ready`
- **WHEN** `--waves` runs
- **THEN** `b` sits in the first plan wave and `a` in a build wave

#### Scenario: A cycle refuses the waves mode
- **GIVEN** `x` after `y` and `y` after `x`, and a free unplanned `z`
- **WHEN** `--waves` runs
- **THEN** the mode exits 1 with an error naming `x -> y -> x` and prints no
  wave

#### Scenario: An unmerged dependency blocks a build wave
- **GIVEN** ready members `a` and `b` with disjoint capabilities, `b` after
  `a`, and the base branch's tree holding no `completed/` entry for `a`
- **WHEN** `--waves --json` runs
- **THEN** the only build wave is `[a]` and `blocked` is
  `[{"member": "b", "waiting_on": ["a"]}]`

#### Scenario: A merged dependency releases its dependent
- **GIVEN** ready member `b` after `a`, and the base branch's tree holding
  `completed/2026-10-15-a`
- **WHEN** `--waves` runs
- **THEN** `b` joins a build wave and `blocked` is empty

#### Scenario: A suffix match is not a merge
- **GIVEN** ready member `b` after `a`, and the base branch's tree holding
  only `completed/2026-10-15-extra-a`
- **WHEN** `--waves` runs
- **THEN** `b` is blocked waiting on `a`

#### Scenario: Disjoint capabilities share a build wave
- **GIVEN** ready members `a` touching capability `x`, `b` touching `y`, and
  `c` touching `x` and `z`, with `--parallel 3`
- **WHEN** `--waves` runs
- **THEN** `a` and `b` share the first build wave and `c` sits alone in the
  second

#### Scenario: The cap splits a wave
- **GIVEN** four ready members with pairwise-disjoint capabilities and
  `--parallel 3`
- **WHEN** `--waves` runs
- **THEN** the first build wave holds three members and the second holds one

#### Scenario: Waves drive nothing
- **WHEN** `--waves` runs
- **THEN** no session, gate, worktree, or heartbeat action occurs and the
  exit code is 0

#### Scenario: A capability is read from the hosting worktree
- **GIVEN** a ready member whose planned change lives under
  `.worktrees/<member>/` rather than the root
- **WHEN** `--waves` runs
- **THEN** that member's capabilities are the `specs/` directory names of
  that worktree's planned change

#### Scenario: Serial cap reproduces today's order
- **WHEN** `--waves --parallel 1` runs on an epic without an `After` column
- **THEN** every wave holds exactly one member: the unplanned members in
  the same order the dry run prints, followed by the ready members in
  risk-ascending order with ties by table order

### Requirement: Launch preflight rubric
id: launch-preflight

The autopilot driver SHALL provide a read-only `--preflight` mode
(`autopilot.py <epic> --preflight [--json]`) that composes a launch rubric
from on-disk state, local git, and the engine's own verbs, drives nothing,
and prints one `ok|warn|fail <check> — <detail>` line per check in the
`shipd doctor` format followed by a `preflight: ok` or `preflight: <n>
problem(s)` summary, exiting non-zero exactly when at least one line is
`fail`. The checks, in order, SHALL be: `epic-lint` (the single-epic lint,
`fail` on any error); `epic-status` (`ok` at `ready` or `active`, `fail`
otherwise naming the remedy); `after-cycle` (`fail` naming the cycle's
slugs as `a -> b -> a`); `members` (`fail` when any member is `unplanned`,
`draft`, or `rejected`, naming the members per state and `/s:epic-grill
<epic>` for the first two and `/s:plan <member>` for a rejected one; `warn`
naming members mid-build; `ok` when every member is `ready` or `archived`);
`gate-check` (one `spec_gate.py <member> --check` run per `ready` member
from its hosting root, `fail` naming the member and its first finding on a
non-zero exit other than a `gated-hash mismatch`); `gated-hash` (`fail`
naming the member and `spec_gate.py <member>` when its check reported a
`gated-hash mismatch`, `warn` when a `ready` plan carries no `Gated-hash`
stamp); `drift` (one `spec_status.py drift --epic <epic> --json` run, `warn`
naming each drifted member with its finding counts and `/s:drift <epic>`
on exit 4, `fail` on any other non-zero exit); `overlap-requirements`
(`fail` naming each pair of planned members whose delta specs modify,
remove, or rename the same master requirement while neither reaches the
other through the `After` graph); `overlap-files` (`warn` naming each such
unordered pair citing the same path in `plan.md`, `tasks.md`, or a delta
spec, with `artefacts/` references and the version-bump exempt paths
ignored); `pipeline` (`ok` with the entry count and provenance, `fail` when
the pipeline does not resolve); then every `shipd doctor` line relayed with
its level and detail unchanged and its check name prefixed `doctor:`, the
doctor's own summary line dropped. With `--json` the mode SHALL print one
object `{"epic", "checks": [{"level", "check", "detail"}], "problems",
"failed"}` carrying the same rubric. The mode SHALL never call the
cycle-refusing member ordering, so a cyclic epic still prints its full
rubric. An epic with no `epic.md` SHALL be an error exit as `--waves`
reports one, and combining `--preflight` with `--waves`, `--dry-run`, or
`--member` SHALL be a usage error. Every external verb SHALL run through
the driver's injectable command seam.

#### Scenario: A green rubric exits zero
- **GIVEN** a lint-clean `ready` epic whose members are all stamped `ready`
  with disjoint master requirements and cited files, whose gate checks,
  drift verb, and doctor all report clean
- **WHEN** `--preflight` runs
- **THEN** every line is `ok`, the summary reads `preflight: ok`, the exit
  code is 0, and no session, gate write, worktree, or heartbeat action
  occurs

#### Scenario: An unplanned member fails naming the grill
- **GIVEN** an epic with one `unplanned` member
- **WHEN** `--preflight` runs
- **THEN** a `fail members —` line names that member under `unplanned` and
  `/s:epic-grill <epic>`, and the exit code is 1

#### Scenario: Edited after gate fails the preflight
- **GIVEN** a `ready` member whose `--check` run exits 2 with a `gated-hash
  mismatch` finding
- **WHEN** `--preflight` runs
- **THEN** a `fail gated-hash —` line names the member and `spec_gate.py
  <member>`, and the `gate-check` line does not repeat that finding

#### Scenario: A dependency cycle fails but the rubric still prints
- **GIVEN** an epic whose `After` column holds `x -> y -> x`
- **WHEN** `--preflight` runs
- **THEN** a `fail after-cycle —` line names `x -> y -> x`, every other
  check line still prints, and the exit code is 1

#### Scenario: Shared master requirement without an edge fails
- **GIVEN** `ready` members `a` and `b` whose deltas both modify
  `cap/req-one`, with no `After` relation between them
- **WHEN** `--preflight` runs
- **THEN** a `fail overlap-requirements —` line names `a & b` and
  `cap/req-one`

#### Scenario: A transitive After path orders two members
- **GIVEN** `c` after `b`, `b` after `a`, and `a` and `c` both modifying
  the same master requirement and citing the same file
- **WHEN** `--preflight` runs
- **THEN** the `overlap-requirements` and `overlap-files` lines are `ok`

#### Scenario: Shared cited file without an edge warns
- **GIVEN** unordered `ready` members `a` and `b` both citing
  `src/engine.py` in their tasks
- **WHEN** `--preflight` runs
- **THEN** a `warn overlap-files —` line names `a & b` and `src/engine.py`,
  and that line alone does not make the exit code non-zero

#### Scenario: The version-bump file never overlaps
- **GIVEN** unordered members both citing
  `plugins/s/.claude-plugin/plugin.json` and nothing else in common
- **WHEN** `--preflight` runs
- **THEN** the `overlap-files` line is `ok`

#### Scenario: Drift warns and names the judgment step
- **GIVEN** a drift verb run exiting 4 with one member carrying two
  `file-drift` findings
- **WHEN** `--preflight` runs
- **THEN** a `warn drift —` line names that member, `file-drift 2`, and
  `/s:drift <epic>`

#### Scenario: Doctor lines are relayed under a prefix
- **GIVEN** a doctor run printing `ok git — found`, `warn protection —
  unprotected`, and `doctor: 1 problem(s)`
- **WHEN** `--preflight` runs
- **THEN** the rubric carries `ok doctor:git — found` and `warn
  doctor:protection — unprotected` and no line for the summary

#### Scenario: JSON is one object
- **WHEN** `--preflight --json` runs on an epic with one failing check
- **THEN** stdout parses as one object whose `checks` list holds every line
  as `{"level", "check", "detail"}`, `failed` is true, and the exit code
  is 1

#### Scenario: Preflight is exclusive with the driving modes
- **WHEN** `--preflight` is combined with `--waves`, `--dry-run`, or
  `--member`
- **THEN** the driver exits 2 with a usage error and prints no rubric

### Requirement: Detached pre-build drift step
id: detached-pre-build-drift

Before the detached driver drives a member's built-in `build` stage — in an
epic run or a targeted drive entering at build, never for a skipped or
replaced build entry — it SHALL run a pre-build step in this order, through
its injectable command, session, gate, and judge seams. First it SHALL
resolve the base ref: a best-effort `git fetch origin main` from the
repository root, then `origin/main` when `git rev-parse --verify --quiet`
resolves it, else `main`. If any `After` dependency of the member is not
merged into that ref (the base-branch tree check), then the member SHALL
park as `needs-human` at stage `dependency` with a reason naming the
unmerged dependencies and the ref, with no session id. It SHALL then merge
the ref into the member's worktree with `git merge --no-edit <ref>`; if the
merge fails, then it SHALL abort the merge and park the member as
`needs-human` at stage `sync` with the merge's first output line. It SHALL
then run `spec_status.py --root <worktree> drift <member> --base <ref>
--json` in the worktree: exit 0 proceeds to build; exit 4 triggers the
judgment; any other exit, or unparseable output, parks the member as
`needs-human` at stage `drift` with the exit code and first stderr line.
The judgment SHALL be one headless turn whose prompt names `/s:drift
<member> --base <ref> --json` and asks for exactly its JSON object, retried
up to the build entry's fresh-attempt budget, each turn's `result` text
parsed with a code fence or surrounding prose tolerated: the member's entry
in `verdicts` gives the verdict, a member listed under `clean` counts as
`holds`, and an `error`, a missing entry, or an unknown verdict word fails
the attempt. An exhausted budget SHALL park the member as `needs-human` at
stage `drift` with the failure and the judge session id. A `holds` verdict
SHALL proceed to build. A `conflict` verdict SHALL park the member as
`needs-human` at stage `drift` with a reason naming the `contradicts`
value and the verdict's reason, with the judge session id. A `revise`
verdict SHALL drive a `replan` session through the enrichment machinery —
the build entry's attempts, timeout, max-resumes, and model, graded on the
member change at `ready` lint-clean — whose prompt names the ref, the
verdict's reason and `revise` text, the drift findings, the rule to keep
every `**Answered by:** USER` answer and epic Decision, the `oracle-lookup` verb for un-inferrable decisions, that no human is present, and the
closing `spec_gate.py <member> --root <worktree> --base <ref>` re-gate;
after a successful session the driver SHALL re-run the gate engine with
`--base <ref>`, so the stamp anchors on the synced ref: a pass proceeds
to build, a rejection records the member `rejected` at stage `replan` with
the session id, and a gate failure parks it `needs-human` at stage
`replan`. Exhausted re-plan attempts SHALL park the member `needs-human` at
stage `replan`. The step SHALL NOT re-measure drift after the re-gate and
SHALL NOT redefine the drift verb, the drift skill, or the merged-dependency
check.

#### Scenario: Clean drift builds without a judge
- **GIVEN** a member whose drift verb exits 0 after the worktree merged the
  base ref
- **WHEN** the driver reaches the build stage
- **THEN** the merge and the drift verb ran in the worktree with
  `--base origin/main`, no judge turn ran, and the build session follows

#### Scenario: A holds verdict builds
- **GIVEN** a drift verb exit 4 and a judge turn whose JSON verdict is
  `holds`
- **WHEN** the step runs
- **THEN** the judge prompt names `/s:drift <member> --base origin/main
  --json`, exactly one judge turn ran, and the build session follows

#### Scenario: A conflict parks with the judge session
- **GIVEN** a judge verdict `conflict` contradicting `Q2`
- **WHEN** the step runs
- **THEN** the member is `needs_human` at stage `drift`, the reason names
  `Q2`, the session id is the judge turn's, and no build session runs

#### Scenario: A revise verdict re-plans and re-gates
- **GIVEN** a judge verdict `revise` and a gate that passes after the
  re-plan session
- **WHEN** the step runs
- **THEN** one `replan` session ran with a prompt naming the reason, `oracle-lookup`, `USER`, and `spec_gate.py --base origin/main`, the gate ran
  once more with `--base origin/main`, and the build session follows

#### Scenario: A rejected re-gate records the member rejected
- **GIVEN** a judge verdict `revise` and a gate exiting 2 after the re-plan
- **WHEN** the step runs
- **THEN** the outcome is `rejected` at stage `replan` with the re-plan
  session id and no build session runs

#### Scenario: A transient judge fault is retried
- **GIVEN** a judge turn that fails once and then returns a `holds` object
  wrapped in a code fence
- **WHEN** the step runs
- **THEN** two judge turns ran and the build session follows

#### Scenario: Exhausted judge attempts park the member
- **WHEN** every judge turn of the budget fails or returns unparseable text
- **THEN** the member is `needs_human` at stage `drift` with the attempt
  count in its reason

#### Scenario: A verb error parks without a judge
- **WHEN** the drift verb exits 1
- **THEN** the member is `needs_human` at stage `drift`, the reason names
  exit 1 and the stderr line, and no judge turn or build session runs

#### Scenario: A failed sync aborts and parks
- **WHEN** `git merge --no-edit origin/main` exits non-zero
- **THEN** `git merge --abort` runs and the member is `needs_human` at
  stage `sync`

#### Scenario: An unmerged dependency parks before the sync
- **GIVEN** a member whose `After` names `a` and a base tree holding no
  `completed/` entry for `a`
- **WHEN** the step runs
- **THEN** the member is `needs_human` at stage `dependency` naming `a`,
  and no merge, drift verb, or build session runs

#### Scenario: Replaced and skipped build entries run no step
- **WHEN** the build entry is replaced by a command or skipped
- **THEN** no merge, drift verb, or judge turn runs for the member

#### Scenario: A targeted ready member gets the step
- **GIVEN** a `ready` member driven with the targeted single-member drive
- **WHEN** it enters at build
- **THEN** the drift verb runs before its build session

### Requirement: The detached run continues past a parked dependency
id: detached-dependent-continue

While driving an epic run's members in order, the autopilot SHALL record
each member's outcome, and when a member's `After` names a member driven
earlier in the same run whose outcome is not `shipped`, it SHALL NOT drive
that member: it SHALL record it `needs-human` at stage `dependency` with a
reason naming the dependency and that dependency's outcome and no session
id, write that outcome to the heartbeat roster, and continue with the next
member. A member none of whose dependencies parked SHALL be driven exactly
as before.

#### Scenario: A dependent of a parked member is not driven
- **GIVEN** members `a` and `b` with `b` after `a`, and a driver that parks
  `a` as `needs_human`
- **WHEN** the run executes
- **THEN** the driver is invoked for `a` only, and the report's `needs_human`
  holds `b` at stage `dependency` with a reason naming `a` and `needs_human`

#### Scenario: A dependent of a shipped member is driven
- **GIVEN** `b` after `a` and a driver that ships `a`
- **WHEN** the run executes
- **THEN** the driver is invoked for `a` then `b`

#### Scenario: A dependent of a drafted member waits
- **GIVEN** `b` after `a` and a driver that records `a` as `drafted`
- **WHEN** the run executes
- **THEN** `b` is reported `needs_human` at stage `dependency` and the
  summary line for it carries no `claude --resume` fragment

### Requirement: Session turn result text
id: session-turn-result-text

The session driver SHALL provide `run_turn_result(prompt, cwd, resume_id=None,
timeout, harness="claude", binary=None, effort=None, model_base=None,
plugin_dir=None, extra_args=None, env=None)` returning `(ok, failure,
session_id, result_text)` where `result_text` is the headless turn's result
string as its harness runner extracts it, or an empty string when the
transcript carries no result text; `run_turn` SHALL accept the same `env`
argument and return the first three values unchanged for every existing
caller. `binary` SHALL default to the selected runner's own executable,
`effort` SHALL be the effort level or concrete model id the runner expresses,
and `model_base` SHALL be the base a harness that expresses a level as a model
variant appends it to. Where `env` is a mapping, the session subprocess SHALL
run with the current process environment overlaid by that mapping; where
`env` is `None`, the subprocess SHALL inherit the current environment
unchanged. A helper `result_text_from_transcript(text)` SHALL expose the
Claude transcript's extraction.

#### Scenario: The result text is returned
- **GIVEN** a binary that prints `{"session_id": "s1", "result":
  "{\"mode\": \"change\"}"}` and exits 0
- **WHEN** `run_turn_result` runs with the default harness
- **THEN** it returns `ok` true, session id `s1`, and the inner object text,
  while `run_turn` on the same binary returns `(True, None, "s1")`

#### Scenario: A non-JSON transcript yields an empty text
- **WHEN** `result_text_from_transcript("not json")` is called
- **THEN** it returns an empty string

#### Scenario: The env overlay reaches the session
- **GIVEN** a fake binary that prints a transcript whose `result` is the
  value of its `SHIPD_UNATTENDED` environment variable
- **WHEN** `run_turn_result` runs it with `env={"SHIPD_UNATTENDED": "1"}`,
  and again with no `env` from a process where the variable is unset
- **THEN** the first result text is `1` and the second is empty

### Requirement: Harness runners
id: harness-runners

The session driver SHALL declare a runner registry keyed by harness id, holding
at least `claude` and `opencode`. Each runner SHALL carry its default binary, an
`argv` builder, a transcript parser, and a prompt rewriter, and `runner_for(id)`
SHALL return the runner or raise a named error for an unknown id.

The `claude` runner SHALL build `[binary, "-p", prompt, "--output-format",
"json", "--plugin-dir", <plugin>, "--permission-mode", "bypassPermissions"]`
plus `--model <model>` and `--resume <id>`, parse the JSON object's `session_id`
and `result`, and rewrite no prompt text. The `opencode` runner SHALL build
`[binary, "run", "--format", "json", "--auto"]` plus `--model <model>` and
`--session <id>`, with the prompt as the trailing positional; parse the JSONL
stream's last top-level `sessionID` and the concatenated `part.text` of every
`type == "text"` line; and rewrite each `/s:<command>` token to
`/shipd-<command>`, the command name the harness installer writes.

#### Scenario: The claude runner keeps today's invocation
- **WHEN** the `claude` runner builds an argv with a model and a resume id
- **THEN** it is `[binary, "-p", <prompt>, "--output-format", "json",
  "--plugin-dir", <plugin>, "--permission-mode", "bypassPermissions",
  "--model", <model>, "--resume", <id>]`

#### Scenario: The opencode runner builds its invocation
- **WHEN** the `opencode` runner builds an argv with a model and a resume id
- **THEN** it is `[binary, "run", "--format", "json", "--auto", "--model",
  <model>, "--session", <id>, <prompt>]`

#### Scenario: The opencode runner parses its JSONL transcript
- **GIVEN** a transcript holding a `step_start` line and two `text` lines
  carrying `"hello"` and `" world"` under one `sessionID`
- **WHEN** the `opencode` runner parses it
- **THEN** the session id is that line's `sessionID` and the result text is
  `hello world`

#### Scenario: The opencode runner rewrites the command vocabulary
- **WHEN** the `opencode` runner rewrites `Run /s:plan for the change x`
- **THEN** the result names `/shipd-plan`, and the `claude` runner rewrites the
  same prompt unchanged

#### Scenario: An unknown harness is refused
- **WHEN** `runner_for("no-such-harness")` is called
- **THEN** it raises a named error naming the id

### Requirement: Pre-build drift step
id: in-session-prebuild-drift

When a driven member's walk reaches an entry whose stage is `build` (built-in
or replaced), the in-session drive SHALL, once per member and before that
entry runs, sync and measure the member: run `git fetch origin main` and `git
merge --no-edit origin/main` in `.worktrees/<member>`, and on a non-zero merge
run `git merge --abort` and park the member as `sync-conflict`; then run
`spec_status.py --root .worktrees/<member> drift <member> --base origin/main
--json`. On exit 0 it SHALL proceed to the build entry; on exit 1 it SHALL
park the member as `drift-error` naming the `Error:` line; on exit 4 it SHALL
spawn one general-purpose sub-agent, working directory the member's
worktree, instructed to run `/s:drift <member> --base origin/main --json` and
end its turn with that object alone, and read `verdicts[0].verdict` from the
sub-agent's final text — a missing or unparseable object parks the member as
`drift-error`. A `holds` verdict SHALL proceed to the build entry; a
`conflict` verdict SHALL park the member as `drift-conflict` naming the
verdict's `contradicts`; a `revise` verdict SHALL spawn one general-purpose
sub-agent in the worktree with the re-plan instruction and then grade from
disk — `spec_status.py status <member>` prints `ready`, `spec_lint.py
<member>` exits 0, and `spec_gate.py <member> --check` exits 0 — proceeding
to the build entry on a pass and parking the member as `replan-failed`
otherwise. The step SHALL NOT repeat for a member within one run and SHALL
NOT pass the verbs' default base.

#### Scenario: A clean member builds without a model
- **GIVEN** a `ready` member whose drift verb exits 0 after the sync
- **WHEN** its walk reaches the build entry
- **THEN** no `/s:drift` sub-agent is spawned and the build entry runs

#### Scenario: A holds verdict builds
- **GIVEN** a member whose drift verb exits 4 and whose `/s:drift` sub-agent
  ends with an object whose first verdict is `holds`
- **WHEN** the drive reads the verdict
- **THEN** the build entry runs

#### Scenario: A revise verdict re-plans and re-gates before building
- **GIVEN** a member whose first verdict is `revise`
- **WHEN** the drive handles it
- **THEN** a re-plan sub-agent runs in the worktree, and the build entry
  starts only after the status reads `ready`, the lint exits 0, and
  `spec_gate.py <member> --check` exits 0

#### Scenario: A conflict verdict parks
- **GIVEN** a member whose first verdict is `conflict` with `contradicts`
  `Q2`
- **WHEN** the drive handles it
- **THEN** the member is parked as `drift-conflict` naming `Q2` and its build
  entry never runs

#### Scenario: A merge conflict parks
- **GIVEN** a member whose `git merge --no-edit origin/main` exits non-zero
- **WHEN** the sync runs
- **THEN** the merge is aborted and the member is parked as `sync-conflict`

### Requirement: Park and continue
id: in-session-park-and-continue

After the Phase 2 confirmation the in-session drive SHALL issue no
AskUserQuestion and no typed question round. A failed stage grade, a gate
rejection, a command entry exiting non-zero, and the pre-build step's
`sync-conflict`, `drift-error`, `drift-conflict`, and `replan-failed`
outcomes SHALL each park the member — recording the reason (`grade-failed
<stage>`, `gate-rejected`, `command-failed <entry> exit <rc>`, or the step's
reason) in the session, emitting `heartbeat.py build-finish <member>
--outcome parked`, and starting no further entry for that member — while the
wave's other in-flight sub-agents run to their end and are graded and the
drive continues with the next round and wave. The parked set SHALL live in
the session only: no plan status is written for a parked member. On every
`--waves` re-run the drive SHALL first run `git fetch origin main`, drop
parked members from the returned waves, mark as held every `blocked` entry
whose `waiting_on` names a parked or held member (repeated to a fixpoint),
skip a wave emptied by the drop, and never start a held member. When no
runnable wave remains but `blocked` holds entries that are not held, the
drive SHALL poll `gh pr view change/<dep> --json state` for each `waiting_on`
every 60 seconds for at most the confirmed `--timeout` seconds in total, and
once every such dependency reports `MERGED` SHALL fetch and re-run `--waves`;
if the bound expires or a dependency reports `CLOSED`, then the drive SHALL
end the run listing those members as blocked. The run summary SHALL list
shipped members by wave with full PR URLs, every parked member with its
reason, the stage or step, and its resume pointer, every blocked member as
held by a parked member or waiting on a dependency with the `/s:autopilot
<epic>` re-run pointer, and every skipped member with its state.

#### Scenario: A failed grade parks and the drive carries on
- **GIVEN** a build wave of three members where one member's build grade
  fails
- **WHEN** the drive observes the failure
- **THEN** that member is parked as `grade-failed build`, the other two run
  their current entry to its end and are graded, the next round starts for
  them, and no question is put to the user

#### Scenario: A gate rejection parks instead of asking
- **WHEN** `spec_gate.py <member>` rejects a member's plan under the drive
- **THEN** the member is parked as `gate-rejected` and the drive continues

#### Scenario: A dependent of a parked member is held
- **GIVEN** parked member `a` and a `--waves` re-run whose `blocked` holds
  `b` waiting on `a` and `c` waiting on `b`
- **WHEN** the drive filters the result
- **THEN** `b` and `c` are held, neither is started, and the summary lists
  both as held by `a`

#### Scenario: A shipped dependency is waited for within the bound
- **GIVEN** no runnable wave, `blocked` holding `b` waiting on shipped `a`,
  and `a`'s PR reporting `MERGED` on the second poll
- **WHEN** the drive waits
- **THEN** it fetches, re-runs `--waves`, and `b` joins the next build wave

#### Scenario: The bound ends the run with blocked members listed
- **GIVEN** `b` waiting on `a` whose PR is still `OPEN` when `--timeout`
  seconds have elapsed
- **WHEN** the bound expires
- **THEN** the run ends and the summary lists `b` as waiting on `a` with the
  re-run pointer

#### Scenario: The summary carries parked members and their pointers
- **WHEN** a run ends with one member parked as `drift-conflict` and one
  shipped
- **THEN** the summary names the shipped member's PR URL, and the parked
  member with its reason and a pointer that names the contradicted `Q<n>` or
  Decision and the re-run command

### Requirement: Unattended stage instructions
id: in-session-unattended-prompts

The in-session drive's plan-stage instruction and its re-plan instruction
SHALL each end with a paragraph stating that no human is available during
the run, that a decision the repository cannot settle is put to the oracle
(run `spec_status.py oracle-lookup` for one compact question and judge it per the oracle consultation contract), that on `INSUFFICIENT`
the recommended default is adopted and recorded in the plan's ledger, and
that no question round and no AskUserQuestion is opened. The re-plan
instruction SHALL additionally name the `/s:drift` verdict's `revise:`
pointer and reason, require the revision to stay within the plan's `USER`
ledger entries and the epic's Decisions, and end with `spec_gate.py <member>
--base origin/main`.

#### Scenario: The plan instruction states the absence of a human
- **WHEN** the drive spawns a plan-stage sub-agent
- **THEN** its instruction states that no human is available and names the
  oracle-then-default rule

#### Scenario: The re-plan instruction carries the verdict and the re-gate
- **GIVEN** a `revise` verdict whose `revise:` names tasks 2.1 and 2.2
- **WHEN** the drive spawns the re-plan sub-agent
- **THEN** its instruction names that pointer and reason, forbids a question
  round, and ends with the `--base origin/main` re-gate

### Requirement: Detached sessions run unattended
id: unattended-session-env

Every headless session the detached autopilot launches — each stage session
driven through its session seam and each drift-judge turn — SHALL run with
the environment variable `SHIPD_UNATTENDED` set to `1`, passed through the
session driver's `env` argument, so a skill inside the session that consults
`shipd init status` never opens its setup wizard. The autopilot SHALL NOT set
the variable in its own process environment, so its other subprocesses and
any eval or room runner sharing the session driver are unaffected.

#### Scenario: A stage session carries the flag
- **GIVEN** the production session seam with `session_driver.run_turn`
  replaced by a fake that records its keyword arguments
- **WHEN** the seam drives one stage session
- **THEN** the recorded `env` is `{"SHIPD_UNATTENDED": "1"}`

#### Scenario: A drift-judge turn carries the flag
- **GIVEN** the production judge seam with `session_driver.run_turn_result`
  replaced by a recording fake
- **WHEN** the seam runs one judge turn
- **THEN** the recorded `env` is `{"SHIPD_UNATTENDED": "1"}`

#### Scenario: The autopilot process itself stays clean
- **GIVEN** `SHIPD_UNATTENDED` is unset before the seams run
- **WHEN** both seams have run once
- **THEN** `SHIPD_UNATTENDED` is still absent from `os.environ`
