# epic-menu-float
Status: verified
Theme: developer-experience

## Idea

Float the epic group header's `≡` menu control on its own layer so the
control stops shrinking every member card in the group.

### Motivation

The menu control is the `Collapsible`'s trailing flex sibling, but that
`Collapsible` holds the group's member cards as well as its title, so the
control's three reserved cells are taken from every card in the group — at 100
columns a card has 7 characters of slug left, and slugs ellipsize on lanes that
have room for them. Only the header's title line has anything to make way for.

### Details

- The menu control moves to a `menu` layer on the group header row, docked to
  the row's trailing edge with a one-cell inset off the lane's scrollbar
  gutter; the `Collapsible` beneath it spans the lane's full content width.
- The title line — and only the title line — reserves the control's cells
  through `CollapsibleTitle`'s own right padding, so an overlong title still
  ellipsizes before the glyph and is never painted under it.
- The three placement tests that assert the old flex ordering assert the
  float's invariant instead: the title's *content* region ends at or before
  the control's left edge.

Affected capabilities: `delivery-dashboard` (modified: `board-epic-grouping`).
Impact: `plugins/s/skills/build/scripts/dashboard.py`,
`plugins/s/skills/build/tests_textual/test_dashboard.py`,
`plugins/s/.claude-plugin/plugin.json`. No new dependencies.

### Non-goals

- No change to what the control does — the action menu, its Run/View gating,
  the confirmation flow, and the anchored popup are untouched.
- No change to the control's size (three cells, one row) or its glyph.
- No change to initiative-mode headers or the standalone pseudo-group, neither
  of which carries a menu control.
- No change to the lane's stable scrollbar gutter, the card ellipsis
  behaviour, or the group band's extent.

## Implementation

- **Float on a layer, not an offset.** `.epic-group-row` declares
  `layers: group menu`; `.epic-group` takes `layer: group`, and
  `.epic-menu-button` takes `layer: menu; dock: right; margin-right: 1`.
  Because layout runs per layer, the `group` layer sees the row's full content
  region and the `Collapsible` keeps the lane's whole content width. Rejected:
  keeping the flex sibling and shrinking the control — the spec fixes the
  control at exactly three cells, and the cost is paid by the cards either way.
- **The title reserves, the cards do not.** `.epic-group CollapsibleTitle`
  takes `padding-right: 4` — exactly the control's three cells plus its
  one-cell inset — so the title's content region ends precisely where the
  control begins. Measured at 80/120/140/200 columns, collapsed and expanded:
  `title.content_region.right == menu.region.x`, so the title ellipsizes
  before the glyph and never underlaps it.
- **Why this is not the layout `header-controls-flex` deleted.** That change
  removed an overlay that clamped controls over the *clipped title tail* using
  construction-time `styles.offset` plus an `on_resize` handler, and it did so
  when the row carried three trailing elements. This float adds no offset, no
  resize handler and no clamp — a static dock — and reserves the title's cells
  up front, which is exactly the property the old overlay lacked. The
  requirement's guarantee that the control never overlaps the title and is
  never painted over clipped text is preserved verbatim.
- **Effect.** Card text width goes 7 → 10 characters at 100 columns, 15 → 18
  at 140, and 31 → 34 at 220.

Risk: a future style that gives the control a different width would silently
desynchronise the title's `padding-right` reservation and let text slide under
the glyph. Guard: the placement tests assert the title's content region against
the control's live region rather than a constant, so a width change fails them.
