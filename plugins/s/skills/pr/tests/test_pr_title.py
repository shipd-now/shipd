#!/usr/bin/env python3
"""Tests for pr_title.py — the ``/s:pr`` title renderer (shipd-pr
pr-title-render). Stdlib ``unittest``. The CLI is driven as a subprocess with
``HOME`` pointed at an empty directory so no real config leaks in."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
sys.path.insert(0, SCRIPTS)

import pr_title  # noqa: E402

SCRIPT = os.path.join(SCRIPTS, "pr_title.py")
PATTERN = "[A-Z]+-[0-9]+"


class RenderTest(unittest.TestCase):
    def test_ticket_from_the_branch(self):
        ticket = pr_title.find_ticket(PATTERN, "change/ABC-12-add-x")
        self.assertEqual(ticket, "ABC-12")
        self.assertEqual(
            pr_title.render_title("{ticket} {summary}", "Add x", ticket, ""),
            "ABC-12 Add x")

    def test_no_ticket_drops_the_placeholder(self):
        self.assertEqual(
            pr_title.render_title("{ticket} {summary}", "Add x", None, ""),
            "Add x")
        self.assertEqual(
            pr_title.render_title("{ticket} {summary}", "Add x", "", ""),
            "Add x")

    def test_missing_ticket_drops_wrapping_brackets(self):
        self.assertEqual(
            pr_title.render_title("[{ticket}] {summary}", "Add x", None, ""),
            "Add x")

    def test_no_pattern_or_no_match_finds_nothing(self):
        self.assertIsNone(pr_title.find_ticket(None, "change/ABC-1-x"))
        self.assertIsNone(pr_title.find_ticket(PATTERN, "change/add-x"))

    def test_change_is_the_slug(self):
        self.assertEqual(
            pr_title.render_title("{change}: {summary}", "Add x", None,
                                  "add-x"), "add-x: Add x")

    def test_whitespace_collapses(self):
        self.assertEqual(
            pr_title.render_title("{summary}", "Add   x \n y", None, ""),
            "Add x y")


class CliTest(unittest.TestCase):
    def _run(self, config, *args):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            if config is not None:
                with open(os.path.join(root, ".shipd-config.json"), "w",
                          encoding="utf-8") as fh:
                    json.dump(config, fh)
            env = dict(os.environ, HOME=os.path.realpath(home))
            return subprocess.run(
                [sys.executable, "-B", SCRIPT, "--root", root, "title", *args],
                capture_output=True, text=True, env=env)

    CONFIG = {"pr": {"title": "{ticket} {summary}",
                     "ticket_pattern": PATTERN}}

    def test_ticket_from_branch(self):
        r = self._run(self.CONFIG, "--summary", "Add x",
                      "--branch", "change/ABC-12-add-x")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "\u2615 Shipd: ABC-12 Add x")

    def test_no_ticket_drops_the_placeholder(self):
        r = self._run(self.CONFIG, "--summary", "Add x",
                      "--branch", "change/add-x")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "\u2615 Shipd: Add x")

    def test_flag_beats_branch(self):
        r = self._run(self.CONFIG, "--summary", "Add x", "--ticket", "XY-9",
                      "--branch", "change/ABC-12-add-x")
        self.assertEqual(r.stdout.strip(), "\u2615 Shipd: XY-9 Add x")

    def test_default_template_is_the_summary(self):
        r = self._run(None, "--summary", "Add x", "--branch", "change/add-x")
        self.assertEqual(r.stdout.strip(), "\u2615 Shipd: Add x")

    def test_change_placeholder_uses_the_branch_slug(self):
        r = self._run({"pr": {"title": "{change}: {summary}"}},
                      "--summary", "Add x", "--branch", "change/add-x")
        self.assertEqual(r.stdout.strip(), "\u2615 Shipd: add-x: Add x")

    def test_printed_title_carries_the_brand_once(self):
        r = self._run(None, "--summary", "Add x")
        self.assertEqual(r.stdout.strip(), "\u2615 Shipd: Add x")
        r = self._run(None, "--summary", "\u2615 Shipd: Add x")
        self.assertEqual(r.stdout.strip(), "\u2615 Shipd: Add x")

    def test_empty_title_exits_1(self):
        r = self._run(None, "--summary", "   ")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(r.stdout.strip(), "")

    def test_bad_config_exits_nonzero(self):
        r = self._run({"pr": {"title": "{ticket}"}}, "--summary", "x")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("pr", r.stderr)


if __name__ == "__main__":
    unittest.main()
