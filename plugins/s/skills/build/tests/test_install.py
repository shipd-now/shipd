#!/usr/bin/env python3
"""Tests for the repo-root ``install.sh`` and the ``shipd`` launcher it writes.

Both are driven as black boxes via subprocess, never sourced: the installer
runs under a throwaway ``HOME`` with a stub ``claude`` first on ``PATH`` that
records its argv, and the launcher runs against a fabricated plugin cache
rooted by ``SHIPD_PLUGIN_CACHE`` — no real ``~/.claude`` and no network in
either direction.

The launcher lives inside ``install.sh`` as a quoted heredoc, which is its
single source of truth; :func:`launcher_body` extracts that body so the
launcher tests exercise exactly the text the installer writes.

Follows ``test_statusline.py``'s pattern of testing a repo file (outside
``plugins/s/``) from the plugin's own test suite.
"""

import os
import shutil
import stat
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
# tests -> build -> skills -> s -> plugins -> repository root
REPO_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", "..", ".."))
INSTALL_SH = os.path.join(REPO_ROOT, "install.sh")

# The heredoc delimiter fencing the launcher body inside install.sh.
LAUNCHER_MARKER = "SHIPD_LAUNCHER_EOF"

# The one command every "no snapshot installed" error must name.
INSTALL_HINT = "claude plugin install s@shipd"

# The post-install auto-update notice. Auto-update is off by default for
# third-party marketplaces, so a successful install has to name both enable
# surfaces — the `/plugin` Marketplaces toggle and the `"autoUpdate": true`
# settings entry — plus how an update applies and the manual fallback. The
# settings fragment doubles as the notice's sentinel: it appears nowhere else,
# so its absence is the notice's absence.
AUTO_UPDATE_SENTINEL = '"autoUpdate": true'
AUTO_UPDATE_FRAGMENTS = (
    "/plugin",
    "Marketplaces",
    "shipd",
    AUTO_UPDATE_SENTINEL,
    "session",
    "claude plugin update s@shipd",
)


def launcher_body():
    """The python3 launcher's source, extracted from ``install.sh``'s quoted
    heredoc — the installer's own copy, so these tests can never drift from
    what a consumer actually gets."""
    with open(INSTALL_SH, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.rstrip().endswith("<<'%s'" % LAUNCHER_MARKER):
            start = i + 1
            break
    if start is None:
        raise AssertionError(
            "no <<'%s' heredoc found in %s" % (LAUNCHER_MARKER, INSTALL_SH))
    for i in range(start, len(lines)):
        if lines[i].strip() == LAUNCHER_MARKER:
            return "\n".join(lines[start:i]) + "\n"
    raise AssertionError(
        "unterminated %s heredoc in %s" % (LAUNCHER_MARKER, INSTALL_SH))


def write_exec(path, body):
    """Write ``body`` to ``path`` (creating parents) and mark it executable."""
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(body)
    os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR | stat.S_IXGRP
             | stat.S_IXOTH)
    return path


