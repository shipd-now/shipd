#!/usr/bin/env python3
"""A tiny CLI kanban app over a JSON store.

`list` prints every card; `board` renders the cards into three fixed lanes.
Cards live in `cards.json` beside this script, each one
`{"id": <int>, "title": <str>, "lane": <str>}` with a lane of
`todo`, `doing`, or `done`.
"""

import json
import os
import sys

LANES = ("todo", "doing", "done")
STORE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cards.json")


def load_cards():
    """Read the card list from `cards.json` beside this script."""
    with open(STORE, encoding="utf-8") as fh:
        return json.load(fh)


def cmd_list(cards):
    """Print one line per card: `#<id> [<lane>] <title>`."""
    for card in cards:
        print("#%s [%s] %s" % (card["id"], card["lane"], card["title"]))


def cmd_board(cards):
    """Render the cards as three columns headed TODO / DOING / DONE."""
    columns = {lane: [c["title"] for c in cards if c["lane"] == lane]
               for lane in LANES}
    width = 20
    headers = [lane.upper().center(width) for lane in LANES]
    print(" | ".join(headers))
    print("-+-".join("-" * width for _ in LANES))
    depth = max((len(col) for col in columns.values()), default=0)
    for row in range(depth):
        cells = []
        for lane in LANES:
            titles = columns[lane]
            cells.append((titles[row] if row < len(titles) else "")[:width]
                         .ljust(width))
        print(" | ".join(cells))


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] not in ("list", "board"):
        print("usage: kanban.py {list|board}", file=sys.stderr)
        return 2
    cards = load_cards()
    if argv[0] == "list":
        cmd_list(cards)
    else:
        cmd_board(cards)
    return 0


if __name__ == "__main__":
    sys.exit(main())
