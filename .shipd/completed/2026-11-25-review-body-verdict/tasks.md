## 1. The review body

- [x] 1.1 [req: gate-review-submission-body, gate-review-event] In `plugins/s/skills/review/tests/test_review_gate.py`, add failing tests: a failing post's body has the second line ``**❌ Fix required** — 1 high, 1 low · commit `064b2ee` `` and the pointer as its third line; a passing post's second line is ``**✅ Ship it** — no findings · commit `dbc5a97` ``; a `--room-agent` post's body holds `## Findings:` and no separate verdict line; and a `pass` post with no findings on the author's own account submits one body-only `COMMENT` review whose result carries `review_event` `COMMENT`. Rewrite every existing test that asserts no review is submitted for a comment-only post with nothing anchored, and every test that asserts the pointer is the body's second line. Run the file and see the new tests fail.
- [x] 1.2 [req: gate-review-submission-body] In `plugins/s/skills/review/scripts/review_gate.py`, add `_verdict_line` and pass its result through `_post_review` per plan.md, at all three `_post_review` call sites in `post`.
- [x] 1.3 [req: gate-review-event] In `plugins/s/skills/review/scripts/review_gate.py`, remove the guard that skips a comment review when nothing anchors, per plan.md, and update the comment above it. Run 1.1's file until it passes.
- [x] 1.4 [req: gate-review-submission-body] In `plugins/s/.claude-plugin/plugin.json`, set the version one patch above the version the main branch carries at build time.
- [x] 1.5 [req: gate-review-event] In `docs/semantic-review-reference.md` (lines 90-98) and `plugins/s/skills/review/references/posting.md` (line 135), replace the statement that a `COMMENT` review is submitted only when findings anchor with the new rule: one `COMMENT` review on every post, body only when nothing anchors. In the reference doc, also name the verdict line the review body carries, with one example. Write against `plugins/s/skills/document/references/standard.md`, change no heading, and run `plugins/s/skills/document/scripts/docs_lint.py docs/semantic-review-reference.md` until it exits 0. Then run `plugins/s/skills/build/tests/test_external_loaders.py` and the review tests and keep them green.

## 2. Verify

- [x] 2.1 [req: *] Run `python3 -B -m unittest discover -s plugins/s/skills/review/tests`, `python3 -B -m unittest discover -s plugins/s/skills/room/tests` and `python3 -B -m unittest discover -s plugins/s/skills/build/tests`, and confirm each prints `OK`.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 44 | 15.7k |
| SubagentHandback | 3 | 4.9k |
| Edit | 7 | 3.8k |
| Agent | 4 | 2.8k |
| Write | 1 | 1.7k |
| Read | 4 | 671 |
| (no tool) | 0 | 580 |
| Monitor | 1 | 261 |
| ToolSearch | 1 | 184 |
| **Total** | 65 | 30.5k |
