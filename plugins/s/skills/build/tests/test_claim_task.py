#!/usr/bin/env python3
"""Tests for claim_task.sh group-aware claiming: parallel groups, barrier
blocking, unready-group emptiness, and untagged (fully sequential) behavior.

The script is driven as a black box via subprocess against a throwaway temp
directory laid out as ``.shipd/planned/<change>/tasks.md`` (run with that temp
root as cwd) — never against the real repo change dirs."""

import os
import shutil
import subprocess
import tempfile
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.normpath(os.path.join(HERE, "..", "scripts", "claim_task.sh"))
CHANGE = "demo"


class ClaimScriptTestBase(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="claim-test-")
        self.change_dir = os.path.join(
            self.root, ".shipd", "planned", CHANGE)
        os.makedirs(self.change_dir)
        self.tasks = os.path.join(self.change_dir, "tasks.md")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def write_tasks(self, text):
        with open(self.tasks, "w", encoding="utf-8") as fh:
            fh.write(text)

    def claim(self):
        return subprocess.run(
            ["bash", SCRIPT, "claim", CHANGE],
            cwd=self.root, capture_output=True, text=True)

    def cmd(self, action, *extra):
        return subprocess.run(
            ["bash", SCRIPT, action, CHANGE, *extra],
            cwd=self.root, capture_output=True, text=True)

    def id_of(self, completed):
        """Parse the leading ordinal ID from a `ID<TAB>TEXT` stdout line."""
        out = completed.stdout.strip()
        if not out:
            return None
        return out.split("\t", 1)[0]


class ParallelGroupTest(ClaimScriptTestBase):
    def test_group_members_claim_concurrently(self):
        self.write_tasks(
            "## 1. Group\n"
            "- [ ] 1.1 [P1] first\n"
            "- [ ] 1.2 [P1] second\n")
        results = {}
        lock = threading.Lock()

        def worker(key):
            r = self.claim()
            with lock:
                results[key] = r

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        ids = sorted(
            self.id_of(results[i]) for i in range(2)
            if self.id_of(results[i]) is not None)
        # Both claims succeed and get distinct ordinal IDs (no double-claim).
        self.assertEqual(ids, ["1", "2"])
        with open(self.tasks, encoding="utf-8") as fh:
            body = fh.read()
        self.assertEqual(body.count("- [~]"), 2)
        self.assertEqual(body.count("- [ ]"), 0)


class BarrierTest(ClaimScriptTestBase):
    def setUp(self):
        super().setUp()
        self.write_tasks(
            "## 1. Work\n"
            "- [ ] 1.1 [P1] a\n"
            "- [ ] 1.2 [P1] b\n"
            "- [ ] 2.1 barrier task\n"
            "- [ ] 3.1 [P2] c\n")

    def test_barrier_blocks_until_prior_group_done(self):
        # Claim both P1 tasks; the barrier is not yet ready.
        self.assertEqual(self.id_of(self.claim()), "1")
        self.assertEqual(self.id_of(self.claim()), "2")
        blocked = self.claim()
        self.assertEqual(blocked.stdout.strip(), "")
        self.assertEqual(blocked.returncode, 0)

        # Finish the P1 group -> the barrier becomes claimable.
        self.cmd("complete", "1")
        self.cmd("complete", "2")
        self.assertEqual(self.id_of(self.claim()), "3")

        # While the barrier is in progress, the P2 group stays blocked.
        blocked2 = self.claim()
        self.assertEqual(blocked2.stdout.strip(), "")
        self.assertEqual(blocked2.returncode, 0)

        # Complete the barrier -> P2 unlocks.
        self.cmd("complete", "3")
        self.assertEqual(self.id_of(self.claim()), "4")


class UnreadyGroupTest(ClaimScriptTestBase):
    def test_unready_group_prints_nothing_but_pending_remains(self):
        # Only pending task is P2, whose predecessor group P1 is not done.
        self.write_tasks(
            "## 1. Work\n"
            "- [~] 1.1 [P1] a\n"
            "- [ ] 2.1 [P2] b\n")
        r = self.claim()
        self.assertEqual(r.stdout.strip(), "")
        self.assertEqual(r.returncode, 0)
        status = self.cmd("status")
        # Pending tasks still exist even though none is claimable.
        self.assertIn("pending=1", status.stdout)
        self.assertIn("in_progress=1", status.stdout)


