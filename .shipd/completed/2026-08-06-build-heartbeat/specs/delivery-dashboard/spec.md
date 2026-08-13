## ADDED Requirements

### Requirement: Interactive build heartbeat
id: build-heartbeat-cli

While an interactive build runs, the build skill SHALL maintain
`<content-dir>/autopilot/<slug>-build-heartbeat.json` through `heartbeat.py`
CLI verbs — `build-start <slug>`, `build-stage <slug> --stage <name>`, and
`build-finish <slug> [--outcome <outcome>]` — each a stateless
read-modify-write: load the existing file when present, apply the transition,
increment a monotonic `seq`, stamp an epoch `updated_at`, and atomically
replace it (temp file + rename). The file SHALL carry the change slug,
`kind: build`, the state (`running`/`finished`), the recorded `location`
(defaulting to the invoking working directory) and `session_id` (defaulting to
`$CLAUDE_CODE_SESSION_ID`, omitted when neither the flag nor the variable
supplies one), the current stage when set, and the outcome on finish. If a
write fails, then the verb SHALL warn on stderr and exit zero — a heartbeat
failure never blocks a build. Because a build runs in its change's worktree,
the board aggregation SHALL discover build heartbeats under both the
invocation root's content directory and every `.worktrees/<name>/` content
directory's `autopilot/`, the newest `updated_at` winning a slug contested
between roots.

#### Scenario: build-start records a running heartbeat
- **WHEN** `build-start <slug>` runs with `CLAUDE_CODE_SESSION_ID` set
- **THEN** the heartbeat file parses as JSON with state `running`,
  `kind: build`, that session id, and the invoking directory as `location`

#### Scenario: Stage transitions bump the sequence
- **WHEN** `build-stage <slug> --stage implement` runs after `build-start`
- **THEN** the file records stage `implement` with a `seq` greater than the
  start write's

#### Scenario: Finish marks the build finished
- **WHEN** `build-finish <slug> --outcome shipped` runs
- **THEN** the file records state `finished` and outcome `shipped`

#### Scenario: A missing session id degrades gracefully
- **WHEN** `build-start` runs with no `--session-id` and no
  `CLAUDE_CODE_SESSION_ID` in the environment
- **THEN** the heartbeat is written without a `session_id` field

#### Scenario: A worktree-hosted heartbeat reaches the board
- **GIVEN** a running build heartbeat written under
  `.worktrees/<name>/<content-dir>/autopilot/` and none in the invocation
  root's own content directory
- **WHEN** the board aggregates from the main checkout
- **THEN** the heartbeat attaches to its slug-matching member

#### Scenario: A failing write never blocks
- **GIVEN** a heartbeat destination that cannot be written
- **WHEN** any build heartbeat verb runs
- **THEN** it exits zero with a warning on stderr

## MODIFIED Requirements

### Requirement: Board TUI
id: board-tui
base: 73ab7bac9754

