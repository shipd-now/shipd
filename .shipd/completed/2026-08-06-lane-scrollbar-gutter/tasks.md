## 1. Stable gutter

- [x] 1.1 [req: lane-scrollbar-gutter] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, add failing
      tests: (a) a board grown via `refresh_board()` from a non-scrolling to
      a scrolling shipped lane keeps `scrollable_content_region.width`
      unchanged; (b) with the scrollbar displayed, every `EpicGroupRow`
      button's region is disjoint from `lane.vertical_scrollbar.region`;
      (c) a non-scrolling lane's content width equals a scrolling lane's at
      the same terminal size. Fold (a) and (b) into
      `assert_board_rows_contained` so the existing sweep carries them.
- [x] 1.2 [req: lane-scrollbar-gutter] In
      `plugins/s/skills/build/scripts/dashboard.py`, add
      `scrollbar-gutter: stable;` to the app-level `Lane` CSS rule; confirm
      the 1.1 tests pass and the existing board sweep stays green.

## 2. Ship

- [x] 2.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json`.
- [x] 2.2 [req: *] Verification barrier: run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` without `textual`, and the
      `tests_textual` suite with it installed; both suites pass.
