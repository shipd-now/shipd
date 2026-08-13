## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Metrics derivation engine
id: metrics-engine
base: d55f795dece3

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
