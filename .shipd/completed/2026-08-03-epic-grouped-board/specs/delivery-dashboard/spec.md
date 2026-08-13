## MODIFIED Requirements

### Requirement: Board TUI
id: board-tui
base: 30e02a8da1df

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
SHALL fall back to a clear `pip install` hint and a non-zero exit. The app SHALL
present a `Header`, a `Footer` showing the key bindings, a **controls strip**
above the board carrying a **group-by-epic toggle** (see the Board epic grouping
requirement), and below it a horizontal board of **five bordered lifecycle
lanes** (`unplanned`, `ready`, `building`, `review`, `shipped`), each a
vertically-scrolling column. Every member SHALL render as a **focusable task-card
widget** carrying its slug and risk, with a left accent bar and a visible
highlight when focused. The app SHALL move focus
between cards and lanes with the arrow keys, toggle epic grouping and quit
via footer-bound keys, open a **modal spec-detail screen** for the focused member
either on `Enter` or on a **mouse click on the card** (a click first focuses the
clicked card, then opens the same modal), and re-read the board on the
`--interval` (default 2) so live runs
update. The **spec-detail screen** SHALL occupy the majority of the viewport and
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

#### Scenario: App mounts the controls strip, lanes, header and footer
- **WHEN** the textual app is mounted (via the test harness) on a board with
  members
- **THEN** its widget tree contains a header, a footer, the group-by-epic toggle
  control, and the five named lifecycle lanes — and no hierarchy panel

#### Scenario: Members are focusable cards in their lifecycle lane
- **GIVEN** a board with a member whose board state maps to the `building` lane
- **WHEN** the app is mounted
- **THEN** that member renders as a focusable task-card inside the `building`
  lane, carrying its slug and risk

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

## ADDED Requirements

### Requirement: Board epic grouping
id: board-epic-grouping

The `tui` board SHALL provide a **group-by-epic** mode, toggled from a control in
the **controls strip** above the lanes and also from a footer-bound key, and
SHALL start with grouping **on** by default. When grouping is **on**, every
lifecycle lane SHALL render its cards grouped under a **collapsible per-epic
header** (one group per epic, in board order, each group individually
collapsible), replacing the previous shipped-lane-only grouping — so an epic's
cards in a lane sit together under that epic's header. Each epic group header
SHALL show the epic's slug and status and, when the epic belongs to an
initiative, that **initiative** (its slug); this re-homes the initiative → epic
structure that the removed hierarchy panel used to carry. The group's visual
SHALL be a plain **gray background** with **black separator lines** dividing
adjacent groups — no per-epic-status colour coding. Each epic group header SHALL
carry a **clickable run control** that fires the **epic-level run** (the same
autopilot launch the removed hierarchy panel triggered) for that epic; activating
the run control SHALL NOT toggle the group's collapsed state (the two affordances
are distinct). When grouping is **off**, every lane SHALL render its cards
**flat** — no epic headers — matching the pre-grouping lane layout. Grouping
state SHALL fold into the diff-aware refresh so an idle board never repaints and a
collapsed group stays collapsed across refreshes; toggling the mode SHALL repaint
the lanes. Removing the hierarchy panel SHALL NOT change the board's **data
layer** (`build_board`, the aggregation, the epic-run launch builder): only the
rendering and the run trigger move.

#### Scenario: Grouping is on by default
- **WHEN** the app is mounted with no override
- **THEN** the group-by-epic mode is active and each lane's cards render under
  per-epic headers

#### Scenario: Each lane groups its cards under per-epic headers when grouped
- **GIVEN** grouping is on and a lane holds cards from two different epics
- **WHEN** the lane is rendered
- **THEN** the cards appear under two collapsible epic headers, each header
  naming its epic, with each epic's cards beneath its own header

#### Scenario: An epic group header shows the epic's initiative
- **GIVEN** grouping is on and an epic that belongs to an initiative
- **WHEN** that epic's group header renders
- **THEN** the header shows the epic's slug and status and the initiative it
  belongs to

#### Scenario: Epic groups use a gray background with black separators
- **GIVEN** grouping is on
- **WHEN** a lane's epic groups render
- **THEN** each group has a gray background and adjacent groups are divided by a
  black separator line, with no per-epic-status colour applied

#### Scenario: Clicking an epic header's run control runs the epic
- **GIVEN** grouping is on and an epic group header with a run control
- **WHEN** the run control is clicked
- **THEN** the epic-level run is dispatched for that epic and the group's
  collapsed state is unchanged

#### Scenario: Toggling grouping off renders flat lanes
- **GIVEN** grouping is on
- **WHEN** the group-by-epic toggle is switched off
- **THEN** every lane re-renders its cards flat, with no epic headers

#### Scenario: A collapsed epic group hides its cards
- **GIVEN** grouping is on and an epic group whose header is expanded
- **WHEN** that group's header is collapsed
- **THEN** that epic's cards in the lane are hidden while another epic's group
  stays visible
