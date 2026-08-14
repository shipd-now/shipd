#!/usr/bin/env python3
"""Unit tests for video_ingest.py's slug derivation and audio extraction
(video-audio-extraction).

Slug derivation folds Unicode whitespace (macOS timestamps a screen
recording's filename with a U+202F narrow no-break space before "am"/"pm")
and every other non-alphanumeric run to a single ``-``, lowercased and
stripped of leading/trailing separators.

Audio extraction runs `ffprobe` (audio-stream check + duration) then
`ffmpeg` (16 kHz mono PCM) through the injectable runner — every path is
passed as its own argv element, never interpolated into a shell string, so
these tests assert on the exact argv list the fake runner receives."""

import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import video_ingest as vi  # noqa: E402

NBSP_FILENAME = "Screen Recording 2024-01-01 at 11.00.10 AM.mov"


class SlugDerivationTest(unittest.TestCase):
    def test_macos_recording_filename_yields_clean_slug(self):
        slug = vi.derive_slug(NBSP_FILENAME)
        self.assertEqual(slug, "screen-recording-2024-01-01-at-11-00-10-am")
        # only lowercase alphanumerics and single '-' separators
        self.assertRegex(slug, r"^[a-z0-9]+(-[a-z0-9]+)*$")

    def test_plain_filename(self):
        self.assertEqual(vi.derive_slug("demo.mov"), "demo")

    def test_strips_leading_and_trailing_separators(self):
        self.assertEqual(vi.derive_slug("__weird--name__.mov"), "weird-name")

    def test_collapses_runs_of_separators(self):
        self.assertEqual(vi.derive_slug("a   b---c.mov"), "a-b-c")


class ExtractAudioArgvTest(unittest.TestCase):
    """Pure argv-construction — no I/O, no subprocess."""

    def test_16khz_mono_wav_argv(self):
        argv = vi.extract_audio_argv("/in/source movie.mov", "/out/audio.wav")
        self.assertEqual(argv, [
            "ffmpeg", "-y", "-i", "/in/source movie.mov", "-vn",
            "-ar", "16000", "-ac", "1", "/out/audio.wav",
        ])

    def test_paths_are_argv_elements_not_a_shell_string(self):
        # A path containing shell metacharacters and the U+202F space must
        # survive as one argv element, never get concatenated into a single
        # command string.
        video = "/in/weird; rm -rf ~ .mov"
        argv = vi.extract_audio_argv(video, "/out/audio.wav")
        self.assertIn(video, argv)
        self.assertIsInstance(argv, list)
        self.assertTrue(all(isinstance(a, str) for a in argv))


class ProbeMediaTest(unittest.TestCase):
    """`probe_media` runs one ffprobe call through the injectable runner and
    parses its JSON stdout for audio-stream presence and duration."""

    def _fake_run(self, rc, stdout="", stderr=""):
        calls = []

        def run(args, input=None):
            calls.append(list(args))
            return rc, stdout, stderr

        run.calls = calls
        return run

    def test_probe_argv_passes_video_path_as_its_own_element(self):
        run = self._fake_run(0, stdout=json.dumps(
            {"format": {"duration": "12.5"},
             "streams": [{"codec_type": "audio"}]}))
        vi.probe_media("/in/a b.mov", run)
        self.assertEqual(len(run.calls), 1)
        self.assertIn("/in/a b.mov", run.calls[0])
        self.assertIsInstance(run.calls[0], list)

    def test_detects_audio_stream_and_duration(self):
        run = self._fake_run(0, stdout=json.dumps({
            "format": {"duration": "48.2"},
            "streams": [
                {"codec_type": "video"},
                {"codec_type": "audio"},
            ],
        }))
        has_audio, duration = vi.probe_media("/in/x.mov", run)
        self.assertTrue(has_audio)
        self.assertAlmostEqual(duration, 48.2)

    def test_silent_video_has_no_audio_stream(self):
        run = self._fake_run(0, stdout=json.dumps({
            "format": {"duration": "10.0"},
            "streams": [{"codec_type": "video"}],
        }))
        has_audio, _duration = vi.probe_media("/in/silent.mov", run)
        self.assertFalse(has_audio)


class ExtractAudioTest(unittest.TestCase):
    """`extract_audio` orchestrates the probe-then-extract sequence through
    the injectable runner, refusing a video with no audio stream."""

    def _fake_run(self, script):
        # `script` maps a probe/ffmpeg call to a canned (rc, stdout, stderr).
        calls = []

        def run(args, input=None):
            calls.append(list(args))
            key = args[0]
            return script[key]

        run.calls = calls
        return run

    def test_extracts_audio_when_stream_present(self):
        run = self._fake_run({
            "ffprobe": (0, json.dumps({
                "format": {"duration": "5.0"},
                "streams": [{"codec_type": "audio"}],
            }), ""),
            "ffmpeg": (0, "", ""),
        })
        duration = vi.extract_audio("/in/x.mov", "/out/audio.wav", run)
        self.assertAlmostEqual(duration, 5.0)
        kinds = [c[0] for c in run.calls]
        self.assertEqual(kinds, ["ffprobe", "ffmpeg"])

    def test_rejects_video_with_no_audio_stream(self):
        run = self._fake_run({
            "ffprobe": (0, json.dumps({
                "format": {"duration": "5.0"},
                "streams": [{"codec_type": "video"}],
            }), ""),
        })
        with self.assertRaises(vi.VideoIngestError) as ctx:
            vi.extract_audio("/in/silent.mov", "/out/audio.wav", run)
        self.assertIn("audio", str(ctx.exception).lower())
        # ffmpeg must never be invoked once the probe finds no audio stream.
        kinds = [c[0] for c in run.calls]
        self.assertEqual(kinds, ["ffprobe"])


if __name__ == "__main__":
    unittest.main()
