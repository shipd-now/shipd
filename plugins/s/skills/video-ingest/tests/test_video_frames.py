#!/usr/bin/env python3
"""Unit tests for video_ingest.py's frame-candidate selection and extraction
(video-deixis-anchors, video-scene-peaks, video-frame-budget,
video-frame-extraction).

Deixis candidates are derived from the attributed transcript's spatial
demonstratives (`this`, `that`, `these`, `those`, `here`, `there` —
deliberately excluding the anaphoric `it`), each contributing a window of
candidates at `t-0.5`, `t`, `t+1.5` seconds, clamped to the recording. Scene
candidates are local maxima of `ffmpeg` scene scores, ranked within the
recording rather than against any absolute threshold. The two are merged,
deduplicated, and capped, and each survivor is extracted as a scaled PNG with
a provenance-carrying `frames.json` index.

Every function under test here is pure (no I/O, no subprocess) except the
extraction argv builder and the `ffmpeg` invocations, which go through the
injectable runner like every other subprocess call in this script."""

import contextlib
import io
import math
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import video_ingest as vi  # noqa: E402


# --- 1. Deixis anchors ------------------------------------------------------


class DeixisCandidatesTest(unittest.TestCase):
    """`deixis_candidates(words, duration)` is a pure function over the
    attributed transcript's words (video-deixis-anchors)."""

    def test_demonstrative_yields_three_frame_window(self):
        words = [{"text": "here", "start": 10.0, "end": 10.3}]
        candidates = vi.deixis_candidates(words, duration=60.0)
        times = sorted(c["time"] for c in candidates)
        self.assertEqual(times, [9.5, 10.0, 11.5])
        for c in candidates:
            self.assertEqual(c["reason"], "deixis")
            self.assertEqual(c["anchor"], "here")
            self.assertEqual(c["word_start"], 10.0)

    def test_anaphoric_it_yields_nothing(self):
        words = [{"text": "it", "start": 5.0, "end": 5.2}]
        self.assertEqual(vi.deixis_candidates(words, duration=60.0), [])

    def test_early_word_clamps_earlier_candidate_to_zero(self):
        words = [{"text": "this", "start": 0.2, "end": 0.4}]
        candidates = vi.deixis_candidates(words, duration=60.0)
        times = sorted(c["time"] for c in candidates)
        self.assertEqual(times[0], 0.0)

    def test_late_word_clamps_later_candidate_to_duration(self):
        words = [{"text": "there", "start": 59.8, "end": 60.0}]
        candidates = vi.deixis_candidates(words, duration=60.0)
        times = sorted(c["time"] for c in candidates)
        self.assertEqual(times[-1], 60.0)

    def test_punctuation_and_capitalization_normalized(self):
        words = [{"text": "This,", "start": 3.0, "end": 3.2}]
        candidates = vi.deixis_candidates(words, duration=60.0)
        self.assertEqual(len(candidates), 3)
        self.assertEqual(candidates[0]["anchor"], "this")

    def test_non_anchor_word_yields_nothing(self):
        words = [{"text": "hello", "start": 1.0, "end": 1.2}]
        self.assertEqual(vi.deixis_candidates(words, duration=60.0), [])

    def test_every_deixis_word_is_covered(self):
        for word in sorted(vi.DEIXIS_WORDS):
            words = [{"text": word, "start": 20.0, "end": 20.2}]
            candidates = vi.deixis_candidates(words, duration=60.0)
            self.assertEqual(len(candidates), 3, word)


# --- 2. Scene peaks ----------------------------------------------------------


SCENE_SCORE_FIXTURE = """\
frame:0    pts:0       pts_time:0
lavfi.scene_score=0.000000
frame:1    pts:1001    pts_time:0.5
lavfi.scene_score=0.010000
frame:2    pts:2002    pts_time:1.0
lavfi.scene_score=0.050000
frame:3    pts:3003    pts_time:1.5
lavfi.scene_score=0.002000
"""


class ParseSceneScoresTest(unittest.TestCase):
    """`parse_scene_scores(text)` is a pure function over `ffmpeg`'s
    `metadata=print` output (video-scene-peaks)."""

    def test_parses_pts_time_and_score_pairs_in_order(self):
        pairs = vi.parse_scene_scores(SCENE_SCORE_FIXTURE)
        self.assertEqual(pairs, [
            (0.0, 0.0),
            (0.5, 0.01),
            (1.0, 0.05),
            (1.5, 0.002),
        ])

    def test_empty_text_yields_empty_list(self):
        self.assertEqual(vi.parse_scene_scores(""), [])

    def test_ignores_unrelated_lines(self):
        text = "some ffmpeg banner line\n" + SCENE_SCORE_FIXTURE
        pairs = vi.parse_scene_scores(text)
        self.assertEqual(len(pairs), 4)


