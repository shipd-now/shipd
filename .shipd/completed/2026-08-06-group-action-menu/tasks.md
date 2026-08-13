## 1. Action menu

- [x] 1.1 [req: board-epic-grouping] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, migrate the
      header-control tests to the menu contract (run and observe failures):
      every group header carries exactly one `≡` (`epic-menu-button
      compact-button`, 3×1) as the row's last child inside the band, no
      `epic-run-button`/`epic-open-button` anywhere; clicking it opens
      `EpicActionMenuScreen` naming the epic without collapsing the group;
      a runnable epic's menu lists View epic and Run epic, a non-runnable
      one only View epic; choosing Run pushes `EpicRunConfirmScreen` (no
      dispatch yet); choosing View pushes `EpicDetailScreen`; `escape`/✕
      closes the menu with nothing dispatched or pushed; the confirmation
      modal's Yes/No/✕/escape behavior is unchanged; update the board sweep
      to the single menu control.
- [x] 1.2 [req: board-epic-grouping] In
      `plugins/s/skills/build/scripts/dashboard.py`, implement it: replace
      the run/open buttons in `_mount_epic_groups._flush` with the single
      `≡` menu button (`epic_menu_slug` marker), add
      `EpicActionMenuScreen(ModalScreen)` per the plan (accent title naming
      the epic, ✕, View epic always, Run epic when runnable at open,
      escape binding; View → dismiss + push `EpicDetailScreen`; Run →
      dismiss + push `EpicRunConfirmScreen`), rewire
      `BoardApp.on_button_pressed` (menu marker in, old two markers out),
      and delete the dead run/open button CSS; confirm the 1.1 tests pass.

## 2. Stable mode segments

- [x] 2.1 [req: board-epic-grouping] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, add a
      failing test: record each of the three mode buttons' regions, select
      `initiative`, then `none`, then `epic` (clicks), and assert every
      button's region is identical across all four states.
- [x] 2.2 [req: board-epic-grouping] In
      `plugins/s/skills/build/scripts/dashboard.py`, pin the segment
      geometry: give each `.mode-button` a fixed width (label length + 2)
      and remove whatever state-dependent styling still reflows (drop
      `text-style: bold` from `.mode-active` only if the test shows it
      moves segments); confirm the 2.1 test passes and the active
      highlight still reads clearly.

## 3. Ship

- [x] 3.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json`.
- [x] 3.2 [req: *] Verification barrier: run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` without `textual`, and the
      `tests_textual` suite with it installed; both suites pass.