class LauncherTest(unittest.TestCase):
    """The version-independent launcher (cache-launcher): newest dotted
    version wins, arguments and exit code pass through, a missing snapshot is
    an actionable error."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="shipd-launcher-test-")
        self.cache = os.path.join(self.tmp, "cache")
        self.launcher = write_exec(
            os.path.join(self.tmp, "shipd"), launcher_body())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # --- fixture helpers --------------------------------------------------
    def make_snapshot(self, version, exit_code=0):
        """A fake cache snapshot whose ``bin/shipd`` echoes its own version
        and the arguments it received, then exits ``exit_code``."""
        body = ('#!/bin/sh\n'
                'echo "snapshot %s argv: $*"\n'
                'exit %d\n' % (version, exit_code))
        return write_exec(
            os.path.join(self.cache, version, "bin", "shipd"), body)

    def run_launcher(self, *args, **kwargs):
        env = dict(os.environ)
        env["SHIPD_PLUGIN_CACHE"] = kwargs.pop("cache", self.cache)
        return subprocess.run(
            ["python3", self.launcher, *args],
            capture_output=True, text=True, env=env)

    # --- tests ------------------------------------------------------------
    def test_newest_snapshot_wins_numerically(self):
        # A lexicographic order would pick 0.6.9; dotted-integer order picks
        # 0.6.10.
        self.make_snapshot("0.6.9")
        self.make_snapshot("0.6.10")
        r = self.run_launcher()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("snapshot 0.6.10", r.stdout)
        self.assertNotIn("0.6.9", r.stdout)

    def test_arguments_and_exit_code_pass_through(self):
        self.make_snapshot("1.2.3", exit_code=7)
        r = self.run_launcher("status", "--root", "/tmp/x")
        self.assertEqual(r.returncode, 7, r.stderr)
        self.assertIn("argv: status --root /tmp/x", r.stdout)

    def test_non_version_directory_is_ignored(self):
        # A stray non-version entry in the cache root must never be chosen.
        self.make_snapshot("0.6.10")
        write_exec(os.path.join(self.cache, "latest", "bin", "shipd"),
                   '#!/bin/sh\necho "snapshot latest argv: $*"\n')
        r = self.run_launcher()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("snapshot 0.6.10", r.stdout)
        self.assertNotIn("latest", r.stdout)

    def test_empty_cache_root_is_actionable_error(self):
        os.makedirs(self.cache)
        r = self.run_launcher()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn(INSTALL_HINT, r.stderr)
        self.assertEqual(r.stdout, "")

    def test_absent_cache_root_is_actionable_error(self):
        r = self.run_launcher(cache=os.path.join(self.tmp, "nowhere"))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn(INSTALL_HINT, r.stderr)


# A stub `claude` recording every invocation's arguments one line per call.
# `$CLAUDE_STUB_MODE` picks the outcome: `ok` succeeds, `already` emulates a
# re-run against an existing marketplace/plugin (nonzero with an
# already-present message), `boom` is a genuine failure.
CLAUDE_STUB = """#!/bin/sh
printf '%s\\n' "$*" >> "$CLAUDE_STUB_LOG"
case "$CLAUDE_STUB_MODE" in
  already)
    case "$2" in
      marketplace) echo "Marketplace shipd already exists" ;;
      *)           echo "Plugin s@shipd is already installed" ;;
    esac
    exit 1
    ;;
  boom)
    echo "network is on fire" >&2
    exit 1
    ;;
