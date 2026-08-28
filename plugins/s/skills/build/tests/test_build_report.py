#!/usr/bin/env python3
"""Unit tests for build_report.render_table: the slim column set
(Model | Tokens ↑ | Tokens ↓ | Token % | Time), per-row Token % arithmetic,
the Total row, degradation, and the zero-output edge case."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import build_report as br  # noqa: E402


def bucket(non_cached_input=0, output=0, cache_write=0, cache_read=0):
    return {
        "non_cached_input": non_cached_input,
        "output": output,
        "cache_write": cache_write,
        "cache_read": cache_read,
    }


class RenderTableTest(unittest.TestCase):
    def setUp(self):
        # Two-model fixture: outputs 750 and 250 -> 75% / 25% of 1000 total.
        self.by_model = {
            "model-a": bucket(non_cached_input=1200, output=750, cache_write=40, cache_read=90),
            "model-b": bucket(non_cached_input=400, output=250, cache_write=10, cache_read=30),
        }
        self.totals = br.totals_of(self.by_model)
        self.by_model_time = {"model-a": 120.0, "model-b": 40.0}
        self.total_time = 160.0

    def render(self):
        return br.render_table(
            self.by_model, self.totals, self.total_time, self.by_model_time
        )

    def test_header_columns_exact(self):
        lines = self.render().splitlines()
        self.assertEqual(
            lines[0], "| Model | Tokens ↑ | Tokens ↓ | Token % | Time |"
        )
        self.assertEqual(lines[1], "| --- | --- | --- | --- | --- |")

    def test_per_row_token_pct(self):
        lines = self.render().splitlines()
        # model-a sorts first (more time attributed).
        self.assertIn("| model-a |", lines[2])
        self.assertIn("| 75% |", lines[2])
        self.assertIn("| model-b |", lines[3])
        self.assertIn("| 25% |", lines[3])

    def test_total_row_100_pct(self):
        out = self.render()
        total_line = [l for l in out.splitlines() if l.startswith("| **Total**")]
        self.assertEqual(len(total_line), 1)
        self.assertIn("100%", total_line[0])

    def test_no_cache_or_time_pct_columns(self):
        out = self.render()
        self.assertNotIn("Cache", out)
        self.assertNotIn("Time %", out)

    def test_total_time_line_present(self):
        out = self.render()
        self.assertIn("Total time: 2m40s", out)

    def test_zero_output_edge_case(self):
        by_model = {
            "model-a": bucket(non_cached_input=100, output=0),
            "model-b": bucket(non_cached_input=50, output=0),
        }
        totals = br.totals_of(by_model)
        out = br.render_table(by_model, totals, 20.0, {"model-a": 12.0, "model-b": 8.0})
        # No division error; every Token % (including Total) renders 0%.
        for line in out.splitlines():
            if line.startswith("| model-") or line.startswith("| **Total**"):
                self.assertIn("0%", line)
                self.assertNotIn("100%", line)

    def test_degrades_when_timing_unavailable(self):
        out = br.render_table(self.by_model, self.totals, None, None)
        lines = out.splitlines()
        # Time column dropped; Token % stays.
        self.assertEqual(lines[0], "| Model | Tokens ↑ | Tokens ↓ | Token % |")
        self.assertIn("Token %", out)
        self.assertNotIn("Time", out)
        self.assertNotIn("Total time:", out)


class AggregateSyntheticTest(unittest.TestCase):
    """aggregate() excludes harness-generated <synthetic> records from both the
    per-model usage map and the timing timeline, while real models (including
    zero-usage ones) stay visible."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def _write_transcript(self, records):
        import json

        path = os.path.join(self.tmp, "transcript.jsonl")
        with open(path, "w", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec) + "\n")
        return path

    @staticmethod
    def _assistant(model, ts, output=0, input_tokens=0):
        return {
            "type": "assistant",
            "timestamp": ts,
            "message": {
                "model": model,
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output,
                    "cache_creation_input_tokens": 0,
                    "cache_read_input_tokens": 0,
                },
            },
        }

    def _fixture(self):
        # A real record, a zero-usage <synthetic> record between two real
        # records, and a zero-usage real-model record.
        return self._write_transcript(
            [
                self._assistant("model-a", "2026-01-01T00:00:10Z", output=100, input_tokens=50),
                self._assistant("<synthetic>", "2026-01-01T00:00:20Z"),
                self._assistant("model-a", "2026-01-01T00:00:30Z", output=200, input_tokens=80),
                self._assistant("model-b", "2026-01-01T00:00:40Z"),
            ]
        )

    def test_no_synthetic_row(self):
        path = self._fixture()
        since = br.parse_since("2026-01-01T00:00:00Z")
        by_model, _timeline = br.aggregate([path], since)
        self.assertNotIn("<synthetic>", by_model)
        self.assertIn("model-a", by_model)

    def test_zero_usage_real_model_stays(self):
        path = self._fixture()
        since = br.parse_since("2026-01-01T00:00:00Z")
        by_model, _timeline = br.aggregate([path], since)
        self.assertIn("model-b", by_model)
        self.assertEqual(by_model["model-b"]["output"], 0)

    def test_synthetic_time_folds_into_real(self):
        path = self._fixture()
        since = br.parse_since("2026-01-01T00:00:00Z")
        _by_model, timeline = br.aggregate([path], since)
        self.assertNotIn("<synthetic>", [m for _ts, m in timeline])
        total_time, by_model_time = br.compute_timing(timeline, since)
        self.assertNotIn("<synthetic>", by_model_time)
        self.assertAlmostEqual(sum(by_model_time.values()), total_time)


