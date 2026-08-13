# Delivery, flow, and engineering metrics for PM/EM/stakeholder observability

## Summary

Three metric families dominate the authoritative literature and together answer
"how fast and how healthy is delivery?" **(1) DORA / Accelerate** defines the
delivery-*outcome* metrics — now five, split into *throughput* (deployment
frequency, change lead time, failed-deployment recovery time) and *instability*
(change fail rate, deployment rework rate), each bounded by explicit timestamps
and with a reference computation in Google's Four Keys [1][2][3]. **(2) Vacanti's
flow metrics** — WIP, cycle time, throughput, linked by Little's Law
(`Cycle Time = WIP / Throughput`) — supply the in-flight predictability toolset,
with the per-item cycle-time **scatterplot** (50/85/95 percentile lines) as the
recommended visual and the basis for **probabilistic (Monte Carlo) forecasting**,
which the literature favors over story-point velocity [4][5][6][13][14].
**(3) SPACE** reframes "productivity" as five dimensions and supplies the central
anti-patterns: never use activity metrics in isolation, and keep individual data
private [11][12]. For a per-PR/per-change event pipeline, deployment frequency,
change lead time, change fail rate, throughput, and cycle time are directly
derivable from ship timestamps, task counts, and shipped/rejected/needs-human
outcomes; recovery time and steady-state forecasting need incident linkage and
roughly-constant WIP respectively [2][3][4].

## DORA: the delivery-outcome metrics

DORA is the standard framework for measuring rate of delivery and delivery health
at the *outcome* level. It now defines **five** metrics (evolved from the original
four), grouped into **throughput** — deployment frequency, change lead time, and
failed-deployment recovery time — and **instability** — change fail rate and
deployment rework rate (the fifth metric, added 2024; "stability" was renamed
"instability", and "MTTR" became "failed-deployment recovery time") [1]. Each is
timestamp-bounded: **change lead time** runs from commit-to-version-control to
production deploy; **change fail rate** is the ratio of deployments needing
immediate intervention (rollback/hotfix); **recovery time** is how long it takes
to restore service after such a failure [1].

Google's **Four Keys** reference implementation gives exact recipes [2][3]:
lead time = **median** of `deploy_ts − commit_ts` joined by commit SHA; change
failure rate = `(failed / total) × 100` with failures joined to incidents by
deployment id; time-to-restore = median `resolved_ts − created_ts` per incident;
deployment frequency counts **deployment-days** (four deploys in one day = one
deployment-day), with the "Daily" band requiring a median ≥ 3 days/week. Two
computation cautions the report must respect: the aggregate is the **median, not
the mean**, and frequency counts deployment-days, **not raw deploy counts** —
using means or raw counts changes the numbers [2][3].

## Flow metrics and Little's Law

The three basic flow metrics are **WIP** (units that entered but not yet exited a
process, delimited by arrival/departure timestamps), **cycle time** (elapsed
*calendar* time an item is in progress — inherently including all delays), and
**throughput** (a departure-rate count of items completing per period) [4][5].
They are linked by **Little's Law** in Vacanti's flow form: `Average Cycle Time =
Average WIP / Average Throughput`, rearrangeable to `Throughput = WIP / Cycle
Time` [4][6][8]. Its reliability depends on **steady-state** conditions (arrival
≈ departure rate, WIP roughly constant, average WIP age not increasing); if
arrivals persistently exceed departures and WIP grows, the relationship breaks
down [4][6][8].

## Probabilistic forecasting beats velocity

The flow literature positions **managing flow, not story-point velocity**, as the
best strategy for delivery predictability, and grounds forecasting in **throughput**
(an empirically observed count) rather than estimated points [4][14]. Vacanti
favors **Monte Carlo simulation** over a direct Little's-Law calculation precisely
because the law's steady-state assumptions are often violated; historical
throughput is exactly the input Monte Carlo consumes to answer "how many items by
date D?" or "when will N items be done?" as a probability, not a promise
[4][13][14]. For a per-PR pipeline, historical per-change throughput is directly
available as that input [2][4].

