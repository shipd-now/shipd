#!/usr/bin/env python3
"""Unit tests for metrics.py — the stdlib-only delivery-metrics derivation
engine (delivery-metrics metrics-engine).

Every test here MUST pass under system ``python3`` with ``textual`` NOT
installed: ``metrics`` is dependency-free and never imports ``textual`` or
``dashboard``. No test reads the real ``~/.shipd/builds`` or ``~/.shipd-config.json``
— collectors take an injected ``config`` log-dir override and temp fixture
roots, and ``derive`` takes an injectable ``now``.
"""

import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
import unittest
import unittest.mock

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import metrics  # noqa: E402


UTC = dt.timezone.utc


# ---------------------------------------------------------------------------
# 1. Pure derivation core: percentiles, DORA band, stat-block shape
# ---------------------------------------------------------------------------

class PercentilesTest(unittest.TestCase):
    def test_nearest_rank_on_sorted_values(self):
        # 1..10: p50 -> 5, p85 -> 9, p95 -> 10 (nearest-rank, 1-indexed
        # ceil(p/100 * n)).
        pct = metrics.percentiles(list(range(1, 11)))
        self.assertEqual(pct["p50"], 5)
        self.assertEqual(pct["p85"], 9)
        self.assertEqual(pct["p95"], 10)

    def test_unsorted_input_is_sorted_first(self):
        pct = metrics.percentiles([10, 1, 5, 3, 9, 2, 8, 4, 7, 6])
        self.assertEqual(pct["p50"], 5)
        self.assertEqual(pct["p85"], 9)
        self.assertEqual(pct["p95"], 10)

    def test_outlier_does_not_move_the_median(self):
        # A single huge outlier leaves p50 anchored to the middle value.
        self.assertEqual(metrics.percentiles([1, 2, 3, 4, 100])["p50"], 3)

    def test_empty_input_yields_no_values(self):
        pct = metrics.percentiles([])
        self.assertIsNone(pct["p50"])
        self.assertIsNone(pct["p85"])
        self.assertIsNone(pct["p95"])

    def test_single_value(self):
        pct = metrics.percentiles([42])
        self.assertEqual(pct["p50"], 42)
        self.assertEqual(pct["p85"], 42)
        self.assertEqual(pct["p95"], 42)


class DoraBandTest(unittest.TestCase):
    def test_daily_at_weekly_median_at_least_three(self):
        self.assertEqual(metrics.dora_band([3, 3, 4, 5]), "daily")

    def test_weekly_at_median_at_least_one(self):
        self.assertEqual(metrics.dora_band([1, 2, 1, 1]), "weekly")

    def test_monthly_when_sparse_but_at_least_one_per_month(self):
        # median weekly deployment-days is 0, but ~1 deployment-day/month.
        self.assertEqual(metrics.dora_band([0, 1, 0, 0]), "monthly")

    def test_yearly_when_almost_never(self):
        self.assertEqual(metrics.dora_band([0] * 20 + [1]), "yearly")

    def test_empty_is_yearly(self):
        self.assertEqual(metrics.dora_band([]), "yearly")

    def test_lowering_cadence_lowers_the_band(self):
        bands = [metrics.dora_band(w) for w in (
            [4, 4, 4], [1, 1, 2], [0, 0, 1, 0])]
        self.assertEqual(bands, ["daily", "weekly", "monthly"])


class LeadTimeDoraBandTest(unittest.TestCase):
    DAY = 86400
    WEEK = 7 * 86400
    MONTH = 30 * 86400

    def test_elite_below_one_day(self):
        self.assertEqual(metrics.lead_time_dora_band(self.DAY - 1), "elite")
        self.assertEqual(metrics.lead_time_dora_band(0), "elite")

    def test_high_below_seven_days_boundary_one_day_is_high(self):
        # A boundary value lands in the lower tier: exactly one day is `high`.
        self.assertEqual(metrics.lead_time_dora_band(self.DAY), "high")
        self.assertEqual(metrics.lead_time_dora_band(self.WEEK - 1), "high")

    def test_medium_below_thirty_days_boundary_seven_days_is_medium(self):
        self.assertEqual(metrics.lead_time_dora_band(self.WEEK), "medium")
        self.assertEqual(metrics.lead_time_dora_band(self.MONTH - 1), "medium")

    def test_low_at_or_beyond_thirty_days(self):
        self.assertEqual(metrics.lead_time_dora_band(self.MONTH), "low")
        self.assertEqual(metrics.lead_time_dora_band(self.MONTH * 3), "low")

    def test_none_median_yields_no_tier(self):
        self.assertIsNone(metrics.lead_time_dora_band(None))


class ThroughputTrendTest(unittest.TestCase):
    def test_none_under_five_weeks_of_history(self):
        self.assertIsNone(metrics.throughput_trend([]))
        self.assertIsNone(metrics.throughput_trend([1, 2, 3, 4]))

    def test_up_when_recent_four_exceed_preceding_four(self):
        # last four sum 10, preceding four sum 4.
        self.assertEqual(
            metrics.throughput_trend([1, 1, 1, 1, 2, 3, 2, 3]), "up")

    def test_down_when_recent_four_below_preceding_four(self):
        self.assertEqual(
            metrics.throughput_trend([3, 3, 3, 3, 1, 1, 1, 1]), "down")

    def test_flat_when_recent_four_equal_preceding_four(self):
        self.assertEqual(
            metrics.throughput_trend([2, 2, 2, 2, 2, 2, 2, 2]), "flat")

    def test_five_weeks_compares_last_four_against_the_single_preceding(self):
        # Exactly five weeks: last four (2+2+2+2=8) vs the preceding one (1).
        self.assertEqual(metrics.throughput_trend([1, 2, 2, 2, 2]), "up")


class StatBlockTest(unittest.TestCase):
    def test_carries_median_percentiles_and_count_but_no_mean(self):
        block = metrics.stat_block([1, 2, 3, 4, 100])
        self.assertEqual(
            set(block), {"median", "p50", "p85", "p95", "n"})
        self.assertNotIn("mean", block)
        self.assertEqual(block["n"], 5)
        # Median is outlier-robust; a bare mean (22) would not be.
        self.assertEqual(block["median"], 3)

    def test_empty_sample(self):
        block = metrics.stat_block([])
        self.assertEqual(block["n"], 0)
        self.assertIsNone(block["median"])
        self.assertIsNone(block["p50"])
        self.assertNotIn("mean", block)


# ---------------------------------------------------------------------------
# 1aa. Monte-Carlo forecast simulation core (delivery-metrics delivery-forecast)
# ---------------------------------------------------------------------------

class DailyThroughputTest(unittest.TestCase):
    def _events(self, *dates):
        return [{"ship_ts": d} for d in dates]

    def test_zero_fills_from_first_ship_through_now(self):
        events = self._events(
            dt.datetime(2026, 7, 1, 9, 0, tzinfo=UTC),
            dt.datetime(2026, 7, 1, 18, 0, tzinfo=UTC),
            dt.datetime(2026, 7, 3, 12, 0, tzinfo=UTC))
        counts = metrics.daily_throughput(
            events, dt.datetime(2026, 7, 3, 23, 0, tzinfo=UTC))
        # Jul 1 (2 ships) · Jul 2 (zero-filled gap) · Jul 3 (1 ship).
        self.assertEqual(counts, [2, 0, 1])

    def test_now_extends_the_tail_with_zero_days(self):
        events = self._events(dt.datetime(2026, 7, 1, tzinfo=UTC))
        counts = metrics.daily_throughput(
            events, dt.datetime(2026, 7, 5, tzinfo=UTC))
        self.assertEqual(counts, [1, 0, 0, 0, 0])

    def test_none_ship_ts_is_ignored(self):
        events = [{"ship_ts": None},
                  {"ship_ts": dt.datetime(2026, 7, 2, tzinfo=UTC)}]
        counts = metrics.daily_throughput(
            events, dt.datetime(2026, 7, 2, tzinfo=UTC))
        self.assertEqual(counts, [1])

    def test_no_dated_events_is_empty(self):
        self.assertEqual(
            metrics.daily_throughput([], dt.datetime(2026, 7, 3, tzinfo=UTC)),
            [])


class ForecastSimulatorTest(unittest.TestCase):
    HISTORY = [2, 0, 1, 3, 0, 1, 2, 1, 0, 2]  # varied daily counts

    def test_when_is_deterministic_for_a_seed(self):
        a = metrics.forecast_when(self.HISTORY, 5, runs=500, seed=7)
        b = metrics.forecast_when(self.HISTORY, 5, runs=500, seed=7)
        self.assertEqual(a, b)

    def test_how_many_is_deterministic_for_a_seed(self):
        a = metrics.forecast_how_many(self.HISTORY, 10, runs=500, seed=7)
        b = metrics.forecast_how_many(self.HISTORY, 10, runs=500, seed=7)
        self.assertEqual(a, b)

    def test_when_bands_are_non_decreasing_with_confidence(self):
        bands = metrics.forecast_when(self.HISTORY, 8, runs=2000, seed=0)
        self.assertLessEqual(bands["p50"], bands["p85"])
        self.assertLessEqual(bands["p85"], bands["p95"])

    def test_how_many_bands_are_non_increasing_with_confidence(self):
        bands = metrics.forecast_how_many(self.HISTORY, 14, runs=2000, seed=0)
        self.assertGreaterEqual(bands["p50"], bands["p85"])
        self.assertGreaterEqual(bands["p85"], bands["p95"])

    def test_empty_history_yields_none_bands(self):
        none_bands = {"p50": None, "p85": None, "p95": None}
        self.assertEqual(metrics.forecast_when([], 5), none_bands)
        self.assertEqual(metrics.forecast_how_many([], 5), none_bands)

    def test_all_zero_history_yields_none_bands_without_looping(self):
        # sum(daily_counts) == 0 short-circuits, so no run ever loops forever.
        none_bands = {"p50": None, "p85": None, "p95": None}
        self.assertEqual(metrics.forecast_when([0, 0, 0], 5), none_bands)
        self.assertEqual(metrics.forecast_how_many([0, 0, 0], 5), none_bands)

    def test_tiny_max_days_caps_a_when_run(self):
        # A large target against a thin history cannot finish within max_days;
        # every run caps at the guard, so all bands equal max_days.
        bands = metrics.forecast_when(
            [0, 0, 1], 1000, runs=200, seed=0, max_days=30)
        self.assertEqual(bands["p50"], 30)
        self.assertEqual(bands["p95"], 30)


# ---------------------------------------------------------------------------
# 1b. Summary renderer and formatting helpers (delivery-metrics metrics-cli)
# ---------------------------------------------------------------------------

class FmtDurationTest(unittest.TestCase):
    def test_seconds_minutes_hours_days(self):
        self.assertEqual(metrics._fmt_duration(42), "42s")
        self.assertEqual(metrics._fmt_duration(720), "12m")
        self.assertEqual(metrics._fmt_duration(12240), "3.4h")
        self.assertEqual(metrics._fmt_duration(181440), "2.1d")

    def test_none_is_na(self):
        self.assertEqual(metrics._fmt_duration(None), "n/a")


class FmtTokensTest(unittest.TestCase):
    def test_units(self):
        self.assertEqual(metrics._fmt_tokens(950), "950")
        self.assertEqual(metrics._fmt_tokens(85000), "85k")
        self.assertEqual(metrics._fmt_tokens(1200000), "1.2M")

    def test_none_is_na(self):
        self.assertEqual(metrics._fmt_tokens(None), "n/a")


class FmtPctTest(unittest.TestCase):
    def test_whole_percent(self):
        self.assertEqual(metrics._fmt_pct(0.18), "18%")
        self.assertEqual(metrics._fmt_pct(0.0), "0%")

    def test_none_is_na(self):
        self.assertEqual(metrics._fmt_pct(None), "n/a")


