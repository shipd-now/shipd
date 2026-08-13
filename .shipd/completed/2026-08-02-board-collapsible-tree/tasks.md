## 1. Per-node hierarchy collapse

- [x] 1.1 [req: board-tui] In `plugins/s/skills/build/tests/test_dashboard.py`,
      add tests for `layout_board`'s new `collapsed_nodes` kwarg: a collapsed
      initiative node key omits its epics/members and marks the row `▸`; a
      collapsed epic node key omits its theme/members while sibling epics stay
      expanded; expanded nodes carry `▾`. Run them and observe failure.
- [x] 1.2 [req: board-tui] In `dashboard.py`, add a `collapsed_nodes=frozenset()`
      keyword arg to `layout_board`; define node keys `("init", slug_or_None)`
      and `("epic", slug)`; prefix each initiative/epic panel row with `▾`/`▸`,
      and skip emitting an initiative's epics (or an epic's theme+members) when
      its node key is in `collapsed_nodes`.
- [x] 1.3 [req: board-tui] In `dashboard.py`, set the initiative and epic
      `tree_row` regions' `action` to `toggle_node` and add a `node` key holding
      their node-key tuple (replacing the dead `select_epic`/`select_member`
      actions on those rows).
- [x] 1.4 [req: board-tui] In `dashboard.py` `_tui_dispatch`, handle
      `action == "toggle_node"` by flipping the region's `node` key in
      `state["collapsed_nodes"]`; seed `state["collapsed_nodes"] = set()` in the
      `tui` loop and pass it to `layout_board`. Confirm 1.1 passes.

## 2. Grouped collapsible SHIPPED column

- [x] 2.1 [req: board-tui] In `test_dashboard.py`, add tests for `layout_board`'s
      new `collapsed_shipped` kwarg: the `shipped` column emits a per-epic header
      region (`kind="shipped_group"`, `action="toggle_shipped_group"`) with a
      `▾` marker above that epic's shipped cards; an epic slug in
      `collapsed_shipped` marks its header `▸` and places none of its cards while
      another epic's shipped cards still render; the other columns emit no
      headers. Run them and observe failure.
- [x] 2.2 [req: board-tui] In `dashboard.py` `layout_board`, when placing the
      `shipped` column, partition its members by epic (board order), emit a
      header line + `shipped_group` region per epic with the `▾`/`▸` marker, and
      place that epic's cards only when its slug is not in `collapsed_shipped`;
      leave the other four columns' flat placement unchanged.
- [x] 2.3 [req: board-tui] In `dashboard.py` `_tui_dispatch`, handle
      `action == "toggle_shipped_group"` by flipping the region's epic slug in
      `state["collapsed_shipped"]`; seed `state["collapsed_shipped"] = set()` in
      the `tui` loop and pass it to `layout_board`. Confirm 2.1 passes.
- [x] 2.4 [req: board-tui] In `dashboard.py`, confirm `region_at` still orders
      `card_button` ahead of the new `shipped_group` region (add a test in
      `test_dashboard.py` asserting a click on a shipped card's button resolves to
      the button, not its group header) and that `_tui_focusables` includes both
      new toggle regions so keyboard nav reaches them.

## 3. Version bump & verification

- [x] 3.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json` (0.6.21 -> 0.6.22), since this
      change touches `plugins/s/`.
- [x] 3.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` and confirm the whole suite passes.
- [x] 3.3 [req: *] Manually launch `python3
      plugins/s/skills/build/scripts/dashboard.py tui` and confirm: Enter/click
      on an initiative or epic row folds/unfolds it (`▾`/`▸`); the SHIPPED column
      shows per-epic headers that fold their cards; and panel-node collapse and
      shipped-group collapse operate independently.
