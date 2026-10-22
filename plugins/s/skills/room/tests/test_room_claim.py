#!/usr/bin/env python3
"""Tests for the review claim module (room_claim.py).

Every GitHub call goes through ``FakeClaimStore``, a fake of the ``gh`` seam
that holds git refs and commits in dicts: no ``gh`` process and no network.
The other room and review test suites reuse the store for their claim calls.
"""

import calendar
import email.utils
import json
import os
import re
import sys
import time
import unittest
import unittest.mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "scripts")))

import room  # noqa: E402
import room_claim  # noqa: E402

START = 1_700_000_000
HEAD = "a" * 40


class FakeClaimStore:
    """A ``gh`` fake for the git-ref, commit, status and repository calls the
    claim module makes. A ref create answers ``201`` once and ``422
    Reference already exists`` after; a ``PATCH`` always succeeds (custom refs
    have no compare-and-swap); commits take ``committer.date`` from the
    settable ``now``; ``gh api -i`` carries a ``Date`` header from the same
    clock; ``push`` is the answered ``permissions.push``."""

    def __init__(self, repo="o/r", push=True):
        self.repo = repo
        self.push = push
        self.now = START
        self.refs = {}          # "shipd/claims/..." -> commit sha
        self.commits = {}       # sha -> {"message", "tree", "date"}
        self.statuses = []      # (sha, payload)
        self.calls = []
        self.fail = []          # [prefix, stderr] answered rc 1 once
        self._n = 0

    # -- helpers -------------------------------------------------------------

    def handles(self, args):
        args = list(args)
        if args[:1] != ["api"]:
            return False
        path = next((a for a in args[1:] if not a.startswith("-")
                     and a != "POST" and a != "PATCH" and a != "DELETE"
                     and a != "GET"), "")
        base = ("repos/%s" % self.repo).lower()
        low = path.lower()
        return low == base or low.startswith(base + "/git/") \
            or low.startswith(base + "/statuses/")

    def _iso(self, when):
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(when))

    def _commit(self, message, tree, date=None):
        self._n += 1
        sha = "%040x" % (0xc0ffee00 + self._n)
        self.commits[sha] = {"message": message, "tree": tree,
                             "date": self.now if date is None else date}
        return sha

    def seed(self, number, agent, sha, gen, holder, state, age=0):
        """Create claim generation ``gen`` whose tip is ``age`` seconds old;
        state ``done`` creates the ``done`` ref instead of a generation."""
        prefix = room_claim.claim_prefix(number, agent, sha)
        message = room_claim._commit_message(holder, state, agent, sha)
        tip = self._commit(message, "tree-" + sha, self.now - age)
        name = "done" if state == "done" else str(gen)
        self.refs["%s/%s" % (prefix, name)] = tip
        return tip

    def under(self, prefix):
        return sorted(r for r in self.refs if r.startswith(prefix))

    def tip_info(self, ref):
        return room_claim._parse_message(
            self.commits[self.refs[ref]]["message"])

    def status_states(self):
        return [(p["context"], p["state"]) for _s, p in self.statuses]

    def writes(self):
        return [a for a, _i in self.calls if "-X" in a]

    # -- dispatch -----------------------------------------------------------

    def __call__(self, args, input=None):
        args = list(args)
        self.calls.append((args, input))
        for failure in self.fail:
            if all(any(want in arg for arg in args) for want in failure[0]):
                self.fail.remove(failure)
                return 1, "", failure[1]
        base = "repos/%s" % self.repo      # GitHub names ignore case
        method = args[args.index("-X") + 1] if "-X" in args else "GET"
        path = next(a for a in args[1:] if a.startswith("repos/"))
        rest = path[len(base):]
        if rest == "":
            if "-i" in args:
                date = email.utils.formatdate(self.now, usegmt=True)
                return 0, ("HTTP/2.0 200 OK\nContent-Type: x\nDate: %s\n\n"
                           "{}" % date), ""
            return 0, json.dumps({"permissions": {"push": self.push}}), ""
        if rest.startswith("/statuses/"):
            self.statuses.append((rest.rsplit("/", 1)[1], json.loads(input)))
            return 0, "{}", ""
        if rest.startswith("/git/matching-refs/"):
            prefix = rest[len("/git/matching-refs/"):]
            return 0, json.dumps([
                {"ref": "refs/" + r, "object": {"sha": s}}
                for r, s in sorted(self.refs.items())
                if r.startswith(prefix)]), ""
        if rest == "/git/commits" and method == "POST":
            payload = json.loads(input)
            sha = self._commit(payload["message"], payload["tree"])
            return 0, json.dumps({
                "sha": sha, "tree": {"sha": payload["tree"]},
                "committer": {"date": self._iso(self.now)}}), ""
        if rest.startswith("/git/commits/"):
            sha = rest.rsplit("/", 1)[1]
            commit = self.commits.get(sha) or {
                "message": "head", "tree": "tree-" + sha, "date": self.now}
            return 0, json.dumps({
                "sha": sha, "message": commit["message"],
                "tree": {"sha": commit["tree"]},
                "committer": {"date": self._iso(commit["date"])}}), ""
        if rest == "/git/refs" and method == "POST":
            payload = json.loads(input)
            ref = payload["ref"][len("refs/"):]
            if ref in self.refs:
                return 1, "", "gh: Reference already exists (HTTP 422)"
            self.refs[ref] = payload["sha"]
            return 0, "{}", ""
        if rest.startswith("/git/refs/") and method == "PATCH":
            ref = rest[len("/git/refs/"):]
            if ref not in self.refs:
                return 1, "", "gh: Not Found (HTTP 404)"
            self.refs[ref] = json.loads(input)["sha"]
            return 0, "{}", ""
        if rest.startswith("/git/refs/") and method == "DELETE":
            ref = rest[len("/git/refs/"):]
            if ref not in self.refs:
                return 1, "", "gh: Not Found (HTTP 404)"
            del self.refs[ref]
            return 0, "", ""
        raise AssertionError("unexpected claim gh call: %r" % (args,))


