## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: In-session sub-agent drive
id: in-session-drive
base: 3c0eda1eb8d9

The autopilot skill SHALL provide an in-session drive that loops over the
epic's members within the current Claude Code session, walking the resolved
pipeline's entry list per member and spawning one general-purpose sub-agent
per built-in stage entry it runs, with that stage's instruction and the
member's worktree as its working directory. It SHALL take the member
ordering from the driver's dry run and the resolved entry list from the
status CLI's `pipeline-show --json` machine contract, deriving neither
itself. Because the dry run's printed member order contains only
`unplanned` members and reports every other member — including `ready`
ones — in its skipped list with their state, the drive SHALL read **both**
sections and select from them: the printed order first, then the skipped
entries whose state is `ready`, in the order printed. It SHALL enter each
selected member's pipeline at the first entry whose stage matches the
member's state — `unplanned` at plan, `ready` at build — treating every
entry before that point, custom entries included, as already satisfied and
not running it; and SHALL leave members in any other state undriven,
reporting them with their state.

#### Scenario: Ordering comes from the dry run, entries from the machine contract
- **WHEN** an in-session drive begins
- **THEN** the member ordering is the one the driver's dry run printed, the
  entry list is the one `pipeline-show --json` emitted, and the dry run
  performed no session, gate, or worktree action

#### Scenario: A ready member is reached despite being absent from the printed order
- **GIVEN** a dry run whose printed member order omits a `ready` member and
  reports it in the skipped list with state `ready`
- **WHEN** the in-session drive selects members
- **THEN** that member is selected and driven, not treated as undrivable

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
