# delivery-dashboard

### Requirement: Autopilot run heartbeat
id: autopilot-heartbeat

While an autopilot run executes (not `--dry-run`), the autopilot SHALL maintain
`<content-dir>/autopilot/<epic>-heartbeat.json`, atomically replaced (temp file +
rename) at every transition — run start, member start, stage attempt start,
member outcome, run end — carrying the epic, the run state
(`running`/`finished`/`aborted`), the pipeline provenance, a monotonically
increasing `seq`, an epoch `updated_at`, and a per-member roster with each
member's slug, risk, and live state (`pending`, `driving` with current stage and
attempt, `shipped`, `rejected`, `needs-human` — with reason and session id when
present, and `skipped` with the skipped state). At run start the autopilot SHALL
record the writer's process id (`pid`) and `host` in the heartbeat, so a reader
can probe whether the writer is still alive. The autopilot SHALL record a
member's `session_id` in its roster entry as soon as a driven turn first yields
one — not only at the member's terminal outcome — so the entry carries a resume
handle while the member is still being driven. The autopilot SHALL record a
member's `started_at` (epoch seconds) in its roster entry when the member first
starts being driven, set once and left unchanged on subsequent stage
re-attempts, so the spec-detail modal can show elapsed time since the build
began. If the run terminates abnormally
but catchably before the clean run-end write — a raised `AutopilotError`, or a
received `SIGTERM`/`SIGINT` — then the autopilot SHALL write a terminal
`aborted` run state, and SHALL NOT overwrite a `finished` state once written. If
a heartbeat write fails, then the run SHALL continue unaffected, warning once and
disabling further writes. The `<content-dir>/autopilot/` directory SHALL be
git-ignored as runtime state.

#### Scenario: Session id is recorded mid-drive
- **WHEN** a driven member's first turn yields a session id, before the member
  reaches any terminal outcome
- **THEN** the heartbeat's roster entry for that member carries the `session_id`
  while its state is still `driving`

#### Scenario: A member start records a start timestamp
- **WHEN** the autopilot starts driving a member for the first time
- **THEN** the heartbeat's roster entry for that member carries a `started_at`
  epoch timestamp, unchanged by a subsequent stage re-attempt of the same member

#### Scenario: Stage transitions are visible mid-run
- **WHEN** the autopilot starts the build stage's first attempt for a member
- **THEN** the heartbeat file parses as JSON and shows that member as `driving`
  at stage `build`, attempt 1, with a `seq` greater than the run-start write

#### Scenario: The heartbeat records the writer identity
- **WHEN** a run starts and seeds its heartbeat
- **THEN** the heartbeat file carries the writer's `pid` and `host`

#### Scenario: A catchably-terminated run leaves an aborted heartbeat
- **GIVEN** a running autopilot whose heartbeat records `state:"running"`
- **WHEN** it receives `SIGTERM` before the clean run-end write
- **THEN** the heartbeat's run state is written once as `aborted`, not left at
  `running`

#### Scenario: A clean finish is never overwritten by abort handling
- **WHEN** a run completes and writes `state:"finished"`
- **THEN** the abort-guarding finally path does not overwrite it, and the
  heartbeat's final run state is `finished`

#### Scenario: Dry runs write nothing
- **WHEN** the autopilot runs with `--dry-run`
- **THEN** no heartbeat file is created

#### Scenario: A failing write never fails the run
- **GIVEN** a heartbeat destination that cannot be written
- **WHEN** the autopilot drives a member
- **THEN** the run completes normally with a single warning and no raised error

### Requirement: Board aggregation
id: board-aggregation

The dashboard CLI SHALL provide a `board` verb that aggregates, for each epic
discovered under the invocation root **or any `.worktrees/<name>` directory
under it** (or only the epic named by `--epic`): the
epic's status, theme, and initiative context — the initiative's status resolved
through the workspace brief when a workspace is discoverable, the bare slug
otherwise, never an error; every stub member's worktree-aware state — derived
from the invocation root first and, when the root says `unplanned`, from a
locate-style probe of `.worktrees/<slug>` (planned change or completed archive),
reporting the state and where it lives; and the run context merged from the live
heartbeat and the latest run report when either exists. Epic discovery SHALL
probe the invocation root first, then each `.worktrees/<name>` directory in
sorted name order, resolving each candidate's content directory independently
and skipping any candidate whose configuration is unreadable; when the same
slug exists in more than one candidate, the invocation root's copy SHALL win,
then the first hosting worktree in sorted order, and the epic SHALL be
aggregated exactly once. Each aggregated epic SHALL carry its hosting root as
`location`, and the epic's file, status, heartbeat, and run report SHALL be
read from that hosting root. The aggregation SHALL
additionally group its epics under their initiative — a workspace-wide group for
epics carrying no `Initiative:` — and SHALL annotate each member with the board
actions eligible for it (`plan` for an `unplanned` member, `run` for a member
ready to drive, `open` for a parked or shipped member carrying a session id) and
that member's resumable `session_id` when known. The verb SHALL print an aligned
human-readable board by default and the full board object as JSON under `--json`;
the human-readable board and the TUI's epic group header SHALL mark an epic
whose `location` is not the invocation root with a `[worktree]` marker, and the
TUI's epic-detail overview SHALL read the epic markdown from the epic's
hosting root.

#### Scenario: Epics group under their initiative
- **GIVEN** two epics sharing one `Initiative:` and one epic carrying none
- **WHEN** the board is built
- **THEN** the two share a single initiative group and the third appears under a
  workspace-wide group

#### Scenario: Members carry eligible actions
- **GIVEN** an epic with an unplanned member, a ready member, and a member parked
  as needs-human with a session id
- **WHEN** the board is built
- **THEN** the unplanned member's eligible actions include `plan`, the ready
  member's include `run`, and the parked member's include `open`

#### Scenario: A worktree-parked member is visible
- **GIVEN** a member whose plan sits at `rejected` inside `.worktrees/<slug>`
  while the root's `planned/` lacks it
- **WHEN** the board is built
- **THEN** the member's row reports `rejected` and its worktree location instead
  of `unplanned`

#### Scenario: JSON mode is machine-readable
- **WHEN** `board --json` runs
- **THEN** stdout parses as a single JSON object listing the initiative groups,
  their epics, and each epic's members

#### Scenario: A worktree-authored epic joins the board
- **GIVEN** an epic whose `epics/<slug>/epic.md` exists only under
  `.worktrees/<name>`'s content directory
- **WHEN** the board is built from the invocation root
- **THEN** the epic is aggregated with its status and members, and its
  `location` is that worktree's root

#### Scenario: The invocation root shadows worktree copies
- **GIVEN** the same epic slug hosted under the invocation root and under a
  worktree
