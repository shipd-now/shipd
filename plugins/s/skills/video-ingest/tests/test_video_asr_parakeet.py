#!/usr/bin/env python3
"""Unit tests for the parakeet ASR backend's transcription call
(video-asr-chunking).

`parakeet_mlx`'s `model.transcribe` defaults to `chunk_duration=None`, which
encodes the whole recording in one forward pass — activation memory then scales
with the recording's length, and a 19-minute screen recording exhausted 25 GB
of unified memory before the kernel killed the backend. The backend therefore
always passes an explicit chunk window.

The backend's heavy import (`from parakeet_mlx import from_pretrained`) lives
inside `main()`, so the module imports without the dependency and these tests
drive `main()` against a stub injected into `sys.modules` — no `mlx`, no model
cache, and no audio. That keeps the suite passing on Ubuntu CI, matching the
subprocess-stubbing rule the rest of the video-ingest tests follow."""

import contextlib
import io
import json
import os
import sys
import unittest
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
BACKENDS = os.path.normpath(os.path.join(HERE, "..", "scripts", "backends"))
if BACKENDS not in sys.path:
    sys.path.insert(0, BACKENDS)

import asr_parakeet  # noqa: E402


class _Token(SimpleNamespace):
    pass


@contextlib.contextmanager
def stub_parakeet(calls):
    """Install a fake `parakeet_mlx` module whose `transcribe` records the
    keyword arguments it was called with, then restore whatever was there."""

    def transcribe(path, **kwargs):
        calls.append({"path": path, "kwargs": kwargs})
        token = _Token(start=0.0, end=0.5, text=" hello")
        return SimpleNamespace(sentences=[SimpleNamespace(tokens=[token])])

    module = SimpleNamespace(
        from_pretrained=lambda model_id: SimpleNamespace(transcribe=transcribe))
    previous = sys.modules.get("parakeet_mlx")
    sys.modules["parakeet_mlx"] = module
    try:
        yield
    finally:
        if previous is None:
            del sys.modules["parakeet_mlx"]
        else:
            sys.modules["parakeet_mlx"] = previous


def run_main(argv):
    """Run the backend's `main` with stdout captured, returning
    `(rc, stdout, calls)`."""
    calls = []
    out = io.StringIO()
    with stub_parakeet(calls), contextlib.redirect_stdout(out):
        rc = asr_parakeet.main(argv)
    return rc, out.getvalue(), calls


class ParakeetChunkingTest(unittest.TestCase):
    """The transcription call is always chunked unless explicitly disabled."""

    def test_default_run_passes_the_chunk_window(self):
        rc, _stdout, calls = run_main(["--audio", "/tmp/a.wav"])
        self.assertEqual(rc, 0)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["kwargs"]["chunk_duration"],
                         asr_parakeet.DEFAULT_CHUNK_DURATION)
        self.assertEqual(calls[0]["kwargs"]["overlap_duration"],
                         asr_parakeet.DEFAULT_OVERLAP_DURATION)

    def test_default_chunk_window_is_bounded(self):
        """The whole point of the default is that it does not grow with the
        recording — a `None` default would reinstate the unchunked pass."""
        self.assertIsInstance(asr_parakeet.DEFAULT_CHUNK_DURATION, float)
        self.assertGreater(asr_parakeet.DEFAULT_CHUNK_DURATION, 0)

    def test_explicit_window_overrides_the_default(self):
        rc, _stdout, calls = run_main(
            ["--audio", "/tmp/a.wav", "--chunk-duration", "30",
             "--overlap-duration", "5"])
        self.assertEqual(rc, 0)
        self.assertEqual(calls[0]["kwargs"]["chunk_duration"], 30.0)
        self.assertEqual(calls[0]["kwargs"]["overlap_duration"], 5.0)

    def test_zero_disables_chunking(self):
        """`0` maps to the library's `None`, matching parakeet-mlx's own CLI
        contract — an explicit opt-out, never the default."""
        rc, _stdout, calls = run_main(
            ["--audio", "/tmp/a.wav", "--chunk-duration", "0"])
        self.assertEqual(rc, 0)
        self.assertIsNone(calls[0]["kwargs"]["chunk_duration"])

    def test_overlap_at_or_past_the_window_is_refused(self):
        """An overlap >= the window makes the library's chunk loop step
        non-positive: negative empties the range, so nothing is encoded and an
        empty transcript is reported with a success exit. Refuse the pair
        rather than emit a silently empty transcript (video-asr-chunking)."""
        for overlap in ("15", "20"):
            with self.subTest(overlap=overlap):
                calls = []
                err = io.StringIO()
                with stub_parakeet(calls), contextlib.redirect_stderr(err):
                    with self.assertRaises(SystemExit) as ctx:
                        asr_parakeet.main(
                            ["--audio", "/tmp/a.wav", "--chunk-duration", "15",
                             "--overlap-duration", overlap])
                self.assertEqual(ctx.exception.code, 2)
                self.assertEqual(calls, [])
                self.assertIn("must be less than", err.getvalue())

    def test_overlap_past_a_disabled_window_is_allowed(self):
        """`--chunk-duration 0` disables chunking outright, so the overlap is
        never consulted and must not be validated against it."""
        rc, _stdout, calls = run_main(
            ["--audio", "/tmp/a.wav", "--chunk-duration", "0",
             "--overlap-duration", "15"])
        self.assertEqual(rc, 0)
        self.assertIsNone(calls[0]["kwargs"]["chunk_duration"])

    def test_still_emits_the_backend_word_contract(self):
        rc, stdout, _calls = run_main(["--audio", "/tmp/a.wav"])
        self.assertEqual(rc, 0)
        payload = json.loads(stdout)
        self.assertEqual(payload["model"], asr_parakeet.MODEL_ID)
        self.assertEqual(payload["words"],
                         [{"start": 0.0, "end": 0.5, "text": "hello"}])

    def test_warm_cache_transcribes_nothing(self):
        rc, stdout, calls = run_main(["--warm-cache"])
        self.assertEqual(rc, 0)
        self.assertEqual(calls, [])
        self.assertEqual(stdout, "")


if __name__ == "__main__":
    unittest.main()