class SceneCandidatesTest(unittest.TestCase):
    """`scene_candidates(scores, duration)` selects local maxima ranked
    within the recording, never against an absolute threshold
    (video-scene-peaks)."""

    def test_only_local_maxima_are_eligible(self):
        # 1.0 at t=10 is a local max (neighbours 0.0, 0.01); 0.02 at t=20
        # is not a local max relative to its neighbours (0.01, 0.03).
        scores = [(0.0, 0.0), (10.0, 1.0), (15.0, 0.01), (20.0, 0.02),
                  (25.0, 0.03)]
        candidates = vi.scene_candidates(scores, duration=30.0)
        times = [c["time"] for c in candidates]
        self.assertIn(10.0, times)
        self.assertNotIn(20.0, times)

    def test_zero_scoring_frames_never_selected(self):
        scores = [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0)]
        self.assertEqual(vi.scene_candidates(scores, duration=3.0), [])

    def test_close_peaks_collapse_to_higher_scoring(self):
        # Two local maxima within SCENE_PEAK_MIN_GAP_SECONDS (1.0s) of each
        # other: only the higher-scoring one survives.
        scores = [
            (0.0, 0.0),
            (10.0, 0.05), (10.3, 0.001), (10.6, 0.08), (10.9, 0.001),
            (20.0, 0.0),
        ]
        candidates = vi.scene_candidates(scores, duration=30.0)
        times = [c["time"] for c in candidates]
        self.assertNotIn(10.0, times)
        self.assertIn(10.6, times)

    def test_caps_at_ceil_duration_over_seconds_per_frame(self):
        # duration=25 -> ceil(25/10) = 3 peaks allowed even though more local
        # maxima are available, well separated so none collapse.
        scores = [(0.0, 0.0)]
        t = 1.0
        while t < 24.0:
            scores.append((t, 0.0))
            scores.append((t + 0.5, 0.05 + 0.001 * t))
            scores.append((t + 1.0, 0.0))
            t += 3.0
        candidates = vi.scene_candidates(scores, duration=25.0)
        self.assertLessEqual(len(candidates), math.ceil(25.0 / 10.0))

    def test_kept_peaks_ranked_by_descending_score(self):
        scores = [
            (0.0, 0.0),
            (5.0, 0.02), (6.0, 0.0),
            (10.0, 0.09), (11.0, 0.0),
            (15.0, 0.05), (16.0, 0.0),
            (20.0, 0.03), (21.0, 0.0),
        ]
        # ceil(25/10) = 3 kept, of the four local maxima 0.02/0.09/0.05/0.03
        # -> top 3 by score: 0.09, 0.05, 0.03
        candidates = vi.scene_candidates(scores, duration=25.0)
        times = sorted(c["time"] for c in candidates)
        self.assertEqual(times, [10.0, 15.0, 20.0])

    def test_no_absolute_threshold_applied(self):
        # Every score sits far below the conventional 0.1/0.3 cut-detection
        # thresholds, but the relative peak is still selected.
        scores = [(0.0, 0.0), (5.0, 0.001), (10.0, 0.02), (15.0, 0.001)]
        candidates = vi.scene_candidates(scores, duration=20.0)
        times = [c["time"] for c in candidates]
        self.assertIn(10.0, times)

    def test_all_zero_scores_yield_empty_result(self):
        scores = [(0.0, 0.0), (5.0, 0.0), (10.0, 0.0)]
        self.assertEqual(vi.scene_candidates(scores, duration=10.0), [])

    def test_candidates_carry_reason_and_score(self):
        scores = [(0.0, 0.0), (10.0, 0.05), (20.0, 0.0)]
        [candidate] = vi.scene_candidates(scores, duration=25.0)
        self.assertEqual(candidate["reason"], "scene")
        self.assertEqual(candidate["time"], 10.0)
        self.assertEqual(candidate["score"], 0.05)


# --- 3. Merge, dedup and cap ------------------------------------------------


