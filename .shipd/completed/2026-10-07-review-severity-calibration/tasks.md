## 1. State the impact floor on both rubric surfaces

- [x] 1.1 [req: review-skill] Confirm the starting point: `wc -l
      plugins/s/skills/review/SKILL.md` reports 316 and `python3 -m
      unittest discover -s plugins/s/skills/review/tests -v` is green.
- [x] 1.2 [req: review-skill] In `plugins/s/skills/review/SKILL.md`'s
      severity rubric, add an `**Impact floor.**` bullet directly after the
      `low` bullet and before `**Exposure floor.**`, stating that the low
      list names *kinds* of defect rather than severities; that every
      finding is rated by what it does, not which kind it resembles; that
      data loss, data corruption, a security exposure, or a broken
      guarantee is `medium` or `high` even when it arrives as one of those
      kinds; and the concrete counter-example that a swallowed error which
      loses a file is not low.
- [x] 1.3 [req: review-skill] In the same file's breadth-sweep step,
      replace "a remaining low-severity defect of the categories named in
      the rubric below" with wording that asks for a remaining defect of
      the *minor kinds* named in the rubric, plus an instruction to rate
      what the sweep finds by the impact floor rather than by the kind that
      surfaced it. Keep "end to end" and the rubric pointer — both are
      pinned by `test_breadth_sweep_points_at_the_rubric_categories`.
- [x] 1.4 [req: review-skill] In `plugins/s/harness/bodies/review.md`, fold
      the same floor into its report step's prose, immediately ahead of its
      existing secret/credential exposure sentence, in that file's prose
      style rather than as a bullet.
- [x] 1.5 [req: review-skill] Confirm both budgets: `wc -l
      plugins/s/skills/review/SKILL.md` under 330, and the rendered review
      body under 140 via
      `hb.render('review', hr.FEATURES, refs_dir='plugins/s/skills/review/references')`.
      Neither should need any compression — the preceding headroom change
      left 14 and 21 lines of slack respectively.

## 2. Guard the floor with a parity test

- [x] 2.1 [req: review-skill] In
      `plugins/s/skills/review/tests/test_skill_references.py`, add
      `_IMPACT_FLOOR_PATTERNS` (one pattern for "kinds of defect, not
      severities" that tolerates markdown emphasis inside the phrase, one
      for an impact word landing within ~200 chars of `medium`/`high`), an
      `_impact_floor_stated` helper mirroring `_exposure_floor_stated`, and
      an `ImpactFloorParityTest` asserting both `SKILL.md` and
      `plugins/s/harness/bodies/review.md` state it. Exclude the copilot
      template and record why in the docstring — it carries the older
      style-and-nits rubric.
- [x] 2.2 [req: review-skill] Prove the test is not vacuous: match the two
      patterns against `git show HEAD:<path>` for both files and confirm
      they miss on the pre-fix text and match on the working-tree text.
      A test that passes on the unfixed file guards nothing.
- [x] 2.3 [req: review-skill] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v` and confirm the whole suite,
      including the new test, passes.

## 3. Version and verification

- [x] 3.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json`'s `version`
      from `0.6.254` to `0.6.255`.
- [x] 3.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v`, `python3 -m unittest discover -s
      plugins/s/skills/build/tests -v`, and `python3
      plugins/s/skills/build/scripts/spec_lint.py` (both the full lint and
      `spec_lint.py review-severity-calibration`), confirming every suite
      and both lints pass.
