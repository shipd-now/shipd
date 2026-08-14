## ADDED Requirements

### Requirement: Autopilot run heartbeat
id: autopilot-heartbeat

While an autopilot run executes (not `--dry-run`), the autopilot SHALL
maintain `<content-dir>/autopilot/<epic>-heartbeat.json`, atomically
replaced (temp file + rename) at every transition — run start, member
start, stage attempt start, member outcome, run end — carrying the epic,
the run state (`running`/`finished`), the pipeline provenance, a
monotonically increasing `seq`, an epoch `updated_at`, and a per-member
roster with each member's slug, risk, and live state (`pending`,
`driving` with current stage and attempt, `shipped`, `rejected`,
`needs-human` — with reason and session id when present, and `skipped`
with the skipped state). If a heartbeat write fails, then the run SHALL
continue unaffected, warning once and disabling further writes. The
`<content-dir>/autopilot/` directory SHALL be git-ignored as runtime
state.

#### Scenario: Stage transitions are visible mid-run
- **WHEN** the autopilot starts the build stage's first attempt for a
  member
- **THEN** the heartbeat file parses as JSON and shows that member as
  `driving` at stage `build`, attempt 1, with a `seq` greater than the
  run-start write

#### Scenario: Parked member carries its recovery context
- **WHEN** a member is parked as needs-human during a run
- **THEN** the heartbeat's roster entry for it records the outcome, the
  failing stage, the reason, and the session id

#### Scenario: Dry runs write nothing
- **WHEN** the autopilot runs with `--dry-run`
- **THEN** no heartbeat file is created

#### Scenario: A failing write never fails the run
- **GIVEN** a heartbeat destination that cannot be written
- **WHEN** the autopilot drives a member
- **THEN** the run completes normally with a single warning and no raised
  error

### Requirement: Board aggregation
id: board-aggregation

The dashboard CLI SHALL provide a `board` verb that aggregates, for each
epic under the resolved content directory (or only the epic named by
`--epic`): the epic's status, theme, and initiative context — the
initiative's status resolved through the workspace brief when a workspace
is discoverable, the bare slug otherwise, never an error; every stub
member's worktree-aware state — derived from the invocation root first
and, when the root says `unplanned`, from a locate-style probe of
`.worktrees/<slug>` (planned change or completed archive), reporting the
state and where it lives; and the run context merged from the live
heartbeat and the latest run report when either exists. The verb SHALL
print an aligned human-readable board by default and the full board
object as JSON under `--json`.

#### Scenario: A worktree-parked member is visible
- **GIVEN** a member whose plan sits at `rejected` inside
  `.worktrees/<slug>` while the root's `planned/` lacks it
- **WHEN** the board is built
- **THEN** the member's row reports `rejected` and its worktree location
  instead of `unplanned`

#### Scenario: Missing workspace degrades initiative context
- **GIVEN** an epic carrying `Initiative:` in a repo with no discoverable
  workspace
- **WHEN** the board is built
- **THEN** the initiative slug is shown without a status and the verb
  exits zero

#### Scenario: Live heartbeat is merged
- **GIVEN** a heartbeat file recording a run driving a member's gate stage
- **WHEN** the board is built for that epic
- **THEN** the board shows the run as running with that member and stage

#### Scenario: JSON mode is machine-readable
- **WHEN** `board --json` runs
- **THEN** stdout parses as a single JSON object listing the epics and
  their members

### Requirement: Board TUI
id: board-tui

The dashboard CLI SHALL provide a `tui` verb rendering the board
full-screen with `curses`, re-aggregating and redrawing every
`--interval` seconds (default 2) and quitting on `q`. Line rendering
SHALL be a pure function shared with the `board` verb's text mode, so it
is testable without a terminal, and `curses` SHALL be imported lazily
inside the verb so importing the dashboard module requires no terminal
or curses support.

#### Scenario: Rendering is pure and shared
- **WHEN** the shared line renderer runs on a board with a driving member
- **THEN** it returns text lines naming the epic, the member, and its
  current stage, with no terminal interaction

#### Scenario: Module import needs no curses
- **WHEN** the dashboard module is imported
- **THEN** no `curses` import occurs until the `tui` verb runs

### Requirement: Board HTML page
id: board-html

The dashboard CLI SHALL provide an `html` verb writing the board as a
single self-contained page to `--out`: inline CSS only, every dynamic
value HTML-escaped, and a `<meta http-equiv="refresh">` tag set to the
`--interval` seconds (default 2) so the browser re-reads the file. By
default the verb SHALL rewrite the page atomically every interval until
interrupted; with `--once` it SHALL write a single snapshot and exit
zero.

#### Scenario: Page self-refreshes with board content
- **WHEN** the HTML renderer runs on a board with members
- **THEN** the page contains the meta refresh tag with the interval and a
  row per member with its state

#### Scenario: Snapshot mode writes once and exits
- **WHEN** `html --out <path> --once` runs
- **THEN** the file is written exactly once and the verb exits zero