def _sample_metrics(per_week_counts=(1, 1, 1, 1, 2, 3, 2, 3)):
    """A derive-shaped dict for renderer tests; ``per_week_counts`` drives the
    throughput weeks so tests can flex the trend segment."""
    per_week = [{"week": "2026-W%02d" % (23 + i), "count": c}
                for i, c in enumerate(per_week_counts)]
    return {
        "generated_at": "2026-07-10T00:00:00+00:00",
        "throughput": {"per_week": per_week, "total": sum(per_week_counts)},
        "deployment_days": {
            "per_week": [
                {"week": "2026-W27", "count": 1},
                {"week": "2026-W28", "count": 2},
                {"week": "2026-W29", "count": 1},
                {"week": "2026-W30", "count": 2},
            ],
            "dora_band": "weekly",
        },
        "lead_time": {"median": 86400, "p50": 86400, "p85": 172800,
                      "p95": 172800, "n": 5},
        "cycle_time": {"median": 720, "p50": 720, "p85": 3000,
                       "p95": 3000, "n": 6},
        "wip": {"by_state": {"ready": 3, "active": 1, "draft": 3},
                "items": [], "aging": {"n": 0}},
        "outcomes": {"counts": {"shipped": 8, "rejected": 1, "needs_human": 1,
                                "skipped": 0},
                     "rework_rate": 0.18},
        "change_failures": {"rate": 0.1, "n_failed": 1, "n_shipped": 10,
                            "failed": [{"slug": "a", "signals": [
                                {"kind": "revert", "ts": "2026-07-01T00:00:00"}]}]},
        "cost": {"tokens_output": {"total": 85000, "median": 950},
                 "seconds": {"total": 12240, "median": 720}},
    }


class RenderSummaryLinesTest(unittest.TestCase):
    def _render(self, **kw):
        return metrics.render_summary_lines(_sample_metrics(**kw))

    def test_header_names_the_generated_date(self):
        self.assertEqual(self._render()[0], "delivery metrics — 2026-07-10")

    def _line(self, lines, prefix):
        for line in lines:
            if line.startswith(prefix):
                return line
        self.fail("no line starting with %r in %r" % (prefix, lines))

    def test_throughput_total_last_four_and_trend_up(self):
        line = self._line(self._render(), "throughput:")
        # total 14, last four weeks 2 3 2 3, recent 4 (10) > preceding 4 (4).
        self.assertIn("14 shipped", line)
        self.assertIn("last 4 weeks: 2 3 2 3", line)
        self.assertIn("trend ↑", line)

    def test_trend_down_when_recent_below_preceding(self):
        line = self._line(
            self._render(per_week_counts=(3, 3, 3, 3, 1, 1, 1, 1)),
            "throughput:")
        self.assertIn("trend ↓", line)

    def test_trend_flat_when_equal(self):
        line = self._line(
            self._render(per_week_counts=(2, 2, 2, 2, 2, 2, 2, 2)),
            "throughput:")
        self.assertIn("trend →", line)

    def test_trend_omitted_under_five_weeks(self):
        line = self._line(
            self._render(per_week_counts=(1, 2, 3, 4)), "throughput:")
        self.assertNotIn("trend", line)
        self.assertIn("last 4 weeks: 1 2 3 4", line)

    def test_deployment_frequency_band_and_recent_days(self):
        line = self._line(self._render(), "deployment frequency:")
        self.assertIn("weekly", line)
        self.assertIn("deployment-days last 4 weeks: 1 2 1 2", line)

    def test_lead_and_cycle_show_median_p85_and_n_never_mean(self):
        lines = self._render()
        lead = self._line(lines, "lead time:")
        cycle = self._line(lines, "cycle time:")
        self.assertIn("median 1.0d", lead)
        self.assertIn("p85 2.0d", lead)
        self.assertIn("(n=5)", lead)
        self.assertIn("median 12m", cycle)
        self.assertIn("(n=6)", cycle)
        self.assertNotIn("mean", "\n".join(lines))

    def test_rework_rate_percentage_with_proxy_label(self):
        line = self._line(self._render(), "rework rate:")
        self.assertIn("18%", line)
        self.assertIn("pre-merge proxy: rejected + needs-human", line)

    def test_change_fail_rate_line_labelled_post_merge(self):
        line = self._line(self._render(), "change-fail rate:")
        self.assertIn("10%", line)
        self.assertIn("post-merge: reverts + declared fixes", line)

    def test_wip_by_state_count_descending_then_name(self):
        line = self._line(self._render(), "wip:")
        # total 7 in flight; ties (draft 3, ready 3) break by name asc.
        self.assertEqual(
            line, "wip: 7 in flight — draft 3 · ready 3 · active 1")

    def test_cost_totals_and_per_change_medians(self):
        line = self._line(self._render(), "cost:")
        self.assertIn("85k output tokens", line)
        self.assertIn("median 950/change", line)
        self.assertIn("3.4h wall-clock", line)
        self.assertIn("median 12m/change", line)

    def test_all_empty_derive_renders_na_without_raising(self):
        empty = {
            "generated_at": "2026-01-01T00:00:00+00:00",
            "throughput": {"per_week": [], "total": 0},
            "deployment_days": {"per_week": [], "dora_band": "yearly"},
            "lead_time": {"median": None, "p50": None, "p85": None,
                          "p95": None, "n": 0},
            "cycle_time": {"median": None, "p50": None, "p85": None,
                           "p95": None, "n": 0},
            "wip": {"by_state": {}, "items": [], "aging": {"n": 0}},
            "outcomes": {"counts": {"shipped": 0, "rejected": 0,
                                    "needs_human": 0, "skipped": 0},
                         "rework_rate": None},
            "cost": {"tokens_output": {"total": 0, "median": None},
                     "seconds": {"total": 0, "median": None}},
        }
        lines = metrics.render_summary_lines(empty)  # must not raise
        text = "\n".join(lines)
        self.assertIn("wip: none", text)
        self.assertIn("rework rate: n/a", text)
        self.assertIn("change-fail rate: n/a", text)
        self.assertIn("n/a", self._line(lines, "lead time:"))


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def _write_json(path, obj):
    _write(path, json.dumps(obj))


