# shipd-plan-deep

### Requirement: Shared risk rubric
id: plan-deep-rubric

The plugin SHALL ship one risk rubric at
`plugins/s/skills/epic/references/risk-rubric.md`, and `/s:plan-deep`,
`/s:epic-grill`, and `/s:epic` SHALL each load it from that path. The
rubric SHALL rate Code, Integration, Unknowns, Risk, and Novelty `low`,
`medium`, or `high`, mapping Novelty from a 1–5 scale (1–2 low, 3 medium,
4–5 high). It SHALL set the Overall level to the highest axis, SHALL lift
any spec with a rabbit hole to at least `medium`, and SHALL make Novelty
4–5 or a Missing interfaces category `high`. It SHALL define a piece as one
decision, one delta requirement, or one task group. It SHALL flag a piece
that touches a `medium` or `high` axis, a rabbit hole, a Partial or Missing
coverage category, a `**Relied on by:**` ledger entry, or a cross-member
interface, and SHALL order flagged pieces high first, then by
`**Relied on by:**` count, then document order.

#### Scenario: Novelty alone makes a spec high
- **WHEN** a spec rates every axis `low` except Novelty 4
- **THEN** its Overall is `high`

#### Scenario: One owner for the scale
- **WHEN** the shipped skills and harness bodies are searched for the
  rubric
- **THEN** the plan-deep, epic-grill, and epic skills and bodies cite
  `skills/epic/references/risk-rubric.md`, no other file defines the
  Novelty scale, and `skills/plan-deep/references/rubric.md` does not exist

### Requirement: Invocation and status guard
id: plan-deep-invocation

`/s:plan-deep <change>` SHALL walk one change, and
`/s:plan-deep <epic> [<member> ...]` SHALL walk the named members in the
order given. With an epic and no members, it SHALL score every member at
`draft`, `ready`, or `rejected` with the rubric and walk those scoring
`medium` or `high` in table order. It SHALL locate each change with
`spec_status.py locate` and read it with `cat change`. In epic mode it
SHALL read the epic with `cat epic` and each sibling's plan with
`cat change`. If a change is `active`, `complete`, or `verified`, then the
skill SHALL report its status and SHALL NOT walk it.

#### Scenario: Built change is refused
- **WHEN** `/s:plan-deep <change>` names a change at `active`
- **THEN** the skill reports the status and edits nothing

#### Scenario: Bare epic walks only risky members
- **GIVEN** an epic with members scoring `low`, `high`, and `medium`
- **WHEN** `/s:plan-deep <epic>` runs
- **THEN** it walks the `high` and `medium` members in table order and
  skips the `low` one

### Requirement: Step-by-step walkthrough
id: plan-deep-walkthrough

For each change, the skill SHALL first restate its decisions, delta
requirements, and task groups, with the rubric's score. It SHALL then walk
one flagged piece per step in rubric order. Each step SHALL restate the
piece and why the rubric flagged it, then end on a plain-text numbered
round offering keep, change, research, and cut or mark out of bounds. A
final step SHALL summarize every unflagged piece in one round. The skill
SHALL NOT issue a question dialog in a turn that carries a restatement.

#### Scenario: Flagged pieces come first, highest risk first
- **GIVEN** a change with one `high` decision, one `medium` requirement,
  and three unflagged task groups
- **WHEN** the walkthrough runs
- **THEN** step 1 is the decision, step 2 the requirement, and step 3 one
  summary of the three task groups

### Requirement: In-place edits and records
id: plan-deep-edits

When the user changes a piece, the skill SHALL edit that change's installed
`plan.md`, delta specs, and `tasks.md` in place. It SHALL append a
`## Questions and answers` entry with `**Answered by:** USER`, continuing
the existing numbering. The skill SHALL NOT edit a sibling member or the
epic file. When an edit touches a sibling's `**Relied on by:**` link or a
shared interface, the skill SHALL name that sibling. When an edit binds
every member, the skill SHALL flag it for `/s:epic <epic> amend`.

#### Scenario: A changed decision is recorded
- **WHEN** the user changes a decision in a plan whose ledger ends at `Q3`
- **THEN** the plan states the new choice and gains a `Q4` entry reading
  `**Answered by:** USER`

#### Scenario: A sibling is named, not edited
- **WHEN** the change edits a default whose entry reads
  `**Relied on by:** b`
- **THEN** the skill names member `b` and leaves `b`'s files untouched

### Requirement: Research hook
id: plan-deep-research

When a piece rests on an external unknown, the skill SHALL offer
`/s:research <question>` as that step's research option. On acceptance it
SHALL invoke `/s:research` by reference, read the installed report back
with `spec_status.py cat research <slug>`, and cite it in the change's
`plan.md` prose.

#### Scenario: Research feeds the plan
- **WHEN** the user picks research on a step
- **THEN** `/s:research` runs, and the plan cites the installed report's
  slug

### Requirement: Re-gate and hand off
id: plan-deep-gate

After walking a change, the skill SHALL run
`spec_gate.py <change> --root <root>`. If the gate exits 2, then the skill
SHALL resolve what the repository answers, ask the user the rest, and
re-gate. The skill SHALL NOT set a status by any other path and SHALL NOT
build. A standalone run SHALL end with `/s:build` alone on its own line. An
epic run SHALL run `autopilot.py <epic> --preflight` once after the last
member, relay its `warn` and `fail` lines and its `preflight:` line, and
print `/s:autopilot <epic>` alone on its own line only on exit 0.

#### Scenario: An edited ready plan is re-gated
- **WHEN** a walk edits a change at `ready`
- **THEN** `spec_gate.py` runs on it, and only its verdict sets the status

#### Scenario: A red epic preflight withholds the hand-off
- **WHEN** an epic run's preflight exits 1
- **THEN** the fail lines are relayed and no `/s:autopilot` line prints
