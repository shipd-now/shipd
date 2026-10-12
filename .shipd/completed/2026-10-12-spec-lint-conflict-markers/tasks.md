# Tasks

- [x] 1.1 [P1] [req: conflict-marker-rejection] Add
      `check_no_conflict_markers(text, location, errors)` to
      `plugins/s/skills/build/scripts/spec_lint.py`, reporting every line that
      starts `<<<<<<<` or `>>>>>>>`, plus a line equal to `=======`, with the
      file and line number. Match `=======` as a whole line only — a markdown
      setext heading underlines with repeated `=`, and a prefix match would
      reject valid documents. Report through `LintError`, never
      `LintWarning`: a warning leaves the exit code clean and the exit code is
      what the `ci` gate reads.
- [x] 1.2 [P1] [req: conflict-marker-rejection] Wire it into
      `lint_master_spec`, `lint_delta_spec`, and `lint_change` for that
      change's `plan.md` and `tasks.md`.
- [x] 2.1 [P2] [req: conflict-marker-rejection] Add tests to
      `plugins/s/skills/build/tests/test_spec_lint.py` covering each delta
      scenario: a master spec with a marker is rejected, a delta spec with a
      marker is rejected, a `plan.md` or `tasks.md` with a marker is rejected,
      and a setext heading underline is **not** reported. The setext case is
      the one that matters most — it is the regression this check could
      introduce — so assert on it directly rather than trusting the whole-line
      match by inspection.
- [x] 2.2 [P2] [req: board-metrics-view] Apply the MODIFIED
      `delivery-dashboard` delta, restating `board-metrics-view` and
      `board-scrollbar-theme` without their marker lines. Confirm afterwards
      that the file carries no line starting `<<<<<<<` or `>>>>>>>`, that it
      still holds 32 requirements, and that no `id:` is duplicated.
- [x] 2.3 [P2] [req: conflict-marker-rejection] Bump
      `plugins/s/.claude-plugin/plugin.json` from 0.6.277 to 0.6.278.
- [x] 3.1 [P3] [req: conflict-marker-rejection] Verify everything the merge
      does not gate. Capture the **pre-repair** library lint: with the check
      wired in and `.shipd/verified/` still carrying both markers, it must
      report each by line number and exit non-zero — that is the proof the
      check detects the real defect, and it is only observable before the
      merge. Then run the build suite and the review suite, reading each
      verdict with `grep -E "^(OK|FAILED|ERROR)|^Ran [0-9]+ tests"` over a
      captured log rather than tailing it, and never run a suite concurrently
      with a probe that mutates a file. Confirm the delta itself carries no
      marker line.
      **The post-repair lint is not a task.** It can only pass once
      `spec_merge.py` has applied the delta, and the engine refuses to stamp
      `verified` while any task is open — so a task asserting it could never
      be completed. It is a post-merge confirmation, reported in the build
      report and the pull request, not a checkbox.
- [x] 3.2 [P3] [req: conflict-marker-rejection] Confirm no `/s:review` prose
      surface changed: nothing under `plugins/s/skills/review/` outside its
      tests directory, and nothing under `plugins/s/harness/` or
      `plugins/s/integrations/`, may differ from the main branch. A
      measurement is calibrated against v0.6.277's review prompt.
