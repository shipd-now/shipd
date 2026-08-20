#!/usr/bin/env python3
"""Tests for worktree.sh: the plugin-owned worktree helper.

The script is driven as a black box via subprocess against a throwaway temp
git repository (git init + one commit) used as cwd — never against the real
repo. Mirrors ``test_claim_task.py``'s fixture style. The helper makes no
assumption about the repository beyond git itself, so the fixture carries no
shipd layout."""

import os
import shutil
import subprocess
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.normpath(os.path.join(HERE, "..", "scripts", "worktree.sh"))


class WorktreeScriptTestBase(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="worktree-test-")
        # A minimal git repo: init + identity + one commit so a branch exists.
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Test")
        with open(os.path.join(self.root, "README.md"), "w") as fh:
            fh.write("seed\n")
        self.git("add", "README.md")
        self.git("commit", "-q", "-m", "seed")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def git(self, *args):
        return subprocess.run(
            ["git", *args], cwd=self.root,
            capture_output=True, text=True, check=True)

    def git_in(self, cwd, *args):
        return subprocess.run(
            ["git", *args], cwd=cwd,
            capture_output=True, text=True, check=True)

    def run_helper(self, *args, cwd=None, env=None):
        run_env = None
        if env is not None:
            run_env = dict(os.environ)
            run_env.update(env)
        return subprocess.run(
            ["bash", SCRIPT, *args],
            cwd=cwd or self.root, capture_output=True, text=True, env=run_env)

    # --- helpers shared by the remove-verb tests -------------------------

    def make_worktree(self, name="my-change"):
        """Create a worktree via the helper; return its absolute path."""
        r = self.run_helper(name)
        self.assertEqual(r.returncode, 0, r.stderr)
        wt = os.path.join(self.root, ".worktrees", name)
        self.assertTrue(os.path.isdir(wt))
        return wt

    def age_tree(self, path, minutes=120):
        """Set the mtime of every file and directory in the tree into the
        past, so the recent-activity guard sees nothing fresh. No sleeping."""
        old = time.time() - minutes * 60
        for dirpath, dirnames, filenames in os.walk(path):
            for name in filenames:
                fp = os.path.join(dirpath, name)
                try:
                    os.utime(fp, (old, old))
                except OSError:
                    pass
            try:
                os.utime(dirpath, (old, old))
            except OSError:
                pass

    def touch_now(self, path):
        """Bump one file's mtime to now (fresh activity)."""
        now = time.time()
        os.utime(path, (now, now))

    def worktree_listed(self, wt):
        """True when `git worktree list` still knows about `wt`."""
        listed = self.git("worktree", "list", "--porcelain").stdout
        return os.path.realpath(wt) in listed or wt in listed

    def combined(self, r):
        return (r.stdout or "") + (r.stderr or "")

    def commit_planned_on_base(self, name="other-change",
                               tasks_body="# Tasks\n\n- [ ] 1.1 todo\n"):
        """Commit a planned change onto the base branch, so every worktree cut
        from it carries that directory as base content rather than own work."""
        d = os.path.join(self.root, ".shipd", "planned", name)
        os.makedirs(d)
        with open(os.path.join(d, "spec.md"), "w") as fh:
            fh.write("# spec\n")
        with open(os.path.join(d, "tasks.md"), "w") as fh:
            fh.write(tasks_body)
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "planned change on base: " + name)
        return d

    # --- helpers shared by the branch-hygiene tests ----------------------

    def branch_sha(self, ref):
        return self.git("rev-parse", ref).stdout.strip()

    def branch_exists(self, branch):
        return bool(self.git("branch", "--list", branch).stdout.strip())

    def branch_with_commit(self, name):
        """Create `change/<name>` carrying one commit, leaving no worktree.
        Returns the branch tip sha."""
        wt = self.make_worktree(name)
        with open(os.path.join(wt, name + ".txt"), "w") as fh:
            fh.write("branch work\n")
        self.git_in(wt, "add", name + ".txt")
        self.git_in(wt, "commit", "-q", "-m", "branch commit")
        self.git("worktree", "remove", wt)
        return self.branch_sha("change/" + name)

    def squash_merge(self, branch):
        """Land `branch` on the base the way `gh pr merge --squash` does:
        same content, no ancestry link back to the branch."""
        self.git("merge", "--squash", branch)
        self.git("commit", "-q", "-m", "squash merge of " + branch)


