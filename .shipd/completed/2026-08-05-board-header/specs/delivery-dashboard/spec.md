## MODIFIED Requirements

### Requirement: Board TUI
id: board-tui
base: 1237370c3271

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
SHALL fall back to a clear `pip install` hint and a non-zero exit. The app SHALL present a single **header bar** in place of textual's stock `Header` and the previous controls strip — carrying, left to right, a **brand block** (an accent-styled `shipd` beside a muted `delivery board` label), the **centered search input** with its clear control and match-count label (see the Board search requirement), the **grouping segmented control** (see the Board epic grouping requirement) with the **autopilot indicator** beside it, and the live throughput chart (see the Board throughput chart requirement) — a `Footer` showing the key bindings, and below the header bar a horizontal board of **five bordered lifecycle lanes** (`unplanned`, `ready`, `building`, `review`, `shipped`), each a
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
clicked card, then opens the same modal), and re-read the board on the `--interval` (default 2) so live runs update. The **autopilot indicator** SHALL derive from a pure, dependency-free predicate over the aggregated board (no `textual`, no I/O) that is live exactly when some epic's heartbeat records run state `running` with an `updated_at` within 3600 seconds of now — the statusline's liveness window, so a long silent stage keeps the light while a crashed run loses it; while live the indicator SHALL render a theme-success-colored `●` with the label `autopilot on`, otherwise a subtle-tier idle marker, re-evaluated on every interval refresh. The **spec-detail screen** SHALL occupy the majority of the viewport and
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
  input, grouping segmented control, and autopilot indicator — a footer, and
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

#### Scenario: A fresh running heartbeat lights the autopilot indicator
- **GIVEN** a board in which one epic's heartbeat records run state `running`
  with an `updated_at` a few seconds old
- **WHEN** the header bar renders after a refresh
- **THEN** the autopilot indicator shows the success-colored `●` and the label
  `autopilot on`

#### Scenario: A stale or absent run leaves the indicator idle
- **GIVEN** a board whose heartbeats are `finished`, absent, or `running` with
  an `updated_at` older than 3600 seconds
- **WHEN** the liveness predicate evaluates the board
- **THEN** it returns false without importing `textual`, and the indicator
  renders the idle marker

### Requirement: Board epic grouping
id: board-epic-grouping
base: 3b4326328250

