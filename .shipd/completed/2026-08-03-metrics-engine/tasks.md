## 1. Pure derivation core (percentiles, bands, shapes)

- [x] 1.1 [req: metrics-engine] In `plugins/s/skills/build/tests/` (a NEW module,
      e.g. `test_metrics.py`), add unit tests for the pure helpers of a new
      `plugins/s/skills/build/scripts/metrics.py`: `percentiles(values, (50, 85,
      95))` (nearest-rank on sorted values, outlier-robust, empty input → no
      values); the DORA band mapping from weekly deployment-day medians (`daily`
      at median ≥ 3, then `weekly`, `monthly`, else `yearly`); and that derived
      lead/cycle blocks carry `median/p50/p85/p95/n` and NO `mean` field. These
      MUST run under system `python3` with `textual` NOT installed. Run and
      observe failure.
- [x] 1.2 [req: metrics-engine] Create `metrics.py` (stdlib-only; imports limited
      to stdlib + the sibling stdlib modules `spec_common`, `spec_status`,
      `heartbeat`) implementing `percentiles`, the deployment-day/DORA-band
      helpers, and the result-shape builders per `plan.md`'s Implementation.
      Confirm 1.1 passes.

## 2. Event collection (log, archives, outcomes, WIP, git)

- [x] 2.1 [req: metrics-engine] In `tests/test_metrics.py`, add fixture-based
      tests: `collect_ship_events` unions the build log with dated
      `completed/<date>-<slug>/` archives (log entry wins; archive-only change
      carries the date fallback; malformed log line skipped, not fatal — all
      against a temp root + `config` log-dir override, never `~`);
      `collect_outcomes` folds multiple autopilot reports into
      shipped/rejected/needs-human/skipped counts + per-member lists;
      `collect_wip` reads a fixture root's epics and counts only in-flight
      members by state, with no fabricated age when evidence is absent. Run and
      observe failure.
- [x] 2.2 [req: metrics-engine] Implement `collect_ship_events(root, config)`,
      `collect_outcomes(root)`, and `collect_wip(root, now)` in `metrics.py` per
      plan (reuse/replicate `build_report.py`'s config resolution for `log_dir`;
      walk epics via `sc.parse_epic_changes` + the `ss` member-state path — do
      NOT import `dashboard`). Confirm 2.1 passes.
- [x] 2.3 [req: metrics-engine] In `tests/test_metrics.py`, add git tests against
      a scratch `git init` repo: `git_change_times(root, slug)` resolves the
      merge timestamp from a `<slug>:`-prefixed commit subject and a
      first-commit timestamp, and returns `None`s when no subject matches. Then
      implement `git_change_times` (stdlib `subprocess`, UTC parsing) and
      confirm the tests pass.

## 3. The derive() entry point

- [x] 3.1 [req: metrics-engine] In `tests/test_metrics.py`, add end-to-end tests:
      `derive(root, now=..., config=...)` on a fixture root returns one
      JSON-serializable dict (`json.dumps` round-trips) with the
      `throughput` / `deployment_days` (+`dora_band`) / `lead_time` /
      `cycle_time` / `wip` / `outcomes` / `cost` blocks shaped per plan; a
      change with unresolvable git timestamps is excluded from the lead-time
      sample without failing derivation; `derive` writes no file into the
      fixture tree and prints nothing. Run and observe failure.
- [x] 3.2 [req: metrics-engine] Implement `derive(root, now=None, config=None)`
      composing the collectors and derivation helpers per plan (deterministic:
      injectable `now`, UTC everywhere; monkeypatchable `git_change_times`).
      Confirm 3.1 passes.

## 4. Version bump & verification

- [x] 4.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json` to the next unused version above
      the branch base (base is 0.6.36, so 0.6.37 — pick the next free one if
      taken, verifying against branches/tags/history).
- [x] 4.2 [req: *] Run the full dependency-free suite `python3 -m unittest
      discover -s plugins/s/skills/build/tests` (must pass with `textual` NOT
      installed — includes the new `test_metrics.py`), then, in a venv with
      `pip install -r requirements.txt`, run
      `plugins/s/skills/build/tests_textual` to confirm no regression; both
      green.
- [x] 4.3 [req: *] Manually exercise the real behavior: run
      `metrics.derive(".")` against THIS repo's actual `.shipd/` + build log (system
      python3, no textual) and sanity-check the output — non-zero throughput,
      plausible DORA band, percentile blocks with `n` > 0, WIP states matching
      the board, JSON-serializable — and paste the summary numbers into the task
      completion note.
