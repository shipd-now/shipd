## MODIFIED Requirements

### Requirement: Metrics derivation engine
id: metrics-engine
base: 97684258e284

The delivery-metrics layer SHALL provide a **stdlib-only derivation engine**
(`metrics.py` beside the other engine scripts — no third-party imports, no
`textual`) that computes delivery metrics **purely from the event sources the
pipeline already emits**; the derivation API writes nothing and prints nothing
— its single entry point (`derive`) returns one JSON-serializable dict — and
the module's user-facing surface is limited to the thin CLI verbs defined by
the `metrics-cli`, `flow-timeseries`, and `delivery-forecast` requirements
(`summary`, `record-flow`, `forecast`), which importing the module never
executes; the flow-capture API defined by the `flow-timeseries` requirement is
the module's one writing surface, and `derive` never invokes it. It SHALL
read: per-change **ship events** from the config-resolved build log
(`log_dir`, default `~/.shipd/builds/builds.jsonl`), unioned with the dated
`completed/<date>-<slug>/` archives as a ship-date fallback for changes the
log missed (the log entry wins on both); **outcome events** from the
`.shipd/autopilot/<epic>-report.json` run reports (shipped / rejected /
needs-human / skipped); a live **WIP snapshot** from the epic tables and
heartbeats via the stdlib spec helpers (never by importing the dashboard
module); and merge/first-commit **timestamps from git** (stdlib subprocess),
where a change's merge commit is resolved by its `<slug>:`-prefixed squash
subject on the base branch and lead time is computed only over changes where
both timestamps resolve. From these it SHALL derive, per the cited canon:
**throughput** (completed-count per period), **deployment-days** per week with
the DORA frequency band (`daily` at a median ≥ 3 deployment-days/week,
`weekly`, `monthly`, else `yearly`); **lead time** (merge − first-commit) and
**cycle time** (v1: the per-change build elapsed recorded in the log) each
reported as **median plus 50/85/95 percentiles with the sample count — never a
bare mean**; **WIP** by lifecycle state with per-item age (age omitted, never
guessed, when no evidence exists); the **outcome distribution** as the
pre-merge rework proxy (the true change-failure input remains a seam for
`change-failure-signal`); **cost** (token-output and wall-clock totals and
per-change medians); and the recorded **flow series** as a read-only `flow`
block (per the `flow-timeseries` requirement). All functions SHALL be **pure
and deterministic** — `root`, `config`, and `now` are injectable, timestamps
are UTC, malformed log lines are skipped rather than fatal — and no metric
SHALL ever be attributed to an individual.

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

## ADDED Requirements

### Requirement: Monte-Carlo delivery forecast
id: delivery-forecast

The delivery-metrics layer SHALL provide a **Monte-Carlo throughput forecast**
on `metrics.py` (stdlib only, no third-party imports) built from pure
simulation functions that sample, with replacement, the **daily throughput
history** — ships per UTC calendar date, zero-filled from the first dated ship
event through `now` — derived from the existing ship-event collection, and
never from estimates or story points. The simulators SHALL be **deterministic
for a given seed**: draws come from `random.Random(seed)` with an injectable
seed defaulting to a fixed value, and `runs` (default 10000) injectable. The
layer SHALL answer both canonical questions with explicit **50/85/95
confidence bands**, directionally correct: for **"how many items by a horizon
date"** the count at confidence `c` is the nearest-rank `(100 − c)`th
percentile of the simulated run totals (the count achieved or exceeded in at
least `c%` of runs, non-increasing as confidence rises); for **"when will N
items complete"** the answer at confidence `c` is the nearest-rank `c`th
percentile of the simulated day-counts (non-decreasing as confidence rises),
reported as both days and a projected date, with each run's day-count capped
by an injectable `max_days` termination guard (default 3650). The layer SHALL
resolve an epic's **remaining members** as the epic stub-table members whose
worktree-aware lifecycle state is not `archived`. The forecast SHALL be
surfaced by a `forecast` verb (`python3 metrics.py forecast --root <root>`)
requiring exactly one mode — `--items N`, `--epic <name>`, or
`--by-date YYYY-MM-DD` — with `--runs`, `--seed`, and `--json` options, whose
result dict carries the history summary (`days`, `total_shipped`), the
question echo, the `bands`, and a `caution` field; when the history spans
fewer than 14 days or fewer than 10 total ships, the result SHALL carry a
sparse-history caution (the steady-state caveat surfaced, never silently
over-promising). The verb SHALL print lines from a **pure renderer**
(`render_forecast_lines(result)` — result dict in, list of lines out, no I/O),
or the result dict as JSON under `--json`. If the ship-event history is empty,
then the simulators and the verb SHALL degrade — `None`/`n/a` bands, exit `0`,
never an unterminating simulation; if the named epic does not exist, then the
verb SHALL report an error and exit non-zero. No forecast output SHALL be
attributed to an individual.

#### Scenario: The when-forecast reports ordered confidence bands
- **GIVEN** a fixture ship-event history spanning several days with varying
  daily counts
- **WHEN** `metrics.py forecast --items 5 --root <root>` runs
- **THEN** it exits `0` and prints 50/85/95 bands as days and projected dates
  with p50 ≤ p85 ≤ p95, and the same invocation with the same seed prints
  identical output

#### Scenario: The how-many-forecast counts down as confidence rises
- **GIVEN** the same fixture history
- **WHEN** `metrics.py forecast --by-date <future date> --root <root>` runs
- **THEN** it exits `0` and prints counts at 50/85/95 confidence with
  p95 ≤ p85 ≤ p50, and `--json` instead prints a JSON dict carrying `history`,
  `bands`, and `caution`

#### Scenario: Epic mode forecasts the remaining members
- **GIVEN** a fixture epic whose stub table holds archived and non-archived
  members
- **WHEN** `metrics.py forecast --epic <name> --root <root>` runs
- **THEN** the forecast targets exactly the non-archived member count and
  echoes those slugs, while a nonexistent epic name reports an error and exits
  non-zero

#### Scenario: Sparse history carries a caution
- **GIVEN** a history with fewer than 14 days of observations
- **WHEN** a forecast runs
- **THEN** the result's `caution` states the history is thin and the rendered
  output includes the caution line

#### Scenario: Empty history degrades and always terminates
- **GIVEN** a fixture root with no ship events
- **WHEN** `forecast --items 3` runs
- **THEN** it exits `0`, renders `n/a` bands without simulating an
  unterminating run, and raises no traceback

#### Scenario: The forecast is dependency-free and deterministic
- **GIVEN** an environment without `textual`
- **WHEN** the forecast verb runs twice with an explicit `--seed`, and
  separately the module is merely imported
- **THEN** both runs succeed without third-party imports and print identical
  bands, and a bare import executes no CLI and prints nothing
