# header-controls-flex
Status: verified

## Idea

Replace the epic group header's overlay-positioned run/open controls with an
honest flex layout — ellipsized title, reserved-width trailing controls, the
count as the row's final segment — and give the epic-detail modal's stall
banner its missing breathing room.

### Motivation

Since the count and initiative segments landed, every group header title is
longer than its lane, so the overlay clamp — designed as a rare fallback —
now pins the controls over the clipped title tail on every row, reading as
buttons pushing text out of the UI; separately, the stall banner sits flush
against the member list below it and its text hugs the banner's left edge.

### Details

- Group header rows become plain flex: the collapsible title truncates with
  an ellipsis in its own `1fr` space; the run/open controls are ordinary
  trailing children with reserved width; the per-lane count renders after
  the controls as the row's final segment. The layer/offset/resize-clamp
  machinery is deleted.
- The stall banner gets one blank row below it and its content inset two
  more cells from the left edge.

Affected capabilities: `delivery-dashboard` (modified: `board-epic-grouping`,
`board-stall-signal`). Impact:
`plugins/s/skills/build/scripts/dashboard.py`,
`plugins/s/skills/build/tests_textual/test_dashboard.py`,
`plugins/s/.claude-plugin/plugin.json`. No new dependencies.

### Non-goals

- No change to which controls render (runnable gating), what they dispatch,
  the confirmation flow, or the epic/spec modals' content.
- No change to grouping modes, signatures, or the diff-aware refresh.
- No restyle beyond the banner spacing — colors and glyphs stay.

## Implementation

- **Flex row.** `EpicGroupRow` drops its layer overlays: children are
  `[Collapsible (width 1fr)] [run?] [open] [count]` in normal horizontal
  flow. Delete `layers: base controls` from `.epic-group-row`, the
  `layer:` rule on `.epic-run-button`/`.epic-open-button`, the
  construction-time `styles.offset`, `on_resize`, `_offset_x`, and the
  `Content.from_text` measuring (drop the import if now unused). The open
  control keeps its 1-cell left margin after a run control; give the run
  control the same 1-cell left margin against the title.
- **Ellipsized title.** App CSS sets the epic group's `CollapsibleTitle` to
  single-line ellipsis truncation (`text-overflow: ellipsis` with no wrap)
  so a long title shortens inside its own space and never underlaps the
  controls.
- **Count segment.** `_flush` stops passing `count=` into
  `epic_group_title` (the parameter and its byte-compat default stay for
  compatibility) and instead appends a muted `Static` (classes
  `epic-count`, content `str(len(group_cards))`, 1-cell left margin) as the
  row's last child. Initiative-mode headers are untouched (they carry no
  controls and no count).
- **Existing tests migrate.** The `tests_textual` cases asserting offset
  placement and the overlong-title clamp are rewritten to the flex
  contract: controls and count fully inside the lane, title region ending
  at or before the run control's left edge, count as the last child.
- **Stall banner spacing.** `#epic-stall-banner` padding goes from
  `0 1 1 1` to `0 1 1 3` (two more cells on the left) and the banner gains
  `margin: 0 0 1 0` (one blank row before the member list).
- **Risk**: `text-overflow: ellipsis` on `CollapsibleTitle` must not break
  the collapse-toggle click region — covered by the existing collapse
  scenario tests, which stay green unchanged.
