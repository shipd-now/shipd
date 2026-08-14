# control-overflow-clamp
Status: verified

## Idea

Clamp the epic header's inline controls inside their lane: when the rendered
title is wider than the lane, the `▶`/`≡` pin at the lane's right edge over
the clipped title instead of being pushed out of the lane and clipped away.

### Motivation

An initiative-suffixed title (e.g. `mikk-knowledge [complete] ·
context-enhancements`, 42 rendered cells in a 35-cell lane on the live board)
pushes the fixed-offset controls past the lane boundary, where the compositor
clips them — the open control becomes invisible and unreachable, and
near-boundary cases paint partial button slivers into the lane gutters.

### Details

- Introduce an `EpicGroupRow` container (subclass of `Horizontal`) that owns
  the placement of its run/open controls and recomputes it on every resize,
  clamping the offset to the row's actual width.
- `_mount_epic_groups` mounts `EpicGroupRow` instead of an anonymous
  `Horizontal` and no longer sets offsets itself.

Affected capability: `delivery-dashboard` (modified `board-epic-grouping`).
Impact: `plugins/s/skills/build/scripts/dashboard.py`,
`plugins/s/skills/build/tests_textual/test_dashboard.py`, and the plugin
version bump in `plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No title truncation and no fix for the swallowed `[status]` markup (tracked
  separately).
- No change to control size, styling, gap, modal behavior, or the data layer.

## Implementation

- **`EpicGroupRow(Horizontal)` owns placement.** Constructed with the header
  `title` text and its `run_button`/`open_button` references (either may be
  `None`); its `on_resize` handler computes
  `x = max(0, min(5 + rendered_title_width, content_width - controls_width))`
  — `rendered_title_width = Text.from_markup(title).cell_len` (the markup-
  consumed width, as before), `controls_width = 7` when a run control is
  present (3 + 1-cell gap + 3) else `3` — and assigns `styles.offset = (x, 1)`
  to both buttons. Both get the identical offset; the shared `controls` layer's
  horizontal flow plus the open control's existing 1-cell left margin keep
  run-then-open packing exactly as today.
- **Hybrid placement: mount-time first pass, `on_resize` clamp pass.** The
  unclamped offset (`5 + rendered width`) is assigned at construction exactly
  as today — a single layout pass, so tests and clicks that never trigger the
  clamp see byte-identical timing and geometry. `on_resize` (which fires
  after first layout, on terminal resizes, and on lane remounts — the moments
  the row's real width is known) recomputes the clamped x and reassigns the
  offset **only when it differs**, so an unclamped row never schedules a
  second layout. Rejected: clamping at mount against `lane.region` — regions
  are not laid out yet (zero-size) at mount time, so only the unclamped part
  is computable there; rejected: pure `on_resize` placement — the first
  correct position would then need an extra layout pass that click-driving
  tests do not wait for; rejected: CSS-only — Textual CSS cannot express
  "row width minus controls" as an offset.
- **Pinned controls paint over the clipped title tail** (they sit on the
  higher `controls` layer). Deliberate: control reachability beats reading the
  last cells of an already-clipped title, and it matches the pre-inline
  layout's always-visible far-edge behavior.
- **Single placement owner.** The offset assignments (and their explanatory
  comments) move out of `_flush` into `EpicGroupRow`; `_flush` only constructs
  the row with its parts. The unclamped short-title result is unchanged
  (`x = 5 + rendered width`), so short-title geometry is unchanged wherever
  the lane is wide enough. At the suite's default 80-column size lanes are
  only 13 cells wide, so even the short fixtures clamp — the after-title
  placement tests therefore run at `size=(200, 24)`, where their premise (a
  title that fits) actually holds; the clamp tests own the overflow case.
- **Tests pin the clamp.** A long-title fixture asserts both controls render
  fully inside the lane, keep the 1-cell gap, and that clicking the pinned
  open control still opens the epic-detail modal.
