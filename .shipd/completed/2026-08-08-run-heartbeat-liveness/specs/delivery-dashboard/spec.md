## MODIFIED Requirements

### Requirement: Autopilot run heartbeat
id: autopilot-heartbeat
base: 0bd63992e7db

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

## ADDED Requirements

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
