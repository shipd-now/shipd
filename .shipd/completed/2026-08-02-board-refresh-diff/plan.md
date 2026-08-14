# board-refresh-diff
Status: verified

## Idea

Make the board's live refresh diff-aware: only remount the lanes and hierarchy
panel whose content actually changed since the last tick, so an idle board never
repaints and the SHIPPED column stops flashing every interval.

### Motivation

`BoardApp.refresh_board()` runs every `--interval` (default 2s) and
unconditionally `remove_children()`s every lane, re-mounts all `TaskCard`s,
rebuilds the shipped `Collapsible` groups, and `tree.clear()`s the hierarchy
panel — so even an idle board tears down and repaints the whole tree each tick,
producing a visible flash (worst in the SHIPPED column) and, as a side effect,
resetting any shipped group the user collapsed.

### Details

- Compute a cheap, deterministic **content signature per lane and for the tree**
  from the aggregated board (per lane: the ordered `(epic, member, lane-state,
  stage, actions)` of its cards, plus the shipped per-epic group headers; for the
  tree: the initiative → epic → change structure).
- On each refresh, compare each lane's / the tree's new signature to the stored
  one and **only** `remove_children()`+remount the ones that changed; skip
  unchanged lanes and the tree entirely. Store the signatures on the app.
- Wrap any actual rebuild in `with self.batch_update():` to coalesce mounts and
  avoid intermediate flicker.

Affected capability: `delivery-dashboard` (modified `board-tui`). Impact:
`plugins/s/skills/build/scripts/dashboard.py` (`_render_lanes`, `_render_tree`,
`refresh_board`/`on_mount`, new signature helpers), tests in
`plugins/s/skills/build/tests_textual/`; plugin version bump.

### Non-goals

- No per-card in-place reconciliation within a changed lane — a lane that
  genuinely changed still rebuilds wholesale (rare; only during a live run).
- No change to the refresh cadence, the `--interval` flag, or the board data
  layer (`build_board` etc.).
- No change to rendering, colours, collapse controls, or actions beyond the
  refresh path.

## Implementation

- **Signatures are pure and derived from the board only.** Add
  `_lane_contents(board)` returning, per lane name, the ordered list of card
  specs `(epic_slug, member, entry)` plus the shipped group order — the exact
  data `_render_lanes` mounts — and `_lane_signature(cards)` /
  `_tree_signature(board)` returning hashable tuples. Signatures depend solely on
  board-derived content, never on transient UI state, so a collapsed shipped
  group (UI state) does not appear in the signature and therefore survives
  because its lane is not rebuilt. Rejected: signing the rendered widget tree —
  it couples the check to `textual` and defeats the point.
- **`_render_lanes` becomes a diff.** Build `_lane_contents(self.board)`; for each
  lane whose signature differs from `self._lane_sigs.get(name)`, and only those,
  `remove_children()` then mount its cards (shipped under its `Collapsible`
  groups), inside `with self.batch_update():`; update `self._lane_sigs`. An
  unchanged lane is left exactly as-is (no teardown → no flash, collapse
  preserved). `_render_tree` gains the same guard against `self._tree_sig`.
  Initialise the stores empty in `__init__`/`on_mount` so the first
  `refresh_board()` renders everything.
- **Testability.** The signature helpers are deterministic and unit-tested; the
  no-repaint behavior is asserted with a `Pilot` test that captures `TaskCard`
  widget identities across an unchanged-board `refresh_board()` (same objects ⇒
  not remounted) and that a collapsed shipped group stays collapsed. These live
  in `tests_textual/` (they import `dashboard`, which needs `textual`).

Risk: a signature that omits a field the render depends on would wrongly skip a
needed repaint; guarded by deriving the signature from the very
`_lane_contents` the renderer consumes, and by the changed-board scenario that
asserts a moved member repaints its lanes.
