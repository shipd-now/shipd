# Tasks

- [x] 1.1 [P1] [req: review-skill] Restore
      `plugins/s/skills/review/SKILL.md` and
      `plugins/s/harness/bodies/review.md` from commit `c677745`, which
      carries v0.6.276's prompt byte for byte. Confirm by diffing both against
      `428e80b`, the v0.6.276 merge, and seeing nothing — restore them from
      that commit rather than hand-removing the clause, so the result is the
      measured content and not an approximation of it.
- [x] 1.2 [P1] [req: review-skill] Remove `DistanceConditionParityTest` from
      `plugins/s/skills/review/tests/test_skill_references.py`, which pins the
      reverted rule and nothing else. Leave every other test in that file
      alone; a failure elsewhere means the restore reached further than it
      should have.
- [x] 1.3 [P1] [req: review-skill-references] Return the `SKILL.md` ceiling to
      340 in `review-skill-references`, which owns it — prose and scenario
      both — and in the assertion enforcing it. In that test's docstring
      record **why the idea is closed and not deferred**: near anchors matched
      the judge 10 of 11 and were redundant rather than false, so banning a
      subset matching at 91% when precision is 28% can only lower precision.
      Keep the measuring discipline the previous raise added — measure the
      figure, never add to the last number written there.
- [x] 1.4 [P1] [req: body-content] Return the rendered-body ceiling to 150 in
      `body-content`, prose and scenario both, and in both assertions in
      `plugins/s/skills/build/tests/test_harness_bodies.py`. Do not restate
      either figure anywhere else.
- [x] 1.5 [P1] [req: review-skill] Bump
      `plugins/s/.claude-plugin/plugin.json` from 0.6.280 to 0.6.281.
- [x] 2.1 [P2] [req: review-skill] Verify the restore is exact and total. The
      diff against `c677745` must be empty for both prompt surfaces. The
      merged `review-skill` must carry no "outside the primary's hunk", no
      "block or table" and no recurrence-exemption text, and its scenario list
      must match `c677745`'s with the five distance scenarios named in
      `Dropped:` lines. `SKILL.md` must be 336 and the worst rendered harness
      body 145 — measure the second by rendering every registered harness,
      never by counting source lines.
- [x] 2.2 [P2] [req: review-skill] Run the whole-library lint, the review
      suite and the build suite, reading each suite verdict with
      `grep -E "^(OK|FAILED|ERROR)|^Ran [0-9]+ tests"` over a captured log
      rather than tailing it, and never running a suite concurrently with a
      probe that mutates a file. Check each delta scenario against the real
      files.