## Visualizing delivery for each audience

The recommended cycle-time visual is a **per-item scatterplot** — completion date
(x) vs cycle time in days (y) — overlaid with **50/85/95 percentile lines** that
convert history into probabilistic commitments (e.g. "the 85% line says 85% of
items finish in ≤ 13 days"), favored over averages that outliers distort [4][7][9].
For delivery over time, a **cumulative flow diagram (CFD)** shows work moving
through workflow states; a **widening band means work is piling up in that stage**
— a bottleneck (arrival rate exceeding departure rate) [10]. A **burnup** chart
(completed work plus a separate total-scope line) exposes **scope growth** that a
single-line burndown hides [10]. (Note: contrary to a common assumption, Vacanti's
book does *not* make the CFD its primary predictability visual — the scatterplot
holds that role; the CFD is a flow/bottleneck diagnostic [4].)

## SPACE and the measurement anti-patterns

**SPACE** (Forsgren et al., ACM Queue 2021) reframes developer productivity as
five dimensions — **S**atisfaction & wellbeing, **P**erformance, **A**ctivity,
**C**ommunication & collaboration, **E**fficiency & flow — insisting productivity
is multidimensional and cannot be captured by any single metric [11]. It supplies
the core guardrails: **never use activity metrics in isolation** (more activity ≠
better outcomes), and **never optimize individual productivity** — it discourages
collaboration, so individual data must stay private and only **aggregated
team/org** values are shared [11][12]. These are the defenses against Goodhart-style
gaming and vanity/comparison misuse; DORA independently echoes not evaluating
individuals with these metrics [12][15].

## What each audience needs

The audiences want different cuts of the same event data [16][17][18]:
- **Engineering Manager** — the operational flow view: cycle-time scatterplot and
  percentiles, CFD/bottlenecks, WIP and aging, throughput trend, and the full DORA
  set to find and fix delivery friction.
- **Product Manager** — predictability and scope: throughput trend, a
  probabilistic forecast ("N items by date D at 85%"), and burnup (progress vs
  scope growth) to steer commitments.
- **Executive / non-technical stakeholder** — a compact rollup: **trend direction**
  and **DORA performance-tier bands** rather than raw numbers, a small set of
  headline outcomes, and cost/throughput at a glance — reported on a slower cadence
  and framed in business terms, not per-item detail [16][17].

## Application to a per-PR autonomous pipeline

Because this consumer ships exactly one change per PR and already records
per-change events (ship timestamp, task counts, cost/time, and a
shipped/rejected/needs-human outcome), most of the above is **directly derivable**
from existing data, per the Four Keys mapping [2][3][4]:
- **Deployment frequency / throughput** ← count of merged changes per period
  (ship timestamps; deployment-days for the DORA band).
- **Change lead time** ← merge timestamp − first-commit timestamp per change
  (median).
- **Cycle time** ← per-change elapsed in-progress time (planned→shipped), plottable
  as the scatterplot with percentiles.
- **WIP / aging** ← in-flight changes by lifecycle state (the board's lanes) and
  their age.
- **Change-fail / rework signal** ← the per-run rejected / needs-human outcomes as
  a *pre-merge* rework proxy (a true DORA change-fail rate needs a *post-merge*
  failure signal — a revert/hotfix link — which is not tracked today).
- **Cost** ← tokens and wall-clock time per change (already in the build log).
- **Forecast** ← Monte Carlo over historical per-change throughput (valid while WIP
  is roughly steady).

## Gaps & Caveats

- **Source strength varies.** DORA definitions and the Four Keys recipes rest on
  primary sources [1][2][3] and are strongest. Flow-metric definitions, Little's
  Law, and the scatterplot/CFD/burnup material are non-controversial flow canon
  from Vacanti's book [4] but were verified largely via a faithful secondary
  re-read [5][6][7] and vendor knowledge bases rather than direct book quotation;
  low-risk. SPACE was verified via secondary sources [11][12] though every
  assertion traces to the 2021 ACM Queue paper.
- **DORA is evolving** — four→five metrics (deployment rework rate added 2024) and
  renamed terms; treat metric counts/names as of 2025–2026 and re-check dora.dev
  [1].
- **Change-failure needs definition here.** A one-change-per-PR pipeline has no
  traditional incident system; whether its own rejected/needs-human outcomes are a
  *valid* stand-in for DORA's incident-linked change-fail rate and recovery time is
  an open modelling decision, not a settled mapping.
- **Forecasting assumes steady state.** Little's-Law and Monte Carlo forecasts
  degrade if WIP is not roughly constant — relevant to a young pipeline with sparse
  history and bursty arrivals [4][8].
- **Aging** was covered only indirectly (via Little's Law and CFD); a dedicated
  work-item-aging chart with its own thresholds/alerting is a known follow-on.

## Sources

1. DORA — DORA metrics guide. https://dora.dev/guides/dora-metrics/
2. Google Cloud — Using the Four Keys to measure DevOps performance. https://cloud.google.com/blog/products/devops-sre/using-the-four-keys-to-measure-your-devops-performance
3. dora-team/fourkeys — reference implementation (METRICS.md). https://github.com/dora-team/fourkeys
4. Daniel S. Vacanti — Actionable Agile Metrics for Predictability. https://actionableagile.com/books/aamfp/
5. T. Cagley — AAMfP re-read wk 3: the basic metrics of flow. https://tcagley.wordpress.com/2017/10/28/actionable-agile-metrics-for-predictability-by-daniel-s-vacanti-re-read-saturday-week-3-the-basic-metrics-of-flow/
6. T. Cagley — AAMfP re-read wk 4: Little's Law. https://tcagley.wordpress.com/2017/11/04/actionable-agile-metrics-for-predictability-by-daniel-s-vacanti-re-read-saturday-week-4-introduction-to-littles-law/
7. T. Cagley — AAMfP re-read wk 11: cycle-time scatterplots. https://tcagley.wordpress.com/2018/01/06/actionable-agile-metrics-for-predictability-by-daniel-s-vacanti-re-read-saturday-week-11-introduction-to-cycle-time-scatterplots/
8. Businessmap — Little's Law explained. https://businessmap.io/continuous-flow/littles-law
9. Scrum.org — Getting to 85% (ActionableAgile), part 1. https://www.scrum.org/resources/blog/getting-85-agile-metrics-actionableagile-part-1
10. LibreTexts (De Anza) — Visual metrics: burndown, burnup, and cumulative flow. https://eng.libretexts.org/Workbench/De_Anza_-_95G/07:_Agile_Metrics_Risk_and_Delivery_Discipline/7.02:_Agile_Delivery_Discipline_Guide/7.2.02:_Visual_Metrics-_Burndown_Burnup_and_Cumulative_Flow
11. Octopus Deploy — The SPACE framework. https://octopus.com/devops/metrics/space-framework/
12. getDX — SPACE metrics. https://getdx.com/blog/space-metrics
13. Expedia Group Tech — Monte Carlo forecasting in software delivery. https://medium.com/expedia-group-tech/monte-carlo-forecasting-in-software-delivery-474bb49cb3f9
14. Scrum.org — Bye bye velocity, hello throughput. https://www.scrum.org/resources/blog/bye-bye-velocity-hello-throughput
15. The Pragmatic Engineer — Measuring developer productivity. https://newsletter.pragmaticengineer.com/p/measuring-developer-productivity
16. Taazaa — DORA metrics and executive reporting. https://www.taazaa.com/blog/dora-metrics-and-executive-reporting
17. Harness — The executive playbook: communicating engineering metrics. https://www.harness.io/blog/the-executive-playbook-communicating-engineering-metrics-for-maximum-business-impact
18. getDX — DORA metrics. https://getdx.com/blog/dora-metrics/
