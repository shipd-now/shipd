# review-branding
Status: verified
Planned-at: aa3b0a8f7d00cbe7be74eabdf743a958aa11afda
Gated-hash: 746ef0df37c2

## Idea

Make both pull-request reviewers post the ☕ shipd review layout. The CI gate's review body will open with the brand line. The room reviewer will review through `/s:review` and `review_gate.py post`, with the full branded summary in its approve or request-changes review.

### Motivation

On https://github.com/mikkel-bergmann/unkannybanny/pull/37 the user expected the shipd header and full details from both reviewers. Instead, the CI gate posted an unbranded body and the room reviewer `reviewer-b` posted a one-line freeform approval, so its findings never reached the PR as anchored threads.

### Details

- CI gate: the posting step of `plugins/s/integrations/copilot/copilot-review-gate.yml` puts `**☕ shipd** semantic review` and a blank line at the top of every body it posts, above the ungrounded notice. It never adds the line twice.
- Poster: `review_gate.py post` gains `--status {set,off,auto}`, `--room-agent`, and `--room-to`.
- Room reviewer: `/s:room`'s `reviewer` runs `shipd room whoami`, then `/s:review <pr-url> status=auto room-agent=<to> room-to=<last_agent>`, then closes the request task.
- Room runner: no code change. A test pins that `_ci_reviews` reads a branded CI body.

Affected capabilities: `copilot-review-skill` (two requirements modified), plus new requirements in `semantic-review`, `shipd-room`, and `room-runner`.

### Non-goals

- No change to `room_run.py` code or its turn prompt. No change to `room.py`, whose run import the sibling change `room-bundle-run` edits.
- No change to the Copilot skill template: the gate adds the brand.
- No per-agent summary marker.

## Implementation

### CI gate brand line

- Add the brand in the posting step's payload heredoc (the one defining `SEV_DOT`). The new `brand(body)` prepends `BRAND + "\n\n"` unless the body's first non-blank line already equals `BRAND`, and its result becomes `payload["body"]`. Rejected: adding the brand in the report cut, because the cut keeps text from the last `## Findings` header and would drop a line placed above it.
- Old and new bodies both parse. The `## Findings:` cut runs on raw CLI output before branding. The verdict scan, the fast-pass scan, and `fold` all walk backwards. `resolve-threads` matches the inline marker, not the body. `earlier_reviews` and `room_run._fix_required` read their own lines. A parity test pins `BRAND` to `review_gate.BRAND_LINE`.

### Poster flags (`review_gate.py`)

- `--status set` is today's behaviour.
- `--status off` sets no status, makes no fast-pass read or merge call, and renders no fast-pass line. The review event still follows `status_state`, so the review still approves or requests changes.
- `--status auto` reads `repos/<repo>/contents/.github/workflows/copilot-review-gate.yml?ref=<baseRefOid>` once. Exit 0 means `off`; `HTTP 404` in stderr means `set`; any other failure means `off` plus a warning. A read that cannot see the gate must never overwrite the gate's status. Rejected: detection inside the skill prose, which would be untestable and would vary by harness.
- `--room-agent` sets the finding Messages' `agent` and the review heading. The summary's card stays `semantic-review`, because the last card per name wins in `room._parse_room` and `_re_review` needs the reviewer's own role. `--room-to` adds `metadata.to`, so `is_actionable` surfaces the task to the asker only.
- Room review body: the heading, a blank line, then `render_summary(review, unanchored, disposition, model, files)`. It is called with no room, head, or earlier argument and its `MARKER` first line is dropped, so it carries no hidden markers and no Earlier-reviews block. On an inline rejection, the retry passes the folded rendering. The shared summary comment (Q1) is unchanged and is still upserted in place.
- On a re-review after a head move, the summary comment is edited in place and gains an Earlier-reviews entry, and a new full review lands on the new head. So the timeline keeps each verdict and the comment keeps the history.

### Room skill

- A new `## Reviewing` section in `plugins/s/skills/room/SKILL.md` covers a reviewer working a task, addressed to it, that asks for a (re-)review: claim `working`, run `whoami` (stop on non-zero), run `/s:review … status=auto room-agent=<to> room-to=<last_agent>`, then close the task `completed` with the verdict and summary URL.
- The skill states both status cases and forbids a freeform `gh pr review`. The same content goes into `plugins/s/harness/bodies/room.md`, `plugins/s/harness/references/room.md`, and `docs/room-run.md`. `posting.md` lists the three options.
- Re-review needs no runner change. Finding tasks name the reviewer as opener, so `room_run._re_review` re-asks it after any push.

