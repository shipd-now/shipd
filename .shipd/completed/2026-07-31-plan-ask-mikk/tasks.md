# Tasks

## 1. The ask-mikk rung in the plan skill

- [x] 1.1 [req: oracle-consultation, oracle-resolution-visibility] In
      `plugins/s/skills/plan/SKILL.md`, add a new section
      `## The ask-mikk rung — consult the oracle before the user` between
      "The depth gate" and "The fast-path question contract" stating: when
      un-inferrable task-shaping decisions remain and a user question round
      would otherwise open (fast-path batched round, depth-path round, or
      enrichment's true-gap round), shape each remaining decision into a
      compact question — the decision, its concrete options, and the
      recommended default the skill already forms — and spawn one `s:oracle`
      per decision, in parallel, via the Agent tool with
      `subagent_type: s:oracle`, passing the compact question, the repo's
      absolute root, and the status CLI path
      `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py`; branch on
      the verdict's first non-blank line (`ANSWER` → fold the decision in as
      resolved, never ask the user; `INSUFFICIENT` → the decision enters the
      user round unchanged, already queued by the oracle; spawn failure or any
      other first line → treat as `INSUFFICIENT`, never block planning);
      report every oracle-settled decision with its position and `Cited:`
      source(s) in the context brief, or in visible status text before
      proceeding when no round remains; a typed user override always
      supersedes the oracle; and the investigation turn stays oracle-free —
      the digest's OPEN QUESTIONS reach the rung only in the post-gate
      rounds.
- [x] 1.2 [req: oracle-consultation] Wire the rung into
      `plugins/s/skills/plan/SKILL.md` with one-line pointers: in Flow
      step 4, before batching questions, consult the rung and ask only the
      `INSUFFICIENT` remainder; in the opening of "The fast-path question
      contract", note the rung precedes the round; in enrichment step 3
      ("Put only the true gaps to the user"), note true gaps go through the
      rung first and only `INSUFFICIENT` gaps reach the typed round.
- [x] 1.3 [req: oracle-consultation] In
      `plugins/s/skills/plan/references/readiness.md`, extend the
      "Any item unmet → investigate or ask" bullet of "How to use the gate"
      to the three-rung ladder: prefer investigation; then put a genuinely
      un-inferrable gap to the ask-mikk oracle (per SKILL.md's ask-mikk-rung
      section); only what comes back `INSUFFICIENT` goes to the user.
- [x] 1.4 [req: oracle-consultation] In
      `plugins/s/skills/plan/references/dialogue.md`, extend "The
      fact/decision test" with a third step: decisions that survive the test
      are routed through the ask-mikk rung (per SKILL.md's ask-mikk-rung
      section) before any round, and only `INSUFFICIENT` decisions enter the
      agenda's grouped rounds — oracle-settled ones are reported in the next
      round's context brief (or in the shared-understanding summary when no
      round remains) with their citations.

## 2. Version and verification

- [x] 2.1 [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` to the next free patch above
      the version currently on the remote main branch (0.6.10 as of
      enrichment — fetch and re-check right before editing; other changes
      merge concurrently).
- [x] 2.2 [req: *] Cross-check the three edited prose files against the
      delta: grep `plugins/s/skills/plan/SKILL.md`,
      `plugins/s/skills/plan/references/readiness.md`, and
      `plugins/s/skills/plan/references/dialogue.md` for the
      `s:oracle` spawn shape, the `ANSWER`/`INSUFFICIENT` branch, the
      treat-as-`INSUFFICIENT` degradation, the cited-visibility rule, and the
      oracle-free investigation turn; fix any drift so all statements agree
      with the delta spec.
- [x] 2.3 [req: *] Run the local eval per the repo rule for SKILL.md changes:
      from the repo root, `python3 evals/run.py --case plan-csv-export` (the
      fixture has no workspace, exercising the rung's graceful
      no-workspace degradation); the case must pass before the change is
      declared done.
