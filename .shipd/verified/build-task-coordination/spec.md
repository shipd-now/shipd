# build-task-coordination

### Requirement: Atomic task claiming with stable IDs
id: atomic-task-claiming-with-stable-ids

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

### Requirement: Completion and release without tracking line numbers
id: completion-and-release-without-tracking-line-numbers

The `complete` and `release` commands SHALL accept an optional task ID. When the ID
is omitted, they SHALL act on the single in-progress (`- [~]`) task. When more than
one task is in-progress and no ID is given, they SHALL fail with a message
instructing the caller to pass an ID, rather than guessing. Both commands
SHALL refuse — exiting non-zero and naming the task's current state — a task
whose box is not `- [~]`, so a completed task can never be flipped back to
pending and a pending task can never be marked done without a claim. Where the
task's claim record names a holder AND the caller passes `--as <label>` with a
different label, both commands SHALL refuse naming both labels; a call without
`--as` SHALL act regardless of the recorded holder. A successful `complete` or
`release` SHALL remove the task's claim record.

#### Scenario: Sequential completion needs no ID
- **WHEN** exactly one task is `- [~]` and a sub-agent runs `complete <change>`
- **THEN** that task becomes `- [x]`

#### Scenario: Targeted completion by ID
- **WHEN** a sub-agent runs `complete <change> <id>` on an in-progress task
- **THEN** the task with that ordinal ID becomes `- [x]` regardless of how many
  tasks are in-progress

#### Scenario: Ambiguous completion is refused, not guessed
- **WHEN** two or more tasks are `- [~]` and `complete <change>` is run with no ID
- **THEN** the script exits non-zero and prints a message telling the caller to
  pass an explicit ID

#### Scenario: Releasing returns a task to pending
- **WHEN** a sub-agent runs `release <change> <id>` (or with no ID and exactly one
  in-progress task) on an in-progress task
- **THEN** that task returns to `- [ ]` and its claim record is removed

#### Scenario: A completed task cannot be released
- **WHEN** `release <change> <id>` runs on a `- [x]` task
- **THEN** the script exits non-zero naming the task's state and the box is
  unchanged

#### Scenario: A pending task cannot be completed
- **WHEN** `complete <change> <id>` runs on a `- [ ]` task
- **THEN** the script exits non-zero naming the task's state and the box is
  unchanged

#### Scenario: A mismatched holder is refused
- **GIVEN** a task claimed with `--as builder-1`
- **WHEN** `complete <change> <id> --as builder-2` runs
- **THEN** the script exits non-zero naming both labels and the box is
  unchanged

#### Scenario: A bare call ignores the recorded holder
- **GIVEN** a task claimed with `--as builder-1`
- **WHEN** `complete <change> <id>` runs with no `--as`
- **THEN** the task becomes `- [x]` exactly as before this change

### Requirement: Status reporting
id: status-reporting

The `status` command SHALL report the counts of pending, in-progress, and done
tasks for a change, with its first output line byte-identical to the
pre-change form. After it, the command SHALL print one line per in-progress
task carrying the task's id, its recorded holder, and its claim age, marked
stale when the age exceeds a threshold (default 30 minutes, overridable via
`--stale-after <mins>`); an in-progress task with no claim record SHALL print
with unknown holder and age and the stale mark, never an error.

#### Scenario: Status counts reflect the file
- **WHEN** `status <change>` is run
- **THEN** it prints the number of `- [ ]`, `- [~]`, and `- [x]` tasks on the
  first line, unchanged in format

#### Scenario: In-progress tasks list holder and age
- **GIVEN** a task claimed as `builder-1`
- **WHEN** `status <change>` runs
- **THEN** a `claimed:` line names the task id, `builder-1`, and its age

#### Scenario: An old claim is marked stale
- **GIVEN** a claim record older than the stale threshold
- **WHEN** `status <change>` runs
- **THEN** that task's `claimed:` line carries the stale mark

#### Scenario: A record-less in-progress task is visible, not fatal
- **GIVEN** a `- [~]` task with no sidecar record
- **WHEN** `status <change>` runs
- **THEN** its line prints with unknown holder and age, marked stale, and the
  exit code is zero

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

### Requirement: Stale claim reclamation
id: stale-claim-reclamation

The coordinator SHALL provide `release --stale <mins>`, which — under the
claim lock — returns to pending every in-progress task whose claim record is
older than the given threshold, an in-progress task with no record counting as
stale, printing one line per released task naming its holder and age, and a
no-stale-claims line when none qualifies. The verb SHALL NOT accept an
explicit task id together with `--stale`, and SHALL never touch a claim
younger than the threshold. Reclamation SHALL be explicit-only: `claim` SHALL
never silently reclaim a stale task on its own.

#### Scenario: Stale claims are reclaimed
- **GIVEN** one claim 45 minutes old, one 5 minutes old, and one `- [~]` task
  with no record
- **WHEN** `release --stale 30 <change>` runs
- **THEN** the old and record-less tasks return to `- [ ]` with one line each,
  and the fresh claim is untouched

#### Scenario: Nothing stale is a clean no-op
- **WHEN** `release --stale 30 <change>` runs and every claim is fresh
- **THEN** it prints the no-stale-claims line and exits zero with no box
  changed

#### Scenario: An id and --stale are mutually exclusive
- **WHEN** `release <change> 3 --stale 30` runs
- **THEN** the script exits non-zero with a usage message and changes nothing

### Requirement: Foreground claim discipline
id: foreground-claim-discipline

The execution worker contract (`sub-agent.md`) SHALL instruct workers to wait
for barriers with `claim --wait` in the foreground of a tool call and SHALL
forbid running claim or status poll loops as background processes — a
detached claim outlives the agent's awareness of it — and SHALL instruct
workers to pass a stable personal `--as` label (their spawn role, or one
short label invented once and reused) on every claim, complete, and release.

#### Scenario: The contract prescribes foreground waiting
- **WHEN** the worker contract's loop section is read
- **THEN** it directs barrier waits through `claim --wait`, forbids
  background claim/status loops, and requires a stable `--as` label

#### Scenario: The build skill documents the verbs
- **WHEN** the build skill's coordinator reference is read
- **THEN** it lists `claim --as/--wait/--timeout`, the `status` claim lines
  with `--stale-after`, and `release --stale`