class SequentialTest(ClaimScriptTestBase):
    def setUp(self):
        super().setUp()
        self.write_tasks(
            "## 1. Steps\n"
            "- [ ] 1.1 first\n"
            "- [ ] 1.2 second\n"
            "- [ ] 1.3 third\n")

    def test_untagged_is_fully_sequential(self):
        # Claim/complete hands tasks out strictly in order, one at a time.
        self.assertEqual(self.id_of(self.claim()), "1")
        # A second claim while task 1 is in progress is blocked (barrier).
        blocked = self.claim()
        self.assertEqual(blocked.stdout.strip(), "")
        self.cmd("complete", "1")
        self.assertEqual(self.id_of(self.claim()), "2")
        self.cmd("complete", "2")
        self.assertEqual(self.id_of(self.claim()), "3")
        self.cmd("complete", "3")
        # Nothing left: claim prints nothing and exits cleanly.
        done = self.claim()
        self.assertEqual(done.stdout.strip(), "")
        self.assertEqual(done.returncode, 0)

    def test_release_returns_task_to_pending(self):
        self.assertEqual(self.id_of(self.claim()), "1")
        self.cmd("release", "1")
        # After release the same first task is claimable again.
        self.assertEqual(self.id_of(self.claim()), "1")


class BranchGuardTest(ClaimScriptTestBase):
    """The mutating verbs refuse to act from a checkout that is not the
    change's `change/<change>` branch, while non-git dirs, repos without that
    branch, and the read-only verbs stay unaffected."""

    def _git(self, *args):
        return subprocess.run(
            ["git", *args], cwd=self.root,
            capture_output=True, text=True, check=True)

    def _init_repo(self, create_change_branch=True):
        """Init a git repo in self.root committing the current tasks tree.
        Leaves the checkout on branch `main`; optionally also creates the
        `change/<CHANGE>` branch (pointing at the same commit)."""
        self._git("init", "-q")
        self._git("config", "user.email", "t@example.com")
        self._git("config", "user.name", "Test")
        self._git("config", "commit.gpgsign", "false")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "init")
        self._git("branch", "-M", "main")
        if create_change_branch:
            self._git("branch", "change/%s" % CHANGE)

    def _head_sha(self):
        return self._git("rev-parse", "HEAD").stdout.strip()

    def setUp(self):
        super().setUp()
        self.write_tasks(
            "## 1. Steps\n"
            "- [ ] 1.1 first\n"
            "- [ ] 1.2 second\n")

    def _assert_no_task_claimed(self):
        with open(self.tasks, encoding="utf-8") as fh:
            body = fh.read()
        self.assertEqual(body.count("- [~]"), 0)

    def test_wrong_branch_claim_refuses_exit3_naming_both(self):
        self._init_repo()  # on 'main', with change/demo existing
        r = self.claim()
        self.assertEqual(r.returncode, 3)
        self.assertEqual(r.stdout.strip(), "")
        # Names both the current and the required branch.
        self.assertIn("main", r.stderr)
        self.assertIn("change/%s" % CHANGE, r.stderr)
        self._assert_no_task_claimed()

    def test_on_branch_claim_works(self):
        self._init_repo()
        self._git("checkout", "-q", "change/%s" % CHANGE)
        r = self.claim()
        self.assertEqual(r.returncode, 0)
        self.assertEqual(self.id_of(r), "1")

    def test_repo_without_change_branch_unaffected(self):
        self._init_repo(create_change_branch=False)  # on 'main', no change/demo
        r = self.claim()
        self.assertEqual(r.returncode, 0)
        self.assertEqual(self.id_of(r), "1")

    def test_non_git_dir_unaffected(self):
        # No git init at all: guard must not trigger for any mutating verb.
        r = self.claim()
        self.assertEqual(r.returncode, 0)
        self.assertEqual(self.id_of(r), "1")
        self.assertEqual(self.cmd("complete", "1").returncode, 0)
        self.assertEqual(self.id_of(self.claim()), "2")
        self.assertEqual(self.cmd("release", "2").returncode, 0)

    def test_detached_head_refuses_exit3(self):
        self._init_repo()
        self._git("checkout", "-q", self._head_sha())  # detached HEAD
        r = self.claim()
        self.assertEqual(r.returncode, 3)
        self._assert_no_task_claimed()

    def test_readonly_verbs_stay_unguarded_on_wrong_branch(self):
        self._init_repo()  # on 'main', change/demo exists
        status = self.cmd("status")
        self.assertEqual(status.returncode, 0)
        self.assertIn("pending=2", status.stdout)
        nxt = self.cmd("next")
        self.assertEqual(nxt.returncode, 0)
        self.assertEqual(self.id_of(nxt), "1")

    def test_complete_and_release_guarded_like_claim(self):
        self._init_repo()  # on 'main', change/demo exists
        complete = self.cmd("complete", "1")
        self.assertEqual(complete.returncode, 3)
        self.assertIn("change/%s" % CHANGE, complete.stderr)
        release = self.cmd("release", "1")
        self.assertEqual(release.returncode, 3)
        self.assertIn("change/%s" % CHANGE, release.stderr)


if __name__ == "__main__":
    unittest.main()
