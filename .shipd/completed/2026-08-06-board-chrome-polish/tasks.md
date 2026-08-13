## 1. Count into the title

- [x] 1.1 [req: board-epic-grouping] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, update the
      count tests to the new form (run and observe failures): a 2-card
      group's header title ends with ` (2)` whose rendered style is the
      muted foreground, no `.epic-count` element exists anywhere, and the
      stdlib `epic_group_title` tests (wherever they live) assert the
      ` [$fg-muted](2)[/]` suffix markup for `count=2` and byte-identical
      output for `count=None`.
- [x] 1.2 [req: board-epic-grouping] In
      `plugins/s/skills/build/scripts/dashboard.py`, render the count as
      the title's muted ` (N)` suffix in `epic_group_title`, pass `count=`
      again from `_mount_epic_groups` and `_mount_initiative_groups`
      (including the `standalone` group), and delete the `.epic-count`
      Static children and CSS; confirm the 1.1 tests pass.

## 2. Idle tint, band continuity, card ellipsis

- [x] 2.1 [req: lane-row-presentation] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, add failing
      tests: an unhovered run/open control's computed background equals the
      theme's `$bg-hover` and a focused one equals the accent tint; an epic
      group's row background is the panel colour across its full box (no
      lane-background band between last card and divider — assert via the
      row's computed background and height covering the Collapsible);
      a card whose `✓ <slug>` is one cell wider than the card paints a
      single line beginning with the slug prefix and containing an
      ellipsis.
- [x] 2.2 [req: lane-row-presentation] In
      `plugins/s/skills/build/scripts/dashboard.py`: change the app-level
      `.compact-button` background to `$bg-hover` and add a
      `.compact-button:focus { background: $primary 50%; }` rule; add
      `background: $panel` to `.epic-group-row`; add `text-wrap: nowrap;
      text-overflow: ellipsis;` to `TaskCard` and `.epic-member-row` CSS.
      Confirm the 2.1 tests pass and the modal ✕ accent overrides still
      hold (existing containment sweep stays green).

## 3. Board-screen sweep

- [x] 3.1 [req: lane-row-presentation] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, add the
      board-screen sweep `assert_board_rows_contained(test, app)` (every
      `EpicGroupRow` button inside its lane's `scrollable_content_region`;
      every `TaskCard`'s painted first line begins with its slug's visible
      prefix) and run it against a multi-epic fixture at terminal widths
      160 and 120; observe it fail before task 2.2's ellipsis fix at the
      narrow width, then pass.

## 4. Ship

- [x] 4.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json`.
- [x] 4.2 [req: *] Verification barrier: run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` without `textual`, and the
      `tests_textual` suite with it installed; both suites pass.