esac
exit 0
"""


class InstallerTest(unittest.TestCase):
    """The repo-root installer (install-script): both `claude plugin` steps,
    the launcher it writes, the PATH hint, the missing-prerequisite abort, and
    an idempotent re-run — all against a stub `claude` and a temp HOME."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="shipd-install-test-")
        self.home = os.path.join(self.tmp, "home")
        os.makedirs(self.home)
        self.bin = os.path.join(self.tmp, "stub-bin")
        os.makedirs(self.bin)
        self.log = os.path.join(self.tmp, "claude-argv.log")
        # python3 must stay reachable even on the pruned PATH the
        # missing-`claude` case uses.
        os.symlink(shutil.which("python3"), os.path.join(self.bin, "python3"))
        self.launcher = os.path.join(self.home, ".local", "bin", "shipd")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # --- fixture helpers --------------------------------------------------
    def stub_claude(self):
        write_exec(os.path.join(self.bin, "claude"), CLAUDE_STUB)

    def run_install(self, mode="ok", local_bin_on_path=False):
        env = {
            "HOME": self.home,
            "CLAUDE_STUB_LOG": self.log,
            "CLAUDE_STUB_MODE": mode,
            # A pruned PATH: the stub dir plus the system directories the
            # script's utilities live in — never the real `claude`.
            "PATH": os.pathsep.join([self.bin, "/usr/bin", "/bin"]),
        }
        if local_bin_on_path:
            env["PATH"] = os.path.join(
                self.home, ".local", "bin") + os.pathsep + env["PATH"]
        return subprocess.run(
            ["sh", INSTALL_SH], capture_output=True, text=True, env=env)

    def claude_calls(self):
        if not os.path.exists(self.log):
            return []
        with open(self.log, encoding="utf-8") as fh:
            return fh.read().splitlines()

    # --- tests ------------------------------------------------------------
    def test_fresh_install_runs_both_steps_and_writes_launcher(self):
        self.stub_claude()
        r = self.run_install()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("plugin marketplace add shipd-now/shipd",
                      self.claude_calls())
        self.assertIn("plugin install s@shipd", self.claude_calls())
        self.assertTrue(os.access(self.launcher, os.X_OK),
                        "%s is missing or not executable" % self.launcher)

    def test_written_launcher_is_the_heredoc_body(self):
        self.stub_claude()
        self.run_install()
        with open(self.launcher, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), launcher_body())

    def test_path_hint_printed_when_local_bin_absent_from_path(self):
        self.stub_claude()
        r = self.run_install()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(os.path.join(self.home, ".local", "bin"), r.stdout)
        self.assertIn("PATH", r.stdout)

    def test_no_path_hint_when_local_bin_already_on_path(self):
        self.stub_claude()
        r = self.run_install(local_bin_on_path=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("PATH", r.stdout)

    def test_success_prints_the_auto_update_notice(self):
        self.stub_claude()
        r = self.run_install()
        self.assertEqual(r.returncode, 0, r.stderr)
        for fragment in AUTO_UPDATE_FRAGMENTS:
            self.assertIn(fragment, r.stdout)

    def test_auto_update_notice_prints_when_local_bin_is_on_path(self):
        # The notice is unconditional: it must not ride along with the PATH
        # hint, which a consumer whose ~/.local/bin is already on PATH misses.
        self.stub_claude()
        r = self.run_install(local_bin_on_path=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(AUTO_UPDATE_SENTINEL, r.stdout)

    def test_install_edits_no_settings_file(self):
        # The notice instructs, never performs: enabling auto-update is the
        # user's toggle to flip, so the installer leaves ~/.claude untouched
        # and only the stub `claude` (which writes nothing) could create it.
        self.stub_claude()
        r = self.run_install()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(
            os.path.exists(os.path.join(self.home, ".claude")),
            "install.sh must not create anything under ~/.claude")

    def test_missing_claude_aborts_without_the_auto_update_notice(self):
        # No stub `claude` -> nothing was installed, so nothing to auto-update.
        r = self.run_install()
        self.assertNotEqual(r.returncode, 0)
        self.assertNotIn(AUTO_UPDATE_SENTINEL, r.stdout)
        self.assertNotIn(AUTO_UPDATE_SENTINEL, r.stderr)

    def test_failed_claude_step_prints_no_auto_update_notice(self):
        self.stub_claude()
        r = self.run_install(mode="boom")
        self.assertNotEqual(r.returncode, 0)
        self.assertNotIn(AUTO_UPDATE_SENTINEL, r.stdout)
        self.assertNotIn(AUTO_UPDATE_SENTINEL, r.stderr)

    def test_missing_claude_aborts_without_writing_launcher(self):
        # No stub `claude` written -> the prerequisite check must abort first.
        r = self.run_install()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("claude", r.stderr.lower())
        self.assertFalse(os.path.exists(self.launcher))
        self.assertEqual(self.claude_calls(), [])

    def test_rerun_with_everything_present_is_idempotent(self):
        self.stub_claude()
        first = self.run_install()
        self.assertEqual(first.returncode, 0, first.stderr)
        second = self.run_install(mode="already")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertTrue(os.access(self.launcher, os.X_OK))

    def test_genuine_claude_failure_is_reported(self):
        # An already-present outcome is success; anything else is not.
        self.stub_claude()
        r = self.run_install(mode="boom")
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
