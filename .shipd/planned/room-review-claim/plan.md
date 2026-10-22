# room-review-claim
Status: ready
Theme: reliability
Planned-at: 88c9b852075daa7c675fec57126dd4c616e1a63f
Gated-hash: 96330be0b290

## Idea

Claim each pull request head through an atomic GitHub ref with a heartbeat, so
exactly one reviewer runner, on any machine, posts a review of it, and let the
merge rules wait for that review.

### Motivation

Reviewer runners for one agent can run on several machines and compete for
the same pull request, and nothing on GitHub stops two of them reviewing one
head; on https://github.com/mikkel-bergmann/unkannybanny/pull/39 a duplicate
approval merged findings the real review was still raising.

### Details

- **Claim.** Before a reviewer or ci turn, the runner creates
  `refs/shipd/claims/pr-<N>/<agent>/<sha>/<gen>` through the GitHub API.
  GitHub creates a ref only once, so exactly one runner wins each generation.
- **Heartbeat.** While its turn runs, the winner moves its claim ref to a new
  claim commit every 60 seconds. GitHub stamps each commit with its own clock.
- **Takeover.** A loser skips the turn while the holder is live. When the
  newest claim has been released, or its last heartbeat is more than 10
  minutes old by GitHub's clock, a runner creates the next generation, again
  atomically. A claim marked done means the head is reviewed: losers skip it.
- **Poster fence.** `review_gate.py post`, run by the reviewing session,
  checks the claim before its first GitHub write and again before the review:
  its generation must still be the newest, its holder must match, and its
  last heartbeat must be under 5 minutes old. Otherwise it posts nothing and
  exits non-zero. After the review, it marks the claim done.
- **Merge guard.** A won claim sets the commit status `room-review/<agent>`
  to `pending` on the head; the poster sets it to `success` after the review.
  A repository requires it by listing the context in `merge.required_checks`
  and running `shipd gate rules apply`.
- **Permission.** Claims need push permission. A reviewer or ci runner whose
  account lacks it refuses to start with one `Error:` line.
- **Cleanup.** When a pull request closes, the runner deletes its claim refs.
- `plugin.json` goes from `0.6.344` to `0.6.345`.

