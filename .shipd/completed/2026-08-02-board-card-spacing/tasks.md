## 1. Single-space button-less cards

- [x] 1.1 [req: board-tui] In `plugins/s/skills/build/tests/test_dashboard.py`,
      add a test asserting single spacing: for a column of member cards with no
      actions, consecutive `card` regions' `y` differ by exactly 2 (one blank
      line, no reserved button row); and for a card that carries a button, the
      button row is `card_y + 1` and the next card is `card_y + 3`. Run it and
      observe it fail (button-less cards are currently spaced by 3).
- [x] 1.2 [req: board-tui] In `dashboard.py` `_place_card`, advance the column
      cursor from the last row actually drawn plus one blank line: place the card
      at `y0`; when the member has actions, draw the buttons on `y0 + 1` and set
      `col_cursor[column] = y0 + 3`; otherwise set `col_cursor[column] = y0 + 2`.
      Confirm 1.1 passes.

## 2. Version bump & verification

- [x] 2.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json` (0.6.22 -> 0.6.23), since this
      change touches `plugins/s/`.
- [x] 2.2 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` and confirm the whole suite passes,
      including the pre-existing card/button/region tests (unchanged geometry for
      buttoned cards).
- [x] 2.3 [req: *] Manually launch `python3
      plugins/s/skills/build/scripts/dashboard.py tui` and confirm the SHIPPED
      column now separates its cards by a single blank line.
