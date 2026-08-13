# add-board
Status: draft

## Idea

Give the kanban app two read views over its `cards.json` store: a flat `list`
and a visual `board` across the three fixed lanes.

### Motivation

The kanban app has no way to see its cards yet, so the store stays illegible
before any command can change it.

### Details

This change gives the app two read views over the shared `cards.json` store: a
flat `list` that prints every card, and a visual `board` that arranges the
cards into the three fixed lanes (todo / doing / done). That is enough to make
the store legible before any command can change it.

### Non-goals

- No adding, editing, moving, or deleting cards — those are later cycles. This
  change is read-only over a pre-seeded store.

## Implementation

- A single stdlib-only `kanban.py` at the repo root, over a `cards.json` store
  beside it. A card is `{"id": <int>, "title": <str>, "lane": <str>}`; the lanes
  are the fixed `todo`, `doing`, `done`.
- `list` prints one line per card as `#<id> [<lane>] <title>`.
- `board` prints three columns headed TODO / DOING / DONE with each card's title
  under its lane.
- `cards.json` is seeded with three sample cards, one per lane, so both views
  render immediately.
