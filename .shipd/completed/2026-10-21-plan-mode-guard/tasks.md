## 1. Contract test

- [x] 1.1 [req: harness-plan-mode-guard] Add
      `plugins/s/skills/build/tests/test_plan_mode_guard_contract.py` with the
      constants and six tests listed in `plan.md`'s Implementation "Test"
      bullet, laid out like `test_question_brief_contract.py`. Run
      `python3 -B -m unittest plugins/s/skills/build/tests/test_plan_mode_guard_contract.py`
      and observe it fail.

## 2. Reference and clauses

- [x] 2.1 [req: harness-plan-mode-guard] Copy `artefacts/harness-plan-mode.md`
      byte for byte to
      `plugins/s/skills/document/references/harness-plan-mode.md`. Run
      `python3 -B plugins/s/skills/document/scripts/docs_lint.py` on it and
      confirm exit 0.
- [x] 2.2 [req: harness-plan-mode-guard] Insert the inline `## Harness plan
      mode` block from `plan.md`'s Implementation, verbatim, above the first
      level-2 heading outside a code fence in each SKILL.md under
      `plugins/s/skills/` except `duck`, `drift`, `explain`, `memory`, and
      `review` (25 files).
- [x] 2.3 [req: harness-plan-mode-guard] Insert the `- **Harness plan mode**`
      bullet from `plan.md`'s Implementation, verbatim, into
      `plugins/s/skills/plan/SKILL.md` directly above "Anything not on this
      list proceeds without asking."
- [x] 2.4 [req: harness-plan-mode-guard] In
      `plugins/s/.claude-plugin/plugin.json`, change `"version": "0.6.340"` to
      `"version": "0.6.341"` (AGENTS.md: every `plugins/s/` change bumps it).

## 3. Verify

- [x] 3.1 [req: *] Run
      `python3 -B -m unittest plugins/s/skills/build/tests/test_plan_mode_guard_contract.py`
      and confirm `OK`, then run the full build test suite and confirm it
      reports `OK` (grep the output for `OK`/`FAILED`).
