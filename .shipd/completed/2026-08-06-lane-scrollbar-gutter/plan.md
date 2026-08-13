# lane-scrollbar-gutter
Status: verified

## Idea

Reserve a stable scrollbar gutter on every lane so lane content and the
scrollbar can never occupy the same cells, whatever the scroll state or
refresh timing.

### Motivation

On the live board the shipped lane's scrollbar visually collides with the
group headers' open controls; headless probes of static, narrow, and
grown-into-scrolling boards all lay out cleanly, so the collision depends on
a live condition we cannot reproduce deterministically — the structural fix
is to stop sizing content conditionally on scrollbar presence at all.

### Details

- Every lifecycle `Lane` reserves its vertical scrollbar's column
  permanently (`scrollbar-gutter: stable`), so row width is identical
  whether or not the lane currently scrolls, and nothing ever reflows or
  collides when the scrollbar appears.
- The board-screen sweep additionally asserts the invariant the gutter
  provides: lane content width is unchanged by content growth that makes
  the scrollbar appear, and no header button intersects the scrollbar's
  region.

Affected capabilities: `delivery-dashboard` (added requirement). Impact:
`plugins/s/skills/build/scripts/dashboard.py`,
`plugins/s/skills/build/tests_textual/test_dashboard.py`,
`plugins/s/.claude-plugin/plugin.json`. No new dependencies.

### Non-goals

- No scrollbar restyling (colors/size stay as themed).
- No changes to row layout — the gutter only fixes the column the rows are
  sized against.

## Implementation

- **One CSS property**: `Lane { scrollbar-gutter: stable; }` in the app-level
  Lane rule. Textual reserves the scrollbar column even while the scrollbar
  is hidden, making content width a constant of the lane rather than a
  function of scroll state. Rejected: right-padding on rows — it papers over
  the collision without removing the conditional reflow that causes it.
- **Sweep extension**: `assert_board_rows_contained` gains two assertions —
  (a) with the lane's vertical scrollbar displayed, every group-header
  button's region is disjoint from the scrollbar's region; (b) growing the
  board from a non-scrolling to a scrolling shipped lane via
  `refresh_board()` leaves the lane's scrollable content width unchanged.
- **Risk**: a permanently reserved 2-cell gutter narrows every lane slightly
  even when nothing scrolls — accepted; stable width is the point.
