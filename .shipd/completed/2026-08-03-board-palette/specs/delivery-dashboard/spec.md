## ADDED Requirements

### Requirement: Board command palette
id: board-command-palette

The `tui` board SHALL open textual's built-in command palette on `ctrl+p`,
and the board SHALL advertise the binding in its footer with the key display
`^p`. When the palette is opened from the board screen, it SHALL list exactly
the board's own commands in place of textual's stock system commands: a
grouping command that toggles the group-by-epic mode through the same path as
the `g` key, a clear-search command — offered only while a search query is
active — that clears the query and restores the full board through the same
path as the search input's `escape`, and a quit command; the stock
theme-change, keys-help, and screenshot commands SHALL NOT be listed. When
the palette is opened from a modal screen, it SHALL offer only the quit
command. The palette SHALL take its styling from theme variables only — the
change introduces no hard-coded colors — and running a palette command SHALL
leave `build_board` aggregation and the pure launch builders unchanged.

#### Scenario: ctrl+p opens the palette
- **WHEN** `ctrl+p` is pressed on the mounted board
- **THEN** textual's command-palette screen is pushed onto the screen stack

#### Scenario: Board commands replace the stock set
- **GIVEN** the mounted board with no active search query
- **WHEN** the palette's command source is read for the board screen
- **THEN** it lists the grouping command and the quit command, and none of
  the stock theme-change, keys-help, or screenshot commands

#### Scenario: Clear-search is offered only while a query is active
- **GIVEN** an active search query filtering the board
- **WHEN** the palette's command source is read for the board screen
- **THEN** the clear-search command is listed — and it is absent once the
  query is cleared

#### Scenario: The grouping command toggles grouping
- **GIVEN** the mounted board with grouping on
- **WHEN** the grouping command's callback runs
- **THEN** the group-by-epic mode flips and the lanes repaint flat, exactly
  as if `g` had been pressed

#### Scenario: The clear-search command restores the board
- **GIVEN** an active query filtering the board to a subset of members
- **WHEN** the clear-search command's callback runs
- **THEN** the query is cleared and every member's card is mounted again

#### Scenario: A modal screen offers only quit
- **GIVEN** a modal screen open above the board
- **WHEN** the palette's command source is read for that modal screen
- **THEN** only the quit command is listed

#### Scenario: The footer advertises the palette key
- **WHEN** the app is mounted
- **THEN** the app carries a visible `ctrl+p` binding for the command palette
  with the key display `^p`
