## MODIFIED Requirements

### Requirement: Member selection and order
id: member-selection-and-order
base: b42006f07a0d

Given an epic at `ready` or `active`, the autopilot SHALL drive only stub
members whose derived state is `unplanned`, ordered in dependency layers
over the stub table's `After` column: an edge runs from each unplanned
member to every `After` slug that is itself unplanned (a dependency in any
other state is satisfied); members with no unsatisfied edge form the next
layer, ordered by the Risk rating ascending (`low`, `medium`, `high`), ties
broken by table order, and the layers are concatenated. Where the table has
no `After` column or every cell is empty, that order SHALL be the
risk-ascending order exactly as before. If the `After` column holds a
dependency cycle, then the autopilot SHALL refuse to run, naming the cycle's
slugs in order and the linter's single-epic mode as the remedy, and SHALL
drive nothing. The dry run SHALL print the order under the label
`Member order (After, then risk ascending):`. Members in any other state
SHALL be reported under that state and left untouched — a `rejected` member
SHALL never be re-driven.

#### Scenario: Risk-ascending order
- **GIVEN** unplanned members rated high, low, and medium in table order and
  no `After` column
- **WHEN** a run starts
- **THEN** the driving order is the low, then medium, then high member

#### Scenario: Declared dependencies order the detached drive
- **GIVEN** unplanned members `a` rated high and `b` rated low, with `b`'s
  `After` cell naming `a`
- **WHEN** a run starts
- **THEN** the driving order is `a` then `b`

#### Scenario: A cycle refuses the run
- **GIVEN** `x` after `y` and `y` after `x` in the stub table
- **WHEN** a run or dry run starts
- **THEN** the autopilot exits non-zero with an error naming `x -> y -> x`
  and drives nothing

#### Scenario: In-flight members are skipped
- **GIVEN** a member whose plan sits at `rejected`
- **WHEN** a run executes
- **THEN** that member is reported as rejected and not driven

### Requirement: Targeted single-member drive
id: targeted-member-drive
base: 0da56359f2eb

The autopilot SHALL support driving a single epic member selected by slug —
independent of the epic-level auto-selection — entering the resolved
`autonomous-pipeline` at the stage matching that member's current lifecycle
state: an `unplanned` member from `plan`, a `ready` (planned, lint-clean) member
from `build`, skipping the stages already satisfied. The targeted drive SHALL
reuse the same worktree, graded stage loop, heartbeat, and park/ship semantics as
an epic run, drive exactly the one named member, and back the board's per-card
`run` action. It SHALL leave the epic-level `member-selection-and-order`
auto-selection unchanged.

#### Scenario: A ready member enters at build
- **GIVEN** an epic member whose plan sits at `ready`, lint-clean
- **WHEN** a targeted single-member drive runs for that member
- **THEN** the pipeline starts at `build` — `plan` and `gate` are skipped — and
  the member is driven through to its terminal outcome

#### Scenario: An unplanned member enters at plan
- **GIVEN** an epic member whose derived state is `unplanned`
- **WHEN** a targeted single-member drive runs for that member
- **THEN** the pipeline starts at `plan`, and no other member is driven

#### Scenario: Auto-selection is untouched
- **WHEN** a normal epic run (no targeted member) is driven
- **THEN** members are still selected and ordered over the `unplanned` set
  exactly as `member-selection-and-order` states

### Requirement: Member wave scheduling
id: member-wave-scheduling
base: 75133e80b898
Dropped: A cycle serialises its members

