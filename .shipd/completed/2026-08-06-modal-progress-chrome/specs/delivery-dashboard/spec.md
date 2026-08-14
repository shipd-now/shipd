## MODIFIED Requirements

### Requirement: Session activity timeline
id: session-activity-timeline
base: 7253387223f4

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

### Requirement: Modal chrome containment
id: modal-chrome-containment
base: 8545d5249250

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

### Requirement: Autopilot run heartbeat
id: autopilot-heartbeat
base: f53d3358e2d6

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
while the member is still being driven. The autopilot SHALL record a member's
`started_at` (epoch seconds) in its roster entry when the member first starts
being driven, set once and left unchanged on subsequent stage re-attempts, so
the spec-detail modal can show elapsed time since the build began. If a
heartbeat write fails, then the run SHALL continue unaffected, warning once and
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

#### Scenario: Dry runs write nothing
- **WHEN** the autopilot runs with `--dry-run`
- **THEN** no heartbeat file is created

#### Scenario: A failing write never fails the run
- **GIVEN** a heartbeat destination that cannot be written
- **WHEN** the autopilot drives a member
- **THEN** the run completes normally with a single warning and no raised error

### Requirement: Interactive build heartbeat
id: build-heartbeat-cli
base: 121aa8bdc5fe

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