The dashboard CLI SHALL provide a `tui` verb rendering the board full-screen as a
`textual` application (the pinned `textual` dependency). When `textual` is not
importable, `dashboard.py`'s script entry SHALL, before importing `textual`,
auto-provision it: create-or-reuse a dedicated virtualenv under
`${XDG_CACHE_HOME:-~/.cache}/shipd/tui-venv`, install the pinned dependency
into it from `requirements.txt` (printing a one-time setup message on stderr),
and re-exec the same command with that venv's interpreter — so the board runs
with no manual install and without modifying the system Python. Provisioning
SHALL be attempted for any `dashboard.py` verb invocation that finds `textual`
missing (so `board` and `html` also work), SHALL be skipped entirely when
`textual` is already importable, and — if venv creation or the install fails —
SHALL fall back to a clear `pip install` hint and a non-zero exit. The app SHALL present a single **header bar** in place of textual's stock `Header` and the previous controls strip — carrying, left to right, a **brand block** (an accent-styled `shipd` beside a muted `delivery board` label), the **centered search input** with its clear control and match-count label (see the Board search requirement), the **grouping segmented control** (see the Board epic grouping requirement) with the **activity indicator** beside it, and the live throughput chart (see the Board throughput chart requirement) — a `Footer` showing the key bindings, and below the header bar a horizontal board of **five bordered lifecycle lanes** (`unplanned`, `ready`, `building`, `review`, `shipped`), each a
vertically-scrolling column. Each lane SHALL carry a **one-row tinted header
band** pinned at its top and excluded from the lane's scrolling — the lane's
name label coloured with that lane's theme variable over a tinted band of the
same colour — replacing the former border title. Every member SHALL render as
a **focusable one-row task-card widget**: a risk glyph `●` coloured through
the theme's risk variables (high=orange, medium=chartreuse, low=dim; an
unknown or missing risk renders the glyph in the muted foreground tier), the
member's slug, and — while the member is being driven — its live stage
appended in the muted tier; a member in the `shipped` lane SHALL render a
subtle-tier `✓` in place of the risk glyph. Each row SHALL occupy exactly one
terminal row, with no inter-row blank margin and a visible highlight when
focused. While a lane mounts no member rows — its board content is empty, or
the active search filters every member out — the lane SHALL show its own
per-lane empty-state text in the subtle tier. The app SHALL move focus
between cards and lanes with the arrow keys, cycle the grouping mode and quit via footer-bound keys, open a **modal spec-detail screen** for the focused member
either on `Enter` or on a **mouse click on the card** (a click first focuses the
clicked card, then opens the same modal), and re-read the board on the `--interval` (default 2) so live runs update. The **activity indicator** SHALL derive from pure, dependency-free predicates over the aggregated board (no `textual`, no I/O) computing two counts: the **live-run count** — epics whose heartbeat records run state `running` with an `updated_at` within 3600 seconds of now, the statusline's liveness window, so a long silent stage keeps the light while a crashed run loses it — and the **live-build count** — members whose interactive build heartbeat records state `running` with a liveness stamp (the newer of its `updated_at` and the aggregation-stamped transcript mtime) within 600 seconds of now, the short window ageing out a heartbeat orphaned by a killed session. While the live-run count is positive the indicator SHALL render a theme-success-colored `●` with the label `autopilot on`, the count appended as `autopilot (N)` when more than one run is live; otherwise, while the live-build count is positive, it SHALL render a `●` in the building lane's theme colour with the label `building`, the count appended as `building (N)` when more than one build is live; otherwise a subtle-tier idle marker — re-evaluated on every interval refresh. The **spec-detail screen** SHALL occupy the majority of the viewport and
SHALL carry a **close control the user can click** to dismiss it (in addition to
`Escape`). Above a horizontal separator it SHALL show the change's slug with its
risk and board state and a **reference to its epic** (the epic's slug and
status); below the separator it SHALL present the change's on-disk spec artifacts
in a **tabbed view** — one tab per file found for the change (its `plan.md`, each
`specs/<capability>/spec.md`, and `tasks.md`), each rendered as Markdown —
resolving the change's artifact directory under the content dir's
`planned/<slug>/` or `completed/<date>-<slug>/`. A change with no artifacts on
disk SHALL instead show a short not-yet-planned notice in place of the tabs.
Resolving and reading those artifact files SHALL be a **dependency-free**
operation (no `textual`), so it is unit-tested without the TUI. The interval
refresh SHALL be **diff-aware**: it re-aggregates and then
repaints only the lanes whose board-derived content
changed since the previous render — leaving unchanged lanes
untouched, so an idle board never repaints (no flashing) and a collapsed epic
group the user has collapsed stays collapsed across refreshes. The board's
**data layer** — `build_board`, `member_actions`, the aggregation, and the
launch-argv builders — SHALL keep its existing contracts; only the rendering
changes. Importing the delivery engine (`autopilot`) SHALL NOT require
`textual`: the run-heartbeat writer it depends on lives in a stdlib module, so
the engine and its test suites stay dependency-free.

#### Scenario: An unchanged board repaints no lane
- **GIVEN** a mounted app whose aggregated board is identical to the previous
  render
- **WHEN** the refresh runs (driven by the test harness)
- **THEN** no lane's children are torn down and remounted — the existing
  task-card widget instances are retained

#### Scenario: A collapsed epic group survives refresh
- **GIVEN** an epic group the user has collapsed in a lane
- **WHEN** an unchanged-board refresh runs
- **THEN** that group remains collapsed (its lane was not rebuilt)

