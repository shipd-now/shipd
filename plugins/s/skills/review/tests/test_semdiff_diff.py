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
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
SCRIPT = os.path.join(SCRIPTS, "semdiff.py")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import semdiff  # noqa: E402

HAVE_DIFFT = shutil.which("difft") is not None


def git(repo, *args, env=None):
    """Run a git command in ``repo`` with the ambient environment."""
    return subprocess.run(
        ["git", "-C", repo, *args],
        capture_output=True, text=True, check=True, env=env)


def _difft_absent_bindir(base):
    """A bin directory holding only a ``git`` symlink, so a process run with
    ``PATH`` set to it cannot find ``difft`` (or ``rg``) at all. Used to
    exercise the hard failure `semdiff diff` now raises when difftastic is
    missing outright."""
    bindir = os.path.join(base, "absentbin")
    os.makedirs(bindir, exist_ok=True)
    git_path = shutil.which("git")
    link = os.path.join(bindir, "git")
    if not os.path.exists(link):
        os.symlink(git_path, link)
    return bindir


def _difft_stub_bindir(base):
    """A bin directory holding a real ``git`` and a ``difft`` stub that always
    produces output `difft_json` cannot parse. `have("difft")` succeeds, so
    `semdiff diff` does not hard-fail on a missing binary, but every per-file
    difft invocation retries through the text engine exactly like a genuine
    parse failure would — this is how the suite exercises the fallback
    without difft ever being absent from PATH."""
    bindir = os.path.join(base, "stubbin")
    os.makedirs(bindir, exist_ok=True)
    git_path = shutil.which("git")
    git_link = os.path.join(bindir, "git")
    if not os.path.exists(git_link):
        os.symlink(git_path, git_link)
    stub = os.path.join(bindir, "difft")
    if not os.path.exists(stub):
        with open(stub, "w") as fh:
            fh.write("#!/bin/sh\necho 'not difft json'\nexit 1\n")
        os.chmod(stub, 0o755)
    return bindir


