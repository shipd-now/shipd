# board-filters tasks

## 1. Pure helpers

- [x] 1.1 [req: board-filter-strip] In
      `plugins/s/skills/build/tests/test_metrics_view.py` add
      `ShippedThisWeekTests` (via the existing `_load_dashboard_stdlib`
      loader, no `textual`): with an injected `now`,
      `shipped_this_week(ship_events, now)` counts only events whose
      `ship_ts` falls on/after the Monday (UTC) of `now`'s ISO week — an
      event the prior week is excluded, a `ship_ts`-less event is skipped,
      an empty list counts 0. Run and observe it fail (helper missing).
- [x] 1.2 [req: board-filter-strip] In
      `plugins/s/skills/build/scripts/dashboard.py` add
      `shipped_this_week(ship_events, now=None)` beside `metrics_view_data`
      — **above** the module-scope `textual` import — per `plan.md`;
      confirm the 1.1 tests pass.
- [x] 1.3 [req: board-filter-strip] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py` add
      `FilterMatchesTest` — `_filter_matches` with empty filters keeps
      everything; same-kind values OR; cross-kind chips AND; `risk` tests
      the member's rating, `epic` the epic slug, `initiative` the epic's
      initiative slug (a `None` initiative never matches) —
      `FilterOptionsTest` — `_filter_options(board, active)` lists risk
      tiers `high`/`medium`/`low`, then epic slugs in board order, then
      distinct initiative slugs, minus the `active` chips — and
      `SyncLabelTest` — `_sync_label` renders the s/m/h tiers and
      `"synced ?"` for `None`. Run and observe them fail.
- [x] 1.4 [req: board-filter-strip] In `dashboard.py` add `_filter_matches`,
      `_filter_options`, and `_sync_label` beside `_search_matches`, exactly
      per `plan.md`; confirm the 1.3 tests pass.

## 2. Filter state and lane filtering

- [x] 2.1 [req: board-filter-strip] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py` add
      filtering tests driven by setting `app.filters` and awaiting
      `app._render_lanes()` on a stubbed `board_fn`: a risk chip mounts only
      matching members; chips compose with an active `search_query` (both
      must keep a member); under an epic-excluding chip and `epic` grouping
      no header for that epic mounts in any lane and an emptied lane shows
      its empty-state text; `_lane_signature` differs when only `filters`
      differs; an unchanged refresh under steady chips retains the card
      widget instances while a chip change repaints. Run and observe them
      fail.
- [x] 2.2 [req: board-filter-strip] In `dashboard.py` add
      `self.filters = []` in `BoardApp.__init__`; extend `_lane_signature`
      with a trailing `filters=()` parameter appended into the signature
      header; apply `_filter_matches` alongside `_search_matches` in
      `_filtered_lane_contents`; pass `tuple(self.filters)` from
      `_render_lanes`. Confirm the 2.1 tests pass.

## 3. Strip chrome

- [x] 3.1 [req: board-filter-strip] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py` add strip
      chrome tests: the mounted app contains `#filter-strip` between
      `#header-bar` and `#body`, holding `#board-totals` with the
      full-board `"N specs · N epics · N initiatives"` counts,
      `#filter-chips` with the `#filter-add` button, `#board-shipped`, and
      `#board-synced`; with a chip active the totals text is unchanged;
      after `refresh_board` the shipped label renders
      `"▲ N shipped this week"` (monkeypatch
      `dashboard.mtr.collect_ship_events` to return fixture events) and the
      synced label a fresh `_sync_label`. Run and observe them fail.
- [x] 3.2 [req: board-filter-strip] In `dashboard.py` yield the
      `#filter-strip` row in `compose` (totals `Static`, `#filter-chips`
      `Horizontal` with the `+ filter` button, shipped and synced
      `Static`s), add its theme-variable CSS (`.filter-chip` mirroring
      `.mode-button`), and update `refresh_board` to stamp
      `self._last_sync`, call `mtr.collect_ship_events(self.root)` +
      `shipped_this_week`, and repaint the three labels through
      query-empty-safe loops, per `plan.md`. Confirm the 3.1 tests pass.

## 4. Picker flow and chips

- [x] 4.1 [req: board-filter-strip] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py` add picker
      tests: `f` pushes `FilterPickerScreen` listing `_filter_options`
      (already-active chips absent); `f` is inert while a modal is open;
      `escape` dismisses without adding; selecting an option adds the chip
      to `app.filters`, mounts its `filter-chip` button, and repaints the
      lanes filtered; pressing a chip button removes it and remounts the
      excluded members; `#filter-add` opens the same picker. Run and
      observe them fail.
- [x] 4.2 [req: board-filter-strip] In `dashboard.py` add
      `FilterPickerScreen`, the `f` binding with `action_add_filter` (inert
      unless the screen stack is the base board), `apply_filter(kind,
      value)` (append, remount `#filter-chips`, await `_render_lanes()`),
      and the chip/`#filter-add` routing in `on_button_pressed` ahead of
      the epic-slug checks, per `plan.md`. Confirm the 4.1 tests pass.

## 5. Command palette

- [x] 5.1 [req: board-command-palette] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py` extend the
      palette tests: with chips active the board-screen command source
      lists "Clear filters" (absent with no chips); its callback empties
      `app.filters`, clears the chip row, and remounts every member's card.
      Run and observe them fail.
- [x] 5.2 [req: board-command-palette] In `dashboard.py` add
      `_clear_filters()` and the conditional
      `SystemCommand("Clear filters", ...)` in `get_system_commands`,
      mirroring the clear-search pattern; confirm the 5.1 tests pass.

## 6. Ship gate

- [x] 6.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version
      0.6.54 → 0.6.55.
- [x] 6.2 [req: *] Run the full `plugins/s/skills/build/tests_textual/`
      suite (venv with `textual`) and the stdlib `python3 -m unittest
      discover -s plugins/s/skills/build/tests` (no `textual`); both must
      pass clean.
