#!/usr/bin/env python3
"""Unit tests for `semdiff doctor` — dependency reporting exit codes and the
installer's pure helpers. No `--fix` is ever passed, so no test touches the
network."""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
SCRIPT = os.path.join(SCRIPTS, "semdiff.py")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import semdiff  # noqa: E402


def _bindir(base, name, tools):
    d = os.path.join(base, name)
    os.makedirs(d, exist_ok=True)
    for tool in tools:
        src = shutil.which(tool)
        if src:
            link = os.path.join(d, tool)
            if not os.path.exists(link):
                os.symlink(src, link)
    return d


def run_doctor(path_dir, home):
    env = {"PATH": path_dir, "HOME": home}
    return subprocess.run([sys.executable, SCRIPT, "doctor"],
                          capture_output=True, text=True, env=env)


class DoctorExitCodeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="semdiff-doctor-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_git_present_difft_missing_exits_zero(self):
        # git available, difft absent (only git symlinked into the bindir).
        bindir = _bindir(self.tmp, "gitonly", ["git"])
        r = run_doctor(bindir, self.tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        out = (r.stdout + r.stderr).lower()
        self.assertIn("difft", out)
        self.assertIn("recommend", out)

    def test_git_missing_exits_nonzero(self):
        # empty bindir: git cannot be found → required tool missing.
        bindir = _bindir(self.tmp, "empty", [])
        r = run_doctor(bindir, self.tmp)
        self.assertNotEqual(r.returncode, 0)


class DifftTargetTest(unittest.TestCase):
    def _target(self, system, machine):
        with mock.patch.object(semdiff.platform, "system",
                               return_value=system), \
             mock.patch.object(semdiff.platform, "machine",
                               return_value=machine):
            return semdiff._difft_target()

    def test_darwin_arm64(self):
        self.assertEqual(self._target("Darwin", "arm64"), "aarch64-apple-darwin")

    def test_darwin_x86_64(self):
        self.assertEqual(self._target("Darwin", "x86_64"), "x86_64-apple-darwin")

    def test_linux_aarch64(self):
        self.assertEqual(self._target("Linux", "aarch64"),
                         "aarch64-unknown-linux-gnu")

    def test_linux_x86_64(self):
        self.assertEqual(self._target("Linux", "x86_64"),
                         "x86_64-unknown-linux-gnu")

    def test_unsupported_os_is_none(self):
        self.assertIsNone(self._target("Windows", "x86_64"))

    def test_unsupported_arch_is_none(self):
        self.assertIsNone(self._target("Linux", "sparc64"))


class InstallDirTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="semdiff-installdir-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_prefers_plugin_root_bin(self):
        root = os.path.join(self.tmp, "plugin")
        with mock.patch.dict(os.environ, {"CLAUDE_PLUGIN_ROOT": root}):
            self.assertEqual(semdiff._install_dir(),
                             os.path.join(root, "bin"))

    def test_falls_back_to_local_bin(self):
        env = dict(os.environ)
        env.pop("CLAUDE_PLUGIN_ROOT", None)
        env["HOME"] = self.tmp
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(
                semdiff._install_dir(),
                os.path.join(self.tmp, ".local", "bin"))


if __name__ == "__main__":
    unittest.main()
