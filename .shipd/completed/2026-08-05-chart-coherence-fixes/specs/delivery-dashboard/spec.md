## MODIFIED Requirements

### Requirement: Graph config dialog
id: graph-config-dialog
base: 0f85740fa935

The graph config dialog SHALL show a width-adaptive 3-row board-throughput
chart with peak, window, and newest-value detail, and three segmented setting
rows — window `45s`/`90s`/`3m` (bucket sizes 3/6/12 seconds), height
`3 rows`/`1 row` (the header chart's footprint), and scale `auto`/`fixed 12K`
— with every option of every row visible and clickable. `↑`/`↓` SHALL move
between rows, `←`/`→` SHALL change the selected row's value, and the dialog
SHALL be dismissable by both a `✕` close control and a priority `escape`
binding. The app SHALL show at most one config dialog: opening it while one
is already on screen pushes no second instance. Setting changes SHALL apply
immediately to every chart as in-app state, not persisted across runs.

#### Scenario: Arrow keys change a setting
- **WHEN** the dialog is open and the user moves to the window row and
  presses an arrow to select `90s`
- **THEN** the app's chart state records 6-second buckets and subsequent
  chart renders use them

#### Scenario: Height governs the header form
- **WHEN** the height setting is switched to `1 row`
- **THEN** the header chart renders as a one-row sparkline while the dialog's
  own chart stays 3 rows

#### Scenario: Every option is visible and clickable
- **WHEN** the dialog is open
- **THEN** each setting row shows all of its options with a visible region,
  and clicking a non-selected option (e.g. `3m`) applies it to the chart
  state

#### Scenario: The close control dismisses
- **WHEN** the `✕` close control is clicked
- **THEN** the dialog is dismissed

#### Scenario: Repeated opens never stack
- **WHEN** the header chart is clicked twice in quick succession
- **THEN** exactly one config dialog is on screen, and a single Escape
  returns to the board

#### Scenario: Escape closes without persisting
- **WHEN** the dialog is dismissed and the app is relaunched
- **THEN** chart settings are back at their defaults (`45s`, 3 rows, auto)
