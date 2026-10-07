# review-breadth-sweep-pointer
Status: verified
Theme: reliability

## Idea

### Motivation

The previous line-budget trim (PR #260, v0.6.251) restored the five
new-code check names but, in the same pass, also weakened step 5c's
breadth-sweep instruction: it dropped "end to end" and the pointer at the
rubric's own category list ("of the categories named in the rubric"),
leaving only "revisit each changed file for remaining low-severity defects
the structural diff and signature-chasing steps do not catch." Peer session
benchy-cf caught it while testing v0.6.251 as item 2's baseline: "pointing
at that list is the core of item 2: it tells the sweep what to look for."

`.shipd/verified/semantic-review/spec.md`'s `review-skill` requirement
already states the correct, un-weakened wording ("revisits each changed
file once more, end to end, for a remaining low-severity defect of those
kinds") — this is `SKILL.md` drifting behind an already-correct spec, not a
new requirement.

### Details

Restore step 5c's wording in `SKILL.md` to match what the spec already
requires, and add a test that locks the "points at the rubric's
categories" property in place so a third trim cannot silently drop it
again — the same lesson PR #260 already applied to the new-code check
names, applied here to the sweep's own pointer.

Affected capability: `semantic-review` (requirement `review-skill`,
modified — one added scenario, no change to existing requirement prose,
which already states the correct wording). Impact:
`plugins/s/skills/review/SKILL.md` (step 5c wording only),
`plugins/s/skills/review/tests/test_skill_references.py` (new test), the
plugin version bump. `harness/bodies/review.md` is untouched — its own
mirror of this step already carries the correct wording and was never
weakened.

### Non-goals

- No other content change. This is strictly a drift-correction to match the
  already-correct spec text, not a rewording or a new idea.
- No change to the five new-code check names or the low-rubric category
  list themselves — both are already correct as of v0.6.251.

## Implementation

Restore `SKILL.md` step 5c to: "Revisit each changed file end to end for a
remaining low-severity defect of the categories named in the rubric below —
a pass the structural diff and signature-chasing steps do not catch." This
costs one line against the 329/330 ceiling (currently 329 again after the
restoration). Free it by shortening step 5's reference pointer from "for
the full guidance and worked examples:" to "for guidance:" — the reference
still carries the full guidance and worked examples regardless of how the
pointer sentence names them, so this costs no content, unlike the trim
being corrected here.

Add `test_breadth_sweep_points_at_the_rubric_categories` to
`test_skill_references.py`, asserting `SKILL.md`'s step 5c section contains
both "end to end" and a reference to the rubric's categories (e.g. the word
"rubric"), so a future line-budget trim that drops either is caught before
it ships rather than after a peer catches it mid-benchmark a second time.

`.shipd/verified/semantic-review/spec.md`'s `review-skill` requirement gains
one scenario asserting this property; its existing prose already states the
correct wording and needs no change.

Plugin version bumps 0.6.251 → 0.6.252.

## Readiness attestation

### Problem and motivation

`SKILL.md` step 5c drifted behind the already-correct `review-skill`
requirement text during the previous change's line-budget trim, dropping
the pointer that tells the breadth sweep what to look for.

Evidence: benchy-cf's cross-session message comparing the v0.6.250 → v0.6.251
diff's step 5c wording against the spec's own prose, both read directly in
this worktree (`.shipd/verified/semantic-review/spec.md` `review-skill`,
`plugins/s/skills/review/SKILL.md` step 5c).

### Scope and non-goals

In scope: `SKILL.md` step 5c's wording, one new test, one new spec
scenario, the version bump. Out of scope: everything else — settled above.

### Affected capabilities and files

One capability, one requirement, no change to its existing prose.

Evidence: capability `semantic-review`, requirement `review-skill` (base
hash `e9577c28bac5`). Runnable premise: `wc -l
plugins/s/skills/review/SKILL.md` reports 329 on this worktree's current
`main`, confirming the ceiling is still live.

### No open task-shaping decision

- Where to find the one line of budget: shorten step 5's pointer sentence,
  which carries no content of its own (the reference file's actual content
  is unaffected either way) — settled above, and is exactly the kind of
  trim that does *not* repeat this change's own root cause.
- Whether to touch the harness body or the five new-code checks: no,
  neither drifted — settled above.