class ResolveFrameCandidatesTest(unittest.TestCase):
    """`resolve_frame_candidates(deixis, scene, max_frames, duration)`
    merges, dedups and caps the two candidate streams by distributing the
    budget across the recording, logging every drop (video-frame-budget)."""

    def test_near_duplicates_collapse_keeping_earlier(self):
        deixis = [{"time": 10.0, "reason": "deixis", "anchor": "here",
                   "word_start": 10.0}]
        scene = [{"time": 10.2, "reason": "scene", "score": 0.05}]
        kept, _dropped = vi.resolve_frame_candidates(
            deixis, scene, max_frames=24, duration=20.0)
        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0]["time"], 10.0)
        self.assertEqual(kept[0]["reason"], "deixis")

    def test_cap_distributes_into_buckets_by_preference(self):
        # duration=45.0 with max_frames=3 makes three 15s-wide buckets:
        # [0,15) holds the t=5 deixis, [15,30) holds the t=15 deixis, and
        # [30,45) holds both scene candidates, where the higher-scoring one
        # (0.09 at t=40) wins the bucket over the lower-scoring one (0.05 at
        # t=30), which is then dropped since no empty bucket remains to
        # backfill it into.
        deixis = [
            {"time": 5.0, "reason": "deixis", "anchor": "here",
             "word_start": 5.0},
            {"time": 15.0, "reason": "deixis", "anchor": "there",
             "word_start": 15.0},
        ]
        scene = [
            {"time": 30.0, "reason": "scene", "score": 0.05},
            {"time": 40.0, "reason": "scene", "score": 0.09},
        ]
        kept, dropped = vi.resolve_frame_candidates(
            deixis, scene, max_frames=3, duration=45.0)
        self.assertEqual(len(kept), 3)
        self.assertEqual([c["time"] for c in kept], [5.0, 15.0, 40.0])
        self.assertEqual(len(dropped), 1)
        self.assertEqual(dropped[0]["time"], 30.0)

    def test_every_dropped_candidate_reported_on_stderr(self):
        deixis = [
            {"time": 5.0, "reason": "deixis", "anchor": "here",
             "word_start": 5.0},
            {"time": 15.0, "reason": "deixis", "anchor": "there",
             "word_start": 15.0},
        ]
        scene = [{"time": 30.0, "reason": "scene", "score": 0.05}]
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            kept, dropped = vi.resolve_frame_candidates(
                deixis, scene, max_frames=1, duration=40.0)
        self.assertEqual(len(kept), 1)
        self.assertEqual(len(dropped), 2)
        output = stderr.getvalue()
        for d in dropped:
            self.assertIn(str(d["time"]), output)
            self.assertIn(d["reason"], output)

    def test_no_candidates_yields_nothing_dropped(self):
        kept, dropped = vi.resolve_frame_candidates(
            [], [], max_frames=24, duration=0.0)
        self.assertEqual(kept, [])
        self.assertEqual(dropped, [])

    def test_under_cap_nothing_dropped(self):
        deixis = [{"time": 1.0, "reason": "deixis", "anchor": "here",
                   "word_start": 1.0}]
        scene = [{"time": 2.0, "reason": "scene", "score": 0.05}]
        kept, dropped = vi.resolve_frame_candidates(
            deixis, scene, max_frames=24, duration=5.0)
        self.assertEqual(len(kept), 2)
        self.assertEqual(dropped, [])


# --- 3b. Distribution across the timeline ------------------------------------


class DistributedCapTest(unittest.TestCase):
    """The cap distributes across the recording's duration instead of
    filling in time order, so a dense early cluster of candidates cannot
    starve candidates that occur later (video-frame-budget). Modelled on the
    measured failure: a 581-second walkthrough where every deixis candidate
    landed inside the first 48 seconds and every scene candidate — marking
    real UI transitions later in the recording — was dropped by the cap."""

    def test_cap_spreads_across_a_580_second_recording(self):
        # 40 deixis candidates all inside the first 50 seconds, 7 scene
        # candidates spread from 380s to 562s, capped at 24. The old
        # time-ordered-deixis-first rule keeps only early deixis candidates
        # and drops every scene candidate.
        deixis = [
            {"time": 1.0 + i * 1.2, "reason": "deixis", "anchor": "here",
             "word_start": 1.0 + i * 1.2}
            for i in range(40)
        ]
        scene = [
            {"time": t, "reason": "scene", "score": 0.01 * (i + 1)}
            for i, t in enumerate(
                [380.0, 410.0, 440.0, 470.0, 500.0, 530.0, 562.0])
        ]
        kept, _dropped = vi.resolve_frame_candidates(
            deixis, scene, max_frames=24, duration=580.0)
        self.assertEqual(len(kept), 24)
        times = [c["time"] for c in kept]
        self.assertTrue(any(t > 300.0 for t in times),
                         "no kept frame past 300s: %r" % times)
        self.assertTrue(any(c["reason"] == "scene" for c in kept),
                         "no scene candidate survived the cap")


