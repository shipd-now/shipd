#!/usr/bin/env python3
"""Unit tests for version_guard: the stdlib-only plugin-version-bump guard
(shipd `plugin-version-advance`).

    python3 -m unittest discover -s plugins/s/skills/build/tests -v

The ``FindFindingTest`` and ``CompareVersionsTest`` classes cover only the
pure comparison, :func:`find_finding` (and the :func:`compare_versions` it
builds on) — no git, no network, no subprocess. ``MainCLITest`` drives
:func:`version_guard.main` end-to-end against a scratch git repository, since
CI consumes this script solely through its exit status and a pure-function
test suite cannot catch a broken ``sys.exit`` call in the CLI wiring.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import version_guard as vg  # noqa: E402


class FindFindingTest(unittest.TestCase):
    """The finding function: base version, head version, touched paths."""

    def test_plugin_change_with_unchanged_version_fails(self):
        finding = vg.find_finding(
            "0.6.222", "0.6.222",
            ["plugins/s/skills/build/tests/test_thing.py"])
        self.assertIsNotNone(finding)

    def test_plugin_change_with_bumped_version_passes(self):
        finding = vg.find_finding(
            "0.6.222", "0.6.223",
            ["plugins/s/skills/build/tests/test_thing.py"])
        self.assertIsNone(finding)

    def test_path_outside_plugin_is_exempt(self):
        finding = vg.find_finding(
            "0.6.222", "0.6.222", ["docs/customise.md"])
        self.assertIsNone(finding)

    def test_manifest_only_path_is_exempt(self):
        finding = vg.find_finding(
            "0.6.222", "0.6.222",
            ["plugins/s/.claude-plugin/plugin.json"])
        self.assertIsNone(finding)

    def test_numeric_components_rank_above_string_length(self):
        finding = vg.find_finding(
            "0.6.9", "0.6.10", ["plugins/s/skills/build/scripts/foo.py"])
        self.assertIsNone(finding)

    def test_decrease_fails(self):
        finding = vg.find_finding(
            "0.6.223", "0.6.222", ["plugins/s/skills/build/scripts/foo.py"])
        self.assertIsNotNone(finding)


class CompareVersionsTest(unittest.TestCase):
    """The pairwise component comparison never coerces to float."""

    def test_equal_versions_compare_equal(self):
        self.assertEqual(vg.compare_versions("0.6.222", "0.6.222"), 0)

    def test_numeric_increase_ranks_above(self):
        self.assertLess(vg.compare_versions("0.6.9", "0.6.10"), 0)

    def test_numeric_decrease_ranks_below(self):
        self.assertGreater(vg.compare_versions("0.6.223", "0.6.222"), 0)

    def test_never_collapses_via_float(self):
        # 0.6.9 and 0.6.90 would compare equal under float() coercion.
        self.assertLess(vg.compare_versions("0.6.9", "0.6.90"), 0)


def _git(repo_dir, *args):
    subprocess.run(
        ["git", *args],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        text=True,
    )


def _write_manifest(repo_dir, version):
    manifest_path = os.path.join(repo_dir, vg.MANIFEST_PATH)
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    with open(manifest_path, "w") as handle:
        json.dump({"name": "s", "version": version}, handle)


def _write_source(repo_dir, content):
    source_path = os.path.join(repo_dir, "plugins", "s", "source.py")
    os.makedirs(os.path.dirname(source_path), exist_ok=True)
    with open(source_path, "w") as handle:
        handle.write(content)


def _commit(repo_dir, message):
    _git(repo_dir, "add", "-A")
    _git(repo_dir, "commit", "-m", message)
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


class MainCLITest(unittest.TestCase):
    """Drive ``main()`` end-to-end against a scratch git repository.

    CI consumes this script only through its exit status, so these tests
    catch a broken ``sys.exit`` call that a pure-function test on
    :func:`find_finding` alone would miss.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo_dir = self._tmp.name
        self.addCleanup(self._tmp.cleanup)
        _git(self.repo_dir, "init", "-q")
        _git(self.repo_dir, "config", "user.email", "test@example.com")
        _git(self.repo_dir, "config", "user.name", "Test User")

    def _run_main(self, base, head):
        with self.assertRaises(SystemExit) as ctx:
            vg.main(["--base", base, "--head", head], cwd=self.repo_dir)
        return ctx.exception.code

    def test_exit_1_when_plugin_changes_without_version_bump(self):
        _write_manifest(self.repo_dir, "0.1.0")
        _write_source(self.repo_dir, "a\n")
        base = _commit(self.repo_dir, "base")

        _write_source(self.repo_dir, "b\n")
        head = _commit(self.repo_dir, "touch plugin, no bump")

        self.assertEqual(self._run_main(base, head), 1)

    def test_exit_0_when_plugin_changes_with_version_bump(self):
        _write_manifest(self.repo_dir, "0.1.0")
        _write_source(self.repo_dir, "a\n")
        base = _commit(self.repo_dir, "base")

        _write_source(self.repo_dir, "b\n")
        _write_manifest(self.repo_dir, "0.1.1")
        head = _commit(self.repo_dir, "touch plugin, with bump")

        self.assertEqual(self._run_main(base, head), 0)

    def test_exit_2_when_ref_has_no_manifest(self):
        with open(os.path.join(self.repo_dir, "README.md"), "w") as handle:
            handle.write("no manifest here\n")
        base = _commit(self.repo_dir, "no manifest")

        _write_manifest(self.repo_dir, "0.1.0")
        head = _commit(self.repo_dir, "add manifest")

        self.assertEqual(self._run_main(base, head), 2)

    def test_exit_2_when_version_is_not_a_string(self):
        _write_manifest(self.repo_dir, "0.1.0")
        base = _commit(self.repo_dir, "base")

        manifest_path = os.path.join(self.repo_dir, vg.MANIFEST_PATH)
        with open(manifest_path, "w") as handle:
            json.dump({"name": "s", "version": 1}, handle)
        head = _commit(self.repo_dir, "non-string version")

        self.assertEqual(self._run_main(base, head), 2)


if __name__ == "__main__":
    unittest.main()
