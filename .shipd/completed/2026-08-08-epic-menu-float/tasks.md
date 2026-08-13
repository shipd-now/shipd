## 1. Placement tests assert the float invariant

- [x] 1.1 [req: board-epic-grouping] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, in
      `EpicHeaderControlPlacementTest.test_menu_control_flows_after_the_title`,
      replace the `assertGreaterEqual(menu.region.x, group.region.right)`
      assertion with one that queries the group's `CollapsibleTitle` and
      asserts `title.content_region.right <= menu.region.x`. Keep the existing
      height/width/y and in-lane assertions unchanged. Rename the test to
      `test_menu_control_floats_at_the_title_row_end` and update the class
      docstring to quote the spec's new wording ("the title's content area ends
      at or before the control's leading edge"). Run the file's
      `EpicHeaderControlPlacementTest` and observe the renamed test fail — the
      CSS float does not exist yet.
- [x] 1.2 [req: board-epic-grouping] In the same file, in
      `EpicHeaderControlPlacementTest.test_non_runnable_menu_control_flows_after_the_title`,
      make the same substitution (`title.content_region.right <=
      menu.region.x` in place of the `group.region.right` comparison) and
      rename it to `test_non_runnable_menu_control_floats_at_the_title_row_end`.
- [x] 1.3 [req: board-epic-grouping] In the same file, in
      `EpicHeaderOverlongTitleTest.test_overlong_title_ellipsizes_beside_the_menu_control`,
      replace `assertLessEqual(group.region.right, menu.region.x)` with
      `assertLessEqual(title.content_region.right, menu.region.x)` against the
      group's `CollapsibleTitle`, and extend the test to repeat the assertion
      with the group collapsed (`group.collapsed = True` followed by
      `await pilot.pause()`).
- [x] 1.4 [req: board-epic-grouping] In the same file, add
      `test_member_cards_keep_the_lane_content_width` to
      `EpicHeaderControlPlacementTest`: mount `_two_epic_board` at
      `(200, 24)`, and assert the group `Collapsible`'s region width equals its
      lane's `scrollable_content_region.width`. Run it and observe it fail.

## 2. Float the control

- [x] 2.1 [req: board-epic-grouping] In
      `plugins/s/skills/build/scripts/dashboard.py`'s app CSS, add
      `layers: group menu;` to the `.epic-group-row` rule and `layer: group;`
      to the `.epic-group` rule.
- [x] 2.2 [req: board-epic-grouping] In the same CSS, add
      `padding-right: 4;` to the `.epic-group CollapsibleTitle` rule — the
      control's three cells plus its one-cell inset.
- [x] 2.3 [req: board-epic-grouping] In the same CSS, add an
      `.epic-menu-button` rule carrying `layer: menu; dock: right;
      margin-right: 1;`, placed before the `.compact-button` rule so the shared
      compact-button styling still applies. Confirm tasks 1.1–1.4's tests now
      pass.
- [x] 2.4 [req: board-epic-grouping] Update the `EpicGroupRow` class docstring
      in the same file: it currently states the menu control is "the ordinary
      trailing child with a reserved width" and that there are "No overlay
      layers, offsets, or resize-clamp". Restate it for the float — the control
      floats on the row's `menu` layer docked right with a one-cell inset, the
      `Collapsible` keeps the lane's full content width, the title reserves the
      control's cells through its own `padding-right`, and the positioning is
      static with no offset and no resize handler.

## 3. Verify and ship

- [x] 3.1 [req: *] Run the full textual suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests_textual`)
      and the stdlib suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`);
      both must pass with no failures.
- [x] 3.2 [req: *] Bump the `version` field in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.70` to `0.6.71`.