class BucketPreferenceTest(unittest.TestCase):
    """Within a single occupied bucket, exactly one candidate wins by
    `_frame_candidate_rank` (video-frame-budget). Each case uses
    max_frames=2, duration=20.0 (two 10s-wide buckets) with a lone,
    unambiguous candidate in the second bucket so the cap is exceeded (3
    candidates over a 2-frame cap) and no backfill slot remains to rescue
    the bucket's loser."""

    def test_deixis_beats_scene_in_the_same_bucket(self):
        deixis = [{"time": 2.0, "reason": "deixis", "anchor": "here",
                   "word_start": 2.0}]
        scene = [
            {"time": 5.0, "reason": "scene", "score": 0.5},
            {"time": 15.0, "reason": "scene", "score": 0.1},
        ]
        kept, dropped = vi.resolve_frame_candidates(
            deixis, scene, max_frames=2, duration=20.0)
        times = [c["time"] for c in kept]
        self.assertIn(2.0, times)
        self.assertNotIn(5.0, times)
        self.assertEqual(dropped[0]["time"], 5.0)

    def test_higher_scoring_scene_wins_over_lower_scoring_scene(self):
        scene = [
            {"time": 2.0, "reason": "scene", "score": 0.02},
            {"time": 5.0, "reason": "scene", "score": 0.09},
            {"time": 15.0, "reason": "scene", "score": 0.5},
        ]
        kept, dropped = vi.resolve_frame_candidates(
            [], scene, max_frames=2, duration=20.0)
        times = [c["time"] for c in kept]
        self.assertIn(5.0, times)
        self.assertNotIn(2.0, times)
        self.assertEqual(dropped[0]["time"], 2.0)

    def test_earlier_deixis_wins_over_later_deixis(self):
        deixis = [
            {"time": 2.0, "reason": "deixis", "anchor": "here",
             "word_start": 2.0},
            {"time": 8.0, "reason": "deixis", "anchor": "there",
             "word_start": 8.0},
            {"time": 15.0, "reason": "deixis", "anchor": "here",
             "word_start": 15.0},
        ]
        kept, dropped = vi.resolve_frame_candidates(
            deixis, [], max_frames=2, duration=20.0)
        times = [c["time"] for c in kept]
        self.assertIn(2.0, times)
        self.assertNotIn(8.0, times)
        self.assertEqual(dropped[0]["time"], 8.0)


class BackfillTest(unittest.TestCase):
    """Slots left by empty buckets are backfilled from the remaining
    unselected candidates, so a sparse recording still reaches the cap
    (video-frame-budget)."""

    def test_empty_buckets_backfill_up_to_the_cap(self):
        # duration=100, max_frames=5 -> five 20s-wide buckets, but all 6
        # candidates fall inside the first ([0,20)); the other four buckets
        # are empty. One candidate wins its bucket outright and the
        # remaining four slots are backfilled from the bucket's losers
        # (earliest first), still reaching the 5-frame cap.
        deixis = [
            {"time": t, "reason": "deixis", "anchor": "here",
             "word_start": t}
            for t in [1.0, 3.0, 5.0, 7.0, 9.0, 11.0]
        ]
        kept, dropped = vi.resolve_frame_candidates(
            deixis, [], max_frames=5, duration=100.0)
        self.assertEqual(len(kept), 5)
        self.assertEqual(len(dropped), 1)
        self.assertEqual(dropped[0]["time"], 11.0)

    def test_fewer_candidates_than_cap_keeps_all_and_reports_nothing(self):
        deixis = [
            {"time": 1.0, "reason": "deixis", "anchor": "here",
             "word_start": 1.0},
            {"time": 50.0, "reason": "deixis", "anchor": "there",
             "word_start": 50.0},
        ]
        scene = [{"time": 90.0, "reason": "scene", "score": 0.2}]
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            kept, dropped = vi.resolve_frame_candidates(
                deixis, scene, max_frames=5, duration=100.0)
        self.assertEqual(len(kept), 3)
        self.assertEqual(dropped, [])
        self.assertEqual(stderr.getvalue(), "")


