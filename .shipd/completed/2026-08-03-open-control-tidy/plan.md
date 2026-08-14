# open-control-tidy
Status: verified

## Idea

Even out the epic header's open control: exactly three cells wide like the run
control, with a one-cell gap separating it from the run control.

### Motivation

The open control renders four cells wide and flush against the run control:
Rich measures the `☰` glyph as two cells (`cell_len("☰") == 2`), so the
`width: auto` compact button comes out one cell wider than the run control's
three, and the pack-adjacent layout leaves no separation between the two
filled button blocks.

### Details

- Swap the open control's glyph `☰` → `≡` (`IDENTICAL TO`, U+2261 — same
  hamburger look, measured one cell by Rich) and pin `.compact-button` to
  `width: 3`, so every compact control is exactly three cells wide.
- Separate the run and open controls by a one-cell gap; the open control
  stays flush to the title when no run control renders.

Affected capability: `delivery-dashboard` (modified `board-epic-grouping`).
Impact: `plugins/s/skills/build/scripts/dashboard.py`,
`plugins/s/skills/build/tests_textual/test_dashboard.py`, and the plugin
version bump in `plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- No change to any control's behavior, routing, or the placement mechanism
  (layer overlay, offsets) beyond the one-cell gap.
- No glyph change for the run (`▶`) or close (`✕`) controls — both already
  measure one cell.

## Implementation

- **Glyph swap, not width fudging.** `≡` measures one cell under the pinned
  Rich (verified: `cell_len("≡") == 1`, `cell_len("☰") == 2`), so the button's
  content+padding is 3 exactly. Rejected: keeping `☰` and forcing `width: 3`
  — Rich still counts the glyph as two cells, so the 1-cell content area
  would clip/misrender it.
- **Pin the width in CSS.** `.compact-button` replaces `width: auto;` with
  `width: 3;`, keeping `min-width: 3;` alongside it — Textual's base `Button`
  rule sets `min-width: 16`, which clamps any button that stops overriding it — "exactly three cells wide" becomes a
  stylesheet contract, and a future 2-cell glyph fails the width/geometry
  tests instead of silently widening the control.
- **Gap via conditional margin in flow.** In `_mount_epic_groups`'s `_flush`,
  when a run control is constructed, set
  `open_button.styles.margin = (0, 0, 0, 1)` (one-cell left margin). The
  `controls` layer keeps horizontal flow, so the margin yields
  `open.x == run.right + 1`; with no run control there is no margin and the
  open control stays flush at the title's right edge (unchanged scenario).
  Rejected: giving the open button its own computed offset — the flow +
  margin already encodes the adjacency without duplicating the width math.
- **Tests pin the contract.** `EpicHeaderControlPlacementTest` asserts the
  one-cell gap (`open.region.x == run.region.right + 1`) and `width == 3` on
  both header controls; `CompactControlTest` adds `width == 3` alongside the
  existing `height == 1` for all five compact controls (header pair and the
  three modal ✕ controls, which already measure 3 via their 1-cell glyphs).
