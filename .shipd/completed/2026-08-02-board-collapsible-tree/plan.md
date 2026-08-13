# board-collapsible-tree
Status: verified
Theme: developer-experience

## Idea

Make the board's hierarchy panel and its SHIPPED column collapsible: each
initiative and epic node folds independently, and the (long) SHIPPED column
groups its cards under collapsible per-epic headers.

### Motivation

The board's hierarchy panel renders every initiative → epic → change row at
once, so a workspace with many `complete` epics is a wall of text you cannot
fold; and the SHIPPED kanban column is one long flat list of every archived
member. There is no way to collapse the noise to focus on what is in flight.

### Details

- Add per-node collapse to the hierarchy panel: each initiative and epic row
  becomes an individually collapsible node (marker `▾` expanded / `▸`
  collapsed), toggled by Enter or click. A collapsed initiative hides its epics
  and their members; a collapsed epic hides its theme and members. Nodes start
  expanded.
- Group the `shipped` kanban column under collapsible per-epic headers (each with
  the same `▾`/`▸` marker); the other four columns stay flat. A collapsed group
  hides its cards.
- Hierarchy-node collapse and shipped-group collapse are **independent** states.

Affected capability: `delivery-dashboard` (modified `board-tui`). Impact:
`plugins/s/skills/build/scripts/dashboard.py` (`layout_board`, the tree/kanban
emission, `region_at` consumers, `_tui_dispatch`, and the `tui` `state` dict),
tests in `plugins/s/skills/build/tests/test_dashboard.py`, plugin version bump.
Stdlib-only (`curses`), per the constitution.

### Non-goals

- No collapse of the other four kanban columns (`unplanned`/`ready`/`building`/
  `review`) — only `shipped` groups, since only it grows long.
- No initiative-level nesting inside the SHIPPED column — per-epic headers only.
- No coupling between panel-node collapse and shipped-group collapse — folding an
  epic in the panel does not fold its SHIPPED group.
- No persistence of collapse state across sessions or `--interval` redraws is
  added beyond the in-memory tui `state` (it already survives redraws; it resets
  on quit, unchanged from `panel_open`).
- No auto-collapse of `complete` epics on launch — everything starts expanded.

## Implementation

- **Collapse state lives in the tui `state` dict, threaded into the pure
  layout.** `layout_board` gains two set-valued keyword args —
  `collapsed_nodes` (node keys for folded initiatives/epics) and
  `collapsed_shipped` (epic slugs whose SHIPPED group is folded) — defaulting to
  empty (fully expanded), so the function stays pure and every collapse
  permutation is unit-testable without a terminal. The `tui` loop seeds
  `state["collapsed_nodes"] = set()` and `state["collapsed_shipped"] = set()`
  and passes them in each redraw. Rejected: a persisted collapse file — out of
  scope and inconsistent with the in-memory `panel_open`.
- **Node keys are `(kind, slug)` tuples.** `("init", <slug-or-None>)` for an
  initiative group (the workspace-wide bucket keyed on `None`) and
  `("epic", <slug>)` for an epic. The panel's initiative and epic `tree_row`
  regions carry the new action `toggle_node` plus their `node` key; a collapsed
  initiative skips emitting its epics, a collapsed epic skips its theme + member
  rows. Each collapsible row's text is prefixed with `▾`/`▸`.
- **SHIPPED grouping is a kanban-render change.** When laying out the `shipped`
  column, partition its members by epic (in board order), emit a header line per
  epic with the `▾`/`▸` marker and a `shipped_group` region (action
  `toggle_shipped_group`, carrying the epic slug); when the epic is in
  `collapsed_shipped`, place no cards under it. The other columns keep the
  existing flat placement. Rejected: reusing `collapsed_nodes` for both — the
  user asked for independent states.
- **Dispatch handles the two new toggle actions.** `_tui_dispatch` adds cases for
  `toggle_node` (flip membership in `state["collapsed_nodes"]`) and
  `toggle_shipped_group` (flip membership in `state["collapsed_shipped"]`),
  alongside the existing `toggle_panel` and `card_button` cases; `region_at` and
  `_tui_focusables` already generalize over region kinds, so both new regions are
  navigable and clickable with no shell changes beyond dispatch. Rejected:
  repurposing the dead `select_epic`/`select_member` actions as-is — replace them
  with `toggle_node` on the collapsible rows.

Risk: card-button actions must still win the hit-test over new header regions;
guarded by keeping `card_button` first in `region_at`'s ordering and giving
`shipped_group`/`tree_row` the same non-overlapping row geometry as today.
