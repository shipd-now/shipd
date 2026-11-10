## MODIFIED Requirements

### Requirement: Member wave scheduling
id: member-wave-scheduling
base: 3d1d93645f8f

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
slugs; a dependency counts as merged exactly as the merged-dependency
check (`merged-dependency-check`) decides, and a failure of that check SHALL
exit the mode non-zero with the check's error and print no wave. Walking the remaining members in risk-ascending order,
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

## ADDED Requirements

### Requirement: Merged-dependency check
id: merged-dependency-check

The autopilot driver SHALL decide whether an `After` dependency has merged
by reading the repository that tracks the content directory: the git work
tree `git rev-parse --show-toplevel` reports from the resolved content
directory — the consuming repository for an in-repo content directory, the
store's own repository where `store_root` relocates it. The base ref SHALL
be `origin/main` where `git rev-parse --verify --quiet` resolves it in that
repository, else `main`. A dependency counts as merged exactly when
`git ls-tree --name-only <ref>` in that repository, on the `completed/`
directory's path relative to that repository's top level, lists an entry
whose name is a leading digits-and-dashes prefix followed by `-<slug>`.
While neither ref resolves, the dependency SHALL count as not merged. If
the content directory is not inside a git work tree, or `git ls-tree` exits
non-zero, then the check SHALL fail with an error naming the dependency, the
repository or content directory, and git's first error line, and SHALL NOT
report the dependency as unmerged. In the detached pre-build step, where
`store_root` is declared and `store_sync` resolves true, the driver SHALL
first run a best-effort `git fetch origin main` in the store's repository
(exit code ignored); the waves mode SHALL NOT fetch. If the check fails in
the pre-build step, then the member SHALL park as `needs-human` at stage
`dependency` with the check's error as the reason and no session id. Where
`store_root` is declared, an unmerged-dependency reason SHALL also name the
store's repository. The stores guide
(`docs/workspaces/nesting-and-stores.md`) SHALL state that dependents
release once the store repository's base branch carries the completed
entry.

#### Scenario: An external store's base releases a dependent
- **GIVEN** `store_root` resolving into a second git repository whose `main`
  tracks `<repo-folder>/completed/2026-01-01-a`, and ready member `b` after
  `a` in the consuming repository
- **WHEN** `--waves --json` runs from the consuming repository
- **THEN** `b` joins a build wave and `blocked` is empty

#### Scenario: An in-repo content directory reads the consuming repository
- **GIVEN** no `store_root` and a base tree holding
  `.shipd/completed/2026-10-15-a`
- **WHEN** the check runs for `a`
- **THEN** `git ls-tree --name-only origin/main -- .shipd/completed/` runs in
  the consuming repository and `a` counts as merged

#### Scenario: An unresolvable base ref blocks
- **GIVEN** a repository where neither `origin/main` nor `main` resolves
- **WHEN** the check runs for `a`
- **THEN** `a` counts as not merged and no error is raised

#### Scenario: A store outside any git work tree fails loudly
- **GIVEN** `store_root` resolving outside any git work tree, and ready
  member `b` after `a`
- **WHEN** `--waves` runs
- **THEN** the mode exits 1 with an error naming `a` and the content
  directory, and prints no wave

#### Scenario: A failing tree read parks with the cause
- **GIVEN** a member after `a` whose `git ls-tree` exits 128 with
  `fatal: not a tree`
- **WHEN** the detached pre-build step runs
- **THEN** the member parks as `needs-human` at stage `dependency`, the
  reason carries `fatal: not a tree`, and no merge or drift command runs

#### Scenario: The pre-build step fetches the store
- **GIVEN** `store_root` declared and `store_sync` true
- **WHEN** the detached pre-build step runs for a member with a dependency
- **THEN** `git fetch origin main` runs once in the store's repository before
  the check, and a failing fetch does not park the member

#### Scenario: The stores guide names the dependency rule
- **WHEN** `docs/workspaces/nesting-and-stores.md` is read
- **THEN** it states that an `After` dependency releases once the store
  repository's base branch carries the completed entry
