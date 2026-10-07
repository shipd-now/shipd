## 1. Restore the breadth-sweep wording

- [x] 1.1 [req: review-skill] Confirm the starting point: `wc -l
      plugins/s/skills/review/SKILL.md` reports 329, and `python3 -m
      unittest discover -s plugins/s/skills/review/tests -v` is green.
- [x] 1.2 [req: review-skill] In `plugins/s/skills/review/SKILL.md` step
      5c, replace "Revisit each changed file for remaining low-severity
      defects the structural diff and signature-chasing steps do not
      catch." with "Revisit each changed file end to end for a remaining
      low-severity defect of the categories named in the rubric below — a
      pass the structural diff and signature-chasing steps do not catch."
- [x] 1.3 [req: review-skill] In the same file's step 5, shorten the
      reference pointer from "for the full guidance and worked examples:"
      to "for guidance:" — the reference file's own content is unaffected,
      this only frees the one line 1.2 costs. Run `wc -l
      plugins/s/skills/review/SKILL.md`; it must be under 330.

## 2. Guard it with a test

- [x] 2.1 [req: review-skill] In
      `plugins/s/skills/review/tests/test_skill_references.py`, add
      `test_breadth_sweep_points_at_the_rubric_categories`, asserting
      SKILL.md's step 5c section contains both "end to end" and a mention
      of "rubric". Confirm it fails against the pre-1.2 wording and passes
      after.
- [x] 2.2 [req: review-skill] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v` and confirm the whole suite,
      including `test_under_line_ceiling` and the new test, passes.

## 3. Version and verification

- [x] 3.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json`'s `version`
      from `0.6.251` to `0.6.252`.
- [x] 3.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v`, `python3 -m unittest discover -s
      plugins/s/skills/build/tests -v`, and `python3
      plugins/s/skills/build/scripts/spec_lint.py` (both the full lint and
      `spec_lint.py review-breadth-sweep-pointer`), and confirm every suite
      and both lints pass.
