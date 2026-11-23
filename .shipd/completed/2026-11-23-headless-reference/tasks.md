# headless-reference — tasks

## 1. The reference and the manifest

- [x] 1.1 [req: headless-contract-reference] Create
      `plugins/s/skills/ask/references/headless.md` with the four `##` parts
      and run `docs_lint.py` on it.
- [x] 1.2 [req: external-loader-manifest] Add
      `plugins/s/skills/build/tests/test_external_loaders.py` and
      `plugins/s/external-loaders.json`; document the manifest in `AGENTS.md`.

## 2. The gate

- [x] 2.1 [req: assumption-entry-check] In
      `plugins/s/skills/build/tests/test_spec_gate.py`, add tests for a
      well-formed, verdict-less, empty-answer, prefix-only, wrapped-answer,
      and `PLANNER` entry; observe them fail.
- [x] 2.2 [req: assumption-entry-check] In
      `plugins/s/skills/build/scripts/spec_gate.py`, add the assumption-entry
      check and confirm the tests pass.
- [x] 2.3 [req: ledger-question-placeholder-exemption] Add placeholder tests for a marker
      in a ledger question (passes) and in an answer or elsewhere (fails),
      then skip the `**Question:**` field in the placeholder check.

## 3. The driver and skills

- [x] 3.1 [req: oracle-aware-driven-sessions, oracle-gate-enrichment]
      In `plugins/s/skills/build/scripts/autopilot.py`, add `HEADLESS_NOTE`
      and use it in the canned reply and the build, enrichment, and re-plan
      prompts; update `test_autopilot.py`.
- [x] 3.2 [req: in-session-unattended-prompts] In
      `plugins/s/skills/autopilot/SKILL.md`, point the plan, build, and re-plan
      instructions at `headless.md`.
- [x] 3.3 [req: headless-contract-reference] Point `plugins/s/skills/epic-grill/SKILL.md` and
      `plugins/s/harness/bodies/epic-grill.md` at `headless.md` with the `PLANNER`
      override; name `ASSUMPTION` in `plugins/s/skills/plan/SKILL.md` and
      `plugins/s/skills/plan/references/emission.md`.

## 4. The eval grader

- [x] 4.1 [req: oracle-default-grading] In `evals/run.py`, require
      `ASSUMPTION`; update `evals/tests/test_runner.py` and `AGENTS.md`'s
      `## Evals` section. Run no model-calling eval.

## 5. Ship

- [x] 5.1 [req: headless-contract-reference] Bump
      `plugins/s/.claude-plugin/plugin.json` and run every CI unit suite, the
      spec lint, and the docs lint.
