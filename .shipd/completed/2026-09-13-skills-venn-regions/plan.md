# skills-venn-regions
Status: verified

## Idea

Put a short name in each Venn region and move the twenty-five skill names into
a list beneath the diagram, so the picture reads at a glance and the detail
stays legible on a phone.

### Motivation

Every region of the skills Venn currently holds its whole skill list — one runs
to 109 characters — so the text spills past its own circle, collides with the
set labels, and forces a canvas no phone can show without scrolling.

### Details

- Replace each region's `text` in the `venn-beta` fence with a short name for
  what that region holds.
- Add a list beneath the fence naming every skill under its region, so nothing
  is lost from the page.

Affected capabilities: `project-readme` (modified `cheatsheet-doc`). Impact:
`docs/cheatsheet.md`; no new dependencies.

### Non-goals

- No change to the three sets or to which region a skill belongs to. This
  change moves names out of the circles; it does not re-sort them.
- No `title` line and no `style` line in the fence — the corpus stays
  presentation-free.
- No change to either command table, and no second diagram.

## Implementation

- **Region names are short because the regions are small.** The three
  intersection regions and the centre are a fraction of a circle's area, so
  their text wraps to two or three words before it collides with its
  neighbours. Verified by rendering this fence through the site's own
  toolchain: at a 360px viewport the panel carries the diagram with zero
  horizontal overflow, against 35px of overflow for the same geometry holding
  the skill lists.
- **The list carries every skill, in region order.** It repeats the three set
  names as written in the fence, then the four overlap regions, so a reader
  moving from a circle to the list finds the same word. This is the surface
  that has to stay readable on a phone, and plain markdown always is.
- **`s:NAME` stays the spelling.** The list names each skill exactly as the
  `/s:` table's rows do, minus the leading slash, so the two surfaces agree.
- Risk: the diagram alone no longer says which skills sit where, so a reader
  who sees only the picture learns the shape and not the roster. That is the
  trade this change makes deliberately — the roster was illegible inside the
  circles, and it sits directly beneath them.
