#!/usr/bin/env python3
"""Tests for store_sync.py — the session-boundary hook that fetches,
fast-forward merges, and pushes a resolved workspace or external store's git
checkout (shipd-wiki store-sync-hook).

Every case runs the script as a real subprocess against real local git repos
(a bare "origin" plus one or more working clones), so the fixture proves the
actual git plumbing rather than a mock of it. ``HOME`` is overridden per test
so a developer's own ``~/.shipd-config.json`` never colours a result.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.normpath(os.path.join(HERE, "..", "scripts", "store_sync.py"))


def _git(*args):
    subprocess.run(["git", *args], capture_output=True, text=True, check=True)


class StoreSyncTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="store-sync-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.home = os.path.join(self.tmp, "home")
        os.makedirs(self.home)

    def write_config(self, directory, data):
        os.makedirs(directory, exist_ok=True)
        with open(os.path.join(directory, ".shipd-config.json"), "w",
                  encoding="utf-8") as fh:
            fh.write(data if isinstance(data, str) else json.dumps(data))

    def write(self, path, body):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(body)

    def make_remote(self):
        """A bare 'origin' repo seeded with one commit on `main`: a
        workspace-declaring config plus a wiki page."""
        remote = os.path.join(self.tmp, "remote.git")
        _git("init", "-q", "--bare", "-b", "main", remote)
        seed = os.path.join(self.tmp, "seed")
        _git("clone", "-q", remote, seed)
        _git("-C", seed, "config", "user.email", "test@example.com")
        _git("-C", seed, "config", "user.name", "Test")
        self.write_config(seed, {"workspace": {}})
        self.write(os.path.join(seed, ".shipd", "wiki", "index.md"), "v1\n")
        _git("-C", seed, "add", "-A")
        _git("-C", seed, "commit", "-q", "-m", "seed")
        _git("-C", seed, "push", "-q", "origin", "main")
        return remote

    def make_clone(self, remote, name="ws"):
        """A working clone of ``remote`` with an in-repo git identity."""
        ws = os.path.join(self.tmp, name)
        _git("clone", "-q", remote, ws)
        _git("-C", ws, "config", "user.email", "test@example.com")
        _git("-C", ws, "config", "user.name", "Test")
        return ws

    def run_hook(self, event, cwd):
        env = dict(os.environ)
        env["HOME"] = self.home
        env.pop("USERPROFILE", None)
        payload = json.dumps({"hook_event_name": event, "cwd": cwd})
        proc = subprocess.run(
            [sys.executable, SCRIPT], input=payload, cwd=cwd, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            timeout=30)
        return proc.returncode, proc.stdout, proc.stderr

    def remote_log(self, remote, ref="main"):
        result = subprocess.run(
            ["git", "-C", remote, "log", "--format=%s", ref],
            capture_output=True, text=True, check=True)
        return result.stdout.strip().split("\n")

    def local_log(self, ws, ref="HEAD"):
        result = subprocess.run(
            ["git", "-C", ws, "log", "--format=%s", ref],
            capture_output=True, text=True, check=True)
        return result.stdout.strip().split("\n")


class TestSessionStart(StoreSyncTestCase):
    def test_fast_forward_merge_plus_push(self):
        remote = self.make_remote()
        ws = self.make_clone(remote)
        # One unpushed local commit.
        self.write(os.path.join(ws, ".shipd", "wiki", "page.md"), "local\n")
        _git("-C", ws, "add", "-A")
        _git("-C", ws, "commit", "-q", "-m", "local change")

        # A collaborator who already has ws's unpublished commit (e.g.
        # through a shared checkout) builds on top of it and publishes both
        # to origin — the only git-mechanically valid way for ws's own
        # unpushed commit to stay fast-forwardable once origin has moved on.
        other = os.path.join(self.tmp, "other")
        _git("clone", "-q", ws, other)
        _git("-C", other, "remote", "set-url", "origin", remote)
        _git("-C", other, "config", "user.email", "test@example.com")
        _git("-C", other, "config", "user.name", "Test")
        self.write(os.path.join(other, ".shipd", "wiki", "upstream.md"), "up\n")
        _git("-C", other, "add", "-A")
        _git("-C", other, "commit", "-q", "-m", "upstream change")
        _git("-C", other, "push", "-q", "origin", "main")

        rc, out, _err = self.run_hook("SessionStart", ws)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")
        self.assertIn("upstream change", self.local_log(ws))
        self.assertIn("local change", self.remote_log(remote))
        self.assertIn("upstream change", self.remote_log(remote))


class TestSessionEnd(StoreSyncTestCase):
    def test_push_pushes_pending_commits(self):
        remote = self.make_remote()
        ws = self.make_clone(remote)
        self.write(os.path.join(ws, ".shipd", "wiki", "page.md"), "local\n")
        _git("-C", ws, "add", "-A")
        _git("-C", ws, "commit", "-q", "-m", "local change")

        rc, out, _err = self.run_hook("SessionEnd", ws)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")
        self.assertIn("local change", self.remote_log(remote))


class TestDivergentUpstream(StoreSyncTestCase):
    def test_divergent_upstream_warns_and_changes_nothing(self):
        remote = self.make_remote()
        ws = self.make_clone(remote)
        self.write(os.path.join(ws, ".shipd", "wiki", "page.md"), "local\n")
        _git("-C", ws, "add", "-A")
        _git("-C", ws, "commit", "-q", "-m", "local change")
        before_local = self.local_log(ws)

        other = self.make_clone(remote, name="other")
        self.write(os.path.join(other, ".shipd", "wiki", "upstream.md"), "up\n")
        _git("-C", other, "add", "-A")
        _git("-C", other, "commit", "-q", "-m", "upstream change")
        _git("-C", other, "push", "-q", "origin", "main")

        rc, out, err = self.run_hook("SessionStart", ws)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")
        self.assertTrue(err.strip())
        self.assertEqual(self.local_log(ws), before_local)
        self.assertNotIn("local change", self.remote_log(remote))


class TestStoreSyncDisabled(StoreSyncTestCase):
    def test_store_sync_false_runs_no_git(self):
        remote = self.make_remote()
        ws = self.make_clone(remote)
        self.write_config(ws, {"workspace": {}, "store_sync": False})
        self.write(os.path.join(ws, ".shipd", "wiki", "page.md"), "local\n")
        _git("-C", ws, "add", "-A")
        _git("-C", ws, "commit", "-q", "-m", "local change")

        rc, out, err = self.run_hook("SessionStart", ws)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")
        self.assertEqual(err, "")
        self.assertNotIn("local change", self.remote_log(remote))


class TestFallbackStore(StoreSyncTestCase):
    def test_in_repo_fallback_store_runs_no_git(self):
        # No workspace declared anywhere: a plain repo with its own content
        # directory is the repo-local fallback store, never synced.
        repo = os.path.join(self.tmp, "repo")
        os.makedirs(repo)
        _git("init", "-q", repo)
        _git("-C", repo, "config", "user.email", "test@example.com")
        _git("-C", repo, "config", "user.name", "Test")
        self.write(os.path.join(repo, ".shipd", "wiki", "index.md"), "v1\n")
        _git("-C", repo, "add", "-A")
        _git("-C", repo, "commit", "-q", "-m", "seed")

        rc, out, err = self.run_hook("SessionStart", repo)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")
        self.assertEqual(err, "")


class TestNonGitStore(StoreSyncTestCase):
    def test_non_git_store_exits_zero(self):
        repo = os.path.join(self.tmp, "plain")
        self.write_config(repo, {"workspace": {}})
        self.write(os.path.join(repo, ".shipd", "wiki", "index.md"), "v1\n")

        rc, out, err = self.run_hook("SessionStart", repo)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")
        self.assertEqual(err, "")


if __name__ == "__main__":
    unittest.main()


class TestUnknownEvent(StoreSyncTestCase):
    def test_unrecognized_event_runs_no_git(self):
        """store-sync-hook: only the two registered events reach the network.

        A payload naming another event — or none at all — must not be read as
        a push request.
        """
        remote = self.make_remote()
        ws = self.make_clone(remote)
        self.write(os.path.join(ws, ".shipd", "wiki", "page.md"), "local\n")
        _git("-C", ws, "add", "-A")
        _git("-C", ws, "commit", "-q", "-m", "local change")

        for event in ("PreToolUse", None):
            rc, out, err = self.run_hook(event, ws)
            self.assertEqual(rc, 0)
            self.assertEqual(out, "")
            self.assertEqual(err, "")
            self.assertNotIn("local change", self.remote_log(remote))


class TestNonOriginUpstream(StoreSyncTestCase):
    def test_fetch_targets_the_upstream_remote(self):
        """store-sync-hook: session start fetches the remote the branch's
        upstream tracks, not a hardcoded `origin`.

        The clone keeps an `origin` (so the hook's gate passes) but tracks a
        second remote, `publish`, which alone carries the upstream commit. A
        hook fetching `origin` would never see it.
        """
        remote = self.make_remote()
        ws = self.make_clone(remote)
        publish = os.path.join(self.tmp, "publish.git")
        _git("clone", "-q", "--bare", ws, publish)
        _git("-C", ws, "remote", "add", "publish", publish)

        # Track `publish` BEFORE it moves, so ws's own refs are up to date
        # and only the hook's fetch can discover the commit added below.
        _git("-C", ws, "fetch", "-q", "publish")
        _git("-C", ws, "branch", "--set-upstream-to", "publish/main", "main")

        other = os.path.join(self.tmp, "other")
        _git("clone", "-q", publish, other)
        _git("-C", other, "config", "user.email", "test@example.com")
        _git("-C", other, "config", "user.name", "Test")
        self.write(os.path.join(other, ".shipd", "wiki", "upstream.md"), "up\n")
        _git("-C", other, "add", "-A")
        _git("-C", other, "commit", "-q", "-m", "publish change")
        _git("-C", other, "push", "-q", "origin", "main")

        rc, _out, err = self.run_hook("SessionStart", ws)
        self.assertEqual(rc, 0, err)
        self.assertIn("publish change", self.local_log(ws))
