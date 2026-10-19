## ADDED Requirements

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
(spawn agent `s:oracle` with one compact question), that on `INSUFFICIENT`
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

## MODIFIED Requirements

### Requirement: Autopilot skill
id: deliver-skill
base: 7c347a4f3a75

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

### Requirement: In-session sub-agent drive
id: in-session-drive
base: f5cd571e1a2b

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

## REMOVED Requirements

### Requirement: In-session failures ask the human instead of parking
id: in-session-asks-human
base: 7c3cf0ae8089
Reason: The epic makes the launch confirmation the last question; after it the in-session drive parks a failing member and carries on with every member that does not depend on it.
Migration: The park-and-continue requirement above replaces it; an interrupted or ended run still resumes from disk by re-invoking `/s:autopilot <epic>`, and the parked member's pointer names its own recovery entry point.