- **WHEN** the board is built
- **THEN** the epic appears exactly once, aggregated from the invocation root

#### Scenario: A worktree-hosted epic is marked on the text board
- **GIVEN** an epic whose `location` is a worktree root
- **WHEN** the human-readable board prints
- **THEN** that epic's header line carries `[worktree]`

#### Scenario: An unreadable worktree config does not break discovery
- **GIVEN** a worktree whose content-directory configuration cannot be read
- **WHEN** the board is built
- **THEN** that worktree is skipped and aggregation completes without raising

### Requirement: Board TUI
id: board-tui

The dashboard CLI SHALL provide a `tui` verb rendering the board full-screen as a
`textual` application (the pinned `textual` dependency). When `textual` is not
importable, `dashboard.py`'s script entry SHALL, before importing `textual`,
auto-provision it: create-or-reuse a dedicated virtualenv under
`${XDG_CACHE_HOME:-~/.cache}/shipd/tui-venv`, install the pinned dependency
into it from `requirements.txt` (printing a one-time setup message on stderr),
and re-exec the same command with that venv's interpreter — so the board runs
with no manual install and without modifying the system Python. Provisioning
SHALL be attempted for any `dashboard.py` verb invocation that finds `textual`
missing (so `board` also works), SHALL be skipped entirely when
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

### Requirement: Board actions
id: board-actions

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

### Requirement: Board epic grouping
id: board-epic-grouping

The `tui` board SHALL provide a three-state **grouping mode** — `epic`, `initiative`, `none` — selected from a **segmented control in the header bar** (one compact one-row button per mode, the active mode visibly highlighted) and cycled in that order by the footer-bound `g` key, and SHALL start in **`epic`** mode by default. The three mode segments SHALL keep **fixed positions and widths** regardless of which mode is active — selecting a mode never moves any segment. While the mode is `epic`, every lifecycle lane SHALL render its cards grouped under a **collapsible per-epic
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
group's contents, so the title row (collapse arrow and title text) is the
group's first row.

The epic group header SHALL carry **no menu control and no other trailing
control** — the title row holds only the **collapse arrow** and the **title
text**. A **click on the header's collapse arrow** (the leading arrow glyph)
SHALL toggle the group's collapsed state and SHALL open no modal. A **click
anywhere else on the header title** SHALL open the **epic-detail modal** for
that epic and SHALL NOT change the group's collapsed state. The title SHALL
span the lane's content width so a click off the arrow anywhere along the
header opens the epic; when the title is wider than its space it SHALL
truncate with an **ellipsis inside its own space**. Every lane's **member
cards** SHALL keep the lane's **full scrollable content width** — no header
control narrows them.

The **epic-detail modal** SHALL occupy the majority of the viewport, carry a
**close (✕) control** the user can click (in addition to `Escape`), and
present the epic's slug and status, its theme and initiative when set, a
**list of the epic's member specs** — each showing its board state and risk
and **clickable to open that change's own spec-detail modal** (the same
spec-detail modal a lane card opens, pushed on top of the epic-detail modal so
dismissing it returns to the epic-detail modal) — and the epic's own overview
rendered as **Markdown** from its `epics/<slug>/epic.md` artifact. Reading
that epic artifact SHALL be a **dependency-free** operation (no `textual`), so
it is unit-tested without the TUI. When the epic is **runnable** — its status
is `ready` or `active` **and** it has at least one `unplanned` or `ready`
member (there is something for the autopilot to drive) — the epic-detail modal
SHALL present a **Run epic** control; a non-runnable epic (`complete`/
`archived`, or one with no drivable member) SHALL present **no Run control**,
so it can never be run from the board. Activating **Run epic** SHALL open a
**confirmation modal** reading exactly "This will deliver the full epic, are
you sure you want to continue?" with a **Yes** control, a **No** control, and
a **close (✕) control in its top-left**. The **epic-level run** (the same
autopilot launch the removed hierarchy panel triggered) SHALL be dispatched
**only** when the user chooses **Yes**; choosing **No**, the ✕ control, or
`Escape` SHALL dismiss the confirmation **without** dispatching any run.
Dismissing the epic-detail modal (its ✕ control or `Escape`) SHALL return to
the board. The modal **close (✕) controls** SHALL be **compact — a single row
high and exactly three cells wide** — while remaining visually evident as
clickable buttons.

While the mode is `initiative`, every lane SHALL render its cards grouped under a **collapsible per-initiative header** — one group per initiative in the aggregation's group order, titled with the initiative's slug and status, the epics carrying no `Initiative:` collected under a single `workspace` group — fed by the aggregation's existing initiative `groups`; an initiative header carries **no menu control** (epic actions are epic-scoped). While the mode is `none`, every lane SHALL render its cards **flat** — no group headers — matching the pre-grouping lane layout. The grouping mode SHALL fold into the diff-aware refresh so an idle board never repaints and a collapsed group stays collapsed across refreshes; any mode change SHALL repaint the lanes.
Removing the hierarchy panel SHALL NOT change the board's **data layer**
(`build_board`, the aggregation, the epic-run launch builder): only the rendering
and the run trigger move.

#### Scenario: Epic mode is the default
- **WHEN** the app is mounted with no override
- **THEN** the grouping mode is `epic` and each lane's cards render under
  per-epic headers

#### Scenario: Mode segments never move
- **GIVEN** the mounted board in `epic` mode
- **WHEN** each of the three modes is selected in turn
- **THEN** every segment button's region is identical across all three
  states

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
- **THEN** the header's title ends with a ` (2)` suffix rendered in the muted
  foreground colour

#### Scenario: The group header is a single row
- **GIVEN** the grouping mode is `epic`
- **WHEN** an epic group renders
- **THEN** its title row is the group's topmost row — no border row above it —
  and the row carries only the collapse arrow and the title text

#### Scenario: Epic groups use a theme surface band with theme border separators
- **GIVEN** the grouping mode is `epic`
- **WHEN** a lane's epic groups render
- **THEN** each group has the theme's panel background and adjacent groups are
  divided by a theme border-variable separator line, with no per-epic-status
  colour applied

#### Scenario: The epic header carries no menu control
- **GIVEN** the grouping mode is `epic` and any epic's group header
- **WHEN** the header renders
- **THEN** the title row carries no `≡` menu control and no other trailing
  control — only the collapse arrow and the title text

#### Scenario: The member cards keep the lane's full content width
- **GIVEN** the grouping mode is `epic` and an epic group with member cards
- **WHEN** the group renders
- **THEN** the group's collapsible box spans the lane's full scrollable content
  width, so no member card is narrowed by a header control