The `tui` board SHALL provide a three-state **grouping mode** — `epic`, `initiative`, `none` — selected from a **segmented control in the header bar** (one compact one-row button per mode, the active mode visibly highlighted) and cycled in that order by the footer-bound `g` key, and SHALL start in **`epic`** mode by default. While the mode is `epic`, every lifecycle lane SHALL render its cards grouped under a **collapsible per-epic
header** (one group per epic, in board order, each group individually
collapsible), replacing the previous shipped-lane-only grouping — so an epic's
cards in a lane sit together under that epic's header. Each epic group header
SHALL show the epic's slug and status and, when the epic belongs to an
initiative, that **initiative** (its slug), and the **count of that epic's
cards in that lane**; this re-homes the initiative → epic
structure that the removed hierarchy panel used to carry. The group's visual
SHALL be a flat **theme surface band** (the registered theme's panel
background) with **theme-variable border separator lines** dividing adjacent
groups — no per-epic-status colour coding and no hard-coded colors (see the
Board theme requirement). The group header SHALL be a **single terminal row**
— no top-border row above the title and no trailing padding row below the
group's contents, so the title row (collapse arrow, title text, and the
inline controls) is the group's first row. Each **runnable** epic group
header SHALL carry a **clickable run control**; an epic is **runnable** when its
status is `ready` or `active` **and** it has at least one `unplanned` or `ready`
member (there is something for the autopilot to drive). A **non-runnable** epic —
a `complete`/`archived` epic, or one with no drivable members — SHALL NOT render a
run control at all, so a closed epic can never be run from the board. Activating a
run control SHALL NOT toggle the group's collapsed state (the two affordances are
distinct); instead it SHALL open a **confirmation modal** reading exactly "This
will deliver the full epic, are you sure you want to continue?" with a **Yes**
control and a **No** control, plus a **close (✕) control in its top-left**. The
**epic-level run** (the same autopilot launch the removed hierarchy panel
triggered) SHALL be dispatched **only** when the user chooses **Yes**; choosing
**No**, the ✕ control, or `Escape` SHALL dismiss the modal **without** dispatching
any run. Independently of the run control, **every** epic group header SHALL also
carry a **clickable open control** — distinct from both the run control and the
collapse toggle, and present on every epic whether runnable or not — that opens an
**epic-detail modal** for that epic. The header's controls SHALL render **inline
on the header's title row, immediately after the epic's title text** — the run
control first (when present), then the open control **one cell after it** (the
open control sits flush to the title when no run control renders), inside the
group's panel — never docked at the far edge of the lane row outside the
group's visual box. If the rendered title is too wide for its lane, the
controls SHALL pin inside the lane's right edge — painting over the clipped
title tail — so they stay visible and clickable; a header control SHALL never
render outside its group row. The header controls and every modal **close (✕) control**
SHALL be **compact — a single row high and exactly three cells wide** — while
remaining visually evident as clickable buttons. The **epic-detail modal** SHALL
occupy the
majority of the viewport, carry a **close (✕) control** the user can click (in
addition to `Escape`), and present the epic's slug and status, its theme and
initiative when set, a **list of the epic's member specs** — each showing its board
state and risk and **clickable to open that change's own spec-detail modal**
(the same spec-detail modal a lane card opens, pushed on top of the epic-detail
modal so dismissing it returns to the epic-detail modal) — and the epic's own
overview rendered as **Markdown** from its
`epics/<slug>/epic.md` artifact. Reading that epic artifact SHALL be a
**dependency-free** operation (no `textual`), so it is unit-tested without the
TUI. Activating the open control SHALL NOT toggle the group's collapsed state, and
dismissing the epic-detail modal (its ✕ control or `Escape`) SHALL return to the
board. While the mode is `initiative`, every lane SHALL render its cards grouped under a **collapsible per-initiative header** — one group per initiative in the aggregation's group order, titled with the initiative's slug and status, the epics carrying no `Initiative:` collected under a single `workspace` group — fed by the aggregation's existing initiative `groups`; an initiative header carries **no run and no open control** (both are epic-scoped). While the mode is `none`, every lane SHALL render its cards **flat** — no group headers — matching the pre-grouping lane layout. The grouping mode SHALL fold into the diff-aware refresh so an idle board never repaints and a collapsed group stays collapsed across refreshes; any mode change SHALL repaint the lanes.
Removing the hierarchy panel SHALL NOT change the board's **data layer**
(`build_board`, the aggregation, the epic-run launch builder): only the rendering
and the run trigger move.

#### Scenario: Epic mode is the default
- **WHEN** the app is mounted with no override
- **THEN** the grouping mode is `epic` and each lane's cards render under
  per-epic headers

#### Scenario: Each lane groups its cards under per-epic headers when grouped
- **GIVEN** the grouping mode is `epic` and a lane holds cards from two different epics
- **WHEN** the lane is rendered
- **THEN** the cards appear under two collapsible epic headers, each header
  naming its epic, with each epic's cards beneath its own header

#### Scenario: An epic group header shows the epic's initiative
- **GIVEN** the grouping mode is `epic` and an epic that belongs to an initiative
- **WHEN** that epic's group header renders
- **THEN** the header shows the epic's slug and status and the initiative it
  belongs to

#### Scenario: The header shows the epic's per-lane card count
- **GIVEN** the grouping mode is `epic` and an epic with two cards in one lane
- **WHEN** that epic's group header renders in that lane
- **THEN** the header's title carries the count 2 alongside the slug, status,
  and initiative

#### Scenario: The group header is a single row
- **GIVEN** the grouping mode is `epic`
- **WHEN** an epic group renders
- **THEN** its title row is the group's topmost row — no border row above it —
  and the inline run/open controls sit on that same row

