## ADDED Requirements

### Requirement: Board filter strip
id: board-filter-strip

The `tui` board SHALL mount a **filter strip** row between the header bar and
the lanes, carrying: a totals label, the active filter chips with a
`+ filter` control, a shipped-this-week label, and a synced-ago label. The
totals label SHALL report the **full** board aggregation — the member count,
the epic count, and the distinct-initiative count — and SHALL NOT shrink
while search or filters narrow the visible board. When `f` is pressed on the
board (or the `+ filter` control is activated), the app SHALL push a modal
**filter picker** listing the available filter options — the risk tiers
`high`/`medium`/`low`, each epic slug, and each initiative slug on the board,
excluding already-active chips — and SHALL dismiss it without effect on
`escape`; while a modal screen is already open, `f` SHALL be inert. When a
picker option is selected, the app SHALL add a removable chip for it to the
strip; when a chip is activated, the app SHALL remove it and restore the
members it excluded. While chips are active, each lane SHALL mount only the
members passing **every** active filter kind, where a member passes a kind
when it matches **at least one** of that kind's chip values (`risk` against
the member's risk rating, `epic` against its epic's slug, `initiative`
against its epic's initiative slug), composed with the live search query
(both must keep a member); a group none of whose members pass SHALL mount no
group header, and a lane left empty SHALL show its empty-state text. The
filter set SHALL be view-level state only — `build_board` aggregation and
the launch builders are unchanged, chips never persist — and SHALL fold into
the diff-aware lane signatures, so a chip change always repaints and an
unchanged refresh under steady chips repaints nothing. The strip SHALL also
show `▲ N shipped this week` — N derived from the delivery-metrics ship
events as the count shipped since the Monday (UTC) of the current ISO week,
via a **dependency-free** helper (no `textual`) defined ahead of the module's
`textual` import — and a synced-ago label derived from the time of the last
interval refresh, both re-evaluated on every refresh.

#### Scenario: The strip mounts with totals and stats
- **WHEN** the app is mounted
- **THEN** the filter strip sits between the header bar and the lanes,
  showing the full-board totals, the `+ filter` control, the
  shipped-this-week label, and the synced-ago label

#### Scenario: f opens the filter picker
- **WHEN** `f` is pressed on the mounted board
- **THEN** the filter picker modal is pushed, listing risk tiers, epic slugs,
  and initiative slugs as selectable options

#### Scenario: Already-active options are not offered
- **GIVEN** an active `risk:high` chip
- **WHEN** the filter picker opens
- **THEN** the `risk high` option is absent while the other options remain

#### Scenario: Escape cancels the picker
- **GIVEN** the open filter picker
- **WHEN** `escape` is pressed
- **THEN** the picker is dismissed and no chip is added

#### Scenario: Selecting an option adds a filtering chip
- **GIVEN** a board with members of differing risk ratings
- **WHEN** the `risk high` option is selected in the picker
- **THEN** a removable `risk:high` chip appears in the strip and the lanes
  mount only high-risk members

#### Scenario: Same-kind chips widen the filter
- **GIVEN** active `risk:high` and `risk:medium` chips
- **WHEN** the lanes render
- **THEN** members matching either rating are mounted

#### Scenario: Cross-kind chips narrow the filter
- **GIVEN** an active `risk:high` chip and an active `epic` chip
- **WHEN** the lanes render
- **THEN** only high-risk members of that epic are mounted

#### Scenario: Chips compose with the live search
- **GIVEN** an active chip and an active search query
- **WHEN** the lanes render
- **THEN** only members kept by both the chip and the query are mounted

#### Scenario: Removing a chip restores its members
- **GIVEN** an active chip excluding some members
- **WHEN** the chip is activated
- **THEN** the chip leaves the strip and the excluded members remount

#### Scenario: A fully filtered group mounts no header
- **GIVEN** a grouping mode is active and chips exclude every member of one
  group
- **WHEN** the lanes render
- **THEN** no group header for that group is mounted in any lane

#### Scenario: An unchanged refresh under steady chips repaints nothing
- **GIVEN** active chips and a board whose aggregation is unchanged
- **WHEN** the interval refresh runs
- **THEN** the lanes retain their existing card widget instances and the
  chips stay applied

#### Scenario: Totals stay full-board while narrowed
- **GIVEN** chips or a query narrowing the visible board
- **WHEN** the strip renders
- **THEN** the totals label still reports the full board's member, epic, and
  initiative counts

#### Scenario: Shipped-this-week counts the current ISO week
- **GIVEN** ship events inside and before the current ISO week (Monday, UTC)
- **WHEN** the dependency-free counter runs with an injected now
- **THEN** it counts only the events on/after that Monday, without `textual`

#### Scenario: The synced label reflects the last refresh
- **WHEN** an interval refresh completes
- **THEN** the synced-ago label reports the age of that refresh

## MODIFIED Requirements

### Requirement: Board command palette
id: board-command-palette
base: ea1267a48e79

The `tui` board SHALL open textual's built-in command palette on `ctrl+p`,
and the board SHALL advertise the binding in its footer with the key display
`^p`. When the palette is opened from the board screen, it SHALL list exactly
the board's own commands in place of textual's stock system commands: a
grouping command that cycles the grouping mode (`epic` → `initiative` →
`none`) through the same path as the `g` key, a clear-search command —
offered only while a search query is active — that clears the query and
restores the full board through the same path as the search input's
`escape`, a clear-filters command — offered only while filter chips are
active — that removes every chip and restores the full board through the
same path as removing each chip, a delivery-metrics command that opens the
board metrics screen through the same path as the `m` key, and a quit
command; the stock theme-change, keys-help, and screenshot commands SHALL
NOT be listed. When the palette is opened from a modal screen, it SHALL
offer only the quit command. The palette SHALL take its styling from theme
variables only — the change introduces no hard-coded colors — and running a
palette command SHALL leave `build_board` aggregation and the pure launch
builders unchanged.

#### Scenario: ctrl+p opens the palette
- **WHEN** `ctrl+p` is pressed on the mounted board
- **THEN** textual's command-palette screen is pushed onto the screen stack

#### Scenario: Board commands replace the stock set
- **GIVEN** the mounted board with no active search query
- **WHEN** the palette's command source is read for the board screen
- **THEN** it lists the grouping command, the delivery-metrics command, and
  the quit command, and none of the stock theme-change, keys-help, or
  screenshot commands

#### Scenario: The delivery-metrics command opens the metrics screen
- **GIVEN** the mounted board
- **WHEN** the delivery-metrics command's callback runs
- **THEN** the board metrics screen is pushed onto the screen stack, exactly
  as if `m` had been pressed

#### Scenario: Clear-search is offered only while a query is active
- **GIVEN** an active search query filtering the board
- **WHEN** the palette's command source is read for the board screen
- **THEN** the clear-search command is listed — and it is absent once the
  query is cleared

#### Scenario: Clear-filters is offered only while chips are active
- **GIVEN** an active filter chip narrowing the board
- **WHEN** the palette's command source is read for the board screen
- **THEN** the clear-filters command is listed — and it is absent once the
  chips are cleared

#### Scenario: The clear-filters command restores the board
- **GIVEN** active filter chips narrowing the board to a subset of members
- **WHEN** the clear-filters command's callback runs
- **THEN** every chip is removed and every member's card is mounted again

#### Scenario: The grouping command cycles grouping
- **GIVEN** the mounted board in `epic` mode
- **WHEN** the grouping command's callback runs
- **THEN** the grouping mode advances to `initiative` and the lanes
  repaint, exactly as if `g` had been pressed

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
