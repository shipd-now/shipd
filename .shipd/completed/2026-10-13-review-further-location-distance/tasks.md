# Tasks

- [x] 1.1 [P1] [req: review-skill] Add the distance condition to the
      further-location sentence in `plugins/s/skills/review/SKILL.md`'s report
      step. State it **conjunctively**: outside the primary's hunk **and**
      outside the function, block or table it sits in. A disjunction is wrong
      and was the first attempt's defect — "outside the function *or* outside
      the hunk" is satisfied by either half alone, and in a file with no
      functions the first half is vacuously true so the rule never binds.
      Name the block or table explicitly so a manifest or data-file primary is
      still constrained, and exempt a genuinely recurring site so the
      condition does not contradict the recurrence rule two sentences below.
      Change nothing else in that paragraph — the three shapes stay exactly as
      they are. The file must end at 341 lines, under its raised 350 ceiling.
- [x] 1.2 [P1] [req: review-skill] Mirror the condition inline in
      `plugins/s/harness/bodies/review.md`'s step 11 location parenthetical,
      since that file ships standalone and can read no reference. That file
      carries **no** recurrence rule of its own, so the exemption has to carry
      one with it or the prohibition stands there with no counterweight.
      Confirm by rendering every registered harness that the worst rendered
      body is 149 and under its raised 160 ceiling — measure it, never infer
      it from the source line count.
- [x] 1.3 [P1] [req: review-skill-references] Raise the `SKILL.md` ceiling
      from 340 to 350 in `review-skill-references`, which owns it, and in the
      assertion that enforces it in
      `plugins/s/skills/review/tests/test_skill_references.py`. Record in that
      test's docstring why: the disjunction bug, and that the correction buys
      correctness rather than volume.
- [x] 1.4 [P1] [req: body-content] Raise the rendered-body ceiling from 150 to
      160 in `body-content`, which owns it — prose and scenario both — and in
      both assertions in
      `plugins/s/skills/build/tests/test_harness_bodies.py`. Record the same
      reason in that docstring. Do not restate either figure anywhere else.
- [x] 1.5 [P1] [req: review-skill] Bump
      `plugins/s/.claude-plugin/plugin.json` from 0.6.278 to 0.6.280 — 0.6.279
      is taken by `spec-owned-wording-drifts`, in review on its own branch.
- [x] 2.1 [P2] [req: review-skill] Confirm the two reference files need no
      edit, by reading them rather than assuming:
      `plugins/s/skills/review/references/pr-description.md` and
      `plugins/s/skills/review/references/risk-lenses.md` must each defer to
      the review skill's general further-location permission rather than
      granting their own, so both inherit the new condition. If either grants
      its own permission, it needs the condition too and this task is a
      finding, not a check.
- [x] 2.2 [P2] [req: review-skill] Confirm the packaging case still qualifies:
      its primary is a manifest line and its further location is an import in a
      different file, so it lies outside the primary's function and hunk. This
      is the case a careless reading of the new condition would break, and it
      is pinned by a new scenario.
- [x] 3.1 [P3] [req: review-skill] Verify. Run the review suite and the build
      suite, reading each verdict with
      `grep -E "^(OK|FAILED|ERROR)|^Ran [0-9]+ tests"` over a captured log
      rather than tailing it, and never run a suite concurrently with a probe
      that mutates a file. Confirm the change lints clean and check each delta
      scenario against the real files.
- [x] 3.2 [P3] [req: review-skill] Confirm the diff is only what it claims:
      exactly three files under `plugins/` — `SKILL.md`, the harness body and
      `plugin.json` — plus the change's own artifacts. On the two prose
      surfaces every hunk must be the distance condition and nothing else; in
      particular the three further-location shapes, the severity rubric and the
      breadth sweep must be unchanged context, since a wording change riding
      along inside a hunk is a defect this series has shipped before.