class _Fixture:
    """A temp fixture root with an ``.shipd/`` content tree and a separate build
    log directory (so no test ever touches ``~``)."""

    def __init__(self):
        self.tmp = tempfile.mkdtemp()
        self.root = os.path.join(self.tmp, "repo")
        self.log_dir = os.path.join(self.tmp, "buildlog")
        os.makedirs(os.path.join(self.root, ".shipd"))
        os.makedirs(self.log_dir)

    @property
    def config(self):
        return {"log_dir": self.log_dir}

    def shipd(self, *parts):
        return os.path.join(self.root, ".shipd", *parts)

    def cleanup(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# 2. Event collection: log, archives, outcomes, WIP
# ---------------------------------------------------------------------------

class CollectShipEventsTest(unittest.TestCase):
    def setUp(self):
        self.fx = _Fixture()
        self.addCleanup(self.fx.cleanup)
        # Build log records change `a` (with cost fields) plus a malformed line.
        lines = [
            json.dumps({
                "timestamp": "2026-07-02T10:00:00Z",
                "change": "a",
                "tasks": {"done": 5, "total": 5},
                "status": "verified",
                "tokens": {"totals": {"output": 1000}},
                "time": {"total_seconds": 200.0},
            }),
            "this is not json {{{",
            "",
        ]
        _write(os.path.join(self.fx.log_dir, "builds.jsonl"),
               "\n".join(lines) + "\n")
        # completed/ archives for `a` (also in the log) and `b` (log-missing).
        os.makedirs(self.fx.shipd("completed", "2026-07-01-a"))
        os.makedirs(self.fx.shipd("completed", "2026-06-15-b"))

    def _by_slug(self):
        events = metrics.collect_ship_events(self.fx.root, config=self.fx.config)
        return {e["slug"]: e for e in events}

    def test_log_and_archive_union_each_change_once(self):
        by_slug = self._by_slug()
        self.assertEqual(set(by_slug), {"a", "b"})

    def test_log_entry_wins_and_carries_cost_fields(self):
        a = self._by_slug()["a"]
        self.assertEqual(a["ship_ts"],
                         dt.datetime(2026, 7, 2, 10, 0, tzinfo=UTC))
        self.assertEqual(a["tokens_output"], 1000)
        self.assertEqual(a["seconds"], 200.0)
        self.assertEqual(a["tasks"], 5)

    def test_archive_only_change_carries_date_fallback(self):
        b = self._by_slug()["b"]
        self.assertEqual(b["ship_ts"],
                         dt.datetime(2026, 6, 15, 0, 0, tzinfo=UTC))
        self.assertIsNone(b["tokens_output"])
        self.assertIsNone(b["seconds"])

    def test_malformed_line_is_skipped_not_fatal(self):
        # setUp's builds.jsonl has a garbage line; collection still succeeds.
        self.assertEqual(len(self._by_slug()), 2)


class CollectOutcomesTest(unittest.TestCase):
    def setUp(self):
        self.fx = _Fixture()
        self.addCleanup(self.fx.cleanup)
        _write_json(self.fx.shipd("autopilot", "epic1-report.json"), {
            "epic": "epic1",
            "shipped": [{"member": "s1", "pr_url": "u1"}],
            "rejected": [{"member": "r1", "stage": "gate", "reason": "x"}],
            "needs_human": [{"member": "n1", "stage": "build", "reason": "y"}],
            "skipped": [{"member": "k1", "state": "ready"}],
        })
        _write_json(self.fx.shipd("autopilot", "epic2-report.json"), {
            "epic": "epic2",
            "shipped": [{"member": "s2"}, {"member": "s3"}],
            "rejected": [],
            "needs_human": [{"member": "n2", "stage": "gate", "reason": "z"}],
            "skipped": [],
        })

    def test_counts_fold_across_all_reports(self):
        out = metrics.collect_outcomes(self.fx.root)
        self.assertEqual(out["counts"], {
            "shipped": 3, "rejected": 1, "needs_human": 2, "skipped": 1})

    def test_per_member_lists_exposed(self):
        out = metrics.collect_outcomes(self.fx.root)
        self.assertEqual(set(out["shipped"]), {"s1", "s2", "s3"})
        self.assertEqual(out["rejected"], ["r1"])
        self.assertEqual(set(out["needs_human"]), {"n1", "n2"})
        self.assertEqual(out["skipped"], ["k1"])

    def test_no_reports_is_all_zero(self):
        fx = _Fixture()
        self.addCleanup(fx.cleanup)
        out = metrics.collect_outcomes(fx.root)
        self.assertEqual(out["counts"], {
            "shipped": 0, "rejected": 0, "needs_human": 0, "skipped": 0})


class CollectWipTest(unittest.TestCase):
    EPIC = (
        "# e1\n"
        "Status: active\n\n"
        "## Changes\n\n"
        "| Change | Description | Risk |\n"
        "| --- | --- | --- |\n"
        "| m_ready | ready one | low |\n"
        "| m_shipped | shipped one | low |\n"
        "| m_unplanned | not started | low |\n"
        "| m_building | no status yet | low |\n"
    )

    def setUp(self):
        self.fx = _Fixture()
        self.addCleanup(self.fx.cleanup)
        _write(self.fx.shipd("epics", "e1", "epic.md"), self.EPIC)
        # m_ready: planned with a readable status -> in-flight, age from plan.md.
        _write(self.fx.shipd("planned", "m_ready", "plan.md"),
               "# m_ready\nStatus: ready\n")
        # m_shipped: a completed archive -> exited, excluded from WIP.
        os.makedirs(self.fx.shipd("completed", "2026-07-01-m_shipped"))
        # m_building: a planned dir with no plan.md -> in-flight, no age evidence.
        os.makedirs(self.fx.shipd("planned", "m_building"))
        # m_unplanned: nothing on disk -> not entered, excluded.
        self.now = dt.datetime(2030, 1, 1, tzinfo=UTC)

    def test_only_in_flight_members_counted_by_state(self):
        wip = metrics.collect_wip(self.fx.root, self.now)
        # ready is in-flight; unplanned + archived are excluded.
        self.assertEqual(wip["by_state"].get("ready"), 1)
        self.assertNotIn("unplanned", wip["by_state"])
        self.assertNotIn("archived", wip["by_state"])
        slugs = {item["slug"] for item in wip["items"]}
        self.assertEqual(slugs, {"m_ready", "m_building"})

    def test_member_with_no_age_evidence_carries_no_fabricated_age(self):
        wip = metrics.collect_wip(self.fx.root, self.now)
        by_slug = {item["slug"]: item for item in wip["items"]}
        self.assertIsNone(by_slug["m_building"]["age_days"])
        # m_ready has a plan.md, so its age is a real non-negative number.
        self.assertIsInstance(by_slug["m_ready"]["age_days"], (int, float))
        self.assertGreaterEqual(by_slug["m_ready"]["age_days"], 0)

    def test_aging_summary_excludes_ageless_members(self):
        wip = metrics.collect_wip(self.fx.root, self.now)
        # Only m_ready contributes an age; m_building (age None) is excluded.
        self.assertEqual(wip["aging"]["n"], 1)


class EpicRemainingTest(unittest.TestCase):
    EPIC = (
        "# e1\n"
        "Status: active\n\n"
        "## Changes\n\n"
        "| Change | Description | Risk |\n"
        "| --- | --- | --- |\n"
        "| m_ready | planned | low |\n"
        "| m_unplanned | not started | low |\n"
        "| m_archived | shipped | low |\n"
    )

    def setUp(self):
        self.fx = _Fixture()
        self.addCleanup(self.fx.cleanup)
        _write(self.fx.shipd("epics", "e1", "epic.md"), self.EPIC)
        # m_ready: an in-flight (non-archived) member.
        _write(self.fx.shipd("planned", "m_ready", "plan.md"),
               "# m_ready\nStatus: ready\n")
        # m_archived: a completed/ archive -> archived (excluded).
        os.makedirs(self.fx.shipd("completed", "2026-07-01-m_archived"))
        # m_unplanned: nothing on disk -> unplanned (still remaining).

    def test_returns_sorted_non_archived_members_including_unplanned(self):
        self.assertEqual(
            metrics.epic_remaining(self.fx.root, "e1"),
            ["m_ready", "m_unplanned"])

    def test_excludes_archived_members(self):
        self.assertNotIn("m_archived",
                         metrics.epic_remaining(self.fx.root, "e1"))

    def test_missing_epic_returns_none(self):
        self.assertIsNone(metrics.epic_remaining(self.fx.root, "nope"))


class MemberStateAndLocationTest(unittest.TestCase):
    """``_member_state_and_location`` delegates to
    ``spec_status._member_state_with_root``, which probes the invocation root
    first, then each ``.worktrees/<name>`` directory — so a member whose
    change lives only under a worktree checkout is reported at that worktree's
    path, never at the invocation root (metrics-dashboard-parity)."""

    def setUp(self):
        self.fx = _Fixture()
        self.addCleanup(self.fx.cleanup)

    def test_worktree_hosted_member_reports_worktree_location(self):
        wt_root = os.path.join(self.fx.root, ".worktrees", "mem")
        _write(os.path.join(wt_root, ".shipd", "planned", "mem", "plan.md"),
               "# mem\nStatus: rejected\n\n## Idea\nx\n"
               "### Motivation\nx\n### Details\nx\n### Non-goals\n- x\n"
               "## Implementation\nx\n")
        state, location = metrics._member_state_and_location(
            self.fx.root, "mem")
        self.assertEqual(state, "rejected")
        self.assertEqual(location, os.path.abspath(wt_root))

    def test_root_hosted_member_reports_root_location(self):
        _write(self.fx.shipd("planned", "mem", "plan.md"),
               "# mem\nStatus: ready\n")
        state, location = metrics._member_state_and_location(
            self.fx.root, "mem")
        self.assertEqual(state, "ready")
        self.assertEqual(location, os.path.abspath(self.fx.root))


class GitChangeTimesTest(unittest.TestCase):
    def setUp(self):
        self.repo = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(
            self.repo, ignore_errors=True))
        self._git("init", "-q")
        self._git("config", "user.email", "t@example.com")
        self._git("config", "user.name", "Tester")

    def _git(self, *args, env=None):
        subprocess.run(["git", "-C", self.repo, *args], check=True,
                       env=env, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)

    def _commit(self, subject, author_date, committer_date):
        env = dict(os.environ,
                   GIT_AUTHOR_DATE=author_date,
                   GIT_COMMITTER_DATE=committer_date)
        self._git("commit", "--allow-empty", "-m", subject, env=env)

    def test_resolves_first_commit_from_parent_and_merge_from_commit(self):
        # The matched squash commit's committer date is the merge timestamp; its
        # first parent's committer date is the first-commit timestamp — so the
        # change's lead time is merge − parent, even though a squash collapses
        # the commit's own author/committer dates onto the merge moment.
        self._commit("other: unrelated work",
                     "2026-02-01T00:00:00+00:00", "2026-02-01T00:00:00+00:00")
        self._commit("slug-a: implement the thing",
                     "2026-02-05T00:00:00+00:00", "2026-02-05T00:00:00+00:00")
        first_commit, merge = metrics.git_change_times(self.repo, "slug-a")
        self.assertEqual(first_commit,
                         dt.datetime(2026, 2, 1, tzinfo=UTC))
        self.assertEqual(merge, dt.datetime(2026, 2, 5, tzinfo=UTC))

    def test_parentless_root_commit_does_not_resolve(self):
        # The `<slug>:` commit is the repo's root (no first parent) -> no
        # first-commit timestamp, so the pair does not resolve.
        self._commit("slug-a: the very first commit",
                     "2026-02-05T00:00:00+00:00", "2026-02-05T00:00:00+00:00")
        self.assertEqual(
            metrics.git_change_times(self.repo, "slug-a"), (None, None))

    def test_returns_nones_when_no_subject_matches(self):
        self._commit("root: base commit",
                     "2026-01-01T00:00:00+00:00", "2026-01-01T00:00:00+00:00")
        self._commit("other: unrelated work",
                     "2026-01-02T00:00:00+00:00", "2026-01-02T00:00:00+00:00")
        self.assertEqual(
            metrics.git_change_times(self.repo, "slug-a"), (None, None))

    def test_prefix_match_is_anchored_to_slug_colon(self):
        # A subject merely containing the slug (not `slug-a:` at the start)
        # does not match.
        self._commit("root: base commit",
                     "2026-01-01T00:00:00+00:00", "2026-01-01T00:00:00+00:00")
        self._commit("chore: touch slug-a config",
                     "2026-01-02T00:00:00+00:00", "2026-01-02T00:00:00+00:00")
        self.assertEqual(
            metrics.git_change_times(self.repo, "slug-a"), (None, None))

    def test_no_git_repo_returns_nones(self):
        empty = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(
            empty, ignore_errors=True))
        self.assertEqual(
            metrics.git_change_times(empty, "slug-a"), (None, None))


# ---------------------------------------------------------------------------
# 2b. Change-failure signal sources (delivery-metrics change-failure-signal)
# ---------------------------------------------------------------------------

class GitRevertSignalsTest(unittest.TestCase):
    def setUp(self):
        self.repo = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(
            self.repo, ignore_errors=True))
        self._git("init", "-q")
        self._git("config", "user.email", "t@example.com")
        self._git("config", "user.name", "Tester")

    def _git(self, *args, env=None):
        subprocess.run(["git", "-C", self.repo, *args], check=True,
                       env=env, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)

    def _commit(self, subject, committer_date):
        env = dict(os.environ,
                   GIT_AUTHOR_DATE=committer_date,
                   GIT_COMMITTER_DATE=committer_date)
        self._git("commit", "--allow-empty", "-m", subject, env=env)

    def test_revert_subject_maps_slug_to_committer_ts(self):
        # A `Revert "<slug>: ..."` subject signals a revert of <slug>, keyed by
        # the quoted `<slug>:` prefix, valued the revert commit's UTC ISO
        # committer timestamp.
        self._commit("a: ship the widget",
                     "2026-02-01T00:00:00+00:00")
        self._commit('Revert "a: ship the widget"',
                     "2026-03-01T00:00:00+00:00")
        signals = metrics.git_revert_signals(self.repo)
        self.assertEqual(
            signals, {"a": [dt.datetime(2026, 3, 1, tzinfo=UTC).isoformat()]})

    def test_revert_of_revert_is_excluded(self):
        # A revert-of-revert (quoted text itself starting `Revert `) re-lands a
        # change; it must never count as a failure signal.
        self._commit("a: ship the widget",
                     "2026-02-01T00:00:00+00:00")
        self._commit('Revert "Revert "a: ship the widget""',
                     "2026-03-01T00:00:00+00:00")
        self.assertEqual(metrics.git_revert_signals(self.repo), {})

    def test_non_repository_root_returns_empty(self):
        empty = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(
            empty, ignore_errors=True))
        self.assertEqual(metrics.git_revert_signals(empty), {})


class CollectFixLinksTest(unittest.TestCase):
    def setUp(self):
        self.fx = _Fixture()
        self.addCleanup(self.fx.cleanup)
        # A shipped fix declaring two Fixes lines → fixes both `a` and `b`.
        _write(self.fx.shipd("completed", "2026-07-01-fixer", "plan.md"),
               "# fixer\nStatus: complete\nFixes: a\nFixes: b\n")
        # A shipped change with no Fixes key → contributes no link.
        _write(self.fx.shipd("completed", "2026-06-01-plain", "plan.md"),
               "# plain\nStatus: complete\nTheme: reliability\n")

    def test_collects_fixed_slug_to_fixing_slugs(self):
        links = metrics.collect_fix_links(self.fx.root)
        self.assertEqual(links, {"a": ["fixer"], "b": ["fixer"]})

    def test_archive_without_fixes_key_is_skipped(self):
        links = metrics.collect_fix_links(self.fx.root)
        self.assertNotIn("plain", links)
        self.assertNotIn("reliability", links)