#### Scenario: Only changed lanes repaint
- **GIVEN** a board in which one member's lane assignment changes between renders
- **WHEN** the refresh runs
- **THEN** only the lanes affected by that member are rebuilt, and the other
  lanes' existing card widgets are retained

#### Scenario: Missing textual provisions a venv and re-execs
- **GIVEN** `textual` is not importable
- **WHEN** the `dashboard.py` script entry runs
- **THEN** it creates the venv under `${XDG_CACHE_HOME:-~/.cache}/shipd/
  tui-venv`, installs the pinned dependency from `requirements.txt`, and
  re-execs the command with that venv's interpreter

#### Scenario: An existing venv is reused without reinstalling
- **GIVEN** `textual` is not importable but the cached venv already has it
- **WHEN** the script entry runs
- **THEN** it re-execs with the venv interpreter and runs no install step

#### Scenario: Already-importable textual skips provisioning
- **GIVEN** `textual` imports successfully
- **WHEN** the script entry runs
- **THEN** no venv is created or probed and the app runs directly

#### Scenario: Provisioning failure falls back to the hint
- **GIVEN** `textual` is not importable and venv creation or the install fails
- **WHEN** the script entry runs
- **THEN** it prints a clear `pip install` hint and exits non-zero

#### Scenario: App mounts the header bar, lanes and footer
- **WHEN** the textual app is mounted (via the test harness) on a board with
  members
- **THEN** its widget tree contains the header bar — brand block, search
  input, grouping segmented control, and activity indicator — a footer, and
  the five named lifecycle lanes, with no stock textual `Header` and no
  hierarchy panel

#### Scenario: Members are focusable cards in their lifecycle lane
- **GIVEN** a board with a member whose board state maps to the `building` lane
- **WHEN** the app is mounted
- **THEN** that member renders as a focusable one-row task-card inside the
  `building` lane, its text carrying the risk-coloured glyph and its slug

#### Scenario: A shipped member renders the dim check glyph
- **GIVEN** a board with a member whose board state maps to the `shipped` lane
- **WHEN** the app is mounted
- **THEN** that member's row renders the subtle-tier `✓` glyph in place of the
  risk glyph

#### Scenario: A driven member's row carries its live stage
- **GIVEN** a member whose heartbeat entry is `driving` at stage `build`
- **WHEN** its row renders
- **THEN** the row text appends the stage in the muted tier after the slug

#### Scenario: Each lane carries its tinted header band
- **WHEN** the app is mounted
- **THEN** each of the five lanes carries a one-row header labelled with its
  lane name, band and label coloured through that lane's theme variable, and
  the band is retained across a lane repaint

#### Scenario: An empty lane shows its empty-state text
- **GIVEN** a board on which one lane holds no members
- **WHEN** the app is mounted
- **THEN** that lane shows its own per-lane empty-state text, and the text is
  replaced by member rows once a member maps to that lane

#### Scenario: Focused card is highlighted
- **WHEN** focus moves to a task-card
- **THEN** that card reflects the focused state (its focus style/flag is set)
  while unfocused cards do not

#### Scenario: Enter opens the member detail modal
- **GIVEN** a focused task-card
- **WHEN** `Enter` is pressed
- **THEN** a modal spec-detail screen for that member is pushed onto the screen
  stack

#### Scenario: Clicking a card opens its detail modal
- **GIVEN** a mounted app with a task-card that is not currently focused
- **WHEN** that task-card is clicked
- **THEN** the same modal spec-detail screen for that member is pushed onto the
  screen stack, and the clicked card holds focus

#### Scenario: Spec-detail modal references the change's epic
- **GIVEN** a focused task-card for a member whose epic is known
- **WHEN** the spec-detail modal opens
- **THEN** its header shows the change's slug (with risk and state) and a
  reference to the epic — the epic slug and its status

#### Scenario: Spec-detail modal tabs the change's spec files
- **GIVEN** a change whose artifact directory on disk holds `plan.md`, a
  `specs/<capability>/spec.md`, and `tasks.md`
- **WHEN** the spec-detail modal opens for that change
- **THEN** it presents a tabbed view with one tab per discovered file (a Plan
  tab, a Spec tab, and a Tasks tab), each rendering that file's Markdown content

