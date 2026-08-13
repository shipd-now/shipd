# delivery-metrics
Status: complete
Theme: developer-experience

## Introduction

Today the pipeline records rich per-change telemetry — every shipped change lands
a `builds.jsonl` event (ship timestamp, task counts, cost, time), a dated
`completed/` archive, and an autopilot run report (shipped / rejected /
needs-human) — but **none of it is aggregated into delivery metrics a human can
read**. A PM cannot see throughput or a probabilistic "when will this epic be
done"; an EM cannot see cycle-time percentiles, WIP, or where work piles up; a
stakeholder has no rollup of delivery health. The raw events exist; the
observation layer does not.

This epic adds a **delivery-metrics layer**: a dependency-free derivation engine
that turns the existing per-change/per-PR events into the standard delivery
metrics — DORA's deployment frequency, change lead time, and change-fail/rework
rate; Vacanti's flow metrics (throughput, cycle time with 50/85/95 percentiles,
WIP, aging); and a Monte-Carlo throughput forecast — surfaced through a text
summary, the TUI board, and audience-framed rollups for PM, EM, and stakeholders.
The research report this epic links grounds every metric definition and
visualization in primary sources, and maps each metric to the event data this
system already emits.

Intended outcome: any of the three audiences can answer "how fast and how healthy
is delivery?" from data the pipeline already produces, without hand-counting PRs.
Success criteria: throughput, lead time, and cycle-time percentiles are derivable
and shown; a probabilistic forecast is available for an epic's remaining members;
and an executive-facing rollup presents trend direction and DORA-tier bands rather
than raw numbers.

### Non-goals

- **No per-individual metrics.** Per the SPACE guardrail, everything is aggregated
  at the team/system level; the layer never scores a person.
- **No story-point velocity.** Forecasting is probabilistic (throughput-based
  Monte Carlo), never estimated points.
- **No new heavy infrastructure** — no external metrics service, database, or
  time-series server; metrics derive from the existing event files (and git/PR),
  and the derivation engine stays stdlib-only.
- **Not a real-time incident/alerting system** — this observes delivery flow, it
  does not page on outages.
- The epic does not itself plan or build the member changes.

## Research

- [Delivery, flow, and engineering metrics for PM/EM/stakeholder observability](../../research/delivery-metrics/report.md) — DORA five keys and the Four Keys computation recipes, Vacanti flow metrics + Little's Law + cycle-time scatterplots, Monte-Carlo forecasting vs velocity, SPACE anti-patterns, audience-specific rollups, and a mapping of each metric to this pipeline's per-change event data.

## Decisions

Cross-cutting choices every member inherits:

- **Derive, don't re-instrument.** Metrics are computed from the events the
  pipeline already emits — `~/.shipd/builds/builds.jsonl`, the dated `.shipd/completed/`
  archives, `.shipd/autopilot/<epic>-report.json`, and git/PR timestamps. Two gaps
  need genuinely new capture (a flow time-series and a post-merge failure signal)
  and are isolated into their own members; everything else is pure derivation.
- **Definitions follow the cited canon** (see `## Research`): deployment
  frequency as merged-changes-per-period (deployment-*days* for the DORA band);
  change lead time as merge − first-commit; cycle time as in-progress elapsed with
  **median and 50/85/95 percentiles** (never a bare mean — outliers distort it);
  throughput as a completed-item count; Little's Law / Monte-Carlo forecasting
  understood to assume roughly steady-state WIP.
- **Team/system level only.** No metric is ever attributed to an individual
  (SPACE); stakeholder views show trends and DORA-tier bands, not raw per-item
  detail.
- **The derivation engine is stdlib-only** (constitution). The single permitted
  `textual` dependency is confined to the TUI metrics view; the text summary,
  forecast, engine, and rollups stay dependency-free and unit-testable without
  `textual`.
- **Change-failure is an explicit modelling decision, not an assumption.** This
  pipeline has no incident system; whether the existing rejected/needs-human
  outcomes are a valid stand-in for DORA's change-fail rate, or whether a
  post-merge revert/hotfix signal must be captured, is decided in
  `change-failure-signal` — the rest of the layer treats the change-fail input as
  a defined seam.

## Design

The layer is a pipeline: **event sources → a stdlib `metrics` derivation engine →
presentation surfaces**, plus two capture members that record what today's data
lacks.

- **Foundation** (`metrics-engine`): a dependency-free module reading the existing
  event sources and computing the metric series (throughput, lead time, cycle time
  + percentiles, WIP, aging, outcome distribution, cost). Pure functions; every
  downstream surface consumes its output.
- **Capture the gaps**: `flow-timeseries` records per-lifecycle-state counts over
  time (today the board only has a live snapshot — a CFD and aging history need a
  recorded series); `change-failure-signal` defines and records the post-merge
  failure/rework signal that a true DORA change-fail rate needs.
- **Present**: `metrics-cli` (a text delivery summary), `delivery-forecast`
  (Monte-Carlo "how many by date / when will the epic finish"), `metrics-board-view`
  (TUI visuals: cycle-time scatter/percentiles, throughput run chart, CFD, DORA
  rollup), and `stakeholder-rollups` (PM predictability, EM operational, and an
  executive tier-band rollup, exportable for non-technical stakeholders).

Seams the decomposition follows: derivation vs presentation (engine vs the four
render members), and derivable-now vs needs-capture (the two capture members). The
engine is the barrier every other member depends on; the capture members feed it
new inputs; the presentation members are mutually independent once the engine and
their inputs exist.

## Changes

| Change | Description | Code | Integration | Unknowns | Risk |
| --- | --- | --- | --- | --- | --- |
| metrics-engine | Stdlib derivation engine: read builds.jsonl / completed archives / autopilot reports / git-PR timestamps and compute throughput, lead time, cycle time + 50/85/95 percentiles, WIP, aging, outcome distribution, and cost | high | medium | medium | medium |
| metrics-cli | A `metrics` text-summary verb: throughput trend, lead/cycle-time median + 85th percentile, deployment-frequency band, rework rate, and cost — dependency-free | medium | low | low | low |
| flow-timeseries | Record per-lifecycle-state counts over time (append-only) so a cumulative-flow diagram and work-item aging have historical data the live board lacks | medium | medium | medium | low |
| change-failure-signal | Define this pipeline's change-failure/rework metric (post-merge revert/hotfix linkage vs the pre-merge rejected/needs-human proxy) and capture it, feeding the DORA change-fail rate | medium | medium | high | medium |
| delivery-forecast | Monte-Carlo throughput-based forecast — "how many changes by date D" and "when will an epic's remaining members ship", with explicit confidence bands, over historical per-change throughput | medium | low | medium | low |
| metrics-board-view | A metrics view in the textual board: cycle-time scatter/percentiles, throughput run chart, a CFD, and the DORA-tier rollup (the one member permitted to use `textual`) | high | medium | medium | medium |
| stakeholder-rollups | Audience-framed presentations — EM operational, PM predictability, and an executive rollup (trend direction + DORA-tier bands, not raw numbers), exportable for non-technical stakeholders | medium | medium | low | low |