class CollectChangeFailuresTest(unittest.TestCase):
    TS_A = "2026-03-01T00:00:00+00:00"
    TS_GHOST = "2026-03-02T00:00:00+00:00"

    def setUp(self):
        self.fx = _Fixture()
        self.addCleanup(self.fx.cleanup)
        # A shipped fix declaring `Fixes: a` and `Fixes: b`.
        _write(self.fx.shipd("completed", "2026-07-01-fixer", "plan.md"),
               "# fixer\nStatus: complete\nFixes: a\nFixes: b\n")
        # Revert signals (monkeypatched): `a` is also reverted; `ghost` is
        # reverted but never shipped and so must be ignored.
        self._real_git = metrics.git_revert_signals
        metrics.git_revert_signals = lambda root, base_ref=None: {
            "a": [self.TS_A], "ghost": [self.TS_GHOST]}
        self.addCleanup(
            lambda: setattr(metrics, "git_revert_signals", self._real_git))
        self.ships = [{"slug": "a"}, {"slug": "b"}, {"slug": "c"}]

    def _collect(self, ships=None):
        return metrics.collect_change_failures(
            self.fx.root, self.ships if ships is None else ships)

    def _by_slug(self, result):
        return {f["slug"]: f for f in result["failed"]}

    def test_reverted_and_fix_declared_changes_appear_with_signals(self):
        result = self._collect()
        by_slug = self._by_slug(result)
        # `a`: reverted → a revert signal carrying the commit ts.
        self.assertIn({"kind": "revert", "ts": self.TS_A},
                      by_slug["a"]["signals"])
        # `b`: only a declared fix → a fix signal naming the fixing change.
        self.assertEqual(by_slug["b"]["signals"], [{"kind": "fix", "by": "fixer"}])

    def test_a_change_with_both_signals_counts_once(self):
        result = self._collect()
        by_slug = self._by_slug(result)
        # `a` carries both a revert and a declared fix, but counts once.
        self.assertEqual(result["n_failed"], 2)  # a and b, not c
        self.assertIn({"kind": "revert", "ts": self.TS_A},
                      by_slug["a"]["signals"])
        self.assertIn({"kind": "fix", "by": "fixer"}, by_slug["a"]["signals"])

    def test_unknown_slug_revert_is_ignored(self):
        result = self._collect()
        self.assertNotIn("ghost", self._by_slug(result))

    def test_failed_is_sorted_by_slug(self):
        result = self._collect()
        self.assertEqual([f["slug"] for f in result["failed"]], ["a", "b"])

    def test_rate_is_failed_over_shipped(self):
        result = self._collect()
        self.assertEqual(result["n_shipped"], 3)
        self.assertEqual(result["rate"], 2 / 3)

    def test_empty_ship_events_yields_none_rate(self):
        result = self._collect(ships=[])
        self.assertIsNone(result["rate"])
        self.assertEqual(result["n_shipped"], 0)
        self.assertEqual(result["n_failed"], 0)
        self.assertEqual(result["failed"], [])


# ---------------------------------------------------------------------------
# 3. The derive() entry point
# ---------------------------------------------------------------------------

def _tree_snapshot(root):
    """Every path under ``root`` — used to assert derive() writes nothing."""
    out = set()
    for dirpath, dirnames, filenames in os.walk(root):
        for name in dirnames + filenames:
            out.add(os.path.join(dirpath, name))
    return out


class DeriveTest(unittest.TestCase):
    def setUp(self):
        self.fx = _Fixture()
        self.addCleanup(self.fx.cleanup)
        # Two ship events in one ISO week, both with cost fields.
        log = [
            json.dumps({
                "timestamp": "2026-07-01T09:00:00Z", "change": "alpha",
                "tasks": {"done": 3, "total": 3}, "status": "verified",
                "tokens": {"totals": {"output": 1000}},
                "time": {"total_seconds": 300.0},
            }),
            json.dumps({
                "timestamp": "2026-07-03T09:00:00Z", "change": "beta",
                "tasks": {"done": 7, "total": 7}, "status": "verified",
                "tokens": {"totals": {"output": 3000}},
                "time": {"total_seconds": 900.0},
            }),
        ]
        _write(os.path.join(self.fx.log_dir, "builds.jsonl"),
               "\n".join(log) + "\n")
        # An epic with one in-flight member for the WIP block.
        _write(self.fx.shipd("epics", "e1", "epic.md"),
               "# e1\nStatus: active\n\n## Changes\n\n"
               "| Change | Description | Risk |\n| --- | --- | --- |\n"
               "| m1 | in flight | low |\n")
        _write(self.fx.shipd("planned", "m1", "plan.md"),
               "# m1\nStatus: ready\n")
        # An autopilot report for the outcome block.
        _write_json(self.fx.shipd("autopilot", "e1-report.json"), {
            "epic": "e1",
            "shipped": [{"member": "alpha"}],
            "rejected": [{"member": "x", "stage": "gate", "reason": "r"}],
            "needs_human": [],
            "skipped": [],
        })
        self.now = dt.datetime(2026, 7, 10, tzinfo=UTC)

        # Only alpha's git timestamps resolve; beta's do not.
        def fake_git(root, slug, base_ref=None):
            if slug == "alpha":
                return (dt.datetime(2026, 6, 30, tzinfo=UTC),
                        dt.datetime(2026, 7, 1, 9, 0, tzinfo=UTC))
            return (None, None)

        self._real_git = metrics.git_change_times
        metrics.git_change_times = fake_git
        self.addCleanup(
            lambda: setattr(metrics, "git_change_times", self._real_git))

    def _derive(self):
        return metrics.derive(self.fx.root, now=self.now, config=self.fx.config)

    def test_result_is_json_serializable_with_all_blocks(self):
        result = self._derive()
        json.dumps(result)  # must not raise
        for key in ("throughput", "deployment_days", "lead_time",
                    "cycle_time", "wip", "outcomes", "cost"):
            self.assertIn(key, result)

    def test_deployment_days_carry_a_dora_band(self):
        self.assertIn("dora_band", self._derive()["deployment_days"])

    def test_throughput_counts_both_ships(self):
        self.assertEqual(self._derive()["throughput"]["total"], 2)

    def test_lead_and_cycle_report_percentiles_never_a_mean(self):
        result = self._derive()
        for key in ("lead_time", "cycle_time"):
            block = result[key]
            self.assertEqual(
                set(block), {"median", "p50", "p85", "p95", "n"})
            self.assertNotIn("mean", block)

    def test_lead_time_excludes_unresolved_git_change(self):
        # alpha resolves, beta does not -> the lead-time sample is just alpha.
        self.assertEqual(self._derive()["lead_time"]["n"], 1)

    def test_cycle_time_uses_both_build_elapsed_samples(self):
        self.assertEqual(self._derive()["cycle_time"]["n"], 2)

    def test_cost_totals_and_medians(self):
        cost = self._derive()["cost"]
        self.assertEqual(cost["tokens_output"]["total"], 4000)
        self.assertEqual(cost["seconds"]["total"], 1200.0)
        self.assertEqual(cost["tokens_output"]["median"], 2000)

    def test_wip_reflects_in_flight_member(self):
        self.assertEqual(self._derive()["wip"]["by_state"].get("ready"), 1)

    def test_outcomes_fold_the_report(self):
        counts = self._derive()["outcomes"]["counts"]
        self.assertEqual(counts["shipped"], 1)
        self.assertEqual(counts["rejected"], 1)

    def test_change_failures_block_present_and_serializable(self):
        block = self._derive()["change_failures"]
        json.dumps(block)  # must not raise
        for key in ("rate", "n_failed", "n_shipped", "failed"):
            self.assertIn(key, block)

    def test_change_failures_none_rate_on_empty_root(self):
        fx = _Fixture()
        self.addCleanup(fx.cleanup)
        result = metrics.derive(fx.root, now=self.now, config=fx.config)
        self.assertIn("change_failures", result)
        self.assertIsNone(result["change_failures"]["rate"])

    def test_derive_writes_no_file_and_prints_nothing(self):
        import contextlib
        import io
        before = _tree_snapshot(self.fx.root)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self._derive()
        self.assertEqual(_tree_snapshot(self.fx.root), before)
        self.assertEqual(buf.getvalue(), "")


class EpicDiscoveryScopeTest(unittest.TestCase):
    """Metrics enumerates its epics through the engine's shared worktree-aware
    discovery seam — the same ``all_epic_slugs_with_roots`` the status CLI and
    the dashboard consume — so a worktree-authored epic counts exactly as a
    root-hosted one does (delivery-metrics metrics-engine). The seam it never
    consumes is the workspace-universe one: metric semantics stay per-repo, so
    a declared project repo's epics contribute nothing.

    Written test-first; expected to FAIL until the discovery swap lands in
    ``metrics.py`` (task 5.1)."""

    EPIC = ("# %s\nStatus: active\n\n## Changes\n\n"
            "| Change | Description | Risk |\n| --- | --- | --- |\n"
            "| %s | in flight | low |\n")

    def setUp(self):
        self.fx = _Fixture()
        self.addCleanup(self.fx.cleanup)
        self.now = dt.datetime(2030, 1, 1, tzinfo=UTC)

    def test_worktree_hosted_epic_contributes_to_the_wip_snapshot(self):
        # The epic was authored inside its own worktree and has not merged, so
        # the invocation root's content directory does not carry it at all.
        _write(os.path.join(self.fx.root, ".worktrees", "epic-e2",
                            ".shipd", "epics", "e2", "epic.md"),
               self.EPIC % ("e2", "m_wt"))
        _write(self.fx.shipd("planned", "m_wt", "plan.md"),
               "# m_wt\nStatus: ready\n")
        wip = metrics.collect_wip(self.fx.root, self.now)
        self.assertEqual(wip["by_state"].get("ready"), 1)
        self.assertEqual([item["slug"] for item in wip["items"]], ["m_wt"])

    def test_declared_project_epics_never_leak_into_derive(self):
        # `self.fx.root` doubles as the workspace root declaring `proj-a`; the
        # project's repo hosts its own epic with an in-flight member.
        _write(os.path.join(self.fx.root, ".shipd-config.json"),
               json.dumps({"workspace": {"projects": {
                   "proj-a": {"repos": [{"path": "proj-a"}]}}}}))
        repo = os.path.join(self.fx.root, "proj-a")
        _write(os.path.join(repo, ".shipd", "epics", "pe1", "epic.md"),
               self.EPIC % ("pe1", "pm1"))
        _write(os.path.join(repo, ".shipd", "planned", "pm1", "plan.md"),
               "# pm1\nStatus: ready\n")
        # The invocation root's own epic, for contrast.
        _write(self.fx.shipd("epics", "e1", "epic.md"),
               self.EPIC % ("e1", "m1"))
        _write(self.fx.shipd("planned", "m1", "plan.md"),
               "# m1\nStatus: ready\n")
        result = metrics.derive(
            self.fx.root, now=self.now, config=self.fx.config)
        self.assertEqual(result["wip"]["by_state"].get("ready"), 1)
        self.assertEqual([item["slug"] for item in result["wip"]["items"]],
                         ["m1"])
        # Nothing of the project's universe reaches any block of the result.
        self.assertNotIn("pm1", json.dumps(result))
        self.assertNotIn("pe1", json.dumps(result))


# ---------------------------------------------------------------------------
# 3b. Audience-framed rollups (delivery-metrics stakeholder-rollups)
# ---------------------------------------------------------------------------

def _seed_rollup_fixture(fx):
    """A fixture root with a multi-week, multi-day ship history (enough for a
    throughput trend and a PM forecast), two epics (one with remaining members,
    one fully archived), autopilot outcomes, and a recorded flow series."""
    # Ship events spanning more than five ISO weeks (for the throughput trend)
    # with a multi-day daily history (for the PM Monte-Carlo forecast).
    dates = [
        "2026-05-04", "2026-05-06", "2026-05-11", "2026-05-13",
        "2026-05-18", "2026-05-20", "2026-05-25", "2026-05-27",
        "2026-06-01", "2026-06-03", "2026-06-08", "2026-06-10",
        "2026-06-15", "2026-06-17", "2026-06-22", "2026-06-24",
        "2026-06-29", "2026-07-01",
    ]
    lines = [json.dumps({
        "timestamp": "%sT09:00:00Z" % d,
        "change": "ship_%02d" % i, "status": "verified",
        "tokens": {"totals": {"output": 1000}},
        "time": {"total_seconds": 300.0},
    }) for i, d in enumerate(dates)]
    _write(os.path.join(fx.log_dir, "builds.jsonl"), "\n".join(lines) + "\n")
    # e1: one archived + two remaining members → total 3, done 1, bands present.
    _write(fx.shipd("epics", "e1", "epic.md"),
           "# e1\nStatus: active\n\n## Changes\n\n"
           "| Change | Description | Risk |\n| --- | --- | --- |\n"
           "| e1_archived | shipped | low |\n"
           "| e1_ready | planned | low |\n"
           "| e1_unplanned | not started | low |\n")
    _write(fx.shipd("planned", "e1_ready", "plan.md"),
           "# e1_ready\nStatus: ready\n")
    os.makedirs(fx.shipd("completed", "2026-06-01-e1_archived"))
    # e2: a single archived member → total 1, done 1, no remaining, bands None.
    _write(fx.shipd("epics", "e2", "epic.md"),
           "# e2\nStatus: active\n\n## Changes\n\n"
           "| Change | Description | Risk |\n| --- | --- | --- |\n"
           "| e2_archived | shipped | low |\n")
    os.makedirs(fx.shipd("completed", "2026-06-02-e2_archived"))
    # Outcomes for the rework-rate headline.
    _write_json(fx.shipd("autopilot", "e1-report.json"), {
        "epic": "e1",
        "shipped": [{"member": "s1"}, {"member": "s2"}],
        "rejected": [{"member": "r1", "stage": "gate", "reason": "x"}],
        "needs_human": [],
        "skipped": [],
    })
    # Recorded flow history for the EM flow block.
    root = os.path.abspath(fx.root)
    flow_lines = [
        json.dumps({"ts": "2026-07-01T00:00:00+00:00", "root": root,
                    "states": {"draft": ["d1"]}}),
        json.dumps({"ts": "2026-07-02T00:00:00+00:00", "root": root,
                    "states": {"ready": ["d1"], "active": ["d2"]}}),
    ]
    _write(os.path.join(fx.log_dir, metrics.FLOW_LOG_FILE),
           "\n".join(flow_lines) + "\n")


