## MODIFIED Requirements

### Requirement: Autopilot skill
id: deliver-skill
base: ccba3353289e
Dropped: A failing preflight stops before the confirmation
Dropped: Warn lines reach the confirmation
Dropped: The parallel control is confirmed with its waves

An `/s:autopilot <epic>` skill SHALL preflight the run by running
`autopilot.py <epic> --preflight`, relaying every `ok|warn|fail` line; if any
line is `fail`, then the skill SHALL stop before the drive, naming the
failing lines and their remedies, and drive nothing. The skill SHALL read the
run controls — `--max-members`, `--timeout`, `--max-resumes`, and, for the
in-session drive, `--parallel` — from the invocation, as flags or plain
words, and SHALL apply each control's default (unlimited, 1800, 4, and 3)
when the invocation names none. It SHALL then show the member roster and the
resolved pipeline, and print a launch brief naming the mode, the resolved
controls, the dry run's member list, every `warn` line, and, for the
in-session drive, the waves the driver's `--waves` mode computes for the
`--parallel` value — and SHALL start the drive in the same turn without
asking any question. The skill SHALL issue no AskUserQuestion and no typed
question round at any point of the run. The skill SHALL default to the
**in-session drive**, and SHALL use the detached `claude -p` driver only when
the invocation asks for a detached run. Where the invocation caps
`--max-members N`, the in-session drive SHALL drive at most N members in the
waves mode's order and report the rest as unreached. When the run is
detached, the skill SHALL run the driver in the foreground, point at
`claude --resume <session-id>` for each needs-human member, and for each
rejected member note that the automatic oracle-backed enrichment attempt
already failed, point at `/s:plan <member>` as the manual enrichment entry
point, and print `claude --resume <session-id>` when the report carries the
member's enrichment session id. Before launching either mode, the launch
brief SHALL name the dashboard TUI command (`dashboard.py tui --epic
<epic>`) as the live view. The skill SHALL keep `deliver` among its trigger
phrases so the former `/s:deliver` vocabulary still resolves to it. The
skill SHALL NOT plan or build a member itself in either mode and SHALL NOT
answer a driven session's questions; in the in-session mode a failure parks
the member rather than asking.

#### Scenario: Preflight blocks a draft epic
- **WHEN** the skill is invoked for an epic at `draft`
- **THEN** the preflight's `epic-status` line is `fail`, the skill reports the
  epic is not approved, and drives nothing

#### Scenario: A failing preflight stops before the drive
- **GIVEN** a preflight whose `members` line is `fail`
- **WHEN** the skill runs Phase 1
- **THEN** it prints the failing line with its remedy, asks nothing, and
  drives nothing

#### Scenario: A plain invocation delivers every member without asking
- **GIVEN** an approved epic with a passing preflight
- **WHEN** the user invokes `/s:autopilot <epic>` with no controls
- **THEN** the skill prints the launch brief with every default control and
  starts driving every driven member in the same turn, with no
  AskUserQuestion and no typed question

#### Scenario: The invocation narrows the run
- **WHEN** the user invokes `/s:autopilot <epic>` asking for just the first
  member, or passing `--max-members 1`
- **THEN** the launch brief shows `--max-members 1`, the drive drives one
  member, and the rest are reported as unreached

#### Scenario: Warn lines reach the launch brief
- **GIVEN** a preflight with a `warn drift —` line and no `fail`
- **WHEN** the skill prints the launch brief
- **THEN** the brief carries that line and the drive starts

#### Scenario: In-session is the default
- **WHEN** the skill is invoked for an approved epic with no detached request
- **THEN** the launch brief names the in-session drive and no headless
  `claude -p` process is started

#### Scenario: The parallel control is shown with its waves
- **WHEN** the skill launches an in-session run
- **THEN** the launch brief shows `--parallel` (3 unless the invocation names
  another value) and the waves computed for that value

#### Scenario: A detached run is opted into
- **WHEN** the invocation asks for a detached run
- **THEN** the skill runs the driver in the foreground as before and relays its
  report

#### Scenario: Preflight names the live board
- **WHEN** the skill prints the launch brief
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

### Requirement: Park and continue
id: in-session-park-and-continue
base: ebbf0d03e1cf

Once the launch brief prints, the in-session drive SHALL issue no
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
every 60 seconds for at most the resolved `--timeout` seconds in total, and
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
