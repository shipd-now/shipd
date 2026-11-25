# review-body-verdict
Status: verified
Planned-at: 49871f4c5dbd272fab5d90c595183252593ccf4e
Gated-hash: ba4e14114481

## Idea

Make every posted semantic review state its own verdict in the review body, and post a review on every run, so a later review never makes an earlier one look wrong.

### Motivation

A person reading a pull request cannot tell what a shipd review decided from the review itself: its body is a pointer, and the summary it points to is rewritten by the next review. On shipd pull request 396 the owner saw "Ship it" directly above a `high` finding and could not tell that they belonged to two commits.

### Details

- The review body gains a verdict line between the heading and the pointer, for example ``**❌ Fix required** — 1 high, 1 low · commit `064b2ee` ``.
- On the author's own account, or with an unreadable login, the poster now submits a `COMMENT` review on every post, body only when no finding anchors.
- `REQUEST_CHANGES` and `APPROVE` stay as they are whenever the reviewer account differs from the author's.
- A room reviewer's body stays the full summary.
- The plugin version moves one patch.

Affected capabilities: `semantic-review` (requirement `gate-review-submission-body`, modified) and `review-approvals` (requirement `gate-review-event`, modified). Impact: `plugins/s/skills/review/scripts/review_gate.py`, `plugins/s/skills/review/tests/test_review_gate.py` and `plugins/s/.claude-plugin/plugin.json`. No new dependencies.

### Non-goals

- No change to which event a review carries when the accounts differ.
- No change to the summary comment, its "Earlier reviews" fold, or the commit status.
- No change to the CI gate workflow, which posts its own review body.
- No change to inline comments, room tasks or review claims.

## Implementation

- **The verdict line.** Add `_verdict_line(review, sha, disposition)` in `review_gate.py`. The verdict words come from `_verdict_header(review["verdict"])` with its leading `## Findings: ` removed, wrapped in `**`. The counts are the text `_status_description(review, disposition)` carries after its first `: `. The commit is `sha[:7]` in backticks. The three parts join as `<verdict> — <counts> · commit <sha>`. Rejected: a second copy of the verdict words or the counting, which would drift from the summary and the status.
- **The body.** `_post_review` takes the line as a new `verdict` parameter. Without `summary`, the body is the heading, the verdict line, then the pointer, one per line. With `summary` (the `--room-agent` path), the body stays the heading, a blank line and the summary.
- **Always one review.** In `post`, drop the `if event != NEUTRAL_EVENT or anchored` guard at line 1261, so the review is submitted on every post. The retry ladder below it stays: a rejected inline review folds its findings and retries body-only with the same event. A `COMMENT` that is rejected with no inline comments is not retried again.
- **Pointer wording.** The pointer keeps its two existing sentences: with inline comments it counts them, without it reads "Semantic review posted. Full report in the summary comment."
- **The self-approval line.** `post` keeps printing `review comment-only: ...` when the login is the author's.
- **Claims.** `submitted` is now set on every successful post, so the room claim's `done` ref is created as it is for a decision review. No claim code changes.
- **Version.** `plugin.json` moves to one patch above the main branch's version at build time.

Risk: one more review notification per run on a single-account pull request. The owner accepted it (Q1), because each review then states its own outcome.

Risk: a test that asserts no review is posted for the author's clean pass now fails. Task 1.1 finds and rewrites those tests first.

## Questions and answers

### Q1: Does a review with nothing to anchor still post?
- **Question:** On the author's own account, should the poster submit a comment review that states the verdict even when no finding anchors? Options: (1) yes, every review posts its own entry; (2) no, only when findings anchor. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Yes, always post, so a failing review and the passing review after it each leave their own entry.
- **Queued:** q-review-comment-when-nothing-anchors

## Readiness attestation

### Problem and motivation

A posted review does not state its verdict, and the summary it points to is overwritten by the next review.

Evidence:

- `plugins/s/skills/review/scripts/review_gate.py:1101-1105` builds the body from the heading and a pointer only.
- `plugins/s/skills/review/scripts/review_gate.py:1261` skips the review when the event is a comment and nothing anchors.
- Capability `semantic-review`, requirement `gate-review-submission-body`, pins the pointer body.

### Scope and non-goals

The change edits the body text and the one skip rule; events, summary and status stay.

Evidence:

- In scope: `review_gate.py` and its test file.
- Out of scope: `review_gate.py:1071-1078` (`_review_event`) takes no edit, and capability `copilot-review-skill` covers the CI gate's own body.

### Affected capabilities and files

Two capabilities and three files are affected, because the body and the skip rule each sit under their own requirement in one script.

Evidence:

- `semantic-review`: `gate-review-submission-body` (base e51e824e4f5f), hash from `spec_status.py base-hash`.
- `review-approvals`: `gate-review-event` (base 3b1454b236e9).
- Files: `review_gate.py:409-412` (`_verdict_header`), `review_gate.py:815-831` (`_status_description`), `review_gate.py:1081-1110` (`_post_review`).
- Runnable premise: `python3 -B -m unittest discover -s plugins/s/skills/review/tests -p test_review_gate.py` → 257 tests, OK.

### No open task-shaping decision

Every task-shaping decision is settled; none remain.

Evidence:

- Posting a review on every run: settled by the user, Q1.
- The line's wording and its reuse of the header and status text, the unchanged room-reviewer body, and the unchanged events: settled by investigation.
