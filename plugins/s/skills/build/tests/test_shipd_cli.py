#!/usr/bin/env python3
"""Tests for ``plugins/s/bin/shipd`` — the curated CLI dispatcher.

The binary is driven as a black box via subprocess, invoked by path so its
shebang and exec bit are exercised too, against throwaway temp repo roots laid
out as ``.shipd/planned/<change>/plan.md`` — never against the real repo. ``HOME``
is isolated so the layered content-dir config resolution never reads the real
home. Mirrors the subprocess-against-temp-roots style of
``test_spec_status.py``.

The ``doctor`` checks are the one exception to the black-box style: they read
the *ambient* environment (PATH, the interpreter, the plugin cache layout), so
driving them through a subprocess would make the suite's verdict depend on the
machine running it. They are instead loaded in-process and exercised through
their injection points — a stub ``which``, a stub ``gh`` runner, a fabricated
cache root, an explicit ``version_info`` — so every branch is deterministic and
nothing shells out.
"""

import contextlib
import importlib.machinery
import importlib.util
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
PLUGIN_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
BIN = os.path.join(PLUGIN_ROOT, "bin", "shipd")
MANIFEST = os.path.join(PLUGIN_ROOT, ".claude-plugin", "plugin.json")

# The curated verb table the usage banner must name (shipd-cli cli-dispatch).
VERBS = ("init", "list", "status", "locate", "related", "epic", "workspace",
         "board", "metrics", "lint", "worktree", "doctor", "statusline",
         "copilot", "vendor", "harness", "install", "update")


def _load_binary():
    """Import ``bin/shipd`` as a module. It has no ``.py`` suffix, so the
    source loader is named explicitly rather than inferred from the path."""
    loader = importlib.machinery.SourceFileLoader("shipd_bin_under_test", BIN)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


shipd = _load_binary()

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
# — ``board`` included — self-provisions the dependency into a
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
    def test_unknown_board_mode_word_falls_through_to_the_interactive_delegate(
            self):
        # ``text`` is the only board mode word, so any other word is not
        # consumed: it reaches ``dashboard.py tui`` as a trailing argument,
        # which argparse rejects by name. Naming it in the assertion is what
        # makes this discriminating — a wrongly-consumed word would run
        # ``dashboard.py board --root <root>`` cleanly instead.
        self.make_epic("ep", ["m1"])
        self.make_change(self.root, "m1", status="ready")
        r = self.cli("board", "frobnicate", "--root", self.root)
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("unrecognized arguments", r.stderr)
        self.assertIn("frobnicate", r.stderr)

    def test_related_is_a_curated_verb_mapped_to_the_status_script(self):
        """The `related` row delegates to ``spec_status.py related``
        (shipd-cli cli-dispatch)."""
        self.assertEqual(shipd.VERB_TABLE.get("related"),
                         ("spec_status.py", ["related"]))

    def test_the_banner_names_related_as_json_capable(self):
        r = self.cli("--help")
        self.assertEqual(r.returncode, 0)
        # The note wraps across lines, so match the whole trailing paragraph
        # naming the --json-capable read verbs.
        note = [para for para in r.stdout.split("\n\n") if "--json" in para]
        self.assertEqual(len(note), 1, r.stdout)
        self.assertIn("related", note[0])

    def test_related_no_match_preserves_output_and_exit_code(self):
        # ``--root`` is the engine parser's *global* option, so it precedes the
        # verb; running from the repo root is the equivalent the sibling
        # ``locate`` delegation test uses.
        direct = self.script("spec_status.py", "--root", self.root,
                             "related", "zzz-no-such-term")
        r = self.cli("related", "zzz-no-such-term")
        self.assertNotEqual(direct.returncode, 0, direct.stderr)
        self.assertEqual(r.returncode, direct.returncode)
        self.assertEqual(r.stderr, direct.stderr)
        self.assertIn("Error:", r.stderr)

    def test_related_delegates_the_ranked_report(self):
        self.make_change(self.root, "dark-mode")
        direct = self.script("spec_status.py", "--root", self.root,
                             "related", "dark-mode")
        r = self.cli("related", "dark-mode")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, direct.stdout)
        self.assertIn("kind: planned", r.stdout)
        self.assertIn("slug: dark-mode", r.stdout)

    def test_init_is_a_curated_verb_mapped_to_the_status_script(self):
        """The `init` row delegates to ``spec_status.py init``
        (shipd-cli cli-dispatch)."""
        self.assertEqual(shipd.VERB_TABLE.get("init"),
                         ("spec_status.py", ["init"]))

    def test_the_banner_lists_init_as_a_verb(self):
        # Discriminating on the verb *row*, not a bare substring: `init` also
        # occurs inside `in-flight` and `initiatives` in the banner's prose.
        r = self.cli("--help")
        self.assertEqual(r.returncode, 0)
        rows = [line.strip() for line in r.stdout.splitlines()
                if line.strip().startswith("init ")]
        self.assertEqual(len(rows), 1, r.stdout)
        self.assertIn("--root", rows[0])

    def test_init_creates_the_layout_and_reports_ready(self):
        target = tempfile.mkdtemp(prefix="shipd-cli-init-")
        self.addCleanup(shutil.rmtree, target, True)
        r = self.cli("init", "--root", target)
        self.assertEqual(r.returncode, 0, r.stderr)
        for name in ("verified", "planned", "completed", "research"):
            self.assertTrue(
                os.path.isdir(os.path.join(target, ".shipd", name)), name)
        self.assertEqual(r.stdout.splitlines()[-1],
                         "all shipd directories are ready")

    def test_worktree_is_a_curated_verb_mapped_to_the_worktree_script(self):
        """The `worktree` row delegates to ``worktree.py``
        (shipd-cli cli-dispatch)."""
        self.assertEqual(shipd.VERB_TABLE.get("worktree"),
                         ("worktree.py", []))

    def test_the_banner_lists_worktree_as_a_verb(self):
        # Discriminating on the verb *row*, not a bare substring: `worktrees`
        # also occurs inside the `list` row's prose.
        r = self.cli("--help")
        self.assertEqual(r.returncode, 0)
        rows = [line.strip() for line in r.stdout.splitlines()
                if line.strip().startswith("worktree ")]
        self.assertEqual(len(rows), 1, r.stdout)

    def test_bare_worktree_prints_the_delegate_usage(self):
        # shipd-cli cli-dispatch: Worktree is a curated verb that delegates.
        direct = self.script("worktree.py")
        r = self.cli("worktree")
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(r.returncode, direct.returncode)
        self.assertEqual(r.stderr, direct.stderr)
        self.assertIn("usage: worktree.py", r.stderr)
        # The delegate's own usage, never the shipd banner.
        self.assertNotIn("usage: shipd <verb>", r.stderr)

    def test_worktree_passes_trailing_arguments_through(self):
        direct = self.script("worktree.py", "prune-branches")
        r = self.cli("worktree", "prune-branches")
        self.assertEqual(r.returncode, direct.returncode)
        self.assertEqual(r.stderr, direct.stderr)

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


class ListJsonTest(ShipdCliTestBase):
    """``shipd list --json`` emits the listing as a JSON array (shipd-cli
    list-json), and a delegated verb passes ``--json`` through verbatim.

    Written test-first; expected to FAIL until the flag lands in
    ``bin/shipd`` (task 2.2)."""

    def json_rows(self, *args):
        r = self.cli("list", "--root", self.root, *args)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def test_list_json_carries_name_location_and_status(self):
        self.make_worktree_change("foo", "foo", status="ready")
        self.assertEqual(
            self.json_rows("--json"),
            [{"name": "foo", "location": "worktree:foo", "status": "ready"}])

    def test_list_json_rows_match_the_text_rows_and_order(self):
        self.make_change(self.root, "alpha", status="active")
        self.make_worktree_change("zulu", "zulu", status="ready")
        text = self.cli("list", "--root", self.root)
        self.assertEqual(text.returncode, 0, text.stderr)
        self.assertEqual(
            [[row["name"], row["location"], row["status"]]
             for row in self.json_rows("--json")],
            [line.split() for line in text.stdout.splitlines()])

    def test_list_json_all_appends_the_archived_rows(self):
        self.make_change(self.root, "live", status="active")
        self.make_archive("bar")
        self.assertEqual(
            self.json_rows("--json", "--all"),
            [{"name": "live", "location": "root", "status": "active"},
             {"name": "bar", "location": "root", "status": "archived"}])

    def test_list_json_omits_archived_rows_without_all(self):
        self.make_archive("bar")
        self.assertEqual(self.json_rows("--json"), [])

    def test_empty_listing_is_an_empty_array(self):
        r = self.cli("list", "--root", self.root, "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout), [])
        self.assertNotIn("no changes in flight", r.stdout)

    def test_list_text_is_unchanged_without_the_flag(self):
        self.make_change(self.root, "foo", status="active")
        r = self.cli("list", "--root", self.root)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "foo  root  active\n")

    def test_delegated_epic_verb_passes_the_flag_through(self):
        # Both run from ``self.root``, so the engine's ``--root`` default
        # resolves identically; the flag is the only trailing argument.
        self.make_epic("ep", ["m1"])
        self.make_change(self.root, "m1", status="ready")
        direct = self.script("spec_status.py", "epic-show", "ep", "--json")
        r = self.cli("epic", "ep", "--json")
        self.assertEqual(direct.returncode, 0, direct.stderr)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, direct.stdout)
        self.assertEqual(json.loads(r.stdout)["kind"], "epic")

    def test_delegated_status_verb_passes_the_flag_through(self):
        self.make_change(self.root, "foo", status="active")
        direct = self.script("spec_status.py", "show", "foo", "--json")
        r = self.cli("status", "foo", "--json")
        self.assertEqual(direct.returncode, 0, direct.stderr)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, direct.stdout)
        self.assertEqual(json.loads(r.stdout)["kind"], "change")


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


