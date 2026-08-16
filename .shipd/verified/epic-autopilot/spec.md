# epic-autopilot

### Requirement: Shared session driver
id: shared-session-driver

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

### Requirement: Member selection and order
id: member-selection-and-order

Given an epic at `ready` or `active`, the autopilot SHALL drive only stub
members whose derived state is `unplanned`, ordered by the stub table's
Risk rating ascending (`low`, `medium`, `high`), ties broken by table
order. Members in any other state SHALL be reported under that state and
left untouched — a `rejected` member SHALL never be re-driven.

#### Scenario: Risk-ascending order
- **GIVEN** unplanned members rated high, low, and medium in table order
- **WHEN** a run starts
- **THEN** the driving order is the low, then medium, then high member

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
listing shipped members with PR URLs, parked members split into rejected
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
derivation actually runs. When the close-out derivation succeeds and
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

An `/s:autopilot <epic>` skill SHALL preflight the run — verifying the epic
exists at `ready` or `active`, showing the member roster and the resolved
pipeline, and confirming the run controls with the user — then drive the epic and
relay its report. The skill SHALL default to the **in-session drive**, and SHALL
use the detached `claude -p` driver only when the invocation asks for a detached
run; the confirmation of run controls SHALL name which mode the run will use.
When the run is detached, the skill SHALL run the driver in the foreground, point
at `claude --resume <session-id>` for each needs-human member, and for each
rejected member note that the automatic oracle-backed enrichment attempt already
failed, point at `/s:plan <member>` as the manual enrichment entry point, and
print `claude --resume <session-id>` when the report carries the member's
enrichment session id. Before launching either mode, the skill SHALL name the
dashboard TUI command (`dashboard.py tui --epic <epic>`) as the live view. The
skill SHALL keep `deliver` among its trigger phrases so the former `/s:deliver`
vocabulary still resolves to it. The skill SHALL NOT plan or build a member
itself in either mode; in the detached mode it SHALL NOT answer a driven
session's questions, while in the in-session mode answering a stopped stage is
the user's, not the skill's, decision to make.

#### Scenario: Preflight blocks a draft epic
- **WHEN** the skill is invoked for an epic at `draft`
- **THEN** it reports the epic is not approved and drives nothing

#### Scenario: In-session is the default
- **WHEN** the skill is invoked for an approved epic with no detached request
- **THEN** the run confirmed with the user is the in-session drive and no
  headless `claude -p` process is started

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
findings by editing the artifacts, consulting the ask-mikk oracle (agent
`s:oracle`, one compact question carrying the decision, options, and
recommendation per gap) for decisions the repository cannot answer instead
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

### Requirement: Targeted single-member drive
id: targeted-member-drive

The autopilot SHALL support driving a single epic member selected by slug —
independent of the risk-ascending auto-selection — entering the resolved
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
- **THEN** members are still selected and ordered risk-ascending over the
  `unplanned` set exactly as before

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

The autopilot skill SHALL provide an in-session drive that loops over the epic's
members within the current Claude Code session, spawning one general-purpose
sub-agent per pipeline stage with that stage's instruction and the member's
worktree as its working directory. It SHALL take the resolved pipeline and the
member ordering from the driver's dry run rather than deriving them itself.
Because the dry run's printed member order contains only `unplanned` members and
reports every other member — including `ready` ones — in its skipped list with
their state, the drive SHALL read **both** sections and select from them: the
printed order first, then the skipped entries whose state is `ready`, in the
order printed. It SHALL enter each selected member's pipeline at the stage
matching its state — `unplanned` at plan, `ready` at build — and SHALL leave
members in any other state undriven, reporting them with their state.

#### Scenario: Pipeline and ordering come from the driver's dry run
- **WHEN** an in-session drive begins
- **THEN** the resolved pipeline and the ordering it uses are those the driver's
  dry run printed, and the dry run performed no session, gate, or worktree action

#### Scenario: A ready member is reached despite being absent from the printed order
- **GIVEN** a dry run whose printed member order omits a `ready` member and
  reports it in the skipped list with state `ready`
- **WHEN** the in-session drive selects members
- **THEN** that member is selected and driven, not treated as undrivable

#### Scenario: Entry stage matches the member's state
- **GIVEN** one member at `unplanned` and one at `ready`
- **WHEN** the in-session drive reaches each
- **THEN** the first enters at the plan stage and the second enters at the build
  stage, its plan stage skipped

#### Scenario: A stage runs as a sub-agent in the member's worktree
- **WHEN** a stage runs under the in-session drive
- **THEN** a sub-agent is spawned for it whose working directory is that member's
  worktree, and no headless `claude -p` process is started

#### Scenario: Non-drivable members are skipped and reported
- **GIVEN** a member whose state is neither `unplanned` nor `ready`
- **WHEN** the in-session drive selects members
- **THEN** it is left untouched and named in the run's summary with its state

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

### Requirement: In-session failures ask the human instead of parking
id: in-session-asks-human

Where the detached drive parks a member as needs-human or rejected, the
in-session drive SHALL instead stop and put the situation to the user, because a
human is present. A failed stage grade and a gate rejection SHALL each surface to
the user with the member and stage named; the drive SHALL NOT continue to the
next member while such a stop is unanswered.

#### Scenario: A failed stage stops and asks
- **WHEN** a stage's grade does not pass under the in-session drive
- **THEN** the user is told which member and stage failed, and no further member
  is started until they answer

#### Scenario: A gate rejection is raised, not parked
- **WHEN** the gate rejects a member's plan under the in-session drive
- **THEN** the rejection is put to the user rather than the member being parked
  as rejected

#### Scenario: An interrupted run resumes from disk
- **GIVEN** an in-session drive stopped part-way through its members
- **WHEN** the skill is invoked again for the same epic
- **THEN** members already advanced are entered at their current state's stage
  and no run-state file is required

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

The engine SHALL export, stdlib-only in `spec_common`, a `MODEL_LADDER`
constant ordered strongest-first (`fable`, `opus`, `sonnet`, `haiku`) and a
pure `resolve_model_tier(tier, session_model=None)` function: `session`
SHALL resolve to `session_model` (a `None` result meaning "inherit the CLI
default"); `tier-below` and `tier-two-below` SHALL resolve to the ladder
alias one or two positions below the anchor — the anchor being
`session_model` when it is a ladder alias, else the ladder top — clamped at
the ladder bottom; any other non-empty string SHALL be returned verbatim as
a concrete model id. When a driven stage's resolved pipeline entry declares
`model`, the autopilot SHALL launch that stage's headless sessions with
`--model <resolved value>`; where the resolution yields `None`, it SHALL
pass no `--model` flag. The autopilot SHALL accept a `--session-model`
control naming the anchor, SHALL print the acting anchor in its dry run,
and SHALL record it in the run report.

#### Scenario: Session tier inherits the CLI default
- **GIVEN** a plan entry declaring `"model": "session"` and no anchor
- **WHEN** the autopilot drives the plan stage
- **THEN** the driven session is launched without a `--model` flag

#### Scenario: Below-tiers step down from the ladder top by default
- **WHEN** `tier-below` and `tier-two-below` resolve with no anchor
- **THEN** they resolve to `opus` and `sonnet` respectively

#### Scenario: Anchored stepping clamps at the ladder bottom
- **GIVEN** `--session-model sonnet`
- **WHEN** `tier-below` and `tier-two-below` resolve
- **THEN** both resolve to `haiku`

#### Scenario: Concrete ids pass through verbatim
- **WHEN** an entry declares `"model": "claude-fable-5"`
- **THEN** the driven session is launched with `--model claude-fable-5`

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
