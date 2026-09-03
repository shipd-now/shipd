#!/usr/bin/env python3
"""Tests for claim_task.sh group-aware claiming: parallel groups, barrier
blocking, unready-group emptiness, untagged (fully sequential) behavior, and
claim liveness — holder-stamped claim records, blocking `claim --wait`,
state-guarded `complete`/`release`, claim lines in `status`, and
`release --stale`.

The script is driven as a black box via subprocess against a throwaway temp
directory laid out as ``.shipd/planned/<change>/tasks.md`` (run with that temp
root as cwd) — never against the real repo change dirs."""

import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.normpath(os.path.join(HERE, "..", "scripts", "claim_task.sh"))
CHANGE = "demo"

# The three checkbox markers, assembled by concatenation so no checkbox-shaped
# marker ever lands at the start of a line in this file.
PENDING = "- " + "[ ]"
WIP = "- " + "[~]"
DONE = "- " + "[x]"


class ClaimScriptTestBase(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="claim-test-")
        self.change_dir = os.path.join(
            self.root, ".shipd", "planned", CHANGE)
        os.makedirs(self.change_dir)
        self.tasks = os.path.join(self.change_dir, "tasks.md")
        self.claims = os.path.join(self.change_dir, ".tasks.claims")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def write_tasks(self, text):
        with open(self.tasks, "w", encoding="utf-8") as fh:
            fh.write(text)

    def claim(self):
        return subprocess.run(
            ["bash", SCRIPT, "claim", CHANGE],
            cwd=self.root, capture_output=True, text=True)

    def cmd(self, action, *extra, **kw):
        return subprocess.run(
            ["bash", SCRIPT, action, CHANGE, *extra],
            cwd=self.root, capture_output=True, text=True, **kw)

    def raw(self, *args, **kw):
        """Run the script with fully explicit argv (no implied change name)."""
        return subprocess.run(
            ["bash", SCRIPT, *args],
            cwd=self.root, capture_output=True, text=True, **kw)

    def env_without_session(self):
        env = dict(os.environ)
        env.pop("CLAUDE_CODE_SESSION_ID", None)
        return env

    def read_claims(self):
        """Parse the claim sidecar into {id: (holder, epoch)}; {} when absent."""
        if not os.path.exists(self.claims):
            return {}
        records = {}
        with open(self.claims, encoding="utf-8") as fh:
            for line in fh:
                line = line.rstrip("\n")
                if not line:
                    continue
                parts = line.split("\t")
                self.assertEqual(
                    len(parts), 3, "claim record is not id<TAB>holder<TAB>epoch: %r" % line)
                records[parts[0]] = (parts[1], int(parts[2]))
        return records

    def backdate(self, task_id, minutes):
        """Rewrite one claim record's epoch to `minutes` ago."""
        records = self.read_claims()
        self.assertIn(task_id, records, "no claim record for task %s" % task_id)
        holder, _ = records[task_id]
        records[task_id] = (holder, int(time.time()) - minutes * 60)
        with open(self.claims, "w", encoding="utf-8") as fh:
            for tid, (who, epoch) in sorted(records.items(), key=lambda kv: int(kv[0])):
                fh.write("%s\t%s\t%d\n" % (tid, who, epoch))

    def boxes(self):
        """The checkbox characters, in file order, as a string like ' ~x'."""
        with open(self.tasks, encoding="utf-8") as fh:
            return "".join(re.findall(r"- \[([ ~x])\]", fh.read()))

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