#### Scenario: Modal close controls are one row high
- **GIVEN** the spec-detail, epic-detail, or epic-run confirmation modal is
  open
- **WHEN** its close (✕) control renders
- **THEN** that control occupies a single row, three cells wide

#### Scenario: An overlong title ellipsizes inside its own space
- **GIVEN** the grouping mode is `epic` and an epic whose rendered header title is wider
  than its lane
- **WHEN** the header renders, whether the group is expanded or collapsed
- **THEN** the title truncates with an ellipsis inside its own space, rendering
  fully inside the lane

#### Scenario: Clicking the header title opens the epic-detail modal
- **GIVEN** the grouping mode is `epic` and an epic's expanded group header
- **WHEN** the user clicks the header title anywhere off the collapse arrow
- **THEN** an epic-detail modal for that epic is pushed onto the screen stack
  and the group's collapsed state is unchanged

#### Scenario: Clicking the collapse arrow toggles without opening
- **GIVEN** the grouping mode is `epic` and an epic's expanded group header
- **WHEN** the user clicks the header's leading collapse arrow
- **THEN** the group's collapsed state toggles and no modal is pushed

#### Scenario: A runnable epic's detail modal offers Run epic
- **GIVEN** a runnable epic
- **WHEN** its epic-detail modal opens
- **THEN** the modal presents a Run epic control

#### Scenario: A non-runnable epic's detail modal offers no Run
- **GIVEN** a `complete`/`archived` epic (or one with no `unplanned`/`ready` member)
- **WHEN** its epic-detail modal opens
- **THEN** the modal presents no Run control, so the epic cannot be run from the
  board

#### Scenario: Choosing Run epic opens the confirmation modal
- **GIVEN** a runnable epic's open epic-detail modal
- **WHEN** the user activates its Run epic control
- **THEN** the confirmation modal reading "This will deliver the full epic, are
  you sure you want to continue?" is pushed, with no epic-level run dispatched
  yet

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
  under a `workspace` group header, and no initiative header carries a menu
  control

### Requirement: Board search
id: board-search

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

### Requirement: Board theme
id: board-shipd-theme

The `tui` app SHALL register a custom `textual` theme named `shipd`, built from
the Shipd design-system tokens — backgrounds base `#0A0A0D`, surface `#111118`,
elevated panel `#1C1C26`, hover `#22222E`, active `#28283A`; accent/primary
`#C6FF4E` (dim `#8FBF1A`); semantic red `#FF4D3D`, orange `#FF8C42`, green
`#3DCC8E`, blue `#4DA6FF`, purple `#9B7FFF`; foreground tiers `#F0F0F8` /
`#8888A0` / `#55556A`; borders `#2A2A38` / `#3E3E52` — and SHALL activate it as
the app's theme on startup. The theme SHALL be the palette's single source: it
SHALL expose per-lane variables (`lane-unplanned` `#8888A0`, `lane-ready`
`#4DA6FF`, `lane-building` `#FF8C42`, `lane-review` `#9B7FFF`, `lane-shipped`
`#3DCC8E`) and risk variables (`risk-high` `#FF8C42`, `risk-medium` `#C6FF4E`,
`risk-low` `#55556A`) as named theme variables for widget CSS to reference,
and the TUI widget CSS SHALL reference colors only through `$` theme
variables — no hex literals and no named colors outside the theme
definition. The board chrome SHALL render flat dark surfaces: lane and modal
borders are flat (non-round)
theme-variable borders, task-card risk glyphs are coloured through the risk
variables (high=orange, medium=chartreuse, low=dim), and focus highlights
derive from the accent.

#### Scenario: The Shipd theme is registered and active
- **WHEN** the board app is mounted
- **THEN** a theme named `shipd` is registered on the app and is its active
  theme

#### Scenario: The theme exposes lane and risk variables
- **WHEN** the `shipd` theme's variables are resolved
- **THEN** they carry the five per-lane colors (`lane-unplanned` `#8888A0`,
  `lane-ready` `#4DA6FF`, `lane-building` `#FF8C42`, `lane-review` `#9B7FFF`,
  `lane-shipped` `#3DCC8E`) and the three risk colors (`risk-high` `#FF8C42`,
  `risk-medium` `#C6FF4E`, `risk-low` `#55556A`)

#### Scenario: Widget CSS carries no hard-coded colors
- **WHEN** the TUI widget CSS blocks are scanned
- **THEN** they contain no hex color literal and no named color — every color
  reference is a `$` theme variable

#### Scenario: Chrome borders are flat, not round
- **WHEN** the lane and modal container styles render
- **THEN** their borders are flat theme-variable borders with no `round`
  border style anywhere in the TUI widget CSS

### Requirement: Board stall signal
id: board-stall-signal

The board SHALL treat an epic as **stalled** when its live heartbeat's run
`state` is `finished` and at least one roster entry sits at `state:
"needs-human"`; `rejected` entries SHALL NOT stall an epic. The stall predicate
and the accessor for the stalled entries SHALL be pure, dependency-free
functions over the aggregated epic dict (no `textual`, no I/O). While an epic
is stalled, its group header title SHALL carry a `✗` marker rendered in the
registered theme's error color immediately before the epic's slug, and the
stall state SHALL fold into the diff-aware refresh so a stall appearing or
clearing repaints the affected lanes.

The stalled epic's **epic-detail modal** SHALL present the stall banner as a
tinted panel: the theme's error color at reduced (10%) alpha for the
background, with a solid error-colored bar one cell wide along the banner's
full left edge, and content in the theme's normal foreground tiers — never a
solid error background with white text. The banner SHALL carry, top to
bottom: a header row with a bold error-colored `STALLED` label and a
right-aligned muted summary naming the parked count (`N member(s) parked ·
needs-human`); one row per `needs-human` member showing its slug in the
default foreground, its parked stage in the muted tier, and its reason as a
warning-colored chip on a warning-tinted (10%) background; a muted
reassurance line stating retry is safe because every step is checkpointed and
the run resumes from the last durable state; and an action row pairing a
**Retry** control whose visible label reads exactly `Retry run` (never
truncated), styled as a primary control (solid accent background, dark bold
label), with a right-aligned subtle `parked <age> ago` label derived from the
heartbeat's `updated_at`. Activating Retry SHALL dispatch the same detached
epic-level autopilot run the group header's run control dispatches and
dismiss the modal. A non-stalled epic's modal SHALL render neither the banner
nor the Retry control.

#### Scenario: Stalled epic is marked in its group header
- **GIVEN** an epic whose heartbeat run is `finished` with a `needs-human`
  roster entry
- **WHEN** its group header renders
- **THEN** the title carries the theme-error-colored `✗` marker before the slug

