# Tasks — tab-focus-contrast

## 1. Focused-tab contrast

- [x] 1.1 [req: board-modal-chrome] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, add a test
      that mounts the spec-detail modal with artifact tabs, focuses the
      `Tabs` widget inside it, and asserts the active `Tab`'s resolved
      `styles.background` is the theme accent at full alpha and its
      `styles.color` the theme background, with bold text (resolve expected
      colors via `app.get_css_variables()` and `Color.parse` per suite
      convention); also assert that before focusing, the active tab's
      background is not the solid accent (the unfocused themed state). Run
      the suite and observe the new test fail.
- [x] 1.2 [req: board-modal-chrome] In
      `plugins/s/skills/build/scripts/dashboard.py`, add the app-wide rule
      from `plan.md`'s `## Implementation` (`Tabs:focus Tab.-active` with
      `color: $background; background: $accent; text-style: bold;`) to
      `BoardApp.CSS`. Confirm the 1.1 test now passes.

## 2. Ship gates

- [x] 2.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` `version` to
      the next patch above the current `main` value (expected `0.6.60` →
      `0.6.61`).
- [x] 2.2 [req: *] Verification barrier: run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` (must
      pass without `textual`) and the `tests_textual` suite with
      `~/.cache/shipd/tui-venv/bin/python3`; both green.
