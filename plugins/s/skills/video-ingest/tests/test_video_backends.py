#!/usr/bin/env python3
"""Unit tests for video_ingest.py's ASR backend selection and invocation
(video-backend-adapters).

Transcription runs as a separate `uv run` script through the injectable
runner. Backend selection defaults to parakeet, overridable via `--asr` or
the resolved configuration's `build.video_asr` key — a flag always wins over
the configured value. A non-zero backend exit or unparseable stdout fails the
ingest with the backend's stderr attached and leaves no partial bundle
directory behind. `--diarizer` and `--speakers` are not recognized options —
passing either fails argument parsing outright.

The success-path tests below assert the invoked backend script and the
written `manifest.json` fields; full transcript assembly (video-transcript-
schema) is covered separately in test_video_bundle.py.

`cmd_ingest` gates on `required_tools_missing()`, which consults the ambient
`PATH` (video-doctor-preflight) — so the tests that drive `cmd_ingest` for
real (`IngestBackendIntegrationTest`) also pin `PATH` to a stub bindir built
by `_stubs.stub_bindir` (video-pipeline-testability), never relying on
`ffmpeg`/`uv` actually being installed on the host running the suite."""

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import video_ingest as vi  # noqa: E402
from _stubs import stub_bindir  # noqa: E402


@contextlib.contextmanager
def home_set_to(path):
    """Override ``$HOME`` for the duration of the block, mirroring
    build/tests/test_spec_common.py's convention — the real home is never
    read or written by these tests."""
    old = os.environ.get("HOME")
    os.environ["HOME"] = path
    try:
        yield
    finally:
        if old is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = old


@contextlib.contextmanager
def path_set_to(path_dir):
    """Override ``$PATH`` for the duration of the block, so
    `required_tools_missing()`'s `shutil.which` lookups see only the stub
    bindir under test — never the ambient host `PATH`."""
    old = os.environ.get("PATH")
    os.environ["PATH"] = path_dir
    try:
        yield
    finally:
        if old is None:
            os.environ.pop("PATH", None)
        else:
            os.environ["PATH"] = old


def make_fake_run(*, asr_result=None, asr_rc=0, asr_stderr="",
                  ffprobe_rc=0, ffprobe_stdout=None, ffmpeg_rc=0):
    """A dispatcher fake matching the injectable runner's signature, routing
    `ffprobe`/`ffmpeg`/`uv run <asr backend script>` calls to canned
    results."""
    calls = []
    if ffprobe_stdout is None:
        ffprobe_stdout = json.dumps({
            "format": {"duration": "5.0"},
            "streams": [{"codec_type": "audio"}],
        })
    if asr_result is None:
        asr_result = {"words": [{"start": 0.0, "end": 1.0, "text": "hi"}],
                     "model": "fake-asr-model"}

    def run(args, input=None):
        calls.append(list(args))
        cmd = args[0]
        if cmd == "ffprobe":
            return ffprobe_rc, ffprobe_stdout, ""
        if cmd == "ffmpeg":
            return ffmpeg_rc, "", ""
        if cmd == "uv":
            script = args[2]
            if "asr_" in os.path.basename(script):
                if asr_rc != 0:
                    return asr_rc, "", asr_stderr
                return 0, json.dumps(asr_result), ""
        raise AssertionError("unexpected call: %r" % (args,))

    run.calls = calls
    return run


class BackendSelectionTest(unittest.TestCase):
    """`resolve_backends` — pure resolution over CLI flags and config."""

    def test_defaults_to_parakeet(self):
        args = SimpleNamespace(asr=None)
        config = {"asr": vi.DEFAULT_ASR}
        self.assertEqual(vi.resolve_backends(args, config), "parakeet")

    def test_flag_overrides_configured_backend(self):
        args = SimpleNamespace(asr="whisper")
        config = {"asr": "parakeet"}
        self.assertEqual(vi.resolve_backends(args, config), "whisper")

    def test_config_selects_when_no_flag(self):
        args = SimpleNamespace(asr=None)
        config = {"asr": "whisper"}
        self.assertEqual(vi.resolve_backends(args, config), "whisper")


