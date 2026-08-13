#!/usr/bin/env python3
"""Tests for dashboard.py's delivery-metrics view helpers — the
dependency-free data assembler (``metrics_view_data``) and the four pure
renderers (``dora_tiles``, ``run_chart_rows``, ``scatter_rows``, ``cfd_rows``)
plus the ``flow_lane`` state→lane mapping that back the board's metrics screen
(delivery-dashboard board-metrics-view spec).

Like ``change_artifacts`` and ``epic_is_runnable``, these helpers are defined
near the top of ``dashboard.py``, ahead of its module-scope ``textual``
import, specifically so they stay usable — and unit-tested here — without
``textual`` installed. :func:`_load_dashboard_stdlib` (copied from
``test_change_artifacts.py``) executes the module and swallows the
``ImportError`` the absent ``textual`` package raises, leaving everything
defined up to that point in the module's namespace. This suite MUST pass under
system ``python3`` with ``textual`` NOT installed (see AGENTS.md and
``plugins/s/skills/build/tests_textual/`` for the ``textual``-dependent
rendering tests)."""

import datetime as _dt
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.normpath(os.path.join(HERE, "..", "scripts"))
DASHBOARD_PATH = os.path.join(SCRIPTS_DIR, "dashboard.py")

UTC = _dt.timezone.utc


def _load_dashboard_stdlib():
    """Execute ``dashboard.py`` far enough to capture its dependency-free,
    top-of-file helpers without requiring ``textual``. See the module
    docstring above for why this works."""
    if SCRIPTS_DIR not in sys.path:
        sys.path.insert(0, SCRIPTS_DIR)
    spec = importlib.util.spec_from_file_location(
        "dashboard_stdlib_probe_metrics", DASHBOARD_PATH)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except ImportError:
        # Expected when `textual` isn't installed — the helpers defined
        # before dashboard.py's module-scope `textual` import already
        # landed in `module.__dict__`.
        pass
    return module


def _ship_event(slug, day, seconds):
    return {
        "slug": slug,
        "ship_ts": _dt.datetime(2026, 8, day, tzinfo=UTC),
        "seconds": seconds,
    }


class FlowLaneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dashboard = _load_dashboard_stdlib()

    def test_state_to_lane_mapping(self):
        flow_lane = self.dashboard.flow_lane
        self.assertEqual(flow_lane("archived"), "shipped")
        self.assertEqual(flow_lane("ready"), "ready")
        self.assertEqual(flow_lane("unplanned"), "unplanned")
        # Everything else lands in the building lane.
        for state in ("draft", "active", "rejected", "needs_human", "?"):
            self.assertEqual(flow_lane(state), "building")


class DoraTilesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dashboard = _load_dashboard_stdlib()

    def _full_metrics(self):
        return {
            "deployment_days": {
                "per_week": [
                    {"week": "2026-W30", "count": 2},
                    {"week": "2026-W31", "count": 3},
                ],
                "dora_band": "weekly",
            },
            "lead_time": {"median": 3600, "p85": 7200, "n": 5},
            "cycle_time": {"median": 600, "p85": 1200, "n": 5},
            "change_failures": {"rate": 0.1},
            "outcomes": {"rework_rate": 0.2},
        }

    def test_full_fixture_renders_bands_tiers_and_labelled_rates(self):
        tiles = self.dashboard.dora_tiles(self._full_metrics())
        # A list of (label, value) pairs.
        for pair in tiles:
            self.assertEqual(len(pair), 2)
        joined_labels = " ".join(label for label, _ in tiles).lower()
        by_label = dict(tiles)

        # Deployment-frequency band + recent weekly deployment-day counts.
        dep = next(v for lbl, v in tiles
                   if "deployment" in lbl.lower())
        self.assertIn("weekly", dep)
        self.assertIn("2 3", dep)  # last-four deployment-day counts

        # Lead-time DORA tier over the 1h median → elite.
        tier = next(v for lbl, v in tiles if "tier" in lbl.lower())
        self.assertEqual(tier, "elite")

        # Both fail rates, labelled post-merge / pre-merge.
        self.assertIn("post-merge", joined_labels)
        self.assertIn("pre-merge", joined_labels)
        cfr = next(v for lbl, v in tiles
                   if "post-merge" in lbl.lower())
        self.assertEqual(cfr, "10%")
        rework = next(v for lbl, v in tiles
                      if "pre-merge" in lbl.lower())
        self.assertEqual(rework, "20%")

        # Humanized lead/cycle medians + p85.
        lead = next(v for lbl, v in tiles
                    if lbl.lower().startswith("lead time"))
        self.assertIn("1.0h", lead)
        self.assertIn("2.0h", lead)
        cycle = next(v for lbl, v in tiles
                     if lbl.lower().startswith("cycle time"))
        self.assertIn("10m", cycle)
        self.assertIn("20m", cycle)

        # No mean anywhere (SPACE guardrail).
        self.assertNotIn("mean", " ".join(
            "%s %s" % (lbl, v) for lbl, v in tiles).lower())

    def test_empty_fixture_renders_na(self):
        tiles = self.dashboard.dora_tiles({})
        values = [v for _, v in tiles]
        # Every statistic is absent → n/a.
        self.assertTrue(any(v == "n/a" for v in values))
        # The rate tiles are exactly n/a.
        cfr = next(v for lbl, v in tiles if "post-merge" in lbl.lower())
        rework = next(v for lbl, v in tiles if "pre-merge" in lbl.lower())
        self.assertEqual(cfr, "n/a")
        self.assertEqual(rework, "n/a")
        tier = next(v for lbl, v in tiles if "tier" in lbl.lower())
        self.assertEqual(tier, "n/a")


class RunChartRowsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dashboard = _load_dashboard_stdlib()

    def test_peak_full_column_zero_blank_and_total_in_label(self):
        per_week = [
            {"week": "2026-W29", "count": 0},
            {"week": "2026-W30", "count": 5},
        ]
        rows, label = self.dashboard.run_chart_rows(per_week, cols=4, rows=4)
        self.assertEqual(len(rows), 4)
        # The peak week (count 5, at the ceiling) paints a full-height column.
        self.assertTrue(all(row[1] == "█" for row in rows))
        # The zero week is blank in every row.
        self.assertTrue(all(row[0] == " " for row in rows))
        # The label carries the total (5) and the newest week.
        self.assertIn("5", label)
        self.assertIn("2026-W30", label)


class ScatterRowsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dashboard = _load_dashboard_stdlib()

    def _cycle_time(self):
        return {"median": 200, "p50": 200, "p85": 300, "p95": 300, "n": 3}

    def test_dots_labelled_percentiles_sample_count_no_mean(self):
        events = [_ship_event("a", 1, 100), _ship_event("b", 2, 200),
                  _ship_event("c", 3, 300)]
        rows, label = self.dashboard.scatter_rows(
            events, self._cycle_time(), cols=12, rows=8)
        joined = "\n".join(rows) + "\n" + label
        # Dot cells are plotted for the events.
        self.assertIn("•", joined)
        # The percentile lines are labelled with humanized durations.
        self.assertIn("p50", joined)
        self.assertIn("p85", joined)
        self.assertIn("p95", joined)
        self.assertIn("3m", joined)  # p50 == 200s
        self.assertIn("5m", joined)  # p85/p95 == 300s
        # The sample count is reported and no mean appears anywhere.
        self.assertIn("3", label)
        self.assertNotIn("mean", joined.lower())

    def test_events_missing_ts_or_seconds_are_skipped(self):
        events = [
            _ship_event("a", 1, 100),
            _ship_event("b", 2, 200),
            {"slug": "c", "ship_ts": None, "seconds": 300},   # no ts
            {"slug": "d", "ship_ts": _dt.datetime(2026, 8, 4, tzinfo=UTC),
             "seconds": None},                                # no seconds
        ]
        _rows, label = self.dashboard.scatter_rows(
            events, self._cycle_time(), cols=12, rows=8)
        # Only two events carry both a timestamp and seconds.
        self.assertIn("n=2", label)

    def test_empty_events_render_na(self):
        rows, label = self.dashboard.scatter_rows(
            [], {"median": None, "p50": None, "p85": None, "p95": None,
                 "n": 0}, cols=12, rows=8)
        self.assertIn("n/a", label)
        # No dots when there is nothing to plot.
        self.assertNotIn("•", "\n".join(rows))


class CfdRowsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dashboard = _load_dashboard_stdlib()

    def test_columns_stack_lanes_bottom_up_with_legend(self):
        series = [
            {"ts": "2026-08-01T00:00:00Z",
             "by_state": {"archived": 2, "active": 2}},
            {"ts": "2026-08-02T00:00:00Z",
             "by_state": {"ready": 1, "unplanned": 3}},
        ]
        rows, label = self.dashboard.cfd_rows(series, cols=10, rows=8)
        self.assertEqual(len(rows), 8)
        joined = "\n".join(rows)
        # All four mapped lanes appear as markup bands.
        self.assertIn("[$lane-shipped]", joined)   # archived → shipped
        self.assertIn("[$lane-building]", joined)   # active → building
        self.assertIn("[$lane-ready]", joined)
        self.assertIn("[$lane-unplanned]", joined)
        # Column 0 stacks shipped at the bottom, building above it.
        self.assertTrue(rows[-1].startswith("[$lane-shipped]"))
        self.assertTrue(rows[0].startswith("[$lane-building]"))
        # A lane-colored legend line names the lanes and the record count.
        self.assertIn("[$lane-shipped]", label)
        self.assertIn("shipped", label)
        self.assertIn("2", label)  # two records

    def test_empty_series_renders_no_history_notice(self):
        rows, label = self.dashboard.cfd_rows([], cols=10, rows=8)
        self.assertIn("no flow history", label.lower())

    def test_small_nonzero_lane_still_paints_a_cell(self):
        # 1 of 33 rounds to zero of 8 rows — the lane must still show a
        # sliver, trimmed from the tallest band, not vanish.
        series = [{"ts": "2026-08-01T00:00:00Z",
                   "by_state": {"archived": 32, "ready": 1}}]
        rows, _label = self.dashboard.cfd_rows(series, cols=4, rows=8)
        joined = "\n".join(rows)
        self.assertIn("[$lane-ready]", joined)
        self.assertIn("[$lane-shipped]", joined)

    def test_label_notes_the_window_when_records_exceed_columns(self):
        series = [{"ts": "2026-08-0%dT00:00:00Z" % (i + 1),
                   "by_state": {"active": 1}} for i in range(5)]
        _rows, label = self.dashboard.cfd_rows(series, cols=3, rows=4)
        self.assertIn("5 records", label)
        self.assertIn("newest 3 shown", label)


class MetricsViewDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dashboard = _load_dashboard_stdlib()

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="metrics-view-data-")
        # Isolate the build/flow log dir to an empty temp subdir so the helper
        # reads no real ~/.shipd/builds data and stays deterministic + hermetic.
        self.log_dir = os.path.join(self.root, "logs")
        os.makedirs(self.log_dir)
        with open(os.path.join(self.root, ".shipd-config.json"), "w",
                  encoding="utf-8") as fh:
            json.dump({"build": {"log_dir": self.log_dir}}, fh)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_returns_metrics_and_ship_events_dict_without_writing(self):
        before = sorted(os.listdir(self.log_dir))
        data = self.dashboard.metrics_view_data(self.root)
        self.assertIn("metrics", data)
        self.assertIn("ship_events", data)
        self.assertIsInstance(data["metrics"], dict)
        self.assertIsInstance(data["ship_events"], list)
        # An empty fixture root ships nothing.
        self.assertEqual(data["ship_events"], [])
        # The helper writes nothing to the log dir.
        self.assertEqual(sorted(os.listdir(self.log_dir)), before)


class ShippedThisWeekTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dashboard = _load_dashboard_stdlib()

    def test_counts_only_events_on_or_after_this_iso_weeks_monday(self):
        shipped_this_week = self.dashboard.shipped_this_week
        # 2026-08-05 is a Wednesday; the Monday (UTC) of its ISO week is
        # 2026-08-03. An injected `now` keeps the boundary deterministic.
        now = _dt.datetime(2026, 8, 5, 12, 0, tzinfo=UTC)
        events = [
            # On the week's Monday midnight — counts (on/after the boundary).
            {"slug": "a", "ship_ts": _dt.datetime(2026, 8, 3, tzinfo=UTC)},
            # Mid-week, before `now` — counts.
            {"slug": "b", "ship_ts": _dt.datetime(2026, 8, 4, 9, tzinfo=UTC)},
            # The prior ISO week (Sunday 2026-08-02) — excluded.
            {"slug": "c", "ship_ts": _dt.datetime(2026, 8, 2, 23, tzinfo=UTC)},
            # Well before the week — excluded.
            {"slug": "d", "ship_ts": _dt.datetime(2026, 7, 20, tzinfo=UTC)},
            # No ship_ts — skipped, never fatal.
            {"slug": "e", "ship_ts": None},
        ]
        self.assertEqual(shipped_this_week(events, now), 2)

    def test_empty_list_counts_zero(self):
        shipped_this_week = self.dashboard.shipped_this_week
        now = _dt.datetime(2026, 8, 5, tzinfo=UTC)
        self.assertEqual(shipped_this_week([], now), 0)


if __name__ == "__main__":
    unittest.main()
