#!/usr/bin/env python3
"""Unit tests for `drive.py`'s `probe` verb (drive-skill-flow): the control
CLI wires the read-only sampler to `browser_worker.py probe` the same way
`login`/`record` wire their own workers — resolving the configured default
target's url and cached storage state, invoking the worker through `uv run`,
and printing the artifact paths it reports.

Like `test_drive_auth_cache.py`, `uv` on the restricted test `PATH` is a
small Python spy script standing in for the injectable `run` subprocess seam
(never a real Playwright worker): it records its invocation to a log file
when `DRIVE_TEST_SPY_LOG` is set, writes the probe evidence files the real
`browser_worker.py probe` would have written, and prints the same `{"ok":
true, ...}` reply on success. `DRIVE_TEST_SPY_FAIL` switches it into a
failure mode that prints an `Error:` line to stderr and exits non-zero,
mirroring the worker's own failure contract."""

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
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


out_dir = _arg("--out")

if os.environ.get("DRIVE_TEST_SPY_FAIL"):
    print("Error: probe failed: simulated failure", file=sys.stderr)
    sys.exit(1)

accessibility = os.path.join(out_dir, "accessibility.json")
testids = os.path.join(out_dir, "testids.json")
html = os.path.join(out_dir, "page.html")
screenshot = os.path.join(out_dir, "screenshot.png")

os.makedirs(out_dir, exist_ok=True)
with open(accessibility, "w", encoding="utf-8") as fh:
    json.dump({{"role": "WebArea"}}, fh)
with open(testids, "w", encoding="utf-8") as fh:
    json.dump([], fh)
with open(html, "w", encoding="utf-8") as fh:
    fh.write("<html></html>")
with open(screenshot, "wb") as fh:
    fh.write(b"")

print(json.dumps({{
    "ok": True,
    "accessibility": accessibility,
    "testids": testids,
    "html": html,
    "screenshot": screenshot,
}}))
"""


class DriveProbeTestBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="drive-probe-")
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

    def write_target_config(self):
        self.write_json(self.user_targets_path(), {
            "default": "app",
            "targets": {
                "app": {"url": "https://app.example",
                        "auth": {"kind": "none"}},
            },
        })

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


class ProbeInvokesWorkerTest(DriveProbeTestBase):
    def test_probe_carries_the_resolved_target_url_and_cached_auth(self):
        self.write_target_config()
        auth_path = self.auth_path()
        self.write_json(auth_path, {"cookies": ["cached"]})

        spy_log = os.path.join(self.tmp, "spy.json")
        r = self.run_cli(
            "probe", extra_env={"DRIVE_TEST_SPY_LOG": spy_log})
        self.assertEqual(r.returncode, 0, r.stderr)

        with open(spy_log, encoding="utf-8") as fh:
            spy = json.load(fh)
        argv = spy["argv"]
        self.assertIn("probe", argv)
        self.assertEqual(argv[argv.index("--url") + 1],
                         "https://app.example")
        self.assertEqual(argv[argv.index("--storage-state") + 1], auth_path)

    def test_probe_prints_the_artifact_paths_the_worker_reports(self):
        self.write_target_config()
        r = self.run_cli("probe")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("accessibility.json", r.stdout)
        self.assertIn("testids.json", r.stdout)
        self.assertIn("page.html", r.stdout)
        self.assertIn("screenshot.png", r.stdout)


class ProbeWorkerFailureTest(DriveProbeTestBase):
    def test_a_worker_failure_is_one_error_line_and_nonzero_exit(self):
        self.write_target_config()
        r = self.run_cli("probe", extra_env={"DRIVE_TEST_SPY_FAIL": "1"})
        self.assertNotEqual(r.returncode, 0)
        error_lines = [ln for ln in r.stderr.splitlines()
                       if ln.startswith("Error:")]
        self.assertEqual(len(error_lines), 1, r.stderr)


if __name__ == "__main__":
    unittest.main()
