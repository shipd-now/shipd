## MODIFIED Requirements

### Requirement: Deferring planner contract
id: epic-grill-planner-contract
base: 9b685c44dab5

The skill SHALL plan the selected `unplanned` members one at a time, each in
its own worktree created with `shipd worktree <member>`, by spawning one
general-purpose sub-agent per member that runs `/s:plan`. The spawn
instruction SHALL name the worktree root of every member already planned in
the run, SHALL forbid any user question round, and SHALL direct the planner,
for each decision the oracle leaves open, to adopt its recommended default
as a settled decision and record a ledger entry with
`**Answered by:** PLANNER`. The instruction SHALL direct the planner, where
its plan builds on a `PLANNER` default in an earlier member's ledger, to
append its own slug to that entry's `**Relied on by:**` field in the earlier
member's installed `plan.md`, and to edit nothing else in another member's
plan. The instruction SHALL direct the planner to install the change and
stop at `Status: draft` without running `spec_gate.py`, ending its turn with
a `DEFERRED:` block listing its `PLANNER` entries. The skill SHALL grade
each planner from disk — `status <member>` printing `draft` and
`spec_lint.py <member>` exiting 0 — and SHALL re-run the linter on every
earlier member after each planner; if a grade or a re-lint fails, then the
skill SHALL stop and ask the human.

#### Scenario: Later planner sees earlier plans
- **WHEN** the second member's planner is spawned
- **THEN** its instruction names the first member's worktree root

#### Scenario: Planner holds questions back
- **WHEN** the oracle returns `INSUFFICIENT` on a planner's decision
- **THEN** the plan adopts the recommended default, records it with
  `**Answered by:** PLANNER`, and no question reaches the user mid-run

#### Scenario: Later planner records its reliance
- **WHEN** member `b`'s plan builds on the default of member `a`'s `PLANNER`
  entry `Q2`
- **THEN** `a`'s installed `plan.md` entry `Q2` carries
  `**Relied on by:** b`, and `a` still passes the linter

### Requirement: Amend, gate, and hand off
id: epic-grill-amend-gate
base: e1feaf440283

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
any other path. The skill SHALL end with a why-first summary per member, a
`## Summary` heading with one sentence, and `/s:autopilot <epic>` on its own
line, and SHALL NOT build.

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
