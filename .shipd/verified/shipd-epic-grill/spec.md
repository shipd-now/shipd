# shipd-epic-grill

### Requirement: Epic preflight and planning order
id: epic-grill-preflight-order

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

### Requirement: Cross-plan consistency pass
id: epic-grill-consistency-pass

After every selected member is planned, the skill SHALL read every selected
member's change through `spec_status.py --root <worktree> cat change
<member>` and SHALL check the plans against each other and against the
epic's Decisions. The skill SHALL fix in place any mismatch the plans and
repository settle — a name, interface, or data shape one plan states
differently from another. The skill SHALL add to the question agenda any
conflict between plans that only a human can settle, recording it as a
`PLANNER` entry in each affected member's ledger.

#### Scenario: Interface mismatch is fixed silently
- **WHEN** one plan names a flag `--defer` and the plan consuming it names
  `--deferred`
- **THEN** the skill aligns the consumer plan without asking the user

### Requirement: One final question round
id: epic-grill-final-round

The skill SHALL build its question agenda from the `PLANNER` entries read
from disk across all selected members, merging entries that pose the same
decision. If the agenda is empty, then the skill SHALL ask nothing. Otherwise
the skill SHALL ask the whole agenda only after the consistency pass, as one
numbered typed round. Each question SHALL open with the brief that
`plugins/s/skills/document/references/question-brief.md` defines, SHALL name
its member(s) and `Q<n>` references, and SHALL list the adopted default as
the first option marked recommended. The skill SHALL NOT issue an
AskUserQuestion for the agenda. For each answered entry that carries a
`**Queued:**` slug, the skill SHALL classify the answer against the capture
rubric and answer or discard the queued block, as `/s:plan` does.

#### Scenario: Five decisions take one typed round
- **WHEN** the agenda holds five decisions
- **THEN** the skill asks all five in one numbered typed round, each with
  its brief, and no question round before the consistency pass

#### Scenario: Empty agenda asks nothing
- **WHEN** no member holds a `PLANNER` entry
- **THEN** the skill asks no question round

### Requirement: Amend, gate, and hand off
id: epic-grill-amend-gate

For each answer, the skill SHALL edit the affected installed artifacts in
place to match it and SHALL rewrite the entry's `**Answered by:**` to `USER`
with the user's resolution as its `**Answer:**`. Where an answer binds every
member, the skill SHALL flag it for `/s:epic <epic> amend` and SHALL NOT
edit the epic. If any answer chose an option other than the adopted default,
then before gating the skill SHALL re-run the consistency pass on the member
holding each overturned entry and on every member that entry's
`**Relied on by:**` field names, or on every selected member when an
overturned entry carries no such field. The re-check SHALL fix in place what
the plans and repository settle and SHALL ask any conflict only a human can
settle in one further round before gating. The skill SHALL then run
`spec_gate.py <member>` on every selected member. If the gate exits 2, then
the skill SHALL resolve the findings the repository answers, ask the human
about the rest, and re-gate. The skill SHALL NOT set a member's status by
any other path. After the last gate the skill SHALL run
`autopilot.py <epic> --preflight` once from the repository root and SHALL
relay every `warn` and `fail` line and the closing `preflight:` line
verbatim. The skill SHALL end with a why-first summary per member and a
`## Summary` heading with one sentence that states the preflight verdict.
When the preflight exits 0, the skill SHALL print `/s:autopilot <epic>` on
its own line; when it exits non-zero, the skill SHALL list every `fail` line
it printed (or its error text when it printed no rubric line), SHALL name
the preflight command to re-run after the remedies, and SHALL NOT print the
hand-off. A `warn` line SHALL NOT block the hand-off. The skill SHALL NOT
build.

#### Scenario: Overridden default amends the plan
- **WHEN** the user picks a non-default option for a member's `Q1`
- **THEN** that member's plan states the chosen option, its ledger entry
  reads `**Answered by:** USER`, and its gate passes

#### Scenario: Overturned default re-checks its dependents
- **WHEN** the user overturns member `a`'s `Q2`, whose entry carries
  `**Relied on by:** b`
- **THEN** the skill re-runs the consistency pass on `a` and `b` before
  gating either

#### Scenario: Accepted defaults skip the re-check
- **WHEN** the user accepts every adopted default
- **THEN** the skill gates every member without a second consistency pass

#### Scenario: Members reach ready only after the round
- **WHEN** the grill is interrupted before the final round
- **THEN** every planned member is left at `draft`

#### Scenario: Green preflight hands off
- **GIVEN** every selected member gated to `ready`
- **WHEN** `autopilot.py <epic> --preflight` exits 0 with every line `ok`
- **THEN** the Ending relays `preflight: ok` and prints `/s:autopilot
  <epic>` on its own line

#### Scenario: Warnings do not block the hand-off
- **WHEN** the preflight exits 0 carrying a `warn drift —` line
- **THEN** the Ending relays that line and still prints `/s:autopilot
  <epic>`

#### Scenario: A failing rubric lists its lines instead
- **WHEN** the preflight exits 1 with a `fail members —` line naming an
  unplanned member
- **THEN** the Ending lists that `fail` line, names the preflight command
  to re-run, and prints no `/s:autopilot` line

#### Scenario: A rubric-less error is red
- **WHEN** the preflight exits non-zero printing no `ok|warn|fail` line
- **THEN** the Ending relays the error text in place of the `fail` lines
  and prints no `/s:autopilot` line

### Requirement: Risk report and plan-deep suggestion
id: epic-grill-risk-report

After the last gate and before the launch preflight, the skill SHALL load
`skills/plan-deep/references/rubric.md` and print one risk table row per
selected member with the columns Member, Code, Integration, Unknowns, Risk,
Novelty, Overall, and Why. The skill SHALL NOT write the scores into any
file. When at least one member's Overall is `medium` or `high`, the skill
SHALL print `/s:plan-deep <epic> <member> ...` naming exactly those members
in table order directly under the table, and SHALL close its whole output,
after the `/s:autopilot` line or the fail list, with the sentence
`There are complex specs worth a deep plan, kick it off with:`, a blank
line, and that same command alone on its own line. When every member is
`low`, the skill SHALL print neither. The skill SHALL NOT run
`/s:plan-deep` itself.

#### Scenario: A medium member earns the suggestion twice
- **GIVEN** a grill whose members `a` and `b` gate to `ready`, scoring `low`
  and `medium`
- **WHEN** the Ending prints
- **THEN** the risk table shows both rows, `/s:plan-deep <epic> b` prints
  under the table, and the output's last line is `/s:plan-deep <epic> b`,
  preceded by the "There are complex specs" sentence and a blank line

#### Scenario: An all-low epic prints no suggestion
- **WHEN** every selected member scores `low`
- **THEN** the risk table prints and no `/s:plan-deep` line appears

#### Scenario: A red preflight still closes on the suggestion
- **GIVEN** a `high` member and a preflight that exits 1
- **WHEN** the Ending prints
- **THEN** the fail lines are listed, no `/s:autopilot` line prints, and the
  output still closes on the `/s:plan-deep` command

#### Scenario: Scores are never persisted
- **WHEN** the risk table prints
- **THEN** no member's `plan.md`, delta spec, or `tasks.md` changes