Affected capabilities: `room-runner` (added `room-review-claim`,
`room-review-claim-permission`, `room-review-status`,
`room-review-claim-cleanup`) and `semantic-review` (added
`gate-poster-room-claim-fence`). Impact: new
`plugins/s/skills/room/scripts/room_claim.py`,
`plugins/s/skills/room/scripts/room_run.py`,
`plugins/s/skills/room/scripts/room_run_repo.py`,
`plugins/s/skills/review/scripts/review_gate.py`,
`plugins/s/skills/room/SKILL.md`, new
`plugins/s/skills/room/tests/test_room_claim.py`, the room and review test
suites, new `docs/room-review-claims.md`, `docs/room-run.md`,
`docs/semantic-review-reference.md`, `plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No claims for author runners; only reviews are deduplicated.
- No central dispatcher or GitHub Actions queue.
- No change to `merge_rules.py`; requiring `room-review/<agent>` is a config
  entry the repository owner adds.
- No claim in the CI gate workflow; its poster runs without
  `SHIPD_ROOM_CLAIM` and behaves exactly as today.
- Runners older than `0.6.345` do not claim. The guarantee holds once every
  runner of the agent runs this version.

## Implementation

- **Live GitHub behaviour this rests on** (probed on unkannybanny as
  shipd-now, refs deleted afterwards, no workflow run triggered):
  - `POST /repos/<r>/git/refs` with `ref=refs/shipd/claims/test/x` answered
    `201`; the same create again answered `422 Reference already exists`.
  - `PATCH` of that custom ref to a non-descendant commit with `force:false`
    answered `200`. The same on a branch answered `422 Update is not a fast
    forward`. **So custom refs give no compare-and-swap on update:** only the
    atomic create decides a winner, and takeover always creates a new
    generation, never rewrites one.
  - `POST /git/trees` with an empty tree answered `422 Invalid tree info`.
    Claim commits therefore reuse the head commit's tree.
  - A commit created through the API carries GitHub's time in
    `committer.date`, and every response's `Date` header is GitHub's current
    time. Ages are always `Date` minus `committer.date`, never local clocks.
- **Module `room_claim.py`** (stdlib only, in `plugins/s/skills/room/scripts/`).
  Every GitHub call goes through the same `gh` seam the room scripts use
  (`gh(args) -> (rc, out, err)`). Interface:
  - `CLAIM_ENV = "SHIPD_ROOM_CLAIM"`, `BEAT_SECONDS = 60`,
    `LEASE_SECONDS = 600`, `FENCE_SECONDS = 300`.
  - `claim_prefix(number, agent, sha)` returns
    `shipd/claims/pr-<number>/<agent>/<sha>`, with `/` in the agent replaced
    by `_`.
  - Claim commit message: `shipd-claim ` followed by compact JSON
    `{"holder": h, "state": s, "agent": a, "sha": sha}`, where `state` is one
    of `claimed`, `beat`, `done`, `released`.
  - `holder_id()` returns `<hostname>:<pid>:<8 hex chars from uuid4>`,
    computed once per runner process.
  - `class Claim`: `repo`, `number`, `agent`, `sha`, `gen`, `holder`, `ref`
    (`refs/<prefix>/<gen>`), `tip` (sha of its newest commit), `last_beat`
    (GitHub time of that commit). `to_env()` and `from_env(text)` round-trip
    it as JSON for `CLAIM_ENV`.
  - `server_now(gh, repo)`: one `gh api -i` call; parses the `Date` header.
  - `acquire(gh, repo, number, agent, sha, holder)` returns
    `("won", Claim)`, `("held", info)` or `("done", info)`, `info` naming the
    holder and generation. It lists `git/matching-refs/<prefix>/`, reads the
    newest generation's tip commit, and: no generation → create gen `1`;
    newest `done` → `done`; newest `released`, or its age over
    `LEASE_SECONDS` → create gen `newest+1`; otherwise `held`. A create
    answering `422` re-lists once and returns `held` or `done`. The first
    commit has state `claimed`, no parent, and the head commit's tree.
  - `beat(gh, claim, state="beat")` creates a commit with parent
    `claim.tip`, moves `claim.ref` to it (`PATCH`, `force=true`), and updates
    `tip` and `last_beat` from the response.
  - `fence(gh, claim)` raises `room.RoomError` unless: no generation above
    `claim.gen` exists under the prefix; the claim ref's tip commit names
    `claim.holder` with state `claimed` or `beat`; and `server_now` minus
    that commit's time is under `FENCE_SECONDS`. On success it calls `beat`.
  - `Heartbeat(gh, claim, interval=BEAT_SECONDS)`: a daemon thread calling
    `beat` every `interval` until `stop()`; a failed beat writes one
    `warning:` line to stderr and keeps trying.
  - `can_claim(gh, repo)` returns the `permissions.push` boolean of
    `repos/<repo>`.
  - `delete_pr_claims(gh, repo, number)` deletes every ref under
    `shipd/claims/pr-<number>/`; it returns the count and lets errors raise.
  - `set_status(gh, repo, sha, agent, state, description)` posts
    `repos/<repo>/statuses/<sha>` with context `room-review/<agent>`.
- **Runner turn wrapper.** Add `claimed_turn(gh, repo, number, agent, head,
  run)` to `room_claim.py`, used by both modes for roles `reviewer` and
  `ci`. It calls `acquire` on `head`:
  - `won`: set `os.environ[CLAIM_ENV] = claim.to_env()`, call
    `set_status(..., "pending", "claimed for <sha7>")`, start a
    `Heartbeat`, call `run()`, then stop the heartbeat and pop `CLAIM_ENV`.
    Then read the claim ref's tip: if its state is not `done`, call
    `beat(gh, claim, "released")` and
    `set_status(..., "pending", "released; waiting for a runner")`. It
    returns `("ran", run's result)`.
  - `held`: write `room run: #<N> head <sha7> is claimed by <holder>;
    skipping` to stderr and return `("held", None)`.
  - `done`: write `room run: #<N> head <sha7> was already reviewed by
    <holder>` and return `("done", None)`.
- **Repo mode** (`room_run_repo.py:_run_loop`). For roles `reviewer` and
  `ci`, read the head with `room_run._head` and wrap the `runner(...)` call
  in `claimed_turn`. On `held`, leave the cursor and `seen` untouched, so the
  next poll revisits. On `done`, advance the cursor past the tasks as after a
  turn and count no turn. Where the loop drops closed PRs from the state
  (`stale`), also call `delete_pr_claims` for each, warning on failure.
- **PR mode** (`room_run.py:_run_pr`). The same wrapping for roles
  `reviewer` and `ci`. On `held`, sleep `opts.interval` and watch again from
  the same cursor. On `done`, advance the cursor. When the room reports the
  pull request closed, call `delete_pr_claims`, warning on failure.
- **Permission check.** In both `cmd_run_repo` and `cmd_run`, for roles
  `reviewer` and `ci`, after the agent lock and before joining any room: if
  `can_claim` is false, raise `room.RoomError("@<login> cannot create review
  claims on <repo> (it needs push permission); a reviewer runner needs them
  to guarantee one review")`.
- **Poster fence** (`review_gate.py:post`). When `room_agent` is set and
  `os.environ` carries `CLAIM_ENV`, import `room_claim` lazily (the room
  scripts are already on `sys.path` there) and parse the claim. Call `fence`
  immediately before the first `_upsert_summary` call, and again immediately
  before the first `_post_review` call. A `RoomError` becomes
  `_fail("room claim lost: <reason>; nothing posted")`. After a review is
  submitted, call `beat(gh, claim, "done")` and `set_status(gh, repo, sha,
  room_agent, "success", "review posted")`. Without `CLAIM_ENV`, `post`
  behaves exactly as today.
- **Room skill.** In `plugins/s/skills/room/SKILL.md` `## Reviewing`, add
  that a post failing with `room claim lost` ends the turn: relay the line
  and post nothing else, no freeform review.
- **Rejected alternatives.**
  - A lease in the agent card comment: comments have no conditional write,
    so two runners can both win.
  - Fast-forward compare-and-swap on one claim ref: GitHub does not enforce
    fast-forward on custom refs (probed above).
  - Branch or tag refs for claims: they appear in the UI and branch pushes
    trigger workflows.
- **Risks.**
  - A runner that freezes for over 5 minutes between the fence and GitHub
    receiving the review can still post late. The `room-review/<agent>`
    status keeps a merge waiting until the claimed review posts.
  - With the status required, a head that no runner claims blocks the merge.
    That is the intended fail-closed behaviour, and the docs say so.
  - Each heartbeat adds one small commit object to the repository. Refs are
    deleted on close, so the objects become unreachable.

## Questions and answers

### Q1: Does the merge-side guard ship in this change?
- **Question:** The claim sets a pending `room-review` status while a review
  is claimed, and the merge rules require it. Options: (a) a separate
  follow-up change; (b) include it in this change; (c) don't build it.
  Recommendation: (a).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** (b) Include it in this change.
- **Queued:** q-room-review-claim-merge-guard-scope

### Q2: What does a runner without push permission do?
- **Question:** Claims need push permission. Options: (a) refuse to start
  with one clear error line; (b) warn and review without a claim.
  Recommendation: (a).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** (a) Refuse to start with one clear error line, failing closed.
- **Queued:** q-room-review-claim-no-push-permission

## Readiness attestation

### Problem and motivation

Runners of one agent on several machines can review one head twice.

Evidence:

- `plugins/s/skills/room/scripts/room_run_repo.py:97-141`: the only guard is
  a local `flock`, which another machine never sees.
- `plugins/s/skills/room/scripts/room.py:607-636`: `cmd_join` edits an
  existing card of the same agent instead of refusing.
- PR 39: two reviewer-b runners re-reviewed one head; the approval merged one
  second before the change request.

### Scope and non-goals

Claims for reviewer and ci turns, the poster fence, the status guard,
permission refusal and cleanup.

Evidence:

- In scope: the files under Details.
- Out of scope: author runners, `merge_rules.py` (it already writes any
  `required_checks` context, `plugins/s/skills/build/scripts/merge_rules.py:86`),
  the CI gate workflow.

### Affected capabilities and files

`room-runner` gains four requirements and `semantic-review` gains one.

Evidence:

- `plugins/s/skills/review/scripts/review_gate.py:1033` is `post`'s first
  GitHub write (`_upsert_summary`); `review_gate.py:61` already puts the room
  scripts on `sys.path`.
- `plugins/s/skills/room/scripts/room_run.py:51-55`: the runner passes the
  process environment to the spawned session, so `CLAIM_ENV` reaches the
  poster.
- `plugin.json` is `0.6.344` on `origin/main` (`88c9b85`).

### No open task-shaping decision

The mechanism rests on live probes, and the user settled Q1 and Q2.

Evidence:

- The live probe results under Implementation.
- Q1 and Q2, answered by the user.
