#!/usr/bin/env python3
"""Tests for dashboard.py's build-heartbeat aggregation and the pure activity
predicates that drive the header-bar indicator (delivery-dashboard board-tui
spec).

``dashboard.py`` top-imports ``textual`` for its App/widget classes, so a plain
``import dashboard`` requires ``textual``. The build-heartbeat discovery/attach
(:func:`attach_build_heartbeats`) and the pure count/marker predicates
(:func:`activity_counts`, :func:`indicator_marker`) are defined ahead of that
module-scope import specifically so this suite exercises them under the system
``python3`` with ``textual`` NOT installed — :func:`_load_dashboard_stdlib`
executes the module and swallows the ``ImportError`` the ``textual`` import
raises, leaving every helper defined up to that point in the namespace (the
pattern ``test_change_artifacts`` uses)."""

import importlib.util
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.normpath(os.path.join(HERE, "..", "scripts"))
DASHBOARD_PATH = os.path.join(SCRIPTS_DIR, "dashboard.py")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import build_report as br  # noqa: E402


def _load_dashboard_stdlib():
    spec = importlib.util.spec_from_file_location(
        "dashboard_stdlib_probe_activity", DASHBOARD_PATH)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except ImportError:
        pass
    return module


def _run_heartbeat(state="running", updated_at=None):
    return {"epic": "ep", "state": state, "seq": 1,
            "updated_at": updated_at, "roster": []}


def _member(slug, location="/x"):
    return {"slug": slug, "description": "d", "risk": "low",
            "state": "active", "location": location, "actions": []}


def _build_hb(state="running", updated_at=None, transcript_mtime=None,
              session_id=None, location=None):
    hb = {"slug": "m", "kind": "build", "state": state, "seq": 1}
    if updated_at is not None:
        hb["updated_at"] = updated_at
    if transcript_mtime is not None:
        hb["transcript_mtime"] = transcript_mtime
    if session_id is not None:
        hb["session_id"] = session_id
    if location is not None:
        hb["location"] = location
    return hb


def _board(epics=(), standalone=()):
    return {"root": "/x", "generated_at": 0.0, "epics": list(epics),
            "groups": [], "standalone": list(standalone)}


class _BuildHeartbeatFixture(unittest.TestCase):
    """An isolated ``CLAUDE_CONFIG_DIR`` plus helpers to plant build-heartbeat
    files and session transcripts at the exact paths the resolvers expect. The
    real ``~/.claude`` is never read."""

    @classmethod
    def setUpClass(cls):
        cls.dashboard = _load_dashboard_stdlib()

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="board-activity-root-")
        self.config = tempfile.mkdtemp(prefix="board-activity-cfg-")
        self._old_cfg = os.environ.get("CLAUDE_CONFIG_DIR")
        os.environ["CLAUDE_CONFIG_DIR"] = self.config

    def tearDown(self):
        if self._old_cfg is None:
            os.environ.pop("CLAUDE_CONFIG_DIR", None)
        else:
            os.environ["CLAUDE_CONFIG_DIR"] = self._old_cfg
        shutil.rmtree(self.root, ignore_errors=True)
        shutil.rmtree(self.config, ignore_errors=True)

    def _write_build_hb(self, slug, **fields):
        self._write_build_hb_at(self.root, slug, **fields)

    def _write_build_hb_at(self, base, slug, **fields):
        """Plant a build heartbeat under ``<base>/.shipd/autopilot/``."""
        path = os.path.join(base, ".shipd", "autopilot",
                            "%s-build-heartbeat.json" % slug)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = {"slug": slug, "kind": "build"}
        data.update(fields)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh)

    def _write_transcript(self, location, session_id):
        tdir = os.path.join(self.config, "projects",
                            br.project_slug(location))
        os.makedirs(tdir, exist_ok=True)
        path = os.path.join(tdir, session_id + ".jsonl")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"type": "assistant",
                                 "timestamp": "2026-01-01T00:00:10Z",
                                 "message": {"id": "a", "model": "m",
                                             "usage": {"output_tokens": 1}}})
                     + "\n")
        return path


