#!/usr/bin/env python3
"""Unit tests for `semdiff diff` — endpoint resolution, working-tree vs ref
comparison, whitespace filtering, and text-engine degradation.

Fixture git repositories are built in temporary directories; no network access
occurs. difft-dependent assertions skip when difftastic is absent, so the suite
exercises the text engine on a difft-less machine (CI has no difft)."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.normpath(os.path.join(HERE, "..", "scripts", "semdiff.py"))

HAVE_DIFFT = shutil.which("difft") is not None


def git(repo, *args, env=None):
    """Run a git command in ``repo`` with the ambient environment."""
    return subprocess.run(
        ["git", "-C", repo, *args],
        capture_output=True, text=True, check=True, env=env)


def _masked_bindir(base):
    """A bin directory holding only a ``git`` symlink, so a process run with
    ``PATH`` set to it cannot find ``difft`` (or ``rg``). Used to force the
    text engine deterministically regardless of what the host has installed."""
    bindir = os.path.join(base, "maskbin")
    os.makedirs(bindir, exist_ok=True)
    git_path = shutil.which("git")
    link = os.path.join(bindir, "git")
    if not os.path.exists(link):
        os.symlink(git_path, link)
    return bindir


def run_semdiff(repo, *args, mask_difft=False, home=None):
    """Invoke semdiff.py inside ``repo`` and return (returncode, parsed_json,
    stderr). When ``mask_difft`` is set, PATH is constrained so difft is absent
    — the text engine must handle it and still exit zero."""
    env = dict(os.environ)
    if mask_difft:
        bindir = _masked_bindir(home or repo)
        env["PATH"] = bindir
        env["HOME"] = home or repo
    r = subprocess.run(
        [sys.executable, SCRIPT, *args],
        cwd=repo, capture_output=True, text=True, env=env)
    parsed = None
    if r.stdout.strip():
        try:
            parsed = json.loads(r.stdout)
        except json.JSONDecodeError:
            parsed = None
    return r.returncode, parsed, r.stderr


class DiffTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="semdiff-diff-")
        self.repo = os.path.join(self.tmp, "repo")
        os.makedirs(self.repo)
        self._init_repo()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, rel, text):
        path = os.path.join(self.repo, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(text)

    def _init_repo(self):
        subprocess.run(["git", "-c", "init.defaultBranch=main", "init", "-q",
                        self.repo], check=True, capture_output=True)
        git(self.repo, "config", "user.email", "t@example.com")
        git(self.repo, "config", "user.name", "Test")
        git(self.repo, "config", "commit.gpgsign", "false")
        # Initial commit on main.
        self._write("src/code.py", "def a():\n    return 1\n\n\ndef b():\n    return 2\n")
        self._write("src/ws.py", "def c():\n    return 3\n")
        self._write("keep.txt", "hello\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "init")
        git(self.repo, "branch", "-M", "main")
        # A feature branch with a distinct edit to code.py.
        git(self.repo, "checkout", "-q", "-b", "feature")
        self._write("src/code.py",
                    "def a():\n    return 1\n\n\ndef feature_only():\n    return 99\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "feature edit")
        git(self.repo, "checkout", "-q", "main")
        # Working-tree edits on main: a content edit, a whitespace-only edit,
        # and an untracked file.
        self._write("src/code.py",
                    "def a():\n    return 1\n\n\ndef worktree_only():\n    return 7\n")
        # ws.py: reindent only — content is identical modulo whitespace.
        self._write("src/ws.py", "def c():\n        return 3\n")
        self._write("src/new.py", "def brand_new():\n    return 0\n")

    # -- working-tree mode ---------------------------------------------------

    def test_working_tree_lists_modified_and_untracked(self):
        rc, out, err = run_semdiff(self.repo, "diff", "main")
        self.assertEqual(rc, 0, err)
        self.assertEqual(out["mode"], "working-tree")
        self.assertEqual(out["base"], "main")
        self.assertIsNone(out["head"])
        by_path = {f["path"]: f for f in out["files"]}
        self.assertIn("src/code.py", by_path)
        self.assertIn("src/new.py", by_path)
        self.assertEqual(by_path["src/code.py"]["kind"], "modified")
        self.assertEqual(by_path["src/new.py"]["kind"], "added")

    def test_whitespace_only_edit_filtered(self):
        rc, out, err = run_semdiff(self.repo, "diff", "main")
        self.assertEqual(rc, 0, err)
        paths = {f["path"] for f in out["files"]}
        self.assertNotIn("src/ws.py", paths)

    def test_signature_change_estimated(self):
        rc, out, err = run_semdiff(self.repo, "diff", "main")
        self.assertEqual(rc, 0, err)
        # The new `def worktree_only()` line is a declaration marker.
        self.assertGreaterEqual(out["summary"]["signature_changes"], 1)

    # -- ref comparison ------------------------------------------------------

    def test_merge_base_mode_reads_after_from_ref(self):
        rc, out, err = run_semdiff(self.repo, "diff", "main", "feature")
        self.assertEqual(rc, 0, err)
        self.assertEqual(out["mode"], "merge-base")
        self.assertTrue(out.get("merge_base"))
        self.assertEqual(out["head"], "feature")
        blob = json.dumps(out["files"])
        # After side is the feature ref, not the working tree on main.
        self.assertIn("feature_only", blob)
        self.assertNotIn("worktree_only", blob)

    def test_linear_mode(self):
        rc, out, err = run_semdiff(self.repo, "diff", "main", "feature", "--linear")
        self.assertEqual(rc, 0, err)
        self.assertEqual(out["mode"], "linear")
        self.assertEqual(out["head"], "feature")

    # -- text-engine degradation --------------------------------------------

    def test_missing_difft_degrades_to_text_engine(self):
        rc, out, err = run_semdiff(self.repo, "diff", "main", mask_difft=True,
                                   home=self.tmp)
        self.assertEqual(rc, 0, err)
        self.assertEqual(out["summary"]["engine"], "text")
        for f in out["files"]:
            self.assertEqual(f["engine"], "text")

    @unittest.skipUnless(HAVE_DIFFT, "difftastic not installed")
    def test_difft_engine_when_available(self):
        rc, out, err = run_semdiff(self.repo, "diff", "main")
        self.assertEqual(rc, 0, err)
        self.assertEqual(out["summary"]["engine"], "difft")
        by_path = {f["path"]: f for f in out["files"]}
        self.assertEqual(by_path["src/code.py"]["engine"], "difft")
        self.assertTrue(by_path["src/code.py"]["hunks"])


class EmptyEndpointTest(unittest.TestCase):
    """A file present at an endpoint with empty content is not a file absent
    from it. Emptying a tracked file is a modification, not a deletion, and
    writing into a tracked empty file is a modification, not an addition —
    both misreported while the blob reader answered ``""`` for either."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="semdiff-empty-")
        self.repo = os.path.join(self.tmp, "repo")
        os.makedirs(self.repo)
        subprocess.run(["git", "-c", "init.defaultBranch=main", "init", "-q",
                        self.repo], check=True, capture_output=True)
        git(self.repo, "config", "user.email", "t@example.com")
        git(self.repo, "config", "user.name", "Test")
        git(self.repo, "config", "commit.gpgsign", "false")
        self._write("emptied.py", "def gone():\n    return 1\n")
        self._write("filled.py", "")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "init")
        # The working tree: the non-empty file emptied, the empty file filled.
        self._write("emptied.py", "")
        self._write("filled.py", "def arrived():\n    return 2\n")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, rel, text):
        with open(os.path.join(self.repo, rel), "w") as fh:
            fh.write(text)

    def _kinds(self, **kwargs):
        rc, out, err = run_semdiff(self.repo, "diff", "HEAD", **kwargs)
        self.assertEqual(rc, 0, err)
        return {f["path"]: f["kind"] for f in out["files"]}

    def test_text_engine_classifies_both_as_modified(self):
        kinds = self._kinds(mask_difft=True, home=self.tmp)
        self.assertEqual(kinds.get("emptied.py"), "modified",
                         "an emptied tracked file was reported as deleted")
        self.assertEqual(kinds.get("filled.py"), "modified",
                         "a filled tracked empty file was reported as added")

    @unittest.skipUnless(HAVE_DIFFT, "difftastic not installed")
    def test_difft_engine_classifies_both_as_modified(self):
        kinds = self._kinds()
        self.assertEqual(kinds.get("emptied.py"), "modified",
                         "an emptied tracked file was reported as deleted")
        self.assertEqual(kinds.get("filled.py"), "modified",
                         "a filled tracked empty file was reported as added")


if __name__ == "__main__":
    unittest.main()
