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
        self.assertEqual(out["location"], "planned")
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

        # A lint-clean planned change reports no findings, and the linter ran.
        self.assertEqual(out["lint"]["findings"], [])
        self.assertNotIn("skipped", out["lint"])

        # Impact files: the path-like token, not the bare-word backticks.
        self.assertIn("plugins/s/skills/review/scripts/semdiff.py",
                      out["impact_files"])
        self.assertNotIn("auth", out["impact_files"])

    def test_archived_change_resolves(self):
        planned = os.path.join(self.repo, ".shipd", "planned", "sample-change")
        completed = os.path.join(self.repo, ".shipd", "completed")
        os.makedirs(completed, exist_ok=True)
        archive = os.path.join(completed, "2026-01-01-sample-change")
        shutil.move(planned, archive)
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "archive")

        rc, out, err = run_semdiff(self.repo, "change", "sample-change")
        self.assertEqual(rc, 0, err)
        self.assertEqual(out["location"], "completed")
        self.assertTrue(
            out["dir"].endswith(os.path.join(
                "completed", "2026-01-01-sample-change")),
            out["dir"])

        # The archive's deltas still parse.
        by_id = {d.get("requirement_id"): d for d in out["deltas"]
                 if d.get("requirement_id")}
        self.assertTrue(any("sixth failed login" in s
                            for s in by_id["rate-limit-login"]["scenarios"]))
        self.assertEqual(out["tasks"]["total"], 4)

        # The linter runs over planned/ only, so an archive reports why not.
        self.assertEqual(out["lint"]["findings"], [])
        self.assertIn("skipped", out["lint"])

    def test_newest_archive_wins(self):
        planned = os.path.join(self.repo, ".shipd", "planned", "sample-change")
        completed = os.path.join(self.repo, ".shipd", "completed")
        os.makedirs(completed, exist_ok=True)
        for name in ("2026-01-01-sample-change", "2026-02-01-sample-change"):
            shutil.copytree(planned, os.path.join(completed, name))
        shutil.rmtree(planned)
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "archive twice")

        rc, out, err = run_semdiff(self.repo, "change", "sample-change")
        self.assertEqual(rc, 0, err)
        self.assertTrue(
            out["dir"].endswith(os.path.join(
                "completed", "2026-02-01-sample-change")),
            out["dir"])

    def test_unknown_change_fails_clearly(self):
        rc, out, err = run_semdiff(self.repo, "change", "nope")
        self.assertNotEqual(rc, 0)
        self.assertIn("nope", err)
        self.assertIn("completed/", err)


if __name__ == "__main__":
    unittest.main()
