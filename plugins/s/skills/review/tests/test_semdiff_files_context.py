#!/usr/bin/env python3
"""Unit tests for `semdiff files` (cohort grouping) and `semdiff context`
(best-effort reference lookup). Fixtures are temp git repos; no network."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.normpath(os.path.join(HERE, "..", "scripts", "semdiff.py"))


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args],
                          capture_output=True, text=True, check=True)


def _git_only_bindir(base):
    """A bin dir holding only a git symlink, so rg/ast-grep are unfindable —
    forcing the git grep fallback deterministically."""
    bindir = os.path.join(base, "gitonly")
    os.makedirs(bindir, exist_ok=True)
    link = os.path.join(bindir, "git")
    if not os.path.exists(link):
        os.symlink(shutil.which("git"), link)
    return bindir


def run_semdiff(repo, *args, mask_rg=False, home=None):
    env = dict(os.environ)
    if mask_rg:
        env["PATH"] = _git_only_bindir(home or repo)
        env["HOME"] = home or repo
    r = subprocess.run([sys.executable, SCRIPT, *args],
                       cwd=repo, capture_output=True, text=True, env=env)
    parsed = json.loads(r.stdout) if r.stdout.strip() else None
    return r.returncode, parsed, r.stderr


class FilesCohortTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="semdiff-files-")
        self.repo = os.path.join(self.tmp, "repo")
        os.makedirs(self.repo)
        subprocess.run(["git", "-c", "init.defaultBranch=main", "init", "-q",
                        self.repo], check=True, capture_output=True)
        git(self.repo, "config", "user.email", "t@example.com")
        git(self.repo, "config", "user.name", "Test")
        git(self.repo, "config", "commit.gpgsign", "false")
        self._write("README.md", "seed\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "init")
        git(self.repo, "branch", "-M", "main")
        # Untracked working-tree changes spanning every cohort.
        for rel in (
            "plugins/s/skills/review/SKILL.md",
            ".shipd/planned/x/plan.md",
            "api/routes/users.py",
            "tests/test_x.py",
            "web/components/App.tsx",
            "randomtop/file.py",
        ):
            self._write(rel, "content\n")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, rel, text):
        path = os.path.join(self.repo, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(text)

    def test_cohort_grouping(self):
        rc, out, err = run_semdiff(self.repo, "files", "main")
        self.assertEqual(rc, 0, err)
        cohorts = out["cohorts"]

        def cohort_of(path):
            for name, paths in cohorts.items():
                if path in paths:
                    return name
            return None

        self.assertEqual(
            cohort_of("plugins/s/skills/review/SKILL.md"), "skills")
        self.assertEqual(cohort_of(".shipd/planned/x/plan.md"), "specs")
        self.assertEqual(cohort_of("api/routes/users.py"), "api")
        self.assertEqual(cohort_of("tests/test_x.py"), "tests")
        self.assertEqual(cohort_of("web/components/App.tsx"), "frontend")
        self.assertEqual(cohort_of("randomtop/file.py"), "randomtop")
        self.assertEqual(out["summary"]["files"], 6)


class ContextTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="semdiff-ctx-")
        self.repo = os.path.join(self.tmp, "repo")
        os.makedirs(self.repo)
        subprocess.run(["git", "-c", "init.defaultBranch=main", "init", "-q",
                        self.repo], check=True, capture_output=True)
        git(self.repo, "config", "user.email", "t@example.com")
        git(self.repo, "config", "user.name", "Test")
        git(self.repo, "config", "commit.gpgsign", "false")
        path = os.path.join(self.repo, "lib", "parser.py")
        os.makedirs(os.path.dirname(path))
        with open(path, "w") as fh:
            fh.write("def parse_spec(text):\n    return text\n\n\n"
                     "def caller():\n    return parse_spec('x')\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "init")
        git(self.repo, "branch", "-M", "main")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_git_grep_fallback_without_rg(self):
        rc, out, err = run_semdiff(self.repo, "context", "parse_spec",
                                   mask_rg=True, home=self.tmp)
        self.assertEqual(rc, 0, err)
        self.assertEqual(out["symbol"], "parse_spec")
        self.assertIn("best-effort", out["note"])
        self.assertGreaterEqual(len(out["matches"]), 2)
        for m in out["matches"]:
            self.assertIn("file", m)
            self.assertIn("line", m)
            self.assertIn("text", m)
        self.assertTrue(any(m["file"].endswith("parser.py")
                            for m in out["matches"]))


if __name__ == "__main__":
    unittest.main()