#### Scenario: Rejected members do not stall
- **GIVEN** an epic whose finished heartbeat roster holds `rejected` and
  `shipped` entries but no `needs-human` entry
- **WHEN** the stall predicate evaluates it
- **THEN** the epic is not stalled and its header renders no marker

#### Scenario: Stalled epic's modal warns in the tinted accent-bar banner
- **GIVEN** a stalled epic
- **WHEN** its epic-detail modal opens
- **THEN** a panel with the theme's error color at 10% alpha as background and
  a solid error-colored one-cell bar on its left edge shows the bold
  error-colored `STALLED` header with the right-aligned muted parked summary,
  each `needs-human` member's slug with its muted stage and warning-chip
  reason, the muted retry-safety reassurance line, and an action row with a
  primary control labeled exactly `Retry run` beside a right-aligned
  `parked <age> ago` label

#### Scenario: Retry dispatches the epic-level run
- **GIVEN** a stalled epic's open epic-detail modal
- **WHEN** the user activates the `Retry run` control
- **THEN** the detached epic-level autopilot launch is dispatched and the modal
  is dismissed

#### Scenario: A stall flip repaints the lane
- **GIVEN** a rendered board whose epic then flips between `needs-human` and
  `driving` roster states with an unchanged stage
- **WHEN** the diff-aware refresh compares lane signatures
- **THEN** the signatures differ and the affected lane repaints

### Requirement: Board throughput chart
id: board-throughput-chart

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

### Requirement: Graph config dialog
id: graph-config-dialog

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

### Requirement: Session activity timeline
id: session-activity-timeline

While the spec-detail modal is open for a member whose session transcript
resolves — the member's recorded session id when present, else the newest
transcript for the member's location while its live heartbeat state is
`driving` — the modal SHALL display, between its header and its artifact tabs,
an activity panel comprising, top to bottom: a **left-aligned progress line**
naming the member's **elapsed time since its build started** and its
**completed-task progress** as `<done>/<total>`; a width-adaptive 3-row
activity chart of that session's own output tokens per bucket (main and
subagent transcripts); and a detail line naming peak, newest value, window, and
session token total — all refreshed on a 3-second interval without the modal
being reopened. The elapsed token SHALL derive from the member's start
timestamp (`started_at`, resolved from its run-heartbeat roster entry, else its
build heartbeat) and SHALL be omitted when none resolves; the task-progress
token SHALL derive from the member's `tasks.md` checkbox counts and SHALL be
omitted when the member has no `tasks.md`. A one-row gap SHALL separate the
detail line from the artifact tab strip. If no transcript resolves, then the
modal SHALL render exactly as it does today, with no activity panel.

#### Scenario: A driving member shows a live chart
- **WHEN** the spec-detail modal opens for a member whose heartbeat entry
  carries a session id with a transcript on disk
- **THEN** the modal shows an activity panel of eighth-block cells with a
  detail line including the session token total

#### Scenario: The progress line shows elapsed and task progress
- **GIVEN** a driving member whose heartbeat carries a `started_at` and whose
  `tasks.md` has 4 of 11 checkboxes done
- **WHEN** its spec-detail modal opens
- **THEN** the activity panel's top progress line shows an elapsed time and the
  task progress `4/11`

#### Scenario: A missing start timestamp omits elapsed
- **GIVEN** a driving member whose heartbeat carries no `started_at`
- **WHEN** its spec-detail modal opens
- **THEN** the progress line omits the elapsed token, still showing task
  progress when a `tasks.md` is present

#### Scenario: A one-row gap precedes the artifact tabs
- **WHEN** the activity panel renders above the artifact tabs
- **THEN** a blank row separates the detail line from the tab strip

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

### Requirement: Worktree-aware modal artifacts
id: modal-worktree-artifacts

When the spec-detail modal resolves a member's artifact tabs, it SHALL locate
the change relative to the member's worktree-aware hosting directory (the
`location` the board aggregation derived), falling back to the invocation
root when no location is recorded — so a change planned or archived inside
its own worktree renders its Plan/Spec/Tasks tabs from the board of the main
checkout. If the located directory holds no change, then the modal SHALL show
the existing not-yet-planned notice.

#### Scenario: A worktree-planned member shows its artifacts
- **WHEN** the spec-detail modal opens for a member whose change lives only
  under `.worktrees/<slug>` (its `location`), with plan, spec, and tasks
  files present there
- **THEN** the modal renders the Plan/Spec/Tasks tabs from the worktree's
  artifact set instead of the not-yet-planned notice

#### Scenario: A root-planned member is unchanged
- **WHEN** the modal opens for a member whose change lives under the
  invocation root's own `planned/`
- **THEN** the tabs render exactly as before

#### Scenario: A missing location degrades to the notice
- **WHEN** the modal opens for a member whose recorded location no longer
  contains the change
- **THEN** the modal shows the not-yet-planned notice and raises no error

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

<<<<<<< HEAD

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
=======

### Requirement: Live modal artifacts
id: modal-live-artifacts

While the spec-detail modal shows the empty-artifacts notice for a member
whose live heartbeat entry carries a stage, the notice SHALL name the
in-flight stage and attempt (e.g. `plan in progress (plan#1) — spec files
appear once emitted`) instead of the idle "not yet planned" text; a member
with no live stage SHALL keep the existing idle notice. While the notice is
showing, the modal SHALL re-resolve the member's artifacts on its refresh
interval and, when artifacts appear, SHALL replace the notice with the tabbed
artifact view without the modal being closed and reopened.

#### Scenario: A driving member's notice names its stage
- **WHEN** the modal opens for a member with no artifacts whose heartbeat
  entry shows stage `plan`, attempt 1
- **THEN** the notice reads that a plan stage is in progress (`plan#1`)
  rather than "not yet planned"

#### Scenario: An idle member keeps the idle notice
- **WHEN** the modal opens for a member with no artifacts and no live stage
- **THEN** the notice is the existing "not yet planned — no spec files" text

#### Scenario: Artifacts appear without reopening
- **WHEN** the modal is open showing the notice and the member's artifact set
  is written to its location
- **THEN** a subsequent refresh tick replaces the notice with the
  Plan/Spec/Tasks tabs on the same open screen

#### Scenario: Mounted tabs are left alone
- **WHEN** the modal already shows artifact tabs
- **THEN** refresh ticks do not remount or reset them

### Requirement: Board modal chrome
id: board-modal-chrome

