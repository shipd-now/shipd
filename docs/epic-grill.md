<!-- doc-type: how-to -->

# Epic grill

The epic grill plans every unplanned member of one approved epic in a single
pass. It asks every human decision in one final round, then gates the plans
together. You run it as `/s:epic-grill <epic>`.

The grill never builds, never opens a pull request, and never edits the epic.
Its hand-off is `/s:autopilot <epic>`.

## When to use it

Use the grill after an epic reaches `ready` and before you deliver its
members. It suits an epic whose members share names, interfaces, or
decisions, because it checks the plans against each other before it asks
you anything.

The grill needs an epic at `ready` or `active`. A `draft` epic still needs
approval, so the grill plans nothing for it. See [Epics](epics.md).

The grill selects two kinds of member:

- every member in the `unplanned` lane;
- every member left at `draft` by an earlier, interrupted grill.

An interrupted grill leaves its planned members at `draft`. A second run of
`/s:epic-grill <epic>` selects them again, so it resumes the first run.

To plan one member on its own, use `/s:plan <member>` instead.

## How to run it

1. **Preflight and member order.** Run `/s:epic-grill <epic>`. The grill
   reads the epic and prints the member order. When the epic's `After`
   column holds a dependency, that column sets the order. Otherwise the
   grill judges the dependency order from the epic's Decisions and Design.
2. **Planning in waves.** The grill plans the members wave by wave, in the
   printed order. Each planner reads the plans of earlier waves. A planner
   asks you nothing. It adopts its recommended default for each open
   decision and records that decision for the final round.
3. **Consistency pass.** The grill checks the plans against each other and
   against the epic's Decisions. It fixes a mismatch that the repository
   settles. It records a conflict that only a human can settle.
4. **Final round.** The grill asks every recorded decision in one numbered
   round. Each question lists the recommended default first. Reply in one
   line, such as `1a 2b`. An empty agenda asks nothing.
5. **Amend and gate.** The grill edits each plan to state your answer, then
   gates every member. A member reaches `ready` only through the gate. An
   answer that binds every member gets a flag for `/s:epic <epic> amend`.
6. **Risk report.** The grill scores each member on the risk rubric and
   prints one table row per member. A member scored `medium` or `high` draws
   a `/s:plan-deep <epic> <member>` suggestion.
7. **Launch preflight.** The grill runs the autopilot launch preflight and
   relays its `warn` and `fail` lines.

The ending depends on the preflight:

- A green preflight ends on the hand-off line `/s:autopilot <epic>`.
- A red preflight lists the failing checks and hands off nothing.

Then run `/s:autopilot <epic>` to deliver the members. See
[Autopilot](autopilot.md).

## Reference

| argument | what it sets | default |
| --- | --- | --- |
| `<epic>` | The slug of the epic to plan. | required |
| `--parallel N` | The most members one plan wave holds. | 3 |

See also:

- [Epics](epics.md) — write and amend the epic the grill plans.
- [Autopilot](autopilot.md) — deliver the members the grill gates.
