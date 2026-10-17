#!/usr/bin/env python3
"""Tests for brand.py: the commit-subject branding script and its hook
(shipd-brand brand-script-verbs, commit-brand-hook-install,
brand-engine-commits)."""

import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
SCRIPT = os.path.join(SCRIPTS, "brand.py")
SKILLS = os.path.normpath(os.path.join(HERE, "..", ".."))
BRAND = "☕ "
MARKER = "# shipd-managed commit-msg hook"


class BrandTestBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="brand-test-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.home = os.path.join(self.tmp, "home")
        os.makedirs(self.home)
        self.root = os.path.join(self.tmp, "repo")
        os.makedirs(self.root)
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Test")
        with open(os.path.join(self.root, "README.md"), "w") as fh:
            fh.write("seed\n")
        self.git("add", "README.md")
        self.git("commit", "-q", "-m", "seed")

    def env(self):
        env = dict(os.environ)
        env["HOME"] = self.home
        env["GIT_CONFIG_GLOBAL"] = os.devnull
        env["GIT_CONFIG_NOSYSTEM"] = "1"
        return env

    def git(self, *args, cwd=None, check=True):
        return subprocess.run(
            ["git", *args], cwd=cwd or self.root, capture_output=True,
            text=True, check=check, env=self.env())

    def brand(self, *args, cwd=None):
        return subprocess.run(
            [sys.executable, "-B", SCRIPT, *args], cwd=cwd or self.root,
            capture_output=True, text=True, env=self.env())

    def add_worktree(self, name="wt"):
        path = os.path.join(self.root, ".worktrees", name)
        self.git("worktree", "add", "-q", "-b", "change/" + name, path)
        return path

    def hook_path(self):
        return os.path.join(self.root, ".git", "hooks", "commit-msg")

    def msgfile(self, text):
        path = os.path.join(self.tmp, "MSG")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    def read(self, path):
        with open(path, encoding="utf-8") as fh:
            return fh.read()

    def last_subject(self, cwd):
        return self.git("log", "-1", "--format=%s", cwd=cwd).stdout.strip()


class SubjectVerbTest(BrandTestBase):
    def test_subject_prints_branded(self):
        r = self.brand("subject", "Install the gate")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), BRAND + "Install the gate")


class CommitMsgTest(BrandTestBase):
    def test_worktree_message_is_branded_comment_kept(self):
        wt = self.add_worktree()
        f = self.msgfile("hello\n# a comment\n")
        r = self.brand("commit-msg", f, cwd=wt)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.read(f), BRAND + "hello\n# a comment\n")

    def test_leading_comment_skipped(self):
        wt = self.add_worktree()
        f = self.msgfile("# c\nhello\n")
        self.brand("commit-msg", f, cwd=wt)
        self.assertEqual(self.read(f), "# c\n" + BRAND + "hello\n")

    def test_root_checkout_untouched(self):
        f = self.msgfile("hello\n")
        r = self.brand("commit-msg", f)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.read(f), "hello\n")


class InstallHookTest(BrandTestBase):
    def test_install_writes_marked_executable_hook(self):
        r = self.brand("install-hook", "--root", self.root)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(r.stdout.startswith("installed:"), r.stdout)
        text = self.read(self.hook_path())
        self.assertEqual(text.splitlines()[1], MARKER)
        self.assertIn(SCRIPT, text)
        self.assertEqual(stat.S_IMODE(os.stat(self.hook_path()).st_mode),
                         0o755)

    def test_marked_hook_is_refreshed(self):
        self.brand("install-hook", "--root", self.root)
        with open(self.hook_path(), "w") as fh:
            fh.write("#!/bin/sh\n%s\nexit 0\n# stale\n" % MARKER)
        r = self.brand("install-hook", "--root", self.root)
        self.assertTrue(r.stdout.startswith("refreshed:"), r.stdout)
        self.assertNotIn("stale", self.read(self.hook_path()))

    def test_refresh_replaces_hook_atomically(self):
        self.brand("install-hook", "--root", self.root)
        before = os.stat(self.hook_path()).st_ino
        hooks = os.path.dirname(self.hook_path())
        self.brand("install-hook", "--root", self.root)
        self.assertNotEqual(os.stat(self.hook_path()).st_ino, before)
        self.assertEqual([n for n in os.listdir(hooks) if ".tmp" in n], [])

    def test_foreign_hook_skipped(self):
        os.makedirs(os.path.dirname(self.hook_path()), exist_ok=True)
        with open(self.hook_path(), "w") as fh:
            fh.write("#!/bin/sh\nexit 0\n")
        r = self.brand("install-hook", "--root", self.root)
        self.assertEqual(r.returncode, 0)
        self.assertTrue(
            r.stdout.startswith("note: commit branding skipped — "),
            r.stdout)
        self.assertEqual(self.read(self.hook_path()), "#!/bin/sh\nexit 0\n")

    def test_hooks_path_skipped(self):
        hp = os.path.join(self.tmp, "myhooks")
        os.makedirs(hp)
        self.git("config", "core.hooksPath", hp)
        r = self.brand("install-hook", "--root", self.root)
        self.assertEqual(r.returncode, 0)
        self.assertTrue(
            r.stdout.startswith("note: commit branding skipped — "),
            r.stdout)
        self.assertEqual(os.listdir(hp), [])
        self.assertFalse(os.path.exists(self.hook_path()))

    def test_real_commit_in_worktree_is_branded(self):
        self.brand("install-hook", "--root", self.root)
        wt = self.add_worktree()
        with open(os.path.join(wt, "x.txt"), "w") as fh:
            fh.write("x\n")
        self.git("add", "x.txt", cwd=wt)
        self.git("commit", "-q", "-m", "add x", cwd=wt)
        self.assertEqual(self.last_subject(wt), BRAND + "add x")

    def test_root_commit_not_branded(self):
        self.brand("install-hook", "--root", self.root)
        with open(os.path.join(self.root, "y.txt"), "w") as fh:
            fh.write("y\n")
        self.git("add", "y.txt")
        self.git("commit", "-q", "-m", "add y")
        self.assertEqual(self.last_subject(self.root), "add y")

    def test_missing_brand_path_lets_commit_through(self):
        self.brand("install-hook", "--root", self.root)
        text = self.read(self.hook_path()).replace(SCRIPT, "/nonexistent/brand.py")
        with open(self.hook_path(), "w") as fh:
            fh.write(text)
        wt = self.add_worktree()
        with open(os.path.join(wt, "x.txt"), "w") as fh:
            fh.write("x\n")
        self.git("add", "x.txt", cwd=wt)
        self.git("commit", "-q", "-m", "add x", cwd=wt)
        self.assertEqual(self.last_subject(wt), "add x")


class SkillCommitLinesTest(unittest.TestCase):
    def test_skill_commit_lines_use_helper(self):
        for skill in ("gate", "epic"):
            path = os.path.join(SKILLS, skill, "SKILL.md")
            with open(path, encoding="utf-8") as fh:
                lines = [l for l in fh if "commit -m" in l]
            self.assertTrue(lines, skill)
            for line in lines:
                self.assertIn('brand.py" subject', line, line)


if __name__ == "__main__":
    unittest.main()
