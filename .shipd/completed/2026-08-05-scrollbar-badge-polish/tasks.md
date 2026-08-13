# Tasks — scrollbar-badge-polish

## 1. Scrollbar theme

- [x] 1.1 [req: board-scrollbar-theme] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, add a test
      asserting `app.get_css_variables()` on the mounted board resolves
      `scrollbar` to `#3E3E52`, `scrollbar-hover` and `scrollbar-active` to
      `#55556A`, and `scrollbar-background`, `scrollbar-background-hover`,
      `scrollbar-background-active`, and `scrollbar-corner-color` to
      `#1C1C26` (compare via `textual.color.Color.parse(...).rgb` per suite
      convention). Run the suite and observe the test fail.
- [x] 1.2 [req: board-scrollbar-theme] In
      `plugins/s/skills/build/scripts/dashboard.py`, add the seven
      scrollbar entries from `plan.md`'s `## Implementation` to
      `SHIPD_THEME.variables`. Confirm the 1.1 test now passes.

## 2. Risk chip guard

- [x] 2.1 [req: board-modal-chrome] In
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, add a test
      mounting the spec-detail modal for a member dict carrying no `risk`
      key and asserting its badge row contains no `badge-risk-*`-classed
      chip and no Static rendering `?` — the row's first chip is the lane
      chip. Keep the existing with-risk badge-row test as the positive case.
      Run the suite and observe the new test fail.
- [x] 2.2 [req: board-modal-chrome] In
      `plugins/s/skills/build/scripts/dashboard.py`, guard the risk badge
      in `MemberDetailScreen.compose` with `if m.get("risk"):` and update
      the badge-row comment accordingly (`_risk_badge` itself is unchanged).
      Confirm the 2.1 test now passes.

## 3. Ship gates

- [x] 3.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` `version` to
      the next patch above the current `main` value (expected `0.6.58` →
      `0.6.59`).
- [x] 3.2 [req: *] Verification barrier: run
      `python3 -m unittest discover -s plugins/s/skills/build/tests` (must
      pass without `textual`) and the `tests_textual` suite with the venv
      interpreter (`~/.cache/shipd/tui-venv/bin/python3`); both green.
