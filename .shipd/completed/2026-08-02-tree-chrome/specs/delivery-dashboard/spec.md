## MODIFIED Requirements

### Requirement: Board TUI
id: board-tui
base: 527edb258020

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
present a `Header`, a `Footer` showing the key bindings, a left **collapsible
hierarchy panel** (a `textual` tree of initiative → epic → change whose
initiative and epic nodes collapse and expand individually, starting expanded;
the tree's synthetic root is hidden — no `hierarchy` header — so the initiative
groups are the top level, and each nesting level is indented by a single guide
character via a minimal `guide_depth`),
and, beside it, a horizontal board of **five bordered lifecycle lanes**
(`unplanned`, `ready`, `building`, `review`, `shipped`), each a
vertically-scrolling column. Every member SHALL render as a **focusable task-card
widget** carrying its slug and risk, with a left accent bar and a visible
highlight when focused. The `shipped` lane SHALL group its cards under
collapsible per-epic headers, coloured by epic status. The app SHALL move focus
between cards and lanes with the arrow keys, toggle the hierarchy panel and quit
via footer-bound keys, open a **modal detail screen** for the focused member on
`Enter`, and re-read the board on the `--interval` (default 2) so live runs
update. The interval refresh SHALL be **diff-aware**: it re-aggregates and then
repaints only the lanes and the hierarchy panel whose board-derived content
changed since the previous render — leaving unchanged lanes and the tree
untouched, so an idle board never repaints (no flashing) and a shipped group the
user has collapsed stays collapsed across refreshes. The board's **data layer** —
`build_board`, `member_actions`, the aggregation, and the launch-argv builders —
SHALL keep its existing contracts; only the rendering changes. Importing the
delivery engine (`autopilot`) SHALL NOT require `textual`: the run-heartbeat
writer it depends on lives in a stdlib module, so the engine and its test suites
stay dependency-free.

#### Scenario: An unchanged board repaints no lane
- **GIVEN** a mounted app whose aggregated board is identical to the previous
  render
- **WHEN** the refresh runs (driven by the test harness)
- **THEN** no lane's children are torn down and remounted — the existing
  task-card widget instances are retained

#### Scenario: A collapsed shipped group survives refresh
- **GIVEN** a shipped per-epic group the user has collapsed
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

#### Scenario: App mounts the panel, lanes, header and footer
- **WHEN** the textual app is mounted (via the test harness) on a board with
  members
- **THEN** its widget tree contains a header, a footer, the hierarchy panel, and
  the five named lifecycle lanes

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
- **THEN** a modal detail screen for that member is pushed onto the screen stack

#### Scenario: Hierarchy epic node collapses
- **GIVEN** the hierarchy panel with an expanded epic node
- **WHEN** that epic node is collapsed
- **THEN** its child change nodes are no longer shown while sibling epics remain
  expanded

#### Scenario: Shipped lane groups collapse
- **GIVEN** the `shipped` lane grouped under a per-epic header
- **WHEN** that group's header is collapsed
- **THEN** that epic's shipped cards are hidden while another epic's group stays
  visible

#### Scenario: Live refresh re-reads the board
- **GIVEN** a mounted app whose underlying heartbeat/report changes
- **WHEN** the refresh interval elapses (driven by the test harness)
- **THEN** the app re-aggregates via `build_board` and the lanes reflect the new
  member states

#### Scenario: The engine imports without textual
- **WHEN** the `autopilot` module is imported in an environment without `textual`
- **THEN** the import succeeds — the run-heartbeat writer it uses is in a stdlib
  module, not `dashboard`


#### Scenario: Hierarchy tree hides its root and indents minimally
- **WHEN** the app is mounted
- **THEN** the hierarchy tree reports `show_root` false (no `hierarchy` header
  row) and a `guide_depth` equal to the reduced minimal value, so initiative
  groups render at the top level with a single-character-per-level indent
