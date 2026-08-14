## 1. Remove the hierarchy panel

- [x] 1.1 [req: board-tui] In `plugins/s/skills/build/tests_textual/
      test_dashboard.py`, update/remove the hierarchy-panel tests: delete tests
      asserting `#hierarchy-panel`, `HierarchyTree`, `show_root`/`guide_depth`,
      and epic-node collapse in the tree; change the mount test to assert the
      widget tree has NO hierarchy panel. Run and observe the expected failures
      (panel still present).
- [x] 1.2 [req: board-tui] In `dashboard.py`, remove `HierarchyTree`,
      `_render_tree`, the `#hierarchy-panel` yield in `compose`, the
      `#hierarchy-panel` CSS, the `_tree_sig` state and its use in
      `refresh_board`, and the `p`/`action_toggle_panel` panel binding. Keep
      `dispatch_epic_run` (it will be re-triggered from the group header in
      task 3). Confirm 1.1 passes and the app still mounts.

## 2. Controls strip and group-by-epic toggle

- [x] 2.1 [req: board-epic-grouping] In `tests_textual/test_dashboard.py`, add
      tests asserting: on mount a controls strip with a group-by-epic toggle
      exists above the lanes; `BoardApp.group_by_epic` defaults to `True`;
      toggling the control (and the footer key) flips the state. Run and observe
      failure.
- [x] 2.2 [req: board-epic-grouping] In `dashboard.py`, add a
      `group_by_epic = True` attribute on `BoardApp`; mount a controls strip
      above the lanes' `Horizontal` holding a labelled toggle widget
      (`Checkbox`/`Switch`, imported under the guarded textual import block);
      wire its change handler and a footer-bound key to flip `group_by_epic` and
      repaint the lanes. Confirm 2.1 passes.

## 3. Generalise per-epic grouping across all lanes

- [x] 3.1 [req: board-epic-grouping] In `tests_textual/test_dashboard.py`, add
      tests: with grouping on, a lane holding two epics renders two collapsible
      epic groups, each header naming its epic and (for an epic with an
      initiative) its initiative; with grouping off, lanes render flat (no
      `Collapsible`); a collapsed group hides its cards. Run and observe failure.
- [x] 3.2 [req: board-epic-grouping] In `dashboard.py`, refactor `_render_lanes`
      so that when `group_by_epic` is on, EVERY lane mounts through the shared
      per-epic grouping path (generalise `_mount_shipped_group`), and when off,
      every lane mounts flat — `shipped` no longer has an always-grouped special
      case. Include the epic's initiative in the group header (thread it via
      `_lane_contents` or look it up from the board by epic slug). Confirm 3.1
      passes.

## 4. Epic run from the group header

- [x] 4.1 [req: board-epic-grouping] In `tests_textual/test_dashboard.py`, add a
      test: clicking an epic group header's run control dispatches the epic-level
      run for that epic (assert via the injectable launch/dispatch seam used by
      the existing epic-run tests) and leaves the group's `collapsed` state
      unchanged. Run and observe failure.
- [x] 4.2 [req: board-epic-grouping] In `dashboard.py`, add a clickable run
      control (a `Button` with a distinct id, mirroring the spec-detail modal's
      `✕` button) inside each epic group header; handle it in `on_button_pressed`
      → `dispatch_epic_run(<epic slug>)`, ensuring the handler does not toggle the
      `Collapsible`'s collapsed state. Confirm 4.1 passes.

## 5. Visual: gray background, black separators

- [x] 5.1 [req: board-epic-grouping] In `tests_textual/test_dashboard.py`, add a
      test asserting the epic-group styling: groups carry the grouping style
      class(es) and no per-epic-status colour class is applied (the
      `Collapsible.status-*` scheme is gone). Run and observe failure.
- [x] 5.2 [req: board-epic-grouping] In `dashboard.py`, replace the
      `Collapsible.status-*` title-colour CSS with a uniform gray group
      background and a black separator line between adjacent groups. Confirm 5.1
      passes.

## 6. Diff-aware refresh, version bump & verification

- [x] 6.1 [req: board-tui] In `dashboard.py`, fold `group_by_epic` into the
      per-lane signature (`_lane_signature`) so toggling the mode repaints the
      affected lanes while an idle board with unchanged grouping does not repaint
      and collapsed groups stay collapsed. Add/confirm a `tests_textual` test for
      "a collapsed epic group survives an unchanged-board refresh".
- [x] 6.2 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json` to the next unused version above the
      branch base (base is 0.6.32, so 0.6.33 — pick the next free one if taken,
      verifying against branches/tags/history).
- [x] 6.3 [req: *] Run the dependency-free suite `python3 -m unittest discover -s
      plugins/s/skills/build/tests` (must pass with `textual` NOT installed),
      then, in a venv with `pip install -r requirements.txt`, run
      `plugins/s/skills/build/tests_textual`; both green.
- [x] 6.4 [req: *] Manually drive the real `BoardApp` (headless `run_test` with
      `textual`): confirm no hierarchy panel; grouping on by default with per-epic
      headers (showing initiative) and gray/black banding; the toggle flips to
      flat lanes and back; clicking a header's run control dispatches the epic run
      without collapsing the group.
