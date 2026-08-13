## 1. Discovery helper

- [x] 1.1 [req: board-standalone-changes] In
      `plugins/s/skills/build/tests/test_change_artifacts.py` (via the
      existing `_load_dashboard_stdlib()` loader), add failing tests for
      `standalone_changes(root, epic_member_slugs)`: a root `planned/`
      change and a worktree `planned/` change with no `Epic:` line are
      returned with slug, state from the plan's `Status:`, and the hosting
      `location`; a slug in `epic_member_slugs` is excluded; a plan with an
      `Epic:` line is excluded; a malformed/unreadable change dir is
      skipped; a worktree whose change was archived to `completed/` reports
      state `archived`.
- [x] 1.2 [req: board-standalone-changes] In
      `plugins/s/skills/build/scripts/dashboard.py`, implement
      `standalone_changes(root, epic_member_slugs)` in the pre-textual
      stdlib zone per the plan (member-shaped dicts, skip-on-error);
      confirm the 1.1 tests pass.

## 2. Aggregation and rendering

- [x] 2.1 [req: board-standalone-changes] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, add
      failing tests: a board fixture with a standalone `Status: active`
      worktree change renders a card in the building lane under a
      `standalone` group header showing the count and carrying no run/open
      buttons (epic mode; also assert flat rendering in `none` mode);
      selecting the card opens `MemberDetailScreen` resolving artifacts
      from the worktree fixture; removing the standalone entry from the
      board between refreshes repaints the lane (signature change); an
      epic-member slug present in both a stub table and the standalone
      fixture renders once.
- [x] 2.2 [req: board-standalone-changes] In
      `plugins/s/skills/build/scripts/dashboard.py`: `build_board`
      collects all epics' member slugs, calls `standalone_changes`, and
      adds the `"standalone"` list (rows get `"actions": []`);
      `_lane_contents` appends standalone rows under pseudo-epic
      `standalone` (status `None`) using `_member_column` with an empty
      entry; `_mount_epic_groups` renders the `standalone` run with count
      but skips both controls; signatures fold the rows as member rows;
      `none` mode renders flat. Confirm the 2.1 tests pass.

## 3. Ship

- [x] 3.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json`.
- [x] 3.2 [req: *] Verification barrier: run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` without `textual`, and the
      `tests_textual` suite with it installed; both suites pass.
