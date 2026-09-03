## MODIFIED Requirements

### Requirement: Atomic task claiming with stable IDs
id: atomic-task-claiming-with-stable-ids
base: 6bca3b94c41d

The coordinator script SHALL assign each task in a change's `tasks.md` a stable
ordinal ID equal to its 1-based position among all checkbox lines,
independent of blank lines, headings, or prose. A checkbox line is one whose
content begins — after optional leading blanks — with the `- [<state>]`
marker (state space, `~`, or `x`); a checkbox-shaped literal appearing
mid-line inside a task's prose SHALL never be counted, and every coordinator
verb — ordinal enumeration, readiness evaluation, in-progress resolution,
status counts, the box rewrite, and the marker strip — SHALL apply this same
anchored grammar. The
`claim` command SHALL atomically transition the next **ready** pending task
(`- [ ]`) to in-progress (`- [~]`) and print its ID and text. A pending task is
ready when every earlier group and barrier before its group is done, per the
parallel task group format; `claim` SHALL never hand out a task whose group is
not yet ready. The script SHALL resolve the change's `tasks.md` under
`.shipd/planned/<change>/`. Every successful claim SHALL record the claim's
holder and a timestamp in a sidecar claim record beside the tasks file,
written under the same lock as the checkbox transition — the holder being the
label given via `claim --as <label>`, defaulting to the caller's session id
and to `anon` when none is available; the checkbox grammar of `tasks.md`
itself SHALL be unchanged by the record. `claim --wait` SHALL block **inside
the single invocation** — retrying the atomic claim every few seconds without
holding the lock between attempts — until it wins a task, no pending task
remains (returning immediately with the existing no-pending message), or a
`--timeout <secs>` deadline (default 600) passes, in which case it SHALL print
a timeout message to stderr, print nothing to stdout, and exit zero — the
established empty-stdout contract for "nothing claimed".

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

#### Scenario: A checkbox literal in task prose is not a task
- **GIVEN** a tasks file whose wrapped task descriptions carry backticked
  checkbox-marker literals on continuation lines
- **WHEN** `status`, `claim`, and `complete <id>` run
- **THEN** the counts reflect only the real tasks, the claimed ordinal maps
  to the real task's line, and the box rewrite lands on that line — never on
  a literal's line

#### Scenario: A claim is stamped with holder and time
- **WHEN** `claim <change> --as builder-2` wins a task
- **THEN** the sidecar record carries that task's id, `builder-2`, and a
  timestamp, and `tasks.md` shows only the ordinary `- [~]` mark

#### Scenario: Wait blocks through a barrier and then claims
- **GIVEN** the only pending task sits behind an in-progress barrier
- **WHEN** `claim --wait` runs and the barrier task is completed a few seconds
  later
- **THEN** the same invocation returns the newly ready task's `ID<TAB>TEXT`

#### Scenario: Wait times out empty
- **GIVEN** a barrier that never completes
- **WHEN** `claim --wait --timeout 1` runs
- **THEN** it prints nothing to stdout, notes the timeout on stderr, and exits
  zero

#### Scenario: Wait returns immediately when nothing is pending
- **WHEN** `claim --wait` runs and no `- [ ]` task remains
- **THEN** it returns at once with empty stdout and the no-pending message,
  not after the timeout
