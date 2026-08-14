# Tasks — delivery-forecast

## 1. Simulation core

- [x] 1.1 [req: delivery-forecast] In
      `plugins/s/skills/build/tests/test_metrics.py`, add failing tests for
      the simulation core: `daily_throughput` zero-fills from first ship date
      through `now` (UTC dates); `forecast_when` and `forecast_how_many` are
      identical across calls with the same seed; when-bands satisfy
      p50 ≤ p85 ≤ p95 and how-many-bands p95 ≤ p85 ≤ p50; an all-zero or empty
      history yields `None` bands without looping; a tiny `max_days` caps a
      when-run. Run the tests and observe them fail.
- [x] 1.2 [req: delivery-forecast] In
      `plugins/s/skills/build/scripts/metrics.py`, add
      `daily_throughput(ship_events, now)` returning the zero-filled per-UTC-day
      ship counts from the first dated event through `now.date()` (empty list
      when no dated events).
- [x] 1.3 [req: delivery-forecast] In `metrics.py`, add
      `forecast_when(daily_counts, items, runs=10000, seed=0, max_days=3650)`
      and `forecast_how_many(daily_counts, days, runs=10000, seed=0)`: sample
      with replacement via `random.Random(seed)`; return `{p50, p85, p95}`
      bands using the existing `percentiles` helper — cth percentile of run
      day-counts for "when", `(100 − c)`th of run totals for "how many";
      short-circuit to all-`None` bands when `sum(daily_counts) == 0` or the
      history is empty; cap each when-run at `max_days`. Confirm the 1.1 tests
      pass.

## 2. Epic resolution

- [x] 2.1 [req: delivery-forecast] In `test_metrics.py`, add failing tests for
      `epic_remaining` against a fixture epic tree: non-archived members
      (including `unplanned`) are returned, `archived` members are excluded,
      and a missing epic returns `None`.
- [x] 2.2 [req: delivery-forecast] In `metrics.py`, add
      `epic_remaining(root, epic)`: read `.shipd/epics/<epic>/epic.md` (via
      `sc.specs_dir`), parse the stub table with `sc.parse_epic_changes`,
      resolve each member through `_member_state_and_location`, and return the
      sorted slugs whose state is not `archived`; return `None` when the epic
      file does not exist. Confirm the 2.1 tests pass.

## 3. Renderer and verb

- [x] 3.1 [req: delivery-forecast, metrics-engine] In `test_metrics.py`, add
      failing tests for the forecast surface: `render_forecast_lines` output
      for both modes including the sparse-history caution line and "n/a" bands
      on empty history; the CLI verb `forecast --items`/`--by-date`/`--epic`
      (exit 0, deterministic repeat with `--seed`, `--json` parses with
      `history`/`bands`/`caution`, empty root exits 0 with "n/a", unknown epic
      exits non-zero, mode flags mutually exclusive and required); and that a
      bare import still executes no CLI.
- [x] 3.2 [req: delivery-forecast] In `metrics.py`, add the result-dict builder
      (`generated_at`, `mode`, `history` with `days`/`total_shipped`, question
      echo with `items`/`epic`/`remaining` or `by_date`/`horizon_days`, `runs`,
      `seed`, `bands` with date+days objects for "when" and counts for
      "how many", `caution` set when history < 14 days or < 10 ships) and the
      pure `render_forecast_lines(result)` renderer (header, history line,
      per-mode bands line, caution line; "n/a" for absent values, no I/O).
- [x] 3.3 [req: delivery-forecast, metrics-engine] In `metrics.py` `main`, add
      the `forecast` subparser: `--root` (default cwd), a required mutually
      exclusive `--items <int>` / `--epic <name>` / `--by-date <YYYY-MM-DD>`,
      `--runs` (default 10000), `--seed` (default 0), `--json`; `_cmd_forecast`
      wires collection → simulation → renderer/JSON, exits 2 on an unparseable
      or non-future `--by-date` and on an unknown epic, else 0. Confirm the 3.1
      tests pass.

## 4. Ship

- [x] 4.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json` (patch bump).
- [x] 4.2 [req: *] Run the full dependency-free suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) without
      `textual` installed and confirm it passes.
