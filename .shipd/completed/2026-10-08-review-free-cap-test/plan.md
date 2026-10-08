# review-free-cap-test
Status: verified
Theme: reliability

## Idea

### Motivation

PR #275's own semantic review raised one finding: no test constructed a changed
file whose per-file cap is reached entirely by **free** candidates — files
already selected for other changed files. The allocator handles it correctly
today, because the per-file cap check runs before the free-or-paid branch, but
a future change that reordered those two would let free candidates bypass the
per-file cap and every existing test would stay green.

The reviewer wrote that test. **It did not ship.** Auto-merge squashed PR #275
at 16:21:08 and the test was committed at 16:21:58 — fifty seconds later, onto a
branch the merge had already consumed. The commit survived only in the local
object store.

So this change is a recovery, and the process defect behind it is worth stating
plainly: arming auto-merge before a review's disposition loop finishes lets a
late fix be silently dropped. The checks were green, so GitHub merged exactly as
armed. Nothing failed; the work simply landed after the door closed.

### Details

Cherry-pick the lost test, and add the spec sentence and scenario it pins —
because the requirement did not actually say that a free candidate stays subject
to the per-file cap, which is the behaviour the test guards.

### Non-goals

- No change to the allocator. It already behaves correctly; this pins it.
- No change to either prompt surface, and no change to `semdiff.py` at all.
- Not the auto-merge timing itself. That is a workflow habit rather than a code
  defect, and it is recorded here rather than fixed by a code change.

## Implementation

The recovered test is `PerFileCapBoundsFreeCandidatesTest` in
`plugins/s/skills/review/tests/test_semdiff_files_context.py`, cherry-picked
unchanged from `e6e085c` — content the PR #275 gate already reviewed.

The `related-context` requirement gains one sentence and one scenario. The
sentence closes a real gap: the requirement says a shared file is charged once
and still listed everywhere, but never said the per-file cap continues to apply
to it. A reader could have concluded a free candidate is exempt, which is
exactly the misreading a future change would need in order to introduce the
defect this test guards against.

### Version

`plugins/s/.claude-plugin/plugin.json` bumps 0.6.266 → 0.6.267.

## Readiness attestation

### Problem and motivation

A test the PR #275 review asked for, and wrote, is absent from `main` because
auto-merge fired before it was pushed.

Evidence: `git merge-base --is-ancestor e6e085c main` exits non-zero;
`test_per_file_cap_holds_even_when_every_candidate_is_free` appears zero times
in `main`'s copy of the test file; the squash commit `6285be2` is dated
2026-10-08 16:21:08 and `e6e085c` 16:21:58. The finding itself is recorded at
https://github.com/shipd-now/shipd/pull/275#issuecomment-6052914572.

### Scope and non-goals

In scope: the cherry-picked test, one spec sentence, one spec scenario, the
version bump. Out of scope: the allocator, `semdiff.py`, both prompt surfaces,
and any change to auto-merge timing.

### Affected capabilities and files

One capability, one requirement.

Evidence: `semantic-review` requirement `related-context`, base `b24f6b1aa7d0`,
computed with `spec_status.py base-hash` in this worktree. Files:
`plugins/s/skills/review/tests/test_semdiff_files_context.py`,
`plugins/s/.claude-plugin/plugin.json`.

Runnable premises measured here: the cherry-pick applies cleanly to current
`main`; the review suite runs 275 tests green with it, against 274 on `main`;
and `PerFileCapBoundsFreeCandidatesTest` passes on its own.

### No open task-shaping decision

- Whether to rewrite the test or recover it: recover it unchanged, since the
  #275 gate already reviewed that content — settled above.
- Whether the spec needs changing: yes, one sentence, because the requirement
  never said a free candidate stays subject to the per-file cap — settled above.
- Whether to fix auto-merge timing here: no, it is a workflow habit, recorded
  not coded — settled in the non-goals.