class BuildHeartbeatAttachTest(_BuildHeartbeatFixture):
    """``attach_build_heartbeats`` discovers ``*-build-heartbeat.json`` files
    under the content dir's ``autopilot/`` and attaches each to its slug-
    matching member (epic member and standalone alike), stamping the resolved
    transcript's mtime when one resolves."""

    def test_attaches_to_epic_member_with_transcript_mtime(self):
        self._write_build_hb("m", state="running", session_id="sess-x",
                             location=self.root, updated_at=time.time())
        path = self._write_transcript(self.root, "sess-x")
        board = _board(epics=[{"slug": "ep", "status": "active",
                               "heartbeat": None,
                               "members": [_member("m", self.root)]}])
        self.dashboard.attach_build_heartbeats(self.root, board)
        hb = board["epics"][0]["members"][0]["build_heartbeat"]
        self.assertEqual(hb["state"], "running")
        self.assertAlmostEqual(hb["transcript_mtime"],
                               os.path.getmtime(path), places=3)

    def test_attaches_to_standalone_member(self):
        self._write_build_hb("solo", state="running", session_id="sess-y",
                             location=self.root)
        board = _board(standalone=[_member("solo", self.root)])
        self.dashboard.attach_build_heartbeats(self.root, board)
        self.assertEqual(
            board["standalone"][0]["build_heartbeat"]["state"], "running")

    def test_no_transcript_omits_mtime(self):
        self._write_build_hb("m", state="running", session_id="missing",
                             location=self.root)
        board = _board(epics=[{"slug": "ep", "status": "active",
                               "heartbeat": None,
                               "members": [_member("m", self.root)]}])
        self.dashboard.attach_build_heartbeats(self.root, board)
        hb = board["epics"][0]["members"][0]["build_heartbeat"]
        self.assertNotIn("transcript_mtime", hb)


class WorktreeBuildHeartbeatDiscoveryTest(_BuildHeartbeatFixture):
    """A build runs in its change's worktree, so its heartbeat lands under
    ``.worktrees/<name>/<content-dir>/autopilot/``. Aggregating from the main
    checkout SHALL discover those worktree-hosted heartbeats too, and — when a
    slug is contested between the invocation root and a worktree — the newest
    ``updated_at`` wins (build-heartbeat-cli)."""

    def test_discovers_worktree_heartbeat_when_root_has_none(self):
        wt = os.path.join(self.root, ".worktrees", "feat")
        self._write_build_hb_at(wt, "feat", state="running",
                                updated_at=time.time())
        found = self.dashboard._discover_build_heartbeats(self.root)
        self.assertIn("feat", found)
        self.assertEqual(found["feat"]["state"], "running")

    def test_worktree_heartbeat_attaches_to_its_member(self):
        wt = os.path.join(self.root, ".worktrees", "feat")
        self._write_build_hb_at(wt, "feat", state="running",
                                updated_at=time.time())
        board = _board(standalone=[_member("feat", wt)])
        self.dashboard.attach_build_heartbeats(self.root, board)
        self.assertEqual(
            board["standalone"][0]["build_heartbeat"]["state"], "running")

    def test_newest_updated_at_wins_a_contested_slug(self):
        wt = os.path.join(self.root, ".worktrees", "feat")
        self._write_build_hb_at(self.root, "feat", state="finished",
                                updated_at=100.0)
        self._write_build_hb_at(wt, "feat", state="running",
                                updated_at=200.0)
        found = self.dashboard._discover_build_heartbeats(self.root)
        self.assertEqual(found["feat"]["state"], "running")
        self.assertEqual(found["feat"]["updated_at"], 200.0)

    def test_root_wins_when_it_is_the_newer_stamp(self):
        wt = os.path.join(self.root, ".worktrees", "feat")
        self._write_build_hb_at(self.root, "feat", state="running",
                                updated_at=300.0)
        self._write_build_hb_at(wt, "feat", state="finished",
                                updated_at=200.0)
        found = self.dashboard._discover_build_heartbeats(self.root)
        self.assertEqual(found["feat"]["state"], "running")
        self.assertEqual(found["feat"]["updated_at"], 300.0)