class DistributedDropReportingTest(unittest.TestCase):
    """Every candidate dropped by the distributed cap — whether it lost its
    bucket or lost the backfill pass — is still reported on stderr with its
    timestamp and reason (video-frame-budget), the same guarantee the old
    time-ordered cap made."""

    def test_every_candidate_dropped_by_the_distributed_cap_is_reported(self):
        # Two occupied buckets, each with a loser, and no empty bucket to
        # backfill into: three candidates are dropped in total, one a
        # bucket's un-won deixis candidate and two un-won scene candidates —
        # every one of them must still show up on stderr.
        deixis = [
            {"time": 2.0, "reason": "deixis", "anchor": "here",
             "word_start": 2.0},
            {"time": 5.0, "reason": "deixis", "anchor": "there",
             "word_start": 5.0},
        ]
        scene = [
            {"time": 10.0, "reason": "scene", "score": 0.05},
            {"time": 25.0, "reason": "scene", "score": 0.1},
            {"time": 30.0, "reason": "scene", "score": 0.9},
        ]
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            kept, dropped = vi.resolve_frame_candidates(
                deixis, scene, max_frames=2, duration=40.0)
        self.assertEqual(len(kept), 2)
        self.assertEqual(len(dropped), 3)
        output = stderr.getvalue()
        for d in dropped:
            self.assertIn("%.2fs" % d["time"], output)
            self.assertIn(d["reason"], output)


# --- 3c. Scene floor ---------------------------------------------------------


class SceneFloorTest(unittest.TestCase):
    """`resolve_frame_candidates` reserves a scene floor after bucket winners
    are chosen: buckets whose winner is deixis and which also hold a scene
    candidate convert to that scene candidate, highest-scoring first, until
    `int(max_frames * scene_floor)` is met or no convertible bucket remains,
    so a recording dense in deixis anchors cannot starve every scene frame
    (video-frame-budget)."""

    def test_scene_floor_is_reserved_from_deixis_buckets(self):
        # 8 buckets (duration=80, max_frames=8), one deixis candidate per
        # bucket so every bucket initially wins on deixis. Buckets 0-2 also
        # hold a scene candidate; floor = int(8*0.25) = 2, so the two
        # highest-scoring convertible buckets (0.9, 0.7) flip to scene and
        # the third (0.3) does not.
        deixis = [
            {"time": 2.0 + i * 10.0, "reason": "deixis", "anchor": "here",
             "word_start": 2.0 + i * 10.0}
            for i in range(8)
        ]
        scene = [
            {"time": 5.0, "reason": "scene", "score": 0.9},
            {"time": 15.0, "reason": "scene", "score": 0.7},
            {"time": 25.0, "reason": "scene", "score": 0.3},
        ]
        kept, _dropped = vi.resolve_frame_candidates(
            deixis, scene, max_frames=8, duration=80.0, scene_floor=0.25)
        self.assertEqual(len(kept), 8)
        scene_kept = [c for c in kept if c["reason"] == "scene"]
        self.assertGreaterEqual(len(scene_kept), int(8 * 0.25))
        scene_times = {c["time"] for c in scene_kept}
        self.assertIn(5.0, scene_times)
        self.assertIn(15.0, scene_times)
        self.assertNotIn(25.0, scene_times)

    def test_floor_never_exceeds_available_scene_candidates(self):
        # Same 8 deixis-won buckets, but only one scene candidate exists at
        # all, so the floor of 2 cannot be reached — only the one available
        # scene candidate converts and no further deixis winner is
        # displaced.
        deixis = [
            {"time": 2.0 + i * 10.0, "reason": "deixis", "anchor": "here",
             "word_start": 2.0 + i * 10.0}
            for i in range(8)
        ]
        scene = [{"time": 5.0, "reason": "scene", "score": 0.9}]
        kept, _dropped = vi.resolve_frame_candidates(
            deixis, scene, max_frames=8, duration=80.0, scene_floor=0.25)
        self.assertEqual(len(kept), 8)
        scene_kept = [c for c in kept if c["reason"] == "scene"]
        self.assertEqual(len(scene_kept), 1)
        self.assertEqual(scene_kept[0]["time"], 5.0)
        deixis_kept = [c for c in kept if c["reason"] == "deixis"]
        self.assertEqual(len(deixis_kept), 7)

    def test_conversion_does_not_change_kept_count(self):
        deixis = [
            {"time": 2.0 + i * 10.0, "reason": "deixis", "anchor": "here",
             "word_start": 2.0 + i * 10.0}
            for i in range(4)
        ]
        scene = [{"time": 5.0, "reason": "scene", "score": 0.9}]
        kept_without_floor, _ = vi.resolve_frame_candidates(
            deixis, scene, max_frames=4, duration=40.0, scene_floor=0.0)
        kept_with_floor, _ = vi.resolve_frame_candidates(
            deixis, scene, max_frames=4, duration=40.0, scene_floor=0.25)
        self.assertEqual(len(kept_without_floor), len(kept_with_floor))

    def test_floor_already_satisfied_leaves_deixis_winner_in_place(self):
        # Bucket 1 holds only a scene candidate, so it wins outright and
        # already satisfies floor=int(4*0.25)=1 before any conversion pass
        # runs. Bucket 0's deixis winner is therefore left in place even
        # though it shares its bucket with a higher-scoring scene candidate.
        deixis = [
            {"time": 2.0, "reason": "deixis", "anchor": "here",
             "word_start": 2.0},
            {"time": 22.0, "reason": "deixis", "anchor": "here",
             "word_start": 22.0},
            {"time": 32.0, "reason": "deixis", "anchor": "here",
             "word_start": 32.0},
        ]
        scene = [
            {"time": 5.0, "reason": "scene", "score": 0.9},
            {"time": 15.0, "reason": "scene", "score": 0.5},
        ]
        kept, _dropped = vi.resolve_frame_candidates(
            deixis, scene, max_frames=4, duration=40.0, scene_floor=0.25)
        self.assertEqual(len(kept), 4)
        times = {c["time"] for c in kept}
        self.assertIn(2.0, times)
        self.assertNotIn(5.0, times)
        scene_kept = [c for c in kept if c["reason"] == "scene"]
        self.assertEqual(len(scene_kept), 1)
        self.assertEqual(scene_kept[0]["time"], 15.0)


