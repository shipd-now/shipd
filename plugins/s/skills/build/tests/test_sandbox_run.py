#!/usr/bin/env python3
"""Tests for sandbox-run.sh: the sandbox env, banner, persistent root,
leak refusal and the project ``sandbox`` config declaration.

The wrapper is driven as a black box by subprocess against a throwaway git
repo. Every run passes a temp fake ``HOME`` and a separate temp ``TMPDIR``, so
no test ever touches the real home directory."""

import hashlib
import json
import os
import shutil
import stat
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.normpath(os.path.join(HERE, "..", "scripts", "sandbox-run.sh"))


class SandboxRunBase(unittest.TestCase):
    def setUp(self):
        self.base = os.path.realpath(tempfile.mkdtemp(prefix="sbx-test-"))
        self.home = os.path.join(self.base, "home")
        self.tmp = os.path.join(self.base, "tmp")
        self.repo = os.path.join(self.base, "repo")
        for d in (self.home, self.tmp, self.repo):
            os.makedirs(d)
        self.git_init(self.repo)

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)

    def git_init(self, repo):
        subprocess.run(["git", "init", "-q", repo], check=True,
                       env=self.env())

    def env(self, **extra):
        env = {"PATH": os.environ["PATH"], "HOME": self.home,
               "TMPDIR": self.tmp}
        env.update(extra)
        return env

    def root_for(self, repo=None):
        digest = hashlib.sha256(
            os.path.realpath(repo or self.repo).encode()).hexdigest()[:12]
        return os.path.join(self.tmp, "shipd-sandbox", digest)

    def run_sbx(self, *args, env=None, cwd=None):
        return subprocess.run(
            ["bash", SCRIPT] + list(args), cwd=cwd or self.repo,
            env=env if env is not None else self.env(),
            capture_output=True, text=True)

    def write_config(self, data, repo=None):
        with open(os.path.join(repo or self.repo, ".shipd-config.json"),
                  "w", encoding="utf-8") as fh:
            json.dump(data, fh)


class EntryPointTest(SandboxRunBase):
    def test_home_write_lands_in_sandbox(self):
        sentinel = os.path.join(self.home, ".review-bot", "config.json")
        os.makedirs(os.path.dirname(sentinel))
        with open(sentinel, "w") as fh:
            fh.write("real")
        res = self.run_sbx(
            "mkdir -p ~/.review-bot && echo sandboxed > "
            "~/.review-bot/config.json")
        self.assertEqual(res.returncode, 0, res.stderr)
        root = self.root_for()
        with open(os.path.join(root, "home", ".review-bot",
                               "config.json")) as fh:
            self.assertEqual(fh.read().strip(), "sandboxed")
        with open(sentinel) as fh:
            self.assertEqual(fh.read(), "real")

    def test_banner_and_flag(self):
        res = self.run_sbx("echo $SHIPD_SANDBOX")
        self.assertEqual(res.stdout.strip(), "1")
        self.assertEqual(res.stderr.splitlines()[0],
                         "sandbox-run: root=" + self.root_for())

    def test_exit_status_propagates(self):
        self.assertEqual(self.run_sbx("exit 7").returncode, 7)

    def test_credentials_scrubbed_and_config_dir(self):
        res = self.run_sbx(
            "env", env=self.env(GH_TOKEN="a", GITHUB_TOKEN="b",
                                GH_ENTERPRISE_TOKEN="c",
                                GITHUB_ENTERPRISE_TOKEN="d"))
        self.assertEqual(res.returncode, 0, res.stderr)
        names = [l.split("=", 1)[0] for l in res.stdout.splitlines()]
        for name in ("GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN",
                     "GITHUB_ENTERPRISE_TOKEN"):
            self.assertNotIn(name, names)
        root = self.root_for()
        lines = res.stdout.splitlines()
        self.assertIn("GH_CONFIG_DIR=" + root + "/home/.config/gh", lines)
        self.assertIn("HOME=" + root + "/home", lines)
        self.assertIn("TMPDIR=" + root + "/tmp", lines)
        self.assertIn("GIT_CONFIG_NOSYSTEM=1", lines)
        self.assertIn("GIT_CONFIG_GLOBAL=" + root + "/home/.gitconfig", lines)
        self.assertIn("SHIPD_SANDBOX_ROOT=" + root, lines)
        self.assertIn("XDG_STATE_HOME=" + root + "/home/.local/state", lines)

    def test_uncreatable_root_exits_3(self):
        blocker = os.path.join(self.base, "blocker")
        with open(blocker, "w") as fh:
            fh.write("x")
        bad_tmp = os.path.join(blocker, "sub")
        marker = os.path.join(self.base, "ran")
        res = self.run_sbx("touch " + marker,
                           env=self.env(TMPDIR=bad_tmp))
        self.assertEqual(res.returncode, 3)
        self.assertIn("sandbox-run: cannot create sandbox root", res.stderr)
        self.assertIn(bad_tmp, res.stderr)
        self.assertFalse(os.path.exists(marker))

    def test_root_inside_real_home_exits_3(self):
        inner_tmp = os.path.join(self.home, "tmpdir")
        os.makedirs(inner_tmp)
        res = self.run_sbx("true", env=self.env(TMPDIR=inner_tmp))
        self.assertEqual(res.returncode, 3)
        self.assertIn("is inside the real HOME", res.stderr)

    def test_state_persists_until_reset(self):
        self.assertEqual(self.run_sbx("echo hi > ~/x").returncode, 0)
        res = self.run_sbx("cat ~/x")
        self.assertEqual(res.stdout.strip(), "hi")
        reset = self.run_sbx("--reset")
        self.assertEqual(reset.returncode, 0)
        self.assertEqual(reset.stdout.strip(), self.root_for())
        self.assertFalse(os.path.exists(self.root_for()))
        self.assertNotEqual(self.run_sbx("cat ~/x").returncode, 0)

    def test_print_root_creates_nothing(self):
        res = self.run_sbx("--print-root")
        self.assertEqual(res.returncode, 0)
        self.assertEqual(res.stdout.strip(), self.root_for())
        self.assertFalse(os.path.exists(self.root_for()))


