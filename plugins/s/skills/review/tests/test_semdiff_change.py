#!/usr/bin/env python3
"""Unit tests for `semdiff change` — the planned-change review bridge over the
shipd spec engine. Uses a copy of the build suite's sample fixture in a temp git
repo; no network access."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.normpath(os.path.join(HERE, "..", "scripts", "semdiff.py"))
SAMPLE_FIXTURE = os.path.normpath(os.path.join(
    HERE, "..", "..", "build", "tests", "fixtures", "sample"))


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args],
                          capture_output=True, text=True, check=True)


def run_semdiff(repo, *args):
    r = subprocess.run([sys.executable, SCRIPT, *args],
                       cwd=repo, capture_output=True, text=True)
    parsed = json.loads(r.stdout) if r.stdout.strip() else None
    return r.returncode, parsed, r.stderr


class ChangeBridgeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="semdiff-change-")
        self.repo = os.path.join(self.tmp, "repo")
        shutil.copytree(SAMPLE_FIXTURE, self.repo)
        # Append a path-like backtick token to the copied plan so impact-file
        # extraction has something to find (editing our own tempdir copy).
        plan = os.path.join(self.repo, ".shipd", "planned", "sample-change",
                            "plan.md")
        with open(plan, "a") as fh:
            fh.write("\n- Touches "
                     "`plugins/s/skills/review/scripts/semdiff.py`.\n")
        subprocess.run(["git", "-c", "init.defaultBranch=main", "init", "-q",
                        self.repo], check=True, capture_output=True)
        git(self.repo, "config", "user.email", "t@example.com")
        git(self.repo, "config", "user.name", "Test")
        git(self.repo, "config", "commit.gpgsign", "false")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "init")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_aggregated_change_context(self):
        rc, out, err = run_semdiff(self.repo, "change", "sample-change")
        self.assertEqual(rc, 0, err)
        self.assertEqual(out["change"], "sample-change")
        self.assertEqual(out["status"], "ready")

        # Deltas: the ADDED requirement carries its scenario text.
        by_id = {d.get("requirement_id"): d for d in out["deltas"]
                 if d.get("requirement_id")}
        self.assertIn("rate-limit-login", by_id)
        added = by_id["rate-limit-login"]
        self.assertEqual(added["operation"], "added")
        self.assertEqual(added["capability"], "auth")
        self.assertTrue(any("sixth failed login" in s
                            for s in added["scenarios"]))
        # The RENAMED operation surfaces its from/to.
        renamed = [d for d in out["deltas"] if d["operation"] == "renamed"]
        self.assertTrue(renamed)
        self.assertEqual(renamed[0]["from"], "password-complexity")
        self.assertEqual(renamed[0]["to"], "password-strength")

        # Task progress from checkbox states: all four unchecked.
        self.assertEqual(out["tasks"]["total"], 4)
        self.assertEqual(out["tasks"]["done"], 0)

        # A lint-clean change reports no findings.
        self.assertEqual(out["lint"]["findings"], [])

        # Impact files: the path-like token, not the bare-word backticks.
        self.assertIn("plugins/s/skills/review/scripts/semdiff.py",
                      out["impact_files"])
        self.assertNotIn("auth", out["impact_files"])

    def test_unknown_change_fails_clearly(self):
        rc, out, err = run_semdiff(self.repo, "change", "nope")
        self.assertNotEqual(rc, 0)
        self.assertIn("nope", err)


if __name__ == "__main__":
    unittest.main()
