# review-base-freshness
Status: verified

## Idea

Make `/s:review` resolve the exact base commit a review should compare against,
disclose it, and refuse to post findings derived from any other base.

### Motivation

A posted review diffed a local `main` 35 commits behind `origin/main`, so six of
its seven findings anchored in files the pull request never touched and the
verdict gated the wrong change. The skill's only fetch rule sits inside its
two-ref bullet, so reviewers running the default mode or the pull-request path
have no way to know their base is stale.

### Details

- `semdiff` resolves a short branch base to its remote-tracking counterpart and
  anchors working-tree mode on the fork point.
- Every endpoint is emitted and printed as a SHA, in human mode and `--json`.
- The skill fetches the base's remote before the first `semdiff` call, every mode.
- `review_gate.py post` compares the review's merge base against the pull
  request's own and aborts before any write when they differ.
- `semdiff doctor` reports a base-freshness line.

Affected capability: `semantic-review` (modified). Impact: `semdiff.py` and
`review_gate.py` under `plugins/s/skills/review/scripts/`; the prose surfaces
`SKILL.md`, `references/posting.md` and `references/json-output.md` in that
skill plus `plugins/s/harness/bodies/review.md` and
`plugins/s/harness/references/review.md`; four test modules under
`plugins/s/skills/review/tests/`. No new dependencies.

### Non-goals

- No fix for `semdiff lint` reading changed paths off disk while its endpoints
  name two refs; the review reports that as a could-not-verify entry instead.
- No change to the CI gate workflow, which already resolves its base from the
  pull-request event and fetches it.
- No change to `shipd doctor`, which stays the environment preflight.
- No automatic pull, rebase, or checkout; the working tree stays the user's.

## Implementation

- **Resolve the base rather than refuse a stale one.** `resolve_endpoints()`
  promotes a base given as a short branch name to the SHA of its remote-tracking
  counterpart — the branch's configured upstream, else
  `refs/remotes/origin/<base>`. A fully-qualified ref, a SHA, or a tag is taken
  as given, which is the unambiguous opt-out. Rejected: refusing a diverged base.
  Promotion resolves the common case without touching the user's tree, so a
  refusal would never fire.
- **Working-tree mode anchors on the fork point.** The before side becomes
  `git merge-base <resolved-base> HEAD`, not the resolved base's tip. Promoting
  without that anchor renders the base's own advance as reversions — the same
  wrong verdict, inverted — as the measurements below show.
- **The engine resolves, the prose fetches.** The promotion lives in the engine so
  it cannot be skipped, mirroring how `semdiff diff` already exits non-zero on a
  missing `difft` rather than degrading. The engine stays network-free, reading
  only already-fetched remote-tracking refs; the skill's short prose block runs
  the `git fetch` the engine will not.
- **The fetch's write scope is stated, so the read-only guarantee holds.** The
  review-start fetch updates remote-tracking refs only — never the working tree,
  the index, or a local branch. A failed fetch becomes a could-not-verify entry
  naming that the base went unchecked against its remote, rather than ending the
  review: an offline review is still worth reading if it says what it missed.
- **Endpoints are emitted as SHAs.** The metadata every subcommand already emits
  gains `base_given`, `base_sha`, `head_sha`, and a `merge_base` that is the fork
  point in working-tree mode and absent under `--linear`. The machine payload
  gains a matching `endpoints` object, which is what gives the poster something
  to check.
- **The poster's guard aborts before any write.** `post` resolves the pull
  request's `baseRefOid` and `headRefOid`, computes their merge base through an
  injectable `git` runner alongside the existing `gh` seam, and compares it with
  the review's `endpoints.merge_base`. An absent `endpoints.merge_base` aborts the
  same way: an unverified base is not a verified base, and all three surfaces
  defining the payload are updated here, so none is left behind.
- **The pull-request path resolves its base through GitHub.** `posting.md` stops
  naming `baseRefName`, whose local resolution was the original defect, and
  fetches `pull/<number>/head` with the base branch so both objects exist
  whatever the fork.
- **The doctor probe stays skill-local.** `semdiff doctor` gains the base line and
  keeps its contract: it compares already-fetched refs with no network, fetches
  first only under `--fix`, and stays report-only, so its exit code is still
  non-zero solely for a missing required tool.
- **`SKILL.md`'s line ceiling moves to 330.** The rule runs on every review, so it
  belongs inline rather than in a condition-gated reference. Rejected: trimming
  another section to stay under 300, which would hide an unrelated edit here.

Risk: promotion silently changes which commit a reviewer asked for. Guarded by
the endpoint line naming the resolved base on every review, and by `base_given`
recording what was passed.

## Questions and answers

### Q1: Engine or skill prose for the stale-base rule?
- **Question:** Where should the stale-base rule be enforced — in `semdiff.py`
  so it cannot be skipped, or as prose in `SKILL.md`? Options: (1) the engine,
  with the skill keeping only the `git fetch` step; (2) skill prose alone.
  Recommendation: (1).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** The engine — option 1. A review correctness guarantee belongs in
  deterministic code that refuses, not in prose that can be missed, and the same
  binary already dies on a missing `difft` rather than degrading and leaving the
  skill layer to notice. The skill keeps only the short prose that runs the
  network step the engine will not.
