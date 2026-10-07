## 1. Restore the five check names inline

- [x] 1.1 [req: review-skill] Confirm the starting point: run `wc -l
      plugins/s/skills/review/SKILL.md` (329) and
      `python3 -m unittest discover -s plugins/s/skills/review/tests -v`
      (green) before any edit.
- [x] 1.2 [req: review-skill] In `plugins/s/skills/review/SKILL.md` step 5,
      add five inline bullets between the intro sentence and the reference
      pointer — one per check (`Wrong quantity measured`, `Escape hatch
      lapsing the guarantee`, `Termination on hostile input`, `Boundary
      agreement`, `Doc comment versus code`), each a bold label plus a
      clause short enough to fit one line, in the exact bullet shape step
      5b already uses for its five risk-lens triggers. Reword the pointer
      sentence to say the reference carries "the full guidance and worked
      examples" (matching 5b's own phrasing), since the names no longer
      live only there.
- [x] 1.3 [req: review-skill] Run `wc -l plugins/s/skills/review/SKILL.md`.
      If it is at or above 330, trim in this order until it is under: first
      the step-5 intro sentence (currently 3 wrapped lines, tighten to 2
      without changing the instruction), then step 5c's wording, then the
      low-rubric bullet's wording — never by removing a restored bullet
      name, which is the point of this change.

## 2. Guard the regression with a test

- [x] 2.1 [req: review-skill] In
      `plugins/s/skills/review/tests/test_skill_references.py`, add
      `test_new_code_checks_named_inline` asserting all five check names
      from task 1.2 appear in SKILL.md's text outside the References table —
      mirroring `test_risk_lens_triggers_stated_inline`'s shape exactly
      (same table-exclusion helper), so a name mentioned only in the table's
      condition column does not pass vacuously. Run it and confirm it fails
      against the pre-fix SKILL.md, then passes after task 1.2's edit.
- [x] 2.2 [req: review-skill] Run
      `python3 -m unittest discover -s plugins/s/skills/review/tests -v`
      and confirm the whole suite, including `test_under_line_ceiling` and
      the new test, passes.

## 3. Version and verification

- [x] 3.1 [req: *] Bump the `version` field in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.250` to `0.6.251`.
- [x] 3.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v`, `python3 -m unittest discover -s
      plugins/s/skills/build/tests -v` (confirms
      `test_every_body_stays_lean_at_the_full_vocabulary` is unaffected,
      since `plugins/s/harness/bodies/review.md` is untouched by this change), and
      `python3 plugins/s/skills/build/scripts/spec_lint.py` (both the full
      lint and `spec_lint.py review-new-code-checks-inline`), and confirm
      every suite and both lints pass.
