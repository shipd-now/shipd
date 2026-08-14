## 1. Writer: record identity and write a terminal aborted state

- [x] 1.1 [req: autopilot-heartbeat] In
      `plugins/s/skills/build/tests/test_heartbeat.py`, add a failing test that
      constructing a `RunHeartbeat` and calling `run_started` writes a heartbeat
      whose JSON carries a `pid` equal to `os.getpid()` and a non-empty `host`.
      Run it and observe it fail — the state dict has no `pid`/`host` yet.
- [x] 1.2 [req: autopilot-heartbeat] In
      `plugins/s/skills/build/scripts/heartbeat.py`, add `pid`
      (`os.getpid()`) and `host` (`socket.gethostname()`, importing `socket`)
      to `RunHeartbeat.__init__`'s `_state` dict so every write carries them;
      confirm 1.1 passes.
- [x] 1.3 [req: autopilot-heartbeat] In
      `plugins/s/skills/build/scripts/heartbeat.py`, add a
      `RunHeartbeat.run_aborted()` method that sets `state:"aborted"` and
      `_write()`s, mirroring `run_finished` but with no `report`.
- [x] 1.4 [req: autopilot-heartbeat] In
      `plugins/s/skills/build/tests/test_autopilot.py`, add a failing test that
      when the injected `member_driver`/`driver` seam raises `AutopilotError`
      (and, separately, `KeyboardInterrupt`) mid-drive, `run`/`run_member` leaves
      the heartbeat at `state:"aborted"`, while a clean run still ends at
      `state:"finished"` (the finally does not overwrite it). Run it and observe
      the abort cases fail.
- [x] 1.5 [req: autopilot-heartbeat] In
      `plugins/s/skills/build/scripts/autopilot.py`, wrap the drive in
      `run`/`run_member` in a `try/finally` placed past the `--dry-run` early
      return (so dry runs stay silent); the finally calls `hb.run_aborted()` only
      when the clean `run_finished` was not reached (track a `finished` flag) and
      never on a `finished` run; confirm the abort/finish cases in 1.4 pass.
- [x] 1.6 [req: autopilot-heartbeat] In
      `plugins/s/skills/build/tests/test_autopilot.py`, add a failing test that
      invoking the `SIGTERM` handler `run`/`run_member` installs writes
      `state:"aborted"` once. Run it and observe it fail.
- [x] 1.7 [req: autopilot-heartbeat] In
      `plugins/s/skills/build/scripts/autopilot.py`, in `run`/`run_member` after
      the live heartbeat is constructed, install a `signal.SIGTERM` handler
      (importing `signal`) whose closure routes into the same `hb.run_aborted()`
      abort write and restores the prior handler on exit; confirm 1.6 passes.

## 2. Reader: dead-run detection and stale lane placement

- [x] 2.1 [req: board-dead-run-detection] In
      `plugins/s/skills/build/tests/test_board_activity.py`, add a failing test
      for a new pure predicate `run_is_dead(heartbeat, now=None, host=None)` in
      `dashboard.py`: dead when `host` matches and `pid` is not a live process;
      alive when `pid` is live; and, when `host` differs, decided by
      `updated_at` vs `AUTOPILOT_FRESH_SECONDS`. Run it and observe it fail.
- [x] 2.2 [req: board-dead-run-detection] In
      `plugins/s/skills/build/scripts/dashboard.py`, add the dependency-free
      `run_is_dead` predicate (using `os.kill(pid, 0)`, `ProcessLookupError` →
      dead, `PermissionError` → alive, and `socket.gethostname()` for the
      reader host); confirm 2.1 passes.
- [x] 2.3 [req: board-dead-run-detection] In
      `plugins/s/skills/build/tests/test_board_activity.py`, add a failing test
      that `_lane_contents` (or `_member_column`) places a `driving` member of a
      dead run into `building` as a stale card carrying its death age, while a
      live run's `driving` member stays actively driving. Run it and observe it
      fail.
- [x] 2.4 [req: board-dead-run-detection] In
      `plugins/s/skills/build/scripts/dashboard.py`, thread the epic heartbeat's
      liveness (via `run_is_dead`) into `_lane_contents`/`_member_column` so a
      dead run's `driving` entry renders in `building` with a `stale` marker and
      its death age (reuse `_age`) instead of the active stage; confirm 2.3
      passes and the existing board-render tests still pass.

## 3. Release plumbing and verification

- [x] 3.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.69` to `0.6.70` (a change
      under `plugins/s/` requires a version bump so the cached snapshot
      refreshes).
- [x] 3.2 [req: *] Run the engine unittest suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) and the
      textual suite if installed, and confirm all pass — the whole heartbeat →
      board path is green with no `textual` required for the engine tests.
