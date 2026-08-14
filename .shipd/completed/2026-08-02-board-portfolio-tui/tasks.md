## 1. Board aggregation — initiative grouping & action eligibility

- [x] 1.1 [req: board-aggregation] In `plugins/s/skills/build/tests/test_dashboard.py`,
      add tests: `build_board` groups epics under their initiative (two epics
      sharing an `Initiative:` land in one group; an epic with none lands in a
      workspace-wide group), and each member carries an `actions` list (`plan`
      for unplanned, `run` for ready, `open` for a parked member with a session
      id). Run them and observe failure.
- [x] 1.2 [req: board-aggregation] In `dashboard.py`, extend `_epic_board` /
      `build_board` to emit an initiative-grouped structure (workspace-wide bucket
      for epics with no `Initiative:`) while preserving the existing per-epic
      fields, worktree-aware member states, heartbeat merge, and `--json` output.
- [x] 1.3 [req: board-aggregation] In `dashboard.py`, add a pure
      `member_actions(member, heartbeat_entry)` helper returning the eligible
      action slugs (`plan`/`run`/`open`) and attach its result plus the member's
      `session_id` (from the heartbeat roster / report) to each member row.
- [x] 1.4 [req: board-aggregation] Update `render_board_lines` / the text `board`
      verb to print the initiative group headers above their epics; confirm
      `test_dashboard.py` from 1.1 passes.

## 2. Heartbeat session id on turn 1

- [x] 2.1 [req: autopilot-heartbeat] In
      `plugins/s/skills/build/tests/test_session_driver.py`, add a test that
      `drive` invokes an `on_session` callback with the session id the first time
      a turn yields one, before the loop ends. Run it and observe failure.
- [x] 2.2 [req: autopilot-heartbeat] In `session_driver.py`, add an optional
      `on_session` callback to `drive`, fired once when a turn first returns a
      non-None session id.
- [x] 2.3 [req: autopilot-heartbeat] In
      `plugins/s/skills/build/tests/test_autopilot.py`, add a test that the
      heartbeat roster entry for a driving member carries `session_id` before the
      member reaches a terminal outcome. Run it and observe failure.
- [x] 2.4 [req: autopilot-heartbeat] In `dashboard.py` (`RunHeartbeat`), add a
      `member_session(slug, session_id)` transition that records the id on the
      roster entry; in `autopilot.py`, thread `on_session` from the session seam
      into that transition. Confirm 2.1 and 2.3 pass.

## 3. Targeted single-member drive

- [x] 3.1 [req: targeted-member-drive] In `test_autopilot.py`, add tests: a
      targeted drive of a `ready` member enters the pipeline at `build` (plan and
      gate skipped); of an `unplanned` member enters at `plan`; and normal
      epic-level selection/order is unchanged. Run them and observe failure.
- [x] 3.2 [req: targeted-member-drive] In `autopilot.py`, add a pure
      `entry_stage(member_state)` mapping (`unplanned`->plan, `ready`->build) and
      a `drive_single_member(root, epic, slug, ...)` entry that selects the one
      member, computes its entry stage, and runs the existing pipeline loop from
      there, reusing the worktree/grade/park semantics.
- [x] 3.3 [req: targeted-member-drive] Add a `--member <slug>` CLI option to
      `autopilot.py` `main` that routes to `drive_single_member`; confirm 3.1
      passes and epic-level runs still work.

## 4. Pure board layout model (hierarchy panel + kanban + regions)

- [x] 4.1 [req: board-tui] In `test_dashboard.py`, add tests for a pure
      `layout_board(board, *, panel_open, width)` returning positioned lines and
      clickable regions: a driving member's card lands in the `building` column
      with its risk chip; collapsing flips the toggle to `[>]` and widens the
      kanban; regions include the panel toggle, tree rows, and card buttons. Run
      and observe failure.
- [x] 4.2 [req: board-tui] In `dashboard.py`, implement `layout_board`: build the
      collapsible hierarchy panel (initiative → epic → change, theme as a label)
      and the lifecycle kanban (`unplanned`/`ready`/`building`/`review`/`shipped`)
      with colour keys per state and per-card action buttons, emitting each
      drawable as a positioned line and each interactive element as a region with
      its bounds, target member/epic, and action. Confirm 4.1 passes.

## 5. Interactive curses TUI

- [x] 5.1 [req: board-tui] Rewrite the `tui` verb in `dashboard.py` to paint
      `layout_board` output with `curses` colour pairs keyed by lifecycle state,
      keeping `curses` imported lazily; support arrow-key navigation, Enter to
      act/expand, a key to toggle the panel, and `q` to quit; re-aggregate and
      redraw every `--interval` seconds.
- [x] 5.2 [req: board-tui] Add mouse support to the `tui` verb via
      `curses.mousemask`: on `KEY_MOUSE`, hit-test the click against
      `layout_board`'s regions and dispatch the matching selection/action; when
      the terminal reports no mouse, run keyboard-only without error.

## 6. Board action launchers (PLAN / RUN / OPEN)

- [x] 6.1 [req: board-actions] In `test_dashboard.py`, add tests for pure launch
      builders: `plan` under `$TMUX` builds a `tmux new-window` running `/s:plan`
      in the member's worktree (no suspend); `run` on a ready member builds a
      detached single-member driver argv; `open` on a parked member builds
      `claude --resume <id>`; `open` is absent for a driving member. Run and
      observe failure.
- [x] 6.2 [req: board-actions] In `dashboard.py`, implement the pure launch
      builders (`build_plan_launch`, `build_run_launch`, `build_open_launch`)
      returning argv plus a `tmux`/`suspend`/`detach` mode, honoring `$TMUX` for
      interactive actions. Confirm 6.1 passes.
- [x] 6.3 [req: board-actions] Wire the builders into the `tui` dispatch: detached
      `run` via `subprocess.Popen`; interactive `plan`/`open` via `tmux
      new-window` when `$TMUX` is set, else suspend curses (`endwin`), run, and
      restore the board on return.

## 7. Version bump & full verification

- [x] 7.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json` (0.6.20 -> 0.6.21), since this
      change touches `plugins/s/`.
- [x] 7.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` and confirm the whole suite passes.
- [x] 7.3 [req: *] Manually launch `python3
      plugins/s/skills/build/scripts/dashboard.py tui` against this repo and
      confirm the interactive board renders in colour, the `[<]`/`[>]` toggle
      collapses the panel by key and click, and cards show the expected
      PLAN/RUN/OPEN buttons per lifecycle state.