def prefix(number=7, agent="rev-b", sha=HEAD):
    return room_claim.claim_prefix(number, agent, sha)


class ClaimBase(unittest.TestCase):
    def setUp(self):
        self.gh = FakeClaimStore()
        patcher = unittest.mock.patch.dict(os.environ, {}, clear=False)
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop(room_claim.CLAIM_ENV, None)

    def acquire(self, holder="h1", gh=None):
        return room_claim.acquire(gh or self.gh, "o/r", 7, "rev-b", HEAD,
                                  holder)


class AcquireTest(ClaimBase):
    """room-review-claim"""

    def test_no_claim_wins_generation_one(self):
        kind, claim = self.acquire()
        self.assertEqual(kind, "won")
        self.assertEqual(claim.gen, 1)
        self.assertEqual(self.gh.under(prefix()), [prefix() + "/1"])
        self.assertEqual(self.gh.tip_info(prefix() + "/1")["state"],
                         "claimed")
        self.assertEqual(claim.ref, "refs/" + prefix() + "/1")

    def test_the_agent_slash_becomes_an_underscore(self):
        self.assertEqual(room_claim.claim_prefix(7, "a/b", "abc"),
                         "shipd/claims/pr-7/a_b/abc")

    def test_the_claim_commit_reuses_the_head_tree_and_has_no_parent(self):
        kind, claim = self.acquire()
        self.assertEqual(claim.tree, "tree-" + HEAD)
        commit_posts = [json.loads(i) for a, i in self.gh.calls
                        if "POST" in a and "repos/o/r/git/commits" in a]
        self.assertEqual(commit_posts[0]["parents"], [])
        self.assertEqual(commit_posts[0]["tree"], "tree-" + HEAD)

    def test_a_live_claim_of_another_holder_is_held(self):
        self.gh.seed(7, "rev-b", HEAD, 1, "other:1:abcd", "beat", age=30)
        kind, info = self.acquire()
        self.assertEqual(kind, "held")
        self.assertEqual(info["holder"], "other:1:abcd")
        self.assertEqual(info["gen"], 1)
        self.assertEqual(self.gh.under(prefix()), [prefix() + "/1"])

    def test_a_done_claim_is_done(self):
        self.gh.seed(7, "rev-b", HEAD, 1, "other", "done", age=5000)
        kind, info = self.acquire()
        self.assertEqual(kind, "done")
        self.assertEqual(info["holder"], "other")
        self.assertEqual(len(self.gh.under(prefix())), 1)

    def test_a_released_claim_is_taken_over_by_generation_two(self):
        self.gh.seed(7, "rev-b", HEAD, 1, "other", "released", age=1)
        kind, claim = self.acquire()
        self.assertEqual((kind, claim.gen), ("won", 2))
        self.assertEqual(len(self.gh.under(prefix())), 2)

    def test_a_stale_claim_is_taken_over_by_generation_two(self):
        self.gh.seed(7, "rev-b", HEAD, 1, "other", "beat", age=601)
        kind, claim = self.acquire()
        self.assertEqual((kind, claim.gen), ("won", 2))

    def test_a_claim_600_seconds_old_is_still_live(self):
        self.gh.seed(7, "rev-b", HEAD, 1, "other", "beat", age=600)
        self.assertEqual(self.acquire()[0], "held")

    def test_a_lost_create_race_is_held(self):
        real = self.gh.__call__

        def racing(args, input=None):
            # The other runner's create lands between our list and create.
            if "repos/o/r/git/refs" in args and "POST" in args and \
                    not self.gh.refs:
                self.gh.seed(7, "rev-b", HEAD, 1, "rival", "claimed")
            return real(args, input)

        kind, info = room_claim.acquire(racing, "o/r", 7, "rev-b", HEAD,
                                        "me")
        self.assertEqual(kind, "held")
        self.assertEqual(info["holder"], "rival")
        self.assertEqual(len(self.gh.under(prefix())), 1)

    def test_a_lost_race_against_a_done_claim_is_done(self):
        real = self.gh.__call__

        def racing(args, input=None):
            if "repos/o/r/git/refs" in args and "POST" in args and \
                    not self.gh.refs:
                self.gh.seed(7, "rev-b", HEAD, 1, "rival", "claimed")
                self.gh.seed(7, "rev-b", HEAD, 1, "rival", "done")
            return real(args, input)

        kind, _info = room_claim.acquire(racing, "o/r", 7, "rev-b", HEAD,
                                         "me")
        self.assertEqual(kind, "done")

    def test_another_head_is_a_separate_claim(self):
        self.gh.seed(7, "rev-b", HEAD, 1, "other", "beat", age=1)
        kind, claim = room_claim.acquire(self.gh, "o/r", 7, "rev-b",
                                         "b" * 40, "me")
        self.assertEqual((kind, claim.gen), ("won", 1))

    def test_a_failed_list_raises(self):
        self.gh.fail.append([["matching-refs"], "boom"])
        with self.assertRaises(room.RoomError):
            self.acquire()

    def test_the_holder_id_is_stable_and_shaped(self):
        first = room_claim.holder_id()
        self.assertEqual(first, room_claim.holder_id())
        self.assertRegex(first, r"^.+:\d+:[0-9a-f]{8}$")

    def test_the_claim_round_trips_through_the_environment(self):
        kind, claim = self.acquire()
        again = room_claim.Claim.from_env(claim.to_env())
        self.assertEqual(again.to_env(), claim.to_env())
        self.assertEqual(again.ref, claim.ref)
        with self.assertRaises(room.RoomError):
            room_claim.Claim.from_env("not json")


