## 1. Test harness

- [x] 1.1 [req: gate-resolves-superseded-threads] In `plugins/s/skills/build/tests/test_copilot_verb.py`, extend `GH_STUB` with the `graphql` branch, and `GateScriptCase.gate()` with the `threads`, `threads_fail`, `resolve_fail`, and `review_model` parameters, the `$GH_GRAPHQL`, `$GH_RESOLVED`, and `$GH_ORDER` logs, and their cleanup, exactly as plan.md's Implementation "Tests" bullet describes. Run the file and confirm every existing test still passes.

## 2. Superseded threads

- [x] 2.1 [req: gate-resolves-superseded-threads] In `plugins/s/skills/build/tests/test_copilot_verb.py`, add `GateThreadResolveTest(GateScriptCase)` covering the four scenarios of `gate-resolves-superseded-threads`: fix-required and ship-it each resolve an earlier-commit gate thread (one per login spelling) before the review POST; another author's thread, a resolved thread, and a head-commit thread are not resolved; a marker-less review, an ungrounded review, and the poll path make no graphql call; a failed query and a failed resolve each print `::warning::`, still post the status and the review, and exit 0. Run it and confirm it fails.
- [x] 2.2 [req: gate-resolves-superseded-threads] In `plugins/s/integrations/copilot/copilot-review-gate.yml`, add the thread query, selection heredoc, and resolve loop to the posting step as plan.md's Implementation describes, with a comment block explaining why. Run the test file and confirm it passes.

## 3. Review model

- [x] 3.1 [req: gate-review-model] In `plugins/s/skills/build/tests/test_copilot_verb.py`, add `GateReviewModelTest(GateScriptCase)` for the set and unset scenarios (CLI arguments and the footer line directly below the stat line, and no model line on an ungrounded review), and in `GateWorkflowTemplateTest` a test that the CLI step and the posting step each carry `SHIPD_REVIEW_MODEL: ${{ vars.SHIPD_REVIEW_MODEL }}`. Run them and confirm they fail.
- [x] 3.2 [req: gate-review-model] In `plugins/s/integrations/copilot/copilot-review-gate.yml`, bind the variable in both steps, build `model_args` in the CLI step, and add `model_line()` to the payload builder, as plan.md's Implementation describes. Run `plugins/s/skills/build/tests/test_copilot_verb.py` and `plugins/s/skills/review/tests/test_skill_references.py` and confirm both pass.

## 4. Contract, docs, and version

- [x] 4.1 [req: gate-review-model] In `plugins/s/integrations/copilot/SKILL.md`, update the stat-line sentence and the "No repository-side model selection" bullet as plan.md's Implementation "Contract" bullet says.
- [x] 4.2 [req: gate-resolves-superseded-threads, gate-review-model] In `docs/copilot-review-reference.md`, describe thread resolution, the `SHIPD_REVIEW_MODEL` variable, and the footer's model line, and narrow the model limit to the poll fallback, staying at or under 250 lines. Run `plugins/s/skills/document/scripts/docs_lint.py docs/copilot-review-reference.md` and confirm it exits 0.
- [x] 4.3 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` by one patch. Run every unittest suite `.github/workflows/ci.yml` runs plus `spec_lint.py`, and confirm each reports OK.
