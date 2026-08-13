# Tasks

## 1. Summary pointer fix

- [x] 1.1 [req: run-report-and-controls] In
      `plugins/s/skills/build/tests/test_autopilot.py`, add failing tests for
      `_summarize`: a needs-human entry with `session_id: None` renders no
      `claude --resume` fragment; an entry with a session id still renders the
      pointer.
- [x] 1.2 [req: run-report-and-controls] In
      `plugins/s/skills/build/scripts/autopilot.py`, make `_summarize` append
      the needs-human resume pointer only when the entry carries a session id
      (mirror the rejected branch); confirm the 1.1 tests pass.

## 2. Close-out invocation and worktree hygiene

- [x] 2.1 [req: run-report-and-controls] In `test_autopilot.py`, add failing
      tests for `_default_sync_fn` with a faked `_run_command` recording
      calls: (a) the spec_status invocation places `--root <wt>` before
      `epic-sync <epic>`; (b) a zero-exit sync with empty
      `git status --porcelain` output triggers `git worktree remove` of the
      close-out worktree and deletion of its `change/epic-close-<epic>`
      branch; (c) a zero-exit sync with non-empty porcelain output triggers no
      removal and prints a line naming the worktree path; (d) a failed
      worktree creation still prints the existing skip message and runs no
      sync.
- [x] 2.2 [req: run-report-and-controls] In `autopilot.py`, implement the
      `_default_sync_fn` changes per the plan: reorder the CLI invocation,
      then on success check `git status --porcelain` in the worktree and
      either clean up (empty) or print the ship-from-here pointer (non-empty),
      routing every subprocess through `_run_command`; confirm the 2.1 tests
      pass.

## 3. Version and verification

- [x] 3.1 [req: *] Bump the patch version in
      `plugins/s/.claude-plugin/plugin.json`.
- [x] 3.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` from the repo root and observe an
      all-green run.
