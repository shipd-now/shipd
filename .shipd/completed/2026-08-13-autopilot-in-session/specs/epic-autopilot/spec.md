## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Autopilot skill
id: deliver-skill
base: dbda571af21c

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
