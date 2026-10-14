## MODIFIED Requirements

### Requirement: Epic preflight and planning order
id: epic-grill-preflight-order
base: 25382aaf45ec

The `/s:epic-grill <epic> [--parallel N]` skill SHALL read the epic only
through `spec_status.py epic-show <epic> --json` and `cat epic <epic>`. If
the epic is missing or its status is neither `ready` nor `active`, then the
skill SHALL stop before planning anything. The skill SHALL select every
member in the `unplanned` lane plus every member whose state is `draft`,
and SHALL report every other member with its state, untouched. Where the
epic's stub table carries an `After` column with at least one non-empty
cell, the skill SHALL obtain the plan waves from
`autopilot.py <epic> --waves --parallel N --json` (N defaulting to 3) and
SHALL print each wave with every member's `after` list before planning the
first member. Where it does not, the skill SHALL order the selected members
by dependency, judged from the epic's Decisions, Design, and member
descriptions, breaking ties by ascending risk and then table order, and
SHALL print that order with a one-line reason per member before planning
the first member.

#### Scenario: Unapproved epic stops the skill
- **WHEN** `/s:epic-grill` runs on an epic whose status is `draft`
- **THEN** it reports the status and plans no member

#### Scenario: Order is printed before planning
- **WHEN** an approved epic with three unplanned members and no `After`
  column is grilled
- **THEN** the skill prints all three in planning order, each with a reason,
  before the first planner starts

#### Scenario: Waves are printed before planning
- **WHEN** an approved epic whose `After` column makes `b` and `c` after `a`
  is grilled
- **THEN** the skill prints wave 1 `[a]` and wave 2 `[b, c]`, each member
  with its `after` list, before the first planner starts

### Requirement: Deferring planner contract
id: epic-grill-planner-contract
base: 8b7da10bb91b

The skill SHALL plan the selected `unplanned` members wave by wave, each in
its own worktree created with `shipd worktree <member>`, by spawning one
general-purpose sub-agent per member that runs `/s:plan`: the sub-agents
of one wave SHALL be spawned together in a single message and the skill
SHALL wait for every one of them before starting the next wave; with no
computed waves every member is its own wave, so planning stays one at a
time. The spawn
instruction SHALL name the worktree root of every member already planned in
the run — every earlier wave's members, never a sibling of the same wave —
SHALL forbid any user question round, and SHALL direct the planner,
for each decision the oracle leaves open, to adopt its recommended default
as a settled decision and record a ledger entry with
`**Answered by:** PLANNER`. The instruction SHALL direct the planner, where
its plan builds on a `PLANNER` default in an earlier member's ledger, to
append its own slug to that entry's `**Relied on by:**` field in the earlier
member's installed `plan.md`, and to edit nothing else in another member's
plan. The instruction SHALL also direct the planner to list each such
reliance in its `DEFERRED:` block as a line `RELIED: <earlier member> Q<n>`.
After each wave, the skill SHALL check every `RELIED:` line against the named
entry's `**Relied on by:**` field and SHALL append the planner's slug where it
is missing, before the re-lint. The instruction SHALL direct the planner to install the change and
stop at `Status: draft` without running `spec_gate.py`, ending its turn with
a `DEFERRED:` block listing its `PLANNER` entries. The skill SHALL grade
each planner from disk — `status <member>` printing `draft` and
`spec_lint.py <member>` exiting 0 — and SHALL re-run the linter on every
earlier member after each wave; if a grade or a re-lint fails, then the
skill SHALL stop and ask the human.

#### Scenario: Later planner sees earlier plans
- **WHEN** the second wave's planners are spawned
- **THEN** each instruction names every first-wave member's worktree root

#### Scenario: Wave members are spawned together
- **WHEN** a plan wave holds three members
- **THEN** three planner sub-agents are spawned in one message and no
  third-wave planner starts until all three are graded

#### Scenario: Planner holds questions back
- **WHEN** the oracle returns `INSUFFICIENT` on a planner's decision
- **THEN** the plan adopts the recommended default, records it with
  `**Answered by:** PLANNER`, and no question reaches the user mid-run

#### Scenario: Later planner records its reliance
- **WHEN** member `b`'s plan builds on the default of member `a`'s `PLANNER`
  entry `Q2`
- **THEN** `a`'s installed `plan.md` entry `Q2` carries
  `**Relied on by:** b`, and `a` still passes the linter

#### Scenario: A lost concurrent append is repaired
- **WHEN** wave members `b` and `c` both rely on member `a`'s `Q2`, and `a`'s
  entry ends the wave carrying only `**Relied on by:** b`
- **THEN** the skill appends `c` from `c`'s `RELIED: a Q2` line before
  re-linting `a`
