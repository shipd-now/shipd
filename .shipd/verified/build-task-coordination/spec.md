# build-task-coordination

### Requirement: Atomic task claiming with stable IDs
id: atomic-task-claiming-with-stable-ids

The coordinator script SHALL assign each task in a change's `tasks.md` a stable
ordinal ID equal to its 1-based position among all checkbox lines
(`- [ ]`, `- [~]`, `- [x]`), independent of blank lines, headings, or prose. The
`claim` command SHALL atomically transition the next **ready** pending task
(`- [ ]`) to in-progress (`- [~]`) and print its ID and text. A pending task is
ready when every earlier group and barrier before its group is done, per the
parallel task group format; `claim` SHALL never hand out a task whose group is
not yet ready. The script SHALL resolve the change's `tasks.md` under
`.shipd/planned/<change>/`.

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

### Requirement: Status reporting
id: status-reporting

The `status` command SHALL report the counts of pending, in-progress, and done
tasks for a change.

#### Scenario: Status counts reflect the file
- **WHEN** `status <change>` is run
- **THEN** it prints the number of `- [ ]`, `- [~]`, and `- [x]` tasks

### Requirement: Parallel task group format
id: parallel-task-group-format

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

The build orchestrator SHALL derive its parallelism from the group tags alone —
spawning up to one sub-agent per currently-claimable task, subject to a
configurable cap — rather than judging task independence ad hoc at spawn time.

#### Scenario: Fan-out follows the tags
- **WHEN** the ready group contains three claimable tasks and the cap allows
- **THEN** the orchestrator runs three sub-agents concurrently, each claiming its
  own task

### Requirement: Mutating verbs are branch-guarded
id: claim-branch-guard

If the repository contains a branch named `change/<change>` and the current
checkout is not on that branch (including a detached HEAD), then the
coordinator's mutating verbs — `claim`, `complete`, and `release` — SHALL
refuse to act, printing a message naming both the current and required
branches and exiting with code 3. When the repository has no
`change/<change>` branch, when the working directory is not a git checkout,
or when the checkout is on the change branch, the verbs SHALL behave
unchanged. The read-only verbs `status` and `next` SHALL never be
branch-guarded.

#### Scenario: Claiming from the wrong checkout is refused
- **GIVEN** a repo where branch `change/x` exists and the checkout is on
  `main` with a planned change `x`
- **WHEN** `claim x` runs
- **THEN** it exits with code 3, names both branches, and marks no task

#### Scenario: The change's own worktree claims normally
- **GIVEN** a checkout on branch `change/x` with a planned change `x`
- **WHEN** `claim x` runs
- **THEN** it claims the next task exactly as before

#### Scenario: A repo without the change branch is unaffected
- **GIVEN** a git repo on any branch where no `change/x` branch exists
- **WHEN** `claim x` runs against its planned change
- **THEN** the guard does not trigger and the verb behaves as before

#### Scenario: A non-git directory is unaffected
- **GIVEN** a plain directory (no git checkout) holding a planned change
- **WHEN** `claim`, `complete`, or `release` run
- **THEN** they behave exactly as before

#### Scenario: Detached HEAD counts as a mismatch
- **GIVEN** a repo where branch `change/x` exists and HEAD is detached
- **WHEN** `claim x` runs
- **THEN** it refuses with exit code 3

#### Scenario: Read-only verbs stay unguarded
- **GIVEN** a repo where branch `change/x` exists and the checkout is on
  `main`
- **WHEN** `status x` or `next x` runs
- **THEN** it reports normally with no branch refusal