class ClaimRecordTest(ClaimScriptTestBase):
    """Every claim is stamped in the `.tasks.claims` sidecar with a holder and
    a timestamp, and the record is cleared when the task is finished."""

    def setUp(self):
        super().setUp()
        self.write_tasks(
            "## 1. Steps\n"
            "- [ ] 1.1 [P1] a\n"
            "- [ ] 1.2 [P1] b\n")

    def test_claim_as_records_holder_and_timestamp(self):
        before = int(time.time())
        r = self.cmd("claim", "--as", "builder-2")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(self.id_of(r), "1")
        records = self.read_claims()
        self.assertIn("1", records)
        holder, epoch = records["1"]
        self.assertEqual(holder, "builder-2")
        self.assertGreaterEqual(epoch, before)
        self.assertLessEqual(epoch, int(time.time()) + 1)
        # tasks.md carries the ordinary in-progress mark and nothing more.
        self.assertEqual(self.boxes(), "~ ")
        with open(self.tasks, encoding="utf-8") as fh:
            self.assertNotIn("builder-2", fh.read())

    def test_bare_claim_records_session_id_default(self):
        env = self.env_without_session()
        env["CLAUDE_CODE_SESSION_ID"] = "sess-abc"
        r = self.cmd("claim", env=env)
        self.assertEqual(self.id_of(r), "1")
        self.assertEqual(self.read_claims()["1"][0], "sess-abc")

    def test_bare_claim_without_session_id_records_anon(self):
        r = self.cmd("claim", env=self.env_without_session())
        self.assertEqual(self.id_of(r), "1")
        self.assertEqual(self.read_claims()["1"][0], "anon")

    def test_complete_and_release_clear_the_record(self):
        self.cmd("claim", "--as", "b1")
        self.cmd("claim", "--as", "b2")
        self.assertEqual(sorted(self.read_claims()), ["1", "2"])
        self.assertEqual(self.cmd("complete", "1").returncode, 0)
        self.assertEqual(sorted(self.read_claims()), ["2"])
        self.assertEqual(self.cmd("release", "2").returncode, 0)
        self.assertEqual(self.read_claims(), {})
        # The sidecar itself is removed once its last record goes.
        self.assertFalse(os.path.exists(self.claims))


class WaitTest(ClaimScriptTestBase):
    """`claim --wait` blocks inside the single invocation until it wins a task,
    nothing is pending, or the timeout passes."""

    def setUp(self):
        super().setUp()
        self.write_tasks(
            "## 1. Steps\n"
            "- [ ] 1.1 first\n"
            "- [ ] 1.2 second\n")

    def test_wait_returns_a_ready_task_immediately(self):
        started = time.time()
        r = self.cmd("claim", "--wait")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(self.id_of(r), "1")
        self.assertLess(time.time() - started, 5)

    def test_wait_blocks_through_a_barrier_then_claims(self):
        self.assertEqual(self.id_of(self.claim()), "1")

        def finish_barrier():
            time.sleep(1.5)
            self.cmd("complete", "1")

        writer = threading.Thread(target=finish_barrier)
        writer.start()
        try:
            r = self.cmd("claim", "--wait", "--timeout", "30")
        finally:
            writer.join()
        self.assertEqual(r.returncode, 0)
        # The same invocation that started while task 2 was blocked returns it.
        self.assertEqual(self.id_of(r), "2")

    def test_wait_times_out_empty_on_stdout(self):
        self.assertEqual(self.id_of(self.claim()), "1")  # barrier held open
        started = time.time()
        r = self.cmd("claim", "--wait", "--timeout", "1")
        elapsed = time.time() - started
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "")
        self.assertIn("timed out", r.stderr)
        self.assertLess(elapsed, 20)
        # The blocked task is untouched.
        self.assertEqual(self.boxes(), "~ ")

    def test_wait_returns_at_once_when_nothing_is_pending(self):
        self.write_tasks(
            "## 1. Steps\n"
            "- [x] 1.1 first\n"
            "- [x] 1.2 second\n")
        started = time.time()
        r = self.cmd("claim", "--wait")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "")
        self.assertIn("No pending tasks.", r.stderr)
        self.assertLess(time.time() - started, 5)


