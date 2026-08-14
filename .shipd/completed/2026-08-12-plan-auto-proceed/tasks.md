## 1. The evidenced readiness attestation

- [x] 1.1 [req: readiness-attestation] In
      `plugins/s/skills/plan/references/readiness.md`, add an "Attestation"
      section after the four items: each of items 1–3 is discharged with a
      concrete citation (capability name, `file:line`, or requirement id),
      item 4 names every task-shaping decision with the rung that settled it
      (investigation, personal memory, oracle, user) or states that none
      remain, and an item with no such evidence counts as unmet.
- [x] 1.2 [req: readiness-attestation, readiness-checklist-gate] In
      `plugins/s/skills/plan/SKILL.md`, rewrite flow step 5 ("Check
      readiness") to require printing the attestation as user-visible text
      before emission, and to state that internal reasoning does not satisfy
      it.

## 2. Auto-proceed replaces the go-ahead question

- [x] 2.1 [req: investigation-findings-digest] In
      `plugins/s/skills/plan/SKILL.md`, rewrite flow step 2's two endings:
      delete the "We have enough details — shall I write the plan now?"
      question and its affirmative loop; when the attestation holds and no
      un-inferrable decision remains, the skill continues in the same turn to
      the depth gate and emission; when decisions remain, the digest names them
      under `OPEN QUESTIONS` and the turn ends on the typed round.
- [x] 2.2 [req: oracle-consultation] In
      `plugins/s/skills/plan/SKILL.md`, remove the "The investigation turn
      stays oracle-free" paragraph from the ask-mikk rung section and replace
      it with the same-turn consultation rule, so the digest, the oracle
      spawns, and the round for the `INSUFFICIENT` remainder form one exchange.
- [x] 2.3 [req: shared-understanding-summary] In
      `plugins/s/skills/plan/SKILL.md`, update flow step 3 and the depth-gate
      section so they no longer key off the go-ahead affirmative, and record
      that a depth path whose grill agenda is empty opens no rounds and so
      skips the shared-understanding summary and its confirmation.
- [x] 2.4 [req: investigation-findings-digest, readiness-attestation] In
      `plugins/s/skills/plan/SKILL.md`, add a short "What still stops the
      flow" list naming the only stop conditions — missing content-directory
      layout, a depth-path grill round, an `INSUFFICIENT` oracle verdict, an
      undischargeable readiness item, and a gate rejection that is a true gap —
      and state that anything not listed proceeds.

## 3. Gate-promoted hand-off

- [x] 3.1 [req: gate-promoted-handoff, emission-carries-status-header] In
      `plugins/s/skills/plan/SKILL.md`, replace step 1 of the Ending section's
      `spec_status.py set-status ready` invocation with
      `spec_gate.py <change> --root <repo-root>`, documenting exit 0 as the
      promotion plus hand-off and exit 2 as entry into the enrichment loop on
      the gate's `## Context insufficient` findings, with forcing the status
      called out as a protocol violation.

## 4. Snapshot and harness

- [x] 4.1 [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.76` to `0.6.77` so the
      cached plugin snapshot picks up the rewritten skill.
- [x] 4.2 [req: *] In `evals/run.py`, update the comment above `GOAHEAD_REPLY`
      and the `run_conversation` docstring: the plan skill's findings
      checkpoint (the go-ahead prompt) no longer fires, so the resume loop now
      answers only genuine typed decision rounds and a clean case is expected
      to reach a gradable state on the first turn.
- [x] 4.3 [req: *] Run `python3 evals/run.py --runs 2` from the repo root and
      record the per-case pass-rate; investigate any case that now fails to
      reach a lint-clean `ready` change in its first turn.
