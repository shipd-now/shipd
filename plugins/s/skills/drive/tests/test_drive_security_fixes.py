#!/usr/bin/env python3
"""Regression tests for three semantic-review findings posted on PR #192
against the drive skill:

1. (high) the auth cache directory (``~/.shipd/drive/auth/``) and the
   storage-state file it holds must never be world-readable — the file
   carries live session cookies. `drive.py login` creates the directory
   through `_ensure_private_dir` (mode `0700`, and `chmod`ed to `0700` even
   when the directory already existed with looser bits); the worker that
   actually writes the storage-state file, `browser_worker.py cmd_login`,
   `chmod`s it to `0600` immediately after writing
   (`_write_storage_state_privately`).

2. (high) the session daemon's Unix socket
   (``~/.shipd/drive/session.sock``) must never be connectable by another
   local user — its handler set includes `eval`, `click`, and `type`
   against an *authenticated* browser, with no peer check. `drive.py
   session start` creates `SESSION_DIR` through the same
   `_ensure_private_dir` helper, and `browser_worker.py cmd_session` binds
   the socket through `_bind_private_socket`, which holds a restrictive
   `0o077` umask for the duration of `bind()` (so the socket file never
   exists, even momentarily, with group/other bits set) and additionally
   `chmod`s it to `0600` right after as a belt-and-braces second layer.

3. (medium) `drive.py`'s `resolve_secret_command` (the `command` auth
   recipe's one leg) must never echo a credential helper's stdout into its
   error message — only `stderr`, with an explicit "no stderr output" note
   when `stderr` is empty — since a broken helper's stdout is exactly where
   a leaked secret would be.

`drive.py` and `browser_worker.py` are both stdlib-only at module scope
(the latter imports `playwright` lazily, inside the functions that actually
drive a browser), so this whole suite runs with no Playwright installed at
all — `_write_storage_state_privately` and `_bind_private_socket` are
exercised directly, with a duck-typed stand-in context and a plain
`socket.socket` respectively, rather than through a real browser or
session. The CLI-level tests use the same restricted-`PATH` spy-`uv`
approach as `test_drive_auth_cache.py` and `test_drive_session.py`.
"""

import json
import os
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
SCRIPT = os.path.join(SCRIPTS, "drive.py")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import drive  # noqa: E402
import browser_worker as bw  # noqa: E402
from _stubs import stub_bindir  # noqa: E402


def _mode(path):
    return stat.S_IMODE(os.stat(path).st_mode)


# --- Finding 1: the auth cache directory and file -------------------------


