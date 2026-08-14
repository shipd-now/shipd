# build-task-coordination — delta

## MODIFIED Requirements

### Requirement: Atomic task claiming with stable IDs
id: atomic-task-claiming-with-stable-ids
base: c6696a87f719
The coordinator script SHALL assign each task in a change's `tasks.md` a stable
ordinal ID equal to its 1-based position among all checkbox lines
(`- [ ]`, `- [~]`, `- [x]`), independent of blank lines, headings, or prose. The
`claim` command SHALL atomically transition the next **ready** pending task
(`- [ ]`) to in-progress (`- [~]`) and print its ID and text. A pending task is
ready when every earlier group and barrier before its group is done, per the
parallel task group format; `claim` SHALL never hand out a task whose group is
not yet ready. The script SHALL resolve the change's `tasks.md` under
`am/spec/changes/<change>/`.

#### Scenario: Claiming returns a stable ID
- **WHEN** a sub-agent runs `claim <change>` and a ready pending task exists
- **THEN** the script marks that task `- [~]` under a lock and prints
  `ID<TAB>TEXT`, where `ID` is the task's checkbox ordinal

#### Scenario: Two sub-agents never claim the same task
- **WHEN** two `claim` invocations for the same change run concurrently
- **THEN** each receives a different ready pending task (or empty output if none
  is ready), and no task is marked in-progress twice

#### Scenario: Unready tasks are not handed out
- **WHEN** the only pending tasks belong to a group whose predecessors are not
  all done
- **THEN** `claim` prints nothing and exits without error, even though pending
  tasks exist

#### Scenario: Nothing left to claim
- **WHEN** `claim <change>` runs and no `- [ ]` task remains
- **THEN** the script prints nothing to stdout and exits without error

### Requirement: Completion and release without tracking line numbers
id: completion-and-release-without-tracking-line-numbers
base: ac66ec07e9dc
The `complete` and `release` commands SHALL accept an optional task ID. When the ID
is omitted, they SHALL act on the single in-progress (`- [~]`) task. When more than
one task is in-progress and no ID is given, they SHALL fail with a message
instructing the caller to pass an ID, rather than guessing.

#### Scenario: Sequential completion needs no ID
- **WHEN** exactly one task is `- [~]` and a sub-agent runs `complete <change>`
- **THEN** that task becomes `- [x]`

#### Scenario: Targeted completion by ID
- **WHEN** a sub-agent runs `complete <change> <id>`
- **THEN** the task with that ordinal ID becomes `- [x]` regardless of how many
  tasks are in-progress

#### Scenario: Ambiguous completion is refused, not guessed
- **WHEN** two or more tasks are `- [~]` and `complete <change>` is run with no ID
- **THEN** the script exits non-zero and prints a message telling the caller to
  pass an explicit ID

#### Scenario: Releasing returns a task to pending
- **WHEN** a sub-agent runs `release <change> <id>` (or with no ID and exactly one
  in-progress task)
- **THEN** that task returns to `- [ ]`

### Requirement: Parallel task group format
id: parallel-task-group-format
base: 0199568ab2c5
The tasks checklist format SHALL support an optional group tag `[P<n>]` at the
start of a task's text (e.g. `- [ ] 2.1 [P2] Add CLI flag`). Tasks sharing a
`P` number are mutually independent and safe to execute concurrently. Groups
become ready in ascending numeric order, and an untagged task is a sequential
barrier: it only becomes ready when everything before it is done, and nothing
after it becomes ready until it is done.

#### Scenario: Same group means independent
- **WHEN** two tasks are tagged `[P1]`
- **THEN** they may be claimed and executed concurrently by different sub-agents

#### Scenario: Untagged task acts as a barrier
- **WHEN** an untagged task sits between `[P1]` and `[P2]` tasks in the file
- **THEN** it is claimable only after all `[P1]` tasks are done, and no `[P2]`
  task is claimable until the untagged task is done

### Requirement: Deterministic fan-out from group tags
id: deterministic-fan-out-from-group-tags
base: 138ab4b86d44
The build orchestrator SHALL derive its parallelism from the group tags alone —
spawning up to one sub-agent per currently-claimable task, subject to a
configurable cap — rather than judging task independence ad hoc at spawn time.

#### Scenario: Fan-out follows the tags
- **WHEN** the ready group contains three claimable tasks and the cap allows
- **THEN** the orchestrator runs three sub-agents concurrently, each claiming its
  own task
