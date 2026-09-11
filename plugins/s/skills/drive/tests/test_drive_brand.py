#!/usr/bin/env python3
"""Unit tests for the shipd-branded video frames (drive-brand-frames): the
title card's title resolution — `change/<slug>` branch, then an explicitly
supplied title, then a fixed default, and never an issue-tracker identifier
— and the fast-forward badge's geometry and its fast-forward-only scope.

Title resolution (`postprocess.resolve_title`, task 6.8) is a pure function:
`drive.py` is the one that asks git which branch the working tree is on, and
hands the resolved branch name (or `None`) in as a plain string, so this
suite never shells out to git and never touches a real repository. The badge
geometry constants (`BADGE_WIDTH`/`BADGE_HEIGHT`) and `badge_position` (task
6.4) are already pure. The "badge only marks fast-forwarded stretches"
scenario is exercised through `postprocess.assemble` itself, via the same
injectable `run` subprocess seam every other assembly test in this suite
uses — no real `ffmpeg` involved, matching `postprocess.py`'s stdlib-only
contract.
"""

import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import postprocess as pp  # noqa: E402


class TitleResolutionTests(unittest.TestCase):
    def test_title_comes_from_the_change_branch(self):
        # drive-brand-frames' own scenario: on `change/drive-skill` with no
        # explicit title supplied, the card's title reads `drive-skill`.
        self.assertEqual(
            pp.resolve_title(branch="change/drive-skill", supplied=None),
            "drive-skill")

    def test_falls_back_to_a_supplied_title_off_a_change_branch(self):
        self.assertEqual(
            pp.resolve_title(branch="main", supplied="Checkout flow demo"),
            "Checkout flow demo")
        # No resolvable branch at all (e.g. detached HEAD) behaves the same
        # way as a non-`change/<slug>` branch.
        self.assertEqual(
            pp.resolve_title(branch=None, supplied="Checkout flow demo"),
            "Checkout flow demo")

    def test_falls_back_to_the_fixed_default_with_neither(self):
        self.assertEqual(pp.resolve_title(branch=None, supplied=None),
                         pp.DEFAULT_TITLE)
        self.assertEqual(pp.resolve_title(branch="main", supplied=None),
                         pp.DEFAULT_TITLE)
        self.assertTrue(pp.DEFAULT_TITLE)

    def test_title_is_never_derived_from_an_issue_tracker_identifier(self):
        # A branch that merely *looks* like it carries a ticket id (but is
        # not `change/<slug>`) must never surface that identifier as the
        # title — drive-brand-frames explicitly forbids deriving the title
        # from an issue-tracker id, so this falls through to the supplied
        # title (absent here) and then the fixed default, exactly like any
        # other non-`change/<slug>` branch.
        ticket_branch = "PROJ-1234-fix-the-thing"
        resolved = pp.resolve_title(branch=ticket_branch, supplied=None)
        self.assertEqual(resolved, pp.DEFAULT_TITLE)
        self.assertNotIn("PROJ-1234", resolved)


class BadgeGeometryTests(unittest.TestCase):
    def test_badge_geometry_fits_the_1280x720_frame(self):
        # drive-brand-frames: "at a 1280 by 720 frame it SHALL be at most 44
        # pixels tall and at most 180 pixels wide."
        self.assertLessEqual(pp.BADGE_HEIGHT, 44)
        self.assertLessEqual(pp.BADGE_WIDTH, 180)

    def test_badge_position_stays_inside_the_frame_for_every_corner(self):
        for corner in ("top-left", "top-right", "bottom-left",
                       "bottom-right"):
            x, y = pp.badge_position(corner, 1280, 720)
            self.assertGreaterEqual(x, 0)
            self.assertGreaterEqual(y, 0)
            self.assertLessEqual(x + pp.BADGE_WIDTH, 1280)
            self.assertLessEqual(y + pp.BADGE_HEIGHT, 720)


class BadgeOverlayScopeTests(unittest.TestCase):
    """The badge overlay is composited only over fast-forwarded segments —
    exercised through `assemble()`'s real segment-encoding decisions, with
    every subprocess call faked out through the injectable `run` seam."""

    def test_badge_only_composited_over_fast_forwarded_segments(self):
        calls = []

        def fake_run(argv):
            calls.append(list(argv))
            if argv[0] == "ffprobe":
                # The whole recording is 20s; nothing else in this test
                # reads this value except `probe_duration`.
                return (0, "20.0", "")
            # Every other call (the leading-cut content-start probe, each
            # segment encode, the concat pass) succeeds trivially — none of
            # them need real output, since `assemble()`'s own bookkeeping
            # (not ffmpeg's actual bytes) is what this test inspects.
            return (0, "", "")

        # One 10s fast-forward-eligible span in the middle of a 20s body,
        # with no leading cut — so `build_segments` yields exactly three
        # segments: normal, fast-forward, normal (see
        # `test_drive_postprocess.py`'s equivalent segment-shape test).
        timeline = {
            "leadingCut": 0.0,
            "spans": [{"start": 5.0, "end": 15.0}],
            "holds": [],
        }

        workdir = tempfile.mkdtemp(prefix="drive-brand-test-")
        self.addCleanup(shutil.rmtree, workdir, ignore_errors=True)
        out_path = os.path.join(workdir, "out.mp4")

        pp.assemble("input.mp4", timeline, out_path, fake_run,
                   workdir=workdir, badge_path="badge.png",
                   badge_corner="bottom-right")

        # Identify the three per-segment encode calls by their shared
        # `trim=start=` filter (both badged and unbadged segment calls
        # carry it; the ffprobe/content-start/concat calls do not).
        segment_calls = [
            c for c in calls
            if any("trim=start=" in str(a) for a in c)]
        self.assertEqual(len(segment_calls), 3, calls)

        badged = [c for c in segment_calls
                 if any("overlay=" in str(a) for a in c)]
        # Only the one fast-forwarded segment (the middle one) gets the
        # badge composited over it.
        self.assertEqual(len(badged), 1, segment_calls)

        unbadged = [c for c in segment_calls if c not in badged]
        self.assertEqual(len(unbadged), 2)
        for call in unbadged:
            self.assertFalse(any("overlay=" in str(a) for a in call))


if __name__ == "__main__":
    unittest.main()