class AuthCacheDirIsPrivateTest(unittest.TestCase):
    """`drive.py login` (drive-auth-cache) must leave
    `~/.shipd/drive/auth/` at mode `0700`, whether it creates that
    directory fresh or finds it already there — and, per the finding, a
    real run left it `0755` (world-readable/traversable), so this pins the
    fix against a directory that *already exists* with looser bits, not
    only the fresh-creation path."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="drive-sec-auth-")
        self.home = os.path.join(self.tmp, "home")
        os.makedirs(self.home, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def user_targets_path(self):
        return os.path.join(self.home, ".shipd", "drive", "targets.json")

    def auth_dir(self):
        return os.path.join(self.home, ".shipd", "drive", "auth")

    def write_json(self, path, data):
        d = os.path.dirname(path)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh)

    def run_cli(self, *args, path_dir):
        env = {"PATH": path_dir, "HOME": self.home}
        return subprocess.run(
            [sys.executable, SCRIPT, *args],
            capture_output=True, text=True, env=env)

    def test_login_leaves_the_auth_dir_owner_only_from_scratch(self):
        self.write_json(self.user_targets_path(), {
            "targets": {
                "app": {"url": "https://app.example",
                        "auth": {"kind": "none"}},
            },
        })
        bindir = stub_bindir(self.tmp, "bin", ["uv"])

        r = self.run_cli("login", "app", path_dir=bindir)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(os.path.isdir(self.auth_dir()))
        self.assertEqual(_mode(self.auth_dir()), 0o700)

    def test_login_re_privatizes_a_pre_existing_world_readable_auth_dir(
            self):
        # Simulates exactly what the finding observed on a real run: the
        # directory already exists, and it is world-readable.
        self.write_json(self.user_targets_path(), {
            "targets": {
                "app": {"url": "https://app.example",
                        "auth": {"kind": "none"}},
            },
        })
        os.makedirs(self.auth_dir(), exist_ok=True)
        os.chmod(self.auth_dir(), 0o755)
        self.assertEqual(_mode(self.auth_dir()), 0o755)
        bindir = stub_bindir(self.tmp, "bin", ["uv"])

        r = self.run_cli("login", "app", path_dir=bindir)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(_mode(self.auth_dir()), 0o700)


class EnsurePrivateDirUnitTest(unittest.TestCase):
    """Direct unit coverage of `drive._ensure_private_dir`: fresh creation
    is `0700`, and an already-existing looser directory is corrected —
    `os.makedirs(..., mode=..., exist_ok=True)` alone would silently keep
    a pre-existing directory's old mode, which is exactly the bug the
    finding reported."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="drive-sec-ensure-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_creates_a_fresh_directory_as_owner_only(self):
        target = os.path.join(self.tmp, "nested", "auth")
        drive._ensure_private_dir(target)
        self.assertEqual(_mode(target), 0o700)

    def test_corrects_an_existing_world_readable_directory(self):
        target = os.path.join(self.tmp, "auth")
        os.makedirs(target, mode=0o755, exist_ok=True)
        os.chmod(target, 0o755)
        self.assertEqual(_mode(target), 0o755)
        drive._ensure_private_dir(target)
        self.assertEqual(_mode(target), 0o700)


