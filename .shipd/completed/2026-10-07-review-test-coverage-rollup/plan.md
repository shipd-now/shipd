# review-test-coverage-rollup
Status: verified
Theme: reliability

## Idea

### Motivation

Step 7 raises one `test-coverage` finding for every finding the review
writes, at every severity. That count scales with the findings themselves,
and benchy-cf's category breakdown shows what it costs in practice:

| | 0.6.249 | 0.6.252 |
| --- | --- | --- |
| test-coverage low findings, 3 rounds | 35 | 50 |
| every other low category, 3 rounds | 33 | 43 |

Half of every low finding the review produces is an auto-generated
test-coverage finding — and +15 of item 2's +25 extra lows were this
artifact rather than anything item 2 was aiming at. Against that, testing
accounts for 7 of the benchmark's 80 golden findings. The step is drowning
the defects it was meant to sit beside.

### Details

Keep the question — would an existing test fail if this defect regressed? —
and keep asking it of every finding at every severity. Change only the
reporting: roll the answers up into one `test-coverage` finding per cohort
with uncovered findings, naming each defect it would guard and where the
tests belong, anchored once where the tests belong.

### Non-goals

- No change to the question or its scope. Every finding at every severity is
  still asked about; only the output shape changes.
- No severity gating. Rolling up was chosen over raising test-coverage
  findings for high/medium findings only, which would have dropped the
  question for lows entirely.
- No change to the `test-coverage` category or the `--json` shape.

### Reversal, stated plainly

This reverses a deliberate choice. Step 7 shipped saying "This runs
alongside, not instead of, the finding it covers — a real defect and its
missing test are two findings, not one." That reasoning was sound in the
abstract and wrong at scale: it did not anticipate that the count would
track the finding count and dominate the low tier. The measurement is what
justifies the reversal, not a change of taste.

## Implementation

`SKILL.md` step 7 is retitled "Check test coverage, rolled up per cohort"
and rewritten: ask of every finding at every severity, then raise one
`test-coverage` finding per cohort with uncovered findings, naming each
defect it would guard and where the tests belong; never one per finding,
with the reason stated (it multiplies with the findings and buries them); a
fully covered cohort raises none; anchor the roll-up once, where the tests
belong, since it reports a gap spanning sites rather than a defect at each.

Cohort is the unit deliberately — it is already the vocabulary `semdiff
files` emits and the vocabulary the report groups by, so it needs no new
definition and gives a bounded count. "Per changed area" left to the
reviewer's judgement would not.

`plugins/s/harness/bodies/review.md` step 12 carries the same, in its prose
style.

Two surfaces name the old heading and need updating with it:
`test_skill_references.py`'s `test_workflow_steps_stayed_inline` pins
`"### 7. Check test coverage per finding"` literally, and the
`review-skill` requirement's harness-body scenario ends "and to check test
coverage per finding".

### The test

`TestCoverageRollupTest` asserts both surfaces say one finding per cohort
*and* rule out the per-finding form explicitly, since the second is the
thing that regressed. Its pattern tolerates markdown emphasis and code
ticks between words — the same trap the impact-floor patterns hit, where
`**one**` and `` `test-coverage` `` defeated a naive `\s+`. Verified
non-vacuous against `git show HEAD:` on both files.

### One unrelated repair

Two preceding changes inserted pattern blocks into
`test_skill_references.py` such that the impact-floor explanatory comment
ended up directly above `_BOTH_DIRECTIONS_PATTERNS`, which it does not
describe, while `_IMPACT_FLOOR_PATTERNS` had no header comment at all. The
comment moves back above its own block. Pure relocation, no behavior, fixed
here because it is in the file this change already edits and a comment
describing the wrong block is worse than the trivial diff.

### Version

`plugins/s/.claude-plugin/plugin.json` bumps 0.6.256 → 0.6.257.

## Readiness attestation

### Problem and motivation

Step 7's per-finding rule makes test-coverage findings scale with the
finding count, so they are half of every low finding produced while testing
is 7 of 80 golden findings.

Evidence: `plugins/s/skills/review/SKILL.md` step 7 reads "Run this check
over **every** finding you write, at **every** severity ... raise the gap as
its own finding"; benchy-cf's three-round category breakdown gives
test-coverage lows 35 → 50 between 0.6.249 and 0.6.252, against 33 → 43 for
every other low category combined, with +15 of item 2's +25 extra lows being
this artifact.

### Scope and non-goals

In scope: the roll-up on both surfaces, the two places naming the old
heading, the new test, the orphaned-comment repair, the version bump. Out of
scope: the question itself, its severity scope, the category, and the
`--json` shape.

### Affected capabilities and files

One capability, one requirement.

Evidence: `semantic-review`/`review-skill` (base `765bf986111e`). Files:
`plugins/s/skills/review/SKILL.md`,
`plugins/s/harness/bodies/review.md`,
`plugins/s/skills/review/tests/test_skill_references.py`,
`plugins/s/.claude-plugin/plugin.json`. Runnable premises: applied and
measured in this worktree — SKILL.md 325/330, rendered harness body
132/140, 236 review tests green — and the new test confirmed non-vacuous by
matching its patterns against `git show HEAD:` for both surfaces (both
False before, both True after).

### No open task-shaping decision

- Roll-up versus severity gating: roll-up, per the user's decision, so the
  question still covers lows.
- Cohort as the roll-up unit: settled above — existing vocabulary, bounded
  count, no new definition needed.
- Where a rolled-up finding anchors: once, where the tests belong, by the
  same reasoning as the description-level single-anchor rule shipped in
  v0.6.256.
- Whether to reverse the original per-finding reasoning silently: no, it is
  named as a reversal in `plan.md` and in the commit, with the measurement
  that justifies it.
