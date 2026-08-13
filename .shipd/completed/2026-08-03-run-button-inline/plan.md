# run-button-inline
Status: verified

## Idea

Move the epic group header's controls — the run control (`▶`) and the open
control (`☰`) — so they render inline, directly after the epic's title text
inside the group's panel, instead of floating at the far edge of the lane row
outside the group's visual box.

### Motivation

The board mounts each epic header's `▶` and `☰` as siblings of the full-width
`Collapsible` in the group row, so they land at the row's right edge —
visually detached from the epic they act on, outside the group's gray panel.

### Details

- Restyle both header controls as compact one-cell-high overlays on a
  `controls` layer of `.epic-group-row`, packed immediately after the
  collapsible title text on the title row: `▶` first (when the epic is
  runnable), then `☰`.
- The Buttons stay siblings of the `Collapsible`; the runnability guard, the
  confirmation modal, the epic-detail modal, and both dispatch routes are
  untouched.
- Compact every modal close (✕) control — `#close-detail`
  (`MemberDetailScreen`), `#epic-run-close` (`EpicRunConfirmScreen`),
  `#epic-detail-close` (`EpicDetailScreen`) — from the default three-row
  Button chrome to a single row, and give all compact controls (header and ✕)
  a tinted background with a hover state so they still read as clickable
  buttons.

Affected capability: `delivery-dashboard` (modified `board-epic-grouping`).
Impact: `plugins/s/skills/build/scripts/dashboard.py`,
`plugins/s/skills/build/tests_textual/test_dashboard.py`, and the plugin
version bump in `plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No change to run/confirm or epic-detail behavior, the runnability guard,
  the data layer, or the flat (ungrouped) rendering.
- No change to the group visuals beyond the controls' placement and their
  compact button styling; the confirm modal's Yes/No action buttons keep the
  standard Button chrome.

## Implementation

- **Placement mechanism — layer overlay, not re-parenting.** `.epic-group-row`
  gains `layers: base controls;`; `.epic-run-button` and `.epic-open-button`
  share one compact rule: `layer: controls; width: 3; min-width: 3;
  height: 1; border: none; padding: 0 1;`. `_mount_epic_groups`'s `_flush`
  sets `styles.offset = (5 + Text.from_markup(title).cell_len, 1)` on
  **both** buttons before mounting — the title's **rendered** cell width, not
  the raw string's: `epic_group_title` embeds `[status]`, which the
  `Collapsible` title consumes as Rich console markup, so `cell_len(raw)`
  overshoots by the bracket span's width. Widgets on a layer keep the
  container's horizontal flow, so the
  identical offset packs them adjacently after the title (`▶` then `☰`, or
  `☰` alone flush to the title when no run control renders). The x constant 5
  is the title row's fixed left chrome under the pinned `textual` 8.2.8
  (`Collapsible` `padding-left: 1` + `CollapsibleTitle` `padding-left: 1` +
  collapse symbol and space, 2 cells + `CollapsibleTitle` `padding-right: 1`);
  y=1 skips the `Collapsible`'s `border-top` row. Validated in a live
  prototype: with a 32-cell title, title region `(x=1, y=1, w=36, h=1)`, run
  at `(x=37, y=1, w=3, h=1)`, open at `(x=40, y=1, w=3, h=1)`.
  - Rejected: mounting the Buttons inside `CollapsibleTitle` with
    `dock: right` — a mounted child collapses the title's auto-sizing to
    height 0 under textual 8.2.8 (prototyped).
  - Rejected: keeping the far-edge siblings and recoloring the row — the
    controls stay visually outside the group, which is the reported defect.
- **Click separation is preserved by construction.** Both Buttons remain
  siblings of the `Collapsible` (never children of `CollapsibleTitle`), and
  `Button._on_click` stops the click event, so activating either control
  cannot reach the collapse toggle; `Button.Pressed` still bubbles to
  `BoardApp.on_button_pressed`, whose `epic_open_slug`-before-`epic_slug`
  routing is unchanged. Prototype-verified: button click → one `Pressed`,
  collapsed state unchanged; a title click still toggles.
- **`Text` import** joins the existing module-scope textual import block
  (`from rich.text import Text`) — `rich` ships as a dependency of the
  pinned `textual`, so import behavior without `textual` is unchanged.
- **Button-evident compact styling.** A compact (height 1, borderless) Button
  loses the default chrome that signals clickability, so all compact controls
  share an affordance: `background: $primary 25%` with
  `&:hover { background: $primary 50%; }` (the alpha-tint syntax the existing
  `TaskCard:focus` rule already uses, valid in both themes). Applied to
  `.epic-run-button`/`.epic-open-button` and the three modal ✕ controls via
  one shared `.compact-button` class added to each Button. The modal ✕
  controls keep their ids, screens, and handlers — only their size/style
  changes (`height: 1; border: none; padding: 0 1; min-width: 3;
  width: auto;`).
- **Risk — lane-width overflow.** A title wider than its lane clips, and the
  overlay controls clip with it (previously they stayed pinned at the row
  edge). Accepted: epic slugs are short kebab slugs, a clipped header already
  degrades the board, and the placement test pins the geometry so a `textual`
  upgrade that moves the chrome constants fails loudly rather than silently
  misplacing the controls.