class StatuslineVerbTest(unittest.TestCase):
    """``shipd statusline`` (shipd-cli statusline-verb).

    The binary's first mutating verb, so it is driven in-process against an
    injected ``--settings`` path under a throwaway temp directory — the real
    ``~/.claude/settings.json`` is never read and never written by this suite.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="shipd-statusline-test-")
        self.settings = os.path.join(self.tmp, "claude", "settings.json")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # -- runners -----------------------------------------------------------

    def run_verb(self, *args, plugin_root=None):
        """``cmd_statusline`` with stdout/stderr captured; the registered
        command's source root is injected so the verdict never depends on
        where this checkout lives."""
        out, err = io.StringIO(), io.StringIO()
        root = plugin_root if plugin_root is not None else self.checkout()
        with unittest.mock.patch.object(shipd, "PLUGIN_ROOT", root):
            with redirect_stdout(out), redirect_stderr(err):
                code = shipd.cmd_statusline(list(args))
        return out.getvalue(), err.getvalue(), code

    def install(self, *args, plugin_root=None):
        return self.run_verb("install", "--settings", self.settings, *args,
                             plugin_root=plugin_root)

    def checkout(self):
        """A fabricated repository checkout's ``plugins/s``."""
        root = os.path.join(self.tmp, "repo", "plugins", "s")
        os.makedirs(os.path.join(root, "integrations"), exist_ok=True)
        return root

    def snapshot(self, versions=("0.6.9", "0.6.10")):
        """A fabricated plugin cache; the *first* version directory is
        returned, so callers run from a snapshot with a newer sibling."""
        base = os.path.join(self.tmp, "cache", "shipd", "s")
        for version in versions:
            os.makedirs(os.path.join(base, version, "integrations"),
                        exist_ok=True)
        return os.path.join(base, versions[0])

    def write_settings(self, text):
        os.makedirs(os.path.dirname(self.settings), exist_ok=True)
        with open(self.settings, "w", encoding="utf-8") as fh:
            fh.write(text)

    def read_settings(self):
        with open(self.settings, encoding="utf-8") as fh:
            return fh.read()

    def registration(self):
        return json.loads(self.read_settings())["statusLine"]

    # -- the registered command -------------------------------------------

    def test_checkout_registers_the_absolute_repo_script_path(self):
        root = self.checkout()
        command = shipd.statusline_command(root)
        self.assertEqual(
            command,
            "bash %s" % os.path.join(root, "integrations", "statusline.sh"))
        self.assertTrue(os.path.isabs(command.split(None, 1)[1]))

    def test_this_checkout_registers_its_own_integrations_script(self):
        # Against the real plugin root, the command must name the checkout's
        # own script — the file the statusline actually renders from.
        command = shipd.statusline_command(shipd.PLUGIN_ROOT)
        self.assertEqual(
            command,
            "bash %s" % os.path.join(str(shipd.PLUGIN_ROOT), "integrations",
                                     "statusline.sh"))

    def test_snapshot_registers_a_version_resolving_command(self):
        root = self.snapshot()
        command = shipd.statusline_command(root)
        # Resolved at render time from the cache directory, ordered by
        # ``sort -V`` — never a pinned version path, which a plugin update
        # would strand.
        self.assertIn("sort -V", command)
        self.assertIn(os.path.dirname(root), command)
        self.assertIn("integrations/statusline.sh", command)
        self.assertNotIn("0.6.9", command)
        self.assertNotIn("0.6.10", command)

    # -- install -----------------------------------------------------------

    def test_install_creates_a_fresh_settings_file(self):
        self.assertFalse(os.path.exists(self.settings))
        out, _err, code = self.install()
        self.assertEqual(code, 0)
        entry = self.registration()
        self.assertEqual(entry["type"], "command")
        self.assertEqual(entry["command"],
                         shipd.statusline_command(self.checkout()))
        self.assertIn(entry["command"], out)

    def test_install_creates_the_parent_directory(self):
        self.assertFalse(os.path.isdir(os.path.dirname(self.settings)))
        _out, _err, code = self.install()
        self.assertEqual(code, 0)
        self.assertTrue(os.path.isfile(self.settings))

    def test_unrelated_keys_survive_the_write(self):
        self.write_settings(json.dumps(
            {"model": "opus", "env": {"FOO": "bar"}}))
        _out, _err, code = self.install()
        self.assertEqual(code, 0)
        data = json.loads(self.read_settings())
        self.assertEqual(data["model"], "opus")
        self.assertEqual(data["env"], {"FOO": "bar"})
        self.assertEqual(data["statusLine"]["type"], "command")

    def test_differing_registration_refuses_without_force(self):
        self.write_settings(json.dumps(
            {"statusLine": {"type": "command", "command": "bash /elsewhere"}}))
        before = self.read_settings()
        _out, err, code = self.install()
        self.assertEqual(code, 1)
        self.assertIn("bash /elsewhere", err)
        self.assertEqual(self.read_settings(), before)

    def test_force_replaces_a_differing_registration(self):
        self.write_settings(json.dumps(
            {"statusLine": {"type": "command", "command": "bash /elsewhere"},
             "model": "opus"}))
        _out, _err, code = self.install("--force")
        self.assertEqual(code, 0)
        self.assertEqual(self.registration()["command"],
                         shipd.statusline_command(self.checkout()))
        self.assertEqual(json.loads(self.read_settings())["model"], "opus")

    def test_existing_settings_keep_their_permission_mode(self):
        # The atomic write renames a temp file over the original, and
        # ``mkstemp`` creates its file 0600 — an existing world-readable
        # settings file must not be quietly tightened by an install.
        self.write_settings(json.dumps(
            {"statusLine": {"type": "command", "command": "bash /elsewhere"}}))
        os.chmod(self.settings, 0o644)
        _out, _err, code = self.install("--force")
        self.assertEqual(code, 0)
        self.assertEqual(
            stat.S_IMODE(os.stat(self.settings).st_mode), 0o644)

    def test_identical_registration_is_idempotent(self):
        _out, _err, first = self.install()
        self.assertEqual(first, 0)
        after_first = self.read_settings()
        _out, _err, second = self.install()
        self.assertEqual(second, 0)
        self.assertEqual(self.read_settings(), after_first)

    def test_malformed_settings_are_never_overwritten(self):
        self.write_settings("{not json")
        _out, err, code = self.install()
        self.assertEqual(code, 1)
        self.assertIn(self.settings, err)
        self.assertEqual(self.read_settings(), "{not json")

    # -- the bare report ---------------------------------------------------

    def test_bare_verb_creates_nothing(self):
        out, _err, code = self.run_verb("--settings", self.settings)
        self.assertEqual(code, 0)
        self.assertFalse(os.path.exists(self.settings))
        self.assertIn(shipd.statusline_command(self.checkout()), out)

    def test_bare_verb_leaves_an_existing_file_byte_identical(self):
        self.write_settings(json.dumps(
            {"statusLine": {"type": "command", "command": "bash /elsewhere"},
             "model": "opus"}))
        before = self.read_settings()
        out, _err, code = self.run_verb("--settings", self.settings)
        self.assertEqual(code, 0)
        self.assertEqual(self.read_settings(), before)
        # The report names both the live registration and what this install
        # would register, so a mismatch is visible without mutating anything.
        self.assertIn("bash /elsewhere", out)
        self.assertIn(shipd.statusline_command(self.checkout()), out)

    # -- dispatch ----------------------------------------------------------

    def test_statusline_dispatches_in_binary_without_delegating(self):
        """Like ``list`` and ``doctor``, the verb is handled here: it writes
        the user's settings, which no engine script touches, so it is not in
        the delegating verb table and never replaces the process."""
        self.assertNotIn("statusline", shipd.VERB_TABLE)
        seen = []

        def fake_statusline(args):
            seen.append(args)
            return 0

        def no_exec(*args):
            self.fail("statusline must not exec-delegate")

        with unittest.mock.patch.object(
                shipd, "cmd_statusline", fake_statusline), \
                unittest.mock.patch.object(shipd.os, "execv", no_exec):
            code = shipd.main(["statusline", "install", "--force"])
        self.assertEqual(code, 0)
        self.assertEqual(seen, [["install", "--force"]])

    def test_bare_verb_on_malformed_settings_reports_and_exits_one(self):
        self.write_settings("{not json")
        _out, err, code = self.run_verb("--settings", self.settings)
        self.assertEqual(code, 1)
        self.assertIn(self.settings, err)
        self.assertEqual(self.read_settings(), "{not json")


