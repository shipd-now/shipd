## MODIFIED Requirements

### Requirement: Board TUI
id: board-tui
base: 3a27ac666f1b

The dashboard CLI SHALL provide a `tui` verb rendering the board full-screen as a
`textual` application (the pinned `textual` dependency; `dashboard.py` may import
it, and when it is not installed the verb SHALL exit with a clear
`pip install` hint rather than a traceback). The app SHALL present a `Header`, a
`Footer` showing the key bindings, a left **collapsible hierarchy panel** (a
`textual` tree of initiative → epic → change whose initiative and epic nodes
collapse and expand individually, starting expanded), and, beside it, a
horizontal board of **five bordered lifecycle lanes** (`unplanned`, `ready`,
`building`, `review`, `shipped`), each a vertically-scrolling column. Every member
SHALL render as a **focusable task-card widget** carrying its slug and risk, with
a left accent bar and a visible highlight when focused. The `shipped` lane SHALL
group its cards under collapsible per-epic headers, coloured by epic status. The
app SHALL move focus between cards and lanes with the arrow keys, toggle the
hierarchy panel and quit via footer-bound keys, open a **modal detail screen** for
the focused member on `Enter`, and re-read the board on the `--interval` (default
2) so live runs update. The board's **data layer** — `build_board`,
`member_actions`, the aggregation, and the launch-argv builders — SHALL keep its
existing contracts; only the rendering changes. Importing the delivery engine
(`autopilot`) SHALL NOT require `textual`: the run-heartbeat writer it depends on
lives in a stdlib module, so the engine and its test suites stay
dependency-free.

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

### Requirement: Board actions
id: board-actions
base: 0fed6f6501cb

The interactive `tui` board SHALL offer per-card actions that act on the member
under the focus (or click), plus an epic-level run:

- `plan` on an `unplanned` member SHALL launch an interactive `/s:plan <member>`
  session in the member's worktree.
- `run` SHALL launch a detached driver that writes the heartbeat the board tails
  — a single named-member drive for a card, or the full autopilot for the
  epic-level run — so the board keeps rendering and never blocks on the run.
- `open` on a parked or shipped member carrying a session id SHALL resume that
  exact session via `claude --resume <id>`; `open` SHALL be disabled while a
  member is mid-drive.

Interactive actions (`plan`, `open`) SHALL open in a new tmux window when `$TMUX`
is set, and otherwise SHALL suspend the running app (via the textual app's
suspend mechanism), run to completion, and restore the board on return. The
argument vector each action spawns SHALL be produced by a pure function so it is
testable without spawning a process.

#### Scenario: Plan launches interactively under tmux
- **GIVEN** `$TMUX` is set
- **WHEN** the `plan` action fires on an unplanned member
- **THEN** the built launch is a `tmux new-window` running `/s:plan` for that
  member in its worktree, and the app is not suspended

#### Scenario: Run is detached and heartbeat-backed
- **WHEN** the `run` action fires on a ready member
- **THEN** the built launch is a detached driver for that single member, not a
  blocking call, and the board continues rendering

#### Scenario: Open is disabled while a member is driving
- **GIVEN** a member whose live state is `driving`
- **WHEN** the board computes that member's eligible actions
- **THEN** `open` is not among them

#### Scenario: Open resumes the exact session when parked
- **GIVEN** a member parked with a recorded session id
- **WHEN** the `open` action fires
- **THEN** the built launch resumes that session id via `claude --resume`
