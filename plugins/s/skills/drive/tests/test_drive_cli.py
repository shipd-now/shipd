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
import involved.

`--fix` additionally installs a missing `ffmpeg`, `ffprobe`, or `vhs`
through the platform package manager (doctor-autofix's widened
drive-doctor). That install is exercised through the same PATH-stubbing
seam rather than the real package manager: a fake `brew` executable is
dropped into the restricted PATH bindir (`_brew_stub`), so `default_run`'s
real `subprocess.run(["brew", "install", ...])` call lands on the stub
instead of a real installer — the stub can report success (optionally
materializing the now-installed tool on PATH so the re-report sees it) or
failure on command."""

import os
import stat
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


def _brew_stub(bindir, exit_code=0, installs=None):
    """Write a fake `brew` into `bindir`: `brew install <package>` exits
    `exit_code` regardless of which package is named. When `exit_code` is
    0, `installs` (a `{package: [tool, ...]}` map) additionally drops an
    executable stub for each named tool into `bindir` when that package is
    the one requested — so installing the `ffmpeg` package can be made to
    provide both the `ffmpeg` and `ffprobe` tool files, mirroring how the
    real Homebrew formula does, purely through PATH and with no real
    package manager ever invoked.

    The target directory is baked into the script as a literal absolute
    path rather than derived from `$0`: `drive.py` invokes `run(["brew",
    ...])` with a bare command name, so the OS resolves it via `PATH` but
    leaves `argv[0]` as the literal string "brew" — `dirname "$0"` would
    resolve to the process's cwd, not `bindir`. `touch`/`chmod` are
    likewise addressed by absolute path (with a Linux/macOS fallback):
    `run_cli`'s env restricts `PATH` to `bindir` alone, the whole point of
    the harness, so a bare `touch`/`chmod` inside this stub would not
    resolve either."""
    installs = installs or {}
    path = os.path.join(bindir, "brew")
    body = "#!/bin/sh\npkg=\"$2\"\ndir=\"%s\"\n" % bindir
    if installs and exit_code == 0:
        body += (
            "TOUCH=/usr/bin/touch; [ -x \"$TOUCH\" ] || TOUCH=/bin/touch\n"
            "CHMOD=/bin/chmod; [ -x \"$CHMOD\" ] || CHMOD=/usr/bin/chmod\n")
        for package, tools in installs.items():
            body += "if [ \"$pkg\" = \"%s\" ]; then\n" % package
            for tool in tools:
                body += "  \"$TOUCH\" \"$dir/%s\"\n" % tool
                body += "  \"$CHMOD\" +x \"$dir/%s\"\n" % tool
            body += "fi\n"
    body += "exit %d\n" % exit_code
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(body)
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return path


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
            self.tmp, "everything", ["uv", "ffmpeg", "ffprobe", "vhs"])
        r = self.run_cli(bindir, self.browsers_dir(True), "doctor")
        self.assertEqual(r.returncode, 0, r.stderr)


class DoctorVhsToolTest(DriveCliTestBase):
    """`vhs` (drive-doctor) joins `ffmpeg`/`ffprobe` as a third,
    terminal-recording-only tier: missing solely because a terminal
    recording is not being requested right now never fails `doctor`, and it
    always names `brew install vhs` as its remedy."""

    def test_missing_vhs_reports_remedy_and_exits_zero(self):
        bindir = _bindir(
            self.tmp, "uv-and-browser-no-vhs", ["uv", "ffmpeg", "ffprobe"])
        r = self.run_cli(bindir, self.browsers_dir(True), "doctor")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = (r.stdout + r.stderr).lower()
        self.assertIn("vhs", out)
        self.assertIn("missing", out)
        self.assertRegex(out, r"vhs.*brew install vhs")

    def test_missing_vhs_with_uv_and_browser_present_exits_zero(self):
        bindir = _bindir(
            self.tmp, "uv-browser-only", ["uv", "ffmpeg", "ffprobe"])
        r = self.run_cli(bindir, self.browsers_dir(True), "doctor")
        self.assertEqual(r.returncode, 0, r.stderr)


class DoctorVhsInstallTest(DriveCliTestBase):
    """`--fix` installs a missing `vhs` through the platform package
    manager (doctor-autofix's widened drive-doctor scope): a successful
    install makes the tool present on the re-report, and a failing one
    reports terminal recording as the affected surface, names
    `brew install vhs` as the manual remedy, and still reports every other
    tool. Both are driven through the injectable runner seam
    (`default_run`'s real `subprocess.run` landing on a PATH-stubbed
    `brew`, via `_brew_stub`) — never the real package manager."""

    def test_fix_installs_vhs_when_absent(self):
        bindir = _bindir(
            self.tmp, "fix-installs-vhs", ["uv", "ffmpeg", "ffprobe"])
        _brew_stub(bindir, exit_code=0, installs={"vhs": ["vhs"]})
        r = self.run_cli(
            bindir, self.browsers_dir(True), "doctor", "--fix")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = (r.stdout + r.stderr).lower()
        self.assertIn("+ vhs", out)

    def test_failed_vhs_install_names_terminal_recording_and_keeps_rest(self):
        bindir = _bindir(
            self.tmp, "fix-vhs-install-fails", ["uv", "ffmpeg", "ffprobe"])
        _brew_stub(bindir, exit_code=1)
        r = self.run_cli(
            bindir, self.browsers_dir(True), "doctor", "--fix")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = (r.stdout + r.stderr).lower()
        self.assertIn("installing vhs", out)
        self.assertIn("terminal recording", out)
        self.assertIn("brew install vhs", out)
        self.assertIn("uv", out)
        self.assertIn("ffmpeg", out)
        self.assertIn("ffprobe", out)
        self.assertIn("playwright browser", out)


class DoctorFixNetworkStatementTest(DriveCliTestBase):
    """`--fix`'s upfront network-access statement must match what it then
    does (drive-doctor's "state the network access it performs before
    performing it", doctor-autofix): claiming "no network access" and then
    brew-installing a missing optional tool on the very next line would
    contradict itself."""

    def test_missing_optional_tool_is_named_before_its_install_runs(self):
        bindir = _bindir(
            self.tmp, "browser-present-vhs-missing",
            ["uv", "ffmpeg", "ffprobe"])
        _brew_stub(bindir, exit_code=0, installs={"vhs": ["vhs"]})
        r = self.run_cli(
            bindir, self.browsers_dir(True), "doctor", "--fix")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = (r.stdout + r.stderr).lower()
        self.assertNotIn("performs no network access", out)
        # `vhs` is named in the upfront statement, before the
        # "installing vhs…" line that runs the actual install.
        pre_install = out.split("installing vhs", 1)[0]
        self.assertIn("vhs", pre_install)

    def test_everything_present_prints_no_network_access_and_installs_nothing(self):
        # No `brew` stub at all: if the optional-tool loop shelled out to
        # brew despite nothing being missing, it would fail to find the
        # command and report it — this asserts that never happens.
        bindir = _bindir(
            self.tmp, "everything-present",
            ["uv", "ffmpeg", "ffprobe", "vhs"])
        r = self.run_cli(bindir, self.browsers_dir(True), "doctor", "--fix")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = (r.stdout + r.stderr).lower()
        self.assertIn("performs no network access", out)
        self.assertNotIn("installing", out)
        self.assertNotIn("failed", out)


class DoctorFfmpegFfprobeInstallTest(DriveCliTestBase):
    """`--fix` installs a missing `ffmpeg`/`ffprobe` through the platform
    package manager too (doctor-autofix's widened drive-doctor scope): a
    successful install makes each tool present on the re-report, and a
    failed one names recording and post-processing as the affected surface
    for both, and still reports every other tool. Driven through the same
    PATH-stubbed `brew` seam as `DoctorVhsInstallTest`."""

    def test_fix_installs_ffmpeg_and_ffprobe_when_absent(self):
        bindir = _bindir(self.tmp, "fix-installs-ffmpeg", ["uv", "vhs"])
        _brew_stub(bindir, exit_code=0, installs={"ffmpeg": ["ffmpeg", "ffprobe"]})
        r = self.run_cli(
            bindir, self.browsers_dir(True), "doctor", "--fix")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = (r.stdout + r.stderr).lower()
        self.assertIn("+ ffmpeg", out)
        self.assertIn("+ ffprobe", out)

    def test_failed_ffmpeg_ffprobe_install_names_recording_surface(self):
        bindir = _bindir(self.tmp, "fix-ffmpeg-install-fails", ["uv", "vhs"])
        _brew_stub(bindir, exit_code=1)
        r = self.run_cli(
            bindir, self.browsers_dir(True), "doctor", "--fix")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = (r.stdout + r.stderr).lower()
        self.assertIn("installing ffmpeg", out)
        self.assertIn("installing ffprobe", out)
        self.assertIn("recording and post-processing", out)
        self.assertIn("uv", out)
        self.assertIn("playwright browser", out)
        self.assertIn("vhs", out)


if __name__ == "__main__":
    unittest.main()
