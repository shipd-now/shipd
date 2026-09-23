#!/usr/bin/env python3
"""Unit tests for `tape.py`'s pure annotation reader and `drive.py`'s
`tape` verb (drive-tape, drive-tape-timeline): a `#hold`/`#endhold` pair
becomes one protected window, an unclosed `#hold` extends to the recording
end, a `#ready` comment becomes `leadingCut`, an unannotated tape still
yields a valid (empty) timeline, and a tape's `Sleep` directives never
contribute to `spans` — every dead-air stretch is left to the
post-processor's spinner backstop instead (drive-postprocess).

`tape.py`'s annotation reader is stdlib-only and takes no subprocess, so
`TapeAnnotationTests` below exercises it directly with no `vhs` involved at
all. `TapeVerbTests` drives `drive.py tape` through the injectable-runner
seam `cmd_doctor` already established (`default_run`'s signature), the same
pattern this suite's `doctor --fix` path uses — so it too runs with no real
`vhs` binary anywhere on the machine."""

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from argparse import Namespace

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import tape  # noqa: E402
import drive  # noqa: E402
import postprocess as pp  # noqa: E402
from _stubs import stub_bindir as _bindir  # noqa: E402


class TapeAnnotationTests(unittest.TestCase):
    def test_hold_and_endhold_become_one_window(self):
        text = "\n".join([
            'Type "echo hi"',
            "Enter",
            "# hold",
            "Sleep 2s",
            "# endhold",
            'Type "echo done"',
        ])
        result = tape.read_annotations(text)
        # "echo hi" is 7 keystrokes plus Enter, at vhs's 50ms default:
        # 0.40s of real recording before the hold opens.
        self.assertEqual(result["holds"], [{"start": 0.40, "end": 2.40}])

    def test_unclosed_hold_extends_to_recording_end(self):
        text = "\n".join([
            "# hold",
            "Sleep 1s",
            'Type "echo hi"',
        ])
        result = tape.read_annotations(text)
        self.assertEqual(len(result["holds"]), 1)
        hold = result["holds"][0]
        self.assertEqual(hold["start"], 0.0)
        # No real duration is known to this pure reader, so an unclosed
        # hold's end is a sentinel far past any real recording rather than
        # the tape's own last offset.
        self.assertGreater(hold["end"], 3600.0)

    def test_ready_becomes_leading_cut(self):
        text = "\n".join([
            "Sleep 1500ms",
            "# ready",
            'Type "echo hi"',
        ])
        result = tape.read_annotations(text)
        self.assertAlmostEqual(result["leadingCut"], 1.5)

    def test_no_annotations_yields_empty_holds_and_no_leading_cut(self):
        text = "\n".join([
            'Type "echo hi"',
            "Enter",
            "Sleep 500ms",
        ])
        result = tape.read_annotations(text)
        self.assertEqual(result["holds"], [])
        self.assertIsNone(result["leadingCut"])

    def test_typing_advances_the_clock_at_the_default_speed(self):
        """Keystrokes are real recorded time. vhs types at 50ms per
        character by default, and a command launched by `Enter` runs
        concurrently with the `Sleep` that follows it — so typing is the
        term that would otherwise drift a hold away from its reveal."""
        text = "\n".join([
            'Type "abcde"',   # 5 keystrokes -> 0.25s
            "Enter",          # 1 keystroke  -> 0.05s
            "# ready",
        ])
        result = tape.read_annotations(text)
        self.assertAlmostEqual(result["leadingCut"], 0.30)

    def test_set_typing_speed_overrides_the_default(self):
        text = "\n".join([
            "Set TypingSpeed 100ms",
            'Type "abcde"',   # 5 keystrokes at 100ms -> 0.50s
            "# ready",
        ])
        result = tape.read_annotations(text)
        self.assertAlmostEqual(result["leadingCut"], 0.50)

    def test_per_line_type_speed_overrides_the_running_speed(self):
        text = "\n".join([
            'Type@200ms "ab"',   # 2 keystrokes at 200ms -> 0.40s
            'Type "ab"',         # 2 keystrokes at the 50ms default -> 0.10s
            "# ready",
        ])
        result = tape.read_annotations(text)
        self.assertAlmostEqual(result["leadingCut"], 0.50)

    def test_repeated_keypresses_cost_one_keystroke_each(self):
        text = "\n".join([
            "Enter 4",   # 4 keystrokes -> 0.20s
            "# ready",
        ])
        result = tape.read_annotations(text)
        self.assertAlmostEqual(result["leadingCut"], 0.20)

    def test_sleep_directives_contribute_no_spans(self):
        text = "\n".join([
            "Sleep 1s",
            "Sleep 2s",
            "Sleep 500ms",
        ])
        result = tape.read_annotations(text)
        self.assertNotIn("spans", result)

    def test_multiple_hold_windows_are_each_captured(self):
        text = "\n".join([
            "# hold",
            "Sleep 1s",
            "# endhold",
            'Type "echo hi"',
            "Sleep 1s",
            "# hold",
            "Sleep 2s",
            "# endhold",
        ])
        result = tape.read_annotations(text)
        self.assertEqual(result["holds"], [
            {"start": 0.0, "end": 1.0},
            # The typed "echo hi" between the windows costs 0.35s.
            {"start": 2.35, "end": 4.35},
        ])