class BeatTest(ClaimBase):
    def test_beat_moves_the_ref_to_a_new_commit_and_updates_the_claim(self):
        _kind, claim = self.acquire()
        first = claim.tip
        self.gh.now += 60
        room_claim.beat(self.gh, claim)
        self.assertNotEqual(claim.tip, first)
        self.assertEqual(self.gh.refs[prefix() + "/1"], claim.tip)
        self.assertEqual(claim.last_beat, self.gh.now)
        self.assertEqual(self.gh.tip_info(prefix() + "/1")["state"], "beat")
        self.assertEqual(self.gh.commits[claim.tip]["date"], self.gh.now)

    def test_beat_with_a_state_writes_that_state(self):
        _kind, claim = self.acquire()
        room_claim.beat(self.gh, claim, "released")
        self.assertEqual(self.gh.tip_info(prefix() + "/1")["state"],
                         "released")

    def test_a_failed_patch_raises(self):
        _kind, claim = self.acquire()
        self.gh.fail.append([["PATCH"], "HTTP 500"])
        with self.assertRaises(room.RoomError):
            room_claim.beat(self.gh, claim)


class FenceTest(ClaimBase):
    def test_a_fresh_claim_passes_and_beats(self):
        _kind, claim = self.acquire()
        self.gh.now += 20
        room_claim.fence(self.gh, claim)
        self.assertEqual(self.gh.tip_info(prefix() + "/1")["state"], "beat")
        self.assertEqual(claim.last_beat, self.gh.now)

    def test_a_newer_generation_raises(self):
        _kind, claim = self.acquire()
        self.gh.seed(7, "rev-b", HEAD, 2, "rival", "claimed")
        with self.assertRaises(room.RoomError) as ctx:
            room_claim.fence(self.gh, claim)
        self.assertIn("newer", str(ctx.exception))

    def test_a_wrong_holder_raises(self):
        _kind, claim = self.acquire()
        claim.holder = "someone-else"
        with self.assertRaises(room.RoomError) as ctx:
            room_claim.fence(self.gh, claim)
        self.assertIn("held by", str(ctx.exception))

    def test_a_released_tip_raises(self):
        _kind, claim = self.acquire()
        room_claim.beat(self.gh, claim, "released")
        with self.assertRaises(room.RoomError):
            room_claim.fence(self.gh, claim)

    def test_a_301_second_old_tip_raises(self):
        _kind, claim = self.acquire()
        self.gh.now += 301
        with self.assertRaises(room.RoomError) as ctx:
            room_claim.fence(self.gh, claim)
        self.assertIn("heartbeat", str(ctx.exception))

    def test_a_299_second_old_tip_passes(self):
        _kind, claim = self.acquire()
        self.gh.now += 299
        room_claim.fence(self.gh, claim)


