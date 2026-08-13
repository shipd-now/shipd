## 1. Dependency, constitution, and engine split (keep the engine textual-free)

- [x] 1.1 [req: board-tui] Add a repo-root `requirements.txt` pinning `textual`
      to a compatible range around the latest stable release (resolve the exact
      current version with `pip index versions textual` or `pip install textual`
      and pin e.g. `textual>=X,<X+1`).
- [x] 1.2 [req: board-tui] Amend `.shipd/constitution.md`'s stdlib-only technology
      constraint to name `dashboard.py`'s `tui` rendering as the sole third-party
      exception (may import the pinned `textual`), with every other engine script
      remaining stdlib-only and import-safe without it; note `textual` is pinned
      in `requirements.txt` and installed in CI only for the textual suite.
- [x] 1.3 [req: board-tui] Create `plugins/s/skills/build/scripts/heartbeat.py`
      and move `RunHeartbeat` and `heartbeat_path` (and any private helpers they
      need) there from `dashboard.py`, unchanged in behavior (stdlib only).
- [x] 1.4 [req: board-tui] Update `autopilot.py` to import `RunHeartbeat`/
      `heartbeat_path` from `heartbeat` instead of `dashboard`, and update
      `plugins/s/skills/build/tests/test_autopilot.py` accordingly. Confirm
      `python3 -c "import autopilot"` succeeds with `textual` NOT installed.
- [x] 1.5 [req: board-tui] In `.github/workflows/ci.yml`, run the existing
      dependency-free suites against `plugins/s/skills/build/tests` (and the
      review tests) as today, then add a step that `pip install -r
      requirements.txt` and runs a new `plugins/s/skills/build/tests_textual`
      suite.
- [x] 1.6 [req: board-tui] Document the dependency in `AGENTS.md`: the board TUI
      requires `textual` (`pip install -r requirements.txt`); the engine and
      other suites stay dependency-free.

## 2. Replace curses with the textual app skeleton

- [x] 2.1 [req: board-tui] Move the dashboard tests that import `dashboard` from
      `tests/test_dashboard.py` into `plugins/s/skills/build/tests_textual/
      test_dashboard.py`; delete the tests covering the curses layout
      (`layout_board`/`_place_card`/`region_at`/`_tui_*`) since that code is being
      removed.
- [x] 2.2 [req: board-tui] In `tests_textual/test_dashboard.py`, add a `textual`
      `App.run_test` test asserting the mounted app's widget tree contains a
      header, footer, the hierarchy panel, and the five named lifecycle lanes, and
      that a member maps to a focusable task-card in its lane. Run it (with
      `textual` installed) and observe failure.
- [x] 2.3 [req: board-tui] In `dashboard.py`, delete the curses board
      (`layout_board`, `_place_card`, `region_at`, `_tui_init_colors`,
      `_tui_paint`, `_tui_focusables`, `_tui_dispatch`, `_tui_handle_mouse`,
      `_cmd_tui`'s curses loop) and add the `textual` App with `Header`/`Footer`,
      inline `CSS`, a collapsible hierarchy `Tree` panel, five bordered `Lane`
      (VerticalScroll) columns, and focusable `TaskCard` widgets built from
      `build_board`. Keep `build_board`/`member_actions`/launch builders intact.
- [x] 2.4 [req: board-tui] Reimplement the `tui` verb to launch the App (passing
      `--root`/`--epic`/`--interval`); when `textual` is not importable, print a
      `pip install -r requirements.txt` hint and exit non-zero. Confirm 2.2
      passes.

## 3. Interaction parity — focus, panel, modal

- [x] 3.1 [req: board-tui] In `tests_textual/test_dashboard.py`, add `Pilot`
      tests: the focused task-card shows the focused state; `Enter` on a focused
      card pushes a member-detail `ModalScreen`; the panel-toggle and `q` bindings
      are registered. Run and observe failure.
- [x] 3.2 [req: board-tui] In `dashboard.py`, wire arrow-key spatial focus across
      cards/lanes, the `TaskCard` focus highlight and left risk accent bar (via
      `CSS` `:focus`), a `ModalScreen` detail screen opened by `Enter`, and
      `App.BINDINGS` for panel-toggle and quit so the footer renders them. Confirm
      3.1 passes.

## 4. Collapse parity — hierarchy nodes and shipped groups

- [x] 4.1 [req: board-tui] In `tests_textual/test_dashboard.py`, add `Pilot`
      tests: collapsing an epic node in the hierarchy tree hides its change nodes
      while siblings stay expanded; collapsing a `shipped` per-epic group hides
      that epic's cards while another group stays visible; shipped group headers
      are coloured by epic status. Run and observe failure.
- [x] 4.2 [req: board-tui] In `dashboard.py`, implement per-node collapse in the
      hierarchy `Tree` and collapsible per-epic groups in the `shipped` lane
      (headers coloured by epic status). Confirm 4.1 passes.

## 5. Live refresh and RUN/PLAN/OPEN actions

- [x] 5.1 [req: board-actions] In `tests_textual/test_dashboard.py`, add tests
      that a task-card's action handler resolves through the existing pure
      builders — `plan` under `$TMUX` builds a `tmux new-window`, `run` builds a
      detached single-member driver argv, `open` on a parked card builds `claude
      --resume <id>`, and `open` is absent while driving. Run and observe failure.
- [x] 5.2 [req: board-actions] In `dashboard.py`, surface the eligible
      RUN/PLAN/OPEN actions on each `TaskCard` (and an epic-level run), dispatching
      through `member_actions`/`resolve_action_launch`/`build_*_launch`: detached
      `run` via `subprocess.Popen`; interactive `plan`/`open` via `tmux
      new-window` when `$TMUX` is set else `App.suspend()`. Confirm 5.1 passes.
- [x] 5.3 [req: board-tui] In `dashboard.py`, add live auto-refresh: on
      `--interval` (default 2) via `set_interval`, re-aggregate `build_board` and
      update the lanes/panel so a live run's transitions appear. Add a
      `tests_textual` test driving one refresh through the harness and confirm the
      lanes reflect the new states.

## 6. Version bump & verification

- [x] 6.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json` to the next unused version above the
      branch base (base is 0.6.24, so 0.6.25 — pick the next free one if an
      unrelated merge took it).
- [x] 6.2 [req: *] Run the dependency-free suite `python3 -m unittest discover -s
      plugins/s/skills/build/tests` (must pass with `textual` NOT installed),
      then `pip install -r requirements.txt` and run `python3 -m unittest discover
      -s plugins/s/skills/build/tests_textual`; both green.
- [x] 6.3 [req: *] Manually launch `python3
      plugins/s/skills/build/scripts/dashboard.py tui` (with `textual`
      installed) and confirm the hierarchy panel, five bordered lanes, focusable
      cards, focus highlight, Enter-modal, collapse, and the footer bindings all
      render and work.
