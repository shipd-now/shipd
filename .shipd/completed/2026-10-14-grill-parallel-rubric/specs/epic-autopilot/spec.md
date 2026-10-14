## MODIFIED Requirements

### Requirement: Member wave scheduling
id: member-wave-scheduling
base: efbd24b07b92

The autopilot driver SHALL provide a `--waves` mode (`autopilot.py <epic>
--waves [--parallel N] [--json]`) that computes, from on-disk state alone,
the waves of members the in-session drive may run concurrently, and drives
nothing. `--parallel` SHALL be an integer of at least 1, default 3, and
SHALL cap every wave's size. The mode SHALL emit plan waves first over the
`unplanned` members. Where the epic's stub table carries an `After` column
with at least one non-empty cell, plan waves SHALL be dependency layers: an
edge runs from each unplanned member to every `After` slug that is itself
unplanned (a dependency in any other state is satisfied); members with no
unsatisfied edge form the next layer, ordered risk-ascending then by table
order and chunked into waves of at most N; members that remain when no
member is free (a cycle) SHALL each form a wave of one, in table order,
after every acyclic layer. Where no non-empty `After` cell exists, plan
waves SHALL be every `unplanned` member in risk-ascending order (ties by
table order), chunked into waves of at most N, exactly as before. Each plan
wave SHALL be tagged stage `plan`. It SHALL then emit build
waves over the `ready` members: each member's capabilities are the
capability directory names under its planned change's `specs/`, read from
the root that hosts the change; walking members in risk-ascending order,
each member joins the earliest build wave whose members' capabilities are
all disjoint from its own and whose size is below N, else opens a new wave.
Members in any other state SHALL be listed as skipped with their state. With
`--json` the mode SHALL print one object `{"epic", "parallel", "waves":
[{"index", "stage", "members": [{"slug", "risk", "capabilities",
"after"}]}], "skipped": [{"member", "state"}]}`, `after` being the member's
declared `After` slugs (empty without the column); without it, one
`wave <index> [<stage>]:` line per wave naming its members and, for build
waves, each member's capabilities, and for plan waves each member's
`after` list when non-empty. The computation SHALL be deterministic for a
given tree.

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

#### Scenario: A cycle serialises its members
- **GIVEN** `x` after `y` and `y` after `x`, both unplanned, and a free
  unplanned `z`
- **WHEN** `--waves` runs
- **THEN** the plan waves are `[z]`, `[x]`, `[y]`

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