class DoneRefTest(ClaimBase):
    def test_mark_done_creates_the_done_ref_once(self):
        _kind, claim = self.acquire()
        room_claim.mark_done(self.gh, claim)
        room_claim.mark_done(self.gh, claim)      # 422 already exists
        self.assertEqual(self.gh.under(prefix()),
                         [prefix() + "/1", prefix() + "/done"])
        self.assertEqual(self.gh.tip_info(prefix() + "/done")["state"],
                         "done")

    def test_the_done_ref_is_not_a_generation(self):
        _kind, claim = self.acquire()
        room_claim.mark_done(self.gh, claim)
        gens = room_claim._generations(self.gh, "o/r", prefix())
        self.assertEqual([g for g, _r, _t in gens], [1])

    def test_fence_raises_once_done(self):
        _kind, claim = self.acquire()
        room_claim.mark_done(self.gh, claim)
        with self.assertRaises(room.RoomError) as ctx:
            room_claim.fence(self.gh, claim)
        self.assertIn("done", str(ctx.exception))

    def test_another_422_is_not_an_existing_ref(self):
        _kind, claim = self.acquire()
        self.gh.fail.append([["git/refs"],
                             "gh: Validation Failed (HTTP 422)"])
        with self.assertRaises(room.RoomError):
            room_claim.mark_done(self.gh, claim)

    def test_a_non_exists_422_on_acquire_raises(self):
        self.gh.fail.append([["git/refs"],
                             "gh: Validation Failed (HTTP 422)"])
        with self.assertRaises(room.RoomError):
            self.acquire()

    def test_is_exists_matches_only_reference_already_exists(self):
        self.assertTrue(room_claim._is_exists(
            1, "", "gh: REFERENCE ALREADY EXISTS (HTTP 422)"))
        self.assertFalse(room_claim._is_exists(1, "", "HTTP 422"))
        self.assertFalse(room_claim._is_exists(0, "", "already exists"))