class ActivityCountsTest(unittest.TestCase):
    """``activity_counts(board, now)`` returns ``(live_runs, live_builds)``,
    the run count honoring the 3600 s window and the build count the 600 s
    window over the newer of a build heartbeat's ``updated_at`` and its
    aggregation-stamped ``transcript_mtime``."""

    @classmethod
    def setUpClass(cls):
        cls.dashboard = _load_dashboard_stdlib()

    def _epic(self, heartbeat, members=()):
        return {"slug": "ep", "status": "active", "heartbeat": heartbeat,
                "members": list(members)}

    def test_fresh_run_counts_as_a_live_run(self):
        board = _board(epics=[self._epic(_run_heartbeat("running", 950.0))])
        self.assertEqual(self.dashboard.activity_counts(board, now=1000.0),
                         (1, 0))

    def test_stale_run_is_not_counted(self):
        board = _board(epics=[self._epic(_run_heartbeat("running",
                                                        1000.0 - 3601))])
        self.assertEqual(self.dashboard.activity_counts(board, now=1000.0),
                         (0, 0))

    def test_fresh_build_counts_as_a_live_build(self):
        member = _member("m")
        member["build_heartbeat"] = _build_hb("running", updated_at=995.0)
        board = _board(epics=[self._epic(None, [member])])
        self.assertEqual(self.dashboard.activity_counts(board, now=1000.0),
                         (0, 1))

    def test_transcript_mtime_keeps_a_silent_build_live(self):
        # `updated_at` is stale but the transcript mtime is fresh — the newer
        # of the two governs, so the build stays live.
        member = _member("m")
        member["build_heartbeat"] = _build_hb(
            "running", updated_at=1000.0 - 700, transcript_mtime=995.0)
        board = _board(standalone=[member])
        self.assertEqual(self.dashboard.activity_counts(board, now=1000.0),
                         (0, 1))

    def test_build_stale_on_both_stamps_is_idle(self):
        member = _member("m")
        member["build_heartbeat"] = _build_hb(
            "running", updated_at=1000.0 - 700, transcript_mtime=1000.0 - 800)
        board = _board(standalone=[member])
        self.assertEqual(self.dashboard.activity_counts(board, now=1000.0),
                         (0, 0))


class IndicatorMarkerTest(unittest.TestCase):
    """``indicator_marker(board, now)`` renders the header indicator by the
    precedence autopilot > building > idle, appending ``(N)`` when N > 1."""

    @classmethod
    def setUpClass(cls):
        cls.dashboard = _load_dashboard_stdlib()

    def _run_epic(self, updated_at, slug="ep"):
        return {"slug": slug, "status": "active",
                "heartbeat": _run_heartbeat("running", updated_at),
                "members": []}

    def _build_member(self, slug="m"):
        member = _member(slug)
        member["build_heartbeat"] = _build_hb("running", updated_at=995.0)
        return member

    def test_single_run_shows_autopilot_on(self):
        board = _board(epics=[self._run_epic(995.0)])
        marker = self.dashboard.indicator_marker(board, now=1000.0)
        self.assertIn("autopilot on", marker)
        self.assertIn("$success", marker)

    def test_multiple_runs_show_the_count(self):
        board = _board(epics=[self._run_epic(995.0, "e1"),
                              self._run_epic(996.0, "e2")])
        self.assertIn("autopilot (2)",
                      self.dashboard.indicator_marker(board, now=1000.0))

    def test_single_build_shows_building(self):
        board = _board(standalone=[self._build_member()])
        marker = self.dashboard.indicator_marker(board, now=1000.0)
        self.assertIn("building", marker)
        self.assertIn("$lane-building", marker)
        self.assertNotIn("(", marker)

    def test_multiple_builds_show_the_count(self):
        board = _board(standalone=[self._build_member("m1"),
                                   self._build_member("m2")])
        self.assertIn("building (2)",
                      self.dashboard.indicator_marker(board, now=1000.0))

    def test_run_takes_precedence_over_build(self):
        board = _board(epics=[self._run_epic(995.0)],
                       standalone=[self._build_member()])
        self.assertIn("autopilot on",
                      self.dashboard.indicator_marker(board, now=1000.0))

    def test_idle_marker_when_nothing_live(self):
        board = _board()
        self.assertIn("idle",
                      self.dashboard.indicator_marker(board, now=1000.0))


