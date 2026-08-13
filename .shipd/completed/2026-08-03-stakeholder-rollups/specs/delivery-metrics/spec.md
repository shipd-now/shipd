## MODIFIED Requirements

### Requirement: Metrics derivation engine
id: metrics-engine
base: 1f535d46f015

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
**outcome distribution** as the pre-merge rework proxy (the true
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

## ADDED Requirements

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