Risk: the reviewer must run in a checkout of the PR's repository, because `/s:review` fetches `pull/<n>/head` and `review_gate.py` resolves the repo from the cwd. `docs/room-run.md` already says "in the same repository".

## Questions and answers

### Q1: Which summary comment does the room reviewer upsert?
- **Question:** Options: (1) the single existing `<!-- shipd-semantic-review -->` summary, edited in place, Earlier reviews kept; (2) a per-room-agent summary keyed by a new marker. Recommendation: (1).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option 1. `gate-poster` fixes `post` to one marker-keyed summary edited in place, and `summary-earlier-reviews` keeps the prior verdict.
- **Cited:** verified/semantic-review (gate-poster, summary-earlier-reviews)

### Q2: Does the room reviewer ever set the semantic-review status?
- **Question:** Options: (1) never; (2) only when the repository has no CI gate workflow. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 2. The reviewer posts with `status=auto`. When `.github/workflows/copilot-review-gate.yml` exists at the PR's base commit, it sets no status. When the contents read returns 404, it sets the status. Any other read failure sets none.
- **Queued:** q-room-reviewer-semantic-review-status

### Q3: Who are the room reviewer's finding tasks addressed to?
- **Question:** Options: (1) the asker, via `--room-agent`/`--room-to`; (2) unaddressed, opener `semantic-review`. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. The tasks are addressed to the agent that requested the review, with the reviewer's room agent as opener.
- **Queued:** q-room-reviewer-finding-task-addressee

### Q4: Brand line or "Not a verdict" notice first on an ungrounded gate body?
- **Question:** Options: (1) brand line, then the notice; (2) the notice, then the brand line. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. The brand line comes first, then a blank line, then the notice.
- **Queued:** q-review-body-brand-line-vs-not-a-verdict-order

### Q5: What does the room reviewer's submitted review body hold?
- **Question:** Options: (1) the speaker heading plus a pointer to the summary comment; (2) the full branded summary. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 2. The approve or request-changes body carries the full branded summary (brand line, verdict, findings table, footer) under the speaker heading. The shared summary comment still holds the history.
- **Queued:** q-room-review-body-pointer-or-full-summary

## Readiness attestation

### Problem and motivation

Neither reviewer on PR 37 posted the shipd layout.

Evidence:

- `gh api repos/mikkel-bergmann/unkannybanny/pulls/37/reviews`: review 5584318350 by `github-actions[bot]` opens `## Findings: ✅ Ship it` with no brand, and review 5584317611 by `shipd-now` is one prose sentence.
- `review_gate.py:79` defines `BRAND_LINE`, and the gate template never emits it (`copilot-review-gate.yml:1293-1298`).

### Scope and non-goals

The change covers the gate body, the poster's flags, and the room reviewer's review step. The runner code, `room.py`, and the Copilot template stay as they are.

Evidence:

- In scope: `copilot-review-gate.yml:1066-1307`, `review_gate.py:728-1057,1500-1515`, `plugins/s/skills/room/SKILL.md:120-125`.
- Out of scope: the `room_run.py:337` prompt, and `room.py` `main` (owned by `room-bundle-run`).

### Affected capabilities and files

Four capabilities and about fifteen files are affected.

Evidence:

- `copilot-review-skill`: `gate-report-extraction` (base d7aaf050399c) and `gate-review-grounding` (base 3cc526e15d7c).
- Runnable premise: `gh api "repos/mikkel-bergmann/unkannybanny/contents/.github/workflows/copilot-review-gate.yml?ref=main"` exited 0, and the same call on a missing path exited 1 with stderr `gh: Not Found (HTTP 404)`.
- Runnable premise: `room_run._fix_required` returned `True` for both a branded and an unbranded fix-required body, and `earlier_reviews` read a branded summary's verdict.
- Runnable premise: `review_gate.py post --help` lists only `--from`, `--disposition`, and `--model`.
- Runnable premise: the base suites pass (copilot verb 233, `test_room_run` 45, `test_review_gate` 170).

### No open task-shaping decision

Every decision is settled.

Evidence:

- Q1 was settled by the oracle. Q2–Q5 were settled by the user.
- The brand insertion point, the summary card name, the status-detection mechanics, and the review-body rendering were settled by investigation, as recorded under Implementation.