#### Scenario: An unplanned change shows a not-yet-planned notice
- **GIVEN** a change with no artifact directory on disk (never planned)
- **WHEN** the spec-detail modal opens for it
- **THEN** it shows a short not-yet-planned notice instead of the tabbed view

#### Scenario: The spec-detail modal is dismissed by its close control
- **GIVEN** an open spec-detail modal
- **WHEN** the user clicks its close control
- **THEN** the modal is dismissed and the board screen is shown again

#### Scenario: Locating a change's artifacts is dependency-free
- **GIVEN** an environment without `textual`
- **WHEN** the artifact-resolving helper is called for a change that has a
  `planned/<slug>/` (or `completed/<date>-<slug>/`) directory
- **THEN** it returns that change's spec files (label, path, and text) in tab
  order without importing `textual`

#### Scenario: Live refresh re-reads the board
- **GIVEN** a mounted app whose underlying heartbeat/report changes
- **WHEN** the refresh interval elapses (driven by the test harness)
- **THEN** the app re-aggregates via `build_board` and the lanes reflect the new
  member states

#### Scenario: The engine imports without textual
- **WHEN** the `autopilot` module is imported in an environment without `textual`
- **THEN** the import succeeds — the run-heartbeat writer it uses is in a stdlib
  module, not `dashboard`

#### Scenario: A fresh running heartbeat lights the autopilot marker
- **GIVEN** a board in which one epic's heartbeat records run state `running`
  with an `updated_at` a few seconds old
- **WHEN** the header bar renders after a refresh
- **THEN** the activity indicator shows the success-colored `●` and the label
  `autopilot on`

#### Scenario: Multiple live runs show the count
- **GIVEN** a board in which two epics' heartbeats record run state `running`
  with fresh `updated_at` stamps
- **WHEN** the header bar renders after a refresh
- **THEN** the activity indicator label reads `autopilot (2)`

#### Scenario: A live interactive build lights the building marker
- **GIVEN** a board with no live autopilot run and one member whose build
  heartbeat records state `running` with a liveness stamp a few seconds old
- **WHEN** the header bar renders after a refresh
- **THEN** the activity indicator shows the `●` in the building lane's colour
  and the label `building`

#### Scenario: A stale build heartbeat goes idle
- **GIVEN** a board whose only build heartbeat is `running` but whose liveness
  stamp (heartbeat `updated_at` and transcript mtime alike) is older than 600
  seconds
- **WHEN** the count predicates evaluate the board
- **THEN** both counts are zero without importing `textual`, and the indicator
  renders the idle marker


### Requirement: Board throughput chart
id: board-throughput-chart
base: 6955ab727313

The board TUI header SHALL display a live 15-column block chart of board
throughput — output tokens per bucket, summed across every driving autopilot
member and every member with a live interactive build heartbeat (state
`running`, fresh per the Board TUI requirement's 600-second liveness window)
whose session transcript resolves (explicit session id first, else the newest
transcript for the member's or heartbeat's location, a worktree location
falling back to the main checkout's transcript directory), deduplicated so a
session is tailed once — refreshed on a 3-second interval. At the configured
3-row height the chart SHALL carry a side label column showing the window
peak, the window length label (`45s`/`90s`/`3m`), and the newest bucket's
value; at 1-row height it SHALL render as a flat sparkline with the newest
value. If no live session resolves, then the chart SHALL render blank without
error. Clicking the chart SHALL open the graph config dialog.

#### Scenario: Driving sessions render throughput
- **WHEN** the board has a driving member with a resolvable transcript
  carrying token events
- **THEN** the header chart shows non-blank eighth-block cells and its labels
  include the newest bucket value

#### Scenario: An interactive build renders throughput
- **WHEN** the board has a member with a live build heartbeat whose recorded
  session transcript carries token events
- **THEN** the header chart shows non-blank eighth-block cells

#### Scenario: No live sessions render blank
- **WHEN** no member is driving and no build heartbeat is live
- **THEN** the header chart renders blank cells and no error is raised

#### Scenario: Clicking the chart opens the config dialog
- **WHEN** the header chart is clicked
- **THEN** the graph config dialog screen is pushed