#### Scenario: Epic groups use a theme surface band with theme border separators
- **GIVEN** the grouping mode is `epic`
- **WHEN** a lane's epic groups render
- **THEN** each group has the theme's panel background and adjacent groups are
  divided by a theme border-variable separator line, with no per-epic-status
  colour applied

#### Scenario: A runnable epic shows a run control
- **GIVEN** the grouping mode is `epic` and an epic whose status is `ready` or `active` with
  at least one `unplanned` or `ready` member
- **WHEN** that epic's group header renders
- **THEN** the header carries a clickable run control

#### Scenario: The header controls sit inline next to the epic name
- **GIVEN** the grouping mode is `epic` and a runnable epic's group header
- **WHEN** the header renders
- **THEN** the run control occupies the header's title row immediately after
  the title text with the open control one cell after it, inside the
  group's panel, not at the lane row's far edge, and each control is one row
  high and three cells wide

#### Scenario: Modal close controls are one row high
- **GIVEN** the spec-detail, epic-detail, or epic-run confirmation modal is
  open
- **WHEN** its close (✕) control renders
- **THEN** that control occupies a single row, three cells wide

#### Scenario: A non-runnable epic's open control sits flush to the title
- **GIVEN** the grouping mode is `epic` and a non-runnable epic's group header
- **WHEN** the header renders
- **THEN** the open control occupies the header's title row immediately after
  the title text, with no run control before it

#### Scenario: An overlong title pins the controls inside the lane
- **GIVEN** the grouping mode is `epic` and an epic whose rendered header title is wider
  than its lane
- **WHEN** the header renders
- **THEN** the run and open controls render fully inside the lane on the title
  row, pinned at the lane's right edge over the clipped title, and remain
  clickable

#### Scenario: A non-runnable epic shows no run control
- **GIVEN** the grouping mode is `epic` and a `complete`/`archived` epic (or one with no
  `unplanned`/`ready` member)
- **WHEN** that epic's group header renders
- **THEN** the header carries no run control, so the epic cannot be run from the
  board

#### Scenario: Clicking a run control opens the confirmation modal
- **GIVEN** the grouping mode is `epic` and a runnable epic's run control
- **WHEN** the run control is clicked
- **THEN** a confirmation modal reading "This will deliver the full epic, are you
  sure you want to continue?" is pushed onto the screen stack, no epic-level run
  has been dispatched yet, and the group's collapsed state is unchanged

#### Scenario: Confirming with Yes dispatches the epic-level run
- **GIVEN** an open epic-run confirmation modal for an epic
- **WHEN** the user activates its Yes control
- **THEN** the epic-level run is dispatched for that epic and the modal is
  dismissed

#### Scenario: Declining or closing the modal runs nothing
- **GIVEN** an open epic-run confirmation modal
- **WHEN** the user activates its No control, its ✕ close control, or presses
  `Escape`
- **THEN** the modal is dismissed and no epic-level run is dispatched

#### Scenario: Every epic group header carries an open control
- **GIVEN** the grouping mode is `epic` and any epic (runnable or not)
- **WHEN** that epic's group header renders
- **THEN** the header carries a clickable open control distinct from the run
  control

#### Scenario: Clicking the open control opens the epic-detail modal
- **GIVEN** the grouping mode is `epic` and an epic group header's open control
- **WHEN** the open control is clicked
- **THEN** an epic-detail modal for that epic is pushed onto the screen stack and
  the group's collapsed state is unchanged

#### Scenario: The epic-detail modal lists the epic's member specs
- **GIVEN** an epic with member specs
- **WHEN** its epic-detail modal opens
- **THEN** the modal shows the epic's slug and status and a list of its member
  specs, each with its board state and risk

#### Scenario: Clicking a member spec opens its spec-detail modal
- **GIVEN** an open epic-detail modal listing the epic's member specs
- **WHEN** the user clicks one of the listed member specs
- **THEN** that change's spec-detail modal is pushed onto the screen stack (the
  same modal a lane card opens), on top of the epic-detail modal, and dismissing
  it returns to the epic-detail modal

