# Tasks

- [x] 1.1 [P1] [req: review-skill] Append the three concrete instances to the
      `Impact floor.` bullet in `plugins/s/skills/review/SKILL.md`: a success
      response that hides a failure — an empty result returned as if real while
      a count or flag says otherwise; a cleanup path that drops the record and
      leaves the data, or the reverse; and an error path that loses the only
      copy. Leave the `low` bullet untouched — it is deliberately not the
      variable. The file must end at 336 lines, under its 340 ceiling.
- [x] 1.2 [P1] [req: review-skill] Carry the same three instances inline in
      `plugins/s/harness/bodies/review.md`'s rate-by-impact sentence. That file
      ships standalone and can read no reference, so the instances go in full
      rather than by pointer. Confirm by rendering every registered harness
      that the worst rendered body is 145 and still under 150 — measure it,
      never infer it from the source line count.
- [x] 1.3 [P1] [req: review-skill] Carry the same three instances in
      `plugins/s/integrations/copilot/SKILL.md`'s own copy of the floor, so all
      three surfaces agree.
- [x] 2.1 [P2] [req: review-skill] Add a test to
      `plugins/s/skills/review/tests/test_skill_references.py` pinning the
      instances on all three surfaces. Match against whitespace-normalised text
      so a reflow at 88 columns cannot make it pass or fail cosmetically, and
      match each instance by a fragment short enough not to wrap rather than by
      a long literal. Then prove it non-vacuous: run it against each surface's content
      as the main branch carries it and watch it fail, with the file otherwise intact —
      check the byte count before and after so a truncating probe cannot be
      mistaken for a real failure.
- [x] 2.2 [P2] [req: review-skill] Bump
      `plugins/s/.claude-plugin/plugin.json` from 0.6.275 to 0.6.276.
- [x] 3.1 [P3] [req: review-skill] Verify. Run the review suite
      (`python3 -m unittest discover -s plugins/s/skills/review/tests`) and the
      build suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`), reading
      each verdict with
      `grep -E "^(OK|FAILED|ERROR)|^Ran [0-9]+ tests"` over a captured log
      rather than tailing it, since those suites print subprocess output after
      their own summary and write the summary to stderr. Confirm
      `python3 plugins/s/skills/build/scripts/spec_lint.py review-rating-verifier`
      exits 0, and check each delta scenario against the real files.
- [x] 3.2 [P3] [req: review-skill] Confirm the change is only what it claims.
      a diff of this branch against the main branch, over the plugin tree, must
      touch exactly five files:
      `plugins/s/skills/review/SKILL.md`,
      `plugins/s/harness/bodies/review.md`,
      `plugins/s/integrations/copilot/SKILL.md`,
      `plugins/s/skills/review/tests/test_skill_references.py` and
      `plugins/s/.claude-plugin/plugin.json`. On the three prose surfaces every
      hunk must be the appended instances and nothing else — in particular the
      `low` bullet, the exposure floor and the verdict rule must be unchanged
      context, since a wording change riding along inside a hunk is the exact
      defect that reached `main` two versions ago.
