## MODIFIED Requirements

### Requirement: Board metrics view
id: board-metrics-view
base: adc2bb6e425a

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


### Requirement: Board scrollbar theme
id: board-scrollbar-theme
base: bdbd762a4163

The registered `shipd` theme SHALL pin the scrollbar palette to the design
system's muted border tones by exposing scrollbar theme variables that
override textual's accent-derived defaults: the thumb (`scrollbar`)
`#3E3E52`, the hover and active thumb states `#55556A`, and the track,
track-hover, track-active, and corner (`scrollbar-background`,
`scrollbar-background-hover`, `scrollbar-background-active`,
`scrollbar-corner-color`) `#1C1C26`. While the `shipd` theme is active, no
scrollbar color SHALL derive from the theme's primary/accent color.

#### Scenario: Scrollbar variables resolve the muted tones
- **WHEN** the `shipd` theme's CSS variables are resolved on the running app
- **THEN** `scrollbar` resolves `#3E3E52`, `scrollbar-hover` and
  `scrollbar-active` resolve `#55556A`, and `scrollbar-background`,
  `scrollbar-background-hover`, `scrollbar-background-active`, and
  `scrollbar-corner-color` resolve `#1C1C26`
