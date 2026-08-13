# Tasks — review-finding-disposition

## 1. Reply and resolve verbs

- [x] 1.1 [req: thread-reply-verb, thread-resolution-verb] In `plugins/s/skills/review/tests/test_review_gate.py`, add failing tests over the fake-`gh` dispatcher (extend it with GraphQL `reviewThreads`/`resolveReviewThread` handling): `reply` posts an `in_reply_to` comment on the root comment and prints its URL; `resolve` resolves a gate-authored thread carrying a reply; resolves one whose PR gained a later commit; refuses (non-zero, listed as undispositioned) a single-comment thread with no later commit; never touches human-authored threads; `resolve --check` prints `unresolved=<n>`, mutates nothing, and exits zero only at zero.
- [x] 1.2 [req: thread-reply-verb, thread-resolution-verb] Implement `reply` and `resolve` (with `--check`) in `plugins/s/skills/review/scripts/review_gate.py` per the plan's thread model (GraphQL thread listing with author + comment count + creation time, REST `in_reply_to` replies, `resolveReviewThread` mutations), through the existing injectable `gh` seam. Tests from 1.1 pass.

## 2. Protection backstop

- [x] 2.1 [req: required-check-protect] In `test_review_gate.py`, add failing tests: `protect` sets `required_conversation_resolution` true alongside the context union (preserving `strict` and other fields); `--remove` clears both; both directions idempotent (no write when already in the desired state); output names contexts and the conversation-resolution state. Then extend `protect` in `review_gate.py` accordingly. Tests pass.

## 3. Skill and autopilot disposition

- [x] 3.1 [req: skill-post-flow] Extend the "Posting to a PR (the gate)" section of `plugins/s/skills/review/SKILL.md` with the disposition loop: after posting, walk every finding regardless of severity — implement (edit, commit, push) when the suggestion is correct, else `review_gate.py reply` with the concrete reason; never leave a finding with neither; finish with `review_gate.py resolve` and report status state, summary URL, and `unresolved=0`.
- [x] 3.2 [req: pipeline-stage-execution] In `plugins/s/skills/build/tests/test_autopilot.py`, add failing tests: the review grade fails on green status with `unresolved=1` and passes on green status with `unresolved=0` (inject the check through the command seam); the review-stage prompt text names the disposition loop (implement or reply, then resolve). Then update `_review_grade` and `_stage_prompt` in `plugins/s/skills/build/scripts/autopilot.py`. Tests pass.

## 4. Docs and plugin

- [x] 4.1 [req: skill-post-flow] Update `AGENTS.md`'s ship-via-PR step: the review post is followed by the disposition loop and `resolve`, and merge requires both green checks plus zero unresolved conversations (GitHub now enforces resolution); bump `plugins/s/.claude-plugin/plugin.json` one patch version.

## 5. Verification

- [x] 5.1 [req: *] Full barrier: engine + review unittest suites green; library lint clean; live drive against merged PR #54's four dangling gate threads — `resolve --check` shows the real unresolved count, disposition each thread for real (a `reply` naming this change as the deferral rationale where the finding is deferred), then `resolve` brings `unresolved=0` — and confirm `main`'s live protection now carries `required_conversation_resolution` only if the orchestrator has run the flip (do NOT run `protect` against this repo yourself; report the observed state).
