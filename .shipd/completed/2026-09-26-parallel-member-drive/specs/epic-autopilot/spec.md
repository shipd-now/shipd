## ADDED Requirements

### Requirement: Member wave scheduling
id: member-wave-scheduling

The autopilot driver SHALL provide a `--waves` mode (`autopilot.py <epic>
--waves [--parallel N] [--json]`) that computes, from on-disk state alone,
the waves of members the in-session drive may run concurrently, and drives
nothing. `--parallel` SHALL be an integer of at least 1, default 3, and
SHALL cap every wave's size. The mode SHALL emit plan waves first: every
`unplanned` member in risk-ascending order (ties by table order), chunked
into waves of at most N, each tagged stage `plan`. It SHALL then emit build
waves over the `ready` members: each member's capabilities are the
capability directory names under its planned change's `specs/`, read from
the root that hosts the change; walking members in risk-ascending order,
each member joins the earliest build wave whose members' capabilities are
all disjoint from its own and whose size is below N, else opens a new wave.
Members in any other state SHALL be listed as skipped with their state. With
`--json` the mode SHALL print one object `{"epic", "parallel", "waves":
[{"index", "stage", "members": [{"slug", "risk", "capabilities"}]}],
"skipped": [{"member", "state"}]}`; without it, one `wave <index> [<stage>]:`
line per wave naming its members and, for build waves, each member's
capabilities. The computation SHALL be deterministic for a given tree.

#### Scenario: Plan waves chunk unplanned members risk-ascending
- **GIVEN** unplanned members rated high, low, low, and medium and
  `--parallel 2`
- **WHEN** `--waves` runs
- **THEN** the first wave is the two low members and the second is the
  medium then the high member, both tagged `plan`

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
- **WHEN** `--waves --parallel 1` runs
- **THEN** every wave holds exactly one member: the unplanned members in
  the same order the dry run prints, followed by the ready members in
  risk-ascending order with ties by table order

## MODIFIED Requirements

### Requirement: In-session sub-agent drive
id: in-session-drive
base: e711c2de2cac
Dropped: Ordering comes from the dry run, entries from the machine contract
Dropped: A ready member is reached despite being absent from the printed order

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
repeat until every member of the wave has finished its walk. After each
wave completes it SHALL re-run `--waves` and continue with the first wave
returned, until the mode returns no wave. It SHALL enter each member's
pipeline at the first entry whose stage matches the member's state —
`unplanned` at plan, `ready` at build — treating every entry before that
point, custom entries included, as already satisfied and not running it;
and SHALL leave members in any other state undriven, reporting them with
their state. With `--parallel 1` the drive SHALL behave exactly as a
one-member-at-a-time walk.

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

### Requirement: In-session failures ask the human instead of parking
id: in-session-asks-human
base: e1d4fbd50cb6

Where the detached drive parks a member as needs-human or rejected, the
in-session drive SHALL instead stop and put the situation to the user, because a
human is present. A failed stage grade and a gate rejection SHALL each surface to
the user with the member and stage named. When a member's grade fails inside a
wave, the drive SHALL let the wave's other members finish their current entry,
SHALL start no further entry for any member and no further wave, and SHALL
then put every stopped member to the user in one report; the drive SHALL NOT
continue while such a stop is unanswered.

#### Scenario: A failed stage stops and asks
- **WHEN** a stage's grade does not pass under the in-session drive
- **THEN** the user is told which member and stage failed, and no further
  entry or wave is started until they answer

#### Scenario: A gate rejection is raised, not parked
- **WHEN** the gate rejects a member's plan under the in-session drive
- **THEN** the rejection is put to the user rather than the member being parked
  as rejected

#### Scenario: A failed grade lets the wave finish
- **GIVEN** a wave of three members where one member's build grade fails
- **WHEN** the drive observes the failure
- **THEN** the other two members' current sub-agents run to their end and
  are graded, no next entry starts for any of the three, and the stop names
  the failed member and stage

#### Scenario: An interrupted run resumes from disk
- **GIVEN** an in-session drive stopped part-way through its members
- **WHEN** the skill is invoked again for the same epic
- **THEN** members already advanced are entered at their current state's stage
  and no run-state file is required

### Requirement: Autopilot skill
id: deliver-skill
base: 509d838de2d2

An `/s:autopilot <epic>` skill SHALL preflight the run — verifying the epic
exists at `ready` or `active`, showing the member roster and the resolved
pipeline, and confirming the run controls with the user — then drive the epic and
relay its report. The skill SHALL default to the **in-session drive**, and SHALL
use the detached `claude -p` driver only when the invocation asks for a detached
run; the confirmation of run controls SHALL name which mode the run will use,
and for the in-session drive SHALL include a `--parallel N` control — the
number of members driven concurrently, default 3, where 1 is a serial run —
and SHALL show the waves the driver's `--waves` mode computes for that value.
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
