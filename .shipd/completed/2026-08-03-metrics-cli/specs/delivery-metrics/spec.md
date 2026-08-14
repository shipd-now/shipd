## MODIFIED Requirements

### Requirement: Metrics derivation engine
id: metrics-engine
base: 9f0a66fb2ff0

The delivery-metrics layer SHALL provide a **stdlib-only derivation engine**
(`metrics.py` beside the other engine scripts — no third-party imports, no
`textual`) that computes delivery metrics **purely from the event sources the
pipeline already emits**; the derivation API writes nothing and prints nothing
— its single entry point (`derive`) returns one JSON-serializable dict — and
the module's only user-facing surface is the thin `summary` CLI shell defined
by the `metrics-cli` requirement, which importing the module never executes. It
SHALL read: per-change **ship events** from the config-resolved build log
(`log_dir`, default `~/.shipd/builds/builds.jsonl`), unioned with the dated
`completed/<date>-<slug>/` archives as a ship-date fallback for changes the log
missed (the log entry wins on both); **outcome events** from the
`.shipd/autopilot/<epic>-report.json` run reports (shipped / rejected / needs-human
/ skipped); a live **WIP snapshot** from the epic tables and heartbeats via the
stdlib spec helpers (never by importing the dashboard module); and
merge/first-commit **timestamps from git** (stdlib subprocess), where a change's
merge commit is resolved by its `<slug>:`-prefixed squash subject on the base
branch and lead time is computed only over changes where both timestamps
resolve. From these it SHALL derive, per the cited canon: **throughput**
(completed-count per period), **deployment-days** per week with the DORA
frequency band (`daily` at a median ≥ 3 deployment-days/week, `weekly`,
`monthly`, else `yearly`); **lead time** (merge − first-commit) and **cycle
time** (v1: the per-change build elapsed recorded in the log) each reported as
**median plus 50/85/95 percentiles with the sample count — never a bare mean**;
**WIP** by lifecycle state with per-item age (age omitted, never guessed, when
no evidence exists); the **outcome distribution** as the pre-merge rework proxy
(the true change-failure input remains a seam for `change-failure-signal`); and
**cost** (token-output and wall-clock totals and per-change medians). All
functions SHALL be **pure and deterministic** — `root`, `config`, and `now` are
injectable, timestamps are UTC, malformed log lines are skipped rather than
fatal — and no metric SHALL ever be attributed to an individual.

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
