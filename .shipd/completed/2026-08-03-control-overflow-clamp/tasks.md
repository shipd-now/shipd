# Tasks

## 1. Clamp header controls inside the lane

- [x] 1.1 [req: board-epic-grouping] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, add a test
      class `EpicHeaderControlClampTest` with a board-fn fixture whose single
      `unplanned`-member epic has slug `delivery-metrics`, status `active`,
      and initiative slug `a-very-long-initiative-for-clamping` (rendered
      title wider than one lane at `run_test(size=(120, 24))`). Two tests:
      (a) geometry — query `#lane-unplanned`, the `#run-epic-unplanned-…` and
      `#open-epic-unplanned-…` Buttons, and assert both regions sit fully
      inside the lane (`run.region.x >= lane.region.x`,
      `open.region.right <= lane.region.right`), on the title row
      (`run.region.y == open.region.y`), with the gap intact
      (`open.region.x == run.region.right + 1`); (b) behavior —
      `pilot.click` the pinned open control and assert
      `app.screen` is a `dashboard.EpicDetailScreen`. Run the textual suite
      with `/Users/mikkelbergmann/projects/shipd/.venv/bin/python -m
      unittest discover -s plugins/s/skills/build/tests_textual` from the
      worktree root and observe both fail (controls currently overflow the
      lane and are unclickable).
- [x] 1.15 [req: board-epic-grouping] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, move
      `EpicHeaderControlPlacementTest`'s two tests to
      `app.run_test(size=(200, 24))` — at the default 80 columns a lane's
      content is 13 cells, so even `ep1 [active] · init` (11 rendered cells,
      offset 16) overflows and the clamp displaces the controls from the
      title edge; 200 columns gives the after-title assertions a lane where
      their premise holds. Keep every assertion unchanged.
- [x] 1.2 [req: board-epic-grouping] In
      `plugins/s/skills/build/scripts/dashboard.py`: add an
      `EpicGroupRow(Horizontal)` class (module scope, near the other board
      widgets, below the textual imports) taking
      `(*children, title, run_button=None, open_button=None, **kwargs)`
      which assigns the unclamped offset
      `styles.offset = (5 + Text.from_markup(title).cell_len, 1)` to each
      non-None button at construction (today's single-pass behavior); its
      `on_resize` handler recomputes
      `x = max(0, min(5 + Text.from_markup(self._title).cell_len,
      self.content_size.width - controls_width))` — `controls_width` 7 when
      `run_button` is present else 3 — and reassigns `styles.offset = (x, 1)`
      **only when x differs from the currently assigned offset**, so an
      unclamped row never triggers a second layout pass. Move the offset
      assignments and
      their placement comments out of `_mount_epic_groups._flush` into this
      class (docstring + handler comment), and have `_flush` mount
      `EpicGroupRow(*row_children, title=title, run_button=run_button,
      open_button=open_button, classes="epic-group-row")` (with
      `run_button`/`open_button` `None` when not constructed). The open
      control's conditional 1-cell left margin stays in `_flush` as today.
- [x] 1.3 [req: board-epic-grouping] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.38` (as bumped on main by PR #117) to `0.6.39`.
- [x] 1.4 [req: board-epic-grouping] From the worktree root, run both suites:
      `/Users/mikkelbergmann/projects/shipd/.venv/bin/python -m unittest
      discover -s plugins/s/skills/build/tests_textual` (new clamp tests and
      all existing `EpicHeaderControlPlacementTest`/`CompactControlTest`/
      `EpicRunControlTest` classes green — short-title geometry must be
      byte-identical to today) and `python3 -m unittest discover -s
      plugins/s/skills/build/tests` (stdlib suite, no textual).
