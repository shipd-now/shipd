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

import importlib.machinery
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
BIN = os.path.normpath(os.path.join(HERE, "..", "..", "..", "bin", "shipd"))

# The curated verb table the usage banner must name (shipd-cli cli-dispatch).
VERBS = ("list", "status", "locate", "epic", "workspace", "board", "metrics",
         "lint", "doctor")


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
    def test_retired_html_mode_falls_through_to_the_interactive_delegate(self):
        # ``html`` is no longer a board mode word, so it is not consumed: it
        # reaches ``dashboard.py tui`` as a trailing argument, which argparse
        # rejects.
        self.make_epic("ep", ["m1"])
        self.make_change(self.root, "m1", status="ready")
        out = os.path.join(self.root, "board.html")
        r = self.cli("board", "html", "--root", self.root, "--out", out,
                     "--once")
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("unrecognized arguments", r.stderr)
        self.assertFalse(os.path.exists(out), "fall-through wrote a page")

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

    # -- textual -----------------------------------------------------------

    def test_textual_importable_is_ok(self):
        level, name, _detail = shipd.check_textual(
            find_spec=lambda name: object())
        self.assertEqual((level, name), ("ok", "textual"))

    def test_textual_missing_warns_about_the_board_only(self):
        level, name, detail = shipd.check_textual(find_spec=lambda name: None)
        self.assertEqual((level, name), ("warn", "textual"))
        self.assertIn("board", detail)

    def test_textual_probe_failure_warns(self):
        def boom(name):
            raise ValueError("no parent package")
        level, name, _detail = shipd.check_textual(find_spec=boom)
        self.assertEqual((level, name), ("warn", "textual"))

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


if __name__ == "__main__":
    unittest.main()
