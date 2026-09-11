## MODIFIED Requirements

### Requirement: Atomic task claiming with stable IDs
id: atomic-task-claiming-with-stable-ids
base: 29e5a5a454ba

The coordinator script SHALL assign each task in a change's `tasks.md` a stable
ID — the task's checkbox ordinal, counting `- [ ]`, `- [~]`, and `- [x]` lines
top-to-bottom — and SHALL hand out a ready pending task atomically under a
lock, marking it `- [~]` and printing `ID<TAB>TEXT`. A task whose parallel
group is not ready SHALL NOT be handed out even though pending tasks exist,
and when nothing is claimable the script SHALL print nothing to stdout and
exit without error. The script SHALL resolve the change's directory under the
resolved content directory's `planned/<change>/`: it SHALL read the engine's
`config-show` output once per invocation, taking the `store:` line's path
when one prints (the fully resolved external per-repo content directory
under a declared `store_root`), else the `content-dir:` line's value; if the
resolution fails or prints neither line, then the script SHALL fall back to
the literal `.shipd`, so it never resolves less than the default
configuration. Every successful claim SHALL record the claim's
holder and a timestamp in a sidecar claim record beside the tasks file,
written under the same lock as the checkbox transition — the holder being the
label given via `claim --as <label>`, defaulting to the caller's session id
and to `anon` when none is available; the checkbox grammar of `tasks.md`
itself SHALL be unchanged by the record. `claim --wait` SHALL block **inside
the single invocation** — retrying the atomic claim every few seconds without
holding the lock between attempts — until it wins a task, no pending task
remains (returning immediately with the existing no-pending message), or a
`--timeout <secs>` deadline passes, in which case it SHALL print
a timeout message to stderr, print nothing to stdout, and exit zero — the
established empty-stdout contract for "nothing claimed". That deadline SHALL
default to a value that fits inside an agent harness's default foreground
tool-call budget, so the documented waiting invocation completes in the
foreground rather than being detached; the shipped default SHALL be 90
seconds, and every place that states it — the script's own usage or header
text, the execution worker contract, and the build skill's coordinator
reference — SHALL state the same value.

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

#### Scenario: The wait default fits a foreground tool call
- **WHEN** the script's `--wait` default deadline is read
- **THEN** it is 90 seconds — inside a 120-second default foreground budget —
  and the script text, the worker contract, and the build skill's coordinator
  reference all state that same number

#### Scenario: A store-resident change is coordinated
- **GIVEN** a repo whose configuration declares `store_root`, with the
  change's `tasks.md` under the store's per-repo `planned/<change>/`
- **WHEN** `status` and `claim` run from the repo root
- **THEN** they operate on the store's tasks file — counts, claims, and the
  sidecar record all land there — instead of dying on a missing
  `.shipd/planned` path

### Requirement: Foreground claim discipline
id: foreground-claim-discipline
base: ae03d438ff41

The execution worker contract (`sub-agent.md`) SHALL instruct workers to wait
for barriers with `claim --wait` in the foreground of a tool call and SHALL
forbid running claim or status poll loops as background processes — a
detached claim outlives the agent's awareness of it — and SHALL instruct
workers to pass a stable personal `--as` label (their spawn role, or one
short label invented once and reused) on every claim, complete, and release.
The contract SHALL further forbid a worker from ending its turn while it
still holds a claim: before stopping for any reason, including to await a
long-running verification, the worker SHALL complete the task or release it,
so a held task never outlives the agent watching it. The orchestrator flow
(`build/SKILL.md`) SHALL direct the orchestrator to check for stale claims
between fan-out rounds with `status <change> --stale-after <mins>` and to act
on any claim the check reports stale; reclamation SHALL remain operator-driven
via `release --stale`, and `claim` SHALL never reclaim a stale task on its own.

#### Scenario: The contract prescribes foreground waiting
- **WHEN** the worker contract's loop section is read
- **THEN** it directs barrier waits through `claim --wait`, forbids
  background claim/status loops, and requires a stable `--as` label

#### Scenario: The contract forbids stopping on a held claim
- **WHEN** the worker contract's loop section is read
- **THEN** it requires a worker to complete or release its claimed task
  before ending its turn, naming awaiting a long-running verification as one
  such stop

#### Scenario: The orchestrator is told to check for stale claims
- **WHEN** the build skill's fan-out phase is read
- **THEN** it directs the orchestrator to run `status --stale-after` between
  rounds and to act on a reported stale claim

#### Scenario: The build skill documents the verbs
- **WHEN** the build skill's coordinator reference is read
- **THEN** it lists `claim --as/--wait/--timeout`, the `status` claim lines
  with `--stale-after`, and `release --stale`
