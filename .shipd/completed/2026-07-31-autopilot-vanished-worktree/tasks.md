## 1. Session driver tolerates a missing cwd

- [x] 1.1 [req: shared-session-driver] In
      `plugins/s/skills/build/tests/test_session_driver.py`, add a test
      calling `run_turn("p", <nonexistent dir>)` with a stub
      `claude_bin` (any string — Popen must fail on the cwd before the
      binary matters): it returns `ok=False`, a failure string containing
      the missing directory path, and `session_id=None`, raising nothing.
      Run the file and observe the new test fail (today it raises
      `FileNotFoundError`).
- [x] 1.2 [req: shared-session-driver] In
      `plugins/s/skills/build/scripts/session_driver.py`, wrap
      `run_turn`'s `subprocess.run` in `except OSError` (alongside the
      existing `TimeoutExpired` handler) returning
      `(False, "working directory missing: <cwd>: <exc>", None)`.
      Confirm the 1.1 test passes.

## 2. Autopilot resolves a vanished worktree

- [x] 2.1 [req: pipeline-stage-execution] In
      `plugins/s/skills/build/tests/test_autopilot.py`, add tests using
      the existing fake `session_fn`/`command_fn` seams: (a) a build
      stage whose fake session removes the member's worktree directory
      and whose fake `command_fn` answers the `gh pr view` probe with a
      URL and `MERGED` → `drive_member` returns outcome `shipped` with
      that URL, and a following pipeline stage (e.g. `review`) never
      runs; (b) same removal but the probe reports no merged PR →
      outcome `needs_human` with a reason containing
      `worktree vanished` and the last session id preserved. Run the
      file and observe the new tests fail.
- [x] 2.2 [req: pipeline-stage-execution] In
      `plugins/s/skills/build/scripts/autopilot.py`: give `_pr_url` an
      explicit directory parameter driven through `command_fn`; add a
      `_resolve_vanished(root, slug, last_session_id, stage,
      command_fn)` helper implementing merged→`shipped` /
      otherwise→`needs_human` (reason `worktree vanished mid-run`); in
      `drive_member`'s pipeline loop check `os.path.isdir(cwd)` at the
      top of each entry iteration and after any failed stage action,
      routing to the helper; switch the end-of-pipeline `_pr_url` call
      to the repo root. Keep the existing offline-test guard semantics
      (the probe goes through `command_fn`). Confirm the 2.1 tests pass.

## 3. Ship gate

- [x] 3.1 [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` to the next free patch
      above `origin/main`'s current value (0.6.6 as of planning).
- [x] 3.2 [req: *] Verification barrier: run
      `python3 -m unittest discover -s plugins/s/skills/build/tests`
      from the repo root and observe zero failures; then run
      `python3 plugins/s/skills/build/scripts/autopilot.py <any-epic>
      --dry-run` and observe it still prints the member order and report
      skeleton without error.