The board's three modals — the spec-detail, epic-detail, and epic-run
confirmation screens — SHALL each carry a one-row **accent title bar**: a band
in the theme's accent color spanning the modal's top, naming the modal's
subject (the member's slug, the epic's slug, or the epic run being confirmed)
in a contrasting foreground, with the compact `✕` close control inline at the
bar's right edge (unchanged in size and behavior). Below the title bar the
spec-detail modal SHALL show a **badge meta row** of theme-tinted chips — a
risk chip colored through the theme's risk variables **only when the member
carries a risk rating** (an unrated member's row renders no placeholder risk
chip), a lane chip colored through the member's lane variable, while the
member is being driven a live-stage chip in the muted tier, and the epic
reference — and the epic-detail modal SHALL show a status chip plus theme and
initiative chips when set. The epic-detail modal's member rows SHALL each
carry a **lane badge** colored through the theme variable of that member's
lane, derived by the same lane derivation the board's lanes use. The
spec-detail modal's artifact **tab strip** SHALL be themed through theme
variables — the active tab in the accent, inactive tabs in the muted tier,
and while the tab strip has focus the active tab SHALL render as a solid
accent block with dark bold text (the theme background tone), never the
light-on-accent block-cursor default —
and every modal SHALL carry a one-row muted **footer key-hint line** at its
bottom naming that modal's keys. While a detail modal is open, `y` SHALL copy
the modal's subject slug via the app clipboard, and `j`/`k` SHALL scroll the
modal's content pane down/up; in the spec-detail modal `Tab` SHALL activate
the next artifact tab, wrapping past the last. When `o` is pressed in a
detail modal, the app SHALL open that modal's artifact — the spec-detail
modal's active tab file, the epic-detail modal's `epics/<slug>/epic.md` — in
the user's editor as a **suspend launch** built by a pure builder returning
`{"mode": "suspend", "argv": [<editor>, <path>], "cwd": <the file's
directory>}`, with the editor resolved from `$EDITOR` and falling back to
`vi`. If the modal has no such artifact on disk, then `o` SHALL be a no-op.
All new modal chrome SHALL reference colors only through `$` theme variables
(see the Board theme requirement).

#### Scenario: Modals carry an accent title bar with inline close
- **GIVEN** the spec-detail, epic-detail, or epic-run confirmation modal
- **WHEN** the modal opens
- **THEN** its top row is an accent-background title bar naming the modal's
  subject, with the compact `✕` close control inline at the bar's right edge

#### Scenario: The spec-detail modal shows a badge meta row
- **GIVEN** a member with a risk rating being driven through a stage
- **WHEN** its spec-detail modal opens
- **THEN** a badge row below the title bar shows a risk chip colored by the
  member's risk, a lane chip colored by the member's lane, a muted live-stage
  chip, and the epic reference

#### Scenario: An unrated member's modal omits the risk chip
- **GIVEN** a member carrying no risk rating
- **WHEN** its spec-detail modal opens
- **THEN** the badge row renders no risk chip and no `?` placeholder — its
  first chip is the member's lane chip

#### Scenario: The epic-detail modal shows status, theme, and initiative chips
- **GIVEN** an epic with a theme and an initiative
- **WHEN** its epic-detail modal opens
- **THEN** a badge row below the title bar shows the epic's status chip and
  chips naming its theme and initiative

#### Scenario: Epic member rows carry lane badges
- **GIVEN** an open epic-detail modal listing the epic's member specs
- **WHEN** the member rows render
- **THEN** each row carries a badge colored through the theme variable of the
  lane the board's own lane derivation assigns that member

#### Scenario: The artifact tab strip is accent-themed
- **WHEN** the spec-detail modal's artifact tabs render
- **THEN** the active tab is styled with the accent and inactive tabs with the
  muted tier, with every color a `$` theme variable

#### Scenario: The focused active tab stays readable
- **GIVEN** an open spec-detail modal showing artifact tabs
- **WHEN** the tab strip gains focus
- **THEN** the active tab renders dark bold text on a solid accent
  background — not the light-on-accent block-cursor default

#### Scenario: Each modal shows its footer key hints
- **GIVEN** the spec-detail, epic-detail, or epic-run confirmation modal
- **WHEN** the modal opens
- **THEN** a one-row muted key-hint line at the modal's bottom names that
  modal's keys

#### Scenario: y copies the modal's subject slug
- **GIVEN** an open spec-detail modal (or epic-detail modal)
- **WHEN** `y` is pressed
- **THEN** the member's slug (or the epic's slug) is copied via the app
  clipboard

#### Scenario: Tab cycles the artifact tabs
- **GIVEN** an open spec-detail modal with more than one artifact tab
- **WHEN** `Tab` is pressed repeatedly
- **THEN** the active tab advances through the artifact tabs, wrapping from
  the last back to the first

#### Scenario: j and k scroll the modal content
- **GIVEN** an open detail modal whose content overflows its pane
- **WHEN** `j` then `k` is pressed
- **THEN** the content pane scrolls down then back up

#### Scenario: o opens the active artifact in the editor
- **GIVEN** an open spec-detail modal showing artifact tabs
- **WHEN** `o` is pressed
- **THEN** a suspend launch is spawned whose argv is the resolved editor
  followed by the active tab's file path

#### Scenario: o without an artifact is a no-op
- **GIVEN** an open spec-detail modal showing the not-yet-planned notice
- **WHEN** `o` is pressed
- **THEN** no launch is spawned and the modal stays open

#### Scenario: The editor launch builder is pure and falls back to vi
- **GIVEN** an environment where `$EDITOR` is unset
- **WHEN** the editor launch builder is called with an artifact path
- **THEN** it returns `{"mode": "suspend", "argv": ["vi", <path>], "cwd":
  <the file's directory>}` without spawning anything, and with `$EDITOR` set
  it uses that editor instead

### Requirement: Board control hierarchy
id: board-control-hierarchy