class LeakRefusalTest(SandboxRunBase):
    def test_pre_expanded_home_refused(self):
        target = os.path.join(self.home, ".review-bot", "config.json")
        res = self.run_sbx("mkdir -p %s && echo x > %s" % (
            os.path.dirname(target), target))
        self.assertEqual(res.returncode, 2)
        self.assertIn("sandbox-run: command names the real HOME outside "
                      "the repo:", res.stderr)
        self.assertFalse(os.path.exists(target))

    def test_repo_path_under_home_allowed(self):
        repo = os.path.join(self.home, "proj")
        os.makedirs(repo)
        self.git_init(repo)
        res = self.run_sbx("echo ran %s/scripts/tool.sh" % repo, cwd=repo)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("ran", res.stdout)

    def test_sibling_of_repo_under_home_refused(self):
        repo = os.path.join(self.home, "proj")
        os.makedirs(repo)
        self.git_init(repo)
        res = self.run_sbx("cat %s-other/x" % repo, cwd=repo)
        self.assertEqual(res.returncode, 2)
        self.assertIn("command names the real HOME outside the repo",
                      res.stderr)

    def test_unquoted_argv_refused(self):
        for args in (("echo", "hi"), ()):
            res = self.run_sbx(*args)
            self.assertEqual(res.returncode, 2)
            self.assertIn("sandbox-run: pass the command as one quoted "
                          "string", res.stderr)

    def test_home_pointing_var_scrubbed(self):
        res = self.run_sbx(
            "env", env=self.env(
                REVIEW_BOT_HOME=os.path.join(self.home, ".review-bot")))
        self.assertEqual(res.returncode, 0, res.stderr)
        names = [l.split("=", 1)[0] for l in res.stdout.splitlines()]
        self.assertNotIn("REVIEW_BOT_HOME", names)


class ProjectConfigTest(SandboxRunBase):
    def test_declared_env_points_into_state(self):
        self.write_config({"sandbox": {"env": {"REVIEW_BOT_HOME":
                                               "review-bot"}}})
        res = self.run_sbx("echo $REVIEW_BOT_HOME")
        self.assertEqual(res.returncode, 0, res.stderr)
        want = os.path.join(self.root_for(), "state", "review-bot")
        self.assertEqual(res.stdout.strip(), want)
        self.assertTrue(os.path.isdir(os.path.dirname(want)))

    def test_fake_bin_shadows_real_tool(self):
        fb = os.path.join(self.repo, "tests", "fake-bin")
        os.makedirs(fb)
        gh = os.path.join(fb, "gh")
        with open(gh, "w") as fh:
            fh.write("#!/bin/sh\necho fake-gh\n")
        os.chmod(gh, os.stat(gh).st_mode | stat.S_IXUSR)
        self.write_config({"sandbox": {"fake_bin": "tests/fake-bin"}})
        res = self.run_sbx("gh api user")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(res.stdout.strip(), "fake-gh")

    def test_missing_fake_bin_exits_3(self):
        self.write_config({"sandbox": {"fake_bin": "tests/nope"}})
        marker = os.path.join(self.base, "ran")
        res = self.run_sbx("touch " + marker)
        self.assertEqual(res.returncode, 3)
        self.assertIn("sandbox-run: fake_bin", res.stderr)
        self.assertIn("does not exist", res.stderr)
        self.assertFalse(os.path.exists(marker))


if __name__ == "__main__":
    unittest.main()
