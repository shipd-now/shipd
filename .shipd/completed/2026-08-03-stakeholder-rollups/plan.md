# stakeholder-rollups
Status: verified
Epic: delivery-metrics

## Idea

Add audience-framed delivery rollups: a `rollup` verb on `metrics.py` that
renders the derived metrics as a self-contained markdown summary cut for one
of three audiences — executive (trend direction + DORA-tier bands, no raw
per-item detail), PM (predictability: throughput trend, per-epic Monte-Carlo
completion bands, progress vs scope), and EM (operational flow: percentiles,
WIP/aging, rework).

### Motivation

The engine derives every delivery metric and `summary`/`forecast` print raw
team-level cuts, but nothing frames them for a specific audience — the epic's
success criterion of an executive-facing rollup presenting trend direction and
DORA-tier bands rather than raw numbers is unmet, and the linked research shows
PM, EM, and stakeholders each need a different cut of the same data. This is
the epic's last non-TUI presentation member, closing that gap.

### Details

- `build_rollup_result(root, audience, ...)`: compose `derive()` — plus, for
  the PM view, the existing forecast simulators over each epic's remaining
  members — into one JSON-serializable, audience-keyed rollup dict.
- Pure `render_rollup_lines(result)`: rollup dict in, markdown lines out — a
  self-contained document (title, section headings, bullets) that is the
  export surface: printed to stdout, redirectable to a shareable file.
- A `lead_time_dora_band` helper mapping the lead-time median onto the DORA
  performance tiers, and a shared `throughput_trend` helper reused by
  `render_summary_lines` (behavior unchanged).
- CLI: `metrics.py rollup --audience {exec,pm,em} [--root <root>] [--json]`.

Affected capability: `delivery-metrics` (`metrics-engine` requirement modified
— verb-allowlist carve-out; `stakeholder-rollups` requirement added). Impact:
`plugins/s/skills/build/scripts/metrics.py`,
`plugins/s/skills/build/tests/test_metrics.py`, plugin version bump. No other
script changes.

### Non-goals

- No file writing — the flow-capture API stays the module's only writing
  surface; "exportable" means self-contained markdown on stdout.
- No TUI rendering (that is `metrics-board-view`) and no change to the true
  change-fail input (`change-failure-signal`'s seam) — the rework rate stays
  labelled as the pre-merge proxy.
- No per-individual attribution anywhere, and no per-item/per-slug detail in
  the executive view (SPACE guardrail).
- No new data capture, no changes to `derive()`'s blocks, and no output change
  to the existing `summary`/`record-flow`/`forecast` verbs.
- No third-party dependencies.

## Implementation

- **Home — `metrics.py`.** The builder, renderer, helpers, and verb join the
  existing module: every delivery-metrics surface hangs off the one engine
  module with its subparser-with-room CLI and pure-renderer pattern
  (`metrics-cli`, `delivery-forecast` precedent). Rejected: a new `rollup.py`
  — it would split the surface from its collectors for no structural gain.
- **One verb, `--audience` choice.** `rollup --audience {exec,pm,em}` with
  argparse `choices` (an unknown audience is argparse's own exit-2 error).
  Rejected: three separate verbs — surface bloat for one parameter.
- **Rollup dict shape.** `build_rollup_result(root, audience, now=None,
  config=None, runs=10000, seed=0)` returns `{generated_at, audience,
  <audience block>}`:
  - `exec`: `{"trend": {"throughput": "up"|"down"|"flat"|None}, "dora":
    {"deployment_frequency": <band>, "lead_time_tier": <tier>|None},
    "headlines": {"shipped_total", "rework_rate"}, "cost":
    {"tokens_output_total", "seconds_total"}}` — bands and direction only,
    never per-item lists.
  - `pm`: `{"throughput": {"last_weeks": [...], "trend": ...}, "epics":
    [{"epic", "done", "total", "bands", "caution"}]}` — one entry per epic
    (walk the epics dir as `collect_wip` does; `done = total − remaining` via
    the existing `epic_remaining`), `bands` the `forecast_when` 50/85/95
    days+date objects over the remaining count (`None` when nothing remains),
    `caution` the existing sparse-history string.
  - `em`: `{"lead_time", "cycle_time", "wip", "deployment_days_last_weeks",
    "rework_rate", "flow": {"n", "latest_by_state"}}` — the stat blocks and
    WIP passed through from `derive`.
- **Lead-time DORA tier.** `lead_time_dora_band(median_seconds)`: `elite`
  below 1 day, `high` below 7 days, `medium` below 30 days, else `low`;
  `None` in → `None` out. The thresholds are the published DORA/Accelerate
  performance clusters — the research report gives only the
  deployment-frequency recipe, so the tier boundaries are documented in the
  docstring as the standard clusters (the epic's exec view requires tier
  bands, plural). Rejected: reusing `dora_band` — it maps weekly
  deployment-day counts, a different axis.
- **Trend helper.** `throughput_trend(counts)` returns `"up"`/`"down"`/
  `"flat"`, or `None` under five weeks of history — the exact
  4-vs-preceding-4 comparison `render_summary_lines` computes inline today;
  the summary renderer switches to the helper with byte-identical output
  (existing tests are the guard).
- **Determinism.** The PM forecast draws through the existing deterministic
  simulators with the builder's injectable `runs`/`seed` (defaults 10000/0);
  the verb exposes no `--seed`/`--runs` — a consumer wanting control uses the
  `forecast` verb. Rejected: seed flags on `rollup` — knob duplication on a
  presentation verb.
- **Renderer.** `render_rollup_lines(result)` — dict in, markdown lines out,
  no I/O, mirroring the sibling renderers: a `# delivery rollup — <audience>
  — <date>` title, `##` sections per block, `- ` bullets; absent statistics
  render `n/a`, the trend line is omitted when `None`; the exec view is
  phrased in plain business terms (each band on one bullet). Export is the
  stdout markdown itself — no `--out` file option, keeping the verified
  write-surface constraint intact.
- **Tests.** Extend the dependency-free
  `plugins/s/skills/build/tests/test_metrics.py`: tier and trend helpers,
  per-audience builder shapes (including exec's no-per-item guarantee and PM
  determinism), renderer markdown, CLI exit codes, and import silence — no
  test touches `~` or the network.
- Risk: low — one module touched, pure additions plus one behavior-preserving
  refactor of the summary trend segment, `derive()` untouched.