class AggregateDedupTest(unittest.TestCase):
    """aggregate() counts each assistant API response exactly once at its final
    usage snapshot, keyed by its message id: every usage field accumulates only
    the positive delta over the highest value already counted, so records
    repeating identical usage add nothing and cumulative streaming snapshots sum
    to the response's final value — while the timing timeline still records
    every timestamped record (build-reporting usage-dedup)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def _write_transcript(self, records):
        path = os.path.join(self.tmp, "transcript.jsonl")
        with open(path, "w", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec) + "\n")
        return path

    @staticmethod
    def _assistant(msg_id, ts, output=0, input_tokens=0, model="model-a",
                   cache_write=0, cache_read=0):
        return {
            "type": "assistant",
            "timestamp": ts,
            "message": {
                "id": msg_id,
                "model": model,
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output,
                    "cache_creation_input_tokens": cache_write,
                    "cache_read_input_tokens": cache_read,
                },
            },
        }

    def test_multi_record_response_counts_once_and_timeline_keeps_all(self):
        # Four records share one message id (each repeating output 678) plus a
        # fifth with a distinct id (output 100).
        records = [
            self._assistant("msg-shared", "2026-01-01T00:00:10Z", output=678,
                            input_tokens=50),
            self._assistant("msg-shared", "2026-01-01T00:00:11Z", output=678,
                            input_tokens=50),
            self._assistant("msg-shared", "2026-01-01T00:00:12Z", output=678,
                            input_tokens=50),
            self._assistant("msg-shared", "2026-01-01T00:00:13Z", output=678,
                            input_tokens=50),
            self._assistant("msg-distinct", "2026-01-01T00:00:20Z", output=100,
                            input_tokens=20),
        ]
        path = self._write_transcript(records)
        since = br.parse_since("2026-01-01T00:00:00Z")
        by_model, timeline = br.aggregate([path], since)
        # The shared response counts once (678, not 2712), the distinct once.
        self.assertEqual(by_model["model-a"]["output"], 678 + 100)
        self.assertEqual(by_model["model-a"]["non_cached_input"], 50 + 20)
        # Every timestamped record still appears in the timing timeline.
        self.assertEqual(len(timeline), 5)

    def test_cumulative_snapshots_count_the_final_value(self):
        # A subagent response's records carry cumulative snapshots under one
        # id (1, 1, then 331): the response counts at its final snapshot.
        records = [
            self._assistant("msg-stream", "2026-01-01T00:00:10Z", output=1),
            self._assistant("msg-stream", "2026-01-01T00:00:11Z", output=1),
            self._assistant("msg-stream", "2026-01-01T00:00:12Z", output=331),
        ]
        path = self._write_transcript(records)
        since = br.parse_since("2026-01-01T00:00:00Z")
        by_model, timeline = br.aggregate([path], since)
        self.assertEqual(by_model["model-a"]["output"], 331)
        # Every timestamped record still appears in the timing timeline.
        self.assertEqual(len(timeline), 3)

    def test_every_usage_field_follows_its_final_snapshot(self):
        records = [
            self._assistant("msg-stream", "2026-01-01T00:00:10Z", output=1,
                            input_tokens=4, cache_write=100, cache_read=2000),
            self._assistant("msg-stream", "2026-01-01T00:00:12Z", output=331,
                            input_tokens=9, cache_write=100, cache_read=5000),
        ]
        path = self._write_transcript(records)
        since = br.parse_since("2026-01-01T00:00:00Z")
        by_model, timeline = br.aggregate([path], since)
        bucket = by_model["model-a"]
        self.assertEqual(bucket["non_cached_input"], 9)
        self.assertEqual(bucket["output"], 331)
        self.assertEqual(bucket["cache_write"], 100)
        self.assertEqual(bucket["cache_read"], 5000)
        self.assertEqual(len(timeline), 2)

    def test_distinct_message_ids_still_accumulate(self):
        records = [
            self._assistant("msg-a", "2026-01-01T00:00:10Z", output=100),
            self._assistant("msg-b", "2026-01-01T00:00:20Z", output=250),
        ]
        path = self._write_transcript(records)
        since = br.parse_since("2026-01-01T00:00:00Z")
        by_model, _timeline = br.aggregate([path], since)
        self.assertEqual(by_model["model-a"]["output"], 350)


class ActivityTailTest(unittest.TestCase):
    """ActivityTail.poll(): an offset-keeping tail over a session's main and
    subagent transcripts that reads only appended bytes, defers a torn
    trailing line, re-discovers subagent files each poll, keys responses by
    message id across polls/files (a later record yielding only its positive
    output-token delta), skips synthetic records, and yields
    ``(start_epoch, end_epoch, output_tokens)`` interval events per response —
    ``end`` the response's timestamp, ``start`` reaching back to the previous
    event's end in the same tail (capped at 120s, first event zero-length)
    (build-reporting session-activity-sampling). Fixtures live in a private
    temp dir — the real ~/.claude is never read."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.session = "sess-1"
        self.main = os.path.join(self.tmp, self.session + ".jsonl")

    @staticmethod
    def _rec(msg_id, ts, output=0, model="model-a"):
        return {
            "type": "assistant",
            "timestamp": ts,
            "message": {"id": msg_id, "model": model,
                        "usage": {"output_tokens": output}},
        }

    def _append(self, path, records):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

    def test_only_appended_records_are_new(self):
        self._append(self.main, [self._rec("m1", "2026-01-01T00:00:10Z", 100)])
        tail = br.ActivityTail(self.tmp, self.session)
        first = tail.poll()
        self.assertEqual(len(first), 1)
        self._append(self.main, [self._rec("m2", "2026-01-01T00:00:20Z", 200),
                                 self._rec("m3", "2026-01-01T00:00:30Z", 300)])
        second = tail.poll()
        self.assertEqual([tok for _s, _e, tok in second], [200, 300])

    def test_interval_spans_back_capped_and_first_zero_length(self):
        # Three responses: first at :10, one 30s later at :40, one 600s after
        # that at 00:10:40 (640s). The interval events span back to the prior
        # end, capped at 120s, with the first event zero-length.
        self._append(self.main, [
            self._rec("m1", "2026-01-01T00:00:10Z", 100),
            self._rec("m2", "2026-01-01T00:00:40Z", 200),
            self._rec("m3", "2026-01-01T00:10:40Z", 300),
        ])
        tail = br.ActivityTail(self.tmp, self.session)
        events = tail.poll()
        self.assertEqual([tok for _s, _e, tok in events], [100, 200, 300])
        (s0, e0, _), (s1, e1, _), (s2, e2, _) = events
        self.assertEqual(e0 - s0, 0)      # first event zero-length
        self.assertEqual(e1 - s1, 30)     # spans back to the previous end
        self.assertEqual(e2 - s2, 120)    # a 600s gap is capped at 120s

    def test_torn_line_deferred_then_yielded_once(self):
        self._append(self.main, [self._rec("m1", "2026-01-01T00:00:10Z", 100)])
        torn = json.dumps(self._rec("m2", "2026-01-01T00:00:20Z", 200))
        half = len(torn) // 2
        with open(self.main, "a", encoding="utf-8") as f:
            f.write(torn[:half])  # a partial line, no trailing newline
        tail = br.ActivityTail(self.tmp, self.session)
        first = tail.poll()
        self.assertEqual(len(first), 1)  # only the complete m1
        with open(self.main, "a", encoding="utf-8") as f:
            f.write(torn[half:] + "\n")  # complete the torn line
        second = tail.poll()
        self.assertEqual([tok for _s, _e, tok in second], [200])

    def test_midrun_subagent_transcript_picked_up(self):
        self._append(self.main, [self._rec("m1", "2026-01-01T00:00:10Z", 100)])
        tail = br.ActivityTail(self.tmp, self.session)
        tail.poll()
        sub = os.path.join(self.tmp, self.session, "subagents",
                           "agent-abc.jsonl")
        self._append(sub, [self._rec("s1", "2026-01-01T00:00:40Z", 500)])
        events = tail.poll()
        self.assertEqual([tok for _s, _e, tok in events], [500])

    def test_cross_poll_message_id_dedup(self):
        self._append(self.main, [self._rec("dup", "2026-01-01T00:00:10Z", 100)])
        tail = br.ActivityTail(self.tmp, self.session)
        self.assertEqual(len(tail.poll()), 1)
        # The same message id reappears (a multi-record response spanning polls).
        self._append(self.main, [self._rec("dup", "2026-01-01T00:00:11Z", 100)])
        self.assertEqual(tail.poll(), [])

    def test_cumulative_snapshots_yield_delta_events(self):
        # A subagent response streams cumulative snapshots under one id: the
        # first record yields its snapshot, the later record yields only the
        # positive delta, timestamped at that later record — so the response's
        # events sum exactly to its final snapshot.
        sub = os.path.join(self.tmp, self.session, "subagents",
                           "agent-abc.jsonl")
        self._append(sub, [self._rec("s1", "2026-01-01T00:00:10Z", 1),
                           self._rec("s1", "2026-01-01T00:00:40Z", 104)])
        tail = br.ActivityTail(self.tmp, self.session)
        events = tail.poll()
        self.assertEqual(sum(tok for _s, _e, tok in events), 104)
        self.assertEqual([tok for _s, _e, tok in events], [1, 103])
        later = br.parse_timestamp("2026-01-01T00:00:40Z").timestamp()
        self.assertEqual(events[-1][1], later)

    def test_repeated_identical_snapshots_yield_no_further_event(self):
        # Records repeating one id's unchanged snapshot — within a poll and
        # again in a later poll — yield an event only for the first record.
        self._append(self.main, [self._rec("dup", "2026-01-01T00:00:10Z", 955),
                                 self._rec("dup", "2026-01-01T00:00:11Z", 955)])
        tail = br.ActivityTail(self.tmp, self.session)
        first = tail.poll()
        self.assertEqual([tok for _s, _e, tok in first], [955])
        self._append(self.main, [self._rec("dup", "2026-01-01T00:00:12Z", 955)])
        self.assertEqual(tail.poll(), [])

    def test_cross_poll_higher_snapshot_yields_delta(self):
        # A response still streaming when the poll boundary falls: the higher
        # snapshot in the next poll yields the delta, so the response's events
        # still sum to its final value.
        self._append(self.main, [self._rec("m1", "2026-01-01T00:00:10Z", 1)])
        tail = br.ActivityTail(self.tmp, self.session)
        self.assertEqual([tok for _s, _e, tok in tail.poll()], [1])
        self._append(self.main, [self._rec("m1", "2026-01-01T00:00:20Z", 331)])
        second = tail.poll()
        self.assertEqual([tok for _s, _e, tok in second], [330])
        self.assertEqual(1 + sum(tok for _s, _e, tok in second), 331)

    def test_synthetic_records_skipped(self):
        self._append(self.main, [
            self._rec("m1", "2026-01-01T00:00:10Z", 100),
            self._rec("syn", "2026-01-01T00:00:20Z", 0, model="<synthetic>"),
            self._rec("m2", "2026-01-01T00:00:30Z", 200),
        ])
        tail = br.ActivityTail(self.tmp, self.session)
        events = tail.poll()
        self.assertEqual([tok for _s, _e, tok in events], [100, 200])