class CreateWorktreeTest(WorktreeScriptTestBase):
    def test_creates_worktree_and_branch(self):
        r = self.run_helper("my-change")
        self.assertEqual(r.returncode, 0, r.stderr)
        worktree = os.path.join(self.root, ".worktrees", "my-change")
        self.assertTrue(os.path.isdir(worktree))
        # The worktree path appears in the helper's output.
        self.assertIn(os.path.join(".worktrees", "my-change"), r.stdout)
        # The branch change/my-change exists.
        branches = self.git("branch", "--list", "change/my-change").stdout
        self.assertIn("change/my-change", branches)

    def test_second_change_succeeds_alongside_first(self):
        first = self.run_helper("first-change")
        self.assertEqual(first.returncode, 0, first.stderr)
        second = self.run_helper("second-change")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertTrue(
            os.path.isdir(os.path.join(self.root, ".worktrees", "first-change")))
        self.assertTrue(
            os.path.isdir(os.path.join(self.root, ".worktrees", "second-change")))


class ReuseWorktreeTest(WorktreeScriptTestBase):
    def test_second_invocation_reuses_worktree(self):
        first = self.run_helper("my-change")
        self.assertEqual(first.returncode, 0, first.stderr)
        worktree = os.path.join(self.root, ".worktrees", "my-change")
        marker = os.path.join(worktree, "scratch.txt")
        with open(marker, "w") as fh:
            fh.write("work in progress\n")

        second = self.run_helper("my-change")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertTrue(os.path.isdir(worktree))
        branch = self.git_in(worktree, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        self.assertEqual(branch, "change/my-change")
        # The file written between the two runs must survive the reuse.
        self.assertTrue(os.path.exists(marker))
        with open(marker) as fh:
            self.assertEqual(fh.read(), "work in progress\n")

    def test_recreates_worktree_from_existing_branch(self):
        first = self.run_helper("my-change")
        self.assertEqual(first.returncode, 0, first.stderr)
        worktree = os.path.join(self.root, ".worktrees", "my-change")
        # Remove the worktree directly, leaving the branch behind — the state
        # `remove` leaves after a teardown.
        self.git("worktree", "remove", worktree)
        self.assertFalse(os.path.exists(worktree))
        branches = self.git("branch", "--list", "change/my-change").stdout
        self.assertIn("change/my-change", branches)

        second = self.run_helper("my-change")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertTrue(os.path.isdir(worktree))
        branch = self.git_in(worktree, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        self.assertEqual(branch, "change/my-change")

    def test_worktree_on_different_branch_is_refused(self):
        worktree = os.path.join(self.root, ".worktrees", "my-change")
        # Put a worktree at the target path, but checked out on some other
        # branch — a genuine conflict, not a re-entry.
        self.git("worktree", "add", worktree, "-b", "other-branch")

        r = self.run_helper("my-change")
        self.assertNotEqual(r.returncode, 0)
        self.assertTrue(os.path.isdir(worktree))
        branch = self.git_in(worktree, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        self.assertEqual(branch, "other-branch")


class RefuseExistingBranchTest(WorktreeScriptTestBase):
    def test_existing_branch_without_worktree_is_attached(self):
        # Pre-create the target branch with no worktree — the state `remove`
        # leaves behind. The helper is idempotent, so it attaches rather than
        # refusing (see ReuseWorktreeTest for the full re-entry coverage).
        self.git("branch", "change/my-change")
        r = self.run_helper("my-change")
        self.assertEqual(r.returncode, 0, r.stderr)
        worktree = os.path.join(self.root, ".worktrees", "my-change")
        self.assertTrue(os.path.isdir(worktree))
        branch = self.git_in(worktree, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        self.assertEqual(branch, "change/my-change")


class ReuseNoticeTest(WorktreeScriptTestBase):
    """The create path announces reuse loudly: a reused worktree or a
    re-attached branch names what it reused plus the branch's ahead/behind
    counts against the base branch, and never claims to have created it."""

    def commit_on_base(self, name="base.txt"):
        with open(os.path.join(self.root, name), "w") as fh:
            fh.write("base work\n")
        self.git("add", name)
        self.git("commit", "-q", "-m", "base commit")

    def commit_in_worktree(self, wt, name="branch.txt"):
        with open(os.path.join(wt, name), "w") as fh:
            fh.write("branch work\n")
        self.git_in(wt, "add", name)
        self.git_in(wt, "commit", "-q", "-m", "branch commit")

    def test_reused_worktree_is_announced_with_counts(self):
        wt = self.make_worktree("my-change")
        self.commit_in_worktree(wt)   # one ahead of base
        self.commit_on_base()         # one behind base

        r = self.run_helper("my-change")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Reusing existing worktree", r.stdout)
        self.assertIn(os.path.join(".worktrees", "my-change"), r.stdout)
        self.assertIn("ahead 1, behind 1", r.stdout)
        self.assertNotIn("Created worktree", r.stdout)
        # The next-steps block survives on the reuse arm.
        self.assertIn("Next steps:", r.stdout)

    def test_attached_branch_is_announced_with_counts(self):
        wt = self.make_worktree("my-change")
        self.commit_in_worktree(wt)
        # Drop the worktree, keeping the branch — the state `remove` leaves.
        self.git("worktree", "remove", wt)
        self.commit_on_base()

        r = self.run_helper("my-change")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Attached worktree", r.stdout)
        self.assertIn("change/my-change", r.stdout)
        self.assertIn("ahead 1, behind 1", r.stdout)
        self.assertNotIn("Created worktree", r.stdout)
        self.assertIn("Next steps:", r.stdout)

    def test_true_creation_still_says_created(self):
        r = self.run_helper("my-change")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Created worktree", r.stdout)
        self.assertNotIn("Reusing existing worktree", r.stdout)
        self.assertNotIn("Attached worktree", r.stdout)


class FreshFlagTest(WorktreeScriptTestBase):
    """`--fresh` guarantees a fresh branch: it recreates a branch whose content
    already reached the base (squash merges included) and refuses everything
    else, so an epic close-out never adopts a stale close-out branch."""

    def test_squash_merged_branch_is_recreated_fresh(self):
        old = self.branch_with_commit("epic-close-x")
        self.squash_merge("change/epic-close-x")
        base_tip = self.branch_sha("HEAD")

        r = self.run_helper("epic-close-x", "--fresh")
        self.assertEqual(r.returncode, 0, self.combined(r))
        wt = os.path.join(self.root, ".worktrees", "epic-close-x")
        self.assertTrue(os.path.isdir(wt))
        self.assertEqual(self.branch_sha("change/epic-close-x"), base_tip)
        self.assertNotEqual(self.branch_sha("change/epic-close-x"), old)
        # The deletion is announced, naming the branch.
        out = self.combined(r)
        self.assertIn("change/epic-close-x", out)
        self.assertIn("delet", out.lower())

    def test_unmerged_branch_refuses_fresh(self):
        old = self.branch_with_commit("epic-close-x")

        r = self.run_helper("epic-close-x", "--fresh")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("change/epic-close-x", self.combined(r))
        # Branch and its commit are untouched, and no worktree appeared.
        self.assertEqual(self.branch_sha("change/epic-close-x"), old)
        self.assertFalse(
            os.path.exists(os.path.join(self.root, ".worktrees", "epic-close-x")))

    def test_existing_worktree_refuses_fresh(self):
        wt = self.make_worktree("my-change")
        old = self.branch_sha("change/my-change")

        r = self.run_helper("my-change", "--fresh")
        self.assertNotEqual(r.returncode, 0)
        self.assertTrue(os.path.isdir(wt))
        self.assertEqual(self.branch_sha("change/my-change"), old)


class PruneBranchesTest(WorktreeScriptTestBase):
    """`prune-branches` reclaims local `change/*` branches whose content has
    already landed on the base — the leftovers a squash-merged PR's remote
    branch deletion never touches — and nothing else."""

    def prune_worktree_created(self):
        """True if the verb name leaked into the create path as a change name."""
        return os.path.exists(
            os.path.join(self.root, ".worktrees", "prune-branches"))

    def test_squash_merged_branches_are_pruned_and_listed(self):
        self.branch_with_commit("a")
        self.branch_with_commit("b")
        self.squash_merge("change/a")
        self.squash_merge("change/b")

        r = self.run_helper("prune-branches")
        self.assertEqual(r.returncode, 0, self.combined(r))
        out = self.combined(r)
        self.assertIn("pruned: change/a", out)
        self.assertIn("pruned: change/b", out)
        self.assertFalse(self.branch_exists("change/a"))
        self.assertFalse(self.branch_exists("change/b"))

    def test_unmerged_and_checked_out_branches_survive(self):
        self.branch_with_commit("wip")   # unmerged, no worktree
        self.make_worktree("active")     # merged, but checked out

        r = self.run_helper("prune-branches")
        self.assertEqual(r.returncode, 0, self.combined(r))
        out = self.combined(r)
        self.assertIn("kept: change/wip", out)
        self.assertIn("kept: change/active", out)
        self.assertTrue(self.branch_exists("change/wip"))
        self.assertTrue(self.branch_exists("change/active"))

    def test_non_change_branch_is_untouched(self):
        # Merged by ancestry (it sits on the base tip) but out of scope.
        self.git("branch", "hotfix")

        r = self.run_helper("prune-branches")
        self.assertEqual(r.returncode, 0, self.combined(r))
        self.assertTrue(self.branch_exists("hotfix"))
        self.assertNotIn("hotfix", self.combined(r))
        self.assertFalse(self.prune_worktree_created())

    def test_nothing_to_prune_exits_zero(self):
        self.branch_with_commit("wip")  # the only candidate, and unmerged

        r = self.run_helper("prune-branches")
        self.assertEqual(r.returncode, 0, self.combined(r))
        self.assertNotIn("pruned:", self.combined(r))
        self.assertTrue(self.branch_exists("change/wip"))
        self.assertFalse(self.prune_worktree_created())


class OutsideRepoRootTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="worktree-norepo-")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_no_git_dir_is_an_error(self):
        r = subprocess.run(
            ["bash", SCRIPT, "my-change"],
            cwd=self.root, capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("repo root", r.stderr)


class RemoveWorktreeTest(WorktreeScriptTestBase):
    """The guarded `remove <change>` verb. All fixtures live in throwaway
    temp repos; mtimes are set via os.utime so nothing sleeps."""

    def test_clean_cold_removes(self):
        wt = self.make_worktree("my-change")
        self.age_tree(wt)  # nothing modified inside the idle window
        r = self.run_helper("remove", "my-change")
        self.assertEqual(r.returncode, 0, self.combined(r))
        self.assertFalse(os.path.exists(wt))
        # Removed and pruned: git no longer tracks the worktree.
        self.assertFalse(self.worktree_listed(wt))

    def test_idle_minutes_zero_disables_activity_for_cold_case(self):
        # A brand-new worktree has fresh mtimes; SHIPD_WORKTREE_IDLE_MINUTES=0
        # disables the activity guard so the otherwise-clean tree removes.
        wt = self.make_worktree("my-change")
        r = self.run_helper(
            "remove", "my-change", env={"SHIPD_WORKTREE_IDLE_MINUTES": "0"})
        self.assertEqual(r.returncode, 0, self.combined(r))
        self.assertFalse(os.path.exists(wt))

    def test_dirty_tree_refuses(self):
        wt = self.make_worktree("my-change")
        with open(os.path.join(wt, "scratch.txt"), "w") as fh:
            fh.write("work in progress\n")
        self.age_tree(wt)  # isolate the dirty guard from recent-activity
        r = self.run_helper("remove", "my-change")
        self.assertEqual(r.returncode, 2, self.combined(r))
        self.assertTrue(os.path.isdir(wt))  # nothing removed
        out = self.combined(r).lower()
        self.assertTrue("dirty" in out or "uncommitted" in out, out)

    def test_unshipped_planned_refuses(self):
        wt = self.make_worktree("my-change")
        planned = os.path.join(wt, ".shipd", "planned", "foo")
        os.makedirs(planned)
        with open(os.path.join(planned, "spec.md"), "w") as fh:
            fh.write("# spec\n")
        # Commit so the tree is clean and only the unshipped guard fires.
        self.git_in(wt, "add", "-A")
        self.git_in(wt, "commit", "-q", "-m", "planned change")
        self.age_tree(wt)
        r = self.run_helper("remove", "my-change")
        self.assertEqual(r.returncode, 2, self.combined(r))
        self.assertTrue(os.path.isdir(wt))
        self.assertIn(".shipd/planned", self.combined(r))

    def test_claim_mark_refuses(self):
        wt = self.make_worktree("my-change")
        planned = os.path.join(wt, ".shipd", "planned", "foo")
        os.makedirs(planned)
        with open(os.path.join(planned, "tasks.md"), "w") as fh:
            fh.write("# Tasks\n\n- [~] 1.1 claimed by a live session\n")
        self.git_in(wt, "add", "-A")
        self.git_in(wt, "commit", "-q", "-m", "claimed task")
        self.age_tree(wt)
        r = self.run_helper("remove", "my-change")
        self.assertEqual(r.returncode, 2, self.combined(r))
        self.assertTrue(os.path.isdir(wt))
        self.assertIn("claim", self.combined(r).lower())

    def test_tasks_lock_refuses(self):
        wt = self.make_worktree("my-change")
        lock = os.path.join(wt, ".shipd", "planned", "foo", ".tasks.lock")
        os.makedirs(lock)  # the coordinator's lock is a directory
        self.age_tree(wt)
        r = self.run_helper("remove", "my-change")
        self.assertEqual(r.returncode, 2, self.combined(r))
        self.assertTrue(os.path.isdir(wt))
        self.assertIn(".tasks.lock", self.combined(r))

    def test_fresh_activity_refuses(self):
        wt = self.make_worktree("my-change")
        self.age_tree(wt)  # everything cold ...
        self.touch_now(os.path.join(wt, "README.md"))  # ... but one fresh file
        r = self.run_helper("remove", "my-change")
        self.assertEqual(r.returncode, 2, self.combined(r))
        self.assertTrue(os.path.isdir(wt))
        out = self.combined(r).lower()
        self.assertTrue("idle" in out or "minute" in out or "recent" in out, out)

    def test_multiple_reasons_all_listed(self):
        wt = self.make_worktree("my-change")
        # dirty + unshipped-planned + claim, all left with fresh mtimes so the
        # recent-activity guard also fires -> four reasons at once.
        with open(os.path.join(wt, "scratch.txt"), "w") as fh:
            fh.write("wip\n")
        planned = os.path.join(wt, ".shipd", "planned", "foo")
        os.makedirs(planned)
        with open(os.path.join(planned, "tasks.md"), "w") as fh:
            fh.write("# Tasks\n\n- [~] 1.1 claimed\n")
        r = self.run_helper("remove", "my-change")
        self.assertEqual(r.returncode, 2, self.combined(r))
        self.assertTrue(os.path.isdir(wt))
        out = self.combined(r)
        low = out.lower()
        self.assertTrue("dirty" in low or "uncommitted" in low, out)
        self.assertIn(".shipd/planned", out)
        self.assertIn("claim", low)
        self.assertTrue("idle" in low or "minute" in low or "recent" in low, out)

    def test_force_on_dirty_removes_and_echoes(self):
        wt = self.make_worktree("my-change")
        with open(os.path.join(wt, "scratch.txt"), "w") as fh:
            fh.write("work in progress\n")
        r = self.run_helper("remove", "my-change", "--force")
        self.assertEqual(r.returncode, 0, self.combined(r))
        self.assertFalse(os.path.exists(wt))
        out = self.combined(r).lower()
        self.assertIn("overrid", out)  # names what it overrode
        self.assertTrue("dirty" in out or "uncommitted" in out, out)

    def test_base_tracked_planned_does_not_guard(self):
        # A planned change committed on the base branch is base content, not
        # this worktree's own work: guard #2 carves it out.
        self.commit_planned_on_base()
        wt = self.make_worktree("my-change")
        r = self.run_helper(
            "remove", "my-change", env={"SHIPD_WORKTREE_IDLE_MINUTES": "0"})
        self.assertEqual(r.returncode, 0, self.combined(r))
        self.assertFalse(os.path.exists(wt))

    def test_modified_base_tracked_planned_still_guards(self):
        # Local modification means the worktree has made it its own work.
        self.commit_planned_on_base()
        wt = self.make_worktree("my-change")
        with open(os.path.join(wt, ".shipd", "planned", "other-change",
                               "spec.md"), "w") as fh:
            fh.write("# spec\n\nedited in the worktree\n")
        r = self.run_helper(
            "remove", "my-change", env={"SHIPD_WORKTREE_IDLE_MINUTES": "0"})
        self.assertEqual(r.returncode, 2, self.combined(r))
        self.assertTrue(os.path.isdir(wt))
        self.assertIn("unshipped change", self.combined(r))

    def test_claim_in_base_tracked_planned_still_guards(self):
        # The claims guard keeps scanning every planned checklist: a `[~]` mark
        # is live coordination wherever it sits.
        self.commit_planned_on_base(
            tasks_body="# Tasks\n\n- [~] 1.1 claimed by a live session\n")
        wt = self.make_worktree("my-change")
        r = self.run_helper(
            "remove", "my-change", env={"SHIPD_WORKTREE_IDLE_MINUTES": "0"})
        self.assertEqual(r.returncode, 2, self.combined(r))
        self.assertTrue(os.path.isdir(wt))
        out = self.combined(r)
        self.assertIn("claim", out.lower())
        # The carve-out still applies to guard #2 — only the claim remains.
        self.assertNotIn("unshipped change", out)

    def test_detached_base_applies_no_carve_out(self):
        # No base resolves -> fail closed, every planned dir guards as before.
        self.commit_planned_on_base()
        wt = self.make_worktree("my-change")
        self.git("checkout", "-q", "--detach")
        r = self.run_helper(
            "remove", "my-change", env={"SHIPD_WORKTREE_IDLE_MINUTES": "0"})
        self.assertEqual(r.returncode, 2, self.combined(r))
        self.assertTrue(os.path.isdir(wt))
        self.assertIn("unshipped change", self.combined(r))

    def test_non_kebab_name_refused(self):
        # A path-ish name must not escape .worktrees/ (see the remove verb's
        # kebab-case guard).
        r = self.run_helper("remove", "../evil")
        self.assertEqual(r.returncode, 1, self.combined(r))
        self.assertIn("kebab-case", self.combined(r))

    def test_unknown_change_exits_1(self):
        r = self.run_helper("remove", "no-such-change")
        self.assertEqual(r.returncode, 1, self.combined(r))


if __name__ == "__main__":
    unittest.main()
