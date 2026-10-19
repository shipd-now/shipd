## 1. Test first

- [x] 1.1 [req: gate-review-event-concurrency] In `plugins/s/skills/build/tests/test_copilot_verb.py`, beside `test_one_concurrency_group_per_pull_request_cancels_superseded_runs`, add `test_other_reviewers_review_events_get_their_own_group`. It reads the single `group:` line of the `concurrency` block and asserts it contains "github.event_name == 'pull_request_review'", "copilot-pull-request-reviewer[bot]", "github.event.review.id", and "-review-". Run it and confirm it fails.

## 2. Template

- [x] 2.1 [req: gate-review-event-concurrency] In `plugins/s/integrations/copilot/copilot-review-gate.yml`, replace the `group:` line with the expression given in plan.md's Implementation, and add the sentence about other reviewers to the comment above `concurrency:`. Run the test file and confirm it passes.

## 3. Docs and version

- [x] 3.1 [req: gate-review-event-concurrency] In `docs/copilot-review-reference.md`, after the "A timeout invents nothing." bullet, add a bullet "**Other reviewers never cancel the gate.**" saying a review from anyone but Copilot runs in its own concurrency group, so a reviewer agent approving first leaves the running review intact.
- [x] 3.2 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version by one patch. Run the full plugin test suite and the repo validation, and confirm both pass.
