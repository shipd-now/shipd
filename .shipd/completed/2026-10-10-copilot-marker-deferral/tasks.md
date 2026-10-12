# Tasks

- [x] 1.1 [P1] [req: skill-template] Apply the MODIFIED `skill-template` delta
      so `.shipd/verified/copilot-review-skill/spec.md` defers the verdict
      marker's reader semantics to `gate-workflow-template` and drops the
      residual rubric clause. Confirm the merged requirement contains neither
      "last non-empty" nor "pure style".
- [ ] 2.1 [P2] [req: skill-template] Add the rubric-parity guard to
      `plugins/s/skills/review/tests/test_skill_references.py`: the copilot
      template's `low` definition, impact floor and three instances match
      `plugins/s/skills/review/SKILL.md`, on whitespace-normalised text. Prove
      it non-vacuous by reverting the copilot template's rubric to a wording
      that disagrees and watching it fail, with the file otherwise intact —
      record the byte count before and after, since a truncating probe gives a
      failure that proves nothing.
- [ ] 2.2 [P2] [req: skill-template] Add the no-restatement guard to the same
      file: `skill-template`'s own text in
      `.shipd/verified/copilot-review-skill/spec.md` carries neither the
      rubric's `low` wording nor the reader's semantics. Prove it non-vacuous
      against the pre-change requirement text, which contains "last non-empty
      line by exact equality" — it must fail there and pass now.
- [ ] 2.3 [P2] [req: skill-template] Bump
      `plugins/s/.claude-plugin/plugin.json` from 0.6.276 to 0.6.277.
- [ ] 3.1 [P3] [req: skill-template] Verify. Run the review suite and the build
      suite, reading each verdict with
      `grep -E "^(OK|FAILED|ERROR)|^Ran [0-9]+ tests"` over a captured log
      rather than tailing it. Never run the build suite at the same time as a
      probe that mutates a file — that produced a spurious failure on an
      earlier pull request. Confirm the full library lint passes and check each
      delta scenario against the real files.
- [ ] 3.2 [P3] [req: skill-template] Confirm the review path's prose is
      untouched: no file under `plugins/s/skills/review/` except the tests
      directory, and no file under `plugins/s/harness/`, may differ from the
      main branch. A measurement is calibrated against v0.6.276's review
      prompt, so a stray edit there invalidates it.
