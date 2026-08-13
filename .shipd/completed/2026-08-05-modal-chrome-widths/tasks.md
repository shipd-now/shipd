## 1. Containment sweep and fixes

- [x] 1.1 [req: modal-chrome-containment] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, add the
      reusable `assert_chrome_contained(screen)` helper (every `Button`,
      `.modal-badge`, and `.modal-title-text` region inside the screen's
      `Container` region, nonzero width; badges additionally narrower than
      half the row) and failing tests running it against all four screens:
      spec-detail opened for a member with risk `low`, a driving `plan#1`
      entry, and an epic (assert all four chips visible and content-sized),
      epic-detail with members (assert member-row lane chips contained),
      the run-confirmation modal, and the graph config dialog. Add a
      focused-✕ test asserting the close control's background is the
      dimmed accent while focused.
- [x] 1.2 [req: modal-chrome-containment] In
      `plugins/s/skills/build/scripts/dashboard.py`, add `width: auto;` to
      the app-level `.modal-badge` rule, and add
      `.modal-title-bar .compact-button:focus { background: $accent-dim;
      color: $background; }` to the member, epic, and run-confirm modal CSS
      blocks beside their hover rules; confirm the 1.1 tests pass.

## 2. Ship

- [x] 2.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json`.
- [x] 2.2 [req: *] Verification barrier: run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` without `textual`, and the
      `tests_textual` suite with it installed; both suites pass.
