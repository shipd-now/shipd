# delivery-forecast
Status: verified
Epic: delivery-metrics

## Idea

Add the Monte-Carlo delivery forecast: pure throughput-based simulation
functions and a `forecast` verb on `metrics.py` answering "how many changes by
date D" and "when will N items (or an epic's remaining members) ship", each
with explicit 50/85/95 confidence bands.

### Motivation

The merged `metrics-engine` computes historical throughput, but nothing turns
that history into a forward-looking answer — a PM cannot ask "when will this
epic be done" or "how many changes by Friday" without hand-extrapolating. The
epic's Design names this member as the probabilistic-forecast surface, grounded
in the linked research's canon: forecast from observed throughput via Monte
Carlo, never from estimated points.

### Details

- Pure simulation core in `metrics.py`: daily throughput history (zero-filled)
  from the existing ship events, sampled with replacement over deterministic
  `random.Random(seed)` runs.
- Two question shapes: `forecast_when` (days until N items complete) and
  `forecast_how_many` (items completed by a horizon date), each reported at
  50/85/95 confidence with correct directionality.
- Epic mode: `--epic <name>` resolves N as the epic's remaining (non-archived)
  stub members via the existing worktree-aware state walk.
- A pure `render_forecast_lines` renderer and a thin `forecast` CLI verb with
  `--items | --epic | --by-date`, plus `--runs`, `--seed`, `--json`.

Affected capability: `delivery-metrics` (`metrics-engine` requirement modified
— verb-allowlist carve-out; `delivery-forecast` requirement added). Impact:
`plugins/s/skills/build/scripts/metrics.py`,
`plugins/s/skills/build/tests/test_metrics.py`, plugin version bump. No other
script changes.

### Non-goals

- No story-point or estimate-based forecasting — throughput samples only (epic
  Decisions).
- No new data capture and no changes to `derive()`'s existing blocks; the
  forecast is a parameterized verb, not a `derive` field.
- No TUI rendering and no audience-framed rollups — those are the
  `metrics-board-view` and `stakeholder-rollups` members.
- No third-party dependencies; no per-individual attribution (SPACE guardrail).

## Implementation

- **Home — `metrics.py`.** The simulation functions, renderer, and verb join
  the existing module: the `metrics-cli` member established the
  subparser-with-room CLI and the pure-renderer pattern there, and the epic's
  presentation members all hang off the one engine module. Rejected: a new
  `forecast.py` — a second file would split the delivery-metrics surface and
  its config/collector helpers for no structural gain.
- **Sampling input — daily throughput, zero-filled.**
  `daily_throughput(ship_events, now)` counts ships per UTC calendar date from
  the first dated ship event through `now.date()` inclusive, zero-filling
  gapless — zero-ship days are real observations the simulation must sample.
  Rejected: weekly sampling — far too few samples on this young pipeline's
  history; daily samples are the canonical Monte-Carlo input (research [13]).
- **Simulation core — deterministic by default.** Both simulators take
  `(daily_counts, runs=10000, seed=0)` and draw with replacement via
  `random.Random(seed)`; the fixed default seed keeps the verb reproducible
  run-to-run (the constitution's determinism bar), `--seed` varies it.
  - `forecast_how_many(daily_counts, days, ...)`: per run, sum `days` sampled
    daily counts. Confidence directionality: the count at confidence `c` is the
    nearest-rank `(100 − c)`th percentile of the run sums — the count achieved
    or exceeded in at least `c%` of runs, so p95 ≤ p85 ≤ p50.
  - `forecast_when(daily_counts, items, ..., max_days=3650)`: per run, count
    days until the cumulative sample reaches `items`, capped at `max_days` (a
    termination guard; a capped run records `max_days`). The days at confidence
    `c` is the nearest-rank `c`th percentile of the run day-counts — later
    dates at higher confidence, so p50 ≤ p85 ≤ p95. Dates are
    `now.date() + days`.
  - Reuse the existing `percentiles` helper on the run distributions; the
    zero-history guard (total shipped = 0) short-circuits both simulators to an
    n/a result rather than sampling a distribution that can never finish.
- **Epic resolution.** `epic_remaining(root, epic)` reads
  `.shipd/epics/<epic>/epic.md`, parses the stub table via
  `spec_common.parse_epic_changes`, resolves each member through the existing
  `_member_state_and_location`, and returns the slugs whose state is not
  `archived` — "remaining" means not yet shipped, so `unplanned` and every
  in-flight state count. A missing epic file returns `None`, which the verb
  reports as an error (exit 2) — an epic typo is user error, unlike empty
  history which degrades to n/a.
- **CLI shape.** `metrics.py forecast --root <root>` with a required, mutually
  exclusive mode: `--items N` | `--epic NAME` (the "when" question) |
  `--by-date YYYY-MM-DD` (the "how many" question); plus `--runs` (default
  10000), `--seed` (default 0), `--json`. A `--by-date` not after today, or an
  unparseable date, is an argparse-style error (exit 2). The result dict is
  JSON-serializable: `generated_at`, `mode`, `history` (`days`,
  `total_shipped`), the question echo (`items`/`epic`/`remaining` or
  `by_date`/`horizon_days`), `runs`, `seed`, `bands` (`{p50, p85, p95}` —
  days-and-date objects for "when", counts for "how many"; all `None` when
  history is empty), and `caution` (`None` or a sparse-history string).
- **Renderer.** `render_forecast_lines(result)` — result dict in, lines out,
  no I/O, mirroring `render_summary_lines`: a `delivery forecast — <date>`
  header, a history line, one bands line phrased per mode (e.g.
  `50% by <date> (<n>d) · 85% …` or `≥<n> at 85%`), and the caution line when
  present. Empty history renders `n/a` bands and exits 0.
- **Sparse-history caution.** When the history spans fewer than 14 days or
  fewer than 10 total ships, `caution` states the sample is thin and the
  forecast low-confidence — the research's steady-state caveat surfaced rather
  than silently over-promising.
- **Tests.** Extend the dependency-free
  `plugins/s/skills/build/tests/test_metrics.py` (the one-test-file-per-module
  convention): simulator determinism and directionality, the zero-history and
  max-days guards, epic resolution against a fixture epic tree, renderer lines,
  and CLI exit codes — no test touches `~` or the network.
- Risk: low — one module touched, pure additions, `derive()` untouched;
  simulation cost (10k runs × horizon days) is a few million integer adds,
  well under a second in CPython.