class HeartbeatTest(ClaimBase):
    def test_the_thread_beats_until_stopped(self):
        _kind, claim = self.acquire()
        beater = room_claim.Heartbeat(self.gh, claim, interval=0.01).start()
        deadline = time.time() + 5
        while time.time() < deadline and \
                self.gh.tip_info(prefix() + "/1")["state"] != "beat":
            time.sleep(0.01)
        beater.stop()
        self.assertEqual(self.gh.tip_info(prefix() + "/1")["state"], "beat")

    def test_a_failed_beat_warns_and_keeps_trying(self):
        _kind, claim = self.acquire()
        self.gh.fail.append([["PATCH"], "HTTP 500"])
        err = io_stderr()
        with unittest.mock.patch.object(sys, "stderr", err):
            beater = room_claim.Heartbeat(self.gh, claim,
                                          interval=0.01).start()
            deadline = time.time() + 5
            while time.time() < deadline and \
                    self.gh.tip_info(prefix() + "/1")["state"] != "beat":
                time.sleep(0.01)
            beater.stop()
        self.assertIn("warning:", err.getvalue())
        self.assertEqual(self.gh.tip_info(prefix() + "/1")["state"], "beat")

    def test_a_done_claim_is_not_beaten_over(self):
        _kind, claim = self.acquire()
        room_claim.mark_done(self.gh, claim)
        before = self.gh.refs[prefix() + "/1"]
        beater = room_claim.Heartbeat(self.gh, claim, interval=0.01).start()
        time.sleep(0.1)
        beater.stop()
        self.assertEqual(self.gh.refs[prefix() + "/1"], before)

    def test_a_beat_after_done_does_not_undo_done(self):
        _kind, claim = self.acquire()
        room_claim.mark_done(self.gh, claim)
        room_claim.beat(self.gh, claim)      # a heartbeat already in flight
        self.assertTrue(room_claim.is_done(self.gh, "o/r", claim))
        kind, _info = self.acquire(holder="h2")
        self.assertEqual(kind, "done")
        self.gh.statuses.clear()
        before = len(self.gh.writes())
        room_claim._release(self.gh, claim)
        self.assertEqual(len(self.gh.writes()), before)
        self.assertEqual(self.gh.statuses, [])


def io_stderr():
    import io
    return io.StringIO()


