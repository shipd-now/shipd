## 1. Hide the root and tighten the indent

- [x] 1.1 [req: board-tui] In `plugins/s/skills/build/tests_textual/
      test_dashboard.py`, add a `Pilot`/`App.run_test` test asserting the mounted
      app's hierarchy tree (`#hierarchy-panel`) reports `show_root` is `False` and
      `guide_depth` equals the reduced minimal value the implementation sets. Run
      it and observe failure.
- [x] 1.2 [req: board-tui] In `dashboard.py` `HierarchyTree`, set `show_root =
      False` and `guide_depth` to the minimal value `textual` allows (probe the
      accepted minimum; use it) — on the instance via `on_mount` or in `__init__`
      after `super().__init__`. Leave `_render_tree`, the `r` epic-run binding,
      and node contents unchanged. Confirm 1.1 passes.

## 2. Version bump & verification

- [x] 2.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json` to the next unused version above the
      branch base (base is 0.6.28, so 0.6.29 — pick the next free one if taken).
- [x] 2.2 [req: *] Run the dependency-free suite `python3 -m unittest discover -s
      plugins/s/skills/build/tests` (must pass with `textual` NOT installed),
      then `pip install -r requirements.txt` in a venv and run
      `plugins/s/skills/build/tests_textual` with it; both green.
- [x] 2.3 [req: *] Manually launch `dashboard.py tui` (with `textual`) and confirm
      the hierarchy panel no longer shows a "hierarchy" header and each level
      indents by roughly one character.
