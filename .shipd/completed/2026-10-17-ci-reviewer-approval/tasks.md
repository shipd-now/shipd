## 1. Tests first

- [x] 1.1 [req: actions-approval-setting] Create `plugins/s/skills/build/tests/test_actions_approval.py` with a recording fake runner and tests for the five scenarios (disabled read, allow body preserving `read`, no-op when enabled, unreadable never written, write that does not take). Run it and observe it fail: the module does not exist.
- [x] 1.2 [req: gate-workflow-template] In `plugins/s/skills/build/tests/test_copilot_verb.py`, add `"PR_AUTHOR": "pr-author"` as a keyword default to the env built in `GateScriptCase.gate` (near `"PR_NUMBER": "7"`), and extend the `GH_STUB` so a review POST whose payload event is in a new `reject_events` list exits 1.
- [x] 1.3 [req: gate-workflow-template] In the same file, replace `test_the_gates_own_review_is_posted_through_the_reviews_api`'s COMMENT-only assertions with ones that require `REVIEW_EVENT` in the posting step and `PR_AUTHOR` in its env, and keep the status-before-review ordering assertion.
- [x] 1.4 [req: gate-workflow-template] In `GateReviewPostTest` and `GateCliReviewerTest`, update the event assertions (`"COMMENT"` at the ship-it and fix-required cases) to `APPROVE` and `REQUEST_CHANGES`, and add tests: marker-less fail-open stays `COMMENT`; strict marker-less stays `COMMENT`; `PR_AUTHOR=github-actions[bot]` and empty `PR_AUTHOR` give `COMMENT`; rejected `APPROVE` twice ends in one body-only `COMMENT` with the not-recorded line and exit 0; the poll path still posts no review. Run the file and observe the new tests fail.

## 2. Workflow

- [x] 2.1 [req: gate-workflow-template] In `plugins/s/integrations/copilot/copilot-review-gate.yml`, add `PR_AUTHOR: ${{ github.event.pull_request.user.login }}` to the classify-and-post step's `env:` beside `PR_NUMBER`.
- [x] 2.2 [req: gate-workflow-template] In the same step, immediately before the payload builder inside `if [[ -n "$comment_file" ]]`, compute `review_event`: `COMMENT` by default; `APPROVE` when `matched_state` is `success` and `REQUEST_CHANGES` when it is `failure`, only if `PR_AUTHOR` is non-empty and not `github-actions[bot]`. Use `case`, no `${var,,}`.
- [x] 2.3 [req: gate-workflow-template] In the Python builder, read `REVIEW_EVENT` from the environment (default `COMMENT`) for the payload's `"event"`, and take a sixth argument `neutral_path`: write the plain payload (no comments) with event `COMMENT` there. Pass `REVIEW_EVENT="$review_event"` and a `review_neutral="${RUNNER_TEMP:-.}/shipd-copilot-review-neutral.json"` path in the invocation.
- [x] 2.4 [req: gate-workflow-template] Replace the POST chain: payload, then on failure the plain retry under the same event; if that fails and `review_event` is not `COMMENT`, echo a `::warning::` line saying the decision was not recorded and naming "Allow GitHub Actions to create and approve pull requests", then POST `$review_neutral`; if the event is `COMMENT` a failed retry still fails the step.
- [x] 2.5 [req: gate-workflow-template] Rewrite the comment above the review step that says the event is COMMENT, never REQUEST_CHANGES: state the event rule, that a stale block clears when the next run on the new head re-posts, and that the poll paths post no review.
- [x] 2.6 [req: gate-workflow-template] Run `python3 -m unittest plugins/s/skills/build/tests/test_copilot_verb.py` from `plugins/s/skills/build/tests` and confirm every task 1.2 to 1.4 test passes.

## 3. Setting reader and consent

- [x] 3.1 [req: actions-approval-setting] Create `plugins/s/skills/build/scripts/actions_approval.py` per the plan's interface (`gh_run`, `read_setting`, `enable`, `main`), printing `actions-approve: enabled|disabled|unknown` and exiting 0, 1, 2 as the spec says. Run task 1.1's tests and confirm they pass.
- [x] 3.2 [req: gate-actions-approval-consent] In `plugins/s/skills/gate/SKILL.md`, add one row to the step 5 table for the `allow` command with its plain-words effect, add a sentence before the table to run the script bare and show the state, add the step 6 denial hint (Settings, Actions, General, Workflow permissions), and the closing-report sentence for a setting left off.

## 4. Docs and version

- [x] 4.1 [req: ci-reviewer-docs-version] In `docs/copilot-review.md` section 4, add a short subsection "Let the CI reviewer approve" naming the setting, `actions_approval.py allow`, and what happens when it is off. In `docs/copilot-review-reference.md` "Tokens, permissions, and the session flow", state the event rule and the degradation.
- [x] 4.2 [req: ci-reviewer-docs-version] Bump `version` in `plugins/s/.claude-plugin/plugin.json` by one patch above `main`'s value and run `python3 plugins/s/skills/build/scripts/version_guard.py --base main --head HEAD`.
- [x] 4.3 [req: *] Run `python3 -m unittest discover -s plugins/s/skills/build/tests` and `python3 -m unittest discover -s plugins/s/skills/review/tests`; grep the output for `OK` and `FAILED`.
