# Tasks — board-theme

## 1. Shipd theme registration

- [x] 1.1 [req: board-shipd-theme] Test-first: add a `ShipdThemeTests` class to
      `plugins/s/skills/build/tests_textual/test_dashboard.py` asserting
      (a) a `BoardApp` mounted via `run_test` (reuse an existing fixture
      `board_fn`) has `app.theme == "shipd"` and `"shipd" in
      app.available_themes`; (b) `dashboard.SHIPD_THEME.variables` carries
      exactly these keys/values: `lane-unplanned #8888A0`, `lane-ready
      #4DA6FF`, `lane-building #FF8C42`, `lane-review #9B7FFF`, `lane-shipped
      #3DCC8E`, `risk-high #FF8C42`, `risk-medium #C6FF4E`, `risk-low #55556A`
      (plus the presence of `shipd-border`, `shipd-border-strong`, `bg-hover`,
      `bg-active`, `accent-dim`, `fg-muted`, `fg-subtle`). Run with
      `~/.cache/shipd/tui-venv/bin/python -m unittest discover -s
      plugins/s/skills/build/tests_textual` and observe it fail
      (`SHIPD_THEME` does not exist yet).
- [x] 1.2 [req: board-shipd-theme] In
      `plugins/s/skills/build/scripts/dashboard.py`, add `from textual.theme
      import Theme` to the existing textual import block and define a
      module-level `SHIPD_THEME = Theme(name="shipd", primary="#C6FF4E",
      secondary="#4DA6FF", accent="#C6FF4E", foreground="#F0F0F8",
      background="#0A0A0D", surface="#111118", panel="#1C1C26",
      success="#3DCC8E", warning="#FF8C42", error="#FF4D3D", dark=True,
      variables={...})` with the exact variables listed in task 1.1 (values
      per plan.md's Implementation section), directly above `BoardApp`.
- [x] 1.3 [req: board-shipd-theme] In `BoardApp.__init__`, immediately after
      `super().__init__()`, call `self.register_theme(SHIPD_THEME)` then set
      `self.theme = "shipd"`. Confirm task 1.1's tests now pass.

## 2. Flat chrome restyle through theme variables

- [x] 2.1 [req: board-shipd-theme, board-epic-grouping] Test-first: extend
      `ShipdThemeTests` with a structural CSS scan over the four class
      attributes `BoardApp.CSS`, `MemberDetailScreen.CSS`,
      `EpicRunConfirmScreen.CSS`, `EpicDetailScreen.CSS` asserting: no hex
      literal (regex `#[0-9a-fA-F]{3,8}\b`), no named color token `black` or
      `white`, and no `round` border style in any of them; and that
      `BoardApp.CSS` styles `.epic-group-row` with `$shipd-border` and
      `.epic-group` with `background: $panel`. Run and observe it fail
      (`solid black` and `round $primary` are still present).
- [x] 2.2 [req: board-epic-grouping] In `BoardApp.CSS`, change
      `.epic-group-row`'s `border-bottom: solid black` to `border-bottom:
      solid $shipd-border`. Leave `.epic-group`'s `background: $panel` as is.
- [x] 2.3 [req: board-shipd-theme] In `BoardApp.CSS`, restyle `Lane`:
      `border: round $primary` → `border: solid $shipd-border`, and add
      `background: $surface;` and `border-title-color: $fg-muted;` to the
      `Lane` block.
- [x] 2.4 [req: board-shipd-theme] In `BoardApp.CSS`, re-point the task-card
      risk bars: `TaskCard.risk-low` → `border-left: thick $risk-low`,
      `TaskCard.risk-medium` → `border-left: thick $risk-medium`,
      `TaskCard.risk-high` → `border-left: thick $risk-high`; change
      `TaskCard:focus` to `background: $accent 15%;` only (delete its
      `border-left: thick $warning` line so the risk bar survives focus); and
      change `.epic-member-row:focus` to `background: $accent 15%`.
- [x] 2.5 [req: board-shipd-theme] In the `CSS` blocks of
      `MemberDetailScreen`, `EpicRunConfirmScreen`, and `EpicDetailScreen`,
      change each `border: round $primary` to `border: solid
      $shipd-border-strong` (no other modal changes). Confirm task 2.1's scan
      now passes.

## 3. Verification and version bump

- [x] 3.1 [req: *] Run the full TUI suite
      (`~/.cache/shipd/tui-venv/bin/python -m unittest discover -s
      plugins/s/skills/build/tests_textual`, the same discover CI uses) and
      the stdlib suite without textual (`python3 -m unittest discover -s
      plugins/s/skills/build/tests`); both pass with no changes to any
      existing test.
- [x] 3.2 [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` from `0.6.42` to `0.6.43`.
