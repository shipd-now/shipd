## 1. Anchored popup offset

- [x] 1.1 [req: board-epic-grouping] In
      `plugins/s/skills/build/tests/test_change_artifacts.py` (via the
      `_load_dashboard_stdlib()` loader) or a sibling stdlib module, add
      failing tests for a pure `menu_offset(anchor, box, screen)` helper:
      a control near top-left opens just below it; a control near the right
      edge shifts left so the box stays fully on screen; a control near the
      bottom opens above; the returned offset always keeps the box within
      the screen bounds.
- [x] 1.2 [req: board-epic-grouping] In
      `plugins/s/skills/build/scripts/dashboard.py`, implement
      `menu_offset` in the pre-textual stdlib zone; confirm the 1.1 tests
      pass.

## 2. Non-modal anchored menu

- [x] 2.1 [req: board-epic-grouping] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, update the
      action-menu tests to the anchored-popup contract (run and observe
      failures): opening the menu leaves the board undimmed (the menu
      screen's background has zero alpha / no dim) and positions its box
      near the `≡` control (its region is not screen-centred and lies within
      the viewport); the menu has no title bar and no ✕; it presents `View
      epic` and (when runnable) `Run epic…` as an `OptionList`; `↑`/`↓` move
      the highlight and Enter selects; selecting View pushes
      `EpicDetailScreen`, Run pushes `EpicRunConfirmScreen` (no dispatch
      yet); `Escape` dismisses acting on nothing; a click on the screen
      outside the menu box dismisses acting on nothing; runnable gating of
      the Run item and the confirmation flow are unchanged.
- [x] 2.2 [req: board-epic-grouping] In
      `plugins/s/skills/build/scripts/dashboard.py`, rework
      `EpicActionMenuScreen`: add `OptionList` to the widget imports; make
      the screen background transparent (no dim) and position its box via
      `menu_offset` from an anchor passed by `on_button_pressed`
      (`event.button.region`), threaded through `_push_epic_menu(slug,
      anchor)`; replace the title bar + buttons body with an `OptionList`
      of the items; select → `dismiss("view"|"run")`; add an outside-box
      `Click` handler dismissing with `None`; keep the `escape` binding and
      the `_after` routing. Delete the dead title-bar/✕/button CSS for this
      screen. Confirm the 2.1 tests pass and the other modals' chrome
      (containment sweep, compact-control tests) stay green.

## 3. Ship

- [x] 3.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json`.
- [x] 3.2 [req: *] Verification barrier: run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` without `textual`, and the
      `tests_textual` suite with it installed; both suites pass.