class MemberSignalTest(unittest.TestCase):
    """``member_signal(member, entry)`` — the pure, dependency-free predicate
    (delivery-dashboard board-parked-member-signal spec) that yields a parked
    member's glyph/label/reason, or ``None`` for a normally-progressing one."""

    @classmethod
    def setUpClass(cls):
        cls.dashboard = _load_dashboard_stdlib()

    def test_rejected_state_yields_the_warning_glyph(self):
        member = _member("m")
        entry = {"state": "rejected", "reason": "context insufficient"}
        signal = self.dashboard.member_signal(member, entry)
        self.assertEqual(signal, {"kind": "rejected", "glyph": "⚠",
                                  "label": "rejected",
                                  "reason": "context insufficient"})

    def test_needs_human_state_yields_the_stop_glyph(self):
        member = _member("m")
        entry = {"state": "needs-human", "reason": None}
        signal = self.dashboard.member_signal(member, entry)
        self.assertEqual(signal, {"kind": "needs-human", "glyph": "⛔",
                                  "label": "needs-human", "reason": None})

    def test_stale_entry_yields_the_dagger_glyph_and_death_age(self):
        member = _member("m")
        entry = {"state": "driving", "stage": "died 8h ago", "stale": True}
        signal = self.dashboard.member_signal(member, entry)
        self.assertEqual(signal, {"kind": "stale", "glyph": "†",
                                  "label": "stale (died 8h ago)",
                                  "reason": None})

    def test_drafted_state_yields_the_informational_glyph(self):
        # A drafted member (delivery-dashboard board-drafted-member spec) is
        # not parked — its signal is informational, carrying the entry's
        # reason when present.
        member = _member("m")
        signal = self.dashboard.member_signal(member, {"state": "drafted"})
        self.assertEqual(signal, {"kind": "drafted", "glyph": "◇",
                                  "label": "drafted", "reason": None})
        with_reason = self.dashboard.member_signal(
            member, {"state": "drafted", "reason": "awaiting review"})
        self.assertEqual(with_reason["reason"], "awaiting review")

    def test_drafted_member_state_yields_the_signal_without_an_entry(self):
        member = dict(_member("m"), state="drafted")
        self.assertEqual(self.dashboard.member_signal(member, {})["kind"],
                         "drafted")

    def test_driving_ready_and_shipped_members_yield_no_signal(self):
        member = _member("m")
        self.assertIsNone(self.dashboard.member_signal(
            member, {"state": "driving", "stage": "build"}))
        self.assertIsNone(self.dashboard.member_signal(
            dict(member, state="ready"), {}))
        self.assertIsNone(self.dashboard.member_signal(
            member, {"state": "shipped"}))