def run_semdiff(repo, *args, stub_difft=False, remove_difft=False, home=None):
    """Invoke semdiff.py inside ``repo`` and return (returncode, parsed_json,
    stderr). When ``stub_difft`` is set, PATH carries a ``difft`` that always
    fails to parse, forcing the per-file text-engine retry while difft stays
    present and `semdiff diff` does not hard-fail. When ``remove_difft`` is
    set, PATH carries no ``difft`` at all, exercising the hard failure."""
    env = dict(os.environ)
    if remove_difft:
        bindir = _difft_absent_bindir(home or repo)
        env["PATH"] = bindir
        env["HOME"] = home or repo
    elif stub_difft:
        bindir = _difft_stub_bindir(home or repo)
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

    # -- missing difft is a hard failure -------------------------------------

    def test_missing_difft_fails_the_diff(self):
        rc, out, err = run_semdiff(self.repo, "diff", "main",
                                   remove_difft=True, home=self.tmp)
        self.assertNotEqual(rc, 0, "a missing difft did not fail the diff")
        self.assertIsNone(out, "a missing difft still emitted diff JSON")
        self.assertIn("difft", err.lower())
        self.assertIn("install", err.lower())

    # -- per-file parse-failure retry -----------------------------------------

    def test_per_file_parse_failure_falls_back_to_text_engine(self):
        # difft stays present (`have("difft")` succeeds) but every per-file
        # invocation fails to parse, so each file retries through the text
        # engine rather than the whole diff hard-failing.
        rc, out, err = run_semdiff(self.repo, "diff", "main", stub_difft=True,
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


class LineNumberParityTest(unittest.TestCase):
    """Both engines must agree with `git -n` truth on the 1-based line number
    of an edited line — the off-by-one this change corrects in the difft
    engine (difft's own `line_number` is 0-based)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="semdiff-lineno-")
        self.repo = os.path.join(self.tmp, "repo")
        os.makedirs(self.repo)
        subprocess.run(["git", "-c", "init.defaultBranch=main", "init", "-q",
                        self.repo], check=True, capture_output=True)
        git(self.repo, "config", "user.email", "t@example.com")
        git(self.repo, "config", "user.name", "Test")
        git(self.repo, "config", "commit.gpgsign", "false")
        self._write("ten.py", "".join(f"line{n}\n" for n in range(1, 11)))
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "init")
        # Edit only the tenth line.
        self._write("ten.py",
                    "".join(f"line{n}\n" for n in range(1, 10)) + "EDITED\n")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, rel, text):
        with open(os.path.join(self.repo, rel), "w") as fh:
            fh.write(text)

    def _after_side_line(self, **kwargs):
        rc, out, err = run_semdiff(self.repo, "diff", "HEAD", **kwargs)
        self.assertEqual(rc, 0, err)
        by_path = {f["path"]: f for f in out["files"]}
        self.assertIn("ten.py", by_path)
        after = [h for h in by_path["ten.py"]["hunks"] if h["side"] == "after"]
        self.assertTrue(after, "no after-side hunk reported")
        return after[0]["line"]

    def test_text_engine_reports_line_10(self):
        self.assertEqual(
            self._after_side_line(stub_difft=True, home=self.tmp), 10)

    @unittest.skipUnless(HAVE_DIFFT, "difftastic not installed")
    def test_difft_engine_reports_line_10(self):
        self.assertEqual(self._after_side_line(), 10)


class AddedFileContentTest(unittest.TestCase):
    """A newly added file with no hunks carries its numbered body inline, so
    brand-new code doesn't ship reviewed on a path and a line count alone."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="semdiff-content-")
        self.repo = os.path.join(self.tmp, "repo")
        os.makedirs(self.repo)
        subprocess.run(["git", "-c", "init.defaultBranch=main", "init", "-q",
                        self.repo], check=True, capture_output=True)
        git(self.repo, "config", "user.email", "t@example.com")
        git(self.repo, "config", "user.name", "Test")
        git(self.repo, "config", "commit.gpgsign", "false")
        self._write("keep.txt", "hello\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "init")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, rel, text):
        with open(os.path.join(self.repo, rel), "w") as fh:
            fh.write(text)

    def _entry(self, path, **kwargs):
        rc, out, err = run_semdiff(self.repo, "diff", "HEAD", **kwargs)
        self.assertEqual(rc, 0, err)
        by_path = {f["path"]: f for f in out["files"]}
        self.assertIn(path, by_path)
        return by_path[path]

    def _assert_three_line_body(self, **kwargs):
        self._write("new.py", "one\ntwo\nthree\n")
        entry = self._entry("new.py", **kwargs)
        self.assertEqual(entry["kind"], "added")
        self.assertFalse(entry["content_truncated"])
        prefixes = [line.split(":", 1)[0] for line in entry["content"].splitlines()]
        self.assertEqual(prefixes, ["1", "2", "3"])

    def test_text_engine_three_line_body(self):
        self._assert_three_line_body(stub_difft=True, home=self.tmp)

    @unittest.skipUnless(HAVE_DIFFT, "difftastic not installed")
    def test_difft_engine_three_line_body(self):
        self._assert_three_line_body()

    def _assert_oversized_body_truncated(self, **kwargs):
        self._write("big.py", "".join(f"line{n}\n" for n in range(1, 701)))
        entry = self._entry("big.py", **kwargs)
        self.assertEqual(entry["kind"], "added")
        self.assertTrue(entry["content_truncated"])
        self.assertEqual(len(entry["content"].splitlines()), 600)

    def test_text_engine_oversized_body_truncated(self):
        self._assert_oversized_body_truncated(stub_difft=True, home=self.tmp)

    @unittest.skipUnless(HAVE_DIFFT, "difftastic not installed")
    def test_difft_engine_oversized_body_truncated(self):
        self._assert_oversized_body_truncated()


class SummarizeChunksLineNumberTest(unittest.TestCase):
    """A guard for the 0-based-to-1-based line number normalization in
    `summarize_chunks` that never depends on a `difft` binary: it calls
    `summarize_chunks` directly on a synthetic difft-shaped `chunks`
    argument, so it always runs regardless of what else is installed."""

    def test_line_number_normalized_to_one_based(self):
        # Shaped like real difft JSON: a list of chunks, each a list of line
        # dicts with "lhs"/"rhs" keys carrying a 0-based "line_number" and a
        # "changes" list of {"content": ...} tokens.
        chunks = [
            [
                {
                    "lhs": None,
                    "rhs": {
                        "line_number": 9,
                        "changes": [{"content": "new text"}],
                    },
                },
            ],
        ]
        hunks = semdiff.summarize_chunks(chunks)
        self.assertEqual(len(hunks), 1)
        self.assertEqual(hunks[0]["side"], "after")
        self.assertEqual(hunks[0]["line"], 10)
        self.assertEqual(hunks[0]["snippet"], "new text")


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
        kinds = self._kinds(stub_difft=True, home=self.tmp)
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