#### Scenario: The epic-detail modal shows the epic overview
- **GIVEN** an epic whose `epics/<slug>/epic.md` artifact exists
- **WHEN** its epic-detail modal opens
- **THEN** the modal renders that epic artifact's content as Markdown

#### Scenario: The epic-detail modal is dismissed by its close control
- **GIVEN** an open epic-detail modal
- **WHEN** the user clicks its ✕ close control or presses `Escape`
- **THEN** the modal is dismissed and the board screen is shown again

#### Scenario: Reading the epic artifact is dependency-free
- **GIVEN** an environment without `textual`
- **WHEN** the epic-artifact helper is called for an epic that has an
  `epics/<slug>/epic.md`
- **THEN** it returns that epic's Markdown text without importing `textual`

#### Scenario: Selecting none renders flat lanes
- **GIVEN** the grouping mode is `epic`
- **WHEN** the mode is set to `none` (via the segmented control or by
  cycling `g`)
- **THEN** every lane re-renders its cards flat, with no group headers

#### Scenario: A collapsed epic group hides its cards
- **GIVEN** the grouping mode is `epic` and an epic group whose header is expanded
- **WHEN** that group's header is collapsed
- **THEN** that epic's cards in the lane are hidden while another epic's group
  stays visible

#### Scenario: The g key cycles the grouping mode
- **GIVEN** the mounted board in `epic` mode
- **WHEN** `g` is pressed three times
- **THEN** the mode advances through `initiative` and `none` back to `epic`,
  the segmented control highlights the active mode at each step, and the lanes
  repaint at each step

#### Scenario: A mode button selects its mode directly
- **GIVEN** the mounted board in `epic` mode
- **WHEN** the segmented control's `initiative` button is activated
- **THEN** the grouping mode becomes `initiative` and the active highlight
  moves to that button

#### Scenario: Initiative mode groups lanes by initiative
- **GIVEN** the grouping mode is `initiative`, two epics sharing one
  initiative, and one epic carrying none
- **WHEN** a lane holding cards from all three epics renders
- **THEN** the shared-initiative epics' cards sit under one collapsible header
  titled with the initiative's slug and status, the third epic's cards sit
  under a `workspace` group header, and no initiative header carries a run or
  open control

### Requirement: Board search
id: board-search
base: 18966134bdeb

The `tui` board SHALL provide live member search from the centered search input in the header bar, accompanied by a clear (✕)
control and a match-count label. When `/` is pressed on the board, the app
SHALL focus the search input. While a non-empty query is active, each lane
SHALL mount only the members matched by a case-insensitive substring test over
the member's slug, its epic's slug, and its epic's initiative slug; a matched
card SHALL highlight the matched span of its slug in the accent style (a card
matched only via its epic or initiative renders unhighlighted); the
match-count label SHALL show the number of matching members (and SHALL be
blank with no active query); and, while a grouping mode is active (`epic` or `initiative`), a group — epic or initiative — none of whose members match SHALL mount no group header in any lane. When `escape` is
pressed in the search input or the ✕ control is activated, the app SHALL
clear the query and restore the full board. The query SHALL be view-level
state only — `build_board` aggregation and the pure launch builders are
unchanged — and SHALL fold into the diff-aware lane signatures, so an
unchanged board under an unchanged query repaints no lane, a query edit
always repaints, and the active filter survives interval refreshes.

#### Scenario: Slash focuses the search input
- **WHEN** `/` is pressed on the mounted board
- **THEN** the header-bar search input holds focus

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
- **GIVEN** the grouping mode is `epic` and an active query matching none of
  one epic's members
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

### Requirement: Board command palette
id: board-command-palette
base: b7ccbc1f0be7

The `tui` board SHALL open textual's built-in command palette on `ctrl+p`,
and the board SHALL advertise the binding in its footer with the key display
`^p`. When the palette is opened from the board screen, it SHALL list exactly
the board's own commands in place of textual's stock system commands: a grouping command that cycles the grouping mode (`epic` → `initiative` → `none`) through the same path as the `g` key, a clear-search command — offered only while a search query is
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