class VideoConfigBackendKeysTest(unittest.TestCase):
    """`video_config` picks up `build.video_asr`, mirroring its
    `build.video_dir` resolution."""

    def setUp(self):
        self.proj = tempfile.mkdtemp(prefix="video-backend-proj-")

    def tearDown(self):
        shutil.rmtree(self.proj, ignore_errors=True)

    def write_config(self, data):
        with open(os.path.join(self.proj, ".shipd-config.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(data, fh)

    def test_defaults_when_unconfigured(self):
        config = vi.video_config(self.proj)
        self.assertEqual(config["asr"], vi.DEFAULT_ASR)

    def test_video_asr_key_overrides(self):
        self.write_config({"build": {"video_asr": "whisper"}})
        config = vi.video_config(self.proj)
        self.assertEqual(config["asr"], "whisper")


class BackendArgvVocabularyTest(unittest.TestCase):
    """`backend_argv` — appends `--vocab <comma-joined terms>` only when a
    non-empty vocabulary is given (video-vocabulary-biasing,
    video-backend-adapters)."""

    def test_configured_vocabulary_appends_vocab_flag(self):
        argv = vi.backend_argv("/scripts/asr_whisper.py", "/tmp/a.wav",
                               vocabulary=["shipd", "am"])
        self.assertEqual(argv, ["uv", "run", "/scripts/asr_whisper.py",
                                "--audio", "/tmp/a.wav",
                                "--vocab", "shipd,am"])

    def test_absent_vocabulary_carries_no_vocab_flag(self):
        argv = vi.backend_argv("/scripts/asr_whisper.py", "/tmp/a.wav")
        self.assertNotIn("--vocab", argv)

    def test_empty_vocabulary_carries_no_vocab_flag(self):
        argv = vi.backend_argv("/scripts/asr_whisper.py", "/tmp/a.wav",
                               vocabulary=[])
        self.assertNotIn("--vocab", argv)


class BackendInvocationTest(unittest.TestCase):
    """`run_backend` — argv construction, JSON parsing, and failure
    reporting for a single backend call."""

    def test_parses_json_object_on_success(self):
        calls = []

        def run(args, input=None):
            calls.append(list(args))
            return 0, json.dumps({"words": [], "model": "m"}), ""

        result = vi.run_backend("/scripts/asr_parakeet.py", "/tmp/a.wav", run)
        self.assertEqual(result, {"words": [], "model": "m"})
        self.assertEqual(calls, [["uv", "run", "/scripts/asr_parakeet.py",
                                  "--audio", "/tmp/a.wav"]])

    def test_nonzero_exit_raises_with_stderr(self):
        def run(args, input=None):
            return 1, "", "model download failed"

        with self.assertRaises(vi.VideoIngestError) as ctx:
            vi.run_backend("/scripts/asr_parakeet.py", "/tmp/a.wav", run)
        self.assertIn("model download failed", str(ctx.exception))

    def test_signal_kill_is_reported_not_masked_by_a_warning(self):
        """An OOM-killed backend writes no diagnostic, so its stderr holds
        only incidental dependency noise. Reporting that noise alone names a
        warning as the cause and hides the kill (video-asr-chunking)."""
        def run(args, input=None):
            return -9, "", "Warning: unauthenticated requests to the HF Hub"

        with self.assertRaises(vi.VideoIngestError) as ctx:
            vi.run_backend("/scripts/asr_parakeet.py", "/tmp/a.wav", run)
        self.assertIn("killed by signal 9", str(ctx.exception))

    def test_exit_status_carried_when_stderr_is_empty(self):
        def run(args, input=None):
            return 137, "", ""

        with self.assertRaises(vi.VideoIngestError) as ctx:
            vi.run_backend("/scripts/asr_parakeet.py", "/tmp/a.wav", run)
        self.assertIn("exit 137", str(ctx.exception))

    def test_unparseable_stdout_raises(self):
        def run(args, input=None):
            return 0, "not json", ""

        with self.assertRaises(vi.VideoIngestError):
            vi.run_backend("/scripts/asr_parakeet.py", "/tmp/a.wav", run)


class IngestBackendIntegrationTest(unittest.TestCase):
    """Full `cmd_ingest` through backend invocation + manifest write (the
    pipeline is not complete until section 5 adds transcript assembly)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="video-ingest-backends-")
        self.home = os.path.join(self.tmp, "home")
        self.proj = os.path.join(self.tmp, "proj")
        os.makedirs(self.home)
        os.makedirs(self.proj)
        self.video = os.path.join(self.tmp, "recording.mov")
        with open(self.video, "wb") as fh:
            fh.write(b"fake video bytes")
        self.bindir = stub_bindir(self.tmp, "bin", ["ffmpeg", "uv"])

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def bundle_path(self, slug="recording"):
        return os.path.join(self.home, ".shipd", "video", slug)

    def test_default_backend_invoked_and_recorded_in_manifest(self):
        run = make_fake_run()
        args = SimpleNamespace(video=self.video, slug=None, force=False,
                               asr=None)
        with home_set_to(self.home), path_set_to(self.bindir):
            rc = vi.cmd_ingest(args, self.proj, run=run)
        self.assertEqual(rc, 0)
        scripts_invoked = [c[2] for c in run.calls if c[0] == "uv"]
        self.assertTrue(any("asr_parakeet" in s for s in scripts_invoked))
        with open(os.path.join(self.bundle_path(), "manifest.json"),
                 encoding="utf-8") as fh:
            manifest = json.load(fh)
        self.assertEqual(manifest["asr_backend"], "parakeet")
        self.assertEqual(manifest["asr_model"], "fake-asr-model")
        # transcript.json and frames/ are real I/O this test does not fake —
        # the ffmpeg call is faked, so audio.wav itself is not asserted here.
        self.assertTrue(os.path.isfile(
            os.path.join(self.bundle_path(), "transcript.json")))
        self.assertTrue(os.path.isdir(
            os.path.join(self.bundle_path(), "frames")))

    def test_flag_overrides_configured_backend(self):
        with open(os.path.join(self.proj, ".shipd-config.json"), "w",
                 encoding="utf-8") as fh:
            json.dump({"build": {"video_asr": "parakeet"}}, fh)
        run = make_fake_run()
        args = SimpleNamespace(video=self.video, slug=None, force=False,
                               asr="whisper")
        with home_set_to(self.home), path_set_to(self.bindir):
            rc = vi.cmd_ingest(args, self.proj, run=run)
        self.assertEqual(rc, 0)
        scripts_invoked = [c[2] for c in run.calls if c[0] == "uv"]
        self.assertTrue(any("asr_whisper" in s for s in scripts_invoked))
        self.assertFalse(any("asr_parakeet" in s for s in scripts_invoked))

    def test_backend_failure_leaves_no_partial_bundle(self):
        run = make_fake_run(asr_rc=1, asr_stderr="boom: no gpu")
        args = SimpleNamespace(video=self.video, slug=None, force=False,
                               asr=None)
        with home_set_to(self.home), path_set_to(self.bindir):
            with self.assertRaises(vi.VideoIngestError) as ctx:
                vi.cmd_ingest(args, self.proj, run=run)
        self.assertIn("boom: no gpu", str(ctx.exception))
        self.assertFalse(os.path.exists(self.bundle_path()))


class DiarizerOptionsRejectedTest(unittest.TestCase):
    """`--diarizer` and `--speakers` are not defined on the `ingest` parser
    — passing either fails argument parsing outright rather than being
    silently accepted (video-backend-adapters)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="video-ingest-diarizer-rejected-")
        self.home = os.path.join(self.tmp, "home")
        self.proj = os.path.join(self.tmp, "proj")
        os.makedirs(self.home)
        os.makedirs(self.proj)
        self.video = os.path.join(self.tmp, "recording.mov")
        with open(self.video, "wb") as fh:
            fh.write(b"fake video bytes")
        self.bindir = stub_bindir(self.tmp, "bin", ["ffmpeg", "uv"])

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def bundle_path(self, slug="recording"):
        return os.path.join(self.home, ".shipd", "video", slug)

    def test_diarizer_flag_is_rejected(self):
        run = make_fake_run()
        err = io.StringIO()
        with home_set_to(self.home), path_set_to(self.bindir), \
             contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit) as ctx:
                vi.main(["--project-dir", self.proj, "ingest", self.video,
                        "--diarizer", "sherpa"], run=run)
        self.assertEqual(ctx.exception.code, 2)
        self.assertIn("unrecognized arguments", err.getvalue())
        self.assertEqual(run.calls, [])
        self.assertFalse(os.path.exists(self.bundle_path()))

    def test_speakers_flag_is_rejected(self):
        run = make_fake_run()
        err = io.StringIO()
        with home_set_to(self.home), path_set_to(self.bindir), \
             contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit) as ctx:
                vi.main(["--project-dir", self.proj, "ingest", self.video,
                        "--speakers", "2"], run=run)
        self.assertEqual(ctx.exception.code, 2)
        self.assertIn("unrecognized arguments", err.getvalue())
        self.assertEqual(run.calls, [])
        self.assertFalse(os.path.exists(self.bundle_path()))


if __name__ == "__main__":
    unittest.main()
