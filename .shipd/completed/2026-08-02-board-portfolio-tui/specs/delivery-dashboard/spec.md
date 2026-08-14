## MODIFIED Requirements

### Requirement: Board TUI
id: board-tui
base: ac1c69677f6f

The dashboard CLI SHALL provide a `tui` verb rendering the board full-screen with
`curses` as an interactive portfolio board: a collapsible left hierarchy panel
grouping changes under their initiative → epic (the epic's `Theme` shown as a
colour-coded label, never a grouping level) beside a right kanban whose columns
are the lifecycle states (`unplanned`, `ready`, `building`, `review`, `shipped`)
holding colour-coded, risk-chipped member cards. The verb SHALL support keyboard
control (arrow-key navigation, Enter to act or expand, a key to toggle the
hierarchy panel, `q` to quit) and mouse control (clickable regions for the
`[<]`/`[>]` panel toggle, tree rows, and card action buttons), re-aggregating and
redrawing every `--interval` seconds (default 2). The board layout — its
positioned lines and its clickable regions — SHALL be computed by a pure function
testable without a terminal; `curses` SHALL be imported lazily inside the verb so
importing the dashboard module needs no terminal. Where the terminal reports no
mouse events, the board SHALL run keyboard-only rather than fail.

#### Scenario: Layout is pure and carries clickable regions
- **WHEN** the pure layout function runs on a board with a driving member and a
  ready member
- **THEN** it returns positioned lines and a set of clickable regions — the panel
  toggle, tree rows, and card buttons — with no terminal interaction

#### Scenario: Driving member is placed in the building column
- **WHEN** the layout runs on an epic whose member is driving the build stage
- **THEN** that member's card is placed in the `building` column carrying its
  stage and risk chip

#### Scenario: Collapsing the panel flips the toggle and reclaims width
- **WHEN** the panel-toggle region is activated while the hierarchy panel is open
- **THEN** the layout collapses the panel, flips the toggle icon to `[>]`, and
  the kanban reclaims the freed width

#### Scenario: Module import needs no curses
- **WHEN** the dashboard module is imported
- **THEN** no `curses` import occurs until the `tui` verb runs

### Requirement: Board aggregation
id: board-aggregation
base: 5a450aa322fa

The dashboard CLI SHALL provide a `board` verb that aggregates, for each epic
under the resolved content directory (or only the epic named by `--epic`): the
epic's status, theme, and initiative context — the initiative's status resolved
through the workspace brief when a workspace is discoverable, the bare slug
otherwise, never an error; every stub member's worktree-aware state — derived
from the invocation root first and, when the root says `unplanned`, from a
locate-style probe of `.worktrees/<slug>` (planned change or completed archive),
reporting the state and where it lives; and the run context merged from the live
heartbeat and the latest run report when either exists. The aggregation SHALL
additionally group its epics under their initiative — a workspace-wide group for
epics carrying no `Initiative:` — and SHALL annotate each member with the board
actions eligible for it (`plan` for an `unplanned` member, `run` for a member
ready to drive, `open` for a parked or shipped member carrying a session id) and
that member's resumable `session_id` when known. The verb SHALL print an aligned
human-readable board by default and the full board object as JSON under `--json`.

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

### Requirement: Autopilot run heartbeat
id: autopilot-heartbeat
base: 833e38be461d

While an autopilot run executes (not `--dry-run`), the autopilot SHALL maintain
`<content-dir>/autopilot/<epic>-heartbeat.json`, atomically replaced (temp file +
rename) at every transition — run start, member start, stage attempt start,
member outcome, run end — carrying the epic, the run state
(`running`/`finished`), the pipeline provenance, a monotonically increasing
`seq`, an epoch `updated_at`, and a per-member roster with each member's slug,
risk, and live state (`pending`, `driving` with current stage and attempt,
`shipped`, `rejected`, `needs-human` — with reason and session id when present,
and `skipped` with the skipped state). The autopilot SHALL record a member's
`session_id` in its roster entry as soon as a driven turn first yields one — not
only at the member's terminal outcome — so the entry carries a resume handle
while the member is still being driven. If a heartbeat write fails, then the run
SHALL continue unaffected, warning once and disabling further writes. The
`<content-dir>/autopilot/` directory SHALL be git-ignored as runtime state.

#### Scenario: Session id is recorded mid-drive
- **WHEN** a driven member's first turn yields a session id, before the member
  reaches any terminal outcome
- **THEN** the heartbeat's roster entry for that member carries the `session_id`
  while its state is still `driving`

#### Scenario: Stage transitions are visible mid-run
- **WHEN** the autopilot starts the build stage's first attempt for a member
- **THEN** the heartbeat file parses as JSON and shows that member as `driving`
  at stage `build`, attempt 1, with a `seq` greater than the run-start write

#### Scenario: Dry runs write nothing
- **WHEN** the autopilot runs with `--dry-run`
- **THEN** no heartbeat file is created

#### Scenario: A failing write never fails the run
- **GIVEN** a heartbeat destination that cannot be written
- **WHEN** the autopilot drives a member
- **THEN** the run completes normally with a single warning and no raised error

## ADDED Requirements

### Requirement: Board actions
id: board-actions

The interactive `tui` board SHALL offer per-card actions that act on the member
under the selection or click, plus an epic-level run:

- `plan` on an `unplanned` member SHALL launch an interactive `/s:plan <member>`
  session in the member's worktree.
- `run` SHALL launch a detached driver that writes the heartbeat the board tails
  — a single named-member drive for a card, or the full autopilot for the
  epic-level run — so the board keeps rendering and never blocks on the run.
- `open` on a parked or shipped member carrying a session id SHALL resume that
  exact session via `claude --resume <id>`; `open` SHALL be disabled while a
  member is mid-drive.

Interactive actions (`plan`, `open`) SHALL open in a new tmux window when `$TMUX`
is set, and otherwise SHALL suspend the board (leaving curses), run, and restore
the board on exit. The argument vector each action spawns SHALL be produced by a
pure function so it is testable without spawning a process.

#### Scenario: Plan launches interactively under tmux
- **GIVEN** `$TMUX` is set
- **WHEN** the `plan` action fires on an unplanned member
- **THEN** the built launch is a `tmux new-window` running `/s:plan` for that
  member in its worktree, and the board is not suspended

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
