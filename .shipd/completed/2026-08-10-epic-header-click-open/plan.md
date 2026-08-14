# epic-header-click-open
Status: verified
Theme: developer-experience

## Idea

Drop the epic group header's `≡` menu control and its anchored action menu.
Clicking an epic header opens the epic straight away; the collapse/expand
toggle fires **only** when the little arrow is clicked. The epic-level **Run**
action moves inside the epic-detail modal.

### Motivation

The epic header today carries a floated `≡` control that opens a small
View/Run action menu — an extra hop for the common case (just look at the
epic) and an extra control to reach for. The whole header row otherwise does
nothing on click except toggle collapse. Making the header itself open the
epic, and reserving the arrow for collapse, collapses two clicks into one and
removes a control. Run epic was the menu's only other item, so it needs a new
home: the epic-detail modal the header now opens.

### Details

- The `≡` control, its `EpicActionMenuScreen` popup, and the `_push_epic_menu`
  routing all go away. The epic group header row holds only the collapse arrow
  and the title.
- A click on the header title's **leading arrow cell** toggles the group's
  collapsed state (and opens nothing); a click **anywhere else** on the title
  opens the epic-detail modal (and never changes the collapsed state).
- The epic-detail modal gains a **Run epic** control, shown only when the epic
  is runnable (`epic_is_runnable`) and not already showing the stall banner's
  Retry. It opens the existing `EpicRunConfirmScreen`; the epic-level run still
  dispatches only on that modal's **Yes**.
- No change to the board's data layer, to initiative/none modes, to the
  standalone pseudo-group, or to the confirmation modal's copy and wiring.

Affected capabilities: `delivery-dashboard` (modified: `board-epic-grouping`).
Impact: `plugins/s/skills/build/scripts/dashboard.py`,
`plugins/s/skills/build/tests_textual/test_dashboard.py`,
`plugins/s/.claude-plugin/plugin.json`. No new dependencies.

### Non-goals

- No change to what running an epic does — the same autopilot launch, the same
  confirmation copy ("This will deliver the full epic, …"), the same
  dispatch-only-on-Yes rule.
- No change to the stall banner's **Retry run** path (unchanged; the new Run
  epic control is gated off when the stall banner is showing).
- No change to initiative-mode headers, the standalone pseudo-group, the
  grouping segmented control, or the `g` cycle.
- No keyboard-behavior change to the collapse toggle (`Enter` on a focused
  header still toggles).

## Implementation

Binding technical decisions the sub-agent must follow:

### Header click routing (`dashboard.py`)

- Import `CollapsibleTitle` from `textual.widgets.collapsible`, `on` from
  `textual`, and `Message` from `textual.message`.
- Add `EpicCollapsibleTitle(CollapsibleTitle)` carrying `epic_slug`. Override
  `_on_click(self, event)` to `event.stop()` then branch on `event.offset.x`:
  the title renders as `<pad-left><arrow> <label>` with `CollapsibleTitle`'s
  default `padding: 0 1`, so the arrow glyph sits at widget column **1**. When
  `event.offset.x <= 1` (the left pad + arrow cell) post the inherited
  `self.Toggle()` message; otherwise post a new `EpicCollapsibleTitle.OpenEpic`
  `Message` carrying `self.epic_slug`. Do **not** post both.
- Add `EpicCollapsible(Collapsible)`: accept an `epic_slug` kwarg, call
  `super().__init__(...)`, then replace `self._title` with an
  `EpicCollapsibleTitle(label=title, collapsed_symbol="▶",
  expanded_symbol="▼", collapsed=collapsed, epic_slug=epic_slug)`. Because
  `Collapsible.compose` yields `self._title` and `_update_collapsed` /
  `_watch_title` drive `self._title`, the subclassed title keeps the toggle and
  label wiring; `Collapsible._on_collapsible_title_toggle` still handles the
  inherited `Toggle`.