The `tui` board SHALL style its action controls in a two-tier hierarchy
expressed only through registered theme variables: **primary** action
controls (the stall banner's `Retry run`, the epic-run confirmation's `Yes`)
SHALL render a solid accent background with dark bold label text, and
**secondary** controls (the confirmation's `No`) SHALL render the
hover-background elevation with muted label text. The grouping segmented
control SHALL render its active mode as a solid accent block with dark bold
text and its inactive modes on the hover-background elevation with muted
text. Where a modal's accent title bar carries its inline `✕` close control,
the control SHALL render its dark glyph directly on the accent background
rather than as an accent-tinted chip.

#### Scenario: Confirm controls split into primary and secondary
- **WHEN** the epic-run confirmation modal renders
- **THEN** its `Yes` control resolves the solid accent background with dark
  bold label text and its `No` control resolves the hover background with
  muted text

#### Scenario: Active grouping mode is a solid accent block
- **WHEN** the segmented grouping control renders with a mode active
- **THEN** the active mode's button resolves the solid accent background with
  dark bold text while the inactive mode buttons resolve the hover background
  with muted text

#### Scenario: Title-bar close matches the accent bar
- **WHEN** a modal's accent title bar renders its inline `✕` close control
- **THEN** the control's background resolves to the accent color and its
  glyph color to the theme's dark background

### Requirement: Standalone changes on the board
id: board-standalone-changes

The board aggregation SHALL discover **standalone changes** — change
directories under the invocation root's `planned/` and under each
`.worktrees/<name>/`'s `planned/` whose plan header carries no `Epic:` line
and whose slug appears in no epic's stub table — recording each with its
worktree-aware state and hosting location, exposed as a top-level
`standalone` list on the board (empty when none), via a dependency-free
helper (no `textual`). Every lane SHALL render its standalone changes as
normal cards under a `standalone` group (in epic and initiative grouping
modes; flat in `none` mode) placed by the same state→lane mapping epic
members use; the `standalone` group header SHALL carry the per-lane count
but **no run and no open control**. Standalone cards SHALL open the standard
spec-detail modal, resolving artifacts from the change's hosting location.
Standalone content SHALL fold into the diff-aware lane signatures, so a
standalone change appearing, moving, or leaving repaints the affected lanes.
If a discovered directory is unreadable or malformed, then discovery SHALL
skip it rather than fail the board.

#### Scenario: A worktree-planned standalone change appears in its lane
- **GIVEN** a worktree `planned/` change with `Status: active` and no
  `Epic:` line, absent from every epic stub table
- **WHEN** the board renders in epic mode
- **THEN** the building lane shows the change as a card under a
  `standalone` group header carrying the count

#### Scenario: Epic members are not double-listed
- **GIVEN** a change whose slug appears in an epic's stub table and is
  planned in its worktree
- **WHEN** the board aggregates
- **THEN** the change appears only as that epic's member, not in the
  standalone list

#### Scenario: An Epic-tagged plan is not standalone
- **GIVEN** a worktree `planned/` change whose plan header carries an
  `Epic:` line
- **WHEN** the board aggregates
- **THEN** the standalone list does not include it

#### Scenario: The standalone group has no epic controls
- **WHEN** a `standalone` group header renders in any lane
- **THEN** it carries neither a run control nor an open control

#### Scenario: A standalone card opens the spec-detail modal
- **GIVEN** a rendered standalone card whose change lives in a worktree
- **WHEN** the card is selected
- **THEN** the spec-detail modal opens and resolves the change's artifacts
  from that worktree location

#### Scenario: Discovery is dependency-free and fault-tolerant
- **GIVEN** an environment without `textual` and a worktree holding a
  malformed plan file
- **WHEN** the discovery helper runs
- **THEN** it returns the readable standalone changes, skips the malformed
  one, and imports no `textual`

#### Scenario: A standalone change leaving repaints the lane
- **GIVEN** a rendered board showing a standalone change
- **WHEN** the change's worktree directory is removed and the board
  refreshes
- **THEN** the lane's signature differs and the card disappears

### Requirement: Board scrollbar theme
id: board-scrollbar-theme

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
>>>>>>> origin/main

### Requirement: Modal chrome containment
id: modal-chrome-containment

Every modal chrome element — badge chips, title text, and every button — of
the board's modal screens (spec-detail, epic-detail, epic-run confirmation,
and graph config) SHALL render fully inside its screen's container with a
nonzero region: badge chips SHALL size to their text (plus padding), never
stretching to the row width or pushing sibling chips outside the modal, so a
member with risk, lane, live stage, and epic renders all of its chips visibly.
The accent title bar and its inline ✕ close control SHALL render within the
container's content region — the title bar's right edge (and the ✕) SHALL NOT
extend past the right edge of the content rows below it, so the title bar never
overhangs the modal's border. While the accent title bar's ✕ close control is
focused, it SHALL keep the accent bar's color scheme (the dimmed-accent
treatment) rather than the theme's default focused-button styling. The test
suite SHALL carry a reusable chrome-containment sweep exercised against all four
modal screens — additionally asserting the title bar's and close control's right
edge do not exceed the container's content region — so a chrome element
rendering outside its container fails CI.

#### Scenario: All badge chips are visible and sized to content
- **WHEN** the spec-detail modal opens for a member with a risk, a derived
  lane, a live stage, and an epic
- **THEN** all four chips render inside the modal container, each sized to
  its text plus padding, none stretched to the row width

#### Scenario: The title bar does not overhang the border
- **WHEN** the spec-detail modal opens
- **THEN** the accent title bar's right edge, and its inline ✕ close control,
  sit within the container's content region — not extending past the right edge
  of the badge and tab rows below

#### Scenario: Epic modal chips are contained
- **WHEN** the epic-detail modal opens for an epic with members
- **THEN** its badge row chips and every member row's lane chip render
  inside the modal container

#### Scenario: The focused close control keeps the accent scheme
- **WHEN** a modal opens and its ✕ close control holds focus
- **THEN** the control's background is the dimmed accent, not the theme's
  default focused-button color

#### Scenario: The containment sweep guards all modal screens
- **WHEN** the chrome-containment sweep runs against the spec-detail,
  epic-detail, run-confirmation, and graph config screens
- **THEN** it asserts every button, badge chip, and title text region — and
  each screen's title bar and close-control right edge — sits inside the
  screen's container with nonzero width, and fails on any violation

### Requirement: Lane row presentation
id: lane-row-presentation

The board's lane rows SHALL present as follows: header controls (the run and
open controls) SHALL use a neutral surface background while idle, taking an
accent-tinted background only on hover and on focus; each group's panel band
SHALL extend unbroken to its divider, with no lane-background gap between
the group's last card and the divider; and every lane card (and the epic
modal's member rows) SHALL render its text on a single line, truncating an
overlong slug with an ellipsis — never wrapping onto a cropped second line
that leaves the slug invisible. The test suite SHALL carry a board-screen
chrome sweep, run at two terminal widths, asserting every group header's
buttons sit inside their lane's scrollable content region and every card's
painted line begins with its slug's visible prefix.

#### Scenario: Idle controls are neutral, hover and focus accent
- **WHEN** an epic group header renders without the pointer over its
  controls
- **THEN** the run/open controls carry the neutral surface background, and
  hovering or focusing a control gives it the accent-tinted background

#### Scenario: The group band reaches the divider
- **GIVEN** an epic group with cards in a lane
- **WHEN** the group renders
- **THEN** the panel background covers the full group box down to the
  divider, with no lane-background gap after the last card

#### Scenario: A long slug ellipsizes instead of blanking
- **GIVEN** a lane whose width leaves a card one cell narrower than its
  `✓ <slug>` text
- **WHEN** the card renders
- **THEN** its single painted line shows the slug's prefix with an ellipsis,
  not a bare glyph with the slug invisible

