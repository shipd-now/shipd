# gate-approves
Status: verified
Epic: merge-rules
Planned-at: d77b207225bc087d35f8ad6aa8de52c77cab6cee
Gated-hash: 6851e47d4471

## Idea

The review poster submits `APPROVE` or `REQUEST_CHANGES` instead of `COMMENT`, and never as the PR's author.

### Motivation

GitHub's required-approval rule counts only approval reviews, so a reviewer agent whose poster submits `COMMENT` cannot satisfy the merge rules the epic sets. The poster must also avoid self-approval, which GitHub rejects with 422.

### Details

- Event follows the `semantic-review` status: `success` gives `APPROVE`, `failure` gives `REQUEST_CHANGES`.
- One decision review per post, body-only when no finding anchors.
- Acting login equal to the PR author (or any unreadable login) gives a `COMMENT` review only when findings anchor, with one explanatory output line.
- Rejection path: retry without inline comments, then a body-only `COMMENT`.

Affected capabilities: `semantic-review` (modified), `review-approvals` (new). Impact: `review_gate.py`, its tests, `posting.md`, `docs/semantic-review-reference.md`, `plugin.json`.

### Non-goals

- No change to the installed workflow's review payload (member `ci-reviewer-approval`).
- No per-agent account selection or room-skill refusal (member `agent-identity`).
- No change to findings, severities, the summary, or the status.

## Implementation

- Constants: `REVIEW_EVENT` is removed; `DECISION_EVENTS` and `NEUTRAL_EVENT` replace it. Rejected: keeping `REVIEW_EVENT` for the neutral case, since a single name would hide that two events now exist.
- Author detection uses the existing `gh` seam: `gh api user` (already read for the heading, now read once in `post` and passed into `_post_review`) against `gh pr view <pr> --json author`. Rejected: extending `_resolve_pr`'s tuple, which six callers unpack.
- Self-approval is prevented before the call, not by catching 422. Rejected: attempt and fall back, which contradicts the epic's rule that it is never attempted.
- A clean pass now posts a body-only review, because required approvals need a review object. A `COMMENT` outcome keeps today's rule of posting only when something anchors.
- Interface: `_review_event(state, login, author) -> str`; `post` result gains `review_event` (submitted event or `None`).
- Risk: a same-account reviewer and author (today's autopilot) now yields only `COMMENT`; that is intended until `agent-identity` lands. A stale `REQUEST_CHANGES` clears when the same account re-posts `APPROVE` on the new head.
- Spec: `semantic-review` requirements `gate-poster` and `gate-review-submission-body` are modified; `gate-review-event` is added in a new capability to keep each delta lean.

## Questions and answers

### Q1: What does the review event derive from?
- **Question:** Derive the event from the status state the poster sets, or from the raw verdict? Options: (1) status state, success to `APPROVE` and failure to `REQUEST_CHANGES`; (2) raw verdict, which under `high-only` or `none` could strand a `REQUEST_CHANGES`. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** (1) status state, so the approval and the status never disagree under any disposition scope.
- **Queued:** q-gate-review-event-follows-status-state
- **Relied on by:** ci-reviewer-approval

### Q2: What is submitted for the author or an unreadable login?
- **Question:** When the acting login equals the PR author, or a login cannot be read, what does the poster submit? Options: (1) a `COMMENT` review only when findings anchor, plus one output line; (2) skip the review entirely; (3) attempt the approval and fall back on 422. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** (1) a `COMMENT` review only when findings anchor, plus one explanatory line; an unreadable login is treated the same way.
- **Queued:** q-review-poster-self-author-event
- **Relied on by:** ci-reviewer-approval, agent-identity

### Q3: What happens when the decision review is rejected twice?
- **Question:** If the retry without inline comments is also rejected, what does the poster do? Options: (1) submit a body-only `COMMENT` and print that the decision was not recorded; (2) ignore the rejection as today; (3) exit non-zero. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** (1) a last body-only `COMMENT` review, with an output line saying the decision was not recorded.
- **Queued:** q-review-gate-retry-rejected-decision
- **Relied on by:** ci-reviewer-approval

## Readiness attestation

### Problem and motivation

Required approvals cannot be met by `COMMENT` reviews, and self-approval is rejected by GitHub.

Evidence:

- `plugins/s/skills/review/scripts/review_gate.py:61-66` pins `REVIEW_EVENT = "COMMENT"`.
- Epic `merge-rules`, Decision "Approvals, not comments".

### Scope and non-goals

The poster, its tests, caller docs and version change; the workflow payload and identity work stay out.

Evidence:

- In scope: `review_gate.py:869-1000` (`_post_review`, `post`), `test_review_gate.py:799-838`.
- Out of scope: `copilot-review-gate.yml:936`, owned by `ci-reviewer-approval`.

### Affected capabilities and files

One capability is modified and one added; five files change.

Evidence:

- Capability `semantic-review`: requirements `gate-poster` (base cef9c0c5d9b0) and `gate-review-submission-body` (base 1b9595a0aa29).
- Files: `review_gate.py`, `test_review_gate.py`, `posting.md`, `docs/semantic-review-reference.md`, `plugin.json`.
- Runnable premise: `gh pr view 336 --json author` returned exit 0 and `{"author":{"login":"mikkel-bergmann",...}}`.
- Runnable premise: `python3 -m unittest discover -s plugins/s/skills/review/tests` returned `Ran 291 tests ... OK`.

### No open task-shaping decision

Every decision is settled; three were defaulted by the planner after the oracle found no position.

Evidence:

- Event basis: planner default, Q1.
- Author and unreadable login handling: planner default, Q2.
- Double-rejection fallback: planner default, Q3.
