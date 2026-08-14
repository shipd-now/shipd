## ADDED Requirements

### Requirement: Board throughput chart
id: board-throughput-chart

The board TUI header SHALL display a live 15-column block chart of board
throughput — output tokens per bucket, summed across every member whose live
heartbeat state is `driving` and whose session transcript resolves (explicit
session id first, else the newest transcript for the member's location) —
refreshed on a 3-second interval. At the configured 3-row height the chart
SHALL carry a side label column showing the window peak, the window length
label (`45s`/`90s`/`3m`), and the newest bucket's value; at 1-row height it
SHALL render as a flat sparkline with the newest value. If no driving session
resolves, then the chart SHALL render blank without error. Clicking the chart
SHALL open the graph config dialog.

#### Scenario: Driving sessions render throughput
- **WHEN** the board has a driving member with a resolvable transcript
  carrying token events
- **THEN** the header chart shows non-blank eighth-block cells and its labels
  include the newest bucket value

#### Scenario: No driving sessions render blank
- **WHEN** no member is driving
- **THEN** the header chart renders blank cells and no error is raised

#### Scenario: Clicking the chart opens the config dialog
- **WHEN** the header chart is clicked
- **THEN** the graph config dialog screen is pushed

### Requirement: Graph config dialog
id: graph-config-dialog

The graph config dialog SHALL show a width-adaptive 3-row board-throughput
chart with peak, window, and newest-value detail, and three segmented setting
rows — window `45s`/`90s`/`3m` (bucket sizes 3/6/12 seconds), height
`3 rows`/`1 row` (the header chart's footprint), and scale `auto`/`fixed 12K`
— where `↑`/`↓` move between rows, `←`/`→` change the selected row's value,
`esc` closes, and options are also clickable. Setting changes SHALL apply
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

#### Scenario: Escape closes without persisting
- **WHEN** the dialog is dismissed and the app is relaunched
- **THEN** chart settings are back at their defaults (`45s`, 3 rows, auto)

### Requirement: Session activity timeline
id: session-activity-timeline

While the spec-detail modal is open for a member whose session transcript
resolves — the member's recorded session id when present, else the newest
transcript for the member's location while its live heartbeat state is
`driving` — the modal SHALL display, between its header and its artifact
tabs, a width-adaptive 3-row activity chart of that session's own output
tokens per bucket (main and subagent transcripts) with a detail line naming
peak, newest value, window, and session token total, refreshed on a 3-second
interval without the modal being reopened. If no transcript resolves, then
the modal SHALL render exactly as it does today, with no activity panel.

#### Scenario: A driving member shows a live chart
- **WHEN** the spec-detail modal opens for a member whose heartbeat entry
  carries a session id with a transcript on disk
- **THEN** the modal shows an activity panel of eighth-block cells with a
  detail line including the session token total

#### Scenario: The chart updates in place
- **WHEN** the modal is open and new assistant records are appended to the
  transcript
- **THEN** a subsequent refresh tick updates the rendered chart without the
  modal being closed and reopened

#### Scenario: No session, no panel
- **WHEN** the spec-detail modal opens for a member with no session id and no
  driving heartbeat entry
- **THEN** no activity panel is mounted and the modal's existing content is
  unchanged

#### Scenario: Artifact tabs are unaffected
- **WHEN** the modal shows an activity panel for a planned member
- **THEN** the Plan/Spec/Tasks tabs still render the change's artifacts as
  before
