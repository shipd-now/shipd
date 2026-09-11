#!/usr/bin/env python3
"""Unit tests for `postprocess.py`'s pure span algebra (drive-postprocess).

These tests exercise only the algebra that decides *which stretches of the
recording get fast-forwarded* — merging blocks split by a short blip,
dropping blocks under the five-second floor, subtracting every `holds`
window, unioning the spinner backstop's spans with the timeline's, building
the ordered segment list, and resolving the leading-cut precedence. None of
that requires a real video or `ffmpeg`: it operates purely on `{"start",
"end"}` second-offset dicts, so this suite never shells out and never
imports `ffmpeg`-adjacent code (the spinner backstop's own sampling, and the
assembly that actually encodes segments, are covered separately once
`ffmpeg` is in play).

`postprocess.py` is stdlib-only Python 3, matching `drive.py`'s split, so
this suite runs with nothing beyond the standard library installed."""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import postprocess as pp  # noqa: E402


class SpanAlgebraTests(unittest.TestCase):
    def test_short_static_stretch_is_not_fast_forwarded(self):
        # A three-second static stretch sits below the five-second floor, so
        # it never becomes a fast-forward-eligible span.
        timeline_spans = [{"start": 3.0, "end": 6.0}]
        ff_spans = pp.compute_ff_spans(timeline_spans, holds=[])
        self.assertEqual(ff_spans, [])

        segments = pp.build_segments(10.0, ff_spans)
        self.assertEqual(segments, [
            {"start": 0.0, "end": 10.0, "speed": pp.NORMAL_SPEED},
        ])

    def test_stretch_inside_holds_window_is_excluded(self):
        # An eight-second stretch is well above the floor, but it sits
        # entirely inside a `holds` window (e.g. an annotation card the
        # viewer must read), so it is excluded from fast-forward regardless
        # of how static it is.
        timeline_spans = [{"start": 2.0, "end": 10.0}]
        holds = [{"start": 2.0, "end": 10.0}]
        ff_spans = pp.compute_ff_spans(timeline_spans, holds=holds)
        self.assertEqual(ff_spans, [])

        segments = pp.build_segments(12.0, ff_spans)
        self.assertEqual(segments, [
            {"start": 0.0, "end": 12.0, "speed": pp.NORMAL_SPEED},
        ])

    def test_sub_floor_fragments_left_by_a_mid_span_hold_are_dropped(self):
        # A 20s dead-air block is well over the floor, but a 16s hold sits
        # in its exact middle (e.g. an annotation shown partway through a
        # long wait). Subtracting the hold leaves two ~2s remainders on
        # either side — each below the five-second floor on its own, and
        # neither is "a dead-air block of at least five seconds", so
        # neither should become fast-forward-eligible (regression: the
        # floor must be re-applied to what subtraction actually produced,
        # not only to the pre-subtraction block).
        timeline_spans = [{"start": 0.0, "end": 20.0}]
        holds = [{"start": 2.0, "end": 18.0}]
        ff_spans = pp.compute_ff_spans(timeline_spans, holds=holds)
        self.assertEqual(ff_spans, [])

        segments = pp.build_segments(20.0, ff_spans)
        self.assertEqual(segments, [
            {"start": 0.0, "end": 20.0, "speed": pp.NORMAL_SPEED},
        ])

    def test_spinner_backstop_spans_are_unioned_with_the_timeline(self):
        # The timeline itself marked no span here, but the spinner backstop
        # (an animated spinner confined to a small region, which pixel
        # freeze detection structurally cannot see) reports a ten-second
        # waiting stretch. It is unioned into the fast-forward-eligible set
        # exactly as if the timeline had recorded it.
        timeline_spans = []
        backstop_spans = [{"start": 5.0, "end": 15.0}]
        ff_spans = pp.compute_ff_spans(
            timeline_spans, holds=[], backstop_spans=backstop_spans)
        self.assertEqual(ff_spans, [{"start": 5.0, "end": 15.0}])

        # The union itself is a general pure operation, independent of the
        # floor/holds steps: two overlapping spans merge into one.
        merged = pp.union_spans(
            [{"start": 0.0, "end": 3.0}], [{"start": 2.0, "end": 5.0}])
        self.assertEqual(merged, [{"start": 0.0, "end": 5.0}])

    def test_segments_cover_the_whole_body_with_nothing_cut(self):
        duration = 20.0
        ff_spans = [{"start": 5.0, "end": 12.0}]
        segments = pp.build_segments(duration, ff_spans)

        # Contiguous, gap-free, and starting/ending exactly on the body.
        self.assertEqual(segments[0]["start"], 0.0)
        self.assertEqual(segments[-1]["end"], duration)
        for prev, nxt in zip(segments, segments[1:]):
            self.assertEqual(prev["end"], nxt["start"])
        total = sum(seg["end"] - seg["start"] for seg in segments)
        self.assertEqual(total, duration)

        # The fast-forward-eligible stretch is represented as its own
        # segment, tagged accordingly.
        ff_segments = [s for s in segments if s["speed"] == pp.FF_SPEED]
        self.assertEqual(ff_segments, [
            {"start": 5.0, "end": 12.0, "speed": pp.FF_SPEED},
        ])

    def test_leading_cut_prefers_marked_then_detected_then_fallback(self):
        # An explicit `leadingCut` from the timeline always wins.
        self.assertEqual(
            pp.resolve_leading_cut(leading_cut=4.0,
                                    detected_content_start=9.0),
            4.0)
        # With no explicit mark, the detected content start is used.
        self.assertEqual(
            pp.resolve_leading_cut(leading_cut=None,
                                    detected_content_start=9.0),
            9.0)
        # With neither available, the fixed fallback applies.
        self.assertEqual(
            pp.resolve_leading_cut(leading_cut=None,
                                    detected_content_start=None),
            pp.FALLBACK_LEADING_CUT_SECONDS)


if __name__ == "__main__":
    unittest.main()
