#!/usr/bin/env python3
"""Tests for ``plugins/s/bin/shipd`` — the curated CLI dispatcher.

The binary is driven as a black box via subprocess, invoked by path so its
shebang and exec bit are exercised too, against throwaway temp repo roots laid
out as ``.shipd/planned/<change>/plan.md`` — never against the real repo. ``HOME``
is isolated so the layered content-dir config resolution never reads the real
home. Mirrors the subprocess-against-temp-roots style of
``test_spec_status.py``.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
BIN = os.path.normpath(os.path.join(HERE, "..", "..", "..", "bin", "shipd"))

# The curated verb table the usage banner must name (shipd-cli cli-dispatch).
VERBS = ("list", "status", "locate", "epic", "workspace", "board", "metrics",
         "lint")

EPIC_HEADER = (
    "| Change | Description | Code | Integration | Unknowns | Risk |\n"
    "| --- | --- | --- | --- | --- | --- |\n")


def _imports_textual(python):
    """True when ``python`` can import ``textual``."""
    try:
        return subprocess.run(
            [python, "-c", "import textual"],
            capture_output=True).returncode == 0
    except OSError:
        return False


# ``dashboard.py``'s script entry calls ``tui_bootstrap.ensure_textual`` before
# its own module-scope ``textual`` import, so *any* subprocess invocation of it
# — ``board`` and ``html`` included — self-provisions the dependency into a
# cached venv over the network when ``textual`` is missing. This suite is the
# stdlib-only one that must pass without ``textual`` installed (the
# constitution's named exception lives in ``tests_textual/``), so every
# board-mode delegation test is skipped rather than allowed to trigger that
# bootstrap. Both the runner's interpreter (which drives the engine script
# directly) and the PATH ``python3`` (which the binary's shebang resolves to)
# must have it.
HAS_TEXTUAL = _imports_textual(sys.executable) and _imports_textual("python3")


class ShipdCliTestBase(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="shipd-cli-test-")
        self.home = tempfile.mkdtemp(prefix="shipd-cli-home-")
        os.makedirs(os.path.join(self.root, ".shipd", "planned"))

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)
        shutil.rmtree(self.root, ignore_errors=True)

    # -- fixture helpers ---------------------------------------------------

    def write(self, path, text):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)

    def make_change(self, root, change, status="ready"):
        """Plant ``<root>/.shipd/planned/<change>/plan.md`` at ``status``."""
        self.write(
            os.path.join(root, ".shipd", "planned", change, "plan.md"),
            "# %s\nStatus: %s\n\n## Idea\n\nA thing.\n" % (change, status))

    def make_worktree_change(self, worktree, change, status="ready"):
        """Plant a change inside ``<root>/.worktrees/<worktree>``."""
        self.make_change(
            os.path.join(self.root, ".worktrees", worktree), change,
            status=status)

    def make_archive(self, change, date="2026-08-14"):
        """Plant an applied change at ``.shipd/completed/<date>-<change>/``."""
        self.write(
            os.path.join(self.root, ".shipd", "completed",
                         "%s-%s" % (date, change), "plan.md"),
            "# %s\nStatus: verified\n\n## Idea\n\nA thing.\n" % change)

    def make_epic(self, slug, members, status="ready"):
        """Plant ``.shipd/epics/<slug>/epic.md`` with a stub member table."""
        body = ["# %s\n" % slug, "Status: %s\n" % status, "\n",
                "## Changes\n", "\n", EPIC_HEADER]
        for member in members:
            body.append("| %s | a member | low | low | low | low |\n" % member)
        self.write(
            os.path.join(self.root, ".shipd", "epics", slug, "epic.md"),
            "".join(body))

    # -- runners -----------------------------------------------------------

    def env(self):
        env = dict(os.environ)
        env["HOME"] = self.home
        # The delivery board's dependency bootstrap caches its venv under
        # XDG_CACHE_HOME; point it at the throwaway home so no test can write
        # to the real cache.
        env["XDG_CACHE_HOME"] = os.path.join(self.home, ".cache")
        return env

    def cli(self, *args, cwd=None):
        """Run the binary itself (shebang + exec bit) from ``cwd``."""
        return subprocess.run(
            [BIN, *args], capture_output=True, text=True,
            cwd=cwd if cwd is not None else self.root, env=self.env())

    def script(self, script, *args, cwd=None):
        """Run an engine script directly, for delegation equivalence."""
        return subprocess.run(
            [sys.executable, os.path.join(SCRIPTS, script), *args],
            capture_output=True, text=True,
            cwd=cwd if cwd is not None else self.root, env=self.env())

    def assertUsageBanner(self, text):
        self.assertIn("usage:", text)
        for verb in VERBS:
            self.assertIn(verb, text, "banner omits verb %r" % verb)


class DispatchTest(ShipdCliTestBase):
    def test_unknown_verb_is_a_usage_error(self):
        r = self.cli("frobnicate")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(r.stdout, "")
        self.assertUsageBanner(r.stderr)

    def test_missing_verb_is_a_usage_error(self):
        r = self.cli()
        self.assertEqual(r.returncode, 2)
        self.assertEqual(r.stdout, "")
        self.assertUsageBanner(r.stderr)

    def test_help_exits_zero_on_stdout(self):
        for flag in ("--help", "-h", "help"):
            with self.subTest(flag=flag):
                r = self.cli(flag)
                self.assertEqual(r.returncode, 0)
                self.assertEqual(r.stderr, "")
                self.assertUsageBanner(r.stdout)

    def test_locate_missing_change_preserves_output_and_exit_code(self):
        r = self.cli("locate", "no-such-change")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Error: change 'no-such-change' not found", r.stderr)

    @unittest.skipUnless(HAS_TEXTUAL, "dashboard.py's script entry provisions "
                                      "textual; see HAS_TEXTUAL")
    def test_bare_board_is_the_interactive_board(self):
        # ``--help`` proves the default-mode mapping (and that flags reach the
        # delegate untouched) without launching the full-screen app.
        direct = self.script("dashboard.py", "tui", "--help")
        r = self.cli("board", "--help")
        self.assertEqual(direct.returncode, 0, direct.stderr)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, direct.stdout)

    @unittest.skipUnless(HAS_TEXTUAL, "dashboard.py's script entry provisions "
                                      "textual; see HAS_TEXTUAL")
    def test_board_text_delegates_to_dashboard_board(self):
        self.make_epic("ep", ["m1", "m2"])
        self.make_change(self.root, "m1", status="ready")
        direct = self.script("dashboard.py", "board", "--root", self.root)
        r = self.cli("board", "text", "--root", self.root)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(direct.returncode, 0)
        self.assertEqual(r.stdout, direct.stdout)
        self.assertIn("epic ep", r.stdout)

    @unittest.skipUnless(HAS_TEXTUAL, "dashboard.py's script entry provisions "
                                      "textual; see HAS_TEXTUAL")
    def test_board_html_writes_one_snapshot(self):
        self.make_epic("ep", ["m1"])
        self.make_change(self.root, "m1", status="ready")
        out = os.path.join(self.root, "board.html")
        r = self.cli("board", "html", "--root", self.root, "--out", out,
                     "--once")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(os.path.exists(out), "html mode wrote no page")
        with open(out, encoding="utf-8") as fh:
            page = fh.read()
        self.assertIn("<html", page.lower())
        self.assertIn("ep", page)

    def test_retired_tui_verb_is_a_usage_error(self):
        r = self.cli("tui")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(r.stdout, "")
        self.assertUsageBanner(r.stderr)


class ListTest(ShipdCliTestBase):
    def rows(self, *args):
        """Run ``shipd list`` and return its non-empty output lines."""
        r = self.cli("list", "--root", self.root, *args)
        self.assertEqual(r.returncode, 0, r.stderr)
        return [line for line in r.stdout.splitlines() if line.strip()]

    def rows_for(self, rows, change):
        """Every row whose first whitespace-separated field is ``change``."""
        return [row for row in rows if row.split()[0] == change]

    def test_root_change_is_listed_as_root(self):
        self.make_change(self.root, "foo", status="active")
        rows = self.rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].split(), ["foo", "root", "active"])

    def test_worktree_change_is_listed_with_its_status(self):
        self.make_worktree_change("foo", "foo", status="ready")
        rows = self.rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].split(), ["foo", "worktree:foo", "ready"])

    def test_duplicate_change_deduped_worktree_wins(self):
        self.make_change(self.root, "foo", status="active")
        self.make_worktree_change("foo", "foo", status="ready")
        rows = self.rows()
        self.assertEqual(len(self.rows_for(rows, "foo")), 1)
        self.assertEqual(rows[0].split(), ["foo", "worktree:foo", "ready"])

    def test_worktree_without_a_content_dir_is_skipped(self):
        os.makedirs(os.path.join(self.root, ".worktrees", "stray"))
        self.make_change(self.root, "foo", status="ready")
        rows = self.rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].split()[0], "foo")

    def test_completed_changes_only_under_all(self):
        self.make_archive("bar")
        plain = self.cli("list", "--root", self.root)
        self.assertEqual(plain.returncode, 0)
        self.assertNotIn("bar", plain.stdout)
        self.assertIn("no changes in flight", plain.stdout)

        rows = self.rows("--all")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].split(), ["bar", "root", "archived"])

    def test_empty_tree(self):
        r = self.cli("list", "--root", self.root)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "no changes in flight")


class VersionTest(ShipdCliTestBase):
    def test_version_is_the_plugin_manifest_version(self):
        manifest = os.path.normpath(
            os.path.join(HERE, "..", "..", "..", ".claude-plugin",
                         "plugin.json"))
        with open(manifest, encoding="utf-8") as fh:
            expected = json.load(fh)["version"]
        r = self.cli("--version")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), expected)


if __name__ == "__main__":
    unittest.main()