class BuildRollupResultTest(unittest.TestCase):
    def setUp(self):
        self.fx = _Fixture()
        self.addCleanup(self.fx.cleanup)
        _seed_rollup_fixture(self.fx)
        # Never let a stray flow-log env var from the environment leak in.
        patch = unittest.mock.patch.dict(os.environ, {}, clear=False)
        patch.start()
        os.environ.pop("SHIPD_FLOW_LOG_DIR", None)
        os.environ.pop("AM_FLOW_LOG_DIR", None)
        self.addCleanup(patch.stop)
        self.now = dt.datetime(2026, 7, 10, tzinfo=UTC)
        # A fixed, resolvable lead time for every change → a stable exec tier
        # (12h span → below one day → elite).
        def fake_git(root, slug, base_ref=None):
            return (dt.datetime(2026, 7, 1, 0, 0, tzinfo=UTC),
                    dt.datetime(2026, 7, 1, 12, 0, tzinfo=UTC))
        self._real_git = metrics.git_change_times
        metrics.git_change_times = fake_git
        self.addCleanup(
            lambda: setattr(metrics, "git_change_times", self._real_git))

    def _build(self, audience):
        return metrics.build_rollup_result(
            self.fx.root, audience, now=self.now, config=self.fx.config)

    def test_envelope_carries_generated_at_and_audience(self):
        result = self._build("exec")
        self.assertEqual(result["audience"], "exec")
        self.assertEqual(result["generated_at"], self.now.isoformat())
        json.dumps(result)  # must be JSON-serializable

    def test_exec_block_carries_trend_dora_headlines_cost_and_no_slug(self):
        block = self._build("exec")["exec"]
        self.assertIn("throughput", block["trend"])
        self.assertEqual(block["dora"]["lead_time_tier"], "elite")
        self.assertIn("deployment_frequency", block["dora"])
        self.assertIn("shipped_total", block["headlines"])
        self.assertIn("rework_rate", block["headlines"])
        self.assertIn("tokens_output_total", block["cost"])
        self.assertIn("seconds_total", block["cost"])
        # SPACE guardrail: no change slug anywhere in the exec block's JSON.
        serialized = json.dumps(block)
        for slug in ("ship_", "e1_", "e2_", "s1", "s2", "r1", "d1"):
            self.assertNotIn(slug, serialized)

    def test_exec_headlines_carry_change_fail_rate_and_stay_slug_free(self):
        # Declare a shipped change failed via a post-merge Fixes archive.
        _write(self.fx.shipd("completed", "2026-07-05-fixer", "plan.md"),
               "# fixer\nStatus: complete\nFixes: ship_00\n")
        result = self._build("exec")
        block = result["exec"]
        self.assertIn("change_fail_rate", block["headlines"])
        self.assertGreater(block["headlines"]["change_fail_rate"], 0)
        # Neither the failed slug nor the fixing slug leaks into the exec cut's
        # JSON or its rendered lines (the exec no-slug rule).
        blob = json.dumps(block) + "\n" + "\n".join(
            metrics.render_rollup_lines(result))
        for slug in ("ship_00", "fixer"):
            self.assertNotIn(slug, blob)

    def test_pm_block_carries_throughput_and_one_entry_per_epic(self):
        block = self._build("pm")["pm"]
        self.assertIn("last_weeks", block["throughput"])
        self.assertIn("trend", block["throughput"])
        epics = {e["epic"]: e for e in block["epics"]}
        self.assertEqual(set(epics), {"e1", "e2"})
        # e1: total 3, one archived → done 1, remaining members → bands present.
        self.assertEqual(epics["e1"]["total"], 3)
        self.assertEqual(epics["e1"]["done"], 1)
        bands = epics["e1"]["bands"]
        self.assertIsNotNone(bands)
        for key in ("p50", "p85", "p95"):
            self.assertIn("days", bands[key])
            self.assertIn("date", bands[key])
        self.assertIn("caution", epics["e1"])

    def test_pm_bands_none_when_no_members_remain(self):
        epics = {e["epic"]: e for e in self._build("pm")["pm"]["epics"]}
        # e2: its only member is archived → nothing remains → no bands.
        self.assertEqual(epics["e2"]["total"], 1)
        self.assertEqual(epics["e2"]["done"], 1)
        self.assertIsNone(epics["e2"]["bands"])

    def test_pm_is_deterministic_across_two_calls(self):
        self.assertEqual(self._build("pm"), self._build("pm"))

    def test_em_block_carries_the_operational_cut(self):
        block = self._build("em")["em"]
        for key in ("median", "p50", "p85", "p95", "n"):
            self.assertIn(key, block["lead_time"])
            self.assertIn(key, block["cycle_time"])
        self.assertNotIn("mean", json.dumps(block))
        self.assertIn("by_state", block["wip"])
        self.assertIsInstance(block["deployment_days_last_weeks"], list)
        self.assertIn("rework_rate", block)
        self.assertEqual(block["flow"]["n"], 2)
        self.assertEqual(block["flow"]["latest_by_state"],
                         {"ready": 1, "active": 1})

    def test_empty_root_degrades_every_block_without_raising(self):
        fx = _Fixture()
        self.addCleanup(fx.cleanup)
        for audience, key in (("exec", "exec"), ("pm", "pm"), ("em", "em")):
            result = metrics.build_rollup_result(
                fx.root, audience, now=self.now, config=fx.config)
            self.assertEqual(result["audience"], audience)
            json.dumps(result)  # must not raise
        exec_block = metrics.build_rollup_result(
            fx.root, "exec", now=self.now, config=fx.config)["exec"]
        self.assertIsNone(exec_block["trend"]["throughput"])
        self.assertIsNone(exec_block["dora"]["lead_time_tier"])
        pm_block = metrics.build_rollup_result(
            fx.root, "pm", now=self.now, config=fx.config)["pm"]
        self.assertEqual(pm_block["epics"], [])
        em_block = metrics.build_rollup_result(
            fx.root, "em", now=self.now, config=fx.config)["em"]
        self.assertIsNone(em_block["lead_time"]["median"])
        self.assertEqual(em_block["flow"]["n"], 0)


# ---------------------------------------------------------------------------
# 4. The summary verb (delivery-metrics metrics-cli)
# ---------------------------------------------------------------------------

class SummaryCliTest(unittest.TestCase):
    def setUp(self):
        self.fx = _Fixture()
        self.addCleanup(self.fx.cleanup)
        # The summary verb has no config injection, so point the root's layered
        # config at the fixture log dir — no test ever reads the real
        # ~/.shipd/builds.
        _write_json(os.path.join(self.fx.root, ".shipd-config.json"),
                    {"build": {"log_dir": self.fx.log_dir}})
        log = [
            json.dumps({
                "timestamp": "2026-07-01T09:00:00Z", "change": "alpha",
                "tasks": {"done": 3, "total": 3}, "status": "verified",
                "tokens": {"totals": {"output": 1000}},
                "time": {"total_seconds": 300.0},
            }),
            json.dumps({
                "timestamp": "2026-07-03T09:00:00Z", "change": "beta",
                "tasks": {"done": 7, "total": 7}, "status": "verified",
                "tokens": {"totals": {"output": 3000}},
                "time": {"total_seconds": 900.0},
            }),
        ]
        _write(os.path.join(self.fx.log_dir, "builds.jsonl"),
               "\n".join(log) + "\n")
        _write(self.fx.shipd("epics", "e1", "epic.md"),
               "# e1\nStatus: active\n\n## Changes\n\n"
               "| Change | Description | Risk |\n| --- | --- | --- |\n"
               "| m1 | in flight | low |\n")
        _write(self.fx.shipd("planned", "m1", "plan.md"),
               "# m1\nStatus: ready\n")
        _write_json(self.fx.shipd("autopilot", "e1-report.json"), {
            "epic": "e1",
            "shipped": [{"member": "alpha"}],
            "rejected": [{"member": "x", "stage": "gate", "reason": "r"}],
            "needs_human": [],
            "skipped": [],
        })

    def _run(self, argv):
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = metrics.main(argv)
        return code, buf.getvalue()

    def test_summary_exits_zero_and_prints_lines(self):
        code, out = self._run(["summary", "--root", self.fx.root])
        self.assertEqual(code, 0)
        self.assertIn("delivery metrics —", out)
        self.assertIn("throughput:", out)
        self.assertIn("deployment frequency:", out)
        self.assertIn("lead time:", out)
        self.assertIn("cycle time:", out)
        self.assertIn("wip:", out)
        self.assertIn("cost:", out)
        self.assertNotIn("mean", out)

    def test_json_mode_prints_the_raw_derive_blocks(self):
        code, out = self._run(["summary", "--root", self.fx.root, "--json"])
        self.assertEqual(code, 0)
        data = json.loads(out)
        for key in ("throughput", "deployment_days", "lead_time",
                    "cycle_time", "wip", "outcomes", "cost"):
            self.assertIn(key, data)
        # JSON mode carries no human-readable summary lines.
        self.assertNotIn("delivery metrics —", out)

    def test_empty_root_exits_zero_with_na(self):
        fx = _Fixture()
        self.addCleanup(fx.cleanup)
        _write_json(os.path.join(fx.root, ".shipd-config.json"),
                    {"build": {"log_dir": fx.log_dir}})
        code, out = self._run(["summary", "--root", fx.root])
        self.assertEqual(code, 0)
        self.assertIn("n/a", out)
        self.assertIn("wip: none", out)

    def test_bare_import_executes_no_cli(self):
        proc = subprocess.run(
            [sys.executable, "-c", "import metrics"],
            cwd=SCRIPTS, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, "")


class SummaryCliMalformedConfigTest(unittest.TestCase):
    """A `.shipd-config.json` that is not parseable JSON is a user-facing
    failure: one `Error:` line on stderr and exit 1, never a traceback (an
    uncaught ConfigError would propagate out of main() and fail this test)."""

    def setUp(self):
        self.fx = _Fixture()
        self.addCleanup(self.fx.cleanup)
        _write(os.path.join(self.fx.root, ".shipd-config.json"), "{ not json")

    def test_malformed_config_is_one_error_line(self):
        import contextlib
        import io
        buf, errbuf = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(buf), \
                contextlib.redirect_stderr(errbuf):
            code = metrics.main(["summary", "--root", self.fx.root])
        self.assertEqual(code, 1)
        lines = errbuf.getvalue().splitlines()
        self.assertEqual(len(lines), 1, errbuf.getvalue())
        self.assertTrue(lines[0].startswith("Error: "), errbuf.getvalue())


