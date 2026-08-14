#!/usr/bin/env python3
"""Unit tests for design.py — the global design scratch area (stdlib only, no
network) backing the design-fidelity handoff (design-handoff
design-scratch-area, design-scratch-cleanup).

``design.py path <change>`` resolves and creates ``<designs-root>/<change>``
(default ``~/.shipd/designs``, overridable via the resolved configuration's
``build.design_dir`` key, home-expanded — mirroring
``build_report.py::build_log_dir``). ``design.py clean <change>`` removes it,
fail-soft: a missing or unremovable directory warns on stderr and still exits
0, mirroring heartbeat.py.

The script is driven as a black box via subprocess against isolated ``$HOME``
and project-dir temp directories — the real home is never read or written."""

import os
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.normpath(os.path.join(HERE, "..", "scripts", "design.py"))
CHANGE = "demo-change"


class DesignScriptTestBase(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="design-home-")
        self.proj = tempfile.mkdtemp(prefix="design-proj-")

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)
        shutil.rmtree(self.proj, ignore_errors=True)

    def cli(self, *args):
        env = dict(os.environ)
        env["HOME"] = self.home
        return subprocess.run(
            ["python3", SCRIPT, "--project-dir", self.proj, *args],
            capture_output=True, text=True, env=env)

    def default_root(self):
        return os.path.join(self.home, ".shipd", "designs")

    def write_project_config(self, data):
        import json
        with open(os.path.join(self.proj, ".shipd-config.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(data, fh)


class PathVerbTest(DesignScriptTestBase):
    def test_prints_and_creates_default_dir(self):
        r = self.cli("path", CHANGE)
        self.assertEqual(r.returncode, 0, r.stderr)
        expected = os.path.join(self.default_root(), CHANGE)
        self.assertEqual(r.stdout.strip(), expected)
        self.assertTrue(os.path.isdir(expected))

    def test_idempotent_when_dir_already_exists(self):
        self.assertEqual(self.cli("path", CHANGE).returncode, 0)
        r = self.cli("path", CHANGE)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_design_dir_config_overrides_root(self):
        override = os.path.join(self.home, "elsewhere", "designs")
        self.write_project_config({"build": {"design_dir": override}})
        r = self.cli("path", CHANGE)
        self.assertEqual(r.returncode, 0, r.stderr)
        expected = os.path.join(override, CHANGE)
        self.assertEqual(r.stdout.strip(), expected)
        self.assertTrue(os.path.isdir(expected))

    def test_design_dir_config_is_home_expanded(self):
        self.write_project_config({"build": {"design_dir": "~/custom-designs"}})
        r = self.cli("path", CHANGE)
        self.assertEqual(r.returncode, 0, r.stderr)
        expected = os.path.join(self.home, "custom-designs", CHANGE)
        self.assertEqual(r.stdout.strip(), expected)
        self.assertTrue(os.path.isdir(expected))


class CleanVerbTest(DesignScriptTestBase):
    def test_removes_existing_dir_and_exits_zero(self):
        self.cli("path", CHANGE)
        expected = os.path.join(self.default_root(), CHANGE)
        self.assertTrue(os.path.isdir(expected))
        r = self.cli("clean", CHANGE)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(os.path.exists(expected))

    def test_missing_dir_warns_and_still_exits_zero(self):
        r = self.cli("clean", CHANGE)
        self.assertEqual(r.returncode, 0)
        self.assertNotEqual(r.stderr.strip(), "")

    def test_unremovable_dir_warns_and_still_exits_zero(self):
        # A plain file where a directory is expected makes shutil.rmtree fail
        # with NotADirectoryError regardless of privilege (unlike a
        # permission-based simulation, which root would bypass).
        root = self.default_root()
        os.makedirs(root, exist_ok=True)
        target = os.path.join(root, CHANGE)
        with open(target, "w", encoding="utf-8") as fh:
            fh.write("not a directory")
        r = self.cli("clean", CHANGE)
        self.assertEqual(r.returncode, 0)
        self.assertNotEqual(r.stderr.strip(), "")


if __name__ == "__main__":
    unittest.main()
