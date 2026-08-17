## MODIFIED Requirements

### Requirement: Flow time-series capture
id: flow-timeseries
base: 51c6bb34a57f

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
succeed. The log directory SHALL resolve as: the `SHIPD_FLOW_LOG_DIR`
environment variable when set, else the legacy `AM_FLOW_LOG_DIR` environment
variable when set (in either case the value the directory; the winning
variable's empty string disabling recording entirely), else an explicit
`config` dict's `log_dir`, else the layered configuration's `build.log_dir`,
else `~/.shipd/builds`. The layer SHALL
also provide a reader, `collect_flow(root, config=None)`, returning the
root-filtered records sorted by `ts` (each with a derived `by_state` count
map, malformed lines skipped, missing file → empty list); `derive` SHALL carry
a `flow` block `{series: [{ts, by_state}], n}` from it; and a `record-flow`
verb (`metrics.py record-flow [--root <root>]`) SHALL append a snapshot and
print the appended record as JSON, or `unchanged` when deduped, exiting `0`.

#### Scenario: A status write appends a full-band snapshot
- **GIVEN** a fixture root whose epic holds members in `unplanned`, `draft`,
  and `archived` states, with `SHIPD_FLOW_LOG_DIR` pointing at a temp dir
- **WHEN** a member's plan status is written via the status CLI
- **THEN** `flow.jsonl` gains a record whose `root` is the fixture root and
  whose `states` lists the members under all three states, `unplanned` and
  `archived` included

#### Scenario: The legacy env var still resolves the log directory
- **GIVEN** `AM_FLOW_LOG_DIR` set to a temp dir and `SHIPD_FLOW_LOG_DIR`
  unset
- **WHEN** `record_flow` runs after a lifecycle mutation
- **THEN** the snapshot is appended under the legacy variable's directory

#### Scenario: The new env var wins over the legacy one
- **GIVEN** both `SHIPD_FLOW_LOG_DIR` and `AM_FLOW_LOG_DIR` set to different
  temp dirs
- **WHEN** `record_flow` runs
- **THEN** the snapshot is appended under the `SHIPD_FLOW_LOG_DIR` directory
  only

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
- **GIVEN** `SHIPD_FLOW_LOG_DIR` set to the empty string
- **WHEN** a hooked lifecycle mutation runs
- **THEN** no flow record is written anywhere and the mutation succeeds
