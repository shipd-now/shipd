# board-card-spacing
Status: verified
Theme: developer-experience

## Idea

Give button-less kanban cards the same single blank-line separation as cards with
action buttons, instead of the two blank lines they get today.

### Motivation

`_place_card` in `dashboard.py` always steps onto a button row (`y += 1`) and then
advances the cursor by two, so a card with no action buttons — every archived
member in the SHIPPED column — leaves an empty reserved button row *plus* a gap
row, double-spacing the whole column and wasting vertical space.

### Details

- Advance the column cursor from the **last row actually drawn** plus one blank
  line: a button-less card ends at its card row, a card with buttons ends at its
  button row, and either way exactly one blank line separates it from the next.
- Add a normative guarantee and a regression scenario that column cards are
  single-spaced regardless of whether they carry buttons.

Affected capability: `delivery-dashboard` (modified `board-tui`). Impact:
`plugins/s/skills/build/scripts/dashboard.py` (`_place_card` only), a test in
`plugins/s/skills/build/tests/test_dashboard.py`, plugin version bump.

### Non-goals

- No change to which cards carry buttons, or to the buttoned-card spacing (it is
  already one blank line and stays that way).
- No zero-gap "dense" mode — one blank line, matching the rest of the board.
- No change to the SHIPPED grouping, collapse behavior, or any other column.

## Implementation

- **Track the last drawn row inside `_place_card`.** Today the function does
  `y += 1` before the button loop unconditionally, then `col_cursor[column] =
  y + 2`. Change it to advance `y` past the card, draw any buttons on that next
  row, and set the cursor to `(last_drawn_row) + 2` where `last_drawn_row` is the
  button row only when a button was actually drawn, else the card row. Concretely:
  compute the card row `y0`, draw the card there; if the member has actions, draw
  the buttons on `y0 + 1` and set `col_cursor = y0 + 3`; otherwise set
  `col_cursor = y0 + 2`. Both leave exactly one blank line. Rejected: subtracting
  a line at the call sites — the off-by-one belongs where the rows are emitted,
  and `_place_card` is the single shared placement path (flat columns and the
  SHIPPED groups both call it), so fixing it here fixes every column at once.
- **The function stays pure-layout-only.** `_place_card` mutates the `lines`,
  `regions`, and `col_cursor` structures `layout_board` owns; no curses, so the
  spacing is asserted directly against `layout_board`'s output in a unit test.

Risk: none material — the change only removes a blank row from button-less cards;
buttoned cards' geometry (card row, button row, one gap) is unchanged, so the
existing card/button/region tests continue to hold.
