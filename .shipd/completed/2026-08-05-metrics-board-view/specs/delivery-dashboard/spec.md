## ADDED Requirements

### Requirement: Board metrics view
id: board-metrics-view

The `tui` board SHALL provide a delivery-metrics screen — a modal occupying
the majority of the viewport, dismissed by `Escape` or a clickable compact ✕
close control — opened by a footer-bound `m` key; while another modal is
already open, the `m` action SHALL do nothing. The screen SHALL present, in a
scrollable body: a **DORA tile row** — the deployment-frequency band with the
recent weekly deployment-day counts, the lead-time tier from
`lead_time_dora_band` over the lead-time median, the post-merge change-fail
rate labelled post-merge beside the pre-merge rework rate labelled as the
proxy, and the lead- and cycle-time medians with p85 in humanized durations —
rendering `n/a` for any absent statistic; a **throughput run chart** of the
per-ISO-week ship counts as eighth-block columns scaled from zero to the
peak weekly count, labelled with the total; a **cycle-time scatterplot**
plotting each shipped change (ship date × cycle seconds) as a dot with the
p50/p85/p95 percentile values overlaid as labelled horizontal lines and the
sample count — a mean SHALL appear nowhere on the screen; and a **cumulative
flow diagram** stacking each recorded flow record's per-state counts, mapped
onto the board lanes (`archived`→`shipped`, `ready`→`ready`,
`unplanned`→`unplanned`, else `building`), bottom-up in the order `shipped`,
`building`, `ready`, `unplanned`, colored through the lane theme variables
with a legend, or a no-flow-history notice when the series is empty. The
screen's data SHALL be assembled by a **dependency-free** helper
(`metrics_view_data(root)` — `metrics.derive` plus
`metrics.collect_ship_events`, no `textual`) run **off the UI thread** (a
thread worker behind a computing placeholder, an injectable data callable
and an apply seam for tests) and refreshed on a 30-second interval while the
screen is open; if the assembly fails, then the screen SHALL keep its last
rendered content (or an unavailable notice) and never raise. The tile,
run-chart, scatter, and CFD renderers SHALL be pure, dependency-free
functions (no `textual`, no I/O), unit-tested without the TUI; screen CSS
SHALL use only `$` theme variables; and no metric SHALL be attributed to an
individual.

#### Scenario: The m key opens the metrics screen
- **GIVEN** the mounted board
- **WHEN** `m` is pressed
- **THEN** the metrics screen is pushed onto the screen stack, and the app
  advertises a visible `m` binding

#### Scenario: The m key is inert while a modal is open
- **GIVEN** a modal screen already open above the board
- **WHEN** the `m` action fires
- **THEN** no metrics screen is pushed and the open modal is undisturbed

#### Scenario: The DORA tile row renders bands, tiers, and both fail rates
- **GIVEN** a metrics fixture with a deployment-frequency band, a resolvable
  lead-time median, a change-fail rate, and a rework rate
- **WHEN** the tile row renders
- **THEN** it shows the band, the lead-time tier, the change-fail rate
  labelled post-merge, the rework rate labelled as the pre-merge proxy, and
  humanized lead/cycle medians — and an absent statistic renders `n/a`

#### Scenario: The run chart scales to the weekly counts
- **GIVEN** per-week ship counts with a known peak
- **WHEN** the run-chart rows render
- **THEN** the peak week paints a full-height column, a zero week is blank,
  and the label carries the total

#### Scenario: The scatter plots points under labelled percentile lines
- **GIVEN** ship events with varying cycle seconds and a cycle-time stat
  block
- **WHEN** the scatter rows render
- **THEN** dot cells appear for the events, the p50/p85/p95 lines are
  overlaid with humanized duration labels and the sample count, no mean
  appears, and an event missing its timestamp or seconds is skipped

#### Scenario: The CFD stacks lane-colored bands from the flow series
- **GIVEN** a flow series whose records hold members across lifecycle states
- **WHEN** the CFD rows render
- **THEN** each record becomes one column stacking its lane-mapped counts
  bottom-up in the order shipped, building, ready, unplanned, using the lane
  theme variables in markup, with a legend line — and an empty series
  renders the no-flow-history notice instead

#### Scenario: The screen populates from the worker and refreshes in place
- **GIVEN** a metrics screen constructed with an injected data callable
- **WHEN** the screen mounts and the apply seam receives the assembled data
- **THEN** the computing placeholder gives way to the four sections without
  the screen being reopened, and a failing assembly leaves the screen
  rendered with no traceback

#### Scenario: Close control and Escape dismiss the screen
- **GIVEN** an open metrics screen
- **WHEN** the user clicks its ✕ control or presses `Escape`
- **THEN** the screen is dismissed and the board is shown again

#### Scenario: The data helper and renderers are dependency-free
- **GIVEN** an environment without `textual`
- **WHEN** `metrics_view_data` runs on a fixture root and the tile,
  run-chart, scatter, and CFD renderers run on fixture data
- **THEN** they succeed without importing `textual` and return their
  assembled dict and text rows

## MODIFIED Requirements

### Requirement: Board command palette
id: board-command-palette
base: e81d28692226

The `tui` board SHALL open textual's built-in command palette on `ctrl+p`,
and the board SHALL advertise the binding in its footer with the key display
`^p`. When the palette is opened from the board screen, it SHALL list exactly
the board's own commands in place of textual's stock system commands: a
grouping command that toggles the group-by-epic mode through the same path as
the `g` key, a clear-search command — offered only while a search query is
active — that clears the query and restores the full board through the same
path as the search input's `escape`, a delivery-metrics command that opens
the board metrics screen through the same path as the `m` key, and a quit
command; the stock theme-change, keys-help, and screenshot commands SHALL NOT
be listed. When the palette is opened from a modal screen, it SHALL offer
only the quit command. The palette SHALL take its styling from theme
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
