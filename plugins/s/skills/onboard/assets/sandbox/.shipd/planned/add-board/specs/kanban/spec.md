## ADDED Requirements

### Requirement: List cards
id: list-cards

The CLI SHALL provide a `list` command that prints every card in the store,
each shown with its id, lane, and title.

#### Scenario: List prints one line per card
- **WHEN** `kanban.py list` runs against a store of three cards
- **THEN** it prints three lines, each carrying a card's id, lane, and title

### Requirement: Board view
id: board-view

The CLI SHALL provide a `board` command that renders the cards as a
three-column board with the fixed todo, doing, and done lanes, each card's
title placed under its lane's column.

#### Scenario: Board renders three lanes
- **WHEN** `kanban.py board` runs against a store spread across the lanes
- **THEN** it prints three columns headed TODO, DOING, and DONE with each
  card's title under its lane
