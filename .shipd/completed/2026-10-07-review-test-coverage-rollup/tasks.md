## 1. Roll the step up on both surfaces

- [x] 1.1 [req: review-skill] Confirm the starting point: `wc -l
      plugins/s/skills/review/SKILL.md` reports 324 and `python3 -m
      unittest discover -s plugins/s/skills/review/tests -v` is green.
- [x] 1.2 [req: review-skill] Retitle `plugins/s/skills/review/SKILL.md`
      step 7 to "Check test coverage, rolled up per cohort" and rewrite its
      body: ask of every finding at every severity whether an existing test
      would fail if that defect regressed; raise one `test-coverage`
      finding per cohort with uncovered findings, naming each defect it
      would guard and where the tests belong; never one per finding, with
      the reason stated; a fully covered cohort raises none; anchor the
      roll-up once, where the tests belong.
- [x] 1.3 [req: review-skill] Make the same change to
      `plugins/s/harness/bodies/review.md` step 12, in that file's prose
      style.
- [x] 1.4 [req: review-skill] Update
      `plugins/s/skills/review/tests/test_skill_references.py`'s
      `test_workflow_steps_stayed_inline`, which pins the old heading
      `"### 7. Check test coverage per finding"` literally, to the new
      heading.
- [x] 1.5 [req: review-skill] Confirm both budgets: `wc -l
      plugins/s/skills/review/SKILL.md` under 330 and the rendered review
      body under 140.

## 2. Guard the roll-up with a test

- [x] 2.1 [req: review-skill] Add `TestCoverageRollupTest` to
      `plugins/s/skills/review/tests/test_skill_references.py`, asserting
      both `SKILL.md` and `plugins/s/harness/bodies/review.md` state one
      `test-coverage` finding per cohort *and* rule out the per-finding
      form explicitly. Make the per-cohort pattern tolerate markdown
      emphasis and code ticks between words — `**one**` and
      `` `test-coverage` `` defeat a naive `\s+`, the same trap the
      impact-floor patterns hit. Record the measurement in the docstring:
      50 test-coverage findings across three rounds against 7 golden
      testing findings in the whole set.
- [x] 2.2 [req: review-skill] Prove the test is not vacuous: match its
      patterns against `git show HEAD:<path>` for both surfaces and confirm
      they miss before the change and match after.
- [x] 2.3 [req: review-skill] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v` and confirm the suite passes.

## 3. Repair the orphaned comment

- [x] 3.1 [req: review-skill] In
      `plugins/s/skills/review/tests/test_skill_references.py`, the
      impact-floor explanatory comment currently sits directly above
      `_BOTH_DIRECTIONS_PATTERNS`, which it does not describe, while
      `_IMPACT_FLOOR_PATTERNS` has no header comment. Move the comment back
      above `_IMPACT_FLOOR_PATTERNS`. Comment relocation only — no pattern,
      helper, or assertion changes.

## 4. Version and verification

- [x] 4.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json`'s `version`
      from `0.6.256` to `0.6.257`.
- [x] 4.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v`, `python3 -m unittest discover -s
      plugins/s/skills/build/tests -v`, and `python3
      plugins/s/skills/build/scripts/spec_lint.py` (both the full lint and
      `spec_lint.py review-test-coverage-rollup`), confirming every suite
      and both lints pass.
