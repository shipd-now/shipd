# delivery-metrics

### Requirement: Metrics derivation engine
id: metrics-engine

The delivery-metrics layer SHALL provide a **stdlib-only derivation engine**
(`metrics.py` beside the other engine scripts — no third-party imports, no
`textual`) that computes delivery metrics **purely from the event sources the
pipeline already emits**; the derivation API writes nothing and prints nothing
— its single entry point (`derive`) returns one JSON-serializable dict — and
the module's user-facing surface is limited to the thin CLI verbs defined by
the `metrics-cli`, `flow-timeseries`, `delivery-forecast`, and
`stakeholder-rollups` requirements (`summary`, `record-flow`, `forecast`,
`rollup`), which importing the module never executes; the flow-capture API
defined by the `flow-timeseries` requirement is the module's one writing
surface, and `derive` never invokes it. It SHALL read: per-change **ship
events** from the config-resolved build log (`log_dir`, default
`~/.shipd/builds/builds.jsonl`), unioned with the dated `completed/<date>-<slug>/`
archives as a ship-date fallback for changes the log missed (the log entry
wins on both); **outcome events** from the `.shipd/autopilot/<epic>-report.json`
run reports (shipped / rejected / needs-human / skipped); a live **WIP
snapshot** from the epic tables and heartbeats via the stdlib spec helpers
(never by importing the dashboard module); and merge/first-commit **timestamps
from git** (stdlib subprocess), where a change's merge commit is resolved by
its `<slug>:`-prefixed squash subject on the base branch and lead time is
computed only over changes where both timestamps resolve. From these it SHALL
derive, per the cited canon: **throughput** (completed-count per period),
**deployment-days** per week with the DORA frequency band (`daily` at a median
≥ 3 deployment-days/week, `weekly`, `monthly`, else `yearly`); **lead time**
(merge − first-commit) and **cycle time** (v1: the per-change build elapsed
recorded in the log) each reported as **median plus 50/85/95 percentiles with
the sample count — never a bare mean**; **WIP** by lifecycle state with
per-item age (age omitted, never guessed, when no evidence exists); the
**outcome distribution** as the pre-merge rework proxy and the post-merge
**change-failure block** (per the `change-failure-signal` requirement, carried
as `change_failures`); **cost** (token-output and wall-clock totals and
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

### Requirement: Delivery summary verb
id: metrics-cli

The delivery-metrics layer SHALL provide a `summary` verb on `metrics.py`
(`python3 metrics.py summary [--root <root>] [--json]`, stdlib argparse, no
third-party imports) that derives the metrics for the root via `derive` and
prints a human-readable, team-level delivery summary composed by a **pure
renderer** (`render_summary_lines(metrics)` — derive-dict in, list of lines
out, no I/O). The summary SHALL present: **throughput** (total shipped, the
last four ISO weeks' counts, and a trend direction comparing the sum of the
four most recent weeks against the preceding four — omitted when history spans
fewer than five weeks); the **DORA deployment-frequency band** with recent
deployment-day counts; **lead time** and **cycle time** each as median and
85th percentile with the sample count, in humanized durations; the **rework
rate** as a whole percentage labelled as the pre-merge proxy; **WIP** counts by
lifecycle state; and **cost** (token-output and wall-clock totals with
per-change medians, humanized) — reading only `median`/`p85`/`n` from the stat
blocks, never a mean, and attributing nothing to an individual. Where `--json`
is given, the verb SHALL print the full derive dict as JSON instead of the
summary lines. If an event source is empty or a statistic is absent, then the
verb SHALL render `n/a` (or omit the segment, for the trend) and exit `0`
rather than fail.

#### Scenario: Summary renders the delivery metrics as text
- **GIVEN** a fixture root with ship events, autopilot outcomes, and in-flight
  members
- **WHEN** `metrics.py summary --root <root>` runs
- **THEN** it exits `0` and prints throughput with per-week counts, the DORA
  band, lead- and cycle-time medians with p85 and sample counts, a rework-rate
  percentage, WIP by state, and cost totals — and no mean appears anywhere

#### Scenario: JSON mode prints the raw derive dict
- **WHEN** `metrics.py summary --root <root> --json` runs
- **THEN** stdout parses as JSON carrying the `throughput`, `deployment_days`,
  `lead_time`, `cycle_time`, `wip`, `outcomes`, and `cost` blocks, with no
  human-readable summary lines

#### Scenario: Empty sources degrade to n/a, never an error
- **GIVEN** a fixture root with no build log, archives, reports, or epics
- **WHEN** the summary verb runs
- **THEN** it exits `0`, absent statistics render as `n/a`, and no traceback is
  raised

#### Scenario: The verb is dependency-free and import stays side-effect-free
- **GIVEN** an environment without `textual`
- **WHEN** the summary verb runs, and separately the module is merely imported
- **THEN** the verb succeeds without any third-party import, and a bare import
  executes no CLI and prints nothing

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

### Requirement: Audience-framed rollups
id: stakeholder-rollups

The delivery-metrics layer SHALL provide **audience-framed rollups** on
`metrics.py` (stdlib only, no third-party imports): a builder
(`build_rollup_result(root, audience, now=None, config=None, runs=10000,
seed=0)`) composing the existing `derive` output — and, for the PM view, the
existing deterministic Monte-Carlo simulators over each epic's remaining
members — into one JSON-serializable rollup dict `{generated_at, audience,
<audience block>}`, and a **pure renderer** (`render_rollup_lines(result)` —
rollup dict in, list of lines out, no I/O) whose lines form a
**self-contained markdown document** (a title naming the audience and
generated date, section headings, bullet lines) — the export surface for
non-technical stakeholders: printed to stdout by the verb and never written
to a file (the flow-capture API remains the module's one writing surface).
The three cuts follow the cited research: **`exec`** SHALL present trend
direction and bands, never raw per-item detail — the throughput trend
(`up`/`down`/`flat` comparing the four most recent ISO weeks' sum against the
preceding four, absent below five weeks of history), the DORA
deployment-frequency band, a **lead-time DORA tier** via
`lead_time_dora_band(median_seconds)` (`elite` below 1 day, `high` below 7
days, `medium` below 30 days, else `low` — the published DORA performance
clusters; `None` when no sample), the headline shipped total and rework rate
labelled as the pre-merge proxy, and cost totals — and its block and rendered
lines SHALL name no change slug and list no per-item detail; **`pm`** SHALL
present predictability — the recent weekly throughput with the trend, and one
entry per epic carrying its done/total member counts (done = stub members
archived) and, when members remain, 50/85/95 completion bands (days and
projected date) from the existing `forecast_when` over the remaining count,
with the sparse-history caution carried; **`em`** SHALL present the
operational flow view — the lead-time and cycle-time stat blocks
(median/percentiles/sample count, never a mean), WIP by state with the aging
summary, recent deployment-days, the rework rate, and the recorded flow
series' record count with its latest per-state counts. The trend SHALL come
from a shared `throughput_trend(counts)` helper that `render_summary_lines`
reuses with unchanged output. The rollup SHALL be surfaced by a `rollup` verb
(`python3 metrics.py rollup --audience {exec,pm,em} [--root <root>]
[--json]`) printing the rendered markdown lines, or the rollup dict as JSON
under `--json`, deterministic for the fixed default seed. If an event source
is empty or a statistic absent, then the verb SHALL render `n/a` (or omit the
trend and forecast bands) and exit `0`; an unrecognized audience SHALL be
rejected with a non-zero exit. No rollup SHALL attribute any metric to an
individual.

#### Scenario: The exec rollup shows trends and bands, never per-item detail
- **GIVEN** a fixture root with at least five ISO weeks of ship events,
  resolvable lead times, and autopilot outcomes
- **WHEN** `metrics.py rollup --audience exec --root <root>` runs
- **THEN** it exits `0` and prints a markdown document carrying a throughput
  trend direction, the DORA deployment-frequency band, a lead-time tier, a
  rework-rate percentage labelled as the pre-merge proxy, and cost totals —
  and no change slug appears anywhere in the output

#### Scenario: The lead-time tier maps the median onto the DORA clusters
- **GIVEN** lead-time medians below one day, below seven days, below thirty
  days, and beyond
- **WHEN** each is mapped through `lead_time_dora_band`
- **THEN** the tiers are `elite`, `high`, `medium`, and `low` respectively,
  and a `None` median yields no tier

#### Scenario: The PM rollup forecasts each epic's remaining members
- **GIVEN** a fixture epic whose stub table holds archived and non-archived
  members plus a multi-day ship history
- **WHEN** `metrics.py rollup --audience pm --root <root>` runs twice
- **THEN** both runs exit `0` with identical output carrying the epic's
  done/total counts and 50/85/95 completion bands as days and projected dates
  for the remaining members

#### Scenario: The EM rollup presents the operational cut without a mean
- **GIVEN** a fixture root with ship events, in-flight members, and recorded
  flow history
- **WHEN** `metrics.py rollup --audience em --root <root>` runs
- **THEN** it exits `0` and prints lead- and cycle-time medians with
  percentiles and sample counts, WIP by state with aging, the rework rate, and
  the flow series' record count with its latest per-state counts — and no mean
  appears anywhere

#### Scenario: Empty sources degrade to n/a and an unknown audience errors
- **GIVEN** a fixture root with no build log, archives, reports, or epics
- **WHEN** the rollup verb runs for each of the three audiences, and then with
  an unrecognized `--audience` value
- **THEN** each audience run exits `0` rendering `n/a` for absent statistics
  with no traceback, while the unrecognized audience exits non-zero

#### Scenario: The rollup is dependency-free, exportable markdown, and JSON-capable
- **GIVEN** an environment without `textual`
- **WHEN** the rollup verb runs with and without `--json`, and separately the
  module is merely imported
- **THEN** the plain run prints a self-contained markdown document (title and
  section headings) writing no file, the `--json` run prints a parseable dict
  carrying `generated_at`, `audience`, and the audience block, and a bare
  import executes no CLI and prints nothing

### Requirement: Change-failure signal
id: change-failure-signal

The delivery-metrics layer SHALL define a shipped change as **failed** when
post-merge remediation exists for it: a **revert** — a commit reachable from
the base ref whose subject starts `Revert "` and whose quoted text begins with
the change's `<slug>:` squash prefix (a revert-of-revert, whose quoted text
starts `Revert `, never counts) — or a **declared fix** — a later shipped
change whose archived `plan.md` header carries a `Fixes:` metadata line naming
the slug (per the shipd-spec-format metadata grammar), read from the dated
`completed/<date>-<slug>/` archives. The layer SHALL provide a pure,
stdlib-only collector on `metrics.py`
(`collect_change_failures(root, ship_events, base_ref=None)`) returning
`{rate, n_failed, n_shipped, failed}` where `failed` lists `{slug, signals}`
per failed shipped change, sorted by slug — each revert signal
`{kind: "revert", ts}` with the revert commit's UTC committer timestamp, each
fix signal `{kind: "fix", by}` with the fixing change's slug — a change
counting **once** in `n_failed` however many signals it accrues, and
`rate = n_failed / n_shipped` (`None` when there are no ship events). The git
revert scan SHALL follow the `git_change_times` idiom: stdlib subprocess,
resolved as a module attribute at call time, and tolerant — no git repository
or a failed scan yields no revert signals, never an error — and a revert whose
slug matches no shipped change SHALL be ignored. The rate SHALL be surfaced
labelled as post-merge, the pre-merge `rework_rate` proxy remaining unchanged
beside it: the `summary` verb SHALL print a change-fail line next to the
rework line; the `em` rollup's rework section SHALL add the rate; the `exec`
rollup's headlines SHALL add the rate **only** — no failed slug in the exec
block or its rendered lines. If the statistic is absent, then the surfaces
SHALL render `n/a` and exit `0`.

#### Scenario: A reverted change counts as failed
- **GIVEN** ship events including change `a` and a base-branch history holding
  a commit with subject `Revert "a: ship the widget"`
- **WHEN** change failures are collected
- **THEN** `a` is failed with one `revert` signal carrying the revert commit's
  UTC timestamp, and the rate reflects one failure over the shipped total

#### Scenario: A shipped fix declaring Fixes marks the fixed change failed
- **GIVEN** a completed archive whose `plan.md` header carries `Fixes: a`
- **WHEN** change failures are collected
- **THEN** `a` is failed with a `fix` signal naming the fixing change's slug,
  and the fixing change itself is not failed by that declaration

#### Scenario: Signals join over shipped changes and count once
- **GIVEN** a revert subject naming a slug absent from the ship events, and
  change `a` carrying both a revert and a declared fix
- **WHEN** change failures are collected
- **THEN** the unknown-slug revert is ignored and `a` counts once in
  `n_failed` with both signals listed

#### Scenario: Empty or git-less history degrades
- **GIVEN** a root with no ship events, and separately a root that is no git
  repository
- **WHEN** failures are collected and the `summary` verb runs
- **THEN** the rate is `None`, derivation succeeds, and the summary renders
  the change-fail line as `n/a` exiting `0`

#### Scenario: Surfaces label post-merge and exec stays slug-free
- **GIVEN** a fixture with a failed shipped change
- **WHEN** `summary`, `rollup --audience em`, and `rollup --audience exec` run
- **THEN** each prints the change-fail rate labelled post-merge, the pre-merge
  proxy line still prints, and no failed slug appears anywhere in the exec
  block's JSON serialization or rendered lines
