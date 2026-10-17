## 1. Tests first

- [x] 1.1 [req: gate-review-event] In `plugins/s/skills/review/tests/test_review_gate.py`, extend `FakeGh` with a `pr_author` constructor argument (default `"pr-author"`) returned as `"author": {"login": ...}` in the `pr view` answer, and make `/reviews` return 422 for event `APPROVE`/`REQUEST_CHANGES` when a new `reject_decisions` count is above zero.
- [x] 1.2 [req: gate-review-event] Replace `ReviewEventTest` with tests for the scenarios: clean pass approves with no comments, failing verdict requests changes with its inline comment, `high-only` over mediums approves, author equal to login (any case) submits no decision and prints one line, unreadable login or author falls back to `COMMENT`, retry keeps the event, double rejection ends in a body-only `COMMENT`. Run it and observe it fail.
- [x] 1.3 [req: gate-review-event] In the same file, change `test_no_findings_posts_no_review` and the `"COMMENT"` assertions in `PostTest` to the new events (acting login `mikkel`, author `pr-author`); run the suite and fix any other test that assumed no review on a clean pass.

## 2. Poster

- [x] 2.1 [req: gate-review-event] In `plugins/s/skills/review/scripts/review_gate.py`, replace `REVIEW_EVENT` and its comment with `DECISION_EVENTS = {"success": "APPROVE", "failure": "REQUEST_CHANGES"}` and `NEUTRAL_EVENT = "COMMENT"`, and a comment stating the reversal and why the status-keyed event cannot strand a block.
- [x] 2.2 [req: gate-review-event] Add `_acting_login(gh)` (the existing `gh api user` read, returning `""` on failure) and `_pr_author(gh, pr)` (`gh pr view <pr> --json author`, returning `""` on failure), and `_review_event(state, login, author)` returning `NEUTRAL_EVENT` when either is empty or they match case-insensitively, else `DECISION_EVENTS[state]`.
- [x] 2.3 [req: gate-review-event] Change `_post_review` to take `event` and `login` parameters instead of reading the login itself and using `REVIEW_EVENT`.
- [x] 2.4 [req: gate-review-event] In `post`, read the login once, compute the event, and replace the `if anchored:` block: for a decision event always submit; for `COMMENT` submit only when `anchored`. On rejection fold findings and retry with no inline and the same event; if that fails and the event is a decision, submit a body-only `COMMENT` and print the not-recorded line. Print the self-approval line when the event is neutral because the logins match. Add `review_event` to the result dict.
- [x] 2.5 [req: gate-review-event] Run the review suite and confirm every task 1.x test passes.

## 3. Specs, docs, version

- [x] 3.1 [req: gate-approvals-docs-version] In `plugins/s/skills/review/references/posting.md` step 5, add two sentences: the review event follows the status (`APPROVE` on success, `REQUEST_CHANGES` on failure) and an acting login equal to the PR author submits a `COMMENT` only.
- [x] 3.2 [req: gate-approvals-docs-version] In `docs/semantic-review-reference.md`, add a short section "The review event" with the event table, the author rule, and the rejection fallback.
- [x] 3.3 [req: gate-approvals-docs-version] Bump `version` in `plugins/s/.claude-plugin/plugin.json` by one patch above `main`'s value and run `version_guard.py --base main --head HEAD`.
- [x] 3.4 [req: *] Run `python3 -m unittest discover -s plugins/s/skills/review/tests` and `python3 -m unittest discover -s plugins/s/skills/build/tests`; confirm both report `OK`. Do not edit `copilot-review-gate.yml` or `test_copilot_verb.py` (the `ci-reviewer-approval` member owns them).
