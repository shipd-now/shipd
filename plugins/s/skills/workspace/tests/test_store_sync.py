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
import time
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
    def diverge(self, local_body="local\n", upstream_body="up\n",
                same_file=False, upstream_name=None):
        """A clone with one unpushed local commit and an upstream that moved
        on with one commit of its own. Returns ``(remote, ws)``."""
        remote = self.make_remote()
        ws = self.make_clone(remote)
        local_name = "index.md" if same_file else "page.md"
        self.write(os.path.join(ws, ".shipd", "wiki", local_name), local_body)
        _git("-C", ws, "add", "-A")
        _git("-C", ws, "commit", "-q", "-m", "local change")

        other = self.make_clone(remote, name="other")
        up_name = upstream_name or (
            "index.md" if same_file else "upstream.md")
        self.write(os.path.join(other, ".shipd", "wiki", up_name),
                   upstream_body)
        _git("-C", other, "add", "-A")
        _git("-C", other, "commit", "-q", "-m", "upstream change")
        _git("-C", other, "push", "-q", "origin", "main")
        return remote, ws

    def test_divergent_upstream_is_rebased_and_pushed(self):
        """store-sync-hook: `A divergent upstream is rebased and pushed`."""
        remote, ws = self.diverge()

        rc, out, err = self.run_hook("SessionStart", ws)
        self.assertEqual(rc, 0, err)
        self.assertEqual(out, "")
        self.assertEqual(self.local_log(ws)[:2],
                         ["local change", "upstream change"])
        remote_log = self.remote_log(remote)
        self.assertIn("local change", remote_log)
        self.assertIn("upstream change", remote_log)

    def test_conflicting_rebase_aborts_and_warns(self):
        """store-sync-hook: `A conflicting rebase aborts and warns`."""
        remote, ws = self.diverge(
            local_body="local line\n", upstream_body="upstream line\n",
            same_file=True)
        before = subprocess.run(
            ["git", "-C", ws, "rev-parse", "HEAD"], capture_output=True,
            text=True, check=True).stdout.strip()

        rc, out, err = self.run_hook("SessionStart", ws)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")
        self.assertEqual(len(err.strip().splitlines()), 1, err)
        after = subprocess.run(
            ["git", "-C", ws, "rev-parse", "HEAD"], capture_output=True,
            text=True, check=True).stdout.strip()
        self.assertEqual(after, before)
        git_dir = os.path.join(ws, ".git")
        self.assertFalse(os.path.exists(os.path.join(git_dir, "rebase-merge")))
        self.assertFalse(os.path.exists(os.path.join(git_dir, "rebase-apply")))
        self.assertNotIn("local change", self.remote_log(remote))

    def test_uncommitted_work_survives_the_rebase(self):
        """store-sync-hook: `Uncommitted work survives the rebase`."""
        remote, ws = self.diverge()
        index = os.path.join(ws, ".shipd", "wiki", "index.md")
        self.write(index, "edited but not committed\n")

        rc, _out, err = self.run_hook("SessionStart", ws)
        self.assertEqual(rc, 0, err)
        self.assertIn("local change", self.remote_log(remote))
        self.assertIn("upstream change", self.local_log(ws))
        with open(index, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "edited but not committed\n")
        status = subprocess.run(
            ["git", "-C", ws, "status", "--porcelain"], capture_output=True,
            text=True, check=True).stdout
        self.assertIn(".shipd/wiki/index.md", status)

    def test_uncommitted_work_conflicting_with_upstream_undoes_the_rebase(
            self):
        """An uncommitted edit to a line the upstream commit also changed:
        git reports the rebase as a success although the autostash would not
        re-apply. The hook undoes the rebase — the branch at its prior
        commit, the edit back in the tree and uncommitted, no conflict
        marker, no stash entry left — pushes nothing, and warns once."""
        remote, ws = self.diverge(
            upstream_body="upstream line\n", upstream_name="index.md")
        index = os.path.join(ws, ".shipd", "wiki", "index.md")
        self.write(index, "edited but not committed\n")
        before = subprocess.run(
            ["git", "-C", ws, "rev-parse", "HEAD"], capture_output=True,
            text=True, check=True).stdout.strip()

        rc, out, err = self.run_hook("SessionStart", ws)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")
        self.assertEqual(len(err.strip().splitlines()), 1, err)
        after = subprocess.run(
            ["git", "-C", ws, "rev-parse", "HEAD"], capture_output=True,
            text=True, check=True).stdout.strip()
        self.assertEqual(after, before)
        with open(index, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "edited but not committed\n")
        status = subprocess.run(
            ["git", "-C", ws, "status", "--porcelain"], capture_output=True,
            text=True, check=True).stdout
        self.assertEqual(status.strip(), "M .shipd/wiki/index.md")
        stash = subprocess.run(
            ["git", "-C", ws, "stash", "list"], capture_output=True,
            text=True, check=True).stdout
        self.assertEqual(stash, "")
        self.assertNotIn("local change", self.remote_log(remote))