class RunIsDeadTest(unittest.TestCase):
    """``run_is_dead(heartbeat, now, host)`` — the dependency-free liveness
    probe (delivery-dashboard board-dead-run-detection spec): while the
    heartbeat's recorded ``host`` matches the reader's, alive iff the recorded
    ``pid`` is a live process; otherwise (a cross-host heartbeat, or one with
    no ``pid``) alive iff ``updated_at`` is within ``AUTOPILOT_FRESH_SECONDS``
    of ``now``."""

    @classmethod
    def setUpClass(cls):
        cls.dashboard = _load_dashboard_stdlib()

    def _dead_pid(self):
        # A process that has already exited: its pid is guaranteed not alive
        # (no live-process false positive), unlike an arbitrary large number.
        p = subprocess.Popen([sys.executable, "-c", "pass"])
        p.wait()
        return p.pid

    def test_same_host_dead_pid_is_dead(self):
        hb = {"host": "h1", "pid": self._dead_pid(), "updated_at": time.time()}
        self.assertTrue(self.dashboard.run_is_dead(hb, host="h1"))

    def test_same_host_live_pid_is_alive(self):
        hb = {"host": "h1", "pid": os.getpid(), "updated_at": time.time()}
        self.assertFalse(self.dashboard.run_is_dead(hb, host="h1"))

    def test_cross_host_recent_update_is_alive_regardless_of_dead_pid(self):
        hb = {"host": "writer", "pid": self._dead_pid(), "updated_at": 1000.0}
        self.assertFalse(
            self.dashboard.run_is_dead(hb, now=1000.0 + 100, host="reader"))

    def test_cross_host_stale_update_is_dead_regardless_of_live_pid(self):
        hb = {"host": "writer", "pid": os.getpid(), "updated_at": 1000.0}
        fresh = self.dashboard.AUTOPILOT_FRESH_SECONDS
        self.assertTrue(
            self.dashboard.run_is_dead(hb, now=1000.0 + fresh + 1,
                                       host="reader"))

    def test_no_pid_falls_back_to_the_time_window(self):
        hb = {"host": "h1", "updated_at": 1000.0}
        fresh = self.dashboard.AUTOPILOT_FRESH_SECONDS
        self.assertFalse(
            self.dashboard.run_is_dead(hb, now=1000.0 + 10, host="h1"))
        self.assertTrue(
            self.dashboard.run_is_dead(hb, now=1000.0 + fresh + 1, host="h1"))


class LaneDeadRunTest(unittest.TestCase):
    """A ``driving`` roster member of a dead run (delivery-dashboard board-
    dead-run-detection spec) renders in the ``building`` lane as a stale card
    carrying its death age, instead of an actively driving card — while a
    live run's ``driving`` member is unaffected."""

    @classmethod
    def setUpClass(cls):
        cls.dashboard = _load_dashboard_stdlib()

    def _dead_pid(self):
        p = subprocess.Popen([sys.executable, "-c", "pass"])
        p.wait()
        return p.pid

    def _epic(self, heartbeat, members):
        return {"slug": "ep", "status": "active", "heartbeat": heartbeat,
                "members": members}

    def _entry_in(self, contents, lane):
        self.assertEqual(len(contents[lane]), 1)
        _epic_slug, _status, _member, entry, _project = contents[lane][0]
        return entry

    def test_dead_runs_driving_member_is_stale_in_building(self):
        hb = {"state": "running", "host": socket.gethostname(),
              "pid": self._dead_pid(), "updated_at": 1000.0,
              "roster": [{"slug": "a", "state": "driving", "stage": "build"}]}
        board = _board(epics=[self._epic(hb, [_member("a")])])
        contents = self.dashboard._lane_contents(board, now=1000.0)
        entry = self._entry_in(contents, "building")
        self.assertTrue(entry.get("stale"))
        self.assertIn("ago", entry.get("stage", ""))
        self.assertEqual(contents["review"], [])

    def test_dead_runs_driving_member_in_review_still_lands_in_building(self):
        hb = {"state": "running", "host": socket.gethostname(),
              "pid": self._dead_pid(), "updated_at": 1000.0,
              "roster": [{"slug": "a", "state": "driving", "stage": "review"}]}
        board = _board(epics=[self._epic(hb, [_member("a")])])
        contents = self.dashboard._lane_contents(board, now=1000.0)
        self.assertEqual(contents["review"], [])
        entry = self._entry_in(contents, "building")
        self.assertTrue(entry.get("stale"))

    def test_live_runs_driving_member_stays_actively_driving(self):
        hb = {"state": "running", "host": socket.gethostname(),
              "pid": os.getpid(), "updated_at": 1000.0,
              "roster": [{"slug": "a", "state": "driving", "stage": "build"}]}
        board = _board(epics=[self._epic(hb, [_member("a")])])
        contents = self.dashboard._lane_contents(board, now=1000.0)
        entry = self._entry_in(contents, "building")
        self.assertFalse(entry.get("stale"))
        self.assertEqual(entry.get("stage"), "build")


