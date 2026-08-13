# review-finding-disposition
Status: verified

## Idea

The review gate posts confident, severity-rated findings — and then nothing
happens to them. A `pass` verdict with low findings merges with every
conversation dangling (PR #54 merged carrying four open threads), and the
autopilot's prompt only mandates fixes on `changes-requested`. Posted
findings are advice nobody is required to read; the user expects sensible
suggestions implemented before merge, disagreements answered on the thread,
and no unresolved conversations at merge time.

This change closes the loop:

- `review_gate.py` grows `reply` (post a rationale onto a finding thread)
  and `resolve` (resolve gate-authored threads — refusing any thread that
  carries neither a later commit nor a reply as disposition evidence),
  plus `resolve --check` printing the unresolved count for grades.
- `protect` additionally flips `required_conversation_resolution` on the
  default branch — GitHub itself blocks merge while threads are open.
- The review skill's post flow gains the disposition loop: after posting,
  every finding (low included) is either implemented (edit, commit, push)
  or answered with a reasoned reply; then threads are resolved and the
  skill reports unresolved=0.
- The autopilot's review stage prompt carries the disposition loop and its
  grade becomes: `semantic-review` status green **and** zero unresolved
  gate threads.

### Non-goals

- No change to the finding rubric itself — evidence-anchored,
  severity-rated findings already gate what is posted; this change governs
  what happens after.
- No resolving of human-authored threads — only threads the gate created;
  humans resolve their own conversations.
- No auto-implementation policy in the engine — deciding implement vs
  push-back is the reviewing session's judgment, per the skill text; the
  engine only enforces that one of the two happened.

Affected capabilities: `semantic-review` (modified), `epic-autopilot`
(modified). Impact: `plugins/s/skills/review/scripts/review_gate.py` and
its tests, `plugins/s/skills/review/SKILL.md`,
`plugins/s/skills/build/scripts/autopilot.py` and its tests, `AGENTS.md`
ship step, plugin version bump.

## Implementation

- **Thread model via GraphQL.** `resolve` lists the PR's review threads
  (GraphQL `reviewThreads` with `isResolved`, comment author logins, and
  comment database ids), selects those whose root comment the gate
  authored, and calls `resolveReviewThread` per thread. The evidence rule:
  a thread resolves only when it has ≥2 comments (a reply exists) or the
  PR gained a commit after the thread's creation time — else it is listed
  as `undispositioned` and the verb exits non-zero. `--check` prints
  `unresolved=<n>` and exits 0/non-zero without mutating. Rejected:
  resolving unconditionally — that would let the loop be skipped silently.
- **`reply`** posts via REST `pulls/comments` `in_reply_to` on the thread's
  root comment id — the same injectable `gh` runner seam as `post`.
- **`protect`** gains `required_conversation_resolution: true` in the same
  PATCH (and `--remove` clears it), preserving all other protection
  fields; idempotent like the contexts flip.
- **Disposition in the skill, enforcement in the engine.** The SKILL.md
  post-flow section instructs: walk findings newest-post first; implement
  when the suggestion is correct (commit + push, which also refreshes the
  review); otherwise `reply` with the concrete reason; finish with
  `resolve` and report its output. The engine never decides — it verifies
  disposition evidence exists.
- **Autopilot grade**: `_review_grade` additionally runs
  `review_gate.py resolve --check` and passes only on green status plus
  `unresolved=0`; the stage prompt names the disposition loop explicitly.
- **Live verification target**: PR #54's four dangling gate threads get
  dispositioned for real in the barrier task — replies where the finding
  is deferred (naming this change or a follow-up), resolution after.

Risk: GraphQL thread queries are the one new API surface — guarded by the
injectable seam (unit tests never hit the network) and the live PR #54
drive; pagination beyond 100 threads is out of scope and documented (the
same known cap as the poster's comment listing).
