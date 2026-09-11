#!/usr/bin/env python3
"""Unit tests for `drive.py`'s verb table and `doctor` preflight
(drive-doctor): an unknown or missing verb prints usage on stderr and exits
2; `uv` and a Playwright browser binary are required for every verb, so
`doctor` exits non-zero and names a remedy when either is absent; `ffmpeg`
and `ffprobe` are required only for recording and post-processing, so
`doctor` exits 0 and marks them recording-only when they are absent but `uv`
and the browser are present.

`drive.py` is stdlib-only (no `playwright` import at module scope, per the
drive-skill plan's CLI split), so this suite runs with no Playwright
installed at all — CI installs only `textual`. Tool presence on PATH is
controlled via a restricted `PATH` directory holding executable stubs
(`_stubs.stub_bindir`, copied in shape from
`plugins/s/skills/video-ingest/tests/_stubs.py`). The Playwright browser
binary is never actually installed here either: `doctor` locates it by
checking for a `chromium*` entry under the browsers directory Playwright
itself resolves from the `PLAYWRIGHT_BROWSERS_PATH` environment variable (a
real Playwright override, not a drive-only invention), so tests fake
"browser present" by pointing that variable at a temp directory holding a
bare `chromium-<rev>` marker directory — no Playwright package, download, or
import involved."""

import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
SCRIPT = os.path.join(SCRIPTS, "drive.py")
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from _stubs import stub_bindir as _bindir  # noqa: E402


class DriveCliTestBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="drive-cli-")
        self.home = tempfile.mkdtemp(prefix="drive-cli-home-")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)
        shutil.rmtree(self.home, ignore_errors=True)

    def browsers_dir(self, with_browser):
        """A directory usable as `PLAYWRIGHT_BROWSERS_PATH`, holding a bare
        `chromium-<rev>` marker directory when `with_browser` is true, and
        nothing when it is false — simulating "browser installed" purely by
        filesystem presence, with no Playwright package involved."""
        d = os.path.join(self.tmp, "browsers")
        os.makedirs(d, exist_ok=True)
        if with_browser:
            os.makedirs(os.path.join(d, "chromium-1105"), exist_ok=True)
        return d

    def run_cli(self, path_dir, browsers_dir, *args):
        env = {
            "PATH": path_dir,
            "HOME": self.home,
            "PLAYWRIGHT_BROWSERS_PATH": browsers_dir,
        }
        return subprocess.run(
            [sys.executable, SCRIPT, *args],
            capture_output=True, text=True, env=env)


class UnknownVerbTest(DriveCliTestBase):
    def test_unknown_verb_is_a_usage_error(self):
        bindir = _bindir(self.tmp, "empty", [])
        r = self.run_cli(bindir, self.browsers_dir(False), "frobnicate")
        self.assertEqual(r.returncode, 2)
        self.assertIn("usage", r.stderr.lower())
        self.assertEqual(r.stdout, "")

    def test_missing_verb_is_a_usage_error(self):
        bindir = _bindir(self.tmp, "empty", [])
        r = self.run_cli(bindir, self.browsers_dir(False))
        self.assertEqual(r.returncode, 2)
        self.assertIn("usage", r.stderr.lower())


class DoctorMissingToolTest(DriveCliTestBase):
    def test_missing_uv_exits_nonzero_with_remedy(self):
        bindir = _bindir(self.tmp, "no-uv", ["ffmpeg", "ffprobe"])
        r = self.run_cli(bindir, self.browsers_dir(True), "doctor")
        self.assertNotEqual(r.returncode, 0)
        out = (r.stdout + r.stderr).lower()
        self.assertIn("uv", out)
        self.assertIn("missing", out)
        self.assertRegex(out, r"uv.*(install|brew)")

    def test_missing_browser_exits_nonzero_with_remedy(self):
        bindir = _bindir(self.tmp, "uv-only", ["uv", "ffmpeg", "ffprobe"])
        r = self.run_cli(bindir, self.browsers_dir(False), "doctor")
        self.assertNotEqual(r.returncode, 0)
        out = (r.stdout + r.stderr).lower()
        self.assertIn("browser", out)
        self.assertIn("missing", out)


class DoctorRecordingOnlyToolsTest(DriveCliTestBase):
    def test_missing_ffmpeg_is_recording_only_and_exits_zero(self):
        bindir = _bindir(self.tmp, "uv-and-browser", ["uv"])
        r = self.run_cli(bindir, self.browsers_dir(True), "doctor")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = (r.stdout + r.stderr).lower()
        self.assertIn("ffmpeg", out)
        self.assertIn("recording", out)

    def test_everything_present_exits_zero(self):
        bindir = _bindir(
            self.tmp, "everything", ["uv", "ffmpeg", "ffprobe"])
        r = self.run_cli(bindir, self.browsers_dir(True), "doctor")
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
