#!/usr/bin/env python3
"""Unit tests for `drive.py`'s cached-login reuse (drive-auth-cache): an
auth file inside the resolved `authCacheTtlHours` TTL is reused with no
login worker invocation; one older than the TTL triggers a fresh login and
an overwrite; and a failed login reports a debug screenshot path and exits
non-zero while leaving the previous auth file exactly as it was.

Like `test_drive_targets.py`, `uv` on the restricted test `PATH` is a small
Python spy script (never a real Playwright worker) that records its
invocation to a log file when `DRIVE_TEST_SPY_LOG` is set, so a test can
assert on *whether* the login worker ran without ever touching a real
browser. `DRIVE_TEST_SPY_FAIL` switches the spy into a failure mode that
writes a debug screenshot marker beside the requested output (mirroring
`browser_worker.py login`'s own `<out>.debug.png` fallback) and exits
non-zero without writing the requested `--out` storage-state file at all —
exactly how a real failed login must never touch the cache it was asked to
refresh."""

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
SCRIPT = os.path.join(SCRIPTS, "drive.py")

_UV_SPY_TEMPLATE = """#!{python}
import json
import os
import sys

argv = sys.argv[1:]
log_path = os.environ.get("DRIVE_TEST_SPY_LOG")
if log_path:
    with open(log_path, "w", encoding="utf-8") as fh:
        json.dump({{"argv": argv, "env": dict(os.environ)}}, fh)


def _arg(flag):
    return argv[argv.index(flag) + 1] if flag in argv else None


out_path = _arg("--out")
debug_path = _arg("--debug-screenshot")

if os.environ.get("DRIVE_TEST_SPY_FAIL"):
    # Mirrors browser_worker.py login's own fallback: a debug screenshot
    # beside the requested output when no explicit path was given, and the
    # requested --out storage state left untouched.
    debug_shot = debug_path or ((out_path or "") + ".debug.png")
    if debug_shot:
        with open(debug_shot, "wb") as fh:
            fh.write(b"")
    print("Error: login failed: simulated failure (screenshot: %s)"
          % debug_shot, file=sys.stderr)
    sys.exit(1)

if out_path:
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump({{"cookies": ["fresh"]}}, fh)

print(json.dumps({{"ok": True, "storageState": out_path}}))
"""


class DriveAuthCacheTestBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="drive-auth-cache-")
        self.home = os.path.join(self.tmp, "home")
        os.makedirs(self.home, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write_json(self, path, data):
        d = os.path.dirname(path)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh)

    def user_targets_path(self):
        return os.path.join(self.home, ".shipd", "drive", "targets.json")

    def auth_path(self, target="app"):
        return os.path.join(
            self.home, ".shipd", "drive", "auth", "%s.json" % target)

    def write_target_config(self, ttl_hours=None):
        data = {
            "targets": {
                "app": {"url": "https://app.example",
                        "auth": {"kind": "none"}},
            },
        }
        if ttl_hours is not None:
            data["authCacheTtlHours"] = ttl_hours
        self.write_json(self.user_targets_path(), data)

    def spy_bindir(self):
        d = os.path.join(self.tmp, "bin")
        os.makedirs(d, exist_ok=True)
        uv_path = os.path.join(d, "uv")
        with open(uv_path, "w", encoding="utf-8") as fh:
            fh.write(_UV_SPY_TEMPLATE.format(python=sys.executable))
        os.chmod(uv_path, os.stat(uv_path).st_mode
                 | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        return d

    def run_cli(self, *args, extra_env=None):
        env = {"PATH": self.spy_bindir(), "HOME": self.home}
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            [sys.executable, SCRIPT, *args],
            capture_output=True, text=True, env=env)


class FreshCacheSkipsLoginTest(DriveAuthCacheTestBase):
    def test_fresh_auth_file_skips_the_login_worker(self):
        # No `authCacheTtlHours` override: the default 8h TTL applies, and
        # the auth file's mtime (just written) is well inside it.
        self.write_target_config()
        auth_path = self.auth_path()
        self.write_json(auth_path, {"cookies": ["cached"]})

        spy_log = os.path.join(self.tmp, "spy.json")
        r = self.run_cli(
            "login", "app", extra_env={"DRIVE_TEST_SPY_LOG": spy_log})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(
            os.path.isfile(spy_log),
            "the login worker ran despite a fresh, in-TTL cache")
        with open(auth_path, encoding="utf-8") as fh:
            self.assertEqual(json.load(fh), {"cookies": ["cached"]})


class ExpiredCacheReLoginsTest(DriveAuthCacheTestBase):
    def test_expired_auth_file_runs_the_login_worker_and_overwrites_it(self):
        self.write_target_config(ttl_hours=1)
        auth_path = self.auth_path()
        self.write_json(auth_path, {"cookies": ["stale"]})
        old = time.time() - 2 * 3600  # 2h old, past the 1h TTL
        os.utime(auth_path, (old, old))

        spy_log = os.path.join(self.tmp, "spy.json")
        r = self.run_cli(
            "login", "app", extra_env={"DRIVE_TEST_SPY_LOG": spy_log})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(
            os.path.isfile(spy_log),
            "the login worker never ran for an expired cache")
        with open(auth_path, encoding="utf-8") as fh:
            self.assertEqual(json.load(fh), {"cookies": ["fresh"]})


class FailedLoginLeavesCacheUntouchedTest(DriveAuthCacheTestBase):
    def test_failed_login_leaves_the_previous_auth_file_untouched(self):
        self.write_target_config(ttl_hours=1)
        auth_path = self.auth_path()
        self.write_json(auth_path, {"cookies": ["previous"]})
        old = time.time() - 2 * 3600  # past the 1h TTL, so login is tried
        os.utime(auth_path, (old, old))

        r = self.run_cli(
            "login", "app", extra_env={"DRIVE_TEST_SPY_FAIL": "1"})
        self.assertNotEqual(r.returncode, 0)
        # The previous cache is exactly as it was — never partially
        # overwritten, never deleted.
        with open(auth_path, encoding="utf-8") as fh:
            self.assertEqual(json.load(fh), {"cookies": ["previous"]})
        # The failure names a debug screenshot path (drive-auth-cache).
        self.assertIn("screenshot", r.stderr.lower())


if __name__ == "__main__":
    unittest.main()
