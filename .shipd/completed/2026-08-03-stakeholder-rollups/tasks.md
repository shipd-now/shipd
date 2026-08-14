# Tasks — stakeholder-rollups

## 1. Tier and trend helpers

- [x] 1.1 [req: stakeholder-rollups] In
      `plugins/s/skills/build/tests/test_metrics.py`, add failing tests for
      the helpers: `lead_time_dora_band` maps medians below 1 day / 7 days /
      30 days / beyond to `elite`/`high`/`medium`/`low` (boundary values land
      in the lower tier: exactly 1 day is `high`) and `None` to `None`;
      `throughput_trend` returns `None` under five weekly counts and
      `"up"`/`"down"`/`"flat"` comparing the last four weeks' sum against the
      preceding four. Run the tests and observe them fail.
- [x] 1.2 [req: stakeholder-rollups] In
      `plugins/s/skills/build/scripts/metrics.py`, add
      `lead_time_dora_band(median_seconds)` (thresholds 86400 / 604800 /
      2592000 seconds, docstring citing the published DORA performance
      clusters) and `throughput_trend(counts)` (the 4-vs-preceding-4
      comparison `render_summary_lines` computes inline today). Refactor
      `render_summary_lines` to call `throughput_trend`, keeping its output
      byte-identical. Confirm the 1.1 tests and the existing summary tests
      pass.

## 2. Rollup builder

- [x] 2.1 [req: stakeholder-rollups] In `test_metrics.py`, add failing tests
      for `build_rollup_result` against fixture roots: the `exec` block
      carries `trend`/`dora`/`headlines`/`cost` with no change slug anywhere
      in its JSON serialization; the `pm` block carries `throughput` and one
      `epics` entry per fixture epic with `done`/`total`/`bands`/`caution`,
      identical across two calls with the same injected `now` (fixed default
      seed), with `bands` `None`
      when no members remain; the `em` block carries the `lead_time`/
      `cycle_time` stat blocks, `wip`, `deployment_days_last_weeks`,
      `rework_rate`, and `flow` (`n`, `latest_by_state`); an empty root
      degrades every block to absent/`None` statistics without raising.
- [x] 2.2 [req: stakeholder-rollups] In `metrics.py`, add
      `build_rollup_result(root, audience, now=None, config=None, runs=10000,
      seed=0)` returning `{generated_at, audience, <audience block>}` per the
      plan's shapes: compose `derive(root, now, config)`; for `pm`, walk the
      epics dir (as `collect_wip` does), compute `total` from the stub rows,
      `done = total − len(epic_remaining(root, epic))`, and the completion
      bands via `daily_throughput` + `forecast_when` (days plus
      `now.date() + days` dates) with `_sparse_caution` carried; for `exec`,
      map the lead-time median through `lead_time_dora_band` and the weekly
      counts through `throughput_trend`. Confirm the 2.1 tests pass.

## 3. Renderer and verb

- [x] 3.1 [req: stakeholder-rollups, metrics-engine] In `test_metrics.py`, add
      failing tests for the surface: `render_rollup_lines` emits a
      `# delivery rollup — <audience> — <date>` title with `##` section
      headings and the literal text "n/a" for absent statistics, omits the
      trend line when the
      trend is `None`, and renders no mean and (for `exec`) no change slug;
      the CLI verb `rollup --audience exec|pm|em` exits `0` on a fixture root
      and on an empty root, `--json` parses carrying `generated_at`/
      `audience`/the audience block, an unrecognized audience exits non-zero,
      two default-seed `pm` runs print identical output, and a bare import
      still executes no CLI.
- [x] 3.2 [req: stakeholder-rollups] In `metrics.py`, add the pure
      `render_rollup_lines(result)` renderer — rollup dict in, markdown lines
      out, no I/O, reusing `_fmt_duration`/`_fmt_tokens`/`_fmt_pct`: title,
      per-block `##` sections, `- ` bullets phrased per audience (exec in
      plain business terms; pm epic entries as a done-of-total count plus band
      dates;
      em stat lines as median · p85 · p95 with n).
- [x] 3.3 [req: stakeholder-rollups, metrics-engine] In `metrics.py` `main`,
      add the `rollup` subparser: `--audience` (required,
      `choices=("exec", "pm", "em")`), `--root` (default cwd), `--json`; wire
      `_cmd_rollup` as builder → renderer/JSON, exiting `0`. Confirm the 3.1
      tests pass.

## 4. Ship

- [x] 4.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json` (patch bump).
- [x] 4.2 [req: *] Run the full dependency-free suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`)
      without `textual` installed and confirm it passes.
