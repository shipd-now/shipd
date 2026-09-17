#!/usr/bin/env python3
"""Unit tests for version_guard: the stdlib-only plugin-version-bump guard
(shipd `plugin-version-advance`).

    python3 -m unittest discover -s plugins/s/skills/build/tests -v

These tests cover only the pure comparison, :func:`find_finding` (and the
:func:`compare_versions` it builds on) — no git, no network, no subprocess.
"""

import os
import sys
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


if __name__ == "__main__":
    unittest.main()