class LaneLiveBuildTest(unittest.TestCase):
    """A member whose attached interactive build heartbeat is live
    (delivery-dashboard board-live-build-lane spec) is placed by that
    heartbeat's stage — ``review`` in the ``review`` lane, any other stage in
    ``building`` — overriding its lifecycle-state mapping. A ``driving``
    roster entry still wins, and an aged-out heartbeat falls back to the
    state mapping with no stale treatment. A standalone change (planned
    outside any epic) is judged against the same injected ``now``."""

    @classmethod
    def setUpClass(cls):
        cls.dashboard = _load_dashboard_stdlib()

    def _member_with_build(self, stage, updated_at, state="archived"):
        member = _member("a")
        member["state"] = state
        member["build_heartbeat"] = {"slug": "a", "kind": "build",
                                     "state": "running", "stage": stage,
                                     "updated_at": updated_at}
        return member

    def _board_with(self, member, roster=()):
        hb = {"state": "running", "host": socket.gethostname(),
              "pid": os.getpid(), "updated_at": 1000.0,
              "roster": list(roster)}
        epic = {"slug": "ep", "status": "active", "heartbeat": hb,
                "members": [member]}
        return _board(epics=[epic])

    def _slugs(self, contents, lane):
        return [member["slug"] for _slug, _status, member, _entry, _project
                in contents[lane]]

    def test_archived_member_mid_review_lands_in_review(self):
        board = self._board_with(self._member_with_build("review", 1000.0))
        contents = self.dashboard._lane_contents(board, now=1000.0)
        self.assertEqual(self._slugs(contents, "review"), ["a"])
        self.assertEqual(contents["shipped"], [])

    def test_non_review_build_stage_lands_in_building(self):
        board = self._board_with(self._member_with_build("implement", 1000.0))
        contents = self.dashboard._lane_contents(board, now=1000.0)
        self.assertEqual(self._slugs(contents, "building"), ["a"])
        self.assertEqual(contents["review"], [])
        self.assertEqual(contents["shipped"], [])

    def test_stale_build_heartbeat_falls_back_to_state_mapping(self):
        stale_at = 1000.0 - self.dashboard.BUILD_FRESH_SECONDS - 1
        board = self._board_with(self._member_with_build("review", stale_at))
        contents = self.dashboard._lane_contents(board, now=1000.0)
        self.assertEqual(self._slugs(contents, "shipped"), ["a"])
        self.assertEqual(contents["review"], [])
        entry = contents["shipped"][0][3]
        self.assertFalse(entry.get("stale"))

    def test_driving_roster_entry_keeps_precedence(self):
        board = self._board_with(
            self._member_with_build("review", 1000.0),
            roster=[{"slug": "a", "state": "driving", "stage": "build"}])
        contents = self.dashboard._lane_contents(board, now=1000.0)
        self.assertEqual(self._slugs(contents, "building"), ["a"])
        self.assertEqual(contents["review"], [])

    def test_standalone_change_is_judged_against_the_injected_clock(self):
        # `now` reaches the standalone loop's `_member_column` too, so an
        # injected clock places a standalone change exactly as it places an
        # epic member (not against the wall clock, under which this
        # heartbeat is ancient and the change would land in `shipped`).
        member = self._member_with_build("review", 1000000.0)
        board = _board(standalone=[member])
        contents = self.dashboard._lane_contents(board, now=1000000.0)
        self.assertEqual(self._slugs(contents, "review"), ["a"])
        self.assertEqual(contents["shipped"], [])