# ---------------------------------------------------------------------------
# 5. Flow time-series capture (delivery-metrics flow-timeseries)
# ---------------------------------------------------------------------------

def _read_flow(path):
    """Every JSON record in a flow.jsonl file (in file order)."""
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


# An epic stub table holding members across every band: unplanned (nothing on
# disk), draft (planned dir, no plan.md), ready (planned dir with a status), and
# archived (a completed/ archive dir).
_FLOW_EPIC = (
    "# e1\n"
    "Status: active\n\n"
    "## Changes\n\n"
    "| Change | Description | Risk |\n"
    "| --- | --- | --- |\n"
    "| m_unplanned | not started | low |\n"
    "| m_draft | staged only | low |\n"
    "| m_ready | planned | low |\n"
    "| m_archived | shipped | low |\n"
)


def _seed_flow_bands(fx):
    """Populate ``fx`` with the _FLOW_EPIC members in their four bands."""
    _write(fx.shipd("epics", "e1", "epic.md"), _FLOW_EPIC)
    _write(fx.shipd("planned", "m_draft", "plan.md"), "# m_draft\nStatus: draft\n")
    _write(fx.shipd("planned", "m_ready", "plan.md"), "# m_ready\nStatus: ready\n")
    os.makedirs(fx.shipd("completed", "2026-07-01-m_archived"))


class FlowSnapshotTest(unittest.TestCase):
    def setUp(self):
        self.fx = _Fixture()
        self.addCleanup(self.fx.cleanup)
        _seed_flow_bands(self.fx)

    def test_maps_every_band_including_unplanned_and_archived(self):
        states = metrics.flow_snapshot(self.fx.root)
        self.assertEqual(states.get("unplanned"), ["m_unplanned"])
        self.assertEqual(states.get("draft"), ["m_draft"])
        self.assertEqual(states.get("ready"), ["m_ready"])
        self.assertEqual(states.get("archived"), ["m_archived"])

    def test_slug_lists_are_sorted_and_deduped(self):
        # A second epic repeats m_ready and adds m_draft2; the shared slug is
        # counted once and each state's list is sorted.
        _write(self.fx.shipd("epics", "e2", "epic.md"),
               "# e2\nStatus: active\n\n## Changes\n\n"
               "| Change | Description | Risk |\n| --- | --- | --- |\n"
               "| m_ready | dup | low |\n"
               "| m_draft2 | staged | low |\n")
        _write(self.fx.shipd("planned", "m_draft2", "plan.md"),
               "# m_draft2\nStatus: draft\n")
        states = metrics.flow_snapshot(self.fx.root)
        self.assertEqual(states.get("ready"), ["m_ready"])
        self.assertEqual(states.get("draft"), ["m_draft", "m_draft2"])


class RecordFlowTest(unittest.TestCase):
    def setUp(self):
        self.fx = _Fixture()
        self.addCleanup(self.fx.cleanup)
        _seed_flow_bands(self.fx)
        # Never let a stray flow-log env var from the environment leak in.
        self._env_patch = unittest.mock.patch.dict(
            os.environ, {}, clear=False)
        self._env_patch.start()
        os.environ.pop("SHIPD_FLOW_LOG_DIR", None)
        os.environ.pop("AM_FLOW_LOG_DIR", None)
        self.addCleanup(self._env_patch.stop)
        self.flow_path = os.path.join(self.fx.log_dir, "flow.jsonl")
        self.now = dt.datetime(2026, 7, 10, 12, 0, tzinfo=UTC)

    def test_appends_one_record_with_ts_root_and_states(self):
        record = metrics.record_flow(
            self.fx.root, config=self.fx.config, now=self.now)
        self.assertIsNotNone(record)
        self.assertEqual(record["root"], os.path.abspath(self.fx.root))
        self.assertEqual(record["ts"], self.now.isoformat())
        self.assertEqual(record["states"].get("unplanned"), ["m_unplanned"])
        self.assertEqual(record["states"].get("archived"), ["m_archived"])
        # And it landed as exactly one JSON line in flow.jsonl.
        on_disk = _read_flow(self.flow_path)
        self.assertEqual(len(on_disk), 1)
        self.assertEqual(on_disk[0], record)

    def test_dedup_skips_an_unchanged_snapshot(self):
        first = metrics.record_flow(
            self.fx.root, config=self.fx.config, now=self.now)
        self.assertIsNotNone(first)
        again = metrics.record_flow(
            self.fx.root, config=self.fx.config,
            now=self.now + dt.timedelta(hours=1))
        self.assertIsNone(again)
        self.assertEqual(len(_read_flow(self.flow_path)), 1)

    def test_a_changed_snapshot_appends_a_second_record(self):
        metrics.record_flow(self.fx.root, config=self.fx.config, now=self.now)
        # Promote m_draft to ready -> the states map changes.
        _write(self.fx.shipd("planned", "m_draft", "plan.md"),
               "# m_draft\nStatus: ready\n")
        second = metrics.record_flow(
            self.fx.root, config=self.fx.config,
            now=self.now + dt.timedelta(hours=1))
        self.assertIsNotNone(second)
        self.assertEqual(len(_read_flow(self.flow_path)), 2)

    def test_worktree_root_records_under_the_main_checkout(self):
        # A linked worktree whose .git is a file pointing into the main
        # checkout's .git/worktrees/ resolves to the main checkout.
        worktree = os.path.join(self.fx.tmp, "wt")
        os.makedirs(worktree)
        gitdir = os.path.join(self.fx.root, ".git", "worktrees", "wt")
        _write(os.path.join(worktree, ".git"), "gitdir: %s\n" % gitdir)
        record = metrics.record_flow(
            worktree, config=self.fx.config, now=self.now)
        self.assertIsNotNone(record)
        self.assertEqual(record["root"], os.path.abspath(self.fx.root))

    def test_env_seam_wins_over_config(self):
        env_dir = os.path.join(self.fx.tmp, "envlog")
        os.makedirs(env_dir)
        os.environ["AM_FLOW_LOG_DIR"] = env_dir
        metrics.record_flow(self.fx.root, config=self.fx.config, now=self.now)
        # The record went to the env dir, not the config dir.
        self.assertTrue(os.path.isfile(os.path.join(env_dir, "flow.jsonl")))
        self.assertFalse(os.path.isfile(self.flow_path))

    def test_empty_env_seam_disables_recording(self):
        os.environ["AM_FLOW_LOG_DIR"] = ""
        result = metrics.record_flow(
            self.fx.root, config=self.fx.config, now=self.now)
        self.assertIsNone(result)
        self.assertFalse(os.path.isfile(self.flow_path))


class FlowLogEnvMigrationTest(unittest.TestCase):
    """The flow-log env seam is ``SHIPD_FLOW_LOG_DIR``, with the pre-rename
    ``AM_FLOW_LOG_DIR`` still honoured as a legacy fallback."""

    def setUp(self):
        self.fx = _Fixture()
        self.addCleanup(self.fx.cleanup)
        _seed_flow_bands(self.fx)
        self._env_patch = unittest.mock.patch.dict(
            os.environ, {}, clear=False)
        self._env_patch.start()
        os.environ.pop("SHIPD_FLOW_LOG_DIR", None)
        os.environ.pop("AM_FLOW_LOG_DIR", None)
        self.addCleanup(self._env_patch.stop)
        self.config_path = os.path.join(self.fx.log_dir, "flow.jsonl")
        self.now = dt.datetime(2026, 7, 10, 12, 0, tzinfo=UTC)

    def _dir(self, name):
        path = os.path.join(self.fx.tmp, name)
        os.makedirs(path)
        return path

    def test_env_constants_carry_the_new_and_legacy_names(self):
        self.assertEqual(metrics.FLOW_LOG_ENV, "SHIPD_FLOW_LOG_DIR")
        self.assertEqual(metrics.FLOW_LOG_ENV_LEGACY, "AM_FLOW_LOG_DIR")

    def test_new_env_resolves_the_log_dir(self):
        new_dir = self._dir("shipdlog")
        os.environ["SHIPD_FLOW_LOG_DIR"] = new_dir
        self.assertEqual(
            metrics.resolve_flow_log_dir(self.fx.root, self.fx.config),
            new_dir)
        metrics.record_flow(self.fx.root, config=self.fx.config, now=self.now)
        self.assertTrue(os.path.isfile(os.path.join(new_dir, "flow.jsonl")))
        self.assertFalse(os.path.isfile(self.config_path))

    def test_legacy_env_alone_still_resolves_the_log_dir(self):
        legacy_dir = self._dir("legacylog")
        os.environ["AM_FLOW_LOG_DIR"] = legacy_dir
        self.assertEqual(
            metrics.resolve_flow_log_dir(self.fx.root, self.fx.config),
            legacy_dir)
        metrics.record_flow(self.fx.root, config=self.fx.config, now=self.now)
        self.assertTrue(os.path.isfile(os.path.join(legacy_dir, "flow.jsonl")))
        self.assertFalse(os.path.isfile(self.config_path))

    def test_new_env_wins_over_the_legacy_one(self):
        new_dir = self._dir("shipdlog")
        legacy_dir = self._dir("legacylog")
        os.environ["SHIPD_FLOW_LOG_DIR"] = new_dir
        os.environ["AM_FLOW_LOG_DIR"] = legacy_dir
        self.assertEqual(
            metrics.resolve_flow_log_dir(self.fx.root, self.fx.config),
            new_dir)
        metrics.record_flow(self.fx.root, config=self.fx.config, now=self.now)
        self.assertTrue(os.path.isfile(os.path.join(new_dir, "flow.jsonl")))
        self.assertFalse(os.path.isfile(os.path.join(legacy_dir, "flow.jsonl")))

    def test_empty_new_env_disables_recording_even_with_legacy_set(self):
        # The *winning* variable's empty string disables: an empty new var is
        # a deliberate off switch, not a fall-through to the legacy one.
        legacy_dir = self._dir("legacylog")
        os.environ["SHIPD_FLOW_LOG_DIR"] = ""
        os.environ["AM_FLOW_LOG_DIR"] = legacy_dir
        self.assertIsNone(
            metrics.resolve_flow_log_dir(self.fx.root, self.fx.config))
        self.assertIsNone(metrics.record_flow(
            self.fx.root, config=self.fx.config, now=self.now))
        self.assertFalse(os.path.isfile(os.path.join(legacy_dir, "flow.jsonl")))
        self.assertFalse(os.path.isfile(self.config_path))

    def test_empty_legacy_env_alone_disables_recording(self):
        os.environ["AM_FLOW_LOG_DIR"] = ""
        self.assertIsNone(
            metrics.resolve_flow_log_dir(self.fx.root, self.fx.config))
        self.assertIsNone(metrics.record_flow(
            self.fx.root, config=self.fx.config, now=self.now))
        self.assertFalse(os.path.isfile(self.config_path))

    def test_neither_env_falls_through_to_the_config_layers(self):
        self.assertEqual(
            metrics.resolve_flow_log_dir(self.fx.root, self.fx.config),
            self.fx.log_dir)
        metrics.record_flow(self.fx.root, config=self.fx.config, now=self.now)
        self.assertTrue(os.path.isfile(self.config_path))

    def test_cli_honours_the_new_env(self):
        new_dir = self._dir("shipdlog")
        env = dict(os.environ, SHIPD_FLOW_LOG_DIR=new_dir)
        env.pop("AM_FLOW_LOG_DIR", None)
        result = subprocess.run(
            [sys.executable, os.path.join(SCRIPTS, "metrics.py"),
             "record-flow", "--root", self.fx.root],
            cwd=SCRIPTS, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        record = json.loads(result.stdout)
        self.assertEqual(record["root"], os.path.abspath(self.fx.root))
        self.assertTrue(os.path.isfile(os.path.join(new_dir, "flow.jsonl")))


class CollectFlowTest(unittest.TestCase):
    def setUp(self):
        self.fx = _Fixture()
        self.addCleanup(self.fx.cleanup)
        # collect_flow resolves the log dir env → config, so clear a stray env.
        patch = unittest.mock.patch.dict(os.environ, {}, clear=False)
        patch.start()
        os.environ.pop("SHIPD_FLOW_LOG_DIR", None)
        os.environ.pop("AM_FLOW_LOG_DIR", None)
        self.addCleanup(patch.stop)
        self.root = os.path.abspath(self.fx.root)
        # Records for this root (out of ts order) plus another root plus a
        # malformed line, all in one flow.jsonl.
        lines = [
            json.dumps({"ts": "2026-07-02T00:00:00+00:00", "root": self.root,
                        "states": {"ready": ["m1"], "draft": ["m2", "m3"]}}),
            json.dumps({"ts": "2026-07-01T00:00:00+00:00", "root": self.root,
                        "states": {"draft": ["m1"]}}),
            json.dumps({"ts": "2026-07-01T00:00:00+00:00", "root": "/other",
                        "states": {"ready": ["x"]}}),
            "this is not json {{{",
        ]
        _write(os.path.join(self.fx.log_dir, metrics.FLOW_LOG_FILE),
               "\n".join(lines) + "\n")

    def test_filters_to_root_sorts_by_ts_and_derives_by_state(self):
        records = metrics.collect_flow(self.fx.root, config=self.fx.config)
        # Only this root's two records, sorted by ts (draft-only first).
        self.assertEqual([r["ts"] for r in records],
                         ["2026-07-01T00:00:00+00:00",
                          "2026-07-02T00:00:00+00:00"])
        self.assertEqual(records[0]["states"], {"draft": ["m1"]})
        self.assertEqual(records[0]["by_state"], {"draft": 1})
        self.assertEqual(records[1]["by_state"], {"ready": 1, "draft": 2})

    def test_missing_file_degrades_to_empty(self):
        fx = _Fixture()
        self.addCleanup(fx.cleanup)
        self.assertEqual(metrics.collect_flow(fx.root, config=fx.config), [])

    def test_non_list_states_value_is_tolerated_not_fatal(self):
        # A well-formed JSON record whose states map carries a non-sized value
        # must not raise past the OSError guard (never-fatal clause).
        fx = _Fixture()
        self.addCleanup(fx.cleanup)
        patch = unittest.mock.patch.dict(os.environ, {}, clear=False)
        patch.start()
        os.environ.pop("SHIPD_FLOW_LOG_DIR", None)
        os.environ.pop("AM_FLOW_LOG_DIR", None)
        self.addCleanup(patch.stop)
        root = os.path.abspath(fx.root)
        _write(os.path.join(fx.log_dir, metrics.FLOW_LOG_FILE),
               json.dumps({"ts": "2026-07-01T00:00:00+00:00", "root": root,
                           "states": {"draft": None, "ready": ["m1"]}}) + "\n")
        records = metrics.collect_flow(fx.root, config=fx.config)  # no raise
        # The non-list value is dropped from the count map; the list survives.
        self.assertEqual(records[0]["by_state"], {"ready": 1})
        # derive over the same corrupted record also stays non-fatal.
        result = metrics.derive(
            fx.root, now=dt.datetime(2026, 7, 10, tzinfo=UTC),
            config=fx.config)
        self.assertEqual(result["flow"]["series"][0]["by_state"], {"ready": 1})
        # A non-string ts in a further record must not make the sort raise on
        # a mixed-type comparison either.
        with open(os.path.join(fx.log_dir, metrics.FLOW_LOG_FILE), "a",
                  encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": 123, "root": root,
                                 "states": {"draft": ["m2"]}}) + "\n")
        records = metrics.collect_flow(fx.root, config=fx.config)  # no raise
        self.assertEqual(len(records), 2)


