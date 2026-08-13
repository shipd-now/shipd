# Tasks — delivery-dashboard

## 1. Heartbeat instrumentation

- [x] 1.1 [req: autopilot-heartbeat] Add
      `plugins/s/skills/build/tests/test_dashboard.py` with heartbeat tests:
      `RunHeartbeat` writes `<content-dir>/autopilot/<epic>-heartbeat.json`
      atomically under a tmpdir root; each transition method bumps `seq`,
      updates `updated_at`, and records the roster state (`pending` →
      `driving` with stage/attempt → outcome); a needs-human
      `member_finished` records stage, reason, and session id; a write
      failure (unwritable directory) warns once via the `out` callback and
      never raises. Run the tests and observe them fail — `dashboard.py`
      does not exist yet.
- [x] 1.2 [req: autopilot-heartbeat] Create
      `plugins/s/skills/build/scripts/dashboard.py` (stdlib only) with the
      `RunHeartbeat` class per the plan: one state dict, transition methods
      `run_started` / `member_started` / `stage_started` / `member_finished`
      / `run_finished`, atomic temp-file + `os.replace` writes, monotonic
      `seq`, epoch `updated_at`, warn-once-and-disable on write failure.
      Confirm the 1.1 tests pass.
- [x] 1.3 [req: autopilot-heartbeat] In
      `plugins/s/skills/build/scripts/autopilot.py`, add a
      `heartbeat=None` keyword seam to `run` and `drive_member`: `run`
      constructs a live `RunHeartbeat` when the seam is `None` and the run
      is not `--dry-run`; call the transition methods at run start, member
      start, each stage attempt (including gate, replacement, and custom
      entries), member outcome, and run end. `None` in `drive_member`
      means no writes.
- [x] 1.4 [req: autopilot-heartbeat] In
      `plugins/s/skills/build/tests/test_autopilot.py`, drive a seam-based
      run (existing fake `session_fn`/`gate_fn`/`command_fn`) against a
      tmpdir root and assert the heartbeat file reflects run start, a
      driving stage, member outcomes, and run end; assert `--dry-run`
      creates no heartbeat file.
- [x] 1.5 [req: autopilot-heartbeat] Add `.shipd/autopilot/` to the repo root
      `.gitignore` (runtime state, alongside `.shipd/state.json`).

## 2. Board aggregation

- [x] 2.1 [req: board-aggregation] In `test_dashboard.py`, add board tests
      over a fixture root: an epic with theme, initiative, and a stub
      table; one member planned at the root, one member `rejected` only
      inside `.worktrees/<slug>/.shipd/planned/<slug>/`, one unplanned; a
      heartbeat and a report file. Assert the worktree member reports
      `rejected` with its worktree location, the initiative degrades to
      slug-only with no workspace, the heartbeat and report are merged,
      `--epic` scopes, and `board --json` stdout parses as one JSON
      object. Run and observe failure.
- [x] 2.2 [req: board-aggregation] In `dashboard.py`, implement
      `member_board_state(root, slug)` (root `_member_state` first, then
      locate-style `.worktrees/<slug>` probe of planned and completed with
      per-candidate config resolution), `build_board(root, epic=None)`
      returning the plan's board shape (initiative status via the
      workspace brief when `find_workspace_root` resolves, else slug-only),
      and the `board` verb (aligned text default, `--json`, `--epic`).
      Confirm the 2.1 tests pass.

## 3. Renderers — TUI and HTML

- [x] 3.1 [req: board-tui] In `test_dashboard.py`, add renderer tests:
      `render_board_lines(board)` returns lines naming the epic, each
      member, its state/stage, and heartbeat age with no terminal
      interaction; importing `dashboard` leaves `curses` out of
      `sys.modules`. Run and observe failure.
- [x] 3.2 [req: board-tui] In `dashboard.py`, implement
      `render_board_lines` (shared by the `board` verb's text mode) and the
      `tui` verb: lazy `import curses` inside the verb, redraw every
      `--interval` seconds (default 2) via `getch` timeout, quit on `q`.
      Confirm the 3.1 tests pass.
- [x] 3.3 [req: board-html] In `test_dashboard.py`, add HTML tests:
      `render_board_html(board, interval)` yields a page containing
      `<meta http-equiv="refresh" content="<interval>">`, a row per member
      with its state, and HTML-escaped dynamic values (a member description
      containing `<` renders escaped); `html --out <path> --once` writes
      the file exactly once and exits zero. Run and observe failure.
- [x] 3.4 [req: board-html] In `dashboard.py`, implement
      `render_board_html` (inline CSS only, `html.escape` on all dynamic
      values) and the `html` verb: atomic writes, default rewrite loop
      every `--interval` seconds until interrupted, `--once` snapshot.
      Confirm the 3.3 tests pass.

## 4. Skill pointer and shipping hygiene

- [x] 4.1 [req: deliver-skill] In `plugins/s/skills/deliver/SKILL.md`,
      have Phase 2 (run-controls confirmation) name the live view before
      launch: watching the run from another terminal with
      `python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/dashboard.py"
      tui --epic <epic>`.
- [x] 4.2 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version
      0.6.3 → 0.6.4 (cache snapshot is keyed by version).
- [x] 4.3 [req: *] Verification barrier: run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` from
      the repo root and confirm the whole suite passes.