class StorageStateFileIsPrivateTest(unittest.TestCase):
    """Direct unit coverage of `browser_worker._write_storage_state_privately`
    — the helper `cmd_login` calls right after Playwright's own
    `context.storage_state(path=...)` write. A plain stand-in object with a
    Playwright-shaped `storage_state(path=...)` method is enough to exercise
    the exact chmod behavior with no real Playwright context involved."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="drive-sec-storage-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_the_written_file_ends_up_owner_only(self):
        out_path = os.path.join(self.tmp, "app.json")

        class _FakeContext:
            def storage_state(self, path):
                with open(path, "w", encoding="utf-8") as fh:
                    json.dump({"cookies": ["fresh"]}, fh)
                # Mirrors a real filesystem write landing at the umask's
                # default, world-readable mode, before this helper's own
                # chmod runs.
                os.chmod(path, 0o644)

        bw._write_storage_state_privately(_FakeContext(), out_path)

        self.assertTrue(os.path.isfile(out_path))
        self.assertEqual(_mode(out_path), 0o600)
        with open(out_path, encoding="utf-8") as fh:
            self.assertEqual(json.load(fh), {"cookies": ["fresh"]})


# --- Finding 2: the session directory and socket ---------------------------


class SessionDirIsPrivateTest(unittest.TestCase):
    """`drive.py session start` (drive-session) must leave `SESSION_DIR`
    (``~/.shipd/drive/``) at mode `0700`, whether created fresh or already
    present with looser bits — the same "already `0755` on a real run"
    scenario the finding reported for the auth directory applies here too,
    since the socket lives in the same directory."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="drive-sec-session-")
        self.home = os.path.join(self.tmp, "home")
        os.makedirs(self.home, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def session_dir(self):
        return os.path.join(self.home, ".shipd", "drive")

    def run_cli(self, *args, path_dir):
        env = {"PATH": path_dir, "HOME": self.home}
        return subprocess.run(
            [sys.executable, SCRIPT, *args],
            capture_output=True, text=True, env=env)

    def test_session_start_leaves_session_dir_owner_only_from_scratch(self):
        bindir = stub_bindir(self.tmp, "bin", ["uv"])
        r = self.run_cli("session", "start", "app", path_dir=bindir)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(os.path.isdir(self.session_dir()))
        self.assertEqual(_mode(self.session_dir()), 0o700)

    def test_session_start_re_privatizes_a_world_readable_session_dir(self):
        os.makedirs(self.session_dir(), exist_ok=True)
        os.chmod(self.session_dir(), 0o755)
        self.assertEqual(_mode(self.session_dir()), 0o755)
        bindir = stub_bindir(self.tmp, "bin", ["uv"])

        r = self.run_cli("session", "start", "app", path_dir=bindir)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(_mode(self.session_dir()), 0o700)


class SessionSocketIsOwnerOnlyTest(unittest.TestCase):
    """Direct unit coverage of `browser_worker._bind_private_socket`: the
    bound socket file ends up mode `0600` regardless of the ambient umask,
    and the process umask is restored afterward rather than leaking a
    changed umask into the rest of the process."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="drive-sec-socket-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_bound_socket_is_owner_only_even_under_a_permissive_umask(self):
        socket_path = os.path.join(self.tmp, "session.sock")
        # A permissive ambient umask is exactly the condition that left the
        # real socket world-connectable (drwxr-xr-x's sibling problem for
        # the socket file itself) — pin the fix against it directly.
        original_umask = os.umask(0o022)
        try:
            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                bw._bind_private_socket(server, socket_path)
                self.assertEqual(_mode(socket_path), 0o600)
            finally:
                server.close()
                if os.path.exists(socket_path):
                    os.remove(socket_path)
        finally:
            # `_bind_private_socket` must restore whatever umask it found,
            # never leave the process on its own restrictive one.
            restored = os.umask(original_umask)
            self.assertEqual(restored, 0o022)

    def test_umask_is_restored_even_when_bind_itself_fails(self):
        # An invalid (nonexistent parent directory) socket path makes
        # `bind()` raise — the umask must still come back, not leak a
        # restrictive 0o077 into the rest of the process.
        bad_path = os.path.join(self.tmp, "missing-dir", "session.sock")
        original_umask = os.umask(0o022)
        try:
            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                with self.assertRaises(OSError):
                    bw._bind_private_socket(server, bad_path)
            finally:
                server.close()
        finally:
            restored = os.umask(original_umask)
            self.assertEqual(restored, 0o022)


# --- Finding 3: the auth-command error never echoes the secret ------------


class AuthCommandErrorNeverLeaksTheSecretTest(unittest.TestCase):
    """Direct unit coverage of `drive.resolve_secret_command`
    (drive-targets-config): a failing credential helper's stdout — exactly
    where a printed secret would land — must never appear in the raised
    `DriveError`, whether or not the helper also wrote to stderr."""

    def test_a_secret_printed_to_stdout_never_reaches_the_error(self):
        secret = "sk-super-secret-value-should-never-leak"

        def fake_run(argv, input=None, env=None):
            return 1, secret, ""

        with self.assertRaises(drive.DriveError) as ctx:
            drive.resolve_secret_command(["helper"], run=fake_run)

        message = str(ctx.exception)
        self.assertNotIn(secret, message)
        self.assertIn("no stderr output", message)

    def test_a_secret_on_stdout_still_does_not_leak_when_stderr_is_present(
            self):
        secret = "sk-super-secret-value-should-never-leak"

        def fake_run(argv, input=None, env=None):
            return 1, secret, "permission denied"

        with self.assertRaises(drive.DriveError) as ctx:
            drive.resolve_secret_command(["helper"], run=fake_run)

        message = str(ctx.exception)
        self.assertNotIn(secret, message)
        self.assertIn("permission denied", message)

    def test_stderr_content_is_still_reported_when_present(self):
        def fake_run(argv, input=None, env=None):
            return 1, "", "helper not found"

        with self.assertRaises(drive.DriveError) as ctx:
            drive.resolve_secret_command(["helper"], run=fake_run)

        self.assertIn("helper not found", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
