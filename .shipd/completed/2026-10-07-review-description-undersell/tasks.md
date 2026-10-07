## 1. Restructure the reference around both directions

- [x] 1.1 [req: review-skill] Confirm the starting point: `wc -l
      plugins/s/skills/review/SKILL.md` reports 321 and `python3 -m
      unittest discover -s plugins/s/skills/review/tests -v` is green.
- [x] 1.2 [req: review-skill] Rewrite
      `plugins/s/skills/review/references/pr-description.md` around two
      bolded directions: **Direction 1 — each claim against the diff**
      (does the diff support, contradict, or fall short of it) and
      **Direction 2 — the diff against the claims** (walk the diff's
      substantial content and ask what the description never mentions).
      State that direction 2 is a distinct pass because unmentioned scope
      carries no claim for direction 1 to iterate over, and scope it to
      substance — a new feature path, dependency, migration, public
      surface, or behavioral change to an existing one — explicitly not
      every file the diff touches.
- [x] 1.3 [req: review-skill] In the same file, rewrite the undersell
      bullet so it names why direction 1 misses it: nothing in the
      description is false, the finding is the silence, and unmentioned
      scope matters because it goes unreviewed.
- [x] 1.4 [req: review-skill] In the same file, add the single-anchor
      paragraph: a drift that is a property of the description rather than
      of any one line carries its primary anchor alone, with a further
      location only where that site independently shows the drift. Include
      the concrete contrast — a claim contradicted at three call sites is
      three sites; an undersell is one finding about the description
      however many files the unmentioned scope spans.

## 2. Name both directions on the two inline surfaces

- [x] 2.1 [req: review-skill] In `plugins/s/skills/review/SKILL.md` step
      5d, replace "verify every claim against the diff" with wording that
      names both directions and the one-sentence reason the second is
      needed (an unmentioned feature has no claim to check).
- [x] 2.2 [req: review-skill] In `plugins/s/harness/bodies/review.md` step
      10, do the same, and additionally carry the single-anchor rule there
      — it has no reference file to defer to.
- [x] 2.3 [req: review-skill] Confirm both budgets: `wc -l
      plugins/s/skills/review/SKILL.md` under 330, and the rendered review
      body under 140. Neither should need compression.

## 3. Guard both directions with a test

- [x] 3.1 [req: review-skill] In
      `plugins/s/skills/review/tests/test_skill_references.py`, add
      `_BOTH_DIRECTIONS_PATTERNS` (one for `both directions`, one for
      `never mentions`/`does not mention`/`unmentioned`), a
      `_both_directions_stated` helper, and a
      `DescriptionCheckDirectionsTest` asserting all three surfaces —
      `SKILL.md`, the harness body, and `plugins/s/skills/review/references/pr-description.md` —
      name both directions. Record in the docstring why the claim direction
      alone cannot reach an undersell, and that the first shipped wording
      matched the benchmark's undersell case 0 of 3 rounds.
- [x] 3.2 [req: review-skill] Prove the test is not vacuous: match the
      patterns against `git show HEAD:<path>` for all three surfaces and
      confirm they miss before the change and match after.
- [x] 3.3 [req: review-skill] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v` and confirm the suite passes.

## 4. Version and verification

- [x] 4.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json`'s `version`
      from `0.6.255` to `0.6.256`.
- [x] 4.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v`, `python3 -m unittest discover -s
      plugins/s/skills/build/tests -v`, and `python3
      plugins/s/skills/build/scripts/spec_lint.py` (both the full lint and
      `spec_lint.py review-description-undersell`), confirming every suite
      and both lints pass.