class DoctorCheckTest(unittest.TestCase):
    """The individual preflight checks (shipd-cli doctor-verb), each driven
    through its injection points so no branch depends on this machine."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="shipd-doctor-test-")
        self.home = os.path.join(self.tmp, "home")
        os.makedirs(self.home)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def stub_which(self, found):
        """A ``shutil.which`` stand-in resolving only the names in ``found``
        (a mapping of name -> path)."""
        return lambda name: found.get(name)

    def make_cache(self, versions):
        """A fabricated plugin cache ``<tmp>/cache/shipd/s/<version>/``; the
        list of created version directories is returned in order."""
        base = os.path.join(self.tmp, "cache", "shipd", "s")
        made = []
        for version in versions:
            path = os.path.join(base, version)
            os.makedirs(os.path.join(path, "bin"))
            made.append(path)
        return made

    # The full preflight roster, in the order ``default_checks`` reports it.
    ALL_CHECKS = ("python", "git", "config", "pipeline", "gh", "difft",
                  "textual", "snapshot", "statusline",
                  "protection", "automerge", "copilot-secret")

    def probed_check_names(self, root):
        """The check names ``default_checks`` reports, with every check — and
        the GitHub context resolution the last three share — stubbed out, so
        ordering is asserted without touching PATH, the network, or ``gh``."""
        patchers = [unittest.mock.patch.object(
            shipd, "gh_context", lambda **kw: {"skip": "stubbed"})]
        for check in self.ALL_CHECKS:
            patchers.append(unittest.mock.patch.object(
                shipd, "check_%s" % check.replace("-", "_"),
                lambda *a, _n=check, **kw: ("ok", _n, "")))
        with contextlib.ExitStack() as stack:
            for patcher in patchers:
                stack.enter_context(patcher)
            return [name for _level, name, _detail
                    in shipd.default_checks(root)]

    # -- python ------------------------------------------------------------

    def test_python_at_the_floor_is_ok(self):
        level, name, detail = shipd.check_python((3, 9, 0, "final", 0))
        self.assertEqual((level, name), ("ok", "python"))
        self.assertIn("3.9", detail)

    def test_python_below_the_floor_fails(self):
        level, name, detail = shipd.check_python((3, 8, 18, "final", 0))
        self.assertEqual((level, name), ("fail", "python"))
        self.assertIn("3.8.18", detail)
        self.assertIn("3.9", detail)

    # -- git ---------------------------------------------------------------

    def test_git_on_path_is_ok(self):
        level, name, detail = shipd.check_git(
            which=self.stub_which({"git": "/usr/bin/git"}))
        self.assertEqual((level, name), ("ok", "git"))
        self.assertIn("/usr/bin/git", detail)

    def test_git_missing_fails_with_a_hint(self):
        level, name, detail = shipd.check_git(which=self.stub_which({}))
        self.assertEqual((level, name), ("fail", "git"))
        self.assertIn("PATH", detail)
        self.assertIn("install", detail.lower())

    # -- config ------------------------------------------------------------

    def config_check(self, root):
        """``check_config`` with ``HOME`` pointed at the throwaway home, so the
        outermost config layer can never be the real user's."""
        env = dict(os.environ)
        env["HOME"] = self.home
        with unittest.mock.patch.dict(os.environ, env, clear=True):
            return shipd.check_config(root)

    def test_config_with_a_content_dir_is_ok(self):
        root = os.path.join(self.tmp, "repo")
        os.makedirs(os.path.join(root, ".shipd", "planned"))
        level, name, detail = self.config_check(root)
        self.assertEqual((level, name), ("ok", "config"))
        self.assertIn(".shipd", detail)

    def test_config_without_a_content_dir_is_ok_with_a_note(self):
        root = os.path.join(self.tmp, "bare")
        os.makedirs(root)
        level, name, detail = self.config_check(root)
        self.assertEqual((level, name), ("ok", "config"))
        self.assertIn("/s:plan", detail)

    def test_unreadable_config_fails_naming_the_file(self):
        root = os.path.join(self.tmp, "broken")
        os.makedirs(root)
        path = os.path.join(root, ".shipd-config.json")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("{not json")
        level, name, detail = self.config_check(root)
        self.assertEqual((level, name), ("fail", "config"))
        self.assertIn(path, detail)

    def test_invalid_pr_mode_fails_carrying_the_resolver_error(self):
        # The `config` check also validates `pr-mode` (shipd-cli
        # doctor-pr-mode-check spec), reporting the accessor's own error line.
        root, path = self.repo_with_config("badmode", {"pr-mode": "always"})
        level, name, detail = self.config_check(root)
        self.assertEqual((level, name), ("fail", "config"))
        self.assertIn("pr-mode", detail)
        self.assertIn("auto", detail)
        self.assertIn("draft", detail)
        self.assertIn(path, detail)

    def test_declared_draft_pr_mode_is_ok_with_the_usual_detail(self):
        root, _path = self.repo_with_config("draftmode", {"pr-mode": "draft"})
        os.makedirs(os.path.join(root, ".shipd", "planned"))
        level, name, detail = self.config_check(root)
        self.assertEqual((level, name), ("ok", "config"))
        self.assertIn("content directory", detail)
        self.assertIn(".shipd", detail)

    def test_undeclared_pr_mode_leaves_the_check_unchanged(self):
        root = os.path.join(self.tmp, "nomode")
        os.makedirs(os.path.join(root, ".shipd", "planned"))
        self.assertEqual(
            self.config_check(root),
            ("ok", "config",
             "content directory %s" % os.path.join(root, ".shipd")))

    # -- pipeline ----------------------------------------------------------

    def pipeline_check(self, root, **kwargs):
        """``check_pipeline`` with ``HOME`` pointed at the throwaway home, so
        the outermost config layer can never be the real user's."""
        env = dict(os.environ)
        env["HOME"] = self.home
        with unittest.mock.patch.dict(os.environ, env, clear=True):
            return shipd.check_pipeline(root, **kwargs)

    def repo_with_config(self, name, config):
        """A throwaway repo root whose ``.shipd-config.json`` holds ``config``;
        the config path is returned alongside the root."""
        root = os.path.join(self.tmp, name)
        os.makedirs(root)
        path = os.path.join(root, ".shipd-config.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(config, fh)
        return root, path

    def test_undeclared_pipeline_is_ok_from_the_default(self):
        root = os.path.join(self.tmp, "nopipeline")
        os.makedirs(root)
        level, name, detail = self.pipeline_check(root)
        self.assertEqual((level, name), ("ok", "pipeline"))
        self.assertIn("default", detail)

    def test_declared_pipeline_reports_no_pydantic_check(self):
        # The validator is stdlib-only, so a repo declaring a pipeline never
        # surfaces a `pydantic` check — the preflight's own roster carries no
        # such name (shipd-cli doctor-verb). Checked by name rather than by
        # scanning every detail for the substring "pydantic": an unrelated
        # check's detail may legitimately embed an absolute path, and that
        # path is free to contain any substring, this worktree's own
        # directory name included.
        root, _path = self.repo_with_config(
            "declared-pipeline-doctor",
            {"autonomous-pipeline": [{"stage": "plan"}]})
        env = dict(os.environ)
        env["HOME"] = self.home
        with unittest.mock.patch.object(
                shipd, "gh_context", lambda **kw: {"skip": "stubbed"}), \
                unittest.mock.patch.dict(os.environ, env, clear=True):
            results = shipd.default_checks(root)
        names = [name for _level, name, _detail in results]
        self.assertNotIn("pydantic", names)
        pipeline_level, _name, pipeline_detail = next(
            r for r in results if r[1] == "pipeline")
        self.assertEqual(pipeline_level, "ok")
        self.assertNotIn("pydantic", pipeline_detail)

    def test_resolved_pipeline_names_its_entry_count_and_provenance(self):
        level, name, detail = self.pipeline_check(
            self.tmp,
            resolve=lambda root: ([{"stage": "plan"}, {"stage": "build"}],
                                  "preset:eco (/tmp/.shipd-config.json)"))
        self.assertEqual((level, name), ("ok", "pipeline"))
        self.assertIn("2", detail)
        self.assertIn("preset:eco (/tmp/.shipd-config.json)", detail)

    def test_unresolvable_pipeline_carries_the_resolver_error_verbatim(self):
        shipd._load_engine()

        def boom(root):
            raise shipd.sc.ConfigError("boom")
        level, name, detail = self.pipeline_check(self.tmp, resolve=boom)
        self.assertEqual((level, name), ("fail", "pipeline"))
        self.assertEqual(detail, "boom")

    # -- gh ----------------------------------------------------------------

    def test_gh_authenticated_is_ok(self):
        level, name, detail = shipd.check_gh(
            which=self.stub_which({"gh": "/opt/bin/gh"}),
            gh_status=lambda: 0)
        self.assertEqual((level, name), ("ok", "gh"))
        self.assertIn("/opt/bin/gh", detail)

    def test_gh_absent_only_warns(self):
        level, name, detail = shipd.check_gh(
            which=self.stub_which({}),
            gh_status=lambda: self.fail("gh must not be probed when absent"))
        self.assertEqual((level, name), ("warn", "gh"))
        self.assertIn("PATH", detail)

    def test_gh_unauthenticated_only_warns(self):
        level, name, detail = shipd.check_gh(
            which=self.stub_which({"gh": "/opt/bin/gh"}),
            gh_status=lambda: 1)
        self.assertEqual((level, name), ("warn", "gh"))
        self.assertIn("gh auth login", detail)

    # -- difft -------------------------------------------------------------

    def test_difft_on_path_is_ok(self):
        level, name, detail = shipd.check_difft(
            which=self.stub_which({"difft": "/opt/bin/difft"}))
        self.assertEqual((level, name), ("ok", "difft"))
        self.assertIn("/opt/bin/difft", detail)

    def test_difft_missing_warns_naming_the_degradation_and_remedy(self):
        level, name, detail = shipd.check_difft(which=self.stub_which({}))
        self.assertEqual((level, name), ("warn", "difft"))
        self.assertIn("text engine", detail)
        self.assertIn("semdiff doctor --fix", detail)

    def test_default_checks_probe_difft_after_gh(self):
        names = self.probed_check_names(self.tmp)
        self.assertEqual(names.index("difft"), names.index("gh") + 1)

    # -- the pip install hint ----------------------------------------------
    #
    # A vendored per-repo install has no checkout to ``-r`` from, so the hint
    # names the pinned specifier wherever no ``requirements.txt`` sits at the
    # probed root. The pin mirrors ``requirements.txt``.

    TEXTUAL_HINT = "pip install 'textual>=8.2.8,<9'"
    REQUIREMENTS_HINT = "pip install -r requirements.txt"

    # On a PEP 668 externally managed interpreter both forms gain the two
    # flags that make the printed command runnable by the interpreter that
    # printed it. The probe is injected in every test below — never read off
    # the machine running the suite — so both branches are exercised whether
    # or not that machine's python3 is externally managed.
    MANAGED = staticmethod(lambda: True)
    UNMANAGED = staticmethod(lambda: False)
    OVERRIDE_FLAGS = "--user --break-system-packages"
    MANAGED_REQUIREMENTS_HINT = (
        "pip install --user --break-system-packages -r requirements.txt")
    MANAGED_TEXTUAL_HINT = (
        "pip install --user --break-system-packages 'textual>=8.2.8,<9'")

    def undeclared_repo(self, name="undeclared"):
        """A throwaway repo root whose layered config declares no pipeline."""
        root = os.path.join(self.tmp, name)
        os.makedirs(root, exist_ok=True)
        return root

    def with_requirements(self, root):
        """Plant a ``requirements.txt`` at ``root`` — the checkout case."""
        with open(os.path.join(root, "requirements.txt"), "w",
                  encoding="utf-8") as fh:
            fh.write("textual>=8.2.8,<9\n")
        return root

    # -- the externally-managed probe --------------------------------------

    def test_probe_reports_managed_when_the_marker_sits_in_the_stdlib(self):
        stdlib = os.path.join(self.tmp, "managed-stdlib")
        os.makedirs(stdlib, exist_ok=True)
        with open(os.path.join(stdlib, "EXTERNALLY-MANAGED"), "w",
                  encoding="utf-8") as fh:
            fh.write("[externally-managed]\n")
        self.assertTrue(shipd.externally_managed(stdlib=stdlib))

    def test_probe_reports_unmanaged_without_the_marker(self):
        stdlib = os.path.join(self.tmp, "plain-stdlib")
        os.makedirs(stdlib, exist_ok=True)
        self.assertFalse(shipd.externally_managed(stdlib=stdlib))

    # -- textual -----------------------------------------------------------

    def test_textual_importable_is_ok(self):
        level, name, _detail = shipd.check_textual(
            self.tmp, find_spec=lambda name: object())
        self.assertEqual((level, name), ("ok", "textual"))

    def test_textual_missing_warns_about_the_board_only(self):
        root = self.with_requirements(self.undeclared_repo("textual-checkout"))
        level, name, detail = shipd.check_textual(
            root, find_spec=lambda name: None, managed=self.UNMANAGED)
        self.assertEqual((level, name), ("warn", "textual"))
        self.assertIn("board", detail)
        self.assertIn(self.REQUIREMENTS_HINT, detail)
        self.assertNotIn(self.OVERRIDE_FLAGS, detail)

    def test_textual_probe_failure_warns(self):
        def boom(name):
            raise ValueError("no parent package")
        level, name, _detail = shipd.check_textual(self.tmp, find_spec=boom)
        self.assertEqual((level, name), ("warn", "textual"))

    def test_textual_hint_pins_the_specifier_without_a_requirements_file(self):
        root = self.undeclared_repo("textual-vendored")
        _level, _name, detail = shipd.check_textual(
            root, find_spec=lambda name: None, managed=self.UNMANAGED)
        self.assertIn(self.TEXTUAL_HINT, detail)
        self.assertNotIn("-r requirements.txt", detail)
        self.assertNotIn(self.OVERRIDE_FLAGS, detail)

    def test_managed_interpreter_flags_the_textual_requirements_hint(self):
        root = self.with_requirements(self.undeclared_repo("textual-managed"))
        level, name, detail = shipd.check_textual(
            root, find_spec=lambda name: None, managed=self.MANAGED)
        self.assertEqual((level, name), ("warn", "textual"))
        self.assertIn(self.MANAGED_REQUIREMENTS_HINT, detail)

    def test_managed_interpreter_flags_the_textual_pinned_hint(self):
        root = self.undeclared_repo("textual-managed-vendored")
        _level, _name, detail = shipd.check_textual(
            root, find_spec=lambda name: None, managed=self.MANAGED)
        self.assertIn(self.MANAGED_TEXTUAL_HINT, detail)
        self.assertNotIn("-r requirements.txt", detail)

    def test_default_checks_run_in_the_documented_order(self):
        self.assertEqual(self.probed_check_names(self.tmp),
                         ["python", "git", "config", "pipeline", "gh", "difft",
                          "textual", "snapshot", "statusline",
                          "protection", "automerge", "copilot-secret"])

    # -- statusline --------------------------------------------------------

    def settings_with(self, text):
        """A settings file under the throwaway temp root holding ``text`` —
        the real ``~/.claude/settings.json`` is never touched."""
        path = os.path.join(self.tmp, "claude", "settings.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    def test_absent_settings_file_warns_with_the_install_remedy(self):
        missing = os.path.join(self.tmp, "nowhere", "settings.json")
        level, name, detail = shipd.check_statusline(missing)
        self.assertEqual((level, name), ("warn", "statusline"))
        self.assertIn("shipd statusline install", detail)

    def test_settings_without_a_statusline_key_warns(self):
        path = self.settings_with(json.dumps({"model": "opus"}))
        level, name, detail = shipd.check_statusline(path)
        self.assertEqual((level, name), ("warn", "statusline"))
        self.assertIn("shipd statusline install", detail)

    def test_registered_statusline_is_ok_naming_its_command(self):
        path = self.settings_with(json.dumps(
            {"statusLine": {"type": "command",
                            "command": "bash /plugins/s/statusline.sh"}}))
        level, name, detail = shipd.check_statusline(path)
        self.assertEqual((level, name), ("ok", "statusline"))
        self.assertIn("bash /plugins/s/statusline.sh", detail)

    def test_unparseable_settings_only_warn(self):
        path = self.settings_with("{not json")
        level, name, detail = shipd.check_statusline(path)
        self.assertEqual((level, name), ("warn", "statusline"))
        self.assertIn(path, detail)

    def test_statusline_check_never_writes(self):
        path = self.settings_with(json.dumps({"model": "opus"}))
        before = os.stat(path)
        shipd.check_statusline(path)
        after = os.stat(path)
        self.assertEqual((before.st_size, before.st_mtime),
                         (after.st_size, after.st_mtime))

    def test_default_checks_probe_statusline_after_snapshot(self):
        names = self.probed_check_names(self.tmp)
        self.assertEqual(names.index("statusline"),
                         names.index("snapshot") + 1)

    # -- snapshot ----------------------------------------------------------

    def test_newest_snapshot_is_ok(self):
        old, new = self.make_cache(["0.6.9", "0.6.10"])
        level, name, detail = shipd.check_snapshot(new)
        self.assertEqual((level, name), ("ok", "snapshot"))
        self.assertIn("0.6.10", detail)
        self.assertNotIn("0.6.9", detail)
        self.assertTrue(os.path.isdir(old))

    def test_stale_snapshot_warns_naming_the_newer_version(self):
        old, _new = self.make_cache(["0.6.9", "0.6.10"])
        level, name, detail = shipd.check_snapshot(old)
        self.assertEqual((level, name), ("warn", "snapshot"))
        self.assertIn("0.6.9", detail)
        self.assertIn("0.6.10", detail)

    def test_stale_snapshot_names_both_ways_to_get_later_versions(self):
        # The durable fix is marketplace auto-update; the manual command is the
        # always-works fallback, so a stale snapshot names both.
        old, _new = self.make_cache(["0.6.9", "0.6.10"])
        _level, _name, detail = shipd.check_snapshot(old)
        self.assertIn("auto-update", detail)
        self.assertIn("/plugin", detail)
        self.assertIn("claude plugin update s@shipd", detail)

    def test_checkout_reports_dev_mode(self):
        plugin_root = os.path.join(self.tmp, "repo", "plugins", "s")
        os.makedirs(os.path.join(plugin_root, "bin"))
        level, name, detail = shipd.check_snapshot(plugin_root)
        self.assertEqual((level, name), ("ok", "snapshot"))
        self.assertIn("dev mode", detail)

    # -- the GitHub-side checks (shipd-cli doctor-github-checks) -----------
    #
    # ``protection``, ``automerge``, and ``copilot-secret`` all probe GitHub
    # through one injected runner, so every branch below is driven from canned
    # ``gh`` responses — the suite never resolves a remote, never
    # authenticates,
    # and never reaches the network.

    NWO = "acme/widget"
    REPO_VIEW = "repo view --json nameWithOwner -q .nameWithOwner"
    HTTP_403 = (1, "", "gh: Forbidden (HTTP 403)\n")
    HTTP_404 = (1, "", "gh: Not Found (HTTP 404)\n")
    OFFLINE = (1, "", "dial tcp: lookup api.github.com: no such host\n")

    def gh_stub(self, responses):
        """A ``_gh_run`` stand-in answering from ``responses`` (the joined
        argument string -> ``(returncode, stdout, stderr)``). Every invocation
        is recorded on ``self.gh_calls``; an unexpected one fails the test."""
        self.gh_calls = []

        def run(args):
            key = " ".join(args)
            self.gh_calls.append(key)
            if key not in responses:
                self.fail("unexpected gh invocation: %s" % key)
            return responses[key]
        return run

    def repo_payload(self, **overrides):
        """The ``gh api repos/<nwo>`` payload the context is resolved from."""
        payload = {"default_branch": "main", "allow_auto_merge": True,
                   "permissions": {"admin": True}}
        payload.update(overrides)
        return payload

    def gh_responses(self, repo=None, probes=None):
        """The two context-resolution responses plus ``probes`` — a mapping of
        path suffix under ``repos/<nwo>/`` to a canned response."""
        responses = {self.REPO_VIEW: (0, self.NWO + "\n", "")}
        if repo is not None:
            responses["api repos/%s" % self.NWO] = (0, json.dumps(repo), "")
        for suffix, response in (probes or {}).items():
            responses["api repos/%s/%s" % (self.NWO, suffix)] = response
        return responses

    def ok_json(self, payload):
        return (0, json.dumps(payload), "")

    def resolve_context(self, responses, which=None, gh_status=None):
        """``(context, run)`` — the once-resolved repository context and the
        shared stub runner the three checks go on probing through."""
        run = self.gh_stub(responses)
        context = shipd.gh_context(
            which=self.stub_which({"gh": "/opt/bin/gh"})
            if which is None else which,
            gh_status=gh_status or (lambda: 0),
            run=run)
        return context, run

    def repo_with_gate(self, name="gated"):
        """A throwaway root carrying the installed copilot gate workflow."""
        root = os.path.join(self.tmp, name)
        path = os.path.join(root, ".github", "workflows",
                            "copilot-review-gate.yml")
        os.makedirs(os.path.dirname(path))
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("name: copilot review gate\n")
        return root

    def automerge_check(self, root, context):
        """``check_automerge`` with ``HOME`` pointed at the throwaway home, so
        the outermost ``pr-mode`` layer can never be the real user's."""
        env = dict(os.environ)
        env["HOME"] = self.home
        with unittest.mock.patch.dict(os.environ, env, clear=True):
            return shipd.check_automerge(root, context)

    # -- context resolution -------------------------------------------------

    def test_no_github_repository_skips_all_three(self):
        root = self.repo_with_gate("nogithub")
        context, _run = self.resolve_context(
            {self.REPO_VIEW: (1, "", "none of the git remotes point to a "
                                     "known GitHub host\n")})
        results = [shipd.check_protection(context),
                   self.automerge_check(root, context),
                   shipd.check_copilot_secret(root, context)]
        self.assertEqual([level for level, _n, _d in results],
                         ["ok", "ok", "ok"])
        self.assertEqual([name for _l, name, _d in results],
                         ["protection", "automerge", "copilot-secret"])
        for _level, name, detail in results:
            self.assertIn("skipped", detail, name)
            self.assertIn("GitHub repository", detail, name)

    def test_gh_absent_skips_without_probing(self):
        context, _run = self.resolve_context({}, which=self.stub_which({}))
        self.assertEqual(self.gh_calls, [])
        level, name, detail = shipd.check_protection(context)
        self.assertEqual((level, name), ("ok", "protection"))
        self.assertIn("skipped", detail)
        self.assertIn("gh", detail)

    def test_unauthenticated_gh_skips_without_probing(self):
        context, _run = self.resolve_context({}, gh_status=lambda: 1)
        self.assertEqual(self.gh_calls, [])
        level, name, detail = shipd.check_automerge(self.tmp, context)
        self.assertEqual((level, name), ("ok", "automerge"))
        self.assertIn("skipped", detail)
        self.assertIn("authenticated", detail)

    def test_unreadable_repository_payload_skips(self):
        context, _run = self.resolve_context(
            {self.REPO_VIEW: (0, self.NWO + "\n", ""),
             "api repos/%s" % self.NWO: self.OFFLINE})
        level, name, detail = shipd.check_protection(context)
        self.assertEqual((level, name), ("ok", "protection"))
        self.assertIn("skipped", detail)

    def test_the_repository_payload_is_fetched_once(self):
        root = self.repo_with_gate("once")
        responses = self.gh_responses(
            self.repo_payload(),
            {"branches/main/protection":
                self.ok_json({"required_status_checks":
                              {"contexts": ["ci", "semantic-review"]}}),
             "actions/secrets":
                self.ok_json({"secrets": [{"name": "COPILOT_GITHUB_TOKEN"}]})})
        context, run = self.resolve_context(responses)
        shipd.check_protection(context, run=run)
        self.automerge_check(root, context)
        shipd.check_copilot_secret(root, context, run=run)
        self.assertEqual(self.gh_calls.count("api repos/%s" % self.NWO), 1)

    def test_the_github_probes_never_mutate(self):
        root = self.repo_with_gate("readonly")
        responses = self.gh_responses(
            self.repo_payload(),
            {"branches/main/protection": self.HTTP_404,
             "branches/main": self.ok_json({"name": "main",
                                            "protected": False}),
             "actions/secrets": self.ok_json({"secrets": []})})
        context, run = self.resolve_context(responses)
        shipd.check_protection(context, run=run)
        self.automerge_check(root, context)
        shipd.check_copilot_secret(root, context, run=run)
        for call in self.gh_calls:
            self.assertNotIn("-X", call)
            self.assertTrue(call.startswith("api ") or call == self.REPO_VIEW,
                            call)

    # -- protection ---------------------------------------------------------

    def protection(self, protection_response, repo=None, branch=None):
        probes = {"branches/main/protection": protection_response}
        if branch is not None:
            probes["branches/main"] = branch
        context, run = self.resolve_context(
            self.gh_responses(repo or self.repo_payload(), probes))
        return shipd.check_protection(context, run=run)

    def test_required_semantic_review_context_is_ok(self):
        level, name, detail = self.protection(self.ok_json(
            {"required_status_checks": {"contexts": ["ci",
                                                     "semantic-review"]}}))
        self.assertEqual((level, name), ("ok", "protection"))
        self.assertIn("semantic-review", detail)
        self.assertIn("main", detail)

    def test_unprotected_default_branch_warns(self):
        level, name, detail = self.protection(self.HTTP_404)
        self.assertEqual((level, name), ("warn", "protection"))
        self.assertIn("main", detail)
        self.assertIn("not protected", detail)
        self.assertIn("semantic-review", detail)

    def test_protection_missing_the_semantic_review_context_warns(self):
        level, name, detail = self.protection(self.ok_json(
            {"required_status_checks": {"contexts": ["ci"]}}))
        self.assertEqual((level, name), ("warn", "protection"))
        self.assertIn("semantic-review", detail)
        # The contexts-append remedy needs both halves of the endpoint path,
        # so every `protection` warning names the repository and the branch.
        self.assertIn(self.NWO, detail)
        self.assertIn("main", detail)

    def test_every_protection_warning_names_the_repository_and_branch(self):
        for probe in (self.HTTP_404,
                      self.ok_json({"required_status_checks":
                                    {"contexts": ["ci"]}}),
                      self.ok_json({})):
            level, _name, detail = self.protection(probe)
            self.assertEqual(level, "warn", detail)
            self.assertIn(self.NWO, detail)
            self.assertIn("`main`", detail)

    def test_non_admin_falls_back_to_the_protected_boolean(self):
        level, name, detail = self.protection(
            self.HTTP_403,
            repo=self.repo_payload(permissions={"admin": False}),
            branch=self.ok_json({"name": "main", "protected": True}))
        self.assertEqual((level, name), ("ok", "protection"))
        self.assertIn("could not be verified", detail)
        self.assertIn("admin", detail)

    def test_the_protected_fallback_asks_for_the_one_branch(self):
        """The fallback reads ``repos/<nwo>/branches/<branch>``, never the
        paginated branch listing — a repository with more than a page of
        branches would hide the default branch behind a page boundary."""
        self.protection(
            self.HTTP_403,
            repo=self.repo_payload(permissions={"admin": False}),
            branch=self.ok_json({"name": "main", "protected": True}))
        self.assertIn("api repos/%s/branches/main" % self.NWO, self.gh_calls)
        self.assertNotIn("api repos/%s/branches" % self.NWO, self.gh_calls)

    def test_non_admin_unprotected_branch_warns(self):
        level, name, detail = self.protection(
            self.HTTP_403,
            repo=self.repo_payload(permissions={"admin": False}),
            branch=self.ok_json({"name": "main", "protected": False}))
        self.assertEqual((level, name), ("warn", "protection"))
        self.assertIn("not protected", detail)

    def test_a_branch_payload_without_the_boolean_is_unverifiable(self):
        level, name, detail = self.protection(
            self.HTTP_403,
            repo=self.repo_payload(permissions={"admin": False}),
            branch=self.ok_json({"name": "main"}))
        self.assertEqual((level, name), ("ok", "protection"))
        self.assertIn("could not be verified", detail)

    def test_missing_admin_permission_is_named_in_the_warn_detail(self):
        level, name, detail = self.protection(
            self.HTTP_404,
            repo=self.repo_payload(permissions={"admin": False}))
        self.assertEqual((level, name), ("warn", "protection"))
        self.assertIn("lacks admin permission", detail)

    def test_admin_token_leaves_the_warn_detail_without_that_note(self):
        _level, _name, detail = self.protection(self.HTTP_404)
        self.assertNotIn("lacks admin permission", detail)

    def test_unreadable_branch_payload_is_ok_unverifiable(self):
        level, name, detail = self.protection(
            self.HTTP_403,
            repo=self.repo_payload(permissions={"admin": False}),
            branch=self.HTTP_403)
        self.assertEqual((level, name), ("ok", "protection"))
        self.assertIn("could not be verified", detail)

    def test_protection_probe_error_is_ok_unverifiable(self):
        level, name, detail = self.protection(self.OFFLINE)
        self.assertEqual((level, name), ("ok", "protection"))
        self.assertIn("could not be verified", detail)

    def test_protection_without_required_status_checks_warns(self):
        """A readable 200 payload carrying no ``required_status_checks`` is not
        an unverifiable read — it says the branch requires *no* status checks,
        so nothing requires the gate's status and the verdict is ignored."""
        level, name, detail = self.protection(self.ok_json({}))
        self.assertEqual((level, name), ("warn", "protection"), detail)
        self.assertIn("requires no status checks at all", detail)
        self.assertIn("semantic-review", detail)
        self.assertNotIn("could not be verified", detail)
        # The skill routes its remedies off the other two warnings'
        # discriminators, and neither remedy fits this one: the append POST
        # 404s, and the whole-protection PUT would clobber the branch's
        # existing settings.
        self.assertNotIn("is not protected", detail)
        self.assertNotIn("does not require the `semantic-review` status "
                         "context", detail)

    def test_malformed_required_status_checks_is_ok_unverifiable(self):
        """Required status checks *are* configured, but the payload's shape is
        not one this reads. That is unknown, not definitive, so it degrades to
        unverifiable silence rather than joining the warning above."""
        for required in ({"contexts": "ci"}, {}, "ci", []):
            level, name, detail = self.protection(self.ok_json(
                {"required_status_checks": required}))
            self.assertEqual((level, name), ("ok", "protection"), detail)
            self.assertIn("could not be verified", detail)
            self.assertNotIn("requires no status checks at all", detail)

    def test_the_no_status_checks_warning_carries_the_admin_note(self):
        _level, _name, detail = self.protection(
            self.ok_json({}),
            repo=self.repo_payload(permissions={"admin": False}))
        self.assertIn("lacks admin permission", detail)

    # -- automerge ----------------------------------------------------------

    def automerge(self, root, **repo_overrides):
        context, _run = self.resolve_context(
            self.gh_responses(self.repo_payload(**repo_overrides)))
        return self.automerge_check(root, context)

    def test_enabled_auto_merge_is_ok(self):
        root = os.path.join(self.tmp, "am-ok")
        os.makedirs(root)
        level, name, detail = self.automerge(root)
        self.assertEqual((level, name), ("ok", "automerge"))
        self.assertIn(self.NWO, detail)

    def test_disabled_auto_merge_warns_under_auto_pr_mode(self):
        root = os.path.join(self.tmp, "am-warn")
        os.makedirs(root)
        level, name, detail = self.automerge(root, allow_auto_merge=False)
        self.assertEqual((level, name), ("warn", "automerge"))
        self.assertIn("auto-merge", detail)

    def test_draft_pr_mode_waives_the_automerge_warning(self):
        root, _path = self.repo_with_config("am-draft", {"pr-mode": "draft"})
        level, name, detail = self.automerge(root, allow_auto_merge=False)
        self.assertEqual((level, name), ("ok", "automerge"))
        self.assertIn("draft", detail)

    def test_absent_allow_auto_merge_field_is_ok_unverifiable(self):
        root = os.path.join(self.tmp, "am-absent")
        os.makedirs(root)
        context, _run = self.resolve_context(self.gh_responses(
            {"default_branch": "main", "permissions": {"admin": True}}))
        level, name, detail = self.automerge_check(root, context)
        self.assertEqual((level, name), ("ok", "automerge"))
        self.assertIn("could not be verified", detail)

    def test_automerge_warn_names_a_missing_admin_permission(self):
        root = os.path.join(self.tmp, "am-noadmin")
        os.makedirs(root)
        level, name, detail = self.automerge(
            root, allow_auto_merge=False, permissions={"admin": False})
        self.assertEqual((level, name), ("warn", "automerge"))
        self.assertIn("lacks admin permission", detail)

    # -- copilot-secret -----------------------------------------------------

    def copilot_secret(self, root, secrets_response=None):
        probes = ({} if secrets_response is None
                  else {"actions/secrets": secrets_response})
        context, run = self.resolve_context(
            self.gh_responses(self.repo_payload(), probes))
        return shipd.check_copilot_secret(root, context, run=run)

    def test_installed_gate_without_the_secret_warns_fail_open(self):
        root = self.repo_with_gate("gate-nosecret")
        level, name, detail = self.copilot_secret(
            root, self.ok_json({"total_count": 0, "secrets": []}))
        self.assertEqual((level, name), ("warn", "copilot-secret"))
        self.assertIn("COPILOT_GITHUB_TOKEN", detail)
        self.assertIn("fail-open", detail)
        self.assertIn("poll", detail)

    def test_installed_gate_with_the_secret_is_ok(self):
        root = self.repo_with_gate("gate-secret")
        level, name, detail = self.copilot_secret(root, self.ok_json(
            {"total_count": 1,
             "secrets": [{"name": "COPILOT_GITHUB_TOKEN"}]}))
        self.assertEqual((level, name), ("ok", "copilot-secret"))
        self.assertIn("COPILOT_GITHUB_TOKEN", detail)

    def test_absent_gate_workflow_skips_the_secret_check(self):
        root = os.path.join(self.tmp, "nogate")
        os.makedirs(root)
        level, name, detail = self.copilot_secret(root)
        self.assertEqual((level, name), ("ok", "copilot-secret"))
        self.assertIn("skipped", detail)
        self.assertIn("copilot-review-gate.yml", detail)

    def test_absent_gate_workflow_never_probes_the_secrets(self):
        root = os.path.join(self.tmp, "nogate-quiet")
        os.makedirs(root)
        self.copilot_secret(root)
        self.assertNotIn("api repos/%s/actions/secrets" % self.NWO,
                         self.gh_calls)

    def test_denied_secrets_listing_is_ok_unverifiable(self):
        root = self.repo_with_gate("gate-denied")
        level, name, detail = self.copilot_secret(root, self.HTTP_403)
        self.assertEqual((level, name), ("ok", "copilot-secret"))
        self.assertIn("could not be verified", detail)

    def test_secret_warn_names_a_missing_admin_permission(self):
        root = self.repo_with_gate("gate-noadmin")
        context, run = self.resolve_context(self.gh_responses(
            self.repo_payload(permissions={"admin": False}),
            {"actions/secrets": self.ok_json({"secrets": []})}))
        level, name, detail = shipd.check_copilot_secret(root, context,
                                                         run=run)
        self.assertEqual((level, name), ("warn", "copilot-secret"))
        self.assertIn("lacks admin permission", detail)

    # -- a gh that never answers --------------------------------------------

    def timing_out_subprocess(self):
        """A ``subprocess.run`` stand-in for a ``gh`` that never returns. It
        asserts the call was bounded before raising, so the seam cannot lose
        its timeout and still pass. Nothing here sleeps or runs a real gh."""
        def run(cmd, **kwargs):
            self.assertEqual(kwargs.get("timeout"), shipd.GH_TIMEOUT, cmd)
            raise subprocess.TimeoutExpired(cmd=cmd,
                                            timeout=shipd.GH_TIMEOUT)
        return run

    def test_a_timed_out_gh_degrades_instead_of_hanging(self):
        """A hung ``gh`` reaches the checks as an ordinary probe failure: both
        subprocess seams are bounded, the context resolves to a skip, and all
        three checks still report ``ok`` rather than stalling the preflight."""
        root = self.repo_with_gate("timed-out")
        with unittest.mock.patch.object(shipd.subprocess, "run",
                                        self.timing_out_subprocess()):
            self.assertEqual(shipd._gh_auth_status(), 1)
            code, out, err = shipd._gh_run(["repo", "view"])
            self.assertEqual((code, out), (1, ""))
            self.assertIn("timed out", err)
            context = shipd.gh_context(
                which=self.stub_which({"gh": "/opt/bin/gh"}),
                gh_status=lambda: 0)
        self.assertIn("skip", context)
        results = [shipd.check_protection(context),
                   self.automerge_check(root, context),
                   shipd.check_copilot_secret(root, context)]
        self.assertEqual([level for level, _n, _d in results], ["ok"] * 3)
        for _level, name, detail in results:
            self.assertIn("skipped", detail, name)

    def test_a_timed_out_probe_is_unverifiable_not_a_failure(self):
        """The same bound applies once the context *has* resolved: a per-check
        probe that times out reads as no response, so the check degrades to an
        unverifiable ``ok`` exactly like any other unreachable probe."""
        root = self.repo_with_gate("timed-out-probe")
        context, _run = self.resolve_context(
            self.gh_responses(self.repo_payload(allow_auto_merge=None)))
        with unittest.mock.patch.object(shipd.subprocess, "run",
                                        self.timing_out_subprocess()):
            results = [shipd.check_protection(context, run=shipd._gh_run),
                       self.automerge_check(root, context),
                       shipd.check_copilot_secret(root, context,
                                                  run=shipd._gh_run)]
        self.assertEqual([level for level, _n, _d in results], ["ok"] * 3)
        for _level, name, detail in results:
            self.assertIn("could not be verified", detail, name)
        _lines, exit_code = shipd.doctor_report(results)
        self.assertEqual(exit_code, 0)

    # -- placement ----------------------------------------------------------

    def test_the_github_checks_report_after_statusline(self):
        names = self.probed_check_names(self.tmp)
        self.assertEqual(names[names.index("statusline") + 1:],
                         ["protection", "automerge", "copilot-secret"])

    def test_the_github_checks_never_fail_the_preflight(self):
        root = self.repo_with_gate("never-fail")
        responses = self.gh_responses(
            self.repo_payload(allow_auto_merge=False,
                              permissions={"admin": False}),
            {"branches/main/protection": self.HTTP_404,
             "actions/secrets": self.ok_json({"secrets": []})})
        context, run = self.resolve_context(responses)
        results = [shipd.check_protection(context, run=run),
                   self.automerge_check(root, context),
                   shipd.check_copilot_secret(root, context, run=run)]
        self.assertEqual([level for level, _n, _d in results],
                         ["warn", "warn", "warn"])
        _lines, code = shipd.doctor_report(results)
        self.assertEqual(code, 0)


class DoctorReportTest(unittest.TestCase):
    """The composed report: line shape, closing line, and exit contract."""

    def report(self, results):
        return shipd.doctor_report(results)

    def test_line_shape_is_level_name_detail(self):
        lines, _code = self.report([("ok", "git", "found at /usr/bin/git")])
        self.assertEqual(lines[0], "ok git — found at /usr/bin/git")

    def test_all_ok_closes_with_ok_and_exits_zero(self):
        lines, code = self.report([("ok", "python", "3.13.0"),
                                   ("ok", "git", "found")])
        self.assertEqual(code, 0)
        self.assertEqual(lines[-1], "doctor: ok")
        for line in lines[:-1]:
            self.assertTrue(line.startswith("ok "), line)

    def test_warnings_alone_do_not_affect_the_exit_code(self):
        lines, code = self.report([("ok", "python", "3.13.0"),
                                   ("warn", "gh", "not on PATH"),
                                   ("warn", "textual", "not importable")])
        self.assertEqual(code, 0)
        self.assertEqual(lines[-1], "doctor: 2 problem(s)")

    def test_any_failure_exits_one(self):
        lines, code = self.report([("fail", "git", "not on PATH"),
                                   ("ok", "python", "3.13.0")])
        self.assertEqual(code, 1)
        self.assertEqual(lines[-1], "doctor: 1 problem(s)")

    def test_failures_and_warnings_are_counted_together(self):
        lines, code = self.report([("fail", "git", "not on PATH"),
                                   ("warn", "gh", "not on PATH")])
        self.assertEqual(code, 1)
        self.assertEqual(lines[-1], "doctor: 2 problem(s)")


class DoctorCommandTest(unittest.TestCase):
    """``cmd_doctor`` composes the checks, prints the report, and returns the
    exit code. The checks themselves are injected, so this never shells out."""

    def run_doctor(self, results, args=()):
        buf = io.StringIO()
        with unittest.mock.patch.object(
                shipd, "default_checks", lambda root: list(results)):
            with redirect_stdout(buf), redirect_stderr(io.StringIO()):
                code = shipd.cmd_doctor(list(args))
        return buf.getvalue(), code

    def test_prints_every_check_line_and_the_closing_line(self):
        out, code = self.run_doctor([("ok", "python", "3.13.0"),
                                     ("warn", "gh", "not on PATH")])
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines(),
                         ["ok python — 3.13.0",
                          "warn gh — not on PATH",
                          "doctor: 1 problem(s)"])

    def test_returns_one_when_a_required_check_fails(self):
        out, code = self.run_doctor([("fail", "git", "not on PATH — install")])
        self.assertEqual(code, 1)
        self.assertIn("fail git — ", out)

    def test_doctor_dispatches_in_binary_without_delegating(self):
        """``doctor`` is handled in the binary like ``list`` — it is not in the
        delegating verb table and never replaces the process."""
        self.assertNotIn("doctor", shipd.VERB_TABLE)
        seen = []

        def fake_doctor(args):
            seen.append(args)
            return 0

        def no_exec(*args):
            self.fail("doctor must not exec-delegate")

        with unittest.mock.patch.object(shipd, "cmd_doctor", fake_doctor), \
                unittest.mock.patch.object(shipd.os, "execv", no_exec):
            code = shipd.main(["doctor"])
        self.assertEqual(code, 0)
        self.assertEqual(seen, [[]])

    def test_takes_no_positional_arguments(self):
        with self.assertRaises(SystemExit) as caught:
            self.run_doctor([("ok", "python", "3.13.0")], args=("extra",))
        self.assertEqual(caught.exception.code, 2)


class DoctorFinishTest(unittest.TestCase):
    """``doctor_finish`` closes the install verb's confirmed finish with the
    same read-only preflight ``doctor`` runs, writing straight to a handle
    rather than returning an exit code."""

    def finish(self, results, root="/tmp/doctor-finish-unused"):
        handle = io.StringIO()
        outcome = shipd.doctor_finish(handle, root=root,
                                      checks=lambda _root: list(results))
        return handle.getvalue(), outcome

    def test_an_all_ok_set_has_the_heading_and_no_pointer(self):
        text, outcome = self.finish([("ok", "python", "3.13.0"),
                                     ("ok", "git", "found")])
        self.assertIn(shipd.INSTALL_FINISH_HEADING, text)
        self.assertIn("ok python — 3.13.0", text)
        self.assertIn("ok git — found", text)
        self.assertIn("doctor: ok", text)
        self.assertNotIn("/s:doctor", text)
        self.assertIsNone(outcome)

    def test_a_failing_check_writes_its_line_and_the_pointer(self):
        text, outcome = self.finish([("fail", "git", "not on PATH"),
                                     ("ok", "python", "3.13.0")])
        self.assertIn("fail git — not on PATH", text)
        self.assertIn("doctor: 1 problem(s)", text)
        self.assertIn("/s:doctor", text)
        self.assertIsNone(outcome)

    def test_a_warning_alone_also_writes_the_pointer(self):
        text, outcome = self.finish([("ok", "python", "3.13.0"),
                                     ("warn", "gh", "not on PATH")])
        self.assertIn("doctor: 1 problem(s)", text)
        self.assertIn("/s:doctor", text)
        self.assertIsNone(outcome)

    def test_checks_and_root_default_to_the_doctor_verbs_own(self):
        fake = unittest.mock.Mock(
            side_effect=lambda root: [("ok", "python", "3.13.0")])
        with unittest.mock.patch.object(shipd, "default_checks", fake):
            handle = io.StringIO()
            outcome = shipd.doctor_finish(handle)
        fake.assert_called_once_with(os.getcwd())
        self.assertIsNone(outcome)


class VendorVerbTestBase(unittest.TestCase):
    """``shipd vendor`` (shipd-cli vendor-verb), driven as a black box through
    the binary itself against throwaway target roots.

    This checkout is only ever the *source* of the vendored copy; every target
    root is a temp directory, and ``HOME`` is isolated so the layered config
    resolution can never read the real user's outermost layer.
    """

    # The four managed surfaces, keyed for the assertions below. ``tree`` and
    # ``marketplace`` sit under the resolved content directory, so their labels
    # are computed per test from that name.
    SCAFFOLD = ("verified", "planned", "completed")

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="shipd-vendor-test-")
        self.home = tempfile.mkdtemp(prefix="shipd-vendor-home-")
        with open(MANIFEST, encoding="utf-8") as fh:
            self.version = json.load(fh)["version"]

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)
        shutil.rmtree(self.root, ignore_errors=True)

    # -- runners -----------------------------------------------------------

    def env(self):
        env = dict(os.environ)
        env["HOME"] = self.home
        return env

    def cli(self, *args):
        """Run the binary itself (shebang + exec bit) against the temp root."""
        return subprocess.run(
            [BIN, "vendor", *args, "--root", self.root],
            capture_output=True, text=True, cwd=self.root, env=self.env())

    # -- the managed surfaces ----------------------------------------------

    def labels(self, content=".shipd"):
        """``{key: reported label}`` for the four managed surfaces."""
        return {
            "tree": os.path.join(content, "plugin", "s"),
            "marketplace": os.path.join(content, "plugin", ".claude-plugin",
                                        "marketplace.json"),
            "settings": os.path.join(".claude", "settings.json"),
            "scaffold": os.path.join(content, "{verified,planned,completed}"),
        }

    def states(self, *args, content=".shipd"):
        """``{surface key: state word}`` parsed from a bare report. The label
        is matched as a whole field, never a substring, so a nested path can
        never be mistaken for its parent."""
        result = self.cli(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        by_label = {label: key
                    for key, label in self.labels(content).items()}
        found = {}
        for line in result.stdout.splitlines():
            fields = line.split()
            if len(fields) >= 2 and fields[1] in by_label:
                found[by_label[fields[1]]] = fields[0]
        return found

    # -- target-tree helpers -----------------------------------------------

    def path(self, *parts):
        return os.path.join(self.root, *parts)

    def tree(self):
        """Every file under the target root, as root-relative paths."""
        found = set()
        for base, _dirs, names in os.walk(self.root):
            for name in names:
                found.add(os.path.relpath(os.path.join(base, name), self.root))
        return found

    def write_json(self, path, data):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
            fh.write("\n")

    def read_json(self, path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)

    def use_content_dir(self, name):
        """Declare a custom content ``dir`` for the target root."""
        self.write_json(self.path(".shipd-config.json"), {"dir": name})

    # -- fixtures ----------------------------------------------------------
    #
    # The report is exercised against a *planted* install rather than one made
    # by ``vendor add``, so these cases stand on their own before the writing
    # modes exist.

    def plant_plugin(self, content=".shipd"):
        """Copy this checkout's plugin tree into the target as ``vendor add``
        would. ``__pycache__`` is generated bytecode, never part of the
        shipping unit, and is excluded on both sides."""
        shutil.copytree(PLUGIN_ROOT, self.path(content, "plugin", "s"),
                        ignore=shutil.ignore_patterns("__pycache__"))

    def plant_marketplace(self, content=".shipd"):
        self.write_json(
            self.path(content, "plugin", ".claude-plugin",
                      "marketplace.json"),
            {"name": "shipd",
             "owner": {"name": "shipd"},
             "plugins": [{"name": "s", "source": "./s"}]})

    def plant_settings(self, content=".shipd", **extra):
        data = {
            "enabledPlugins": {"s@shipd": True},
            "extraKnownMarketplaces": {
                "shipd": {
                    "source": {"source": "directory",
                               "path": "%s/plugin" % content},
                    "autoUpdate": True,
                },
            },
        }
        data.update(extra)
        self.write_json(self.path(".claude", "settings.json"), data)

    def plant_scaffold(self, content=".shipd"):
        for name in self.SCAFFOLD:
            os.makedirs(self.path(content, name), exist_ok=True)
            with open(self.path(content, name, ".gitkeep"), "w") as fh:
                fh.write("")

    def plant_install(self, content=".shipd"):
        self.plant_plugin(content)
        self.plant_marketplace(content)
        self.plant_settings(content)
        self.plant_scaffold(content)

    def vendored_manifest(self, content=".shipd"):
        return self.path(content, "plugin", "s", ".claude-plugin",
                         "plugin.json")

    # -- tree comparison ---------------------------------------------------

    def files_under(self, base):
        """Sorted ``base``-relative paths of every file under it, generated
        bytecode caches excluded."""
        found = []
        for current, dirs, names in os.walk(base):
            dirs[:] = [name for name in dirs if name != "__pycache__"]
            for name in names:
                found.append(
                    os.path.relpath(os.path.join(current, name), base))
        return sorted(found)

    def assertTreeIsByteIdentical(self, content=".shipd"):
        """The vendored tree holds exactly this plugin's files, byte for
        byte."""
        target = self.path(content, "plugin", "s")
        expected = self.files_under(PLUGIN_ROOT)
        self.assertEqual(self.files_under(target), expected)
        for relative in expected:
            with open(os.path.join(PLUGIN_ROOT, relative), "rb") as fh:
                source = fh.read()
            with open(os.path.join(target, relative), "rb") as fh:
                self.assertEqual(fh.read(), source, relative)

    def add(self, *args):
        result = self.cli("add", *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result


class VendorDispatchTest(VendorVerbTestBase):
    """``vendor`` is a curated verb handled inside the binary (shipd-cli
    cli-dispatch), like ``copilot``: it writes files in a target repository,
    which no engine script does, so it never replaces the process."""

    def test_vendor_dispatches_in_binary_without_delegating(self):
        self.assertNotIn("vendor", shipd.VERB_TABLE)
        seen = []

        def fake_vendor(args):
            seen.append(args)
            return 0

        def no_exec(*args):
            self.fail("vendor must not exec-delegate")

        with unittest.mock.patch.object(shipd, "cmd_vendor", fake_vendor), \
                unittest.mock.patch.object(shipd.os, "execv", no_exec):
            code = shipd.main(["vendor", "add", "--force"])
        self.assertEqual(code, 0)
        self.assertEqual(seen, [["add", "--force"]])

    def test_an_unknown_mode_word_is_a_usage_error(self):
        result = self.cli("frobnicate")
        self.assertEqual(result.returncode, 2)
        self.assertIn("frobnicate", result.stderr)
        # A usage error writes nothing into the target repository.
        self.assertEqual(self.tree(), set())


class VendorAddTest(VendorVerbTestBase):
    """``vendor add`` — the idempotent install/refresh of all four surfaces."""

    # -- the vendored tree -------------------------------------------------

    def test_add_writes_a_byte_identical_plugin_tree(self):
        self.add()
        self.assertTreeIsByteIdentical()

    def test_add_vendors_the_test_suites_too(self):
        self.add()
        self.assertTrue(os.path.isfile(self.path(
            ".shipd", "plugin", "s", "skills", "build", "tests",
            "test_shipd_cli.py")))

    def test_add_vendors_an_executable_binary(self):
        self.add()
        vendored = self.path(".shipd", "plugin", "s", "bin", "shipd")
        self.assertTrue(os.access(vendored, os.X_OK), vendored)

    def test_add_reports_every_surface_installed(self):
        self.add()
        self.assertEqual(self.states(),
                         {key: "installed" for key in self.labels()})

    def test_add_leaves_no_temporary_files_behind(self):
        self.add()
        strays = [name for name in self.tree()
                  if os.path.basename(name).startswith(".shipd-")]
        self.assertEqual(strays, [])

    # -- the marketplace manifest ------------------------------------------

    def test_add_generates_the_marketplace_manifest(self):
        self.add()
        data = self.read_json(self.path(".shipd", "plugin", ".claude-plugin",
                                        "marketplace.json"))
        self.assertEqual(data["name"], "shipd")
        self.assertEqual([(entry["name"], entry["source"])
                          for entry in data["plugins"]],
                         [("s", "./s")])

    # -- the settings merge ------------------------------------------------

    def settings(self):
        return self.read_json(self.path(".claude", "settings.json"))

    def test_add_merges_the_two_managed_settings_keys(self):
        self.add()
        data = self.settings()
        self.assertIs(data["enabledPlugins"]["s@shipd"], True)
        self.assertEqual(
            data["extraKnownMarketplaces"]["shipd"],
            {"source": {"source": "directory", "path": ".shipd/plugin"},
             "autoUpdate": True})

    def test_add_registers_the_vendored_statusline(self):
        self.add()
        entry = self.settings()["statusLine"]
        self.assertEqual(entry["type"], "command")
        self.assertIn(".shipd/plugin/s/integrations/statusline.sh",
                      entry["command"])

    def test_add_preserves_an_existing_statusline(self):
        self.write_json(self.path(".claude", "settings.json"),
                        {"statusLine": {"type": "command",
                                        "command": "bash /elsewhere"}})
        self.add()
        data = self.settings()
        self.assertEqual(data["statusLine"]["command"], "bash /elsewhere")
        self.assertIs(data["enabledPlugins"]["s@shipd"], True)
        self.assertIn("shipd", data["extraKnownMarketplaces"])

    def test_add_keeps_unrelated_settings_keys(self):
        self.write_json(self.path(".claude", "settings.json"),
                        {"model": "opus", "env": {"FOO": "bar"}})
        self.add()
        data = self.settings()
        self.assertEqual(data["model"], "opus")
        self.assertEqual(data["env"], {"FOO": "bar"})

    def test_add_refuses_to_rewrite_unparseable_settings(self):
        os.makedirs(self.path(".claude"))
        with open(self.path(".claude", "settings.json"), "w") as fh:
            fh.write("{not json")
        result = self.cli("add")
        self.assertEqual(result.returncode, 1)
        self.assertIn(".claude/settings.json", result.stderr)
        with open(self.path(".claude", "settings.json")) as fh:
            self.assertEqual(fh.read(), "{not json")

    # -- the content scaffold ----------------------------------------------

    def test_add_creates_the_scaffold_with_gitkeeps(self):
        self.add()
        for name in self.SCAFFOLD:
            self.assertTrue(os.path.isdir(self.path(".shipd", name)), name)
            self.assertTrue(os.path.isfile(self.path(".shipd", name,
                                                     ".gitkeep")), name)

    def test_add_never_touches_existing_spec_content(self):
        os.makedirs(self.path(".shipd", "planned", "a-change"))
        with open(self.path(".shipd", "planned", "a-change", "plan.md"),
                  "w") as fh:
            fh.write("# a-change\n")
        self.add()
        with open(self.path(".shipd", "planned", "a-change",
                            "plan.md")) as fh:
            self.assertEqual(fh.read(), "# a-change\n")

    # -- a configured content directory ------------------------------------

    def test_a_configured_content_dir_relocates_every_surface(self):
        self.use_content_dir("specs")
        self.add()
        self.assertTreeIsByteIdentical("specs")
        self.assertFalse(os.path.exists(self.path(".shipd", "plugin")))
        self.assertEqual(
            self.settings()["extraKnownMarketplaces"]["shipd"]["source"],
            {"source": "directory", "path": "specs/plugin"})
        self.assertEqual(self.states(content="specs"),
                         {key: "installed" for key in self.labels("specs")})

    # -- idempotence and refresh -------------------------------------------

    def test_repeated_add_is_a_no_op(self):
        self.add()
        before = {}
        for relative in self.tree():
            with open(self.path(relative), "rb") as fh:
                before[relative] = fh.read()
        self.add()
        after = {}
        for relative in self.tree():
            with open(self.path(relative), "rb") as fh:
                after[relative] = fh.read()
        self.assertEqual(after, before)
        self.assertEqual(self.states(),
                         {key: "installed" for key in self.labels()})

    def test_add_refreshes_a_stale_install_and_prunes_extraneous_files(self):
        self.plant_install()
        manifest = self.read_json(self.vendored_manifest())
        manifest["version"] = "0.0.1"
        self.write_json(self.vendored_manifest(), manifest)
        stray = self.path(".shipd", "plugin", "s", "STRAY.md")
        with open(stray, "w") as fh:
            fh.write("not mine\n")
        self.assertEqual(self.states()["tree"], "stale")

        self.add()
        self.assertFalse(os.path.exists(stray))
        self.assertEqual(self.read_json(self.vendored_manifest())["version"],
                         self.version)
        self.assertTreeIsByteIdentical()
        self.assertEqual(self.states()["tree"], "installed")

    def test_add_repairs_a_modified_vendored_file(self):
        self.plant_install()
        target = self.path(".shipd", "plugin", "s", "bin", "shipd")
        with open(target, "a", encoding="utf-8") as fh:
            fh.write("\n# local edit\n")
        self.add()
        self.assertTreeIsByteIdentical()

    def test_add_completes_a_partial_scaffold(self):
        os.makedirs(self.path(".shipd", "planned"))
        self.add()
        self.assertEqual(self.states()["scaffold"], "installed")

    # -- the foreign guard -------------------------------------------------

    def plant_foreign_plugin(self):
        os.makedirs(self.path(".shipd", "plugin", "s"))
        with open(self.path(".shipd", "plugin", "s", "README.md"), "w") as fh:
            fh.write("someone else's plugin\n")

    def test_add_refuses_a_foreign_plugin_directory_and_writes_nothing(self):
        self.plant_foreign_plugin()
        result = self.cli("add")
        self.assertEqual(result.returncode, 1)
        self.assertIn(os.path.join(".shipd", "plugin", "s"), result.stderr)
        self.assertEqual(self.tree(),
                         {os.path.join(".shipd", "plugin", "s", "README.md")})

    def test_force_replaces_a_foreign_plugin_directory(self):
        self.plant_foreign_plugin()
        self.add("--force")
        self.assertTreeIsByteIdentical()
        self.assertFalse(os.path.exists(
            self.path(".shipd", "plugin", "s", "README.md")))
        self.assertEqual(self.states(),
                         {key: "installed" for key in self.labels()})


class VendorRemoveTest(VendorVerbTestBase):
    """``vendor remove`` — the guarded delete of what the verb owns, and only
    that: the user's spec content is never its to remove."""

    def settings(self):
        return self.read_json(self.path(".claude", "settings.json"))

    def remove(self, *args):
        result = self.cli("remove", *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def test_remove_deletes_the_whole_vendored_plugin_directory(self):
        self.plant_install()
        self.remove()
        self.assertFalse(os.path.exists(self.path(".shipd", "plugin")))
        states = self.states()
        self.assertEqual(states["tree"], "absent")
        self.assertEqual(states["marketplace"], "absent")

    def test_remove_drops_the_two_managed_settings_keys(self):
        self.plant_install()
        self.plant_settings(model="opus")
        self.remove()
        data = self.settings()
        self.assertNotIn("enabledPlugins", data)
        self.assertNotIn("extraKnownMarketplaces", data)
        self.assertEqual(data["model"], "opus")
        self.assertEqual(self.states()["settings"], "absent")

    def test_remove_drops_a_statusline_pointing_into_the_vendored_tree(self):
        self.plant_install()
        self.plant_settings(statusLine={
            "type": "command",
            "command": "bash .shipd/plugin/s/integrations/statusline.sh"})
        self.remove()
        self.assertNotIn("statusLine", self.settings())

    def test_remove_keeps_a_statusline_it_did_not_write(self):
        self.plant_install()
        self.plant_settings(statusLine={"type": "command",
                                        "command": "bash /elsewhere"})
        self.remove()
        self.assertEqual(self.settings()["statusLine"]["command"],
                         "bash /elsewhere")

    def test_remove_keeps_the_scaffold_and_every_planned_change(self):
        self.plant_install()
        os.makedirs(self.path(".shipd", "planned", "a-change"))
        with open(self.path(".shipd", "planned", "a-change", "plan.md"),
                  "w") as fh:
            fh.write("# a-change\n")
        self.remove()
        for name in self.SCAFFOLD:
            self.assertTrue(os.path.isdir(self.path(".shipd", name)), name)
        with open(self.path(".shipd", "planned", "a-change",
                            "plan.md")) as fh:
            self.assertEqual(fh.read(), "# a-change\n")
        self.assertEqual(self.states()["scaffold"], "installed")

    def test_remove_on_an_absent_install_exits_zero_and_deletes_nothing(self):
        self.plant_scaffold()
        before = self.tree()
        self.remove()
        self.assertEqual(self.tree(), before)

    def test_remove_is_idempotent(self):
        self.plant_install()
        self.remove()
        after_first = self.tree()
        self.remove()
        self.assertEqual(self.tree(), after_first)

    def test_remove_honors_a_configured_content_directory(self):
        self.use_content_dir("specs")
        self.plant_install("specs")
        self.remove()
        self.assertFalse(os.path.exists(self.path("specs", "plugin")))
        self.assertTrue(os.path.isdir(self.path("specs", "verified")))

    def test_remove_refuses_a_foreign_plugin_directory(self):
        os.makedirs(self.path(".shipd", "plugin", "s"))
        with open(self.path(".shipd", "plugin", "s", "README.md"), "w") as fh:
            fh.write("someone else's plugin\n")
        before = self.tree()
        result = self.cli("remove")
        self.assertEqual(result.returncode, 1)
        self.assertIn(os.path.join(".shipd", "plugin", "s"), result.stderr)
        self.assertEqual(self.tree(), before)

    def test_force_removes_a_foreign_plugin_directory(self):
        os.makedirs(self.path(".shipd", "plugin", "s"))
        with open(self.path(".shipd", "plugin", "s", "README.md"), "w") as fh:
            fh.write("someone else's plugin\n")
        self.remove("--force")
        self.assertFalse(os.path.exists(self.path(".shipd", "plugin")))


class VendorReportTest(VendorVerbTestBase):
    """The bare verb's read-only per-surface state report."""

    def test_empty_root_reports_every_surface_absent(self):
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        for label in self.labels().values():
            self.assertIn(label, result.stdout)
        self.assertEqual(
            self.states(),
            {key: "absent" for key in self.labels()})

    def test_bare_report_creates_nothing(self):
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.tree(), set())

    def test_bare_report_names_this_installs_version(self):
        result = self.cli()
        self.assertIn(self.version, result.stdout)

    def test_owned_install_at_this_version_reports_installed(self):
        self.plant_install()
        self.assertEqual(
            self.states(),
            {key: "installed" for key in self.labels()})

    def test_older_vendored_version_reports_stale(self):
        self.plant_install()
        manifest = self.read_json(self.vendored_manifest())
        manifest["version"] = "0.0.1"
        self.write_json(self.vendored_manifest(), manifest)
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.states()["tree"], "stale")
        self.assertIn("0.0.1", result.stdout)

    def test_extraneous_vendored_file_reports_stale(self):
        self.plant_install()
        with open(self.path(".shipd", "plugin", "s", "STRAY.md"), "w") as fh:
            fh.write("not mine\n")
        self.assertEqual(self.states()["tree"], "stale")

    def test_modified_vendored_file_reports_stale(self):
        self.plant_install()
        target = self.path(".shipd", "plugin", "s", "bin", "shipd")
        with open(target, "a", encoding="utf-8") as fh:
            fh.write("\n# local edit\n")
        self.assertEqual(self.states()["tree"], "stale")

    def test_plugin_dir_without_a_manifest_reports_foreign(self):
        os.makedirs(self.path(".shipd", "plugin", "s"))
        with open(self.path(".shipd", "plugin", "s", "README.md"), "w") as fh:
            fh.write("someone else's plugin\n")
        self.assertEqual(self.states()["tree"], "foreign")

    def test_plugin_dir_with_an_unparseable_manifest_reports_foreign(self):
        os.makedirs(self.path(".shipd", "plugin", "s", ".claude-plugin"))
        with open(self.vendored_manifest(), "w", encoding="utf-8") as fh:
            fh.write("{not json")
        self.assertEqual(self.states()["tree"], "foreign")

    def test_plugin_dir_naming_another_plugin_reports_foreign(self):
        self.plant_plugin()
        manifest = self.read_json(self.vendored_manifest())
        manifest["name"] = "someone-else"
        self.write_json(self.vendored_manifest(), manifest)
        self.assertEqual(self.states()["tree"], "foreign")

    def test_a_foreign_tree_makes_its_marketplace_manifest_foreign(self):
        self.plant_install()
        manifest = self.read_json(self.vendored_manifest())
        manifest["name"] = "someone-else"
        self.write_json(self.vendored_manifest(), manifest)
        self.assertEqual(self.states()["marketplace"], "foreign")

    def test_marketplace_manifest_naming_another_source_reports_stale(self):
        self.plant_install()
        self.write_json(
            self.path(".shipd", "plugin", ".claude-plugin",
                      "marketplace.json"),
            {"name": "shipd", "plugins": [{"name": "s", "source": "./other"}]})
        self.assertEqual(self.states()["marketplace"], "stale")

    def test_settings_without_the_managed_keys_report_absent(self):
        self.plant_install()
        self.write_json(self.path(".claude", "settings.json"),
                        {"model": "opus"})
        self.assertEqual(self.states()["settings"], "absent")

    def test_partially_merged_settings_report_stale(self):
        self.plant_install()
        self.write_json(self.path(".claude", "settings.json"),
                        {"enabledPlugins": {"s@shipd": True}})
        self.assertEqual(self.states()["settings"], "stale")

    def test_unparseable_settings_report_foreign(self):
        self.plant_install()
        with open(self.path(".claude", "settings.json"), "w") as fh:
            fh.write("{not json")
        self.assertEqual(self.states()["settings"], "foreign")

    def test_a_foreign_statusline_never_makes_the_settings_stale(self):
        # ``add`` never replaces an existing ``statusLine``, so one it did not
        # write is not drift.
        self.plant_install()
        self.plant_settings(
            statusLine={"type": "command", "command": "bash /elsewhere"})
        self.assertEqual(self.states()["settings"], "installed")

    def test_partial_scaffold_reports_stale(self):
        self.plant_install()
        shutil.rmtree(self.path(".shipd", "completed"))
        self.assertEqual(self.states()["scaffold"], "stale")

    def test_report_honors_a_configured_content_directory(self):
        self.use_content_dir("specs")
        self.plant_install("specs")
        self.assertEqual(
            self.states(content="specs"),
            {key: "installed" for key in self.labels("specs")})


class InstallVerbTest(unittest.TestCase):
    """``shipd install`` (shipd-cli cli-dispatch, install-tui install-verb):
    an in-binary verb, since it owns the terminal for the length of its
    question and writes only the user's own files. The flow itself is
    ``test_install_tui.py``'s subject; what is under test here is the verb.
    """

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="shipd-install-verb-home-")

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)

    def cli(self, *args):
        """Run the binary detached from any controlling terminal, so the verb
        takes its headless path whether or not the suite runs in one."""
        env = dict(os.environ)
        env["HOME"] = self.home
        return subprocess.run(
            [BIN, "install", *args], capture_output=True, text=True,
            env=env, start_new_session=True)

    def test_install_dispatches_in_binary_without_delegating(self):
        self.assertNotIn("install", shipd.VERB_TABLE)
        seen = []

        def fake_install(args):
            seen.append(args)
            return 0

        def no_exec(*args):
            self.fail("install must not exec-delegate")

        with unittest.mock.patch.object(shipd, "cmd_install", fake_install), \
                unittest.mock.patch.object(shipd.os, "execv", no_exec):
            code = shipd.main(["install"])
        self.assertEqual(code, 0)
        self.assertEqual(seen, [[]])

    def test_the_banner_lists_install(self):
        r = subprocess.run([BIN, "--help"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("install", r.stdout)

    def test_help_describes_the_verb_and_exits_zero(self):
        r = self.cli("--help")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("shipd install", r.stdout)

    def test_a_headless_run_writes_nothing_and_exits_zero(self):
        r = self.cli()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("shipd install", r.stdout)
        self.assertEqual(os.listdir(self.home), [],
                         "the headless path must write nothing")

    def test_an_argument_is_a_usage_error(self):
        r = self.cli("codex")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(os.listdir(self.home), [])

    def test_cmd_install_closes_with_the_doctor_finish_hook(self):
        calls = []

        class FakeInstallTui:
            def main(self, args, **kwargs):
                calls.append((args, kwargs))
                return 7

        fake = FakeInstallTui()
        with unittest.mock.patch.object(shipd, "_load_install_tui",
                                        lambda: None), \
                unittest.mock.patch.object(shipd, "iu", fake):
            code = shipd.cmd_install(["--flag"])
        self.assertEqual(code, 7)
        self.assertEqual(calls, [(["--flag"],
                                  {"finish": shipd.doctor_finish})])


class ShipdUpdateVerbTests(unittest.TestCase):
    """``shipd update`` (shipd-cli cli-update): compares the newest installed
    plugin snapshot against the version the registered ``shipd`` marketplace
    publishes and, unless ``--check`` is given, applies it through the
    ``claude`` CLI. Driven in-process against fabricated fixtures — a
    throwaway ``HOME``, a ``SHIPD_PLUGIN_CACHE``-rooted cache, a fabricated
    ``known_marketplaces.json`` and marketplace tree, and a stub over
    ``shipd._claude_run`` — the doctor-check style, since the real thing
    touches ``~/.claude`` and the network.
    """

    MARKETPLACE_KEY = "plugin marketplace update shipd"
    APPLY_KEY = "plugin update s@shipd"

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="shipd-update-test-")
        self.home = os.path.join(self.tmp, "home")
        os.makedirs(self.home)
        self.cache = os.path.join(self.tmp, "cache")
        self.marketplace_dir = os.path.join(self.tmp, "marketplace-checkout")
        self._env_patch = unittest.mock.patch.dict(
            os.environ,
            {"HOME": self.home, "SHIPD_PLUGIN_CACHE": self.cache}, clear=True)
        self._env_patch.start()
        # ``clear=True`` above wipes PATH too, so a real ``which("claude")``
        # would depend on this machine — stubbed here so every test but the
        # missing-claude one sees it as present, the fabricated-fixtures style
        # this class's docstring commits to.
        self._which_patch = unittest.mock.patch.object(
            shipd.shutil, "which",
            lambda name: "/usr/bin/claude" if name == "claude" else None)
        self._which_patch.start()

    def tearDown(self):
        self._which_patch.stop()
        self._env_patch.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def make_cache(self, versions):
        """A fabricated cache root ``<cache>/<version>/bin/`` for each
        version, rooted at the env-overridden ``SHIPD_PLUGIN_CACHE`` rather
        than the real cache path."""
        for version in versions:
            os.makedirs(os.path.join(self.cache, version, "bin"))

    def register_marketplace(self, version, plugin_name="s",
                              source="./plugins/s"):
        """A fabricated ``known_marketplaces.json`` naming
        ``self.marketplace_dir`` as the ``shipd`` marketplace's install
        location, plus that location's own marketplace manifest and the
        ``s`` plugin's manifest declaring ``version`` — mirrors this
        machine's real registration (plan.md's ``## Implementation``)."""
        plugins_dir = os.path.join(self.home, ".claude", "plugins")
        os.makedirs(plugins_dir, exist_ok=True)
        registry = {
            "shipd": {
                "source": {"source": "directory", "path": self.marketplace_dir},
                "installLocation": self.marketplace_dir,
            }
        }
        with open(os.path.join(plugins_dir, "known_marketplaces.json"),
                  "w", encoding="utf-8") as fh:
            json.dump(registry, fh)
        manifest_dir = os.path.join(self.marketplace_dir, ".claude-plugin")
        os.makedirs(manifest_dir, exist_ok=True)
        with open(os.path.join(manifest_dir, "marketplace.json"),
                  "w", encoding="utf-8") as fh:
            json.dump({"plugins": [{"name": plugin_name, "source": source}]},
                      fh)
        plugin_manifest_dir = os.path.join(
            self.marketplace_dir, "plugins", "s", ".claude-plugin")
        os.makedirs(plugin_manifest_dir, exist_ok=True)
        with open(os.path.join(plugin_manifest_dir, "plugin.json"),
                  "w", encoding="utf-8") as fh:
            json.dump({"version": version}, fh)

    def claude_stub(self, responses, apply_creates=None):
        """A ``_claude_run`` stand-in answering from ``responses`` (the
        joined argument string -> ``(returncode, stdout, stderr)``); every
        call is recorded on ``self.claude_calls`` and an unlisted one fails
        the test. When ``apply_creates`` is given, the ``plugin update`` call
        also creates that version directory under the fabricated cache,
        mirroring the real command fetching a new snapshot before
        ``cmd_update`` re-resolves what the cache actually holds."""
        self.claude_calls = []

        def run(args, timeout=None):
            key = " ".join(args)
            self.claude_calls.append((key, timeout))
            if key not in responses:
                self.fail("unexpected claude invocation: %s" % key)
            if apply_creates and key == self.APPLY_KEY:
                os.makedirs(os.path.join(self.cache, apply_creates, "bin"),
                            exist_ok=True)
            return responses[key]

        return run

    def run_update(self, argv, responses, apply_creates=None):
        run = self.claude_stub(responses, apply_creates=apply_creates)
        out, err = io.StringIO(), io.StringIO()
        with unittest.mock.patch.object(shipd, "_claude_run", run), \
                redirect_stdout(out), redirect_stderr(err):
            code = shipd.cmd_update(argv)
        return code, out.getvalue(), err.getvalue()

    def test_missing_claude_is_an_actionable_error(self):
        with unittest.mock.patch.object(shipd.shutil, "which",
                                        lambda name: None):
            code, out, err = self.run_update([], {})
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        lines = err.strip().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith("Error:"))
        self.assertIn("claude", lines[0])
        self.assertIn("PATH", lines[0])
        self.assertEqual(self.claude_calls, [])

    def test_newer_version_is_applied(self):
        self.make_cache(["0.6.9"])
        self.register_marketplace("0.6.10")
        code, out, _err = self.run_update(
            [], {
                self.MARKETPLACE_KEY: (0, "", ""),
                self.APPLY_KEY: (0, "Updated s@shipd\n", ""),
            }, apply_creates="0.6.10")
        self.assertEqual(code, 0)
        self.assertIn("0.6.9", out)
        self.assertIn("0.6.10", out)
        self.assertIn("new session", out)
        self.assertIn(self.APPLY_KEY, [key for key, _t in self.claude_calls])

    def test_check_reports_without_applying(self):
        self.make_cache(["0.6.9"])
        self.register_marketplace("0.6.10")
        code, out, _err = self.run_update(
            ["--check"], {self.MARKETPLACE_KEY: (0, "", "")})
        self.assertEqual(code, 0)
        self.assertIn("0.6.9", out)
        self.assertIn("0.6.10", out)
        self.assertNotIn(self.APPLY_KEY, [key for key, _t in self.claude_calls])

    def test_already_current_changes_nothing(self):
        self.make_cache(["0.6.10"])
        self.register_marketplace("0.6.10")
        code, out, _err = self.run_update(
            [], {self.MARKETPLACE_KEY: (0, "", "")})
        self.assertEqual(code, 0)
        self.assertIn("0.6.10", out)
        self.assertEqual([key for key, _t in self.claude_calls],
                         [self.MARKETPLACE_KEY])

    def test_newest_snapshot_wins_numerically(self):
        self.make_cache(["0.6.9", "0.6.10"])
        self.assertEqual(shipd.newest_installed(self.cache), "0.6.10")

    def test_unregistered_marketplace_is_an_actionable_error(self):
        self.make_cache(["0.6.9"])
        code, _out, err = self.run_update([], {})
        self.assertEqual(code, 1)
        self.assertIn("claude plugin marketplace add shipd-now/shipd", err)

    def test_failing_marketplace_refresh_reports_no_comparison(self):
        self.make_cache(["0.6.9"])
        self.register_marketplace("0.6.10")
        code, out, err = self.run_update(
            [], {self.MARKETPLACE_KEY: (1, "", "boom")})
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertTrue(err.strip())

    def test_empty_cache_is_an_actionable_error(self):
        self.register_marketplace("0.6.10")
        code, _out, err = self.run_update(
            [], {self.MARKETPLACE_KEY: (0, "", "")})
        self.assertEqual(code, 1)
        self.assertIn("claude plugin install s@shipd", err)

    def test_failing_apply_is_an_error(self):
        self.make_cache(["0.6.9"])
        self.register_marketplace("0.6.10")
        code, _out, err = self.run_update(
            [], {
                self.MARKETPLACE_KEY: (0, "", ""),
                self.APPLY_KEY: (1, "", "apply failed"),
            })
        self.assertEqual(code, 1)
        self.assertTrue(err.strip())

    def test_non_dotted_numeric_published_version_is_an_actionable_error(self):
        self.make_cache(["0.6.9"])
        self.register_marketplace("1.0.0-rc1")
        code, out, err = self.run_update(
            [], {self.MARKETPLACE_KEY: (0, "", "")})
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        lines = err.strip().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith("Error:"))
        self.assertIn("1.0.0-rc1", lines[0])
        self.assertNotIn(self.APPLY_KEY, [key for key, _t in self.claude_calls])


if __name__ == "__main__":
    unittest.main()
