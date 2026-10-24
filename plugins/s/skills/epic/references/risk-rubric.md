# Risk rubric

The one risk rubric `/s:epic`, `/s:epic-grill`, and `/s:plan-deep` share.
All three load it from `skills/epic/references/risk-rubric.md`; none restates
the scale. It scores a spec `low`, `medium`, or `high` and flags the pieces
that deserve a closer look. A plan's score is a judgement against the plan as
written, shown on screen and never saved into a file. Only `/s:epic`'s four
stub ratings are written down, in the epic table.

Source: research `epic-complexity-map` (read it with `spec_status.py cat
research epic-complexity-map`).

## Axes

Rate each axis `low`, `medium`, or `high`. Code, Integration, Unknowns, and
Risk are the epic table's four ratings, re-judged against the plan as written
rather than copied from the stub.

| Axis | low | medium | high |
|---|---|---|---|
| Code | A few files, an existing pattern to follow | Several files or a new module in a known shape | Many files, a new subsystem, or a wide refactor |
| Integration | Self-contained | Touches one other component or contract | Touches several components, a sibling member, or an external system |
| Unknowns | Every question answered | A few assumptions still unverified | A load-bearing question open or resting on an external fact |
| Risk | A failure is cheap and visible | A failure costs rework | A failure loses data, breaks callers, or is hard to undo |
| Novelty | Keogh 1-2 | Keogh 3 | Keogh 4-5 |

`/s:epic` uses only this Axes table, for its four stub rating cells; the rest
scores a written plan.

### Novelty (Keogh scale)

Liz Keogh rates work by who has done it before. Pick the level, then map it.

- 5: "Nobody in the world has ever done this before."
- 4: "Someone in the world did this, but not in our organization."
- 3: "Someone in our company has done this, or we have access to expertise."
- 2: "Someone in our team knows how to do this."
- 1: "We all know how to do this."

Mapping: 1-2 is `low`, 3 is `medium`, 4-5 is `high`. A 5 is a spike, not a
plan; a skill that cannot spike cuts the piece or marks it out of bounds.

## Rabbit holes

A rabbit hole is a part of the spec too unknown, complex, or open-ended to
bet on. Walk each use case in slow motion and look for four:

- New technical work never done here.
- A technical assumption not yet verified.
- An open-ended piece with no natural stopping point.
- A case with no stated out-of-bounds.

Resolve a hole by patching it, cutting it, or declaring it out of bounds.

## Coverage categories

Mark each of seven categories `Clear`, `Partial`, or `Missing`:

1. Scope and behavior
2. Interfaces and data shapes
3. Integration and dependencies
4. Edge cases and failure
5. Constraints and trade-offs
6. Completion signals
7. Terminology

## Overall

- The Overall level is the highest of the five axes.
- Any rabbit hole lifts Overall to at least `medium`.
- Novelty 4-5, or a Missing interfaces-and-data-shapes category, makes Overall
  `high`.

## Pieces

A piece is one decision, one delta requirement, or one task group.

A piece is flagged when it touches any of:

- an axis rated `medium` or `high`,
- a rabbit hole,
- a Partial or Missing coverage category,
- a ledger entry carrying `**Relied on by:**`,
- a cross-member interface.

Order flagged pieces `high` first, then by `**Relied on by:**` count (most
first), then document order. Unflagged pieces are summarized together in one
closing step.

## The grill's table

`/s:epic-grill` prints one row per selected member:

`| Member | Code | Integration | Unknowns | Risk | Novelty | Overall | Why |`

`Novelty` shows the mapped level. `Why` is a short phrase naming the axis,
hole, or category that set Overall.