class MultiTailBucketTest(unittest.TestCase):
    """MultiTail syncs a keyed set of per-session tails (adding and dropping
    sessions between polls) and merges their events, and bucket_events folds
    interval events into fixed-size buckets — distributing each event's tokens
    across the buckets its span overlaps, proportional to overlap, and
    preserving the token total exactly (build-reporting
    session-activity-sampling). Fixtures live in a private temp dir."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    @staticmethod
    def _rec(msg_id, ts, output):
        return {"type": "assistant", "timestamp": ts,
                "message": {"id": msg_id, "model": "m",
                            "usage": {"output_tokens": output}}}

    def _append(self, session, records):
        path = os.path.join(self.tmp, session + ".jsonl")
        with open(path, "a", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

    def test_multitail_follows_the_driving_set(self):
        self._append("A", [self._rec("a1", "2026-01-01T00:00:10Z", 111)])
        self._append("B", [self._rec("b1", "2026-01-01T00:00:10Z", 222)])
        mt = br.MultiTail()
        mt.sync([(self.tmp, "A"), (self.tmp, "B")])
        first = mt.poll()
        self.assertEqual(sorted(tok for _s, _e, tok in first), [111, 222])
        # Drop A, add C, keep B; append new records to B and C.
        self._append("B", [self._rec("b2", "2026-01-01T00:00:20Z", 223)])
        self._append("C", [self._rec("c1", "2026-01-01T00:00:20Z", 333)])
        mt.sync([(self.tmp, "B"), (self.tmp, "C")])
        second = mt.poll()
        # B's kept offset means b1 is not re-yielded; A is dropped entirely.
        self.assertEqual(sorted(tok for _s, _e, tok in second), [223, 333])

    def test_spanning_event_distributes_across_buckets(self):
        # A 30-second event bucketed at 3s spreads its tokens across the
        # overlapped buckets instead of landing in a single bucket.
        buckets = br.bucket_events([(100.0, 130.0, 300)], 3)
        self.assertEqual(sum(buckets.values()), 300)  # total preserved exactly
        self.assertGreater(len(buckets), 1)           # spread, not one blip
        self.assertLess(max(buckets.values()), 300)   # no bucket holds it all

    def test_zero_length_event_lands_in_one_bucket(self):
        # A first (zero-length) event lands wholly in the bucket of its stamp.
        buckets = br.bucket_events([(100.0, 100.0, 50)], 3)
        self.assertEqual(buckets, {99: 50})           # 100 // 3 * 3 == 99

    def test_rebucketing_preserves_totals(self):
        # A mix of spanning and zero-length interval triples.
        events = [
            (100.0, 100.0, 10), (101.5, 131.5, 20), (105.0, 105.0, 30),
            (112.0, 172.0, 40), (130.0, 130.0, 50),
        ]
        total = sum(tok for _s, _e, tok in events)
        b3 = br.bucket_events(events, 3)
        b12 = br.bucket_events(events, 12)
        self.assertEqual(sum(b3.values()), total)     # exactly, no float drift
        self.assertEqual(sum(b12.values()), total)
        # Different bucket sizes group the same events differently.
        self.assertNotEqual(len(b3), len(b12))


class ChartHelpersTest(unittest.TestCase):
    """render_chart draws a series as eighth-block strings, scale_bounds
    computes auto/fixed floors and ceilings, and fmt_tokens abbreviates
    (build-reporting block-chart-rendering)."""

    def _topmost_nonspace(self, rows_strings, col):
        for r in range(len(rows_strings)):
            if rows_strings[r][col] != " ":
                return rows_strings[r][col]
        return " "

    def test_render_chart_three_rows(self):
        result = br.render_chart([0, 3000, 1500], 3, 0, 3000)
        self.assertEqual(len(result), 3)
        for s in result:
            self.assertEqual(len(s), 3)
        # The ceiling column (col 1) is a full-height bar of █.
        self.assertEqual([result[r][1] for r in range(3)], ["█", "█", "█"])
        # The floor column (col 0) is blank.
        self.assertEqual([result[r][0] for r in range(3)], [" ", " ", " "])
        # The intermediate column (col 2) tops out in a partial eighth-block.
        top = self._topmost_nonspace(result, 2)
        self.assertNotEqual(top, " ")
        self.assertNotEqual(top, "█")
        self.assertIn(top, "▁▂▃▄▅▆▇")

    def test_render_chart_one_row(self):
        result = br.render_chart([0, 3000, 1500], 1, 0, 3000)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], " ")   # floor blank
        self.assertEqual(result[0][1], "█")   # ceiling full

    def test_scale_bounds_auto(self):
        floor, ceiling = br.scale_bounds([4000, 7000, 10000], "auto")
        self.assertEqual(floor, 3000)
        self.assertEqual(ceiling, 11000)  # ceil(11000/500)*500

    def test_scale_bounds_fixed(self):
        self.assertEqual(br.scale_bounds([1, 2, 3], "fixed"), (0, 12000))

    def test_scale_bounds_all_zero_safe(self):
        floor, ceiling = br.scale_bounds([0, 0, 0], "auto")
        self.assertEqual(floor, 0)
        self.assertEqual(ceiling, 500)  # minimum ceiling

    def test_fmt_tokens(self):
        self.assertEqual(br.fmt_tokens(678), "678")
        self.assertEqual(br.fmt_tokens(5600), "5.6K")


class ResolveProjectRootTest(unittest.TestCase):
    """resolve_project_root: linked-worktree .git files resolve to the main
    checkout root; everything else (normal .git dir, submodule .git file,
    unreadable/odd shape) returns the project dir unchanged."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_linked_worktree_resolves_to_main_checkout(self):
        main = os.path.join(self.tmp, "main")
        wt = os.path.join(main, ".worktrees", "feature")
        os.makedirs(wt)
        gitdir = os.path.join(main, ".git", "worktrees", "feature")
        os.makedirs(gitdir)
        with open(os.path.join(wt, ".git"), "w", encoding="utf-8") as f:
            f.write("gitdir: %s\n" % gitdir)
        self.assertEqual(br.resolve_project_root(wt), os.path.abspath(main))

    def test_relative_gitdir_resolved_against_worktree(self):
        main = os.path.join(self.tmp, "main")
        wt = os.path.join(self.tmp, "wt")
        os.makedirs(wt)
        gitdir = os.path.join(main, ".git", "worktrees", "feature")
        os.makedirs(gitdir)
        rel = os.path.relpath(gitdir, wt)
        with open(os.path.join(wt, ".git"), "w", encoding="utf-8") as f:
            f.write("gitdir: %s\n" % rel)
        self.assertEqual(br.resolve_project_root(wt), os.path.abspath(main))

    def test_normal_git_directory_unchanged(self):
        proj = os.path.join(self.tmp, "proj")
        os.makedirs(os.path.join(proj, ".git"))
        self.assertEqual(br.resolve_project_root(proj), os.path.abspath(proj))

    def test_submodule_gitdir_unchanged(self):
        proj = os.path.join(self.tmp, "sub")
        os.makedirs(proj)
        with open(os.path.join(proj, ".git"), "w", encoding="utf-8") as f:
            f.write("gitdir: /some/parent/.git/modules/sub\n")
        self.assertEqual(br.resolve_project_root(proj), os.path.abspath(proj))

    def test_no_git_at_all_unchanged(self):
        proj = os.path.join(self.tmp, "bare")
        os.makedirs(proj)
        self.assertEqual(br.resolve_project_root(proj), os.path.abspath(proj))


