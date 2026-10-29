<!-- description: Walk one spec's riskiest pieces step by step, edit in place, and re-gate — epic-aware. -->
# /s:plan-deep — walk a risky spec, piece by piece

A gated spec can still hide pieces that deserve a closer look. Walk one
change's riskiest pieces with the user, one step at a time, edit the spec in
place, and re-gate it. You never build, spike, write code, ship, or open a PR.

<!-- include:preamble -->

Run every command from the repository root. The invocation is
`/s:plan-deep <change>` or `/s:plan-deep <epic> [<member> ...]`.

1. **Resolve.** Run `python3 "$S/spec_status.py" locate <name>`. If it names
   no change, run `cat epic <name>` and treat it as an epic; if neither
   resolves, say so and stop. Read each change with
   `--root <root> cat change <change>`; in epic mode also read the epic and
   every sibling's plan.
2. **Guard.** Walk a change only at `draft`, `ready`, or `rejected`. For
   `active`, `complete`, or `verified`, report the status and edit nothing.
3. **Pick members.** With named members, walk them in the order given. With an
   epic and no members, score every eligible member with the rubric at
   `skills/epic/references/risk-rubric.md`, print the risk table, and walk
   the `medium` and `high` members in table order. That file owns the scale;
   never restate it.
4. **Restate.** Per change, restate its decisions, delta requirements, and
   task groups with the rubric's score and the flagged pieces in rubric order,
   in a turn that carries no question dialog.
5. **Walk.** One step per flagged piece, highest risk first. Each step
   restates the piece, says why it was flagged, and ends on a plain-text
   numbered round: keep, change, research, or cut or mark out of bounds. Novelty
   5 always offers cut or out of bounds. Open each round with the brief from
   `skills/document/references/question-brief.md`. A final step summarizes every
   unflagged piece in one round.
6. **Research.** When a piece rests on an external unknown, offer
   `/s:research <question>`; invoke it by reference only while the user is
   present. Read the report with `cat research <slug>` and cite its slug in
   `plan.md` prose.
7. **Edit.** Edit only that change's installed `plan.md`, delta specs, and
   `tasks.md`. Append a `## Questions and answers` entry per changed decision,
   continuing the numbering, with `**Answered by:** USER`. Never edit a sibling
   or the epic. Name any sibling whose `**Relied on by:**` link or shared
   interface the edit touches, and flag an answer that binds every member for
   `/s:epic <epic> amend`. Re-lint with `spec_lint.py <change> --root <root>`.
8. **Re-gate.** Run `spec_gate.py <change> --root <root>`. A pass leaves or
   makes it `ready`. On exit 2, resolve what the repository answers, ask the
   user the rest in one typed round, and re-gate. Never set a status by any
   other path.
9. **Hand off.** Standalone: summarize, then print `/s:build` alone on its
   own line. Epic: after the last member run
   `python3 "$S/autopilot.py" <epic> --preflight` once, relay every `warn` and
   `fail` line and the `preflight:` line, and print `/s:autopilot <epic>`
   alone on its own line only on exit 0; otherwise list the `fail` lines and
   print no hand-off. Never build.
