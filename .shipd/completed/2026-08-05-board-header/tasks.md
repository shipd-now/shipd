# board-header tasks

## 1. Pure helpers

- [x] 1.1 [req: board-tui, board-epic-grouping] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py` add
      `AutopilotLiveTest` — `autopilot_live(board, now=...)` is true for an
      epic heartbeat with `state: "running"` and a fresh `updated_at`; false
      for `finished`, for a missing heartbeat/`updated_at`, and for `running`
      older than 3600 s — and `InitiativeGroupTitleTest` —
      `initiative_group_title({"slug": "s", "status": "active"})` is
      `"s [active]"`, `initiative_group_title(None)` is `"workspace"`. Run the
      two classes and observe them fail (helpers do not exist yet).
- [x] 1.2 [req: board-tui, board-epic-grouping] In
      `plugins/s/skills/build/scripts/dashboard.py`'s pure-renderers section
      (near `epic_stalled`) add `AUTOPILOT_FRESH_SECONDS = 3600`,
      `autopilot_live(board, now=None)`, and `initiative_group_title(
      initiative)` exactly as `plan.md` specifies; confirm the 1.1 tests pass.

## 2. Grouping mode and initiative groups

- [x] 2.1 [req: board-epic-grouping, board-command-palette] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, rewrite the
      boolean-grouping tests to
      the mode contract: default `app.group_mode == "epic"`; pressing `g`
      cycles epic → initiative → none → epic with a lane repaint at each step;
      `_lane_signature` differs across the three modes (replace its
      `group_by_epic=` kwarg uses); the palette grouping command advances
      `epic` → `initiative` through the same path as `g`. Add an
      initiative-mode test: two epics sharing an initiative render under one
      collapsible header titled `"<slug> [<status>]"`, a no-initiative epic's
      cards under a `workspace` group, and no initiative header mounts a run
      or open button. Run and observe the new/rewritten tests fail.
- [x] 2.2 [req: board-epic-grouping] In `dashboard.py` add
      `GROUP_MODES = ("epic", "initiative", "none")`; replace
      `self.group_by_epic` with `self.group_mode = "epic"`; change
      `_lane_signature`'s second parameter to the mode string; branch
      `_render_lanes` per mode (`epic` → `_mount_epic_groups`, `initiative` →
      `_mount_initiative_groups`, `none` → flat).
- [x] 2.3 [req: board-epic-grouping] In `dashboard.py` add
      `_mount_initiative_groups(lane, lane_name, cards)` per `plan.md`:
      walk `self.board["groups"]` in order, collect each group's epics' card
      specs from the lane's filtered list, mount one `Collapsible`
      (`classes="epic-group lane-item"`,
      `id="init-group-<lane>-<slug or workspace>"`,
      `collapsed=False`) titled by `initiative_group_title`, cards as
      `TaskCard`s with the active `search_query`; mount nothing for a group
      with no kept cards.
- [x] 2.4 [req: board-epic-grouping, board-command-palette] In `dashboard.py`
      replace `action_toggle_grouping`/`on_checkbox_changed` with
      `action_cycle_grouping` (the `g` binding, description `Group`) and
      `_set_group_mode(mode)` updating the mode buttons' `mode-active` class
      and awaiting `_render_lanes()`; route `group_mode_value`-carrying
      buttons in `on_button_pressed` before the epic-slug checks; change the
      palette `SystemCommand` to ("Cycle grouping", cycling description,
      `self.action_cycle_grouping`). Confirm the 2.1 tests pass.

## 3. Header bar chrome

- [x] 3.1 [req: board-tui, board-search] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py` amend the
      chrome tests: the mounted app contains `#header-bar` holding
      `#brand`, `#board-search-input`, `#board-search-clear`,
      `#board-search-count`, the three `#group-mode-*` buttons with
      `mode-active` on the current mode, `#autopilot-indicator`, and
      `HeaderChart` — and no stock textual `Header`, no `#controls-strip`, no
      `Checkbox`; `/` still focuses the header-bar search input; the indicator
      shows `autopilot on` under a fresh `running` heartbeat board and the
      idle marker otherwise (drive both through `refresh_board` with a stubbed
      `board_fn`). Run and observe the new assertions fail.
- [x] 3.2 [req: board-tui] In `dashboard.py` rewrite `BoardApp.compose` and
      CSS per `plan.md`: drop `yield Header()` and the controls strip; yield
      the three-zone `#header-bar` (brand `Static`, centered
      `#search-cluster` re-homing the search widgets unchanged, `#group-mode`
      buttons, `#autopilot-indicator`, `HeaderChart`); add the
      `.mode-button`/`.mode-active` and zone CSS; remove the now-unused
      `Checkbox` and `Header` imports.
- [x] 3.3 [req: board-tui] In `dashboard.py` update `refresh_board` to repaint
      `#autopilot-indicator` from `autopilot_live(self.board)` with the
      query-empty-safe loop and the exact live/idle markup in `plan.md`;
      confirm the 3.1 tests pass.

## 4. Ship gate

- [x] 4.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version
      0.6.52 → 0.6.53.
- [x] 4.2 [req: *] Run the full `plugins/s/skills/build/tests_textual/`
      suite (venv with `textual`) and the stdlib `python3 -m unittest discover
      -s plugins/s/skills/build/tests` (no `textual`); both must pass clean.