class TapeVerbTests(unittest.TestCase):
    """`drive.py tape` (drive-tape) driven directly (`drive.cmd_tape`) with
    an injected `run`, following the injectable-runner pattern `cmd_doctor`
    already established (`default_run`'s signature) — `vhs` is never on
    this machine (per the plan), so every case here controls `vhs`
    presence through a PATH stub (`_stubs.stub_bindir`) and never lets a
    real `vhs` invocation happen (the injected `run` stands in for it)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="drive-tape-verb-")
        self._orig_path = os.environ.get("PATH", "")
        os.environ["PATH"] = _bindir(self.tmp, "bin-with-vhs", ["vhs"])

    def tearDown(self):
        os.environ["PATH"] = self._orig_path
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write_tape(self, output_name="demo.mp4", body='Type "echo hi"\n'):
        output_path = os.path.join(self.tmp, output_name)
        tape_path = os.path.join(self.tmp, "demo.tape")
        with open(tape_path, "w", encoding="utf-8") as fh:
            fh.write("Output %s\n" % output_path)
            fh.write(body)
        return tape_path, output_path

    def test_success_writes_video_and_timeline_and_prints_json(self):
        tape_path, video_path = self._write_tape()

        def fake_run(argv, input=None, env=None):
            self.assertEqual(argv, ["vhs", tape_path])
            # A real `vhs` run would itself create the declared Output
            # file; the injected runner stands in for that.
            with open(video_path, "wb") as fh:
                fh.write(b"fake-video-bytes")
            return 0, "", ""

        buf = io.StringIO()
        args = Namespace(tape=tape_path)
        with contextlib.redirect_stdout(buf):
            rc = drive.cmd_tape(args, run=fake_run)

        self.assertEqual(rc, 0)
        timeline_path = os.path.splitext(video_path)[0] + ".timeline.json"
        self.assertTrue(os.path.isfile(video_path))
        self.assertTrue(os.path.isfile(timeline_path))

        printed = json.loads(buf.getvalue().strip())
        self.assertEqual(printed["video"], video_path)
        self.assertEqual(printed["timeline"], timeline_path)

    def test_nonzero_vhs_exit_reports_failure_and_writes_no_timeline(self):
        tape_path, video_path = self._write_tape()

        def fake_run(argv, input=None, env=None):
            return 1, "", "vhs: something broke"

        args = Namespace(tape=tape_path)
        with self.assertRaises(drive.DriveError) as ctx:
            drive.cmd_tape(args, run=fake_run)
        self.assertIn("something broke", str(ctx.exception))

        timeline_path = os.path.splitext(video_path)[0] + ".timeline.json"
        self.assertFalse(os.path.isfile(timeline_path))

    def test_absent_vhs_names_remedy_and_records_nothing(self):
        tape_path, video_path = self._write_tape()
        os.environ["PATH"] = _bindir(self.tmp, "bin-without-vhs", [])

        def fake_run(argv, input=None, env=None):
            self.fail("vhs should never be invoked when absent from PATH")

        args = Namespace(tape=tape_path)
        with self.assertRaises(drive.DriveError) as ctx:
            drive.cmd_tape(args, run=fake_run)
        self.assertIn("brew install vhs", str(ctx.exception))

        self.assertFalse(os.path.isfile(video_path))
        timeline_path = os.path.splitext(video_path)[0] + ".timeline.json"
        self.assertFalse(os.path.isfile(timeline_path))


class TapeTimelineConvergenceTest(unittest.TestCase):
    """The seam that keeps both capture media converging on the same
    `post` (drive-postprocess): a tape's timeline carries no `spans` key
    at all (drive-tape-timeline — "carry `holds` and `leadingCut` only"),
    unlike `record`'s, which always writes one. `cmd_post`'s timeline
    loader (a plain `json.load` of whatever was written beside the
    recording) and the `compute_ff_spans` call `assemble` drives from the
    result must both tolerate that absence rather than assuming a
    `record`-shaped timeline."""

    def test_a_tape_timeline_round_trips_and_drives_compute_ff_spans(self):
        tape_text = "\n".join([
            "# hold",
            "Sleep 2s",
            "# endhold",
            "Sleep 1s",
            "# ready",
        ])
        timeline = tape.read_annotations(tape_text)
        self.assertNotIn("spans", timeline)

        # `cmd_post`'s own timeline loader is exactly this: `json.load` of
        # whatever `tape`/`record` wrote beside the recording.
        loaded = json.loads(json.dumps(timeline))
        self.assertNotIn("spans", loaded)

        # `assemble` (drive-postprocess) reads `spans`/`holds` purely via
        # `.get(...)`, never indexing — exercised directly here since
        # driving the full `assemble` needs a real video and `ffmpeg`. A
        # `dict["spans"]` regression here would raise `KeyError` instead.
        ff_spans = pp.compute_ff_spans(
            loaded.get("spans") or [], holds=loaded.get("holds") or [])
        self.assertEqual(ff_spans, [])


if __name__ == "__main__":
    unittest.main()
