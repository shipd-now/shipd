## 1. Flex header controls

- [x] 1.1 [req: board-epic-grouping] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, rewrite the
      control-placement tests to the flex contract and add the new ones (run
      them and observe failures): for a runnable epic header, the run and
      open buttons and the count Static are flex children after the
      Collapsible, each button 3×1, all regions inside the lane, none
      overlapping the Collapsible's region; for an overlong title the
      Collapsible's region ends at or before the run control's left edge
      (title ellipsizes in its own space) and controls+count stay fully
      inside the lane; the count Static is the row's last child showing the
      per-lane card count; delete/replace the offset- and clamp-asserting
      tests (the `styles.offset` and pinned-over-title expectations).
- [x] 1.2 [req: board-epic-grouping] In
      `plugins/s/skills/build/scripts/dashboard.py`, convert `EpicGroupRow`
      to plain flex: children `[Collapsible (width 1fr)][run?][open][count
      Static (classes "epic-count", muted, 1-cell left margin)]`; remove
      `layers: base controls` from `.epic-group-row`, the `layer:` rule on
      `.epic-run-button`/`.epic-open-button`, the construction-time
      `styles.offset`, `on_resize`, `_offset_x`, and the `Content.from_text`
      measuring (drop the import if unused); give the run control a 1-cell
      left margin (keep the open control's existing conditional margin); add
      App CSS giving the epic group's `CollapsibleTitle` single-line
      ellipsis truncation; in `_mount_epic_groups._flush`, stop passing
      `count=` to `epic_group_title` and append the count Static instead.
      Confirm the 1.1 tests pass and the existing collapse/click/grouping
      tests stay green.

## 2. Stall banner spacing

- [x] 2.1 [req: board-stall-signal] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, add failing
      assertions to the stall-banner tests: the banner's first text content
      starts three cells from the banner region's left edge, and one blank
      row separates the banner's bottom from the member list's first row.
- [x] 2.2 [req: board-stall-signal] In
      `plugins/s/skills/build/scripts/dashboard.py`, set
      `#epic-stall-banner` padding to `0 1 1 3` and add `margin: 0 0 1 0`;
      confirm the 2.1 tests pass.

## 3. Ship

- [x] 3.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json`.
- [x] 3.2 [req: *] Verification barrier: run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` without `textual`, and the
      `tests_textual` suite with it installed; both suites pass.