The autopilot driver SHALL provide a `--waves` mode (`autopilot.py <epic>
--waves [--parallel N] [--json]`) that computes, from on-disk state and the
local git refs alone, the waves of members the in-session drive may run
concurrently, and drives nothing. `--parallel` SHALL be an integer of at
least 1, default 3, and SHALL cap every wave's size. If the stub table's
`After` column holds a dependency cycle, then the mode SHALL exit non-zero
with an error naming the cycle's slugs in order and SHALL print no wave.
The mode SHALL emit plan waves first over the `unplanned` members. Where the
epic's stub table carries an `After` column with at least one non-empty
cell, plan waves SHALL be dependency layers: an edge runs from each unplanned
member to every `After` slug that is itself unplanned (a dependency in any
other state is satisfied); members with no unsatisfied edge form the next
layer, ordered risk-ascending then by table order and chunked into waves of
at most N. Where no non-empty `After` cell exists, plan waves SHALL be every
`unplanned` member in risk-ascending order (ties by table order), chunked
into waves of at most N, exactly as before. Each plan wave SHALL be tagged
stage `plan`. It SHALL then emit build waves over the `ready` members: each
member's capabilities are the capability directory names under its planned
change's `specs/`, read from the root that hosts the change. A `ready`
member whose `After` cell names a dependency not yet merged into the base
branch SHALL join no wave and SHALL be listed as blocked with the unmerged
slugs; a dependency counts as merged exactly when the base branch's tree —
`origin/main` where that ref exists, else `main`, read with `git ls-tree`
from the repository root — holds a `completed/` entry whose name is a
leading digits-and-dashes prefix followed by `-<slug>`, and any git failure
counts as not merged. Walking the remaining members in risk-ascending order,
each member joins the earliest build wave whose members' capabilities are
all disjoint from its own and whose size is below N, else opens a new wave.
Members in any other state SHALL be listed as skipped with their state. With
`--json` the mode SHALL print one object `{"epic", "parallel", "waves":
[{"index", "stage", "members": [{"slug", "risk", "capabilities",
"after"}]}], "blocked": [{"member", "waiting_on"}], "skipped": [{"member",
"state"}]}`, `after` being the member's declared `After` slugs (empty
without the column) and `blocked` always present; without it, one
`wave <index> [<stage>]:` line per wave naming its members and, for build
waves, each member's capabilities, and for plan waves each member's
`after` list when non-empty, then one `blocked: <slug> (waiting on <slugs>)`
line per blocked member. The computation SHALL be deterministic for a given
tree and set of refs.

#### Scenario: Plan waves chunk unplanned members risk-ascending
- **GIVEN** unplanned members rated high, low, low, and medium, no `After`
  column, and `--parallel 2`
- **WHEN** `--waves` runs
- **THEN** the first wave is the two low members and the second is the
  medium then the high member, both tagged `plan`

#### Scenario: Declared dependencies layer the plan waves
- **GIVEN** an `After` column making `b` after `a`, and `c`, `d`, `e` after
  `b`, all unplanned, with `--parallel 3`
- **WHEN** `--waves` runs
- **THEN** the plan waves are `[a]`, `[b]`, `[c, d, e]`, and each member
  entry carries its `after` list

#### Scenario: A satisfied dependency does not block
- **GIVEN** `b` after `a` where `a` is already `ready`
- **WHEN** `--waves` runs
- **THEN** `b` sits in the first plan wave and `a` in a build wave

#### Scenario: A cycle refuses the waves mode
- **GIVEN** `x` after `y` and `y` after `x`, and a free unplanned `z`
- **WHEN** `--waves` runs
- **THEN** the mode exits 1 with an error naming `x -> y -> x` and prints no
  wave

#### Scenario: An unmerged dependency blocks a build wave
- **GIVEN** ready members `a` and `b` with disjoint capabilities, `b` after
  `a`, and the base branch's tree holding no `completed/` entry for `a`
- **WHEN** `--waves --json` runs
- **THEN** the only build wave is `[a]` and `blocked` is
  `[{"member": "b", "waiting_on": ["a"]}]`

#### Scenario: A merged dependency releases its dependent
- **GIVEN** ready member `b` after `a`, and the base branch's tree holding
  `completed/2026-10-15-a`
- **WHEN** `--waves` runs
- **THEN** `b` joins a build wave and `blocked` is empty

#### Scenario: A suffix match is not a merge
- **GIVEN** ready member `b` after `a`, and the base branch's tree holding
  only `completed/2026-10-15-extra-a`
- **WHEN** `--waves` runs
- **THEN** `b` is blocked waiting on `a`

#### Scenario: Disjoint capabilities share a build wave
- **GIVEN** ready members `a` touching capability `x`, `b` touching `y`, and
  `c` touching `x` and `z`, with `--parallel 3`
- **WHEN** `--waves` runs
- **THEN** `a` and `b` share the first build wave and `c` sits alone in the
  second

#### Scenario: The cap splits a wave
- **GIVEN** four ready members with pairwise-disjoint capabilities and
  `--parallel 3`
- **WHEN** `--waves` runs
- **THEN** the first build wave holds three members and the second holds one

#### Scenario: Waves drive nothing
- **WHEN** `--waves` runs
- **THEN** no session, gate, worktree, or heartbeat action occurs and the
  exit code is 0

#### Scenario: A capability is read from the hosting worktree
- **GIVEN** a ready member whose planned change lives under
  `.worktrees/<member>/` rather than the root
- **WHEN** `--waves` runs
- **THEN** that member's capabilities are the `specs/` directory names of
  that worktree's planned change

#### Scenario: Serial cap reproduces today's order
- **WHEN** `--waves --parallel 1` runs on an epic without an `After` column
- **THEN** every wave holds exactly one member: the unplanned members in
  the same order the dry run prints, followed by the ready members in
  risk-ascending order with ties by table order