class StateGuardTest(ClaimScriptTestBase):
    """`complete` and `release` refuse any task that is not in progress."""

    def setUp(self):
        super().setUp()
        self.write_tasks(
            "## 1. Steps\n"
            "- [x] 1.1 done already\n"
            "- [ ] 1.2 pending\n"
            "- [~] 1.3 in progress\n")

    def test_completing_a_pending_task_is_refused(self):
        r = self.cmd("complete", "2")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("pending", r.stderr)
        self.assertEqual(self.boxes(), "x ~")

    def test_releasing_a_completed_task_is_refused(self):
        # Regression: `release <change> <id>` on a `- [x]` task used to flip it
        # back to `- [ ]`, silently undoing finished work.
        r = self.cmd("release", "1")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("done", r.stderr)
        self.assertEqual(self.boxes(), "x ~")

    def test_releasing_a_pending_task_is_refused(self):
        r = self.cmd("release", "2")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("pending", r.stderr)
        self.assertEqual(self.boxes(), "x ~")

    def test_completing_an_already_done_task_is_refused(self):
        r = self.cmd("complete", "1")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("done", r.stderr)
        self.assertEqual(self.boxes(), "x ~")

    def test_in_progress_task_still_completes(self):
        r = self.cmd("complete", "3")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(self.boxes(), "x x")


class HolderVerificationTest(ClaimScriptTestBase):
    """Holder verification is soft: only an explicit, mismatching `--as` is
    refused; a bare call acts exactly as it did before this change."""

    def setUp(self):
        super().setUp()
        self.write_tasks(
            "## 1. Steps\n"
            "- [ ] 1.1 [P1] a\n"
            "- [ ] 1.2 [P1] b\n")

    def test_mismatched_holder_on_complete_is_refused(self):
        self.cmd("claim", "--as", "builder-1")
        r = self.cmd("complete", "1", "--as", "builder-2")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("builder-1", r.stderr)
        self.assertIn("builder-2", r.stderr)
        self.assertEqual(self.boxes(), "~ ")

    def test_mismatched_holder_on_release_is_refused(self):
        self.cmd("claim", "--as", "builder-1")
        r = self.cmd("release", "1", "--as", "builder-2")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("builder-1", r.stderr)
        self.assertIn("builder-2", r.stderr)
        self.assertEqual(self.boxes(), "~ ")

    def test_matching_holder_completes(self):
        self.cmd("claim", "--as", "builder-1")
        r = self.cmd("complete", "1", "--as", "builder-1")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(self.boxes(), "x ")

    def test_bare_call_ignores_the_recorded_holder(self):
        self.cmd("claim", "--as", "builder-1")
        r = self.cmd("complete", "1")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(self.boxes(), "x ")


class StatusClaimLinesTest(ClaimScriptTestBase):
    """`status` keeps its counts line byte-identical and appends one line per
    in-progress task with holder, age, and a stale marker."""

    def setUp(self):
        super().setUp()
        self.write_tasks(
            "## 1. Steps\n"
            "- [ ] 1.1 [P1] a\n"
            "- [ ] 1.2 [P1] b\n"
            "- [ ] 1.3 [P1] c\n")

    def claimed_lines(self, *extra):
        r = self.cmd("status", *extra)
        self.assertEqual(r.returncode, 0)
        lines = r.stdout.rstrip("\n").split("\n")
        return r, lines

    def test_first_line_is_byte_identical(self):
        self.cmd("claim", "--as", "b1")
        r, lines = self.claimed_lines()
        self.assertEqual(lines[0], "pending=2 in_progress=1 done=0")

    def test_claimed_line_names_id_holder_and_age(self):
        self.cmd("claim", "--as", "b1")
        r, lines = self.claimed_lines()
        claimed = [ln for ln in lines if ln.startswith("claimed:")]
        self.assertEqual(len(claimed), 1)
        self.assertRegex(claimed[0], r"^claimed: 1 by b1 age (\d+s|\d+m|\d+h \d+m)$")

    def test_old_claim_is_marked_stale(self):
        self.cmd("claim", "--as", "b1")
        self.cmd("claim", "--as", "b2")
        self.backdate("1", 45)
        r, lines = self.claimed_lines()
        claimed = [ln for ln in lines if ln.startswith("claimed:")]
        self.assertEqual(len(claimed), 2)
        self.assertEqual(claimed[0], "claimed: 1 by b1 age 45m [stale]")
        self.assertNotIn("[stale]", claimed[1])

    def test_stale_after_override(self):
        self.cmd("claim", "--as", "b1")
        self.backdate("1", 10)
        _, lines = self.claimed_lines("--stale-after", "5")
        self.assertIn("[stale]", lines[1])
        _, lines = self.claimed_lines("--stale-after", "60")
        self.assertNotIn("[stale]", lines[1])

    def test_recordless_in_progress_is_visible_not_fatal(self):
        self.write_tasks(
            "## 1. Steps\n"
            "- [~] 1.1 orphaned\n"
            "- [ ] 1.2 next\n")
        r, lines = self.claimed_lines()
        self.assertEqual(lines[0], "pending=1 in_progress=1 done=0")
        self.assertEqual(lines[1], "claimed: 1 by unknown age unknown [stale]")

    def test_no_claim_lines_when_nothing_in_progress(self):
        r, lines = self.claimed_lines()
        self.assertEqual(lines, ["pending=3 in_progress=0 done=0"])


