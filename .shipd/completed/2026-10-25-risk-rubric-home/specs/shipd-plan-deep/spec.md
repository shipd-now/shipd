## MODIFIED Requirements

### Requirement: Shared risk rubric
id: plan-deep-rubric
base: 3b705d1e979b

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