#### Scenario: The board sweep guards lane rows at multiple widths
- **WHEN** the board-screen chrome sweep runs at two different terminal
  widths
- **THEN** it asserts header buttons are inside their lane's scrollable
  content region and card lines begin with their slug prefix, failing on
  any violation

### Requirement: Stable lane scrollbar gutter
id: lane-scrollbar-gutter

Every lifecycle lane SHALL reserve its vertical scrollbar's column
permanently (a stable scrollbar gutter), so the lane's content width is
identical whether or not the lane currently scrolls, no lane content is ever
laid out or painted in the scrollbar's column, and the appearance or
disappearance of the scrollbar never reflows the lane's rows. The
board-screen sweep SHALL assert that a scrolling lane's group-header buttons
are disjoint from the scrollbar's region and that content width is unchanged
by growth that makes the scrollbar appear.

#### Scenario: Content width is scroll-state independent
- **GIVEN** a board whose shipped lane does not scroll
- **WHEN** the board grows via refresh until the shipped lane's scrollbar
  appears
- **THEN** the lane's scrollable content width is the same before and after

#### Scenario: Buttons never share the scrollbar's column
- **GIVEN** a lane whose vertical scrollbar is displayed
- **WHEN** its group headers render
- **THEN** every header button's region is disjoint from the scrollbar's
  region

#### Scenario: The gutter is reserved while not scrolling
- **GIVEN** a lane with too little content to scroll
- **WHEN** it renders
- **THEN** the scrollbar column is still reserved, and the lane's content
  width equals that of a scrolling lane of the same outer width

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
supplies one), the current stage when set, and the outcome on finish. On
`build-start` the verb SHALL additionally stamp a `started_at` epoch timestamp
when the file does not already carry one, left unchanged by later verbs and by a
repeated `build-start`, so elapsed time is measured from the build's first
start. If a write fails, then the verb SHALL warn on stderr and exit zero — a
heartbeat failure never blocks a build. Because a build runs in its change's
worktree, the board aggregation SHALL discover build heartbeats under both the
invocation root's content directory and every `.worktrees/<name>/` content
directory's `autopilot/`, the newest `updated_at` winning a slug contested
between roots.

#### Scenario: build-start records a running heartbeat
- **WHEN** `build-start <slug>` runs with `CLAUDE_CODE_SESSION_ID` set
- **THEN** the heartbeat file parses as JSON with state `running`,
  `kind: build`, that session id, and the invoking directory as `location`

#### Scenario: build-start stamps a start timestamp once
- **WHEN** `build-start <slug>` runs and the heartbeat file does not yet exist
- **THEN** the file carries a `started_at` epoch timestamp, and a later
  `build-stage` or repeated `build-start` leaves that `started_at` unchanged

#### Scenario: Stage transitions bump the sequence
- **WHEN** `build-stage <slug> --stage implement` runs after `build-start`
- **THEN** the file records stage `implement` with a `seq` greater than the
  start write's

#### Scenario: Finish marks the build finished
- **WHEN** `build-finish <slug> --outcome shipped` runs
- **THEN** the file records state `finished` and outcome `shipped`

### Requirement: Board dead-run detection
id: board-dead-run-detection

The dashboard's board derivation SHALL judge whether an autopilot run is still
live through a dependency-free liveness probe (no `textual`, unit-testable
without the TUI): while the heartbeat's recorded `host` matches the reader's host
and it carries a `pid`, the writer is alive iff probing that pid reports the
process still exists (`os.kill(pid, 0)` not raising `ProcessLookupError`; a
permission error counts as alive); otherwise the run is live only while its
`updated_at` is within `AUTOPILOT_FRESH_SECONDS` (3600 seconds) of now. When a
run whose heartbeat state is `running` is judged dead by this probe, a member
whose roster entry is `driving` SHALL render in the `building` lane as a **stale**
card carrying its death age (via the shared age formatter), not as an actively
driving card. A run judged live SHALL keep placing its `driving` members as
actively driving.

#### Scenario: A dead writer's driving card reads stale
- **GIVEN** a heartbeat with `state:"running"` and a `driving` roster member,
  whose recorded `host` is the reader's host and whose recorded `pid` is not a
  live process
- **WHEN** the board lane placement runs
- **THEN** that member's card is placed in the `building` lane marked stale with
  its death age, not as an actively driving card

#### Scenario: A live writer's driving card stays active
- **GIVEN** a heartbeat with a `driving` roster member whose recorded `host` is
  the reader's host and whose recorded `pid` is a live process
- **WHEN** the board lane placement runs
- **THEN** that member renders as actively driving (in `building`, or `review`
  while its review stage runs)

#### Scenario: A cross-host run falls back to the time-window
- **GIVEN** a heartbeat whose recorded `host` differs from the reader's host
- **WHEN** the board judges the run's liveness
- **THEN** liveness is decided by `updated_at` within 3600 seconds of now — dead
  once older — rather than by probing the foreign pid

### Requirement: Board parked-member signal
id: board-parked-member-signal

The board SHALL surface a **parked** member — one the delivery pipeline could
not carry forward — with an at-a-glance signal on its lane card and, in its
spec-detail modal, an obvious rendering of the validation output that parked it,
so a parked member is never mistaken for an idle or an actively-driving one. The
signal SHALL be derived by a **pure, dependency-free predicate** over the
member's worktree-derived board state and its heartbeat roster entry (no
`textual`, no I/O), unit-testable without the TUI.

A member is parked when its roster entry was marked **stale** by dead-run
detection, or when its roster entry state (or, absent an entry, its
worktree-derived board state) is `rejected` or `needs-human`. For each parked
kind the predicate SHALL yield a distinct **error-tier glyph** and a short
**state label**: a stale card yields `†` with `stale (<death age>)` reusing the
death age dead-run detection already writes onto the entry; a `rejected` member
yields `⚠` with `rejected`; a `needs-human` member yields `⛔` with
`needs-human`. It SHALL also carry the entry's `reason` when present. A member
progressing normally — driving, ready, unplanned, or shipped — SHALL yield no
signal.

On the **lane card**, a parked member SHALL render its signal glyph in the
theme's error color in place of the risk glyph, followed by the slug and the
state label in the muted tier. The shipped `✓` card and the actively-driving
`● slug · <stage>` card SHALL be unchanged, and the parked signal SHALL fold
into the diff-aware refresh so a member entering or leaving a parked state
repaints its lane.

