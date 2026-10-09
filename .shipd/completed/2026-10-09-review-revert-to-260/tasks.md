# Tasks

The reference point for every revert task is commit `e360273`, which shipped
v0.6.260. Restore a file with `git checkout e360273 -- <path>` rather than by
hand-editing it back, so the result is the measured content and not an
approximation of it.

- [x] 1.1 [P1] [req: review-skill] Restore `plugins/s/skills/review/references/json-output.md` to
      its `e360273` content, removing the `killed` array, the `verifier`
      object, `candidate`, `candidates_by_spawn`, and the discovery-order
      paragraph. Confirm with `git diff e360273 -- <that path>` printing
      nothing.
- [x] 1.2 [P1] [req: review-skill] Restore `plugins/s/harness/references/review.md` to its
      `e360273` content, removing the same payload additions. Confirm the same
      way.
- [x] 1.3 [P1] [req: review-skill] Restore `plugins/s/skills/review/scripts/review_gate.py` to its
      `e360273` content, removing `_verifier_line()` and its call in
      `render_summary`, and drop the verifier-line tests from
      `plugins/s/skills/review/tests/test_review_gate.py`. Every other test in
      that file must still pass.
- [x] 1.4 [P1] [req: review-skill-references] Delete `plugins/s/skills/review/references/verification.md` with
      `git rm`. Nothing else may reference it when the build finishes — grep
      the whole repository for `verification.md` and resolve every hit.
- [x] 1.5 [P1] [req: review-skill] Rewrite the `low` bullet in
      `plugins/s/integrations/copilot/SKILL.md` to v0.6.260's *skill* wording:
      the kinds list (swallowed errors, resource leaks on rare paths, dead or
      duplicated code, unread variables, unstable ids, blocking calls in async
      contexts), that pure style, naming and formatting are never findings,
      and the impact floor stating those are kinds rather than severities.
      Remove v0.6.262's concrete instances and its
      uncertainty-is-not-grounds-for-omitting sentence. Do **not** restore
      that file's v0.6.260 text, which is the stale
      "style, naming, minor redundancy, defensive nits" bullet.
- [x] 2.1 [P2] [req: review-skill] Restore `plugins/s/skills/review/SKILL.md` to its `e360273`
      content, then re-apply the further-location keeper in the report step:
      replace the three-line `**location** (the fix site, never a symptom)`
      sentence with the eight-line version carrying the primary-anchor clause
      and the three further-location shapes, exactly as `HEAD` states it.
      The file must end at 332 lines, the steps must number 1, 2, 3, 3b, 4, 5,
      5b, 5c, 5d, 6, 7, the References table must carry no `verification.md`
      row, and the subcommand list must not name `related`.
- [x] 2.2 [P2] [req: review-skill] Restore `plugins/s/harness/bodies/review.md` to its `e360273`
      content, then re-apply both keepers: step 10's "a further location
      follows the same permission as step 11, never a separate rule", and step
      11's location parenthetical naming the three shapes. The file must end
      at 137 lines.
- [x] 3.1 [P3] [req: body-content] Change the rendered-body ceiling in
      `plugins/s/skills/build/tests/test_harness_bodies.py` from 250 to 150 in
      both assertions of `test_every_body_stays_lean_at_the_full_vocabulary`,
      and extend its docstring with this change: the first lowering in the
      series, the measured worst case of 141 for `review` on `aider` against
      138 at the full vocabulary, and that v0.6.260's own 140 would not have
      held because its test rendered only the full vocabulary. Keep the
      every-registered-harness loop. Do not restate the figure anywhere else —
      `body-content` owns it.
- [x] 3.2 [P3] [req: review-skill] Prune `plugins/s/skills/review/tests/test_skill_references.py`
      of every test pinning reverted behaviour: the verify-stage classes
      (`VerifyStageStepTest`, `KilledNeverInFindingsTest`,
      `VerifierHandoverTest`, `VerdictIndexNumberingTest`,
      `SeverityRubricInSpawnTest`, `NoRubricCopyInVerificationMdTest`,
      `TwoStageRubricSeparationTest`,
      `OrientationSentenceNamesOtherRubricTest`, `DriftSpawnCarriesBothTest`,
      `AsymmetryStatedTest`, `KilledEntryCategoryTest`,
      `PerSpawnCandidateCountTest`), the related-file-context step tests, and
      the tests asserting v0.6.262's concrete instances and contained-impact
      `low`. Restore v0.6.260's assertions on the kinds-list `low` bullet and
      the impact floor from `e360273`. Keep every further-location test. Each
      removal needs a one-line reason naming the behaviour that is gone; a
      test that fails because a keeper was reverted is a bug in task 2.1 or
      2.2, not a test to delete.
- [x] 3.3 [P3] [req: review-skill] Bump `plugins/s/.claude-plugin/plugin.json` from 0.6.274 to
      0.6.275.
- [x] 4.1 [P4] [req: review-skill] Verify. Run the review suite
      (`python3 -m unittest discover -s plugins/s/skills/review/tests`) and the
      build suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`), reading
      each verdict with
      `grep -E "^(OK|FAILED|ERROR)|^Ran [0-9]+ tests"` over the captured log
      rather than tailing it, since those suites print subprocess output after
      their own summary and write the summary to stderr. Then confirm
      `python3 plugins/s/skills/build/scripts/spec_lint.py review-revert-to-260`
      exits 0, and check each delta scenario against the real files rather
      than trusting the suites.
- [x] 4.2 [P4] [req: review-skill] Prove the revert is complete and nothing else moved. Run
      `git diff e360273 HEAD -- plugins/s/skills/review/SKILL.md
      plugins/s/harness/bodies/review.md` and confirm every remaining hunk is
      a further-location keeper. Run `git diff e360273 HEAD -- plugins/s/`
      and account for every other file still differing: `plugins/s/skills/review/scripts/semdiff.py` and its
      tests (the `related` subcommand stays), `plugins/s/skills/review/references/risk-lenses.md` and
      `plugins/s/skills/review/references/pr-description.md`
      (further-location consequences),
      `plugins/s/integrations/copilot/SKILL.md` (task 1.5), `plugins/s/skills/build/tests/test_harness_bodies.py`
      (the ceiling and its docstring),
      `plugins/s/skills/review/tests/test_skill_references.py`, and
      `plugins/s/.claude-plugin/plugin.json`. A file differing for any other reason is an incomplete
      revert.
