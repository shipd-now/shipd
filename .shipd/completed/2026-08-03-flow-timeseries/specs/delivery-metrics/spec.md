## ADDED Requirements

### Requirement: Flow time-series capture
id: flow-timeseries

The delivery-metrics layer SHALL record the board's per-lifecycle-state
membership as an **append-only time series** in `flow.jsonl` beside the build
log, via a stdlib-only capture API on `metrics.py` (`flow_snapshot` /
`record_flow`) that is separate from `derive` — which remains write-free. Each
record SHALL be one JSON line `{ts, root, states}` where `ts` is an ISO-8601
UTC timestamp, `root` is the absolute **main-checkout** path (a linked
worktree resolves to its main checkout via its `.git`-file `gitdir:` line),
and `states` maps every lifecycle state — **including** `unplanned` and
`archived` — to the sorted slugs of the epic stub members in that state
(deduplicated across epics, attributed to no individual). If the same root's
latest record already carries an equal `states` map, then `record_flow` SHALL
skip the append. When a lifecycle mutation completes — a plan status write
(`spec_status.write_status`, covering `set-status`, `sync`, and the gate's
promote/reject), a change install (`spec_emit.py change`), or an archive
(`spec_merge.archive_change`) — the system SHALL append a snapshot
best-effort; if capture fails for any reason, then the mutation SHALL still
succeed. The log directory SHALL resolve as: the `AM_FLOW_LOG_DIR` environment
variable when set (its value the directory; the empty string disabling
recording entirely), else an explicit `config` dict's `log_dir`, else the
layered configuration's `build.log_dir`, else `~/.shipd/builds`. The layer SHALL
also provide a reader, `collect_flow(root, config=None)`, returning the
root-filtered records sorted by `ts` (each with a derived `by_state` count
map, malformed lines skipped, missing file → empty list); `derive` SHALL carry
a `flow` block `{series: [{ts, by_state}], n}` from it; and a `record-flow`
verb (`metrics.py record-flow [--root <root>]`) SHALL append a snapshot and
print the appended record as JSON, or `unchanged` when deduped, exiting `0`.

#### Scenario: A status write appends a full-band snapshot
- **GIVEN** a fixture root whose epic holds members in `unplanned`, `draft`,
  and `archived` states, with `AM_FLOW_LOG_DIR` pointing at a temp dir
- **WHEN** a member's plan status is written via the status CLI
- **THEN** `flow.jsonl` gains a record whose `root` is the fixture root and
  whose `states` lists the members under all three states, `unplanned` and
  `archived` included

#### Scenario: An unchanged snapshot is not appended twice
- **GIVEN** a root already recorded in `flow.jsonl`
- **WHEN** `record_flow` runs again with no lifecycle change
- **THEN** the file gains no new record and the verb prints `unchanged`