class StaleReleaseTest(ClaimScriptTestBase):
    """`release --stale <mins>` reclaims old and record-less claims only."""

    def setUp(self):
        super().setUp()
        self.write_tasks(
            "## 1. Steps\n"
            "- [ ] 1.1 [P1] a\n"
            "- [ ] 1.2 [P1] b\n"
            "- [~] 1.3 [P1] orphaned\n")

    def test_stale_claims_are_reclaimed_fresh_ones_spared(self):
        self.cmd("claim", "--as", "old-holder")   # task 1
        self.cmd("claim", "--as", "fresh")        # task 2
        self.backdate("1", 45)
        r = self.cmd("release", "--stale", "30")
        self.assertEqual(r.returncode, 0)
        released = [ln for ln in r.stdout.rstrip("\n").split("\n") if ln]
        self.assertEqual(len(released), 2, r.stdout)
        self.assertIn("old-holder", released[0])
        self.assertIn("45m", released[0])
        self.assertIn("Task 1 released", released[0])
        self.assertIn("Task 3 released", released[1])
        # Task 1 (old) and task 3 (record-less) are back to pending; task 2 is
        # untouched and keeps its record.
        self.assertEqual(self.boxes(), " ~ ")
        self.assertEqual(sorted(self.read_claims()), ["2"])

    def test_nothing_stale_is_a_clean_no_op(self):
        self.write_tasks(
            "## 1. Steps\n"
            "- [ ] 1.1 [P1] a\n"
            "- [ ] 1.2 [P1] b\n")
        self.cmd("claim", "--as", "fresh")
        r = self.cmd("release", "--stale", "30")
        self.assertEqual(r.returncode, 0)
        self.assertIn("No stale claims.", r.stdout)
        self.assertEqual(self.boxes(), "~ ")
        self.assertEqual(sorted(self.read_claims()), ["1"])

    def test_flags_before_the_change_name_are_accepted(self):
        self.cmd("claim", "--as", "old-holder")
        self.backdate("1", 45)
        r = self.raw("release", "--stale", "30", CHANGE)
        self.assertEqual(r.returncode, 0)
        self.assertIn("Task 1 released", r.stdout)
        # The stale claim and the record-less `- [~]` both go back to pending.
        self.assertEqual(self.boxes(), "   ")

    def test_an_id_and_stale_are_mutually_exclusive(self):
        self.cmd("claim", "--as", "b1")
        r = self.cmd("release", "1", "--stale", "30")
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(self.boxes(), "~ ~")
        self.assertEqual(sorted(self.read_claims()), ["1"])


