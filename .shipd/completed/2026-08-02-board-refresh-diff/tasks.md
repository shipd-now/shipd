## 1. Diff-aware refresh

- [x] 1.1 [req: board-tui] In `plugins/s/skills/build/tests_textual/
      test_dashboard.py`, add tests: `_lane_contents(board)` maps members to the
      correct lane order (with shipped grouped per epic); `_lane_signature` is
      equal for an unchanged board and differs when a member's lane/state/stage/
      actions change; a `Pilot` test that an unchanged-board `refresh_board()`
      retains the same `TaskCard` widget instances (no remount); a `Pilot` test
      that a collapsed shipped group stays collapsed across an unchanged refresh;
      and a `Pilot` test that moving a member to a new lane rebuilds only the
      affected lanes while other lanes' cards are retained. Run and observe
      failure.
- [x] 1.2 [req: board-tui] In `dashboard.py`, add pure helpers `_lane_contents(
      board)` (per-lane ordered card specs + shipped group order — the data
      `_render_lanes` mounts) and `_lane_signature(cards)` / `_tree_signature(
      board)` returning hashable tuples derived solely from board content.
- [x] 1.3 [req: board-tui] In `dashboard.py`, initialise `self._lane_sigs = {}`
      and `self._tree_sig = None` (in `__init__`/`on_mount`), and rewrite
      `_render_lanes` to build `_lane_contents(self.board)` and — inside `with
      self.batch_update():` — `remove_children()`+remount only the lanes whose
      signature differs from `self._lane_sigs`, updating the store; leave
      unchanged lanes untouched. Guard `_render_tree` against `self._tree_sig` the
      same way. Confirm 1.1 passes.

## 2. Version bump & verification

- [x] 2.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json` to the next unused version above the
      branch base (base is 0.6.27, so 0.6.28 — pick the next free one if taken).
- [x] 2.2 [req: *] Run the dependency-free suite `python3 -m unittest discover -s
      plugins/s/skills/build/tests` (must pass with `textual` NOT installed),
      then `pip install -r requirements.txt` in a venv and run
      `plugins/s/skills/build/tests_textual` with it; both green.
- [x] 2.3 [req: *] Manually launch the board (`dashboard.py tui`) against this
      repo and confirm the SHIPPED column no longer flashes on the 2s interval
      when idle, and that collapsing a shipped group stays collapsed across
      refreshes.
