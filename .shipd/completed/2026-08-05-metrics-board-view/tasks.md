## 1. Dependency-free data helper and renderers (stdlib prelude)

- [x] 1.1 [req: board-metrics-view] Add
      `plugins/s/skills/build/tests/test_metrics_view.py` loading
      `dashboard.py` via the `_load_dashboard_stdlib` pattern (copy it from
      `plugins/s/skills/build/tests/test_change_artifacts.py`), covering:
      `flow_lane` state→lane
      mapping (`archived`→`shipped`, `ready`→`ready`,
      `unplanned`→`unplanned`, `draft`/`active`/`rejected`→`building`);
      `dora_tiles` on a full metrics fixture (band, lead-time tier,
      post-merge-labelled change-fail rate, pre-merge-labelled rework rate,
      humanized medians) and on an empty fixture (n/a values);
      `run_chart_rows` (peak week full column, zero week blank, total in the
      label); `scatter_rows` (dot cells, labelled p50/p85/p95 lines, sample
      count, no `mean`, events missing `ship_ts`/`seconds` skipped, empty
      events → n/a label); `cfd_rows` (one column per record, bottom-up
      stack order shipped/building/ready/unplanned, `[$lane-*]` markup,
      legend line, empty series → no-flow-history notice); and
      `metrics_view_data` on a temp fixture root (a `metrics`/`ship_events`
      dict, no file writes). Run it and observe it fail — none of the
      helpers exist yet.
- [x] 1.2 [req: board-metrics-view] In
      `plugins/s/skills/build/scripts/dashboard.py`, in the stdlib prelude
      ahead of the `textual` import, add `flow_lane(state)` and
      `dora_tiles(metrics)` per the plan (import `metrics` beside the other
      prelude imports; humanize durations via `metrics._fmt_duration`;
      absent statistics render n/a).
- [x] 1.3 [req: board-metrics-view] In the same prelude, add
      `run_chart_rows(per_week, cols, rows)`: `build_report.render_chart`
      over the newest `cols` weeks' counts with bounds `(0, max(counts) or
      1)` and a label line carrying the total and newest week.
- [x] 1.4 [req: board-metrics-view] In the same prelude, add
      `scatter_rows(ship_events, cycle_time, cols, rows)`: x maps `ship_ts`
      linearly over the observed span, y maps `seconds` from 0 to the max;
      `•` for any-point cells, `─` percentile overlays labelled at the right
      edge with humanized p50/p85/p95 and `n`; a point wins a contested
      cell; skip events missing `ship_ts` or `seconds`; empty → blank rows
      plus an n/a label.
- [x] 1.5 [req: board-metrics-view] In the same prelude, add
      `cfd_rows(series, cols, rows)`: newest `cols` records as columns
      (oldest→newest), each stacking `flow_lane`-mapped counts bottom-up in
      order shipped/building/ready/unplanned as `[$lane-<name>]█[/]` markup
      scaled to the series' max stacked total, plus a lane-colored legend
      line with the record count; empty series returns the no-flow-history
      notice.
- [x] 1.6 [req: board-metrics-view] In the same prelude, add
      `metrics_view_data(root, now=None)` returning `{"metrics":
      metrics.derive(root, now), "ship_events":
      metrics.collect_ship_events(root)}`; confirm all of
      `plugins/s/skills/build/tests/test_metrics_view.py` now passes under a
      `python3` without `textual`.

## 2. MetricsScreen and app wiring (textual)

- [x] 2.1 [req: board-metrics-view, board-command-palette] Extend
      `plugins/s/skills/build/tests_textual/test_dashboard.py` with failing
      tests: pressing `m` on the mounted board pushes the metrics screen and
      the app carries a visible `m` binding; the `m` action is inert while
      another modal is open; a screen constructed with an injected
      `data_fn` populates its four sections through `_apply_data` (placeholder
      gone, tiles/run-chart/scatter/CFD mounted) without reopening; a failing
      `data_fn` leaves the screen rendered with no traceback; `Escape` and
      the ✕ control dismiss back to the board; the board-screen palette
      source lists the delivery-metrics command (beside grouping and quit)
      and its callback pushes the metrics screen; modal palette still lists
      only quit.
- [x] 2.2 [req: board-metrics-view] In `dashboard.py`, add
      `MetricsScreen(ModalScreen)`: ~90% viewport container on `$surface`
      with a flat `$shipd-border-strong` border, header row with a
      `compact-button` ✕ (`escape` binding dismisses), `VerticalScroll` body
      with a computing placeholder; `__init__(root, data_fn=None)` defaulting
      to `metrics_view_data`; `on_mount` runs the data callable in a thread
      worker and re-derives on a 30-second `set_interval`; `_apply_data(data)`
      swaps the placeholder for the DORA tile row, run chart, scatter, and
      CFD sections rendered from the pure helpers (width-adaptive columns
      per the `ActivityChart` idiom; rows: chart 4, scatter 8, CFD 8;
      theme-variable CSS only); worker failure keeps the last rendered
      content or an unavailable notice.
- [x] 2.3 [req: board-metrics-view, board-command-palette] Wire `BoardApp`:
      add `Binding("m", "show_metrics", "Metrics")`; `action_show_metrics`
      pushes `MetricsScreen(self.root)` only when no modal is open
      (`len(self.screen_stack) == 1`); add the board-screen "Delivery
      metrics" `SystemCommand` to `get_system_commands` routing through the
      same action. Confirm the 2.1 tests pass.

## 3. Version bump and verification

- [x] 3.1 [req: board-metrics-view] Bump
      `plugins/s/.claude-plugin/plugin.json` version 0.6.49 → 0.6.50 (a
      `plugins/s/` change must ship a version bump).
- [x] 3.2 [req: *] Verification barrier: run `python3 -m unittest discover
      -s plugins/s/skills/build/tests` under a `textual`-free interpreter
      and the `tests_textual` suite with `textual` installed
      (`pip install -r requirements.txt`); both green.