class AnchoredGrammarTest(ClaimScriptTestBase):
    """The anchored checkbox grammar (build-task-coordination
    ``atomic-task-claiming-with-stable-ids``): a checkbox line's content begins
    — after optional leading blanks — with the marker, so a checkbox-shaped
    literal quoted inside a task's wrapped prose is prose, never a task, for
    every verb: ordinals, readiness, status counts, the box rewrite, and the
    marker strip.

    Written test-first; expected to FAIL until ``claim_task.sh`` anchors its
    matchers (task 2.2)."""

    # Indices (0-based, over the fixture's split lines) of the continuation
    # lines that carry the quoted literals. They must never be rewritten.
    PROSE_IDX = (2, 5)

    REAL_BOX_RE = re.compile(r"^[ \t]*- \[([ ~x])\]")

    def setUp(self):
        super().setUp()
        # Two grouped tasks, a barrier, then a later group — with quoted
        # checkbox literals on the continuation lines of two of them.
        self.write_tasks(
            "## 1. Work\n"
            + PENDING + " 1.1 [P1] first task, whose wrapped prose quotes\n"
            + "      a `" + PENDING + "` marker and a `" + DONE + "` marker.\n"
            + PENDING + " 1.2 [P1] second task\n"
            + PENDING + " 2.1 barrier task, whose prose quotes the\n"
            + "      `" + WIP + "` marker inline.\n"
            + PENDING + " 3.1 [P2] after the barrier\n")
        self.prose_before = [self.lines()[i] for i in self.PROSE_IDX]

    def lines(self):
        with open(self.tasks, encoding="utf-8") as fh:
            return fh.read().split("\n")

    def real_boxes(self):
        """Checkbox chars of the *real* task lines only, in file order."""
        hits = [self.REAL_BOX_RE.match(ln) for ln in self.lines()]
        return "".join(m.group(1) for m in hits if m)

    def assert_prose_unchanged(self):
        after = [self.lines()[i] for i in self.PROSE_IDX]
        self.assertEqual(after, self.prose_before)

    def test_status_counts_only_real_tasks(self):
        r = self.cmd("status")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.rstrip("\n").split("\n")[0],
                         "pending=4 in_progress=0 done=0")

    def test_claim_ordinals_map_to_the_real_task_lines(self):
        self.assertEqual(self.id_of(self.claim()), "1")
        self.assertEqual(self.id_of(self.claim()), "2")
        # Both P1 tasks are in progress; the barrier and P2 are untouched.
        self.assertEqual(self.real_boxes(), "~~  ")
        self.assert_prose_unchanged()

    def test_complete_marks_the_line_the_claim_marked(self):
        self.assertEqual(self.id_of(self.claim()), "1")
        self.assertEqual(self.id_of(self.claim()), "2")
        r = self.cmd("complete", "2")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.real_boxes(), "~x  ")
        self.assert_prose_unchanged()

    def test_readiness_ignores_literals_between_a_barrier_and_a_group(self):
        self.assertEqual(self.id_of(self.claim()), "1")
        self.assertEqual(self.id_of(self.claim()), "2")
        # The barrier waits on the whole P1 group, not on any literal.
        self.assertEqual(self.claim().stdout.strip(), "")
        self.cmd("complete", "1")
        self.cmd("complete", "2")
        self.assertEqual(self.id_of(self.claim()), "3")
        # P2 waits on the in-progress barrier.
        self.assertEqual(self.claim().stdout.strip(), "")
        self.cmd("complete", "3")
        self.assertEqual(self.id_of(self.claim()), "4")
        self.assertEqual(self.real_boxes(), "xxx~")
        self.assert_prose_unchanged()

    def test_indented_checkbox_participates_and_keeps_its_indent(self):
        self.write_tasks(
            "## 1. Work\n"
            + PENDING + " 1.1 first\n"
            + "  " + PENDING + " 1.2 indented second\n")
        self.assertEqual(self.id_of(self.claim()), "1")
        self.cmd("complete", "1")
        r = self.claim()
        # The indented line is ordinal 2 and its text strips indent + marker.
        self.assertEqual(self.id_of(r), "2")
        self.assertEqual(r.stdout.rstrip("\n").split("\t", 1)[1],
                         "1.2 indented second")
        # The rewrite lands on that line and preserves its leading blanks.
        self.assertEqual(self.lines()[2], "  " + WIP + " 1.2 indented second")


if __name__ == "__main__":
    unittest.main()
