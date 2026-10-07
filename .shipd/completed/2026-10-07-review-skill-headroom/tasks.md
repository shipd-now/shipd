## 1. Extract steps 3 and 4 into one reference

- [x] 1.1 [req: review-skill] Confirm the starting point: `wc -l
      plugins/s/skills/review/SKILL.md` reports 329 and `python3 -m
      unittest discover -s plugins/s/skills/review/tests -v` is green.
- [x] 1.2 [req: review-skill] Create
      `plugins/s/skills/review/references/call-site-tracing.md` with two
      sections — "Downstream impact" (the five checks: untouched callers,
      every match a candidate, `--lang` missing extensionless scripts,
      changed constants as contract changes, uneven sibling sites) and
      "Call-site values — reachability and comment accuracy" (the two
      checks: unreachable guard / dead branch, comment / intent vs. actual
      behaviour) — carrying the full explanatory prose moved verbatim from
      SKILL.md's current steps 3 and 4. Open the file with a level-1 title
      and a "The skill reads this file when..." condition sentence sharing
      at least three content words with the table row added in 1.4, per
      `test_each_reference_opens_with_title_and_condition` and
      `test_table_cell_agrees_with_reference_condition`.
- [x] 1.3 [req: review-skill] In `plugins/s/skills/review/SKILL.md`,
      replace step 3's five full bullets with its intro sentence, a pointer
      to `${CLAUDE_PLUGIN_ROOT}/skills/review/references/call-site-tracing.md`,
      and five one-line name bullets; replace step 4's two full bullets
      with its intro, a "same reference as step 3" pointer, and two
      one-line name bullets, keeping its closing "Both are usually low
      severity alone, but they compound" paragraph.
- [x] 1.4 [req: review-skill] Add the References table row:
      `| `${CLAUDE_PLUGIN_ROOT}/skills/review/references/call-site-tracing.md` | a changed signature, constant, guard, or helper needs chasing to its call sites |`
- [x] 1.5 [req: review-skill] Run `wc -l
      plugins/s/skills/review/SKILL.md` — it should report 316, well under
      the 330 ceiling — and `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v`, confirming green.

## 2. Raise the harness-body ceiling

- [x] 2.1 [req: body-content] Record the current sizes for the change's
      own evidence: render every body at `hr.FEATURES` and confirm review
      119, epic 119, gate 118, ask 116, with the next largest at 112.
- [x] 2.2 [req: body-content] In
      `plugins/s/skills/build/tests/test_harness_bodies.py`, raise
      `test_every_body_stays_lean_at_the_full_vocabulary`'s `assertLess`
      constant from 120 to 140, and add a docstring recording why: the
      ceiling guards against bloat and is not a budget to compress real
      instructions into; four bodies had reached 116-119; twice that
      compression silently dropped content a reviewer had to restore.
- [x] 2.3 [req: body-content] Run `python3 -m unittest
      plugins.s.skills.build.tests.test_harness_bodies -v` and confirm all
      27 tests pass.

## 3. Generalize the inline-names rule and its tests

- [x] 3.1 [req: review-skill] In
      `plugins/s/skills/review/tests/test_skill_references.py`, add two
      phrase tuples beside the existing `NEW_CODE_CHECKS` — the five
      downstream-impact check names and the two call-site-value check
      names, each matched case-insensitively as literal phrases — plus a
      `_missing_*` helper and a test asserting all of them appear in
      SKILL.md outside the References table, mirroring
      `test_new_code_checks_named_inline` and `_missing_checks` exactly.
      Match the names against what task 1.3 actually left inline.
- [x] 3.2 [req: review-skill] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v` and confirm the new test passes
      and nothing else broke.

## 4. Version and verification

- [x] 4.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json`'s `version`
      from `0.6.253` to `0.6.254`.
- [x] 4.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v`, `python3 -m unittest discover -s
      plugins/s/skills/build/tests -v`, and `python3
      plugins/s/skills/build/scripts/spec_lint.py` (both the full lint and
      `spec_lint.py review-skill-headroom`), confirming every suite and
      both lints pass.
