<!-- description: Plan every unplanned member of an approved epic in one pass, ask every open decision in one final round, then reconcile and gate the plans together and hand off to /s:autopilot on a green preflight. -->
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
2. **Order and print.** The invocation may carry `--parallel N` (default 3).
   If the epic's `## Changes` table carries an `After` column with at least
   one non-empty cell, run
   `python3 "$S/autopilot.py" <slug> --waves --parallel N --json`, keep the
   `plan` waves restricted to the selected members, and print each wave with
   its members' `after` lists before planning the first. Otherwise order the
   selected members by dependency, judged from the epic's Decisions, Design,
   and member descriptions; break ties by ascending risk, then table order;
   print the order with one reason per member before planning the first, each
   member being its own wave.
3. **Plan wave by wave, in this session.** Run one planner per member of a
   wave, reading the plans of every earlier wave first and never a sibling of
   the same wave; grade the whole wave and re-lint every earlier member before
   the next wave starts. Before the first wave, add every selected `draft`
   member to the plans you read, since computed waves hold only `unplanned`
   members. For an `unplanned` member
   run `shipd worktree <member>`, then follow the `/s:plan` workflow inside
   `.worktrees/<member>`. Open no
   question round. For every decision the oracle leaves open, adopt your
   recommended default and record a `## Questions and answers` entry with
   `**Answered by:** PLANNER`: the options in `**Question:**` with the default
   first, the default in `**Answer:**`, and `**Queued:**` when the oracle
   filed one. Where a member's plan builds on an earlier member's `PLANNER` default,
   append the later member's slug to that entry's `**Relied on by:**` field (adding it as
   the entry's last line if absent) in that member's installed plan, edit
   nothing else in it, and list each such reliance as a `RELIED: <member> Q<n>`
   line in its `DEFERRED:` block. After each wave, check each `RELIED:` line
   against that entry's `**Relied on by:**` field and append a missing slug
   before the re-lint of that member. Install the change through
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
   opens with the brief from `skills/document/references/question-brief.md`,
   names its member(s) and `Q<n>`, lists the options with the adopted default
   first and marked "(Recommended)", and the user replies by number. Capture
   each answer that carries a `**Queued:**` slug with `wiki-queue-answer` or
   `wiki-queue-discard`, per `skills/ask/references/capture-rubric.md`.
6. **Amend and gate.** Edit each member's installed artifacts to match the
   answers, rewrite each answered entry to `**Answered by:** USER`, and flag an
   answer that binds every member for `/s:epic <slug> amend` instead of editing
   the epic. When an answer overturned a default, re-run the consistency pass on
   that entry's member and on every member its `**Relied on by:**` field names
   (every selected member when the field is absent), fix what the plans and
   repository settle, and ask any conflict only a human can settle as one more
   numbered typed round (each question opening with the same brief), then
   apply those answers the same way without re-checking again. Keep the
   field when rewriting an entry to `USER`. Then run `spec_gate.py <member> --root <worktree>` on every
   selected member. On exit 2, resolve what the repository answers, ask the
   user about the rest, and re-gate. Never set a status by any other path.
7. **Risk report, preflight, and hand off.** After the last gate, print a
   why-first summary per member, any epic-wide answers and shared-requirement
   pairs, then the risk report: load `skills/plan-deep/references/rubric.md`,
   score each selected member against its plan as written, and print a
   `| Member | Code | Integration | Unknowns | Risk | Novelty | Overall | Why |`
   row per member (write the scores into no file). When any member's Overall is
   `medium` or `high`, print `/s:plan-deep <epic> <member> ...` under the table
   naming exactly those members; when all are `low`, print neither. Then run
   `python3 "$S/autopilot.py" <slug> --preflight` once from the repository
   root and relay every `warn` and `fail` line and the `preflight:` line. Then
   a `## Summary` heading with one sentence stating the preflight
   verdict, and hand off only when the preflight exits 0 by printing
   `/s:autopilot <slug>` alone on its own line; otherwise list every `fail`
   line (or the error text when no rubric line printed), name the preflight
   command to re-run, and print no hand-off. With any `medium` or `high`
   member, end the whole output, after the hand-off or the fail list, with
   `There are complex specs worth a deep plan, kick it off with:`, a blank
   line, and the same `/s:plan-deep <epic> <member> ...` command alone on its
   own line. Never run it, and never build.