class TranscriptDiscoveryFallbackTest(unittest.TestCase):
    """transcript_dir prefers the working directory's own slug dir, and only
    falls back to the resolved main-checkout slug dir when the own one is
    absent. Isolated from ~/.claude via CLAUDE_CONFIG_DIR."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.config = os.path.join(self.tmp, "config")
        self._prev = os.environ.get("CLAUDE_CONFIG_DIR")
        os.environ["CLAUDE_CONFIG_DIR"] = self.config
        self.addCleanup(self._restore)

    def _restore(self):
        if self._prev is None:
            os.environ.pop("CLAUDE_CONFIG_DIR", None)
        else:
            os.environ["CLAUDE_CONFIG_DIR"] = self._prev

    def _make_worktree(self):
        main = os.path.join(self.tmp, "main")
        wt = os.path.join(main, ".worktrees", "feature")
        os.makedirs(wt)
        gitdir = os.path.join(main, ".git", "worktrees", "feature")
        os.makedirs(gitdir)
        with open(os.path.join(wt, ".git"), "w", encoding="utf-8") as f:
            f.write("gitdir: %s\n" % gitdir)
        return main, wt

    def _slug_dir(self, project_dir):
        return os.path.join(self.config, "projects", br.project_slug(project_dir))

    def test_prefers_own_slug_when_present(self):
        main, wt = self._make_worktree()
        own = self._slug_dir(wt)
        os.makedirs(own)
        os.makedirs(self._slug_dir(main))  # main also exists; own still wins
        self.assertEqual(br.transcript_dir(wt), own)

    def test_falls_back_to_main_when_own_absent(self):
        main, wt = self._make_worktree()
        main_slug = self._slug_dir(main)
        os.makedirs(main_slug)  # only main exists
        self.assertEqual(br.transcript_dir(wt), main_slug)

    def test_returns_own_slug_when_neither_exists(self):
        main, wt = self._make_worktree()
        # Neither slug dir created: degrade to the own (nonexistent) path.
        self.assertEqual(br.transcript_dir(wt), self._slug_dir(wt))


class BuildConfigTest(unittest.TestCase):
    """Build settings come from the resolved layered configuration's ``build``
    key (defaults when absent), and the log lands under the resolved build log
    dir (default ``~/.shipd/builds/``) — never ``~/.am/`` or ``~/.automikk/``
    (build-reporting persistent-build-log, user-configuration-file). ``$HOME``
    is isolated so the real home is never read or written."""

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="br-home-")
        self.proj = tempfile.mkdtemp(prefix="br-proj-")
        self._old_home = os.environ.get("HOME")
        os.environ["HOME"] = self.home

    def tearDown(self):
        if self._old_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = self._old_home
        shutil.rmtree(self.home, ignore_errors=True)
        shutil.rmtree(self.proj, ignore_errors=True)

    def _write_home_config(self, data):
        with open(os.path.join(self.home, ".shipd-config.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(data, fh)

    def _builds_dir(self):
        return os.path.join(self.home, ".shipd", "builds")

    def test_defaults_when_no_build_key(self):
        cfg = br.build_config(self.proj)
        self.assertTrue(cfg["logging_enabled"])
        self.assertEqual(cfg["number_format"], "short")

    def test_log_dir_default_is_dot_am_builds(self):
        cfg = br.build_config(self.proj)
        self.assertEqual(
            os.path.normpath(br.build_log_dir(cfg)),
            os.path.normpath(self._builds_dir()))

    def test_build_key_overrides_defaults(self):
        self._write_home_config(
            {"build": {"logging_enabled": False, "number_format": "long"}})
        cfg = br.build_config(self.proj)
        self.assertFalse(cfg["logging_enabled"])
        self.assertEqual(cfg["number_format"], "long")

    def test_write_log_entry_creates_dir_on_demand(self):
        cfg = br.build_config(self.proj)
        self.assertFalse(os.path.exists(self._builds_dir()))
        br.write_log_entry({"change": "my-change", "status": "ok"}, cfg)
        builds = self._builds_dir()
        self.assertTrue(os.path.isdir(builds))
        self.assertTrue(os.path.isfile(os.path.join(builds, "builds.jsonl")))
        per = [f for f in os.listdir(builds)
               if f.endswith(".json") and "my-change" in f]
        self.assertTrue(per)

    def test_no_am_path_read_or_written(self):
        cfg = br.build_config(self.proj)
        br.write_log_entry({"change": "c"}, cfg)
        self.assertFalse(os.path.exists(os.path.join(self.home, ".am")))
        self.assertFalse(os.path.exists(os.path.join(self.home, ".automikk")))


class LogEntryCLITest(unittest.TestCase):
    """Driving build_report.py's ``--log`` mode through the CLI (subprocess),
    following BuildConfigTest's convention of isolating ``$HOME`` so the
    entry lands under a temporary log directory rather than the real home
    (build-reporting persistent-build-log: no schema/workflow label)."""

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="br-home-")
        self.proj = tempfile.mkdtemp(prefix="br-proj-")
        self.env = dict(os.environ)
        self.env["HOME"] = self.home
        self.env.pop("CLAUDE_CONFIG_DIR", None)

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)
        shutil.rmtree(self.proj, ignore_errors=True)

    def _run(self, *extra_args):
        return subprocess.run(
            [sys.executable, os.path.join(SCRIPTS, "build_report.py"),
             "--project-dir", self.proj, "--change", "my-change",
             "--tasks-done", "1", "--tasks-total", "1", "--status", "verified",
             "--commit", "abc123", "--log", *extra_args],
            capture_output=True, text=True, env=self.env)

    def test_appended_entry_has_no_schema_key(self):
        proc = self._run()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        jsonl_path = os.path.join(self.home, ".shipd", "builds", "builds.jsonl")
        with open(jsonl_path, encoding="utf-8") as f:
            lines = f.read().strip().splitlines()
        entry = json.loads(lines[-1])
        self.assertNotIn("schema", entry)

    def test_schema_option_rejected(self):
        proc = self._run("--schema", "spec-driven")
        self.assertNotEqual(proc.returncode, 0)


class AggregateToolsTest(unittest.TestCase):
    """aggregate_tools()/render_tool_table(): the per-tool breakdown counts each
    assistant response once at its final usage snapshot (keyed by message id,
    synthetic records skipped) and splits its output tokens evenly across the
    ``tool_use`` blocks its records carry, merging main and subagent transcripts
    into the same rows, with a ``(no tool)`` row for tool-less responses, rows
    sorted by output tokens descending, and a bold ``**Total**`` row equal to the
    deduplicated sum (build-reporting tool-usage-breakdown)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="br-tools-")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def _write_transcript(self, records, name="transcript.jsonl"):
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec) + "\n")
        return path

    @staticmethod
    def _assistant(msg_id, ts, output=0, tools=(), model="model-a"):
        content = [{"type": "text", "text": "hi"}]
        for name in tools:
            content.append({"type": "tool_use", "id": "tu-%s" % name,
                            "name": name, "input": {}})
        return {
            "type": "assistant",
            "timestamp": ts,
            "message": {
                "id": msg_id,
                "model": model,
                "content": content,
                "usage": {
                    "input_tokens": 10,
                    "output_tokens": output,
                    "cache_creation_input_tokens": 0,
                    "cache_read_input_tokens": 0,
                },
            },
        }

    @staticmethod
    def _since():
        return br.parse_since("2026-01-01T00:00:00Z")

    def test_multi_tool_response_splits_evenly(self):
        path = self._write_transcript([
            self._assistant("msg-1", "2026-01-01T00:00:10Z", output=100,
                            tools=("Bash", "Read")),
        ])
        by_tool = br.aggregate_tools([path], self._since())
        self.assertEqual(by_tool["Bash"], {"calls": 1, "output": 50})
        self.assertEqual(by_tool["Read"], {"calls": 1, "output": 50})

    def test_tool_less_response_lands_in_no_tool_row(self):
        path = self._write_transcript([
            self._assistant("msg-1", "2026-01-01T00:00:10Z", output=80),
        ])
        by_tool = br.aggregate_tools([path], self._since())
        self.assertEqual(by_tool[br.NO_TOOL_LABEL],
                         {"calls": 0, "output": 80})
        rendered = br.render_tool_table(by_tool)
        self.assertIn("| %s | 0 | 80 |" % br.NO_TOOL_LABEL, rendered)

    def test_subagent_tool_calls_merge_natively(self):
        main = self._write_transcript([
            self._assistant("msg-main", "2026-01-01T00:00:10Z", output=100,
                            tools=("Bash",)),
        ], name="main.jsonl")
        sub = self._write_transcript([
            self._assistant("msg-sub", "2026-01-01T00:00:20Z", output=40,
                            tools=("Bash",)),
        ], name="agent-1.jsonl")
        by_tool = br.aggregate_tools([main, sub], self._since())
        self.assertEqual(list(by_tool), ["Bash"])
        self.assertEqual(by_tool["Bash"], {"calls": 2, "output": 140})

    def test_cumulative_snapshots_attribute_the_final_value_once(self):
        # One message id spanning snapshots 1, 1, 331 — the last carrying the
        # tool_use block — attributes 331, not 333.
        path = self._write_transcript([
            self._assistant("msg-stream", "2026-01-01T00:00:10Z", output=1),
            self._assistant("msg-stream", "2026-01-01T00:00:11Z", output=1),
            self._assistant("msg-stream", "2026-01-01T00:00:12Z", output=331,
                            tools=("Bash",)),
        ])
        by_tool = br.aggregate_tools([path], self._since())
        self.assertEqual(by_tool, {"Bash": {"calls": 1, "output": 331}})

    def test_total_preserves_the_deduplicated_sum(self):
        records = [
            self._assistant("msg-1", "2026-01-01T00:00:10Z", output=100,
                            tools=("Bash", "Read", "Edit")),
            self._assistant("msg-2", "2026-01-01T00:00:20Z", output=55),
            self._assistant("msg-3", "2026-01-01T00:00:30Z", output=7,
                            tools=("Bash",)),
            self._assistant("msg-3", "2026-01-01T00:00:31Z", output=7,
                            tools=("Bash",)),
        ]
        path = self._write_transcript(records)
        since = self._since()
        by_model, _timeline = br.aggregate([path], since)
        deduped = by_model["model-a"]["output"]
        self.assertEqual(deduped, 162)
        by_tool = br.aggregate_tools([path], since)
        self.assertEqual(
            sum(row["output"] for row in by_tool.values()), deduped)
        rendered = br.render_tool_table(by_tool)
        # msg-3's two records repeat one tool_use block, so the union across the
        # response's records counts it once: 3 calls (msg-1) + 1 (msg-3).
        self.assertIn("| **Total** | 4 | %s |" % br.human(deduped), rendered)

    def test_rows_sort_by_output_tokens_descending(self):
        path = self._write_transcript([
            self._assistant("msg-1", "2026-01-01T00:00:10Z", output=10,
                            tools=("Read",)),
            self._assistant("msg-2", "2026-01-01T00:00:20Z", output=300,
                            tools=("Bash",)),
            self._assistant("msg-3", "2026-01-01T00:00:30Z", output=90,
                            tools=("Edit",)),
        ])
        rendered = br.render_tool_table(
            br.aggregate_tools([path], self._since()))
        names = [line.split("|")[1].strip()
                 for line in rendered.splitlines()
                 if line.startswith("| ") and not line.startswith("| --- ")
                 and not line.startswith("| Tool ")]
        self.assertEqual(names, ["Bash", "Edit", "Read", "**Total**"])

    def test_skips_synthetic_records(self):
        path = self._write_transcript([
            self._assistant("msg-synth", "2026-01-01T00:00:10Z", output=999,
                            tools=("Bash",), model=br.SYNTHETIC_MODEL),
            self._assistant("msg-real", "2026-01-01T00:00:20Z", output=12,
                            tools=("Read",)),
        ])
        by_tool = br.aggregate_tools([path], self._since())
        self.assertEqual(by_tool, {"Read": {"calls": 1, "output": 12}})

    def test_empty_scope_prints_nothing_with_exit_zero(self):
        path = self._write_transcript([
            self._assistant("msg-1", "2026-01-01T00:00:10Z", output=100,
                            tools=("Bash",)),
        ])
        proc = subprocess.run(
            [sys.executable, os.path.join(SCRIPTS, "build_report.py"),
             "--transcript", path, "--project-dir", self.tmp,
             "--since", "2030-01-01T00:00:00Z", "--tool-table"],
            capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, "")

    def test_tool_table_prints_the_section(self):
        path = self._write_transcript([
            self._assistant("msg-1", "2026-01-01T00:00:10Z", output=100,
                            tools=("Bash",)),
        ])
        proc = subprocess.run(
            [sys.executable, os.path.join(SCRIPTS, "build_report.py"),
             "--transcript", path, "--project-dir", self.tmp,
             "--since", "2026-01-01T00:00:00Z", "--tool-table"],
            capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("## Token usage breakdown", proc.stdout)
        self.assertIn("| Tool | Calls | Output tokens |", proc.stdout)
        self.assertIn("| Bash | 1 | 100 |", proc.stdout)


if __name__ == "__main__":
    unittest.main()