class DeriveFlowBlockTest(unittest.TestCase):
    def setUp(self):
        self.fx = _Fixture()
        self.addCleanup(self.fx.cleanup)
        patch = unittest.mock.patch.dict(os.environ, {}, clear=False)
        patch.start()
        os.environ.pop("SHIPD_FLOW_LOG_DIR", None)
        os.environ.pop("AM_FLOW_LOG_DIR", None)
        self.addCleanup(patch.stop)
        self.root = os.path.abspath(self.fx.root)
        lines = [
            json.dumps({"ts": "2026-07-01T00:00:00+00:00", "root": self.root,
                        "states": {"draft": ["m1"]}}),
            json.dumps({"ts": "2026-07-02T00:00:00+00:00", "root": self.root,
                        "states": {"ready": ["m1"]}}),
            "not json",
        ]
        _write(os.path.join(self.fx.log_dir, metrics.FLOW_LOG_FILE),
               "\n".join(lines) + "\n")
        self.now = dt.datetime(2026, 7, 10, tzinfo=UTC)

    def _derive(self):
        return metrics.derive(self.fx.root, now=self.now, config=self.fx.config)

    def test_flow_block_carries_counts_only_series_and_n(self):
        flow = self._derive()["flow"]
        self.assertEqual(flow["n"], 2)
        self.assertEqual(
            flow["series"],
            [{"ts": "2026-07-01T00:00:00+00:00", "by_state": {"draft": 1}},
             {"ts": "2026-07-02T00:00:00+00:00", "by_state": {"ready": 1}}])
        # The counts-only series carries no slug lists.
        self.assertNotIn("states", flow["series"][0])

    def test_derive_result_stays_json_serializable_with_flow(self):
        result = self._derive()
        json.dumps(result)  # must not raise
        self.assertIn("flow", result)

    def test_derive_writes_no_file_and_does_not_grow_the_flow_log(self):
        flow_path = os.path.join(self.fx.log_dir, metrics.FLOW_LOG_FILE)
        before_tree = _tree_snapshot(self.fx.root)
        with open(flow_path, encoding="utf-8") as fh:
            before_lines = len(fh.readlines())
        self._derive()
        self.assertEqual(_tree_snapshot(self.fx.root), before_tree)
        with open(flow_path, encoding="utf-8") as fh:
            self.assertEqual(len(fh.readlines()), before_lines)


class RecordFlowCliTest(unittest.TestCase):
    def setUp(self):
        self.fx = _Fixture()
        self.addCleanup(self.fx.cleanup)
        _seed_flow_bands(self.fx)
        self.flow_dir = os.path.join(self.fx.tmp, "flowlog")
        os.makedirs(self.flow_dir)

    def _run(self):
        # The legacy variable still redirects the CLI's flow log — with the
        # current one cleared so the fallback is what is under test.
        env = dict(os.environ, AM_FLOW_LOG_DIR=self.flow_dir)
        env.pop("SHIPD_FLOW_LOG_DIR", None)
        return subprocess.run(
            [sys.executable, os.path.join(SCRIPTS, "metrics.py"),
             "record-flow", "--root", self.fx.root],
            cwd=SCRIPTS, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, env=env)

    def test_first_run_prints_record_then_unchanged_on_repeat(self):
        first = self._run()
        self.assertEqual(first.returncode, 0, first.stderr)
        record = json.loads(first.stdout)
        self.assertEqual(record["root"], os.path.abspath(self.fx.root))
        self.assertEqual(record["states"].get("unplanned"), ["m_unplanned"])
        self.assertEqual(record["states"].get("archived"), ["m_archived"])
        # A repeat run with no lifecycle change dedups to `unchanged`.
        second = self._run()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(second.stdout.strip(), "unchanged")


# ---------------------------------------------------------------------------
# 6. Monte-Carlo forecast: renderer + verb (delivery-metrics delivery-forecast)
# ---------------------------------------------------------------------------

def _when_result(bands="default", caution=None, items=5):
    return {
        "generated_at": "2026-07-10T00:00:00+00:00",
        "mode": "when",
        "history": {"days": 20, "total_shipped": 15},
        "items": items,
        "runs": 100, "seed": 0,
        "bands": {
            "p50": {"days": 3, "date": "2026-07-13"},
            "p85": {"days": 5, "date": "2026-07-15"},
            "p95": {"days": 8, "date": "2026-07-18"},
        } if bands == "default" else bands,
        "caution": caution,
    }


def _how_many_result(bands="default", caution=None):
    return {
        "generated_at": "2026-07-10T00:00:00+00:00",
        "mode": "how_many",
        "history": {"days": 20, "total_shipped": 15},
        "by_date": "2026-07-20", "horizon_days": 10,
        "runs": 100, "seed": 0,
        "bands": {"p50": 7, "p85": 4, "p95": 2} if bands == "default" else bands,
        "caution": caution,
    }


class RenderForecastLinesTest(unittest.TestCase):
    def _line(self, lines, prefix):
        for line in lines:
            if line.startswith(prefix):
                return line
        self.fail("no line starting with %r in %r" % (prefix, lines))

    def test_header_names_the_generated_date(self):
        lines = metrics.render_forecast_lines(_when_result())
        self.assertEqual(lines[0], "delivery forecast — 2026-07-10")

    def test_history_line(self):
        line = self._line(
            metrics.render_forecast_lines(_when_result()), "history:")
        self.assertIn("15", line)
        self.assertIn("20", line)

    def test_when_bands_line_shows_dates_and_days(self):
        line = self._line(
            metrics.render_forecast_lines(_when_result()), "forecast")
        self.assertIn("50%", line)
        self.assertIn("2026-07-13", line)
        self.assertIn("3d", line)
        self.assertIn("95%", line)
        self.assertIn("2026-07-18", line)

    def test_how_many_bands_line_shows_counts_at_confidence(self):
        line = self._line(
            metrics.render_forecast_lines(_how_many_result()), "forecast")
        self.assertIn("2026-07-20", line)
        self.assertIn("7", line)
        self.assertIn("50%", line)
        self.assertIn("95%", line)

    def test_caution_line_present_when_set(self):
        text = "\n".join(metrics.render_forecast_lines(
            _when_result(caution="thin history — low-confidence forecast")))
        self.assertIn("caution:", text)
        self.assertIn("thin history", text)

    def test_no_caution_line_when_absent(self):
        text = "\n".join(metrics.render_forecast_lines(_when_result()))
        self.assertNotIn("caution:", text)

    def test_empty_history_renders_na_bands_both_modes(self):
        none_bands = {"p50": None, "p85": None, "p95": None}
        when_lines = metrics.render_forecast_lines(
            _when_result(bands=none_bands))
        self.assertIn("n/a", self._line(when_lines, "forecast"))
        how_lines = metrics.render_forecast_lines(
            _how_many_result(bands=none_bands))
        self.assertIn("n/a", self._line(how_lines, "forecast"))


def _forecast_log(fx):
    """A build log spanning two weeks with a dozen ships — enough history for a
    non-degenerate forecast fixture."""
    days = [1, 1, 2, 3, 5, 6, 6, 8, 9, 10, 12, 14]
    lines = [json.dumps({
        "timestamp": "2026-07-%02dT09:00:00Z" % d,
        "change": "c%d" % i, "status": "verified",
        "time": {"total_seconds": 300.0},
    }) for i, d in enumerate(days)]
    _write(os.path.join(fx.log_dir, "builds.jsonl"), "\n".join(lines) + "\n")