class ClaimedTurnTest(ClaimBase):
    """room-review-claim, room-review-status"""

    def turn(self, run, gh=None):
        return room_claim.claimed_turn(gh or self.gh, "o/r", 7, "rev-b",
                                       HEAD, run)

    def test_a_win_runs_with_pending_status_and_the_env(self):
        seen = {}

        def run():
            seen["env"] = os.environ.get(room_claim.CLAIM_ENV)
            seen["statuses"] = list(self.gh.statuses)
            return "result"

        outcome, result = self.turn(run)
        self.assertEqual((outcome, result), ("ran", "result"))
        self.assertEqual(room_claim.Claim.from_env(seen["env"]).gen, 1)
        sha, payload = seen["statuses"][0]
        self.assertEqual(sha, HEAD)
        self.assertEqual(payload["context"], "room-review/rev-b")
        self.assertEqual(payload["state"], "pending")
        self.assertNotIn(room_claim.CLAIM_ENV, os.environ)

    def test_a_turn_that_posts_nothing_releases_the_claim(self):
        self.turn(lambda: None)
        self.assertEqual(self.gh.tip_info(prefix() + "/1")["state"],
                         "released")
        self.assertEqual(self.gh.status_states()[-1],
                         ("room-review/rev-b", "pending"))
        self.assertIn("released", self.gh.statuses[-1][1]["description"])

    def test_a_done_claim_stays_done_after_the_turn(self):
        def run():
            claim = room_claim.Claim.from_env(
                os.environ[room_claim.CLAIM_ENV])
            room_claim.mark_done(self.gh, claim)

        self.turn(run)
        self.assertTrue(room_claim.is_done(self.gh, "o/r", prefix()))
        self.assertEqual(self.gh.tip_info(prefix() + "/1")["state"],
                         "claimed")
        self.assertEqual(len(self.gh.statuses), 1)

    def test_a_raising_turn_still_releases(self):
        def run():
            raise KeyboardInterrupt

        with self.assertRaises(KeyboardInterrupt):
            self.turn(run)
        self.assertEqual(self.gh.tip_info(prefix() + "/1")["state"],
                         "released")
        self.assertNotIn(room_claim.CLAIM_ENV, os.environ)

    def test_a_held_claim_runs_nothing(self):
        self.gh.seed(7, "rev-b", HEAD, 1, "other:9:ffff", "beat", age=10)
        calls = []
        err = io_stderr()
        with unittest.mock.patch.object(sys, "stderr", err):
            outcome, result = self.turn(lambda: calls.append(1))
        self.assertEqual((outcome, result), ("held", None))
        self.assertEqual(calls, [])
        self.assertIn("is claimed by other:9:ffff; skipping", err.getvalue())
        self.assertEqual(self.gh.statuses, [])

    def test_a_done_claim_runs_nothing(self):
        self.gh.seed(7, "rev-b", HEAD, 1, "other", "done")
        calls = []
        err = io_stderr()
        with unittest.mock.patch.object(sys, "stderr", err):
            outcome, _r = self.turn(lambda: calls.append(1))
        self.assertEqual(outcome, "done")
        self.assertEqual(calls, [])
        self.assertIn("was already reviewed by other", err.getvalue())

    def test_an_unreadable_head_is_held(self):
        calls = []
        outcome, _r = room_claim.claimed_turn(
            self.gh, "o/r", 7, "rev-b", "", lambda: calls.append(1))
        self.assertEqual(outcome, "held")
        self.assertEqual(calls, [])
        self.assertEqual(self.gh.calls, [])


class PermissionAndCleanupTest(ClaimBase):
    """room-review-claim-permission, room-review-claim-cleanup"""

    def test_can_claim_reads_push(self):
        self.assertTrue(room_claim.can_claim(self.gh, "o/r"))
        self.gh.push = False
        self.assertFalse(room_claim.can_claim(self.gh, "o/r"))

    def test_delete_pr_claims_removes_every_ref_of_that_pr_only(self):
        self.gh.seed(7, "rev-b", HEAD, 1, "x", "beat")
        self.gh.seed(7, "rev-b", HEAD, 1, "x", "done")
        self.gh.seed(7, "rev-c", "b" * 40, 1, "x", "beat")
        self.gh.seed(70, "rev-b", HEAD, 1, "x", "beat")
        count = room_claim.delete_pr_claims(self.gh, "o/r", 7)
        self.assertEqual(count, 3)
        self.assertEqual(list(self.gh.refs),
                         [room_claim.claim_prefix(70, "rev-b", HEAD) + "/1"])

    def test_delete_pr_claims_lets_errors_raise(self):
        self.gh.seed(7, "rev-b", HEAD, 1, "x", "done")
        self.gh.fail.append([["DELETE"], "HTTP 403"])
        with self.assertRaises(room.RoomError):
            room_claim.delete_pr_claims(self.gh, "o/r", 7)

    def test_set_status_posts_the_context(self):
        room_claim.set_status(self.gh, "o/r", HEAD, "rev-b", "success", "ok")
        self.assertEqual(self.gh.statuses[0][0], HEAD)
        self.assertEqual(self.gh.statuses[0][1], {
            "state": "success", "context": "room-review/rev-b",
            "description": "ok"})


if __name__ == "__main__":
    unittest.main()
