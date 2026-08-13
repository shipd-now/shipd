# semantic-review-gate
Status: verified
Epic: autonomous-delivery

## Idea

The semantic review engine (`semdiff` + `/s:review`, the
`semantic-review-engine` member) produces a verdict, but that verdict lives
and dies inside the session that ran it: nothing reaches the PR, GitHub knows
nothing about it, and auto-merge waits only on `ci`. The autopilot likewise
skips its `review` pipeline stage as "not yet automated". The epic requires
every PR to be gated by ci **plus** the semantic review — a CodeRabbit-style
summary and inline comments on the PR, and a required status check that
auto-merge must see green.

This change wires the verdict to GitHub:

- A new mechanical poster, `plugins/s/skills/review/scripts/review_gate.py`:
  `post` consumes the `/s:review --json` object and publishes it to a PR
  (upserted summary comment, anchor-validated inline comments, a
  `semantic-review` commit status on the head SHA); `protect` adds/removes
  `semantic-review` in the default branch's required status check contexts.
- `/s:review` gains an explicit post-to-PR flow that emits the JSON and
  invokes the poster — only on explicit request, never as a side effect.
- The autopilot's `review` stage becomes a driven stage: a headless
  review-and-post session graded on a green `semantic-review` status.
- Bootstrap on this repo: post the review on this change's own PR, then flip
  branch protection so both contexts are required; `AGENTS.md` documents the
  new ship flow; plugin version bump.

### Non-goals

- No review runs in CI — model spend stays out of the `ci` workflow; the
  review runs in local/driven sessions and only its result reaches GitHub.
- No committable `suggestion` blocks in inline comments — comments carry the
  finding's what/why/fix as text.
- No Checks API / GitHub App — plain commit statuses via the user's `gh`
  token.
- No auto-close or auto-merge-cancel on a red verdict: the PR stays open with
  the failing required check blocking it; the autopilot parks the member as
  `needs-human`.
- No push-triggered re-review automation: a new commit invalidates the status
  naturally (statuses bind to SHAs) and a human or driven session re-runs the
  review.

Affected capabilities: `semantic-review` (modified — poster, protect verb,
skill post flow, tests), `epic-autopilot` (modified — `review` joins the
driven stages). Impact: new `plugins/s/skills/review/scripts/review_gate.py`
and `plugins/s/skills/review/tests/test_review_gate.py`;
`plugins/s/skills/review/SKILL.md`;
`plugins/s/skills/build/scripts/autopilot.py` and
`plugins/s/skills/build/tests/test_autopilot.py`; `AGENTS.md`;
`plugins/s/.claude-plugin/plugin.json` (0.5.0 → 0.5.1); one-time branch
protection change on this repo. No new dependencies; no `ci.yml` change (it
already discovers `plugins/s/skills/review/tests`).

## Implementation

- **Judgement in the skill, posting mechanical.** `review_gate.py` is
  stdlib-only Python 3 with no analysis: it reads the review JSON (file path
  or stdin), shapes GitHub payloads, and shells out to `gh` for every network
  call. Rejected: ad-hoc `gh` calls from skill prose — untestable and
  unrepeatable; the semdiff split (dumb tool, judging skill) is the
  established pattern.
- **Commit statuses, not check runs.** The Checks API requires a GitHub App;
  `POST /repos/{o}/{r}/statuses/{sha}` works with the user token and required
  status check contexts match on the context string (`semantic-review`) —
  exactly how `ci` gates today. State `success` iff verdict `pass`, else
  `failure`; description carries the verdict and finding counts; `target_url`
  points at the summary comment. Head SHA read via
  `gh pr view --json headRefOid`.
- **Idempotent summary upsert.** The summary comment carries a hidden marker
  (`<!-- am-semantic-review -->`); `post` finds a marker comment and edits it
  in place, else creates it — re-runs never stack summaries. Rendering
  mirrors the skill's human report (verdict header, effort, `# | rating |
  details` table with the two sanctioned emoji sites; nothing else).
- **Anchor-validated inline comments.** `post` reads
  `gh api repos/{o}/{r}/pulls/{n}/files` patches, computes the RIGHT-side
  commentable lines per path, and posts one PR review (event `COMMENT`) with
  inline comments only for findings whose `location` (`path:LINE`) anchors;
  unanchorable findings fold into an "Additional findings" section of the
  summary. On a 422 from the review POST, retry once with no inline comments
  and fold everything into the summary. Rejected: posting blind and letting
  the API reject the whole review.
- **`protect` preserves existing contexts.** It GETs current branch
  protection, unions/removes `semantic-review` in
  `required_status_checks.contexts`, and PATCHes only that object —
  idempotent, never touching other protection settings. `--remove` undoes it.
  The command targets the repo's default branch.
- **Autopilot: `review` joins `DRIVEN_STAGES`** (drop `NOT_AUTOMATED_STAGES`).
  The stage prompt tells the driven session to run `/s:review` on
  `change/<member>` vs `main`, post via `review_gate.py post`, and — if the
  verdict is `changes-requested` — fix the findings, push, and re-review
  until green. Grade: the combined status for the PR's head SHA
  (`gh api repos/{o}/{r}/commits/{sha}/status`) shows context
  `semantic-review` with state `success`. Three-strike re-drive and
  `needs-human` parking are inherited from the existing stage machinery
  unchanged; a parked member's PR stays open with findings posted.
- **Bootstrap ordering.** This change's own PR gets its review posted
  *before* `protect` flips the requirement, so the flip never strands the PR
  that ships it. Once flipped, every open PR needs a posted review before
  auto-merge — `AGENTS.md`'s ship section documents the extra step.
- **Tests with an injectable `gh` seam.** `test_review_gate.py` injects a
  fake command runner (no network): marker upsert vs create, anchor
  computation from patch text, status payload/state mapping, 422 fallback,
  protect union/remove/idempotency. `test_autopilot.py` gains review-stage
  cases via the existing injectable `session_fn`/`command_fn` seams.

Risks: flipping protection blocks any other open PR until it gets a review —
accepted and documented; `protect` needs admin scope on the repo, which the
owner's `gh` auth has; statuses API is stable, so no difftastic-style shape
risk.