class ForecastCliTest(unittest.TestCase):
    def setUp(self):
        self.fx = _Fixture()
        self.addCleanup(self.fx.cleanup)
        # No config injection on the verb, so point the layered config at the
        # fixture log dir — no test reads the real ~/.shipd/builds.
        _write_json(os.path.join(self.fx.root, ".shipd-config.json"),
                    {"build": {"log_dir": self.fx.log_dir}})
        _forecast_log(self.fx)
        # An epic with two remaining (non-archived) members for --epic mode.
        _write(self.fx.shipd("epics", "e1", "epic.md"),
               "# e1\nStatus: active\n\n## Changes\n\n"
               "| Change | Description | Risk |\n| --- | --- | --- |\n"
               "| m_ready | planned | low |\n"
               "| m_unplanned | not started | low |\n")
        _write(self.fx.shipd("planned", "m_ready", "plan.md"),
               "# m_ready\nStatus: ready\n")

    def _run(self, argv):
        import contextlib
        import io
        buf, errbuf = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(buf), \
                contextlib.redirect_stderr(errbuf):
            try:
                code = metrics.main(argv)
            except SystemExit as exc:
                code = exc.code
        return code, buf.getvalue()

    def test_items_mode_exits_zero_and_renders(self):
        code, out = self._run(
            ["forecast", "--root", self.fx.root, "--items", "3",
             "--runs", "50"])
        self.assertEqual(code, 0)
        self.assertIn("delivery forecast —", out)
        self.assertIn("forecast", out)

    def test_by_date_mode_exits_zero(self):
        code, out = self._run(
            ["forecast", "--root", self.fx.root, "--by-date", "2099-01-01",
             "--runs", "50"])
        self.assertEqual(code, 0)
        self.assertIn("2099-01-01", out)

    def test_epic_mode_exits_zero(self):
        code, _out = self._run(
            ["forecast", "--root", self.fx.root, "--epic", "e1", "--runs", "50"])
        self.assertEqual(code, 0)

    def test_seed_makes_the_rendered_run_deterministic(self):
        a = self._run(["forecast", "--root", self.fx.root, "--items", "4",
                       "--runs", "200", "--seed", "1"])
        b = self._run(["forecast", "--root", self.fx.root, "--items", "4",
                       "--runs", "200", "--seed", "1"])
        self.assertEqual(a, b)

    def test_json_mode_carries_history_bands_and_caution(self):
        code, out = self._run(
            ["forecast", "--root", self.fx.root, "--items", "3",
             "--runs", "50", "--json"])
        self.assertEqual(code, 0)
        data = json.loads(out)
        for key in ("history", "bands", "caution"):
            self.assertIn(key, data)

    def test_empty_root_exits_zero_with_na(self):
        fx = _Fixture()
        self.addCleanup(fx.cleanup)
        _write_json(os.path.join(fx.root, ".shipd-config.json"),
                    {"build": {"log_dir": fx.log_dir}})
        code, out = self._run(
            ["forecast", "--root", fx.root, "--items", "3", "--runs", "50"])
        self.assertEqual(code, 0)
        self.assertIn("n/a", out)

    def test_unknown_epic_exits_nonzero(self):
        code, _out = self._run(
            ["forecast", "--root", self.fx.root, "--epic", "nope",
             "--runs", "50"])
        self.assertNotEqual(code, 0)

    def test_mode_is_required(self):
        code, _out = self._run(["forecast", "--root", self.fx.root])
        self.assertNotEqual(code, 0)

    def test_modes_are_mutually_exclusive(self):
        code, _out = self._run(
            ["forecast", "--root", self.fx.root, "--items", "3",
             "--by-date", "2099-01-01"])
        self.assertNotEqual(code, 0)

    def test_bare_import_executes_no_cli(self):
        proc = subprocess.run(
            [sys.executable, "-c", "import metrics"],
            cwd=SCRIPTS, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, "")


# ---------------------------------------------------------------------------
# 7. Audience-framed rollups: renderer + verb (delivery-metrics
# stakeholder-rollups)
# ---------------------------------------------------------------------------

def _exec_rollup(trend="up", tier="elite", dep="weekly"):
    return {
        "generated_at": "2026-07-10T00:00:00+00:00", "audience": "exec",
        "exec": {
            "trend": {"throughput": trend},
            "dora": {"deployment_frequency": dep, "lead_time_tier": tier},
            "headlines": {"shipped_total": 18, "rework_rate": 0.1,
                          "change_fail_rate": 0.2},
            "cost": {"tokens_output_total": 85000, "seconds_total": 12240},
        },
    }


def _pm_rollup(trend="up", e1_bands="default"):
    default_bands = {"p50": {"days": 3, "date": "2026-07-13"},
                     "p85": {"days": 5, "date": "2026-07-15"},
                     "p95": {"days": 8, "date": "2026-07-18"}}
    return {
        "generated_at": "2026-07-10T00:00:00+00:00", "audience": "pm",
        "pm": {
            "throughput": {"last_weeks": [2, 3, 2, 3], "trend": trend},
            "epics": [
                {"epic": "e1", "done": 1, "total": 3,
                 "bands": default_bands if e1_bands == "default" else e1_bands,
                 "caution": None},
                {"epic": "e2", "done": 1, "total": 1,
                 "bands": None, "caution": None}],
        },
    }


def _em_rollup():
    return {
        "generated_at": "2026-07-10T00:00:00+00:00", "audience": "em",
        "em": {
            "lead_time": {"median": 86400, "p50": 86400, "p85": 172800,
                          "p95": 172800, "n": 5},
            "cycle_time": {"median": 720, "p50": 720, "p85": 3000,
                           "p95": 3000, "n": 6},
            "wip": {"by_state": {"ready": 3, "active": 1, "draft": 3},
                    "items": [], "aging": {"median": 4.0, "p85": 9.0,
                                           "p95": 9.0, "n": 2}},
            "deployment_days_last_weeks": [1, 2, 1, 2],
            "rework_rate": 0.18,
            "change_fail_rate": 0.2,
            "flow": {"n": 2, "latest_by_state": {"ready": 1, "active": 1}},
        },
    }


class RenderRollupLinesTest(unittest.TestCase):
    def test_title_names_the_audience_and_date(self):
        lines = metrics.render_rollup_lines(_exec_rollup())
        self.assertEqual(lines[0], "# delivery rollup — exec — 2026-07-10")

    def test_has_markdown_section_headings(self):
        text = "\n".join(metrics.render_rollup_lines(_exec_rollup()))
        self.assertIn("\n## ", "\n" + text)

    def test_exec_shows_trend_bands_headlines_cost_no_mean(self):
        text = "\n".join(metrics.render_rollup_lines(_exec_rollup()))
        self.assertIn("up", text)               # throughput trend direction
        self.assertIn("weekly", text)           # deployment-frequency band
        self.assertIn("elite", text)            # lead-time tier
        self.assertIn("10%", text)              # rework rate
        self.assertIn("pre-merge proxy", text)
        self.assertIn("85k", text)              # cost total
        self.assertNotIn("mean", text)

    def test_exec_shows_change_fail_rate_post_merge(self):
        text = "\n".join(metrics.render_rollup_lines(_exec_rollup()))
        line = [ln for ln in metrics.render_rollup_lines(_exec_rollup())
                if "change-fail rate:" in ln][0]
        self.assertIn("20%", line)          # change_fail_rate 0.2
        self.assertIn("post-merge", line)

    def test_exec_absent_tier_renders_na_and_trend_line_omitted(self):
        text = "\n".join(metrics.render_rollup_lines(
            _exec_rollup(trend=None, tier=None)))
        self.assertIn("n/a", text)                    # absent tier → n/a
        self.assertNotIn("throughput trend", text)    # trend line omitted

    def test_pm_epics_show_done_of_total_and_band_dates(self):
        text = "\n".join(metrics.render_rollup_lines(_pm_rollup()))
        self.assertIn("1 of 3", text)     # done of total
        self.assertIn("50%", text)
        self.assertIn("2026-07-13", text)  # projected band date

    def test_pm_epic_without_remaining_renders_na_bands(self):
        text = "\n".join(metrics.render_rollup_lines(_pm_rollup()))
        self.assertIn("1 of 1", text)  # e2 done of total
        self.assertIn("n/a", text)     # e2 has no remaining → n/a bands

    def test_pm_trend_line_omitted_when_none(self):
        text = "\n".join(metrics.render_rollup_lines(_pm_rollup(trend=None)))
        self.assertNotIn("throughput trend", text)

    def test_em_stat_lines_flow_and_rework_no_mean(self):
        text = "\n".join(metrics.render_rollup_lines(_em_rollup()))
        self.assertIn("median 1.0d", text)   # lead-time median humanized
        self.assertIn("(n=5)", text)
        self.assertIn("median 12m", text)    # cycle-time median
        self.assertIn("18%", text)           # rework rate
        self.assertIn("ready 1", text)       # latest flow per-state count
        self.assertNotIn("mean", text)

    def test_em_rework_section_shows_change_fail_rate(self):
        lines = metrics.render_rollup_lines(_em_rollup())
        rework_idx = lines.index("## rework")
        section = "\n".join(lines[rework_idx:])
        self.assertIn("change-fail rate:", section)
        self.assertIn("20%", section)        # change_fail_rate 0.2
        self.assertIn("post-merge", section)


class RollupCliTest(unittest.TestCase):
    def setUp(self):
        self.fx = _Fixture()
        self.addCleanup(self.fx.cleanup)
        # The verb has no config injection, so point the layered config at the
        # fixture log dir — no test reads the real ~/.shipd/builds.
        _write_json(os.path.join(self.fx.root, ".shipd-config.json"),
                    {"build": {"log_dir": self.fx.log_dir}})
        _seed_rollup_fixture(self.fx)
        patch = unittest.mock.patch.dict(os.environ, {}, clear=False)
        patch.start()
        os.environ.pop("SHIPD_FLOW_LOG_DIR", None)
        os.environ.pop("AM_FLOW_LOG_DIR", None)
        self.addCleanup(patch.stop)

    def _run(self, argv):
        import contextlib
        import io
        buf, errbuf = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(buf), \
                contextlib.redirect_stderr(errbuf):
            try:
                code = metrics.main(argv)
            except SystemExit as exc:
                code = exc.code
        return code, buf.getvalue()

    def test_each_audience_exits_zero_and_prints_markdown(self):
        for audience in ("exec", "pm", "em"):
            code, out = self._run(
                ["rollup", "--audience", audience, "--root", self.fx.root])
            self.assertEqual(code, 0, audience)
            self.assertIn("# delivery rollup — %s —" % audience, out)
            self.assertIn("## ", out)

    def test_exec_output_names_no_change_slug(self):
        _code, out = self._run(
            ["rollup", "--audience", "exec", "--root", self.fx.root])
        for slug in ("ship_", "e1_", "e2_", "s1", "s2", "r1"):
            self.assertNotIn(slug, out)

    def test_json_mode_carries_envelope_and_audience_block(self):
        code, out = self._run(
            ["rollup", "--audience", "em", "--root", self.fx.root, "--json"])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data["audience"], "em")
        self.assertIn("generated_at", data)
        self.assertIn("em", data)

    def test_empty_root_exits_zero_with_na(self):
        fx = _Fixture()
        self.addCleanup(fx.cleanup)
        _write_json(os.path.join(fx.root, ".shipd-config.json"),
                    {"build": {"log_dir": fx.log_dir}})
        for audience in ("exec", "pm", "em"):
            code, out = self._run(
                ["rollup", "--audience", audience, "--root", fx.root])
            self.assertEqual(code, 0, audience)
            self.assertIn("n/a", out)

    def test_unrecognized_audience_exits_nonzero(self):
        code, _out = self._run(
            ["rollup", "--audience", "cto", "--root", self.fx.root])
        self.assertNotEqual(code, 0)

    def test_default_seed_pm_runs_are_identical(self):
        a = self._run(["rollup", "--audience", "pm", "--root", self.fx.root])
        b = self._run(["rollup", "--audience", "pm", "--root", self.fx.root])
        self.assertEqual(a, b)

    def test_bare_import_executes_no_cli(self):
        proc = subprocess.run(
            [sys.executable, "-c", "import metrics"],
            cwd=SCRIPTS, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, "")


if __name__ == "__main__":
    unittest.main()
