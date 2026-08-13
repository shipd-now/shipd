# Tasks

## 1. Build heartbeat writer

- [x] 1.1 [req: build-heartbeat-cli] Add
      `plugins/s/skills/build/tests/test_build_heartbeat.py` covering:
      `build-start` writes a `running` heartbeat with `kind: build`, the
      session id from `CLAUDE_CODE_SESSION_ID`, and the invoking cwd as
      `location`; `build-stage --stage implement` records the stage with a
      `seq` above the start write's; `build-finish --outcome shipped` records
      `finished`/`shipped`; no `--session-id` and no env var writes no
      `session_id` field; an unwritable destination exits 0 with a stderr
      warning. Run the file and observe it fail — the verbs do not exist yet.
- [x] 1.2 [req: build-heartbeat-cli] In
      `plugins/s/skills/build/scripts/heartbeat.py`, add
      `build_heartbeat_path(root, slug)` (`<content-dir>/autopilot/
      <slug>-build-heartbeat.json`) and an argparse `main` with verbs
      `build-start <slug>`, `build-stage <slug> --stage <name>`,
      `build-finish <slug> [--outcome <outcome>]`, options `--root`
      (default cwd), `--location` (default cwd abspath), `--session-id`
      (default `$CLAUDE_CODE_SESSION_ID`). Each verb loads the existing JSON
      when present, applies its transition, bumps `seq`, stamps `updated_at`,
      and atomically replaces via the same temp-file + `os.replace` shape as
      `RunHeartbeat._write`; any `OSError` warns on stderr and exits 0.
      Confirm 1.1 passes.

## 2. Board aggregation and pure predicates

- [x] 2.1 [req: board-tui] In `plugins/s/skills/build/tests/`, extend the
      dashboard tests: `build_board` attaches a `running` build heartbeat to
      its slug-matching member (standalone and epic member alike) with an
      aggregation-stamped transcript mtime when one resolves; a pure
      `activity_counts(board, now)` returns `(live_runs, live_builds)`
      honoring the 3600s run window and the 600s build window (newer of
      `updated_at`/transcript mtime); a pure `indicator_marker(board, now)`
      yields `autopilot on`, `autopilot (2)`, `building`, `building (2)`,
      and the idle marker by precedence. Run and observe failures.
- [x] 2.2 [req: board-tui] In
      `plugins/s/skills/build/scripts/dashboard.py`, implement the
      aggregation attach (`*-build-heartbeat.json` discovery in the content
      dir's `autopilot/`, matched to members by slug, transcript mtime
      stamped via `_resolve_member_session` + `os.path.getmtime`),
      `activity_counts`, and `indicator_marker` (keeping `autopilot_live`
      delegating to the run count for statusline parity); wire
      `refresh_board`'s marker to `indicator_marker`, rendering `building`
      in the building lane's theme colour. Confirm 2.1 passes.
- [x] 2.3 [req: board-throughput-chart] Extend the dashboard tests:
      `driving_session_keys` also yields the `(tdir, session_id)` key for a
      member with a live build heartbeat (explicit session id first, else
      newest transcript for the heartbeat's location), deduplicates a session
      appearing twice, and excludes a stale (`>600s`) build heartbeat. Run
      and observe failures.
- [x] 2.4 [req: board-throughput-chart] In `dashboard.py`, extend
      `driving_session_keys` to include live-build members via
      `_resolve_member_session(heartbeat location or member location,
      heartbeat session_id)`, deduplicating keys. Confirm 2.3 passes.
- [x] 2.5 [req: board-tui] In
      `plugins/s/skills/build/tests_textual/`, update the autopilot
      indicator rendering test to the new marker text and add a case where a
      live build heartbeat renders the `building` marker.

## 3. Build skill heartbeat protocol

- [x] 3.1 [req: build-heartbeat-cli] In `plugins/s/skills/build/SKILL.md`,
      add the heartbeat protocol: run `heartbeat.py build-start <change>`
      right after the change moves to `active`, `build-stage` at each stage
      transition (implement / verify / review / merge), and `build-finish`
      with the outcome at merge/archive or park; note every call is
      fail-soft and never blocks the build.

## 4. Skill rename deliver → autopilot

- [x] 4.1 [req: deliver-skill] `git mv plugins/s/skills/deliver
      plugins/s/skills/autopilot`; in its `SKILL.md` set the frontmatter
      `name: autopilot`, retitle the heading `/s:autopilot`, and update the
      description/trigger phrases keeping `deliver` among them.
- [x] 4.2 [req: deliver-skill] Sweep remaining `am:deliver` / `/s:deliver`
      references (other skills' SKILL.md files, `evals/`, docs) to
      `/s:autopilot`, leaving `.shipd/completed/` archives untouched.

## 5. Ship gates

- [x] 5.1 [req: *] Bump the version in
      `plugins/s/.claude-plugin/plugin.json`.
- [x] 5.2 [req: *] Verification barrier: `python3 -m unittest discover -s
      plugins/s/skills/build/tests` passes without `textual`; the
      `tests_textual` suite passes with `textual` installed; with a live
      interactive build running, `dashboard.py tui` shows the `building`
      marker and a non-blank throughput chart.

## 6. Worktree heartbeat discovery (verification finding)

- [x] 6.1 [req: build-heartbeat-cli] In
      `plugins/s/skills/build/tests/test_board_activity.py`, add coverage:
      `_discover_build_heartbeats` (and `attach_build_heartbeats` through it)
      finds a running heartbeat under
      `.worktrees/<name>/.shipd/autopilot/*-build-heartbeat.json` when the
      invocation root's own `autopilot/` has none, and — when both roots carry
      a heartbeat for the same slug — the one with the newest `updated_at`
      wins. Run and observe the failures.
- [x] 6.2 [req: build-heartbeat-cli] In
      `plugins/s/skills/build/scripts/dashboard.py`, extend
      `_discover_build_heartbeats(root)` to also glob every
      `.worktrees/*/<content-dir>/autopilot/*-build-heartbeat.json` (resolving
      each worktree's content dir the way `standalone_changes` does),
      newest-`updated_at`-wins on a contested slug. Confirm 6.1 passes.
