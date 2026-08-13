## ADDED Requirements

### Requirement: Metrics derivation engine
id: metrics-engine

The delivery-metrics layer SHALL provide a **stdlib-only derivation engine**
(`metrics.py` beside the other engine scripts — no third-party imports, no
`textual`) that computes delivery metrics **purely from the event sources the
pipeline already emits**, writing nothing and printing nothing: its surface is a
Python API whose single entry point (`derive`) returns one JSON-serializable
dict. It SHALL read: per-change **ship events** from the config-resolved build
log (`log_dir`, default `~/.shipd/builds/builds.jsonl`), unioned with the dated
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
