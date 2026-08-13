# metrics-engine
Status: verified
Epic: delivery-metrics

## Idea

The stdlib **delivery-metrics derivation engine**: a new
`plugins/s/skills/build/scripts/metrics.py` that reads the pipeline's existing
per-change event sources and computes the delivery metrics every later surface
consumes — throughput, change lead time, cycle time with 50/85/95 percentiles,
WIP and work-item aging, outcome distribution, and cost — as pure functions with
no user-facing verb (the `metrics-cli` member adds that next).

### Motivation

The pipeline already records everything needed to answer "how fast and how
healthy is delivery?" — `builds.jsonl` ship events, dated `completed/` archives,
autopilot outcome reports, epic tables and heartbeats — but no code aggregates it
into metrics. This engine is the epic's foundation member: every presentation
member (`metrics-cli`, `delivery-forecast`, `metrics-board-view`,
`stakeholder-rollups`) depends on its output, so it ships first, alone, and
dependency-free.

### Details

- **Event collection**: per-change ship events from the build log (config-resolved
  `log_dir`, default `~/.shipd/builds/builds.jsonl`), with the dated
  `completed/<date>-<slug>/` archives as a ship-date fallback for changes the log
  missed; outcome events from `.shipd/autopilot/<epic>-report.json`; the live WIP
  snapshot from the epic tables + heartbeats; merge/first-commit timestamps from
  git (stdlib `subprocess`) for lead time.
- **Derivation** (canon per the epic's Decisions and the linked research):
  throughput as completed-count per period; deployment-**days** per week and the
  DORA frequency band; lead time (merge − first-commit) and cycle time as
  **median + 50/85/95 percentiles**, never bare means; WIP by lifecycle state
  with per-item age; outcome distribution (shipped / rejected / needs-human) as
  the pre-merge rework proxy; token/time cost totals and per-change medians.
- **Seams**: change-failure input stays a defined seam (the
  `change-failure-signal` member decides its true source later); no flow
  time-series (the `flow-timeseries` member records history — this engine
  computes only from what exists today).

Affected capability: new `delivery-metrics` (added `metrics-engine`
requirement). Impact: new `plugins/s/skills/build/scripts/metrics.py`, new
stdlib tests in `plugins/s/skills/build/tests/`; plugin version bump. No
change to existing scripts.

### Non-goals

- No CLI verb, rendering, or formatting — the engine's surface is its Python API.
- No forecasting (Monte Carlo lives in `delivery-forecast`).
- No new data capture — no flow time-series, no post-merge failure signal.
- No per-individual attribution of any metric (SPACE guardrail).
- No third-party dependencies — `textual` never appears in this module or its
  tests.

## Implementation

- **Module layout** (`metrics.py`, beside the other engine scripts; imports only
  stdlib plus the sibling stdlib modules `spec_common as sc`, `spec_status as
  ss`, `heartbeat`):
  - `collect_ship_events(root, config=None)` — read the build log (reuse
    `build_report.py`'s config helpers: `load_config`/`build_log_dir`, or
    equivalent local resolution of `~/.shipd-config.json`'s `log_dir`) into
    per-change dicts `{slug, ship_ts, tasks, status, tokens_output, seconds}`;
    union with `completed/<date>-<slug>/` dirs (date-prefix → midnight-UTC
    ship-date fallback) so a change missing from the log still counts, keyed by
    slug with the log entry winning.
  - `collect_outcomes(root)` — fold every `.shipd/autopilot/*-report.json` into
    counts + per-member lists for `shipped` / `rejected` / `needs_human` /
    `skipped`.
  - `collect_wip(root, now)` — walk `.shipd/epics/*/epic.md` via
    `sc.parse_epic_changes` + `ss`-derived member board state (the same
    stdlib path the dashboard's data layer uses; do **not** import `dashboard`),
    yielding in-flight members `{slug, state, age_days}` where age comes from the
    member's worktree/planned artifacts' mtimes — clamp missing evidence to
    `age_days=None` rather than guessing.
  - `git_change_times(root, slug)` — `subprocess.run(["git","log","--format=..."])`
    resolving the squash-merge commit on the base branch whose subject starts
    with `"<slug>:"` → merge timestamp, and its first parent-side commit
    timestamp as first-commit; return `None`s on any miss (shallow clone, no
    match) — lead time is computed only over changes with both timestamps.
  - `percentiles(values, (50,85,95))` — nearest-rank on sorted values, pure.
  - `derive(root, now=None, config=None)` — the one entry point: returns a plain
    dict `{"throughput": {per_week list, total}, "deployment_days": per-week
    counts + "dora_band", "lead_time": {median, p50, p85, p95, n},
    "cycle_time": {...same shape...}, "wip": {by_state counts, items, aging},
    "outcomes": {...}, "cost": {tokens_output total/median, seconds
    total/median}}` — JSON-serializable, no printing, no writes.
- **DORA band** from deployment-days/week medians per the Four Keys recipe:
  `daily` (median ≥ 3 days/week), `weekly` (≥ 1 day/week), `monthly` (≥ 1
  deployment/month), else `yearly`.
- **Cycle time v1** = per-change build elapsed (`time.total_seconds` from the
  log) — the honest in-progress measure available today; lead time = merge −
  first-commit from git. Both documented in docstrings as the v1 timestamp
  definitions so later members (flow-timeseries) can refine cycle time with real
  state history.
- **Injectable seams for tests**: `derive` and collectors take `root` (temp
  fixture trees), `config` (log-dir override — no test touches `~`), and `now`
  (deterministic aging/windows). Git calls isolated in `git_change_times` so
  tests monkeypatch it or run against a scratch git repo.
- **Determinism**: no wall-clock reads outside the `now` default, no network,
  UTC everywhere (`datetime.timezone.utc`); malformed log lines are skipped, not
  fatal (mirrors `build_report.py`'s tolerance).

Risk: medium — new module with several source parsers, but zero changes to
existing scripts, pure functions throughout, and every parser is
fixture-testable in the dependency-free suite CI already runs.