class LaneDraftedTest(unittest.TestCase):
    """A member whose roster entry state is ``drafted`` (delivery-dashboard
    board-drafted-member spec) awaits human review and merge, so it lands in
    ``review`` — even though its change is archived and its worktree-derived
    board state therefore reads ``archived``, which would otherwise carry it
    into ``shipped``."""

    @classmethod
    def setUpClass(cls):
        cls.dashboard = _load_dashboard_stdlib()

    def _slugs(self, contents, lane):
        return [member["slug"] for _slug, _status, member, _entry, _project
                in contents[lane]]

    def test_drafted_entry_over_an_archived_member_lands_in_review(self):
        member = dict(_member("a"), state="archived")
        self.assertEqual(
            self.dashboard._member_column(member, {"state": "drafted"}),
            "review")

    def test_drafted_member_is_mounted_in_the_review_lane(self):
        member = dict(_member("a"), state="archived")
        hb = {"state": "finished", "host": socket.gethostname(),
              "pid": os.getpid(), "updated_at": 1000.0,
              "roster": [{"slug": "a", "state": "drafted"}]}
        epic = {"slug": "ep", "status": "active", "heartbeat": hb,
                "members": [member]}
        contents = self.dashboard._lane_contents(_board(epics=[epic]),
                                                 now=1000.0)
        self.assertEqual(self._slugs(contents, "review"), ["a"])
        self.assertEqual(contents["shipped"], [])


class DrivingSessionKeysBuildTest(_BuildHeartbeatFixture):
    """``driving_session_keys`` also yields the ``(tdir, session_id)`` key for a
    member with a live build heartbeat (explicit session id first, else the
    newest transcript for the heartbeat's location), deduplicating and excluding
    stale build heartbeats (board-throughput-chart)."""

    def _live_build_member(self, slug, *, session_id=None, location=None,
                           updated_at=None, transcript_mtime=None):
        member = _member(slug, location or self.root)
        member["build_heartbeat"] = _build_hb(
            "running",
            updated_at=updated_at if updated_at is not None else time.time(),
            transcript_mtime=transcript_mtime,
            session_id=session_id, location=location or self.root)
        return member

    def test_explicit_session_id_resolves_over_a_newer_transcript(self):
        self._write_transcript(self.root, "sess-a")
        self._write_transcript(self.root, "sess-b")  # a second candidate
        board = _board(standalone=[
            self._live_build_member("m", session_id="sess-a")])
        keys = self.dashboard.driving_session_keys(board)
        tdir = br.transcript_dir(self.root)
        self.assertIn((tdir, "sess-a"), keys)

    def test_newest_transcript_when_no_session_id(self):
        self._write_transcript(self.root, "sess-only")
        board = _board(standalone=[self._live_build_member("m")])
        keys = self.dashboard.driving_session_keys(board)
        tdir = br.transcript_dir(self.root)
        self.assertIn((tdir, "sess-only"), keys)

    def test_a_session_appearing_twice_is_deduplicated(self):
        self._write_transcript(self.root, "sess-dup")
        board = _board(standalone=[
            self._live_build_member("m1", session_id="sess-dup"),
            self._live_build_member("m2", session_id="sess-dup")])
        keys = self.dashboard.driving_session_keys(board)
        tdir = br.transcript_dir(self.root)
        self.assertEqual(keys.count((tdir, "sess-dup")), 1)

    def test_a_stale_build_heartbeat_is_excluded(self):
        self._write_transcript(self.root, "sess-stale")
        board = _board(standalone=[self._live_build_member(
            "m", session_id="sess-stale",
            updated_at=time.time() - 700, transcript_mtime=time.time() - 800)])
        self.assertEqual(self.dashboard.driving_session_keys(board), [])


if __name__ == "__main__":
    unittest.main()
