## MODIFIED Requirements

### Requirement: Atomic task claiming with stable IDs
id: atomic-task-claiming-with-stable-ids
base: ffb322c8ef92

The coordinator script SHALL assign each task in a change's `tasks.md` a stable
ordinal ID equal to its 1-based position among all checkbox lines
(`- [ ]`, `- [~]`, `- [x]`), independent of blank lines, headings, or prose. The
`claim` command SHALL atomically transition the next **ready** pending task
(`- [ ]`) to in-progress (`- [~]`) and print its ID and text. A pending task is
ready when every earlier group and barrier before its group is done, per the
parallel task group format; `claim` SHALL never hand out a task whose group is
not yet ready. The script SHALL resolve the change's `tasks.md` under
`am/planned/<change>/`.

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
