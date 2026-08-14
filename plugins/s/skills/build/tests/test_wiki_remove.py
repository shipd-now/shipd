#!/usr/bin/env python3
"""Unit tests for the ``wiki-remove <slug>`` status verb (spec-status
wiki-remove-verb): page + index + log update, inbound-wikilink block with
byte-for-byte restore, reserved/missing-slug refusal, git auto-commit scoping,
non-git no-commit, and ``--personal`` store targeting."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import spec_common as sc  # noqa: E402

STATUS = os.path.join(SCRIPTS, "spec_status.py")


class WikiRemoveTestBase(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="wiki-remove-root-")
        self.home = tempfile.mkdtemp(prefix="wiki-remove-home-")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)
        shutil.rmtree(self.home, ignore_errors=True)

    def declare_workspace(self):
        with open(os.path.join(self.root, ".shipd-config.json"), "w",
                  encoding="utf-8") as fh:
            json.dump({"workspace": {}}, fh)

    def cli(self, *args):
        env = dict(os.environ)
        env["HOME"] = self.home
        return subprocess.run(
            ["python3", STATUS, "--root", self.root, *args],
            capture_output=True, text=True, env=env)

    def wiki(self):
        return os.path.join(self.root, ".shipd", "wiki")

    def write_page(self, store, slug, text):
        pages = os.path.join(store, "wiki")
        os.makedirs(pages, exist_ok=True)
        with open(os.path.join(pages, slug + ".md"), "w",
                  encoding="utf-8") as fh:
            fh.write(text)

    def write_file(self, store, name, text):
        with open(os.path.join(store, name), "w", encoding="utf-8") as fh:
            fh.write(text)

    def read_file(self, store, name):
        with open(os.path.join(store, name), encoding="utf-8") as fh:
            return fh.read()

    def snapshot(self, store):
        """Return a {relpath: bytes} map of every file under ``store``."""
        out = {}
        for dirpath, _dirs, names in os.walk(store):
            for name in names:
                p = os.path.join(dirpath, name)
                with open(p, "rb") as fh:
                    out[os.path.relpath(p, store)] = fh.read()
        return out


class WikiRemoveWorkspaceTest(WikiRemoveTestBase):
    """``wiki-remove`` on the workspace store (non-git tempdir root)."""

    def seed(self):
        self.declare_workspace()
        self.assertEqual(self.cli("wiki-init").returncode, 0)

    def test_successful_removal_updates_page_index_and_log(self):
        self.seed()
        store = self.wiki()
        self.write_page(store, "some-page", "# Some Page\n\nBody.\n")
        self.write_file(
            store, "index.md",
            "# Index\n\n- [[some-page]] — A removable page.\n")
        r = self.cli("wiki-remove", "some-page")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(
            os.path.exists(os.path.join(store, "wiki", "some-page.md")))
        self.assertNotIn("some-page", self.read_file(store, "index.md"))
        log = self.read_file(store, "log.md")
        self.assertRegex(log, r"##\s+\[\d{4}-\d{2}-\d{2}\]\s+remove\s+\|\s+some-page")

    def test_inbound_wikilink_blocks_and_restores(self):
        self.seed()
        store = self.wiki()
        self.write_page(store, "some-page", "# Some Page\n\nBody.\n")
        self.write_page(
            store, "other-page", "# Other\n\nSee [[some-page]] for more.\n")
        self.write_file(
            store, "index.md",
            "# Index\n\n- [[some-page]] — A page.\n"
            "- [[other-page]] — Another page.\n")
        before = self.snapshot(store)
        r = self.cli("wiki-remove", "some-page")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("other-page", r.stderr)
        self.assertEqual(self.snapshot(store), before)  # byte-for-byte restore

    def test_missing_page_refused(self):
        self.seed()
        store = self.wiki()
        before = self.snapshot(store)
        r = self.cli("wiki-remove", "no-such-page")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no-such-page", r.stderr)
        self.assertEqual(self.snapshot(store), before)

    def test_reserved_slug_refused(self):
        self.seed()
        store = self.wiki()
        before = self.snapshot(store)
        r = self.cli("wiki-remove", "index")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("reserved", r.stderr.lower())
        self.assertEqual(self.snapshot(store), before)

    def test_non_git_store_removal_succeeds_without_commit(self):
        # The tempdir root is not inside a git work tree, so no commit is
        # attempted and the removal still installs.
        self.seed()
        store = self.wiki()
        self.write_page(store, "some-page", "# Some Page\n\nBody.\n")
        self.write_file(
            store, "index.md", "# Index\n\n- [[some-page]] — A page.\n")
        r = self.cli("wiki-remove", "some-page")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(
            os.path.exists(os.path.join(store, "wiki", "some-page.md")))
        self.assertFalse(os.path.isdir(os.path.join(self.root, ".git")))


class WikiRemoveGitTest(WikiRemoveTestBase):
    """``wiki-remove`` auto-commits inside a git work tree (shipd-wiki
    wiki-autocommit)."""

    def git(self, *args):
        return subprocess.run(
            ["git", "-C", self.root, *args],
            capture_output=True, text=True)

    def test_git_store_removal_commits_touched_files(self):
        self.declare_workspace()
        self.assertEqual(self.git("init").returncode, 0)
        self.git("config", "user.email", "t@example.com")
        self.git("config", "user.name", "Test")
        self.assertEqual(self.cli("wiki-init").returncode, 0)
        store = self.wiki()
        self.write_page(store, "some-page", "# Some Page\n\nBody.\n")
        self.write_file(
            store, "index.md", "# Index\n\n- [[some-page]] — A page.\n")
        # Commit the initial store so the removal has tracked files to change.
        self.git("add", "-A")
        self.git("commit", "-m", "seed store")

        r = self.cli("wiki-remove", "some-page")
        self.assertEqual(r.returncode, 0, r.stderr)
        subject = self.git("log", "-1", "--format=%s").stdout.strip()
        self.assertEqual(subject, "shipd-wiki: remove some-page")
        # The commit is scoped to exactly the touched files.
        files = self.git(
            "show", "--name-only", "--format=", "HEAD").stdout.split()
        self.assertIn(".shipd/wiki/wiki/some-page.md", files)
        self.assertIn(".shipd/wiki/index.md", files)
        self.assertIn(".shipd/wiki/log.md", files)
        self.assertEqual(len(files), 3)


class WikiRemovePersonalTest(WikiRemoveTestBase):
    """``wiki-remove --personal`` targets the personal memory store and leaves
    the workspace store untouched."""

    def setUp(self):
        super().setUp()
        self.mem = tempfile.mkdtemp(prefix="wiki-remove-mem-")

    def tearDown(self):
        shutil.rmtree(self.mem, ignore_errors=True)
        super().tearDown()

    def test_personal_removal_leaves_workspace_untouched(self):
        with open(os.path.join(self.root, ".shipd-config.json"), "w",
                  encoding="utf-8") as fh:
            json.dump({"workspace": {}, "memory_dir": self.mem}, fh)
        # Workspace store with its own page.
        self.assertEqual(self.cli("wiki-init").returncode, 0)
        ws = self.wiki()
        self.write_page(ws, "some-page", "# WS Page\n\nBody.\n")
        self.write_file(
            ws, "index.md", "# Index\n\n- [[some-page]] — A ws page.\n")
        ws_before = self.snapshot(ws)
        # Personal store with a page of the same slug.
        self.assertEqual(self.cli("wiki-init", "--personal").returncode, 0)
        store = os.path.join(self.mem, "wiki")
        self.write_page(store, "some-page", "# Personal\n\nBody.\n")
        self.write_file(
            store, "index.md", "# Index\n\n- [[some-page]] — A personal page.\n")

        r = self.cli("wiki-remove", "some-page", "--personal")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(
            os.path.exists(os.path.join(store, "wiki", "some-page.md")))
        self.assertNotIn("some-page", self.read_file(store, "index.md"))
        # The workspace store is byte-for-byte unchanged.
        self.assertEqual(self.snapshot(ws), ws_before)


if __name__ == "__main__":
    unittest.main()
