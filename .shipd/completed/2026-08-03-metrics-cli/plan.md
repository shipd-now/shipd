# metrics-cli
Status: verified
Epic: delivery-metrics

## Idea

Add the delivery-metrics text summary: a stdlib `summary` verb on `metrics.py`
that renders `derive()`'s team-level metrics as a human-readable delivery
summary, with `--json` for the raw dict.

### Motivation

The merged `metrics-engine` member computes throughput, lead/cycle time, WIP,
outcomes, and cost, but exposes only a Python API — `metrics.py`'s `__main__`
today exits refusing CLI use, so no human can read the metrics without writing
code. This member is the epic's first presentation surface: the dependency-free
text summary the epic's Design names `metrics-cli`.

### Details

- Replace `metrics.py`'s `__main__` refusal with a thin argparse CLI:
  `python3 metrics.py summary [--root <root>] [--json]`.
- A pure renderer `render_summary_lines(metrics)` turns the `derive()` dict
  into text lines: throughput + trend, DORA deployment-frequency band,
  lead/cycle-time median + p85 with sample counts, rework rate, WIP by state,
  and cost — humanized units, `n/a` for absent statistics.
- `--json` prints the full derive dict (`indent=2, sort_keys=True`), matching
  the board verb's convention.

Affected capability: `delivery-metrics` (`metrics-engine` requirement modified
— CLI carve-out; `metrics-cli` requirement added). Impact:
`plugins/s/skills/build/scripts/metrics.py`,
`plugins/s/skills/build/tests/test_metrics.py`, plugin version bump. No other
script changes.

### Non-goals

- No forecasting, TUI rendering, or audience-framed rollups/exports — those are
  the `delivery-forecast`, `metrics-board-view`, and `stakeholder-rollups`
  members.
- No new metrics and no new data capture — the verb renders exactly what
  `derive()` already returns.
- No third-party dependencies; `dashboard.py` is untouched.
- No per-individual attribution of any metric (SPACE guardrail).

## Implementation

- **Verb home — `metrics.py` itself.** `dashboard.py` top-imports `textual`,
  so a dependency-free verb cannot live there, and the metrics-engine plan
  explicitly reserved the user-facing verb for this member. A subparser-style
  CLI (`summary`) leaves room for later verbs. Rejected: a new
  `metrics_cli.py` script — a second file for one thin shell; rejected: a
  `dashboard.py` verb — drags `textual` into a dependency-free surface.
- **CLI shape.** `main(argv=None)` returns an exit code; argparse subparsers
  with `summary` carrying `--root` (default cwd) and `--json`, wired via
  `set_defaults(func=...)` — the `dashboard.py` pattern. Importing the module
  stays side-effect-free; only
  `if __name__ == "__main__": raise SystemExit(main())` executes it, replacing
  the current refusal block.
- **Renderer is pure.** `render_summary_lines(metrics)` takes the derive dict
  and returns a list of strings — no I/O — mirroring `render_board_lines`, so
  tests assert on lines without stdout capture. `_cmd_summary` is the thin
  shell: `derive` → print lines, or `json.dumps` under `--json`.
- **Summary content and layout (binding):**
  - Header: `delivery metrics — <generated_at date>`.
  - `throughput: <total> shipped · last 4 weeks: <c> <c> <c> <c> · trend <↑|↓|→>`
    — trend compares the sum of the 4 most recent ISO weeks against the
    preceding 4 (`↑` greater, `↓` smaller, `→` equal); with fewer than 5 weeks
    of history the trend segment is omitted. Fewer than 4 weeks show what
    exists.
  - `deployment frequency: <dora_band> · deployment-days last 4 weeks: <c> <c> <c> <c>`.
  - `lead time: median <dur> · p85 <dur> (n=<n>)`, and `cycle time:` likewise.
  - `rework rate: <pct> (pre-merge proxy: rejected + needs-human)` — `n/a`
    when the rate is `None`.
  - `wip: <total> in flight — <state> <n> · …` (states sorted by count
    descending, then name); `wip: none` when empty.
  - `cost: <tok> output tokens (median <tok>/change) · <dur> wall-clock (median <dur>/change)`.
  - Every absent statistic renders `n/a`; empty sources never raise; exit 0.
- **Formatting helpers** (pure module-level functions, `None`-tolerant →
  `n/a`): `_fmt_duration(seconds)` → `42s` / `12m` / `3.4h` / `2.1d` (whole
  seconds/minutes, one decimal for hours/days); `_fmt_tokens(n)` → `950` /
  `85k` / `1.2M`; `_fmt_pct(rate)` → whole percent (`18%`).
- **No mean anywhere.** The renderer reads only `median`/`p85`/`n` from the
  stat blocks — percentiles, never bare means, per the epic's canon.
- Risk: low — one module touched, pure renderer, `derive()` behavior
  unchanged; guarded by extending the existing dependency-free suite, which CI
  runs without `textual`.
