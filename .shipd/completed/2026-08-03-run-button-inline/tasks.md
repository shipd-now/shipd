# Tasks

## 1. Inline header controls placement

- [x] 1.1 [req: board-epic-grouping] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, add a test
      class `EpicHeaderControlPlacementTest` (near `EpicRunGuardTest`) with
      two tests over `dashboard.BoardApp(root="/x", board_fn=_two_epic_board)`
      under `run_test()`: (a) query `#epic-group-ready-ep1`'s title widget via
      the string selector `"CollapsibleTitle"`, the `#run-epic-ready-ep1`
      `Button`, and the `#open-epic-ready-ep1` `Button`, and assert
      `run.region.y == title.region.y`,
      `run.region.x == title.region.right`, and
      `open.region.offset == run.region.top_right` (open packed directly
      after run on the same row); (b) with `board_fn=_shipped_board`, query
      `#epic-group-shipped-es1`'s `"CollapsibleTitle"` and
      `#open-epic-shipped-es1` `Button` and assert the open control sits at
      `open.region.y == title.region.y` and
      `open.region.x == title.region.right` (flush to the title when no run
      control renders). Run the suite from the worktree root with
      `/Users/mikkelbergmann/projects/shipd/.venv/bin/python -m unittest
      discover -s plugins/s/skills/build/tests_textual` and observe both new
      tests fail (the buttons currently mount at the row's far edge).
- [x] 1.2 [req: board-epic-grouping] In
      `plugins/s/skills/build/scripts/dashboard.py` `BoardApp.CSS`: add
      `layers: base controls;` to the `.epic-group-row` rule, and replace the
      separate `.epic-run-button` and `.epic-open-button` rules with one
      shared rule `.epic-run-button, .epic-open-button { layer: controls;
      width: 3; min-width: 3; height: 1; border: none; padding: 0 1; }`.
- [x] 1.3 [req: board-epic-grouping] In
      `plugins/s/skills/build/scripts/dashboard.py`: add
      `from rich.text import Text` to the module's existing textual
      import block (the `from textual...` imports near the top); in
      `_mount_epic_groups`'s `_flush`, set
      `styles.offset = (5 + Text.from_markup(title).cell_len, 1)` on `run_button` (when
      constructed) and on `open_button` before the row mounts; update the two
      comments above the button constructions to say the controls are layer
      overlays packed just after the title text (x = 5 cells of fixed
      title-row chrome + the title's cell width, y = 1 skipping the
      Collapsible's border-top row; the shared layer keeps horizontal flow so
      the identical offset packs run-then-open adjacently) and stay siblings
      of the Collapsible so their stopped clicks never reach the collapse
      toggle.
- [x] 1.4 [req: board-epic-grouping] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.35` to `0.6.36`.
- [x] 1.5 [req: board-epic-grouping] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, change
      `EpicRunControlTest`'s six `app.run_test()` calls to
      `app.run_test(size=(120, 24))` (the default 80-col harness makes lanes
      too narrow for the inline controls to be hittable — the same realistic
      width `EpicDetailModalTest` already uses). Then, from the worktree
      root, run
      `/Users/mikkelbergmann/projects/shipd/.venv/bin/python -m unittest
      discover -s plugins/s/skills/build/tests_textual` (the new placement
      tests and the existing `EpicRunGuardTest`/`EpicRunControlTest`/
      epic-detail tests must all pass) and `python3 -m unittest discover -s
      plugins/s/skills/build/tests` (the stdlib suite, without textual).

## 2. Compact, button-evident controls

- [x] 2.1 [req: board-epic-grouping] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, add a test
      class `CompactControlTest` asserting every compact control renders one
      row high (`region.height == 1`): (a) on
      `dashboard.BoardApp(root="/x", board_fn=_two_epic_board)` at
      `run_test(size=(120, 24))`, the `#run-epic-ready-ep1` and
      `#open-epic-ready-ep1` Buttons; (b) the three modal close controls —
      open each modal the same way the existing tests for that screen do
      (`MemberDetailScreen`'s `#close-detail`, `EpicDetailScreen`'s
      `#epic-detail-close`, `EpicRunConfirmScreen`'s `#epic-run-close`) and
      assert each ✕ Button's `region.height == 1`. Run the textual suite and
      observe the modal-✕ assertions fail (those Buttons currently render
      the default three-row chrome).
- [x] 2.2 [req: board-epic-grouping] In
      `plugins/s/skills/build/scripts/dashboard.py`: add to `BoardApp.CSS`
      a shared rule pair `.compact-button { height: 1; border: none;
      padding: 0 1; width: auto; min-width: 3; background: $primary 25%; }`
      and `.compact-button:hover { background: $primary 50%; }` (App-level
      CSS applies across all screens); slim the
      `.epic-run-button, .epic-open-button` rule down to `layer: controls;`
      only; add `compact-button` to the `classes` of the five Buttons — the
      header `▶` (`epic-run-button compact-button`), the header `☰`
      (`epic-open-button compact-button`), and the three modal ✕ Buttons
      (`classes="compact-button"` alongside their existing ids); delete the
      now-redundant `MemberDetailScreen #close-detail`,
      `EpicDetailScreen #epic-detail-close`, and
      `EpicRunConfirmScreen #epic-run-close` width rules from those screens'
      CSS blocks.
- [x] 2.3 [req: board-epic-grouping] From the worktree root, re-run both
      suites: `/Users/mikkelbergmann/projects/shipd/.venv/bin/python -m
      unittest discover -s plugins/s/skills/build/tests_textual` (all
      classes including `CompactControlTest` and
      `EpicHeaderControlPlacementTest` green) and `python3 -m unittest
      discover -s plugins/s/skills/build/tests` (stdlib suite, without
      textual).
