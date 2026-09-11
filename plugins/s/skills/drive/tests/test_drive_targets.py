#!/usr/bin/env python3
"""Unit tests for `drive.py`'s target/credential resolution
(drive-targets-config): a repository-level `<content-dir>/drive/targets.json`
overrides the same-named entry in the user-level `~/.shipd/drive/targets.json`;
the `env` and `command` auth recipes each resolve both secrets; the login
worker's argv never carries a resolved secret while its environment does; and
naming a target declared in neither file is a single `Error:` line with a
non-zero exit.

`drive.py` never imports `playwright` and shells to the login worker only
through `uv run`, so these tests never touch a real browser: the `uv` binary
on the restricted test `PATH` is a small Python spy script (its shebang is
this test process's own interpreter, so it needs nothing else on `PATH`)
that records its invocation (argv and environment) to a log file and, in
place of the real worker, writes a placeholder storage-state file at the
requested `--out` path — enough for `drive.py login`'s success path without
any Playwright involved. This mirrors `test_drive_cli.py`'s restricted-PATH
approach, extended with a behavior-recording stub rather than a bare
presence stub, since these scenarios turn on *what* the worker was invoked
with, not merely that a `uv`-named file exists on `PATH`."""

import json
import os
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

out_path = None
if "--out" in argv:
    out_path = argv[argv.index("--out") + 1]
if out_path:
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump({{"cookies": []}}, fh)

print(json.dumps({{"ok": True, "storageState": out_path}}))
"""


class DriveTargetsTestBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="drive-targets-")
        self.home = os.path.join(self.tmp, "home")
        self.repo = os.path.join(self.tmp, "repo")
        os.makedirs(self.home, exist_ok=True)
        os.makedirs(self.repo, exist_ok=True)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write_json(self, path, data):
        d = os.path.dirname(path)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh)

    def user_targets_path(self):
        return os.path.join(self.home, ".shipd", "drive", "targets.json")

    def repo_targets_path(self):
        # No `.shipd-config.json` is written in these tests, so the content
        # directory resolves to its built-in default, `.shipd`
        # (shipd-config content-dir-key).
        return os.path.join(self.repo, ".shipd", "drive", "targets.json")

    def spy_bindir(self, extra_tools=()):
        """A restricted-PATH directory whose `uv` is the recording spy
        script above, plus one bare exit-0 stub per name in `extra_tools`
        (mirroring `_stubs.stub_bindir`'s shape for anything the login path
        also probes for, e.g. `ffmpeg`)."""
        d = os.path.join(self.tmp, "bin")
        os.makedirs(d, exist_ok=True)
        uv_path = os.path.join(d, "uv")
        with open(uv_path, "w", encoding="utf-8") as fh:
            fh.write(_UV_SPY_TEMPLATE.format(python=sys.executable))
        os.chmod(uv_path, os.stat(uv_path).st_mode
                 | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        for tool in extra_tools:
            path = os.path.join(d, tool)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("#!/bin/sh\nexit 0\n")
            os.chmod(path, os.stat(path).st_mode
                     | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        return d

    def run_cli(self, *args, path_dir=None, extra_env=None):
        env = {
            "PATH": path_dir or self.spy_bindir(),
            "HOME": self.home,
        }
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            [sys.executable, SCRIPT, *args],
            capture_output=True, text=True, env=env, cwd=self.repo)


class RepositoryOverridesUserTargetTest(DriveTargetsTestBase):
    def test_repository_entry_overrides_user_entry(self):
        self.write_json(self.user_targets_path(), {
            "default": "app",
            "targets": {
                "app": {"url": "https://user.example",
                        "auth": {"kind": "none"}},
            },
        })
        self.write_json(self.repo_targets_path(), {
            "targets": {
                "app": {"url": "https://repo.example",
                        "auth": {"kind": "none"}},
            },
        })

        r = self.run_cli("targets")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("https://repo.example", r.stdout)
        self.assertNotIn("https://user.example", r.stdout)


class AuthRecipeResolutionTest(DriveTargetsTestBase):
    def test_env_auth_recipe_resolves_both_secrets(self):
        self.write_json(self.user_targets_path(), {
            "targets": {
                "app": {
                    "url": "https://app.example",
                    "auth": {
                        "kind": "env",
                        "username": "DRIVE_TEST_USERNAME",
                        "password": "DRIVE_TEST_PASSWORD",
                    },
                },
            },
        })

        r = self.run_cli(
            "login", "app",
            extra_env={
                "DRIVE_TEST_USERNAME": "env-user",
                "DRIVE_TEST_PASSWORD": "env-pass",
            })
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_command_auth_recipe_resolves_both_secrets_and_argv_stays_clean(
            self):
        secret = "spy-password-should-never-appear-in-argv"
        self.write_json(self.user_targets_path(), {
            "targets": {
                "app": {
                    "url": "https://app.example",
                    "auth": {
                        "kind": "command",
                        "username": [sys.executable, "-c",
                                     "print('spy-user')"],
                        "password": [sys.executable, "-c",
                                     "print(%r)" % secret],
                    },
                },
            },
        })

        spy_log = os.path.join(self.tmp, "spy.json")
        r = self.run_cli(
            "login", "app", extra_env={"DRIVE_TEST_SPY_LOG": spy_log})
        self.assertEqual(r.returncode, 0, r.stderr)

        self.assertTrue(os.path.isfile(spy_log),
                         "the login worker (spied `uv run ...`) never ran")
        with open(spy_log, encoding="utf-8") as fh:
            spied = json.load(fh)

        # The worker's argv is the login worker contract's public surface —
        # a resolved secret must never appear there.
        argv_text = " ".join(spied["argv"])
        self.assertNotIn(secret, argv_text)
        # ...while its environment is exactly how drive.py is required to
        # pass it (drive-targets-config: "through its environment only").
        self.assertEqual(spied["env"].get("DRIVE_LOGIN_PASSWORD"), secret)


class UnknownTargetTest(DriveTargetsTestBase):
    def test_unknown_target_is_a_single_error_line(self):
        self.write_json(self.user_targets_path(), {
            "targets": {
                "app": {"url": "https://app.example",
                        "auth": {"kind": "none"}},
            },
        })

        r = self.run_cli("login", "does-not-exist")
        self.assertNotEqual(r.returncode, 0)
        stderr_lines = [ln for ln in r.stderr.splitlines() if ln.strip()]
        self.assertEqual(len(stderr_lines), 1, r.stderr)
        self.assertTrue(stderr_lines[0].startswith("Error: "), r.stderr)
        self.assertIn("does-not-exist", stderr_lines[0])
        self.assertEqual(r.stdout, "")


if __name__ == "__main__":
    unittest.main()