#### Scenario: A worktree root records under the main checkout
- **GIVEN** a linked git worktree of a fixture project (its `.git` a file whose
  `gitdir:` points into the main checkout's `.git/worktrees/`)
- **WHEN** `record_flow` runs with the worktree as `root`
- **THEN** the appended record's `root` is the main checkout's absolute path

#### Scenario: Capture failure never fails the mutation
- **GIVEN** an unwritable flow log destination
- **WHEN** a status write, change install, or archive runs
- **THEN** the mutation itself succeeds exactly as before and no traceback
  escapes the hook

#### Scenario: The reader filters by root and derive exposes the series
- **GIVEN** a `flow.jsonl` holding records for two different roots plus one
  malformed line
- **WHEN** `derive` runs against one root with the matching config
- **THEN** its `flow.series` carries only that root's records, sorted by `ts`,
  each as `{ts, by_state}` counts; the malformed line is skipped; and `derive`
  still writes no file

#### Scenario: The empty env seam disables recording
- **GIVEN** `AM_FLOW_LOG_DIR` set to the empty string
- **WHEN** a hooked lifecycle mutation runs
- **THEN** no flow record is written anywhere and the mutation succeeds

## MODIFIED Requirements

### Requirement: Metrics derivation engine
id: metrics-engine
base: 851ecc6c724f

The delivery-metrics layer SHALL provide a **stdlib-only derivation engine**
(`metrics.py` beside the other engine scripts — no third-party imports, no
`textual`) that computes delivery metrics **purely from the event sources the
pipeline already emits**; the derivation API writes nothing and prints nothing
— its single entry point (`derive`) returns one JSON-serializable dict — and
the module's user-facing surface is limited to the thin CLI verbs defined by
the `metrics-cli` and `flow-timeseries` requirements (`summary`,
`record-flow`), which importing the module never executes; the flow-capture
API defined by the `flow-timeseries` requirement is the module's one writing
surface, and `derive` never invokes it. It SHALL read: per-change **ship
events** from the config-resolved build log (`log_dir`, default
`~/.shipd/builds/builds.jsonl`), unioned with the dated `completed/<date>-<slug>/`
archives as a ship-date fallback for changes the log missed (the log entry
wins on both); **outcome events** from the `.shipd/autopilot/<epic>-report.json`
run reports (shipped / rejected / needs-human / skipped); a live **WIP
snapshot** from the epic tables and heartbeats via the stdlib spec helpers
(never by importing the dashboard module); and merge/first-commit
**timestamps from git** (stdlib subprocess), where a change's merge commit is
resolved by its `<slug>:`-prefixed squash subject on the base branch and lead
time is computed only over changes where both timestamps resolve. From these
it SHALL derive, per the cited canon: **throughput** (completed-count per
period), **deployment-days** per week with the DORA frequency band (`daily` at
a median ≥ 3 deployment-days/week, `weekly`, `monthly`, else `yearly`); **lead
time** (merge − first-commit) and **cycle time** (v1: the per-change build
elapsed recorded in the log) each reported as **median plus 50/85/95
percentiles with the sample count — never a bare mean**; **WIP** by lifecycle
state with per-item age (age omitted, never guessed, when no evidence exists);
the **outcome distribution** as the pre-merge rework proxy (the true
change-failure input remains a seam for `change-failure-signal`); **cost**
(token-output and wall-clock totals and per-change medians); and the recorded
**flow series** as a read-only `flow` block (per the `flow-timeseries`
requirement). All functions SHALL be **pure and deterministic** — `root`,
`config`, and `now` are injectable, timestamps are UTC, malformed log lines
are skipped rather than fatal — and no metric SHALL ever be attributed to an
individual.

#### Scenario: Ship events come from the log with completed-archive fallback
- **GIVEN** a fixture root whose build log records change `a` and whose
  `completed/` holds dated archives for changes `a` and `b`
- **WHEN** ship events are collected
- **THEN** both changes are present exactly once, `a` carrying the log's
  timestamp and cost fields and `b` carrying the archive-date fallback

#### Scenario: Cycle and lead time report percentiles, never a bare mean
- **GIVEN** ship events with an outlier build duration
- **WHEN** metrics are derived
- **THEN** cycle time (and lead time, over changes with resolved git
  timestamps) reports median, p50, p85, p95, and the sample count, with no mean
  field in the result

#### Scenario: Deployment-days map to the DORA band
- **GIVEN** ship events whose weekly deployment-day median is at least 3
- **WHEN** metrics are derived
- **THEN** the deployment-frequency band is `daily`, and lowering the fixture's
  cadence lowers the band accordingly

#### Scenario: WIP snapshot counts in-flight members by state
- **GIVEN** a fixture root whose epics hold members in `unplanned`, `ready`, and
  `shipped` states
- **WHEN** the WIP snapshot is collected
- **THEN** only the in-flight members are counted, grouped by lifecycle state,
  and a member with no age evidence carries no fabricated age

#### Scenario: Outcome distribution folds the autopilot reports
- **GIVEN** autopilot run reports containing shipped, rejected, and needs-human
  members
- **WHEN** outcomes are collected
- **THEN** the distribution counts each category across all reports and exposes
  the per-member lists

#### Scenario: Lead time skips changes whose git timestamps do not resolve
- **GIVEN** a change with no matching `<slug>:` merge commit on the base branch
- **WHEN** metrics are derived
- **THEN** that change is excluded from the lead-time sample (its count reflects
  only resolved changes) and derivation does not fail

#### Scenario: The engine is dependency-free and side-effect-free
- **GIVEN** an environment without `textual`
- **WHEN** the metrics module is imported and `derive` runs on a fixture root
- **THEN** it succeeds, returns a JSON-serializable dict, and writes no file —
  and a malformed line in the build log is skipped rather than raising
