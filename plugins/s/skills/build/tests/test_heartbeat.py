#!/usr/bin/env python3
"""Tests for heartbeat.py — the autopilot's live run heartbeat writer.

Stdlib only: no test opens a terminal or imports a third-party package,
mirroring ``heartbeat.py`` itself staying dependency-free so importing the
delivery engine (``autopilot``) never requires ``textual``.
"""

import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
sys.path.insert(0, SCRIPTS)

import autopilot  # noqa: E402
import heartbeat  # noqa: E402


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def _member(slug, risk, state="unplanned", order=0, desc="a member"):
    return autopilot.Member(slug=slug, description=desc, risk=risk,
                            state=state, order=order)


class HeartbeatTestBase(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="heartbeat-test-")
        self._base_home = tempfile.mkdtemp(prefix="heartbeat-home-")
        self._old_home = os.environ.get("HOME")
        os.environ["HOME"] = self._base_home

    def tearDown(self):
        if self._old_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = self._old_home
        shutil.rmtree(self._base_home, ignore_errors=True)
        shutil.rmtree(self.root, ignore_errors=True)


# ---------------------------------------------------------------------------
# RunHeartbeat: atomic transition writes
# ---------------------------------------------------------------------------

class HeartbeatTest(HeartbeatTestBase):
    def _path(self, epic):
        return os.path.join(self.root, ".shipd", "autopilot",
                            "%s-heartbeat.json" % epic)

    def _read(self, epic):
        with open(self._path(epic), encoding="utf-8") as fh:
            return json.load(fh)

    def test_transitions_bump_seq_and_track_roster_state(self):
        hb = heartbeat.RunHeartbeat(self.root, "ep")
        to_drive = [_member("a", "low"), _member("b", "high")]
        hb.run_started(to_drive, [], "default")

        first = self._read("ep")
        self.assertEqual(first["epic"], "ep")
        self.assertEqual(first["state"], "running")
        self.assertEqual(first["provenance"], "default")
        roster = {r["slug"]: r for r in first["roster"]}
        self.assertEqual(roster["a"]["state"], "pending")
        self.assertEqual(roster["a"]["risk"], "low")
        self.assertEqual(roster["b"]["state"], "pending")
        start_seq = first["seq"]
        start_updated = first["updated_at"]

        hb.member_started("a")
        hb.stage_started("a", "build", 1)
        driving = self._read("ep")
        self.assertGreater(driving["seq"], start_seq)
        self.assertGreaterEqual(driving["updated_at"], start_updated)
        a_row = {r["slug"]: r for r in driving["roster"]}["a"]
        self.assertEqual(a_row["state"], "driving")
        self.assertEqual(a_row["stage"], "build")
        self.assertEqual(a_row["attempt"], 1)

        hb.member_finished(
            "a", autopilot.MemberResult(outcome="shipped",
                                        pr_url="http://pr/a"))
        shipped = self._read("ep")
        self.assertGreater(shipped["seq"], driving["seq"])
        a_done = {r["slug"]: r for r in shipped["roster"]}["a"]
        self.assertEqual(a_done["state"], "shipped")

        hb.run_finished("/tmp/ep-report.json")
        finished = self._read("ep")
        self.assertEqual(finished["state"], "finished")
        self.assertGreater(finished["seq"], shipped["seq"])

    def test_run_started_records_writer_identity(self):
        hb = heartbeat.RunHeartbeat(self.root, "ep")
        hb.run_started([_member("a", "low")], [], "default")
        state = self._read("ep")
        self.assertEqual(state["pid"], os.getpid())
        self.assertTrue(state["host"])

    def test_seq_is_monotonic_across_every_write(self):
        hb = heartbeat.RunHeartbeat(self.root, "ep")
        hb.run_started([_member("a", "low")], [], "default")
        seqs = [self._read("ep")["seq"]]
        hb.member_started("a")
        seqs.append(self._read("ep")["seq"])
        hb.stage_started("a", "plan", 1)
        seqs.append(self._read("ep")["seq"])
        hb.stage_started("a", "plan", 2)
        seqs.append(self._read("ep")["seq"])
        self.assertEqual(seqs, sorted(seqs))
        self.assertEqual(len(seqs), len(set(seqs)))

    def test_member_started_stamps_started_at_once(self):
        hb = heartbeat.RunHeartbeat(self.root, "ep")
        hb.run_started([_member("a", "low")], [], "default")
        hb.member_started("a")
        started_at = {r["slug"]: r for r in self._read("ep")["roster"]}["a"] \
            .get("started_at")
        self.assertIsNotNone(started_at,
                             "member_started should stamp started_at")
        self.assertGreater(started_at, 0)

        # A subsequent stage_started for the same member leaves it unchanged.
        hb.stage_started("a", "build", 1)
        again = {r["slug"]: r for r in self._read("ep")["roster"]}["a"]
        self.assertEqual(again["started_at"], started_at)

    def test_skipped_members_carry_their_state(self):
        hb = heartbeat.RunHeartbeat(self.root, "ep")
        hb.run_started([_member("go", "low")],
                       [_member("done", "low", state="archived")], "default")
        roster = {r["slug"]: r for r in self._read("ep")["roster"]}
        self.assertEqual(roster["done"]["state"], "skipped")
        self.assertEqual(roster["done"]["skipped_state"], "archived")

    def test_needs_human_records_recovery_context(self):
        hb = heartbeat.RunHeartbeat(self.root, "ep")
        hb.run_started([_member("a", "medium")], [], "default")
        hb.member_started("a")
        hb.stage_started("a", "build", 3)
        hb.member_finished(
            "a", autopilot.MemberResult(outcome="needs_human", stage="build",
                                        reason="grade unmet", session_id="sess-9"))
        row = {r["slug"]: r for r in self._read("ep")["roster"]}["a"]
        self.assertEqual(row["state"], "needs-human")
        self.assertEqual(row["stage"], "build")
        self.assertEqual(row["reason"], "grade unmet")
        self.assertEqual(row["session_id"], "sess-9")

    def test_write_failure_warns_once_and_never_raises(self):
        # Make the autopilot directory unwritable by planting a file where the
        # directory must go: makedirs then raises and the write is disabled.
        _write(os.path.join(self.root, ".shipd", "autopilot"), "not a dir")
        warnings = []
        hb = heartbeat.RunHeartbeat(self.root, "ep", out=warnings.append)
        # None of these raise, even though every write fails.
        hb.run_started([_member("a", "low")], [], "default")
        hb.member_started("a")
        hb.stage_started("a", "plan", 1)
        hb.member_finished("a", autopilot.MemberResult(outcome="shipped"))
        hb.run_finished("/tmp/r.json")
        self.assertEqual(len(warnings), 1)  # warned exactly once
        self.assertFalse(os.path.isfile(self._path("ep")))


if __name__ == "__main__":
    unittest.main()