- **Cited:** verified/semantic-review requirement `text-fallback`,
  wiki/prompt-convention-enforcement

### Q2: Which divergence stops a review?
- **Question:** When the base is a local branch diverging from its
  remote-tracking counterpart, should the review refuse on any divergence or
  only when the base is behind? Options: (1) any divergence; (2) behind only.
  Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Neither: resolve the base instead of refusing it. A short branch
  name promotes to its remote-tracking SHA, and working-tree mode anchors on the
  fork point, so no divergence needs a refusal on the diff path. The poster's
  merge-base guard stays the one place a review is stopped.
- **Queued:** q-review-base-divergence-refusal-scope, discarded as non-durable
  because the resolved behaviour lands as a requirement in this capability

### Q3: Which preflight carries the base probe?
- **Question:** Which preflight gains the base-freshness probe — `semdiff
  doctor` or `shipd doctor`? Options: (1) `semdiff doctor` only; (2) both;
  (3) `shipd doctor` only. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** `semdiff doctor` only — option 1. A repo-state probe serving one
  skill belongs in that skill's own engine doctor, and the placement keeps the
  script's network-only-under-`--fix` contract intact. `shipd doctor` stays the
  environment preflight, where a skill-scoped probe would force a wholesale
  restatement of its exhaustively enumerated check list.
- **Queued:** q-base-freshness-probe-doctor-placement

## Readiness attestation

### Problem and motivation

A posted review diffed a local `main` 35 commits behind `origin/main`, so six of
its seven findings anchored in files the pull request never touched. The skill
gives a reviewer no way to see which base was used.

Evidence:

- `plugins/s/skills/review/SKILL.md:52-58` defaults the base to `main` against
  the working tree and names no fetch for that mode.
- `plugins/s/skills/review/references/posting.md:63` reviews a pull request as
  `diff <baseRefName> <headRefOid>`, resolving the base as a local ref.
- Requirement `gate-poster` in capability `semantic-review` publishes to a pull
  request with no check that the review's base matches it.

### Scope and non-goals

The change covers base resolution, endpoint disclosure, the poster's guard, the
doctor probe, and the prose on four review surfaces. The lint content mismatch,
the CI workflow, and `shipd doctor` stay out.

Evidence:

- In scope: `plugins/s/skills/review/scripts/semdiff.py:198-222`,
  `plugins/s/skills/review/scripts/review_gate.py:502-508` and `:607-650`.
- Out of scope: `plugins/s/skills/review/scripts/semdiff.py:930-943` builds
  linter argv over on-disk paths; left as a reported limitation.
- Out of scope: `plugins/s/integrations/copilot/copilot-review-gate.yml:257` and
  `:299-308` already pass the pull request's base SHA and fetch it.

### Affected capabilities and files

One capability and nine files are affected: two engine scripts carry the
behaviour, four prose surfaces state it, four test modules pin it.

Evidence:

- Capability `semantic-review`: modified requirement `review-skill-references`,
  base hash 756ed4ea29eb from `spec_status.py base-hash` (exit 0).
- Files: `scripts/semdiff.py`, `scripts/review_gate.py`, `SKILL.md`,
  `references/posting.md`, `references/json-output.md`,
  `harness/bodies/review.md`, `harness/references/review.md`,
  `tests/test_semdiff_diff.py`, `tests/test_semdiff_doctor.py`,
  `tests/test_review_gate.py`, `tests/test_skill_references.py`.
- Runnable premise: in a scratch clone whose local `main` sat three commits
  behind `origin/main`, `git diff --name-only main...origin/feature` listed
  `a.txt` and `b.txt`, while `git diff --name-only origin/main...origin/feature`
  listed `b.txt` alone — the reported failure, reproduced and fixed.
- Runnable premise: in that clone's working tree with one edit, `git diff
  --name-only main` listed `c.txt`, `git diff --name-only origin/main` listed
  `a.txt` and `c.txt`, and `git diff --name-only $(git merge-base origin/main
  HEAD)` listed `c.txt` — which is why promotion alone is insufficient.
- Runnable premise: `gh pr view --json` lists `baseRefOid` and `headRefOid`
  among its fields, so the poster can resolve the pull request's own base.
- Runnable premise: `git cat-file -p origin/feature:b.txt` printed the blob with
  that branch never checked out, so no worktree is needed to read a base.
- Runnable premise: `python3 semdiff.py files main HEAD` emitted `"base":
  "main"` and `"head": "HEAD"` — ref names, not SHAs — so nothing downstream can
  currently check the base.

### No open task-shaping decision

Five task-shaping decisions are settled and none remain.

Evidence:

- Enforcement site, the engine over skill prose: settled by the oracle, Q1.
- Divergence policy, resolution over refusal: settled by the user, Q2.
- Doctor placement, `semdiff doctor` only: settled by the user, Q3.
- A review payload carrying no `endpoints.merge_base` aborts the post: settled
  by the user in the same round, recorded under `## Implementation`.
- `semdiff lint` stays out of scope and reports its limitation: settled by the
  user in the same round, recorded under `### Non-goals`.
