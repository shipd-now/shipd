#!/usr/bin/env python3
"""Unit tests for `video_ingest.py doctor` — the tiered dependency preflight
modelled on `semdiff.py doctor` (video-doctor-preflight): `ffmpeg` and `uv`
are required (missing → non-zero exit, concrete hint printed); the backend
model caches are recommended (missing → reported with a download size, exit
zero). `ingest` gates on the required tier and refuses before writing
anything when a required tool is missing.

Tool presence is controlled via a restricted ``PATH`` directory holding
executable stubs for the tools under test (`_stubs.stub_bindir` —
video-pipeline-testability), and model-cache state is controlled via an
isolated ``$HOME`` (mirroring `test_video_bundle.py`) — so these tests are
deterministic regardless of what is actually installed on the machine running
them. A CLI test may pass ``--fix``, but the network boundary still holds: the
restricted ``PATH`` bindir's `uv` stub is inert (`#!/bin/sh exit 0`), so a
`--fix` run's warm invocation executes the stub rather than real `uv`. The
`--fix` install/pre-warm helpers (``install_required_tool``,
``warm_backend_cache``) are additionally exercised directly, in-process,
against a fake injectable runner (mirroring
`review/tests/test_review_gate.py`'s `FakeGh`), so the network boundary is
never crossed there either."""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
SCRIPT = os.path.join(SCRIPTS, "video_ingest.py")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import video_ingest as vi  # noqa: E402
from _stubs import stub_bindir as _bindir  # noqa: E402


class DoctorTestBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="video-doctor-")
        self.home = tempfile.mkdtemp(prefix="video-doctor-home-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        shutil.rmtree(self.home, ignore_errors=True)

    def run_cli(self, path_dir, *args):
        env = {"PATH": path_dir, "HOME": self.home}
        return subprocess.run(
            [sys.executable, SCRIPT, *args],
            capture_output=True, text=True, env=env)


class DoctorMissingToolTest(DoctorTestBase):
    def test_missing_ffmpeg_exits_nonzero_with_hint(self):
        bindir = _bindir(self.tmp, "uvonly", ["uv"])
        r = self.run_cli(bindir, "doctor")
        self.assertNotEqual(r.returncode, 0)
        out = (r.stdout + r.stderr).lower()
        self.assertIn("ffmpeg", out)
        self.assertIn("missing", out)
        self.assertRegex(out, r"ffmpeg.*(install|brew)")

    def test_missing_uv_exits_nonzero_with_hint(self):
        bindir = _bindir(self.tmp, "ffmpegonly", ["ffmpeg"])
        r = self.run_cli(bindir, "doctor")
        self.assertNotEqual(r.returncode, 0)
        out = (r.stdout + r.stderr).lower()
        self.assertIn("uv", out)
        self.assertIn("missing", out)

    def test_both_present_and_cache_warm_exits_zero(self):
        bindir = _bindir(self.tmp, "both", ["ffmpeg", "uv"])
        # Pre-populate every model cache location doctor checks so this is
        # the "everything present" control case.
        for rel in (
            os.path.join(".cache", "huggingface", "hub",
                        "models--mlx-community--parakeet-tdt-0.6b-v2"),
            os.path.join(".cache", "huggingface", "hub",
                        "models--mlx-community--whisper-large-v3-turbo"),
        ):
            os.makedirs(os.path.join(self.home, rel), exist_ok=True)
        r = self.run_cli(bindir, "doctor")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = (r.stdout + r.stderr).lower()
        self.assertNotIn("recommend", out)


class DoctorColdCacheTest(DoctorTestBase):
    def test_cold_model_cache_recommended_exits_zero(self):
        bindir = _bindir(self.tmp, "both", ["ffmpeg", "uv"])
        # self.home is a fresh temp dir: no model cache present anywhere.
        r = self.run_cli(bindir, "doctor")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = (r.stdout + r.stderr).lower()
        self.assertIn("recommend", out)
        # a concrete download size is named for at least one cold cache
        self.assertRegex(out, r"~?\d+(\.\d+)?\s*(mb|gb)")

    def test_cold_cache_names_no_diarization_model_or_token(self):
        bindir = _bindir(self.tmp, "both", ["ffmpeg", "uv"])
        # self.home is a fresh temp dir: no model cache present anywhere,
        # and run_cli's env carries no HF_TOKEN.
        r = self.run_cli(bindir, "doctor")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = (r.stdout + r.stderr).lower()
        self.assertNotIn("diariz", out)
        self.assertNotIn("token", out)
        self.assertNotIn("gated", out)
        self.assertNotIn("pyannote", out)
        self.assertNotIn("sherpa", out)


class IngestPreflightTest(DoctorTestBase):
    def test_ingest_refuses_missing_required_tool(self):
        bindir = _bindir(self.tmp, "empty", [])
        video = os.path.join(self.tmp, "recording.mov")
        open(video, "w", encoding="utf-8").close()
        env = {"PATH": bindir, "HOME": self.home}
        r = subprocess.run(
            [sys.executable, SCRIPT, "--project-dir", self.tmp,
             "ingest", video],
            capture_output=True, text=True, env=env)
        self.assertNotEqual(r.returncode, 0)
        out = (r.stdout + r.stderr).lower()
        self.assertIn("missing", out)
        bundle = os.path.join(self.home, ".shipd", "video")
        self.assertFalse(os.path.isdir(bundle))


def fake_run(rc, stdout="", stderr=""):
    calls = []

    def run(args, input=None):
        calls.append((list(args), input))
        return rc, stdout, stderr

    run.calls = calls
    return run


class FixHelpersTest(unittest.TestCase):
    """Direct (in-process) tests of the `--fix` install/pre-warm helpers,
    driven against a fake injectable runner — no real `brew` or `uv` process
    is ever spawned, so these never touch the network."""

    def test_install_required_tool_invokes_brew(self):
        run = fake_run(0)
        ok = vi.install_required_tool("ffmpeg", run)
        self.assertTrue(ok)
        self.assertEqual(run.calls, [(["brew", "install", "ffmpeg"], None)])

    def test_install_required_tool_reports_failure(self):
        run = fake_run(1, stderr="no formula")
        ok = vi.install_required_tool("ffmpeg", run)
        self.assertFalse(ok)

    def test_warm_backend_cache_invokes_uv_run_with_warm_flag(self):
        run = fake_run(0)
        vi.warm_backend_cache("/path/to/asr_parakeet.py", run)
        self.assertEqual(
            run.calls,
            [(["uv", "run", "/path/to/asr_parakeet.py", "--warm-cache"],
              None)])

    def test_warm_backend_cache_raises_on_failure(self):
        run = fake_run(1, stderr="download failed")
        with self.assertRaises(vi.VideoIngestError):
            vi.warm_backend_cache("/path/to/asr_parakeet.py", run)


if __name__ == "__main__":
    unittest.main()
