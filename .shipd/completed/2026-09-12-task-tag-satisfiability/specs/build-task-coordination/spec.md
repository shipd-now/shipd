## MODIFIED Requirements

### Requirement: Parallel task group format
id: parallel-task-group-format
base: 1ff579d10246

The tasks checklist format SHALL support an optional group tag `[P<n>]` at the
start of a task's text, marking tasks that may run concurrently. Tasks sharing
a group number are mutually independent; groups run in ascending order; and a
task carrying no tag is a sequential barrier, claimable only once every task
before it in file order is done and blocking every later group until it is
done. A task's tag SHALL NOT change the task's traceability tag, its ordinal
id, or any other element of the checklist grammar, and a claimed task SHALL
stay claimed from the moment it becomes ready until it is done.

Because a barrier orders by **file position** while a group orders by
**number**, the two can contradict each other: a barrier sitting between a
higher-numbered group and a lower-numbered one makes every task in both
unreachable. The authoring guidance in the build skill SHALL therefore direct
authors to one of the two configurations that cannot contradict themselves —
every task untagged (fully sequential), or every task tagged with group
numbers that never decrease down the file — and SHALL NOT describe an
untagged task as unconditionally safe, since it is safe only where no groups
surround it.

#### Scenario: Same group means independent
- **WHEN** two tasks are tagged `[P1]`
- **THEN** they may be claimed and executed concurrently by different sub-agents

#### Scenario: Untagged task acts as a barrier
- **WHEN** an untagged task sits between `[P1]` and `[P2]` tasks in the file
- **THEN** it is claimable only after all `[P1]` tasks are done, and no `[P2]`
  task is claimable until the untagged task is done

#### Scenario: The guidance names the safe idioms
- **WHEN** the build skill's task-authoring guidance is read
- **THEN** it directs the author to either a fully untagged file or group
  numbers that never decrease down the file, and does not call an untagged
  task unconditionally safe
