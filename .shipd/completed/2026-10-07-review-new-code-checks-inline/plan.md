# review-new-code-checks-inline
Status: verified
Theme: reliability

## Idea

### Motivation

Shipping the low-severity-rubric change (PR #259, v0.6.250) needed line
budget in `plugins/s/skills/review/SKILL.md`, which was already at its
329/330-line test ceiling. Step 5 ("Judge new code on its own terms")'s five
checks were fully extracted to a new reference file,
`references/new-code-checks.md`, leaving only a pointer sentence inline —
no check names stayed in SKILL.md at all.

That is the wrong half of this repo's own established pattern. The
risk-lens step right next to it (`5b`) already solves the identical
problem: it keeps its five trigger *names* inline as bare bullets and
defers only the full guidance and worked examples to `risk-lenses.md`,
specifically because those triggers are "always, never gated" — a check
that always applies cannot depend on the model choosing to open a
conditionally-loaded file, or it silently stops running the moment that
read is skipped. `test_risk_lens_triggers_stated_inline` enforces exactly
this for the risk lenses. Step 5's five checks are the same kind of
always-applies check (every new function/class/guard/helper, not a rare
trigger) and deserve the same treatment — caught by peer session benchy-cf
while benchmarking item 2 against ReviewBench, before it had run any
reviews that could have been skewed by it.

### Details

Restore the five check names as inline bullets under step 5, in the same
shape `5b` already uses for its five triggers — bare bold labels with a
short clause, no full explanation — and keep the reference pointer for the
full guidance and worked examples. Add a test mirroring
`test_risk_lens_triggers_stated_inline` so this cannot regress silently a
second time.

Affected capability: `semantic-review` (requirement `review-skill`,
modified). Impact: `plugins/s/skills/review/SKILL.md` (step 5 regains inline
bullets), `plugins/s/skills/review/tests/test_skill_references.py` (new
test), `.shipd/verified/semantic-review/spec.md`, the plugin version bump.
`references/new-code-checks.md` and `harness/bodies/review.md` need no
change — the reference already carries the full explanations and examples
(unaffected), and the harness body's mirror of step 5 was never extracted
in the first place (it ships into other repos with no
`${CLAUDE_PLUGIN_ROOT}` and was always a single inline paragraph with no
bullets to begin with).

### Non-goals

- No change to the five checks' content, the reference file's explanations
  or worked examples, or the low-severity rubric and breadth-sweep step
  item 2 just shipped.
- No change to `harness/bodies/review.md` — it was never over-extracted.
- Not a re-opening of PR #259; item 2's measurement stands on its own
  evidence, this is a follow-up correctness fix peer session benchy-cf will
  test as the new baseline for step 5's behavior going forward.

## Implementation

In `plugins/s/skills/review/SKILL.md`'s step 5, add five inline bullets
between the intro sentence and the reference pointer, one per check
(`Wrong quantity measured`, `Escape hatch lapsing the guarantee`,
`Termination on hostile input`, `Boundary agreement`, `Doc comment versus
code`), each a bold label plus a clause short enough to fit one line,
mirroring `5b`'s bullet shape and line budget exactly. Reword the pointer
sentence to say the reference carries "the full guidance and worked
examples" (matching `5b`'s own phrasing) rather than "the five checks," since
the names no longer live only there.

This adds roughly 5 lines against the 329/330 ceiling with no slack. Trim
the intro sentence (currently 3 wrapped lines) to 2 by dropping a clause
that does not change the instruction, and if that is not enough, the
implementer trims step 5c's wording (already minimal) or the low-rubric
bullet (already minimal) next, in that order, re-running
`test_under_line_ceiling` after each trim — never by re-removing the
restored bullet names, which is the point of this change.

Add `test_new_code_checks_named_inline` to `test_skill_references.py`'s
`SkillMdStructureTest` (or a new small test class beside
`ReferenceFreeSurfacesCarryRiskLensesTest`, whichever fits the file's
existing organization better), asserting all five check names appear in
SKILL.md's inline text — mirroring
`test_risk_lens_triggers_stated_inline`'s shape (exclude the References
table from the search, same as that test does, so a name mentioned only in
the table's condition column does not pass vacuously).

`.shipd/verified/semantic-review/spec.md`'s `review-skill` requirement gets
one added sentence stating the five new-code checks' names must also appear
inline, outside any reference file, with a new scenario. Plugin version
bumps 0.6.250 → 0.6.251.

## Readiness attestation

### Problem and motivation

Step 5's five "judge new code" checks are fully extracted to a
conditionally-loaded reference with no names left inline, unlike the
identical-shape risk-lens step beside it — an always-applies check that
silently stops running if the model skips the read, flagged by benchy-cf
before any ReviewBench evidence could be skewed by it.

Evidence: `plugins/s/skills/review/SKILL.md` step 5 (current: intro sentence
+ pointer only); step 5b (five bullet names + pointer, the pattern to
match); `test_risk_lens_triggers_stated_inline` in
`plugins/s/skills/review/tests/test_skill_references.py` (the existing test
enforcing that pattern for 5b, with no equivalent for step 5).

### Scope and non-goals

In scope: restoring the five names inline in SKILL.md, a matching test, the
spec sentence, the version bump. Out of scope: the checks' content, the
reference file, the harness body (never over-extracted), and item 2's
already-shipped rubric/breadth-sweep content.

### Affected capabilities and files

One capability, one requirement, one file with behavior content
(`SKILL.md`), one test file, one spec file, one manifest.

Evidence: capability `semantic-review`, requirement `review-skill` (base
hash `d856d3edfa7c`, from `spec_status.py base-hash semantic-review
review-skill` against this worktree's current `main`). Runnable premise:
`wc -l plugins/s/skills/review/SKILL.md` reports 329 right now, confirming
the ceiling is still live and the implementer must trim to make the
restored bullets fit.

### No open task-shaping decision

- Which bullet shape to use: the risk-lens step's exact shape — settled
  above, it is the established, tested pattern.
- Where to trim if the restored bullets do not fit as-is: the intro
  sentence first, then step 5c, then the low-rubric bullet, in that order —
  settled above, never by dropping the bullet names again.
- Whether to touch the harness body or the reference file: no, neither was
  over-extracted or needs content changes — settled above.
