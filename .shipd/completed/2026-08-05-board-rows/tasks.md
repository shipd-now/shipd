# Tasks — board-rows

## 1. Group header per-lane count (pure helper)

- [x] 1.1 [req: board-epic-grouping] Test-first: in
      `plugins/s/skills/build/tests_textual/test_dashboard.py`, beside
      `EpicGroupTitleStallTest`, add tests for `epic_group_title`'s new
      keyword-only `count` parameter: (a) `count=2` appends `" · 2"` as the
      title's final segment, after the initiative segment when one is present
      and directly after the `[status]` token otherwise; (b) `count=None`
      (the default) returns output byte-identical to today's, stalled and
      not. Run `~/.cache/shipd/tui-venv/bin/python -m unittest discover -s
      plugins/s/skills/build/tests_textual` and observe the new tests fail.
- [x] 1.2 [req: board-epic-grouping] In
      `plugins/s/skills/build/scripts/dashboard.py`, add the keyword-only
      `count=None` parameter to `epic_group_title`, appending `" · %d" %
      count` after the initiative segment (before the stall-marker prefix
      logic, which wraps the whole title). Confirm task 1.1's tests pass.

## 2. One-row task rows with risk glyphs

- [x] 2.1 [req: board-tui, board-shipd-theme] Test-first: in
      `test_dashboard.py`, add row-text tests for `TaskCard._card_text`:
      high risk → `"[$risk-high]●[/] <slug>"`, medium → `$risk-medium`, low
      → `$risk-low`, missing/unknown risk → `"[$fg-muted]●[/] <slug>"`; a
      `driving` entry at stage `build` appends `"[$fg-muted] · build[/]"`; a
      shipped member (`_member_column(member, entry) == "shipped"`) renders
      `"[$fg-subtle]✓[/] <slug>"` with no risk glyph; an active search query
      still wraps the matched slug span in `[$accent]…[/]`. Add structural
      CSS asserts on `BoardApp.CSS`: no `border-left` rule for `TaskCard` or
      `.risk-*`, no `margin` rule on `TaskCard`, and a `height: 1` on
      `TaskCard`. Add one mounted-app assertion (via `run_test`) that a
      high-risk card renders without markup errors and its `_card_text`
      markup resolves (querying the card's rendered content raises nothing) —
      the custom-variable markup path `[$text-error]` already exercises.
      Observe the new tests fail.
- [x] 2.2 [req: board-tui, board-shipd-theme] In `dashboard.py`, rewrite
      `TaskCard._card_text` to the glyph form of task 2.1 (drop the
      `"%s [%s]"` slug-risk format), remove the `add_class("risk-%s")` call
      in `TaskCard.__init__`, and in `BoardApp.CSS` delete the `TaskCard`
      `border-left` accent-bar rule, the three `TaskCard.risk-*` blocks, and
      the `margin: 0 0 1 0`, adding `height: 1` in their place (`padding: 0
      1` and `TaskCard:focus` stay). Amend the existing tests that assert
      the old `slug [risk]` text or the `risk-*` class. Confirm task 2.1's
      tests pass.

## 3. Tinted per-lane header bands

- [x] 3.1 [req: board-tui] Test-first: in `test_dashboard.py`, assert that a
      mounted app carries, inside each of the five `#lane-<name>` `Lane`s,
      one `.lane-header` `Static` whose text is the lane name uppercased;
      that `Lane.border_title` is no longer set; and structurally that
      `BoardApp.CSS` holds a `.lane-header` block with `dock: top` and five
      `#lane-<name> .lane-header` blocks each referencing `$lane-<name>` for
      both `background` and `color`. Observe the tests fail.
- [x] 3.2 [req: board-tui] In `dashboard.py`, give `Lane` a `compose()`
      yielding `Static(self.lane_name.upper(), classes="lane-header")`,
      delete the `self.border_title` assignment, and add the `.lane-header`
      CSS of task 3.1 (`dock: top; height: 1; padding: 0 1; text-style:
      bold;` plus the five per-lane tint blocks, `background:
      $lane-<name> 15%; color: $lane-<name>;`). Confirm task 3.1 passes.
- [x] 3.3 [req: board-tui] In `_render_lanes`/`_mount_epic_groups`, tag every
      widget mounted into a lane with class `lane-item` (flat-mode
      `TaskCard(..., classes="lane-item")`, `EpicGroupRow(...,
      classes="epic-group-row lane-item")`) and replace `await
      lane.remove_children()` with `await
      lane.remove_children(".lane-item")`. Add a test: mount, force a
      content repaint (a changed board via `board_fn`), and assert the
      `.lane-header` widget instance in an affected lane is the same object
      before and after while the lane's cards were remounted.

## 4. Per-lane empty-state texts

- [x] 4.1 [req: board-tui] Test-first: add tests asserting (a) on a board
      where a lane holds no members, that lane mounts one `.lane-empty`
      `Static` carrying that lane's `LANE_EMPTY_TEXTS` entry; (b) when a
      subsequent refresh maps a member into that lane, the empty text is
      gone and the member's row is mounted; (c) a search query matching no
      member of a lane leaves that lane showing its empty text. Observe the
      tests fail.
- [x] 4.2 [req: board-tui] In `dashboard.py`, add the module-level
      `LANE_EMPTY_TEXTS` dict (unplanned "nothing unplanned", ready
      "nothing ready", building "nothing building", review "nothing in
      review", shipped "nothing shipped yet"); in `_render_lanes`, when a
      repainting lane's filtered content is empty, mount
      `Static(LANE_EMPTY_TEXTS[lane_name], classes="lane-empty lane-item")`;
      add `.lane-empty { color: $fg-subtle; text-style: italic; padding: 0
      1; }` to `BoardApp.CSS`. Confirm task 4.1 passes.

## 5. One-row epic group headers

- [x] 5.1 [req: board-epic-grouping] Test-first: add tests asserting (a)
      `BoardApp.CSS`'s `.epic-group` block sets `border-top: none` and
      `padding-bottom: 0`, and a `.epic-group Contents` (or equivalent
      selector) block sets top padding 0; (b) on a mounted grouped board,
      a group's run and open buttons carry `styles.offset` y == 0; (c) a
      mounted group header's `Collapsible.title` ends with `" · <n>"` where
      `<n>` is that epic's card count in that lane (two-member fixture).
      Observe the tests fail.
- [x] 5.2 [req: board-epic-grouping] In `dashboard.py`: extend the
      `.epic-group` CSS with `border-top: none; padding-bottom: 0;` (keep
      the textual default `padding-left: 1` — `EpicGroupRow`'s title-x
      constant 5 depends on it) and add `.epic-group Contents { padding: 0 0
      0 2; }`; change both offset assignments in `EpicGroupRow` (constructor
      and `on_resize`) from `(x, 1)` to `(x, 0)`; in
      `_mount_epic_groups._flush`, pass `count=len(group_cards)` to
      `epic_group_title`. Amend existing tests that assert the old title
      format where needed. Confirm task 5.1 passes and the existing
      overlong-title clamp and stall-marker tests still pass.

## 6. Verification and version bump

- [x] 6.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version
      0.6.47 → 0.6.48 (every `plugins/s/` change bumps in its own PR).
- [x] 6.2 [req: *] Run both suites and fix any remaining amended assertions:
      `python3 -m unittest discover -s plugins/s/skills/build/tests` (must
      pass with no `textual` installed — this change adds nothing there) and
      `~/.cache/shipd/tui-venv/bin/python -m unittest discover -s
      plugins/s/skills/build/tests_textual` (all board tests green,
      including the untouched search, palette, stall, and diff-aware
      refresh suites).
