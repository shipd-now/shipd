# metrics-board-view
Status: verified
Epic: delivery-metrics

## Idea

Add a delivery-metrics view to the textual board: an `m`-key modal screen
rendering the four research-pinned visuals — a DORA-tier rollup row, a weekly
throughput run chart, a cycle-time scatterplot with 50/85/95 percentile
lines, and a cumulative flow diagram — from the metrics the engine already
derives.

### Motivation

The delivery-metrics epic derives throughput, cycle time, flow history, and
the DORA bands, but the board TUI — the one surface a human watches live —
shows none of it; the epic's stub commits this member to the TUI visuals
(cycle-time scatter/percentiles, throughput run chart, CFD, DORA rollup) as
the layer's only `textual`-permitted presentation.

### Details

- A `MetricsScreen` modal on the board, opened by a footer-bound `m` key and
  a command-palette entry, closed by `Escape` or its compact ✕ control.
- Content, top to bottom: a DORA tile row (deployment-frequency band,
  lead-time tier, post-merge change-fail rate beside the pre-merge rework
  proxy, lead/cycle medians), a per-ISO-week throughput run chart, a
  cycle-time scatterplot overlaid with the p50/p85/p95 lines, and a CFD
  stacking the recorded flow series by board lane in the lane theme colors.
- Data comes from `metrics.derive` plus `metrics.collect_ship_events`
  (per-item scatter points), assembled by a dependency-free helper and
  computed off the UI thread; every visual degrades to `n/a`/blank on empty
  sources.

Affected capabilities: `delivery-dashboard` (added `board-metrics-view`,
modified `board-command-palette`). Impact:
`plugins/s/skills/build/scripts/dashboard.py`,
`plugins/s/skills/build/tests/test_metrics_view.py` (new),
`plugins/s/skills/build/tests_textual/test_dashboard.py`,
`plugins/s/.claude-plugin/plugin.json`. No change to `metrics.py` and no
new dependencies.

### Non-goals

- No change to the `delivery-metrics` engine capability — the view is a
  read-only consumer of `derive`/`collect_ship_events`; nothing new is
  derived or captured.
- No forecast or rollup surfaces in the TUI — those ship as `metrics.py`
  CLI verbs (`forecast`, `rollup`).
- No burnup chart (the research names it; the epic stub pins four visuals).
- No metrics on the `html` verb's page and no persistence of view state.
- No per-individual attribution and no mean anywhere — stat blocks surface
  median/percentiles only, matching the epic's SPACE guardrail.

## Implementation

- **Entry and screen.** `MetricsScreen(ModalScreen)` sized like the existing
  detail modals (~90% viewport, `$surface` background, flat
  `$shipd-border-strong` border), pushed by a new `Binding("m",
  "show_metrics", "Metrics")` on `BoardApp` and dismissed by `Escape` or a
  `compact-button` ✕. `action_show_metrics` no-ops while any modal is
  already open (`len(self.screen_stack) > 1`), so `m` from a modal cannot
  stack screens. Body is a `VerticalScroll` of section `Static`s. All CSS
  through `$` theme variables (board-shipd-theme rule).
- **Palette.** `get_system_commands` adds a board-screen `SystemCommand`
  ("Delivery metrics") routing through `action_show_metrics` — the
  `board-command-palette` requirement is modified accordingly; modal screens
  still get quit only.
- **Data assembly, off the UI thread.** A dependency-free
  `metrics_view_data(root, now=None)` in `dashboard.py`'s stdlib prelude
  (ahead of the `textual` import, like `change_artifacts`) returns
  `{"metrics": metrics.derive(root, now), "ship_events":
  metrics.collect_ship_events(root)}`. `derive` shells out to git per
  shipped change, far too slow for the 2 s board tick, so the screen runs
  the assembly in a thread worker (`run_worker(..., thread=True)`) on mount
  behind a "computing metrics…" placeholder, repaints via an
  `_apply_data(data)` seam, and re-derives on a 30 s `set_interval` while
  open. The data callable is injectable (`data_fn` constructor argument,
  mirroring `board_fn`) and `_apply_data` is the test seam, so `tests_textual`
  never waits on a worker or touches git. A failing assembly keeps the last
  rendered data (or shows "metrics unavailable") — never a traceback.
- **Pure renderers** live in the stdlib prelude, returning plain/markup text
  rows, unit-tested in `tests/` without `textual` (via the
  `_load_dashboard_stdlib` pattern):
  - `dora_tiles(metrics)` → `(label, value)` pairs: deployment-frequency
    band with the recent weekly deployment-day counts; lead-time tier via
    `metrics.lead_time_dora_band(median)`; change-fail rate labelled
    post-merge; rework rate labelled pre-merge proxy; lead- and cycle-time
    medians (p85 alongside) humanized via `metrics._fmt_duration` — reused,
    not duplicated, the same way `render_summary_lines` uses it; absent
    values render `n/a`.
  - `run_chart_rows(per_week, cols, rows)` → eighth-block rows via
    `build_report.render_chart` over the newest `cols` weeks' counts with
    bounds `(0, max(counts) or 1)` plus a label carrying total and newest
    week.
    Rejected: `build_report.scale_bounds` — its 500-token minimum ceiling
    flattens single-digit weekly counts to nothing.
  - `scatter_rows(ship_events, cycle_time, cols, rows)` → the Vacanti
    scatter: x maps `ship_ts` linearly over the observed span, y maps the
    per-change `seconds` linearly from 0 to the max value; a cell with any
    point renders `•`, the p50/p85/p95 values overlay as `─` lines labelled
    at the right edge with humanized durations and the sample count; a
    point wins the cell over a line. Events without `ship_ts`/`seconds` are
    skipped; no events → empty rows and an `n/a` label.
  - `flow_lane(state)` maps a lifecycle state to its board lane, mirroring
    `_member_column`'s state-only branch (`archived`→`shipped`,
    `ready`→`ready`, `unplanned`→`unplanned`, else `building`), and
    `cfd_rows(series, cols, rows)` renders the CFD: one column per record
    over the newest `cols` flow records (oldest→newest), each column
    stacking its lane counts bottom-up in order `shipped`, `building`,
    `ready`, `unplanned` as `[$lane-<name>]█[/]` markup scaled against the
    series' max stacked total, plus a lane-colored legend line and the
    record count. Rejected: time-resampled columns — the series is
    event-driven (one record per lifecycle mutation) and resampling adds
    complexity without changing the read; the label states the span
    instead. Empty series → a "no flow history recorded yet" notice.
- **Chart geometry.** Sections are width-adaptive like `ActivityChart`
  (column count from the rendered width); fixed heights — tiles 1 row per
  line, run chart 4 rows, scatter 8, CFD 8 — inside the scrollable body.
- **Theme colors in markup.** Lane bands and percentile/label accents use
  content-markup theme variables (`[$lane-shipped]`, `[$fg-muted]` …), the
  `epic_group_title` stall-marker idiom, keeping the no-hex rule intact.
- **Versioning.** `plugins/s/` changes, so `plugin.json` bumps
  0.6.49 → 0.6.50 in this change.
- **Risks.** `derive`'s git subprocess cost is capped by the worker + 30 s
  cadence; a concurrent `board-rows`/`shipped-column-polish` merge touches
  `dashboard.py` (merge-order conflicts only, no structural overlap); flow
  history may be short-lived data on young repos — the CFD's honest empty
  state covers it.