class DelayedTestCase(StoreSyncTestCase):
    """The helper's delayed mode (shipd-wiki store-push-debounce). ``TMPDIR``
    points into the test's own temp tree, so the token file each helper
    writes is isolated and inspectable."""

    def setUp(self):
        super().setUp()
        self.tokens = os.path.join(self.tmp, "tokens")
        os.makedirs(self.tokens)

    def delayed_env(self):
        env = dict(os.environ)
        env["HOME"] = self.home
        env["TMPDIR"] = self.tokens
        env.pop("USERPROFILE", None)
        return env

    def delayed_argv(self, store, delay):
        return [sys.executable, SCRIPT, "--delayed", store,
                "--delay", str(delay)]

    def run_delayed(self, store, delay=0):
        proc = subprocess.run(
            self.delayed_argv(store, delay), stdin=subprocess.DEVNULL,
            env=self.delayed_env(), stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, timeout=30)
        return proc.returncode, proc.stdout, proc.stderr

    def commit(self, ws, name, body, subject):
        self.write(os.path.join(ws, ".shipd", "wiki", name), body)
        _git("-C", ws, "add", "-A")
        _git("-C", ws, "commit", "-q", "-m", subject)


class TestDelayedPush(DelayedTestCase):
    def test_unpushed_commit_reaches_the_remote(self):
        """store-push-debounce: the delayed helper pushes a local commit."""
        remote = self.make_remote()
        ws = self.make_clone(remote)
        self.commit(ws, "page.md", "local\n", "local change")

        rc, _out, err = self.run_delayed(ws)
        self.assertEqual(rc, 0, err)
        self.assertIn("local change", self.remote_log(remote))

    def test_diverged_store_is_rebased_and_pushed(self):
        """store-push-debounce: the helper integrates as store-sync-hook
        specifies — a diverged store is rebased, then pushed."""
        remote = self.make_remote()
        ws = self.make_clone(remote)
        self.commit(ws, "page.md", "local\n", "local change")
        other = self.make_clone(remote, name="other")
        self.commit(other, "upstream.md", "up\n", "upstream change")
        _git("-C", other, "push", "-q", "origin", "main")

        rc, _out, err = self.run_delayed(ws)
        self.assertEqual(rc, 0, err)
        self.assertEqual(self.local_log(ws)[:2],
                         ["local change", "upstream change"])
        self.assertIn("local change", self.remote_log(remote))

    def test_store_without_origin_exits_zero(self):
        """store-push-debounce: a store with no `origin` is skipped."""
        repo = os.path.join(self.tmp, "solo")
        os.makedirs(repo)
        _git("init", "-q", repo)
        _git("-C", repo, "config", "user.email", "test@example.com")
        _git("-C", repo, "config", "user.name", "Test")
        self.commit(repo, "index.md", "v1\n", "seed")

        rc, out, err = self.run_delayed(repo)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")
        self.assertEqual(err, "")

    def test_non_git_store_exits_zero(self):
        plain = os.path.join(self.tmp, "plain")
        os.makedirs(plain)
        rc, out, err = self.run_delayed(plain)
        self.assertEqual(rc, 0)
        self.assertEqual(err, "")


class TestDelayedDebounce(DelayedTestCase):
    def wait_for_token(self, timeout=10):
        """Return the one token file's content once the first helper has
        written it."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            names = [n for n in os.listdir(self.tokens)
                     if n.startswith("shipd-store-push-")
                     and n.endswith(".token")]
            if names:
                with open(os.path.join(self.tokens, names[0]),
                          encoding="utf-8") as fh:
                    body = fh.read().strip()
                if body:
                    return os.path.join(self.tokens, names[0]), body
            time.sleep(0.05)
        self.fail("the first helper never wrote its token")

    def test_a_burst_of_writes_ends_in_one_push(self):
        """store-push-debounce: `A burst of writes ends in one push`.

        The first helper (delay 2) is superseded by a second (delay 0),
        which pushes. A commit made after the second helper finishes must
        not reach the remote: the first helper, on waking, finds another
        helper's token and exits having run no git."""
        remote = self.make_remote()
        ws = self.make_clone(remote)
        self.commit(ws, "page.md", "one\n", "first write")

        first = subprocess.Popen(
            self.delayed_argv(ws, 2), stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            env=self.delayed_env())
        self.addCleanup(first.kill)
        token_path, first_token = self.wait_for_token()

        rc, _out, err = self.run_delayed(ws, 0)
        self.assertEqual(rc, 0, err)
        with open(token_path, encoding="utf-8") as fh:
            self.assertNotEqual(fh.read().strip(), first_token)
        self.assertIn("first write", self.remote_log(remote))

        self.commit(ws, "late.md", "late\n", "late write")
        self.assertEqual(first.wait(timeout=30), 0)
        self.assertNotIn("late write", self.remote_log(remote))


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
