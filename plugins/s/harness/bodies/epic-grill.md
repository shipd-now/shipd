<!-- description: Plan every unplanned member of an approved epic in one pass, ask every open decision in one final round, then reconcile and gate the plans together. -->
# /s:epic-grill — plan a whole epic, ask once

Planning an epic member by member means answering questions one member at a
time, and the plans can drift apart. Plan every unplanned member of one epic,
collect each open human decision into a single final round, then reconcile the
plans and gate them together. You **never build, ship, or open a PR**, and you
never edit the epic file.

<!-- include:preamble -->

Run every command from the repository root. The invocation carries the epic
slug (`/s:epic-grill <slug>`).

1. **Preflight.** Run `python3 "$S/spec_status.py" epic-show <slug> --json` and
   `cat epic <slug>`. If the epic is missing or its status is neither `ready`
   nor `active`, report the status and stop. Select every member in the
   `unplanned` lane plus every member in state `draft`; report the rest
   untouched.
2. **Order and print.** Order the selected members by dependency, judged from
   the epic's Decisions, Design, and member descriptions; break ties by
   ascending risk, then table order. Print the order with one reason per
   member before planning the first.
3. **Plan each member in turn, in this session.** For an `unplanned` member
   run `shipd worktree <member>`, then follow the `/s:plan` workflow inside
   `.worktrees/<member>`, reading the plans already made first. Open no
   question round. For every decision the oracle leaves open, adopt your
   recommended default and record a `## Questions and answers` entry with
   `**Answered by:** PLANNER`: the options in `**Question:**` with the default
   first, the default in `**Answer:**`. Install the change through
   `spec_emit.py` and stop at `Status: draft`; do not run `spec_gate.py`. For
   a `draft` member, find its root with `locate <member>` and do not re-plan
   it. Grade each member from disk: `--root <worktree> status <member>` prints
   `draft` and `spec_lint.py <member> --root <worktree>` exits 0. On a failed
   grade, stop and ask the user.
4. **Consistency pass.** Read each member with
   `--root <worktree> cat change <member>`. Fix in place any mismatch the plans
   and the repository settle (a name, interface, or data shape stated
   differently). Add each conflict only a human can settle as a `PLANNER` entry
   in every affected member's ledger. Note members that modify the same master
   requirement.
5. **One final round.** Build the agenda from the `PLANNER` entries on disk,
   merging entries that pose the same decision. If it is empty, ask nothing.
   Otherwise ask the whole agenda as one numbered typed round: each question
   names its member(s) and `Q<n>`, lists the options with the adopted default
   first and marked "(Recommended)", and the user replies by number. Capture
   each answer that carries a `**Queued:**` slug with `wiki-queue-answer` or
   `wiki-queue-discard`, per `skills/ask/references/capture-rubric.md`.
6. **Amend and gate.** Edit each member's installed artifacts to match the
   answers, rewrite each answered entry to `**Answered by:** USER`, and flag an
   answer that binds every member for `/s:epic <slug> amend` instead of editing
   the epic. Then run `spec_gate.py <member> --root <worktree>` on every
   selected member. On exit 2, resolve what the repository answers, ask the
   user about the rest, and re-gate. Never set a status by any other path.
7. **Hand off.** Print a why-first summary per member, any epic-wide answers
   and shared-requirement pairs, then a `## Summary` heading with one
   sentence, then `/s:autopilot <slug>` alone on its own line. Never build.
