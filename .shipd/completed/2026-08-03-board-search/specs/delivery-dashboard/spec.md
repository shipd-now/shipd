## ADDED Requirements

### Requirement: Board search
id: board-search

The `tui` board SHALL provide live member search from a search input in the
controls strip (beside the group-by-epic toggle), accompanied by a clear (✕)
control and a match-count label. When `/` is pressed on the board, the app
SHALL focus the search input. While a non-empty query is active, each lane
SHALL mount only the members matched by a case-insensitive substring test over
the member's slug, its epic's slug, and its epic's initiative slug; a matched
card SHALL highlight the matched span of its slug in the accent style (a card
matched only via its epic or initiative renders unhighlighted); the
match-count label SHALL show the number of matching members (and SHALL be
blank with no active query); and, with grouping on, an epic none of whose
members match SHALL mount no group header in any lane. When `escape` is
pressed in the search input or the ✕ control is activated, the app SHALL
clear the query and restore the full board. The query SHALL be view-level
state only — `build_board` aggregation and the pure launch builders are
unchanged — and SHALL fold into the diff-aware lane signatures, so an
unchanged board under an unchanged query repaints no lane, a query edit
always repaints, and the active filter survives interval refreshes.

#### Scenario: Slash focuses the search input
- **WHEN** `/` is pressed on the mounted board
- **THEN** the controls-strip search input holds focus

#### Scenario: Typing filters the lanes to matching members
- **GIVEN** a board whose members include one slug containing the query and
  one slug (in a different epic) not matching it anywhere
- **WHEN** the query is typed into the search input
- **THEN** the matching member's card is mounted and the non-matching
  member's card is not

#### Scenario: An epic or initiative match keeps its members visible
- **GIVEN** a member whose slug does not contain the query but whose epic's
  slug (or initiative slug) does
- **WHEN** that query is active
- **THEN** the member's card remains mounted

#### Scenario: The matched slug span is highlighted in accent
- **GIVEN** an active query that matches a member's slug
- **WHEN** that member's card renders
- **THEN** the matched span of the slug carries the accent highlight styling

#### Scenario: The match count reports matching members
- **GIVEN** an active query matching exactly N members across the lanes
- **WHEN** the lanes render
- **THEN** the match-count label shows N matches, and clearing the query
  blanks the label

#### Scenario: Escape in the input clears the search
- **GIVEN** an active query filtering the board
- **WHEN** `escape` is pressed in the search input
- **THEN** the query is cleared and every member's card is mounted again

#### Scenario: The clear control clears the search
- **GIVEN** an active query filtering the board
- **WHEN** the ✕ control is activated
- **THEN** the query is cleared and every member's card is mounted again

#### Scenario: A fully filtered epic mounts no group header
- **GIVEN** grouping is on and an active query matching none of one epic's
  members
- **WHEN** the lanes render
- **THEN** no group header for that epic is mounted in any lane

#### Scenario: An unchanged refresh under an active query repaints nothing
- **GIVEN** an active query and a board whose aggregation is unchanged
- **WHEN** the interval refresh runs
- **THEN** the lanes retain their existing card widget instances and the
  filter stays applied

#### Scenario: A query edit repaints
- **GIVEN** a lane's rendered cards under one query
- **WHEN** the query changes
- **THEN** the lane's signature differs from its last-rendered one, so the
  lane repaints with the new filter and highlights
