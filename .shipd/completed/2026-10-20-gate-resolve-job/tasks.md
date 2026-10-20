## 1. Tests

- [x] 1.1 [req: gate-resolves-superseded-threads] In `plugins/s/skills/build/tests/test_copilot_verb.py`, make "gate_job" return the "gate" job by name, add "resolve_script(text)", and extend "GateScriptCase" so "gate()" runs the resolve script after the gate script under the conditions plan.md's Implementation "Tests" bullet names. Update "GateThreadResolveTest" (review before resolve, a refused-decision case, a plain-retry case) and "GateWorkflowTemplateTest" (two jobs, the new job's needs, guard, permissions, outputs, no "secrets." and no checkout). Run the file and confirm the new assertions fail.

## 2. Workflow

- [x] 2.1 [req: gate-resolves-superseded-threads] In `plugins/s/integrations/copilot/copilot-review-gate.yml`, give the posting step "id: verdict", delete its resolution block, set "decision_posted" and write the two outputs as plan.md's Implementation describes, add the "gate" job "outputs:", and add the "resolve-threads" job with the moved script and a comment block explaining the token split and the ordering. Update the header comment's trust-boundary list to name the new job. Run `python3 -B -m unittest plugins/s/skills/build/tests/test_copilot_verb.py` and confirm it passes.

## 3. Docs and version

- [x] 3.1 [req: gate-resolves-superseded-threads] In `docs/copilot-review-reference.md`, update the thread bullet and the "Tokens, permissions, and the session flow" paragraph as plan.md's Implementation "Docs" bullet says. Run `python3 plugins/s/skills/document/scripts/docs_lint.py docs/copilot-review-reference.md` and confirm it exits 0.
- [x] 3.2 [req: *] Set `plugins/s/.claude-plugin/plugin.json` version to 0.6.339. Run every unittest suite `.github/workflows/ci.yml` runs plus `spec_lint.py`, and confirm each reports OK.