In the **spec-detail modal** badge meta row, a parked member SHALL render an
error-tier **state chip** carrying the state label in place of the muted
live-stage chip; the live-stage chip SHALL appear only while the member is being
driven, never for a parked member whose stage is a stale leftover. When the
parked member's roster entry carries a `reason`, the modal SHALL present it as a
**tinted callout above the artifact tabs**: the theme's error color at 10% alpha
for the background, a solid error-colored one-cell bar along the callout's full
left edge, and the reason text in the theme's warning tier — the member-level
analogue of the epic stall banner — so the validation output is obvious without
opening the Plan tab. A parked member with no recorded reason SHALL render the
state chip but no callout, and a non-parked member's modal SHALL render neither
the state chip nor the callout. All new chrome SHALL reference colors only
through `$` theme variables.

#### Scenario: A rejected member's card carries the warning glyph and state label
- **GIVEN** a member whose worktree-derived board state is `rejected`
- **WHEN** its lane card text renders
- **THEN** the text is the error-tier `⚠` glyph, the slug, and `· rejected` in
  the muted tier — not the risk glyph

#### Scenario: A needs-human member's card carries the stop glyph
- **GIVEN** a member whose roster entry state is `needs-human`
- **WHEN** its lane card text renders
- **THEN** the text is the error-tier `⛔` glyph, the slug, and `· needs-human`
  in the muted tier

#### Scenario: A stale dead-run card carries the dagger glyph and death age
- **GIVEN** a driving member marked stale by dead-run detection, its entry
  carrying the `died <age>` death age
- **WHEN** its lane card text renders
- **THEN** the text is the error-tier `†` glyph, the slug, and
  `· stale (died <age>)` — not an actively-driving `● slug · <stage>` card

#### Scenario: A normal card is unchanged
- **GIVEN** a ready member (or a driving member, or a shipped member)
- **WHEN** its lane card text renders
- **THEN** it renders the existing risk glyph (or the driving stage suffix, or
  the shipped `✓`) with no parked-signal glyph or state label

#### Scenario: The parked-signal predicate is pure and dependency-free
- **GIVEN** a member dict and a roster entry, evaluated with `textual` not
  importable
- **WHEN** the parked-signal predicate is called
- **THEN** it returns the kind, glyph, label, and reason for a parked member and
  `None` for a normally-progressing one, raising no error

#### Scenario: A parked member's modal shows a state chip, not a stale stage chip
- **GIVEN** a `rejected` member whose roster entry still carries a leftover
  `stage: gate`
- **WHEN** its spec-detail modal opens
- **THEN** the badge row shows an error-tier `rejected` state chip and renders
  no `stage:` chip

#### Scenario: A parked member's modal surfaces the reason in the tinted callout
- **GIVEN** a `rejected` member whose roster entry carries a `reason`
- **WHEN** its spec-detail modal opens
- **THEN** a callout above the artifact tabs renders the reason text on the
  theme's error color at 10% alpha with a solid error-colored one-cell bar on
  its left edge

#### Scenario: A driving member's modal keeps its live-stage chip
- **GIVEN** a member being driven at stage `build`
- **WHEN** its spec-detail modal opens
- **THEN** the badge row shows the muted `stage: build` chip and renders no
  state chip and no reason callout

#### Scenario: A parked member with no reason shows the chip but no callout
- **GIVEN** a `needs-human` member whose roster entry carries no `reason`
- **WHEN** its spec-detail modal opens
- **THEN** the badge row shows the error-tier `needs-human` state chip and no
  reason callout is mounted

#### Scenario: A parked flip repaints the lane
- **GIVEN** a rendered board whose member flips from `driving` to `rejected`
- **WHEN** the diff-aware refresh compares lane signatures
- **THEN** the signatures differ and the affected lane repaints

### Requirement: Board live-build lane
id: board-live-build-lane

While a member's attached interactive build heartbeat is live — state
`running` with a liveness stamp (the newer of its `updated_at` and the
aggregation-stamped transcript mtime) within the 600-second build-freshness
window — the board's lane resolution SHALL place the member's card in the
`review` lane while the heartbeat's stage is `review`, and in the `building`
lane at any other stage, overriding the member's lifecycle-state mapping (so
an already-archived member whose interactive build is mid-review renders in
`review`, not `shipped`). A live autopilot roster entry in state `driving`
SHALL keep precedence over the build heartbeat, so autopilot-driven placement
is unchanged. If the build heartbeat is not live — state `finished`, or its
liveness stamp aged past the window — then lane resolution SHALL fall back to
the existing state mapping unchanged, with no stale treatment (the dagger
signal remains autopilot-roster-only). While a card is placed by a live build
heartbeat, its row SHALL append the heartbeat's stage in the muted tier after
the slug, the same rendering as a roster-driven member, and the member's
spec-detail modal SHALL show the muted `stage:` chip derived from that
heartbeat whenever no roster stage chip or parked signal applies.

#### Scenario: An archived member mid-review renders in the review lane
- **GIVEN** a member whose board state is `archived` with an attached build
  heartbeat of state `running`, stage `review`, and a fresh `updated_at`
- **WHEN** the lane contents are derived
- **THEN** the member's card is in the `review` lane and the `shipped` lane
  does not carry it

#### Scenario: A non-review build stage renders in building
- **GIVEN** a member with a live build heartbeat at stage `implement`
- **WHEN** the lane contents are derived
- **THEN** the member's card is in the `building` lane

#### Scenario: A stale build heartbeat falls back to the state mapping
- **GIVEN** an `archived` member whose build heartbeat records state `running`
  at stage `review` but a liveness stamp older than the freshness window
- **WHEN** the lane contents are derived
- **THEN** the member's card is in the `shipped` lane

#### Scenario: A driving roster entry keeps precedence
- **GIVEN** a member whose live autopilot roster entry is `driving` at stage
  `build` and whose build heartbeat is live at stage `review`
- **WHEN** the lane contents are derived
- **THEN** the member's card is in the `building` lane, per the roster entry

#### Scenario: The card row appends the live build stage
- **GIVEN** a member card placed by a live build heartbeat at stage `review`
- **WHEN** the card's row text renders
- **THEN** the stage is appended in the muted tier after the slug

#### Scenario: The modal shows the build-stage chip
- **GIVEN** the spec-detail modal of a member with a live build heartbeat at
  stage `review` and no roster stage or parked signal
- **WHEN** the modal's badge row composes
- **THEN** it carries the muted `stage: review` chip and its lane badge reads
  `review`

### Requirement: Board brand mark
id: board-brand-mark

The `tui` board's header-bar brand block SHALL open with the ☕ coffee-cup brand mark directly before the accent-styled `shipd` label, keeping the muted `delivery board` label beside it and every other header-bar zone unchanged.

#### Scenario: Header brand block carries the mark
- **WHEN** the `tui` app mounts its header bar
- **THEN** the brand block's content begins with `☕` followed by the accent-styled `shipd`