- In `_mount_epic_groups._flush`, build an `EpicCollapsible` (not `Collapsible`)
  with the same `id="epic-group-<lane>-<slug>"`, `classes="epic-group"`, and
  pass `epic_slug=group_slug`. Drop the `≡` `menu_button` block entirely; the
  `EpicGroupRow` wraps only the collapsible. Keep `EpicGroupRow` and its
  `epic-group-row lane-item` classing (the panel band + divider + the tests
  that query it).
- On the board app, handle the open message with
  `@on(EpicCollapsibleTitle.OpenEpic)` (or the derived `on_...` handler)
  pushing `EpicDetailScreen(event.epic_slug)` onto the board stack. Remove
  `_push_epic_menu` and the `epic_menu_slug` branch in `on_button_pressed`
  (leave the search-clear, mode-button, and filter-chip branches intact).
- Remove the `EpicActionMenuScreen` class entirely, and drop it from any
  registry/CSS collections that reference it (e.g. the modal-CSS test map is a
  test-side change).

### Run epic in the epic-detail modal (`dashboard.py`)

- In `EpicDetailScreen.compose`, after the badge row and only when
  `epic_is_runnable(epic)` **and not** `epic_stalled(epic)`, yield an action
  row with a `Button("Run epic", id="epic-run", classes="button-primary")`.
- In `EpicDetailScreen.on_button_pressed`, handle `epic-run` by pushing
  `EpicRunConfirmScreen(self.epic_slug)` (do **not** dispatch directly — the
  run fires only from that modal's Yes, exactly as before). Keep the existing
  `epic-detail-close` and `epic-retry` branches.

### CSS (`dashboard.py`)

- Remove the `.epic-menu-button` rule and the `menu` layer: drop `menu` from
  `.epic-group-row { layers: … }` (leaving just `group`, or remove the
  `layers`/`layer` pairing if `group` is then unused — but keeping
  `.epic-group-row .epic-group { layer: group }` harmlessly is fine).
- In `.epic-group CollapsibleTitle`, change `padding-right: 4` to
  `padding-right: 1` (no control to clear now; keep a one-cell gutter so long
  titles still ellipsize before the lane's scrollbar).

### Tests (`tests_textual/test_dashboard.py`)

- Delete the menu-specific machinery and tests: the `_open_epic_menu` /
  `_choose_menu_item` helpers, `EpicActionMenuTest`, and every test asserting
  the `≡` control, its float geometry, or the View/Run action-menu items
  (`test_menu_control_*`, `test_runnable_epic_menu_offers_run_and_view`,
  `test_non_runnable_epic_menu_offers_only_view`, the menu-anchor/dismiss
  tests, `test_overlong_title_ellipsizes_beside_the_menu_control`,
  `test_runnable_epic_headers_have_exactly_one_menu_control`,
  `test_non_runnable_epic_headers_still_have_menu_control`, the
  `#menu-epic-*`/`.epic-menu-button` assertions in the standalone and
  initiative tests, etc.).
- For tests that reached the epic-detail modal *through* the menu (View epic),
  replace the two-step menu open with a single click on the header title (an
  offset clear of the arrow, e.g. `Offset(6, 0)` on the `CollapsibleTitle`) and
  assert `EpicDetailScreen` is pushed.
- Add tests: (a) clicking the header title (off the arrow) opens
  `EpicDetailScreen` and leaves the group's `collapsed` unchanged; (b) clicking
  the arrow cell toggles `collapsed` and pushes no modal; (c) the epic header
  has no `.epic-menu-button`; (d) a runnable epic's detail modal shows a
  `#epic-run` button whose activation pushes `EpicRunConfirmScreen`, and a
  non-runnable epic's detail modal has no `#epic-run`.
- Remove `EpicActionMenuScreen` from the modal-CSS registry test.

Run the textual suite (`pip install -r requirements.txt` first) and the
stdlib-only build tests; both must pass.
