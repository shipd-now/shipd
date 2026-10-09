## ADDED Requirements

### Requirement: Epic preflight and planning order
id: epic-grill-preflight-order

The `/s:epic-grill <epic>` skill SHALL read the epic only through
`spec_status.py epic-show <epic> --json` and `cat epic <epic>`. If the epic
is missing or its status is neither `ready` nor `active`, then the skill
SHALL stop before planning anything. The skill SHALL select every member in
the `unplanned` lane plus every member whose state is `draft`, and SHALL
report every other member with its state, untouched. The skill SHALL order
the selected members by dependency, judged from the epic's Decisions,
Design, and member descriptions, breaking ties by ascending risk and then
table order, and SHALL print that order with a one-line reason per member
before planning the first member.

#### Scenario: Unapproved epic stops the skill
- **WHEN** `/s:epic-grill` runs on an epic whose status is `draft`
- **THEN** it reports the status and plans no member

#### Scenario: Order is printed before planning
- **WHEN** an approved epic has three unplanned members
- **THEN** the skill prints all three in planning order, each with a reason,
  before the first planner starts

### Requirement: Deferring planner contract
id: epic-grill-planner-contract

The skill SHALL plan the selected `unplanned` members one at a time, each in
its own worktree created with `shipd worktree <member>`, by spawning one
general-purpose sub-agent per member that runs `/s:plan`. The spawn
instruction SHALL name the worktree root of every member already planned in
the run, SHALL forbid any user question round, and SHALL direct the planner,
for each decision the oracle leaves open, to adopt its recommended default
as a settled decision and record a ledger entry with
`**Answered by:** PLANNER`. The instruction SHALL direct the planner to
install the change and stop at `Status: draft` without running
`spec_gate.py`, ending its turn with a `DEFERRED:` block listing its
`PLANNER` entries. The skill SHALL grade each planner from disk —
`status <member>` printing `draft` and `spec_lint.py <member>` exiting 0 —
and if a grade fails, then the skill SHALL stop and ask the human.

#### Scenario: Later planner sees earlier plans
- **WHEN** the second member's planner is spawned
- **THEN** its instruction names the first member's worktree root

#### Scenario: Planner holds questions back
- **WHEN** the oracle returns `INSUFFICIENT` on a planner's decision
- **THEN** the plan adopts the recommended default, records it with
  `**Answered by:** PLANNER`, and no question reaches the user mid-run

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
the skill SHALL ask the whole agenda only after the consistency pass, through
AskUserQuestion calls of at most four questions each, each question naming
its member(s) and `Q<n>` references, with the adopted default as the first
option marked recommended. The turn issuing a dialog SHALL carry no other
substantive prose. For each answered entry that carries a `**Queued:**`
slug, the skill SHALL classify the answer against the capture rubric and
answer or discard the queued block, as `/s:plan` does.

#### Scenario: Five decisions take two dialogs
- **WHEN** the agenda holds five decisions
- **THEN** the skill issues two AskUserQuestion calls, of four and one
  questions, and no question round before the consistency pass

#### Scenario: Empty agenda asks nothing
- **WHEN** no member holds a `PLANNER` entry
- **THEN** the skill issues no AskUserQuestion call

### Requirement: Amend, gate, and hand off
id: epic-grill-amend-gate

For each answer, the skill SHALL edit the affected installed artifacts in
place to match it and SHALL rewrite the entry's `**Answered by:**` to `USER`
with the user's resolution as its `**Answer:**`. Where an answer binds every
member, the skill SHALL flag it for `/s:epic <epic> amend` and SHALL NOT
edit the epic. The skill SHALL then run `spec_gate.py <member>` on every
selected member. If the gate exits 2, then the skill SHALL resolve the
findings the repository answers, ask the human about the rest, and re-gate.
The skill SHALL NOT set a member's status by any other path. The skill SHALL
end with a why-first summary per member, a `## Summary` heading with one
sentence, and `/s:autopilot <epic>` on its own line, and SHALL NOT build.

#### Scenario: Overridden default amends the plan
- **WHEN** the user picks a non-default option for a member's `Q1`
- **THEN** that member's plan states the chosen option, its ledger entry
  reads `**Answered by:** USER`, and its gate passes

#### Scenario: Members reach ready only after the round
- **WHEN** the grill is interrupted before the final round
- **THEN** every planned member is left at `draft`