# --- 4. Extraction and index -------------------------------------------------


class FrameExtractionArgvTest(unittest.TestCase):
    """Extraction argv is pure — seeks to the candidate's timestamp, requests
    a single frame, writes a scaled `.png` under `frames/`
    (video-frame-extraction)."""

    def test_argv_seeks_scales_and_writes_png(self):
        argv = vi.extract_frame_argv("/in/video.mov", 12.94,
                                     "/bundle/frames/000-12.94s.png")
        self.assertEqual(argv[0], "ffmpeg")
        self.assertIn("-ss", argv)
        self.assertIn("12.94", argv)
        self.assertIn("-i", argv)
        self.assertIn("/in/video.mov", argv)
        self.assertIn("-vframes", argv)
        self.assertIn("1", argv)
        self.assertTrue(argv[-1].endswith(".png"))
        self.assertIn("/bundle/frames/000-12.94s.png", argv)
        self.assertIn(
            "scale='min(1568,iw)':'min(1568,ih)':"
            "force_original_aspect_ratio=decrease",
            argv)


class FramesIndexTest(unittest.TestCase):
    """`frames.json` carries a schema `version` and a `frames` array whose
    entries carry provenance, not just a filename (video-frame-extraction)."""

    def test_deixis_entry_schema(self):
        candidates = [{"time": 10.0, "reason": "deixis", "anchor": "here",
                       "word_start": 10.0, "file": "000-10.00s.png"}]
        index = vi.build_frames_index(candidates)
        self.assertIn("version", index)
        [entry] = index["frames"]
        self.assertEqual(entry["file"], "000-10.00s.png")
        self.assertEqual(entry["time"], 10.0)
        self.assertEqual(entry["reason"], "deixis")
        self.assertEqual(entry["anchor"], "here")
        self.assertEqual(entry["word_start"], 10.0)

    def test_scene_entry_schema(self):
        candidates = [{"time": 20.0, "reason": "scene", "score": 0.05,
                       "file": "000-20.00s.png"}]
        index = vi.build_frames_index(candidates)
        [entry] = index["frames"]
        self.assertEqual(entry["file"], "000-20.00s.png")
        self.assertEqual(entry["time"], 20.0)
        self.assertEqual(entry["reason"], "scene")
        self.assertEqual(entry["score"], 0.05)

    def test_no_candidates_yields_empty_array(self):
        index = vi.build_frames_index([])
        self.assertEqual(index["frames"], [])
        self.assertEqual(index["version"], vi.FRAMES_SCHEMA_VERSION)


if __name__ == "__main__":
    unittest.main()
