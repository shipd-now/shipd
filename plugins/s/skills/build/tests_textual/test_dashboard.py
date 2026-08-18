#!/usr/bin/env python3
"""Tests for dashboard.py — the delivery board's data layer and `textual` app.

Requires `textual` (``pip install -r requirements.txt``) — this suite lives
apart from ``plugins/s/skills/build/tests/`` precisely because importing
``dashboard`` now pulls it in. Two layers: the ``board`` aggregation over a
fixture root (root and worktree-parked members) plus the pure renderers
(the shared line renderer) — unchanged data-layer contracts — and the
`textual` App itself, driven headless via ``App.run_test``/``Pilot``. The
``RunHeartbeat`` writer's own tests live in
``plugins/s/skills/build/tests/test_heartbeat.py``.
"""

import contextlib
import datetime as _dt
import io
import json
import os
import re
import shutil
import sys
import tempfile
import time
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
sys.path.insert(0, SCRIPTS)

import dashboard  # noqa: E402
import autopilot  # noqa: E402
import build_report as br  # noqa: E402

from textual.color import Color  # noqa: E402
from textual.command import CommandPalette  # noqa: E402
from textual.containers import VerticalScroll  # noqa: E402
from textual.geometry import Offset  # noqa: E402
from textual.screen import ModalScreen  # noqa: E402
from textual.widgets import (  # noqa: E402
    Button, Checkbox, Collapsible, Footer, Header, Tab,
    TabbedContent, TabPane, Tabs)


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


def _make_epic(root, slug, rows, status="active", theme=None, initiative=None):
    """Write ``.shipd/epics/<slug>/epic.md`` with a header metadata block (Theme,
    Initiative) and a ``## Changes`` stub table; ``rows`` are ``(member_slug,
    description, risk)`` triples."""
    body = ["# %s\n" % slug, "Status: %s\n" % status]
    if theme is not None:
        body.append("Theme: %s\n" % theme)
    if initiative is not None:
        body.append("Initiative: %s\n" % initiative)
    body += ["\n", "## Changes\n", "\n",
             "| Change | Description | Code | Integration | Unknowns | Risk |\n",
             "| --- | --- | --- | --- | --- | --- |\n"]
    for mslug, desc, risk in rows:
        body.append("| %s | %s | low | low | low | %s |\n" % (mslug, desc, risk))
    _write(os.path.join(root, ".shipd", "epics", slug, "epic.md"), "".join(body))


def _plan(root, slug, status, rel=""):
    """Plant a planned member change at ``status`` under ``root`` (or under a
    ``rel`` subdirectory of it, e.g. a ``.worktrees/<slug>`` checkout)."""
    base = os.path.join(root, rel) if rel else root
    _write(os.path.join(base, ".shipd", "planned", slug, "plan.md"),
           "# %s\nStatus: %s\n\n## Idea\n\nx\n" % (slug, status))


class DashboardTestBase(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="dashboard-test-")
        self._base_home = tempfile.mkdtemp(prefix="dashboard-home-")
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
# build_board: worktree-aware aggregation over a fixture root
# ---------------------------------------------------------------------------

class BoardTest(DashboardTestBase):
    def _fixture(self):
        _make_epic(
            self.root, "ep",
            [("planned-root", "a planned member", "low"),
             ("rej", "a rejected member", "medium"),
             ("fresh", "an unplanned member", "high")],
            status="active", theme="observability",
            initiative="delivery-init")
        # One member planned at the root.
        _plan(self.root, "planned-root", "active")
        # One member rejected only inside its own worktree (root planned/ lacks it).
        _plan(self.root, "rej", "rejected", rel=os.path.join(".worktrees", "rej"))
        # A live heartbeat driving a member's gate stage, plus a run report.
        _write(dashboard.heartbeat_path(self.root, "ep"), json.dumps({
            "epic": "ep", "state": "running", "provenance": "default",
            "seq": 4, "updated_at": time.time(),
            "roster": [{"slug": "planned-root", "state": "driving",
                        "stage": "gate", "attempt": 1}]}))
        _write(os.path.join(self.root, ".shipd", "autopilot", "ep-report.json"),
               json.dumps({"epic": "ep",
                           "shipped": [{"member": "planned-root"}]}))

    def test_worktree_parked_member_reports_its_worktree_location(self):
        self._fixture()
        epic = dashboard.build_board(self.root)["epics"][0]
        members = {m["slug"]: m for m in epic["members"]}
        self.assertEqual(members["rej"]["state"], "rejected")
        self.assertIn(".worktrees", members["rej"]["location"])
        self.assertTrue(members["rej"]["location"].endswith("rej"))
        # The root-planned and unplanned members keep their root derivation.
        self.assertEqual(members["planned-root"]["state"], "active")
        self.assertNotIn(".worktrees", members["planned-root"]["location"])
        self.assertEqual(members["fresh"]["state"], "unplanned")
        # The stub-table description and risk survive into the row.
        self.assertEqual(members["rej"]["description"], "a rejected member")
        self.assertEqual(members["rej"]["risk"], "medium")

    def test_missing_workspace_degrades_initiative_to_slug_only(self):
        self._fixture()
        epic = dashboard.build_board(self.root)["epics"][0]
        self.assertEqual(epic["theme"], "observability")
        self.assertEqual(epic["initiative"]["slug"], "delivery-init")
        self.assertIsNone(epic["initiative"]["status"])
        self.assertEqual(epic["status"], "active")

    def test_heartbeat_and_report_are_merged(self):
        self._fixture()
        epic = dashboard.build_board(self.root)["epics"][0]
        self.assertIsNotNone(epic["heartbeat"])
        self.assertEqual(epic["heartbeat"]["state"], "running")
        self.assertEqual(epic["heartbeat"]["roster"][0]["stage"], "gate")
        self.assertIsNotNone(epic["report"])
        self.assertEqual(epic["report"]["shipped"][0]["member"], "planned-root")

    def test_epic_flag_scopes_to_one_epic(self):
        self._fixture()
        _make_epic(self.root, "other", [("z", "z member", "low")],
                   status="ready")
        full = dashboard.build_board(self.root)
        self.assertEqual({e["slug"] for e in full["epics"]}, {"ep", "other"})
        scoped = dashboard.build_board(self.root, epic="ep")
        self.assertEqual([e["slug"] for e in scoped["epics"]], ["ep"])

    def test_board_unknown_epic_slug_fails_cleanly(self):
        self._fixture()
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            rc = dashboard.main(["board", "--root", self.root,
                                 "--epic", "no-such-epic"])
        # A clean exit 1 with a one-line message naming the slug, never a raw
        # FileNotFoundError traceback out of _epic_board.
        self.assertEqual(rc, 1)
        self.assertIn("no-such-epic", err.getvalue())

    def test_board_json_stdout_parses_as_one_object(self):
        self._fixture()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = dashboard.main(["board", "--root", self.root, "--json",
                                 "--epic", "ep"])
        self.assertEqual(rc, 0)
        data = json.loads(out.getvalue())
        self.assertIsInstance(data, dict)
        self.assertEqual({e["slug"] for e in data["epics"]}, {"ep"})


class WorktreeEpicBoardTest(DashboardTestBase):
    """An epic authored inside a ``.worktrees/<name>`` worktree joins the board
    (delivery-dashboard board-aggregation): it aggregates once, carries the
    hosting worktree root as ``location``, and has its file, status, heartbeat,
    and run report read from there. The invocation root always shadows a
    worktree's copy of the same slug.

    Written test-first; expected to FAIL until the worktree-aware discovery
    lands in ``dashboard.py`` (task 3.2)."""

    def worktree(self, name):
        return os.path.join(self.root, ".worktrees", name)

    def test_worktree_authored_epic_joins_the_board(self):
        wt = self.worktree("epic-shipd-port")
        _make_epic(wt, "shipd-port",
                   [("m1", "a member", "low"), ("m2", "another", "high")],
                   status="active", theme="observability",
                   initiative="shipd-dx")
        board = dashboard.build_board(self.root)
        self.assertEqual([e["slug"] for e in board["epics"]], ["shipd-port"])
        epic = board["epics"][0]
        # File and status came from the worktree, not the (empty) root.
        self.assertEqual(epic["status"], "active")
        self.assertEqual(epic["theme"], "observability")
        self.assertEqual(epic["initiative"]["slug"], "shipd-dx")
        self.assertEqual([m["slug"] for m in epic["members"]], ["m1", "m2"])
        self.assertEqual(epic["location"], os.path.abspath(wt))
        self.assertNotEqual(epic["location"], board["root"])

    def test_root_hosted_epic_location_is_the_board_root(self):
        _make_epic(self.root, "ep", [("m1", "a member", "low")],
                   status="ready")
        board = dashboard.build_board(self.root)
        self.assertEqual(board["epics"][0]["location"], board["root"])

    def test_root_epics_come_before_worktree_only_epics(self):
        _make_epic(self.root, "r-b", [("m1", "a member", "low")])
        _make_epic(self.root, "r-a", [("m2", "a member", "low")])
        _make_epic(self.worktree("epic-w"), "w-a", [("m3", "a member", "low")])
        board = dashboard.build_board(self.root)
        self.assertEqual([e["slug"] for e in board["epics"]],
                         ["r-a", "r-b", "w-a"])

    def test_a_slug_hosted_in_both_aggregates_once_from_the_root(self):
        _make_epic(self.root, "ep", [("m1", "a member", "low")],
                   status="ready", theme="root-theme")
        _make_epic(self.worktree("epic-ep"), "ep",
                   [("m1", "a member", "low"), ("m2", "another", "high")],
                   status="complete", theme="worktree-theme")
        board = dashboard.build_board(self.root)
        self.assertEqual([e["slug"] for e in board["epics"]], ["ep"])
        epic = board["epics"][0]
        self.assertEqual(epic["status"], "ready")
        self.assertEqual(epic["theme"], "root-theme")
        self.assertEqual(epic["location"], board["root"])

    def test_worktree_epic_heartbeat_and_report_read_from_its_root(self):
        wt = self.worktree("epic-shipd-port")
        _make_epic(wt, "shipd-port", [("m1", "a member", "low")],
                   status="active")
        _write(dashboard.heartbeat_path(wt, "shipd-port"), json.dumps({
            "epic": "shipd-port", "state": "running", "seq": 7,
            "updated_at": time.time(),
            "roster": [{"slug": "m1", "state": "driving", "stage": "gate"}]}))
        _write(os.path.join(wt, ".shipd", "autopilot",
                            "shipd-port-report.json"),
               json.dumps({"epic": "shipd-port",
                           "shipped": [{"member": "m1"}]}))
        epic = dashboard.build_board(self.root)["epics"][0]
        self.assertIsNotNone(epic["heartbeat"])
        self.assertEqual(epic["heartbeat"]["seq"], 7)
        self.assertIsNotNone(epic["report"])
        self.assertEqual(epic["report"]["shipped"][0]["member"], "m1")

    def test_worktree_epic_members_are_excluded_from_standalone(self):
        # `m1` is planned at the root but adopted by a worktree-authored epic,
        # so it must not also list as a standalone change.
        _make_epic(self.worktree("epic-shipd-port"), "shipd-port",
                   [("m1", "a member", "low")], status="active")
        _plan(self.root, "m1", "ready")
        self.assertIn("m1", dashboard._all_epic_member_slugs(self.root))
        board = dashboard.build_board(self.root)
        self.assertEqual([row["slug"] for row in board["standalone"]], [])

    def test_epic_flag_scopes_to_a_worktree_hosted_epic(self):
        _make_epic(self.worktree("epic-shipd-port"), "shipd-port",
                   [("m1", "a member", "low")], status="active")
        _make_epic(self.root, "ep", [("m2", "a member", "low")])
        scoped = dashboard.build_board(self.root, epic="shipd-port")
        self.assertEqual([e["slug"] for e in scoped["epics"]], ["shipd-port"])

    def test_an_unreadable_worktree_config_does_not_break_discovery(self):
        _make_epic(self.root, "ep", [("m1", "a member", "low")])
        broken = self.worktree("epic-broken")
        os.makedirs(broken, exist_ok=True)
        _write(os.path.join(broken, ".shipd-config.json"), "{not valid json")
        _make_epic(self.worktree("epic-w"), "w-a", [("m2", "a member", "low")])
        board = dashboard.build_board(self.root)
        self.assertEqual([e["slug"] for e in board["epics"]], ["ep", "w-a"])


# ---------------------------------------------------------------------------
# Initiative grouping and per-member action eligibility
# ---------------------------------------------------------------------------

class InitiativeGroupingTest(DashboardTestBase):
    def _groups(self, board):
        """Split a board's groups into ``(by_initiative_slug, workspace_wide)``.
        The workspace-wide bucket is the group whose ``initiative`` is None."""
        by_init = {}
        workspace_wide = None
        for g in board["groups"]:
            init = g.get("initiative")
            if init is None:
                workspace_wide = g
            else:
                by_init[init["slug"]] = g
        return by_init, workspace_wide

    def test_epics_group_under_their_initiative(self):
        # Two epics share one Initiative; a third carries none.
        _make_epic(self.root, "ep1", [("a", "low", "low")],
                   status="active", initiative="delivery-init")
        _make_epic(self.root, "ep2", [("b", "low", "low")],
                   status="active", initiative="delivery-init")
        _make_epic(self.root, "solo", [("c", "low", "low")], status="active")

        board = dashboard.build_board(self.root)
        by_init, workspace_wide = self._groups(board)

        # The two initiative-bearing epics share a single group.
        self.assertIn("delivery-init", by_init)
        self.assertEqual(
            {e["slug"] for e in by_init["delivery-init"]["epics"]},
            {"ep1", "ep2"})
        # The initiative-less epic lands in the workspace-wide group.
        self.assertIsNotNone(workspace_wide)
        self.assertEqual(
            {e["slug"] for e in workspace_wide["epics"]}, {"solo"})
        # The flat epics list is preserved alongside the grouping.
        self.assertEqual({e["slug"] for e in board["epics"]},
                         {"ep1", "ep2", "solo"})


class MemberActionsTest(DashboardTestBase):
    def test_members_carry_eligible_actions_and_session_id(self):
        # fresh: unplanned -> plan; rdy: ready plan -> run; stuck: parked
        # needs-human with a heartbeat session id -> open.
        _make_epic(
            self.root, "ep",
            [("fresh", "an unplanned member", "low"),
             ("rdy", "a ready member", "medium"),
             ("stuck", "a parked member", "high")],
            status="active")
        _plan(self.root, "rdy", "ready")
        _plan(self.root, "stuck", "rejected")
        _write(dashboard.heartbeat_path(self.root, "ep"), json.dumps({
            "epic": "ep", "state": "finished", "seq": 5,
            "updated_at": time.time(),
            "roster": [{"slug": "stuck", "state": "needs-human",
                        "session_id": "sess-stuck"}]}))

        epic = dashboard.build_board(self.root)["epics"][0]
        members = {m["slug"]: m for m in epic["members"]}

        self.assertIn("plan", members["fresh"]["actions"])
        self.assertIn("run", members["rdy"]["actions"])
        self.assertIn("open", members["stuck"]["actions"])
        # The parked member's resume handle rides on the row.
        self.assertEqual(members["stuck"]["session_id"], "sess-stuck")
        # A ready member with no session id is not openable.
        self.assertNotIn("open", members["rdy"]["actions"])

    def test_open_is_absent_while_a_member_is_driving(self):
        # A driving member carries a session id but open stays disabled.
        entry = {"slug": "m", "state": "driving", "stage": "build",
                 "session_id": "sess-live"}
        member = {"slug": "m", "state": "active", "session_id": "sess-live"}
        self.assertNotIn("open", dashboard.member_actions(member, entry))

    def test_parked_member_with_session_is_openable(self):
        entry = {"slug": "m", "state": "needs-human", "session_id": "sess-9"}
        member = {"slug": "m", "state": "rejected", "session_id": "sess-9"}
        self.assertIn("open", dashboard.member_actions(member, entry))


# ---------------------------------------------------------------------------
# Pure renderers: shared line renderer, terminal-free
# ---------------------------------------------------------------------------

def _sample_board():
    """A board dict with one running epic — a driving member (its stage in the
    heartbeat roster) and a parked one — for the pure renderers."""
    return {
        "root": "/x",
        "generated_at": time.time(),
        "epics": [{
            "slug": "ep",
            "status": "active",
            "theme": "observability",
            "initiative": {"slug": "delivery-init", "status": None},
            "members": [
                {"slug": "driver", "description": "the driven one",
                 "risk": "low", "state": "driving", "location": "/x"},
                {"slug": "parked", "description": "the parked one",
                 "risk": "high", "state": "needs-human",
                 "location": "/x/.worktrees/parked"},
            ],
            "heartbeat": {
                "epic": "ep", "state": "running", "seq": 3,
                "updated_at": time.time() - 5,
                "roster": [{"slug": "driver", "state": "driving",
                            "stage": "build", "attempt": 2}],
            },
            "report": None,
        }],
    }


class RendererTest(unittest.TestCase):
    def test_render_board_lines_names_epic_members_state_and_stage(self):
        lines = dashboard.render_board_lines(_sample_board())
        self.assertTrue(all(isinstance(ln, str) for ln in lines))
        text = "\n".join(lines)
        self.assertIn("ep", text)             # the epic
        self.assertIn("driver", text)         # each member
        self.assertIn("driving", text)        # its state
        self.assertIn("build", text)          # its current stage (heartbeat)
        self.assertIn("parked", text)
        self.assertIn("needs-human", text)
        self.assertIn("ago", text)            # heartbeat age, not liveness

    def test_render_board_lines_handles_no_heartbeat(self):
        board = _sample_board()
        board["epics"][0]["heartbeat"] = None
        # A run that never started (or crashed away its heartbeat) still renders.
        lines = dashboard.render_board_lines(board)
        self.assertIn("ep", "\n".join(lines))


class WorktreeEpicMarkerTest(unittest.TestCase):
    """The ``[worktree]`` marker on an epic whose ``location`` is not the board
    root (delivery-dashboard board-aggregation): the human-readable board's
    epic header line and the TUI's epic group header both carry it, and a
    root-hosted epic carries none. Pure — no terminal.

    Written test-first; expected to FAIL until the markers land in
    ``dashboard.py`` (task 3.4)."""

    def _worktree_board(self):
        board = _sample_board()
        board["epics"][0]["location"] = "/x/.worktrees/epic-ep"
        return board

    def test_text_board_marks_a_worktree_hosted_epic_header(self):
        lines = dashboard.render_board_lines(self._worktree_board())
        header = [ln for ln in lines if ln.strip().startswith("epic ep")]
        self.assertEqual(len(header), 1, lines)
        self.assertIn("[worktree]", header[0])

    def test_text_board_leaves_a_root_hosted_epic_unmarked(self):
        board = _sample_board()
        board["epics"][0]["location"] = board["root"]
        lines = dashboard.render_board_lines(board)
        header = [ln for ln in lines if ln.strip().startswith("epic ep")]
        self.assertEqual(len(header), 1, lines)
        self.assertNotIn("[worktree]", header[0])

    def test_text_board_leaves_a_locationless_epic_unmarked(self):
        # A hand-built fixture predating `location` still renders unmarked.
        lines = dashboard.render_board_lines(_sample_board())
        header = [ln for ln in lines if ln.strip().startswith("epic ep")]
        self.assertNotIn("[worktree]", header[0])

    def test_epic_group_title_carries_the_marker(self):
        title = dashboard.epic_group_title("ep", "active", None, worktree=True)
        self.assertIn("[worktree]", title)

    def test_epic_group_title_is_unchanged_without_the_marker(self):
        self.assertEqual(
            dashboard.epic_group_title("ep", "active", None, worktree=False),
            dashboard.epic_group_title("ep", "active", None))
        self.assertNotIn(
            "[worktree]",
            dashboard.epic_group_title("ep", "active", {"slug": "init"},
                                       count=2, stalled=True))


class FlowLaneDelegationTest(unittest.TestCase):
    """``flow_lane`` delegates to ``spec_status.board_lane`` — the single shared
    state→lane projection the epic report also groups its members with, so the
    board and the report cannot drift (spec-status epic-status-verbs)."""

    def test_flow_lane_matches_the_shared_projection(self):
        import spec_status as ss
        for state in ("archived", "ready", "unplanned", "draft", "active",
                      "complete", "verified", "rejected", "?"):
            self.assertEqual(dashboard.flow_lane(state), ss.board_lane(state),
                             state)


class AgeRendererTest(unittest.TestCase):
    """`_age` prefixes its human age with a caller-chosen ``verb`` — defaulting
    to ``updated`` so every existing call site is byte-identical, while the
    stall banner reframes the same heartbeat age as ``parked <age> ago``."""

    def test_default_verb_is_updated(self):
        self.assertEqual(dashboard._age(time.time()), "updated 0s ago")
        self.assertEqual(dashboard._age(None), "updated ?")

    def test_parked_verb_reframes_the_age(self):
        self.assertEqual(
            dashboard._age(time.time() - 5, verb="parked"), "parked 5s ago")
        self.assertEqual(
            dashboard._age(time.time() - 120, verb="parked"), "parked 2m ago")
        self.assertEqual(
            dashboard._age(time.time() - 7200, verb="parked"), "parked 2h ago")

    def test_parked_missing_timestamp_falls_back(self):
        self.assertEqual(dashboard._age(None, verb="parked"), "parked ?")
        self.assertEqual(dashboard._age(0, verb="parked"), "parked ?")


# ---------------------------------------------------------------------------
# Stall predicate and the group-header stall marker (pure)
# ---------------------------------------------------------------------------

class StallPredicateTest(unittest.TestCase):
    def _epic(self, run_state, roster):
        return {"slug": "ep", "status": "active",
                "heartbeat": {"epic": "ep", "state": run_state,
                              "roster": roster}}

    def test_finished_run_with_needs_human_is_stalled(self):
        epic = self._epic("finished", [
            {"slug": "a", "state": "shipped"},
            {"slug": "b", "state": "needs-human", "stage": "worktree",
             "reason": "worktree creation failed"}])
        self.assertTrue(dashboard.epic_stalled(epic))
        entries = dashboard.stalled_entries(epic)
        self.assertEqual([e["slug"] for e in entries], ["b"])
        self.assertEqual(entries[0]["stage"], "worktree")
        self.assertEqual(entries[0]["reason"], "worktree creation failed")

    def test_finished_run_with_only_rejected_and_shipped_not_stalled(self):
        epic = self._epic("finished", [
            {"slug": "a", "state": "shipped"},
            {"slug": "b", "state": "rejected", "stage": "gate",
             "reason": "insufficient context"}])
        self.assertFalse(dashboard.epic_stalled(epic))
        self.assertEqual(dashboard.stalled_entries(epic), [])

    def test_running_run_with_needs_human_not_stalled(self):
        epic = self._epic("running", [
            {"slug": "b", "state": "needs-human", "stage": "build",
             "reason": "x"}])
        self.assertFalse(dashboard.epic_stalled(epic))
        self.assertEqual(dashboard.stalled_entries(epic), [])

    def test_missing_heartbeat_not_stalled(self):
        epic = {"slug": "ep", "status": "active", "heartbeat": None}
        self.assertFalse(dashboard.epic_stalled(epic))
        self.assertEqual(dashboard.stalled_entries(epic), [])


class EpicGroupTitleStallTest(unittest.TestCase):
    def test_stalled_prefixes_theme_error_marker(self):
        title = dashboard.epic_group_title("ep", "active", None, stalled=True)
        self.assertTrue(title.startswith("[$text-error]✗[/] "))
        self.assertIn("ep [active]", title)

    def test_not_stalled_is_byte_identical_to_today(self):
        base = dashboard.epic_group_title("ep", "active", None)
        self.assertEqual(
            dashboard.epic_group_title("ep", "active", None, stalled=False),
            base)
        self.assertNotIn("✗", base)


class EpicGroupTitleCountTest(unittest.TestCase):
    def test_count_appends_a_muted_suffix_without_initiative(self):
        # The per-lane count rides the title as a muted ` (N)` suffix (theme
        # `$fg-muted` markup), not a separate trailing element (delivery-
        # dashboard board-epic-grouping spec).
        title = dashboard.epic_group_title("ep", "active", None, count=2)
        self.assertEqual(title, "ep [active] [$fg-muted](2)[/]")

    def test_count_appends_after_the_initiative_segment(self):
        title = dashboard.epic_group_title(
            "ep", "active", {"slug": "init"}, count=3)
        self.assertEqual(title, "ep [active] · init [$fg-muted](3)[/]")

    def test_count_none_is_byte_identical_to_today(self):
        self.assertEqual(
            dashboard.epic_group_title("ep", "active", None, count=None),
            dashboard.epic_group_title("ep", "active", None))
        self.assertEqual(
            dashboard.epic_group_title("ep", "active", {"slug": "init"},
                                       count=None),
            dashboard.epic_group_title("ep", "active", {"slug": "init"}))

    def test_count_none_is_byte_identical_when_stalled(self):
        self.assertEqual(
            dashboard.epic_group_title("ep", "active", None, stalled=True,
                                       count=None),
            dashboard.epic_group_title("ep", "active", None, stalled=True))


class AutopilotLiveTest(unittest.TestCase):
    """`autopilot_live(board, now=...)` is the pure, dependency-free liveness
    predicate driving the header-bar autopilot indicator (delivery-dashboard
    board-tui spec): true exactly when some epic's heartbeat records run state
    ``running`` with an ``updated_at`` within 3600 s of ``now``."""

    def _board(self, epics):
        return {"root": "/x", "generated_at": 0.0, "epics": epics,
                "groups": []}

    def _epic(self, heartbeat):
        return {"slug": "ep", "status": "active", "heartbeat": heartbeat}

    def test_fresh_running_heartbeat_is_live(self):
        board = self._board([self._epic(
            {"state": "running", "updated_at": 950.0})])
        self.assertTrue(dashboard.autopilot_live(board, now=1000.0))

    def test_finished_run_is_not_live(self):
        board = self._board([self._epic(
            {"state": "finished", "updated_at": 999.0})])
        self.assertFalse(dashboard.autopilot_live(board, now=1000.0))

    def test_missing_heartbeat_is_not_live(self):
        board = self._board([self._epic(None)])
        self.assertFalse(dashboard.autopilot_live(board, now=1000.0))

    def test_missing_updated_at_is_not_live(self):
        board = self._board([self._epic({"state": "running"})])
        self.assertFalse(dashboard.autopilot_live(board, now=1000.0))

    def test_running_older_than_the_window_is_not_live(self):
        board = self._board([self._epic(
            {"state": "running", "updated_at": 1000.0 - 3601})])
        self.assertFalse(dashboard.autopilot_live(board, now=1000.0))


class InitiativeGroupTitleTest(unittest.TestCase):
    """`initiative_group_title(initiative)` labels an initiative-mode lane
    group (delivery-dashboard board-epic-grouping spec): ``<slug> [<status>]``
    for a real initiative, ``workspace`` for the ``None`` (no-initiative)
    bucket."""

    def test_initiative_renders_slug_and_status(self):
        self.assertEqual(
            dashboard.initiative_group_title({"slug": "s", "status": "active"}),
            "s [active]")

    def test_none_renders_workspace(self):
        self.assertEqual(dashboard.initiative_group_title(None), "workspace")


# ---------------------------------------------------------------------------
# Pure board-action launch builders (PLAN / RUN / OPEN)
# ---------------------------------------------------------------------------

class LaunchBuilderTest(unittest.TestCase):
    def _member(self, slug, **kw):
        m = {"slug": slug, "location": "/repo", "risk": "low",
             "state": "unplanned", "actions": [], "session_id": None}
        m.update(kw)
        return m

    def test_plan_under_tmux_builds_new_window_no_suspend(self):
        m = self._member("feat", state="unplanned")
        launch = dashboard.build_plan_launch("/repo", "ep", m, tmux=True)
        self.assertEqual(launch["mode"], "tmux")
        self.assertEqual(launch["argv"][:2], ["tmux", "new-window"])
        joined = " ".join(launch["argv"])
        self.assertIn("/s:plan", joined)
        self.assertIn("feat", joined)
        # The new window opens in the member's worktree (tmux -c).
        self.assertIn("-c", launch["argv"])
        wt = launch["argv"][launch["argv"].index("-c") + 1]
        self.assertTrue(wt.endswith(os.path.join(".worktrees", "feat")))

    def test_plan_without_tmux_suspends_in_worktree(self):
        m = self._member("feat")
        launch = dashboard.build_plan_launch("/repo", "ep", m, tmux=False)
        self.assertEqual(launch["mode"], "suspend")
        self.assertIn("/s:plan feat", " ".join(launch["argv"]))
        self.assertTrue(
            launch["cwd"].endswith(os.path.join(".worktrees", "feat")))

    def test_run_builds_detached_single_member_driver(self):
        m = self._member("feat", state="ready")
        # Detached regardless of $TMUX — the board tails the heartbeat.
        launch = dashboard.build_run_launch("/repo", "ep", m, tmux=True)
        self.assertEqual(launch["mode"], "detach")
        argv = launch["argv"]
        self.assertIn("--member", argv)
        self.assertEqual(argv[argv.index("--member") + 1], "feat")
        self.assertIn("ep", argv)
        self.assertIn("autopilot.py", " ".join(argv))

    def test_open_parked_member_resumes_session_suspend(self):
        m = self._member("feat", state="rejected", session_id="sess-7")
        launch = dashboard.build_open_launch("/repo", "ep", m, tmux=False)
        self.assertEqual(launch["mode"], "suspend")
        self.assertIn("--resume", launch["argv"])
        self.assertIn("sess-7", launch["argv"])

    def test_open_under_tmux_new_window(self):
        m = self._member("feat", state="shipped", session_id="sess-7")
        launch = dashboard.build_open_launch("/repo", "ep", m, tmux=True)
        self.assertEqual(launch["mode"], "tmux")
        joined = " ".join(launch["argv"])
        self.assertIn("--resume", joined)
        self.assertIn("sess-7", joined)

    def test_open_absent_for_driving_member(self):
        # A mid-drive member is not openable — via its eligible actions.
        entry = {"slug": "feat", "state": "driving", "stage": "build",
                 "session_id": "sess-live"}
        m = self._member("feat", state="active", session_id="sess-live")
        self.assertNotIn("open", dashboard.member_actions(m, entry))

    def test_open_none_without_a_session_id(self):
        m = self._member("feat", session_id=None)
        self.assertIsNone(
            dashboard.build_open_launch("/repo", "ep", m, tmux=False))

    def test_editor_launch_resolves_editor_from_environment(self):
        with mock.patch.dict(os.environ, {"EDITOR": "nano"}):
            launch = dashboard.build_editor_launch("/x/plan.md")
        self.assertEqual(
            launch, {"mode": "suspend", "argv": ["nano", "/x/plan.md"],
                     "cwd": "/x"})

    def test_editor_launch_falls_back_to_vi_when_editor_unset(self):
        env = {k: v for k, v in os.environ.items() if k != "EDITOR"}
        with mock.patch.dict(os.environ, env, clear=True):
            launch = dashboard.build_editor_launch("/x/plan.md")
        self.assertEqual(
            launch, {"mode": "suspend", "argv": ["vi", "/x/plan.md"],
                     "cwd": "/x"})

    def test_editor_launch_honors_explicit_editor_argument(self):
        with mock.patch.dict(os.environ, {"EDITOR": "nano"}):
            launch = dashboard.build_editor_launch(
                "/x/plan.md", editor="code")
        self.assertEqual(
            launch, {"mode": "suspend", "argv": ["code", "/x/plan.md"],
                     "cwd": "/x"})


class ResolveActionLaunchTest(unittest.TestCase):
    """The pure wiring the tui dispatch runs: resolve a card-button region to a
    launch spec by looking up the builder and the member row."""

    def _board(self):
        epic = {"slug": "ep", "members": [
            {"slug": "rdy", "state": "ready", "location": "/repo",
             "risk": "low", "actions": ["run"], "session_id": None},
            {"slug": "parked", "state": "rejected", "location": "/repo",
             "risk": "high", "actions": ["open"], "session_id": "sess-9"},
        ]}
        return {"root": "/repo", "epics": [epic]}

    def test_run_region_resolves_to_detached_driver(self):
        region = {"kind": "card_button", "epic": "ep", "member": "rdy",
                  "action": "run"}
        launch = dashboard.resolve_action_launch(self._board(), "/repo", region)
        self.assertEqual(launch["mode"], "detach")
        self.assertIn("--member", launch["argv"])
        self.assertEqual(
            launch["argv"][launch["argv"].index("--member") + 1], "rdy")

    def test_open_region_resolves_with_member_session(self):
        region = {"kind": "card_button", "epic": "ep", "member": "parked",
                  "action": "open"}
        launch = dashboard.resolve_action_launch(
            self._board(), "/repo", region)
        self.assertIn("sess-9", launch["argv"])

    def test_unknown_member_resolves_to_none(self):
        region = {"kind": "card_button", "epic": "ep", "member": "ghost",
                  "action": "run"}
        self.assertIsNone(
            dashboard.resolve_action_launch(self._board(), "/repo", region))


# ---------------------------------------------------------------------------
# The textual App: mounted widget tree, driven headless via App.run_test
# ---------------------------------------------------------------------------

def _kanban_board():
    """A board with one epic whose member is driving the build stage (maps to
    the ``building`` lane), a ready member, and an unplanned member — each
    carrying its eligible actions — for exercising the mounted App."""
    epic = {
        "slug": "ep", "status": "active", "theme": "obs",
        "initiative": {"slug": "init", "status": "active"},
        "members": [
            {"slug": "driver", "description": "d", "risk": "low",
             "state": "active", "location": "/x", "actions": ["open"],
             "session_id": "s1"},
            {"slug": "rdy", "description": "r", "risk": "medium",
             "state": "ready", "location": "/x", "actions": ["run"],
             "session_id": None},
            {"slug": "fresh", "description": "f", "risk": "high",
             "state": "unplanned", "location": "/x", "actions": ["plan"],
             "session_id": None},
        ],
        "heartbeat": {
            "epic": "ep", "state": "running", "seq": 2,
            "updated_at": time.time(),
            "roster": [{"slug": "driver", "state": "driving", "stage": "build",
                        "attempt": 1, "session_id": "s1"}],
        },
        "report": None,
    }
    return {
        "root": "/x", "generated_at": time.time(),
        "epics": [epic],
        "groups": [{"initiative": {"slug": "init", "status": "active"},
                    "epics": [epic]}],
    }


# The five named lifecycle lanes, exactly as the delta spec names them.
_LANE_NAMES = ("unplanned", "ready", "building", "review", "shipped")


class FilterMatchesTest(unittest.TestCase):
    """``_filter_matches`` — faceted chip semantics (delivery-dashboard
    board-filter-strip spec): same-kind OR, cross-kind AND, empty matches
    all."""

    def setUp(self):
        self.init_a = {"slug": "ia", "status": "active"}
        self.init_b = {"slug": "ib", "status": "active"}
        self.high = {"slug": "m1", "risk": "high"}
        self.low = {"slug": "m2", "risk": "low"}

    def test_empty_filters_keep_everything(self):
        self.assertTrue(
            dashboard._filter_matches([], "ep1", self.init_a, self.high))

    def test_risk_kind_tests_the_member_rating(self):
        fm = dashboard._filter_matches
        self.assertTrue(fm([("risk", "high")], "ep1", self.init_a, self.high))
        self.assertFalse(fm([("risk", "high")], "ep1", self.init_a, self.low))

    def test_epic_kind_tests_the_epic_slug(self):
        fm = dashboard._filter_matches
        self.assertTrue(fm([("epic", "ep1")], "ep1", self.init_a, self.high))
        self.assertFalse(fm([("epic", "ep2")], "ep1", self.init_a, self.high))

    def test_initiative_kind_tests_the_epics_initiative_slug(self):
        fm = dashboard._filter_matches
        self.assertTrue(
            fm([("initiative", "ia")], "ep1", self.init_a, self.high))
        self.assertFalse(
            fm([("initiative", "ib")], "ep1", self.init_a, self.high))

    def test_none_initiative_never_matches(self):
        self.assertFalse(dashboard._filter_matches(
            [("initiative", "ia")], "ep1", None, self.high))

    def test_same_kind_values_or(self):
        # Either rating keeps the member — the second same-kind chip widens.
        self.assertTrue(dashboard._filter_matches(
            [("risk", "high"), ("risk", "low")], "ep1", self.init_a, self.low))

    def test_cross_kind_chips_and(self):
        fm = dashboard._filter_matches
        # High-risk member of ep1 passes both kinds.
        self.assertTrue(fm([("risk", "high"), ("epic", "ep1")],
                           "ep1", self.init_a, self.high))
        # Right risk, wrong epic — the epic kind rejects it.
        self.assertFalse(fm([("risk", "high"), ("epic", "ep2")],
                            "ep1", self.init_a, self.high))


class FilterOptionsTest(unittest.TestCase):
    """``_filter_options`` — the picker's available options in a fixed order
    (delivery-dashboard board-filter-strip spec)."""

    def _board(self):
        init_a = {"slug": "ia", "status": "active"}
        init_b = {"slug": "ib", "status": "active"}
        ep1 = {"slug": "ep1", "initiative": init_a}
        ep2 = {"slug": "ep2", "initiative": init_b}
        ep3 = {"slug": "ep3", "initiative": None}
        return {
            "epics": [ep1, ep2, ep3],
            "groups": [{"initiative": init_a, "epics": [ep1]},
                       {"initiative": init_b, "epics": [ep2]},
                       {"initiative": None, "epics": [ep3]}],
        }

    def test_lists_risk_tiers_epics_then_initiatives_in_order(self):
        options = dashboard._filter_options(self._board(), [])
        self.assertEqual(options, [
            ("risk", "high"), ("risk", "medium"), ("risk", "low"),
            ("epic", "ep1"), ("epic", "ep2"), ("epic", "ep3"),
            ("initiative", "ia"), ("initiative", "ib"),
        ])

    def test_active_chips_are_excluded(self):
        options = dashboard._filter_options(
            self._board(), [("risk", "high"), ("epic", "ep2")])
        self.assertNotIn(("risk", "high"), options)
        self.assertNotIn(("epic", "ep2"), options)
        self.assertIn(("risk", "medium"), options)
        self.assertIn(("epic", "ep1"), options)
        self.assertIn(("initiative", "ia"), options)


class SyncLabelTest(unittest.TestCase):
    """``_sync_label`` — the synced-ago strip stat with ``_age``-style s/m/h
    tiers (delivery-dashboard board-filter-strip spec)."""

    def test_never_synced_renders_a_placeholder(self):
        self.assertEqual(dashboard._sync_label(None), "synced ?")

    def test_seconds_minutes_and_hours_tiers(self):
        sl = dashboard._sync_label
        now = 10_000.0
        self.assertEqual(sl(now - 5, now=now), "synced 5s ago")
        self.assertEqual(sl(now - 120, now=now), "synced 2m ago")
        self.assertEqual(sl(now - 7200, now=now), "synced 2h ago")


class AppMountTest(unittest.IsolatedAsyncioTestCase):
    """``BoardApp`` is constructed with an injectable ``board_fn`` seam (a
    zero-arg callable returning a board dict) so a test mounts it against a
    fixed board without a real repo root — mirroring the ``member_driver``/
    ``sync_fn`` seams elsewhere in the engine."""

    async def test_app_mounts_header_bar_footer_and_five_lanes_no_panel(self):
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test():
            # The header bar replaces the stock textual Header and the old
            # controls strip / group-by-epic checkbox (delivery-dashboard
            # board-tui spec).
            self.assertFalse(app.query(Header))
            self.assertFalse(app.query("#controls-strip"))
            self.assertFalse(app.query(Checkbox))
            self.assertFalse(app.query("#hierarchy-panel"))
            bar = app.query_one("#header-bar")
            self.assertTrue(bar.query("#brand"))
            # The brand block opens with the ☕ mark directly before the
            # accent `shipd` label (delivery-dashboard board-brand-mark spec).
            brand = str(bar.query_one("#brand", dashboard.Static).content)
            self.assertTrue(
                brand.startswith("☕ "),
                "brand block does not open with the ☕ mark: %r" % brand)
            # With the style tags stripped, the mark is directly followed by
            # the `shipd` label, then the muted `delivery board` label.
            plain = re.sub(r"\[/?[^\]]*\]", "", brand)
            self.assertTrue(plain.startswith("☕ shipd"), plain)
            self.assertIn("delivery board", plain)
            self.assertTrue(bar.query("#board-search-input"))
            self.assertTrue(bar.query("#board-search-clear"))
            self.assertTrue(bar.query("#board-search-count"))
            for mode in ("epic", "initiative", "none"):
                self.assertTrue(bar.query("#group-mode-%s" % mode))
            self.assertTrue(bar.query("#autopilot-indicator"))
            self.assertTrue(bar.query(dashboard.HeaderChart))
            self.assertTrue(app.query(Footer))
            for lane in _LANE_NAMES:
                self.assertIsInstance(
                    app.query_one("#lane-%s" % lane), dashboard.Lane)

    async def test_member_renders_as_focusable_card_in_its_lane(self):
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test():
            lane = app.query_one("#lane-building", dashboard.Lane)
            cards = list(lane.query(dashboard.TaskCard))
            card = next((c for c in cards if c.member["slug"] == "driver"),
                       None)
            self.assertIsNotNone(card)
            self.assertEqual(card.member["risk"], "low")
            self.assertTrue(card.can_focus)

    async def test_click_on_unfocused_card_opens_detail_and_focuses_it(self):
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        # A wider viewport than the 80-column default: with both the run and
        # open controls now sharing the group-header row, a lane's default
        # 80-column share is too narrow for the card to get a clickable
        # region.
        async with app.run_test(size=(120, 24)) as pilot:
            lane = app.query_one("#lane-ready", dashboard.Lane)
            card = next(c for c in lane.query(dashboard.TaskCard)
                       if c.member["slug"] == "rdy")
            self.assertFalse(card.has_focus)
            await pilot.click(card)
            self.assertIsInstance(app.screen, dashboard.MemberDetailScreen)
            self.assertEqual(app.screen.member["slug"], "rdy")
            self.assertTrue(card.has_focus)


class HeaderBarChromeTest(unittest.IsolatedAsyncioTestCase):
    """The Shipd-style header bar (delivery-dashboard board-tui spec): the
    segmented grouping control highlights the active mode, ``/`` focuses the
    header-bar search input, and the autopilot indicator lights for a fresh
    ``running`` heartbeat and idles otherwise."""

    async def test_segmented_control_highlights_the_active_mode(self):
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test() as pilot:
            epic_btn = app.query_one("#group-mode-epic", Button)
            init_btn = app.query_one("#group-mode-initiative", Button)
            self.assertTrue(epic_btn.has_class("mode-active"))
            self.assertFalse(init_btn.has_class("mode-active"))
            await pilot.press("g")  # epic -> initiative
            self.assertFalse(epic_btn.has_class("mode-active"))
            self.assertTrue(init_btn.has_class("mode-active"))

    async def test_mode_button_selects_its_mode_directly(self):
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test(size=(120, 24)) as pilot:
            await pilot.click("#group-mode-initiative")
            await pilot.pause()
            self.assertEqual(app.group_mode, "initiative")
            self.assertTrue(
                app.query_one("#group-mode-initiative", Button)
                .has_class("mode-active"))

    async def test_mode_segments_never_move_across_active_states(self):
        # The three grouping segments keep fixed positions and widths whatever
        # the active mode (delivery-dashboard board-epic-grouping spec: "Mode
        # segments never move") — selecting a mode must never reflow the
        # segmented control.
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test(size=(120, 24)) as pilot:
            await pilot.pause()
            ids = ["#group-mode-epic", "#group-mode-initiative",
                   "#group-mode-none"]

            def _regions():
                return {i: app.query_one(i, Button).region for i in ids}

            baseline = _regions()  # epic active (the default)
            for target in ("#group-mode-initiative", "#group-mode-none",
                           "#group-mode-epic"):
                await pilot.click(target)
                await pilot.pause()
                self.assertEqual(_regions(), baseline)

    async def test_slash_focuses_the_header_bar_search_input(self):
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test() as pilot:
            await pilot.press("slash")
            inp = app.query_one("#board-search-input", dashboard.SearchInput)
            self.assertTrue(inp.has_focus)
            # The input lives inside the header bar's centered search cluster.
            self.assertTrue(
                app.query_one("#header-bar").query("#board-search-input"))

    async def test_autopilot_indicator_reflects_liveness_across_refreshes(self):
        # Drive both states through refresh_board with a stubbed board_fn: an
        # idle board (no live heartbeat) then a fresh `running` one.
        state = {"board": _two_epic_board()}
        app = dashboard.BoardApp(root="/x", board_fn=lambda: state["board"])
        async with app.run_test():
            ind = app.query_one("#autopilot-indicator", dashboard.Static)
            self.assertIn("idle", str(ind.render()))
            self.assertNotIn("autopilot on", str(ind.render()))
            state["board"] = _kanban_board()  # fresh running heartbeat
            await app.refresh_board()
            self.assertIn("autopilot on", str(ind.render()))

    async def test_indicator_shows_building_for_a_live_interactive_build(self):
        # No live autopilot run, but one standalone change carries a fresh
        # `running` build heartbeat — the indicator drops to the `building`
        # marker (delivery-dashboard board-tui spec).
        member = {"slug": "solo", "description": "d", "risk": "low",
                  "state": "active", "location": "/x", "actions": [],
                  "build_heartbeat": {"slug": "solo", "kind": "build",
                                      "state": "running",
                                      "updated_at": time.time()}}
        board = {"root": "/x", "generated_at": time.time(), "epics": [],
                 "groups": [], "standalone": [member]}
        app = dashboard.BoardApp(root="/x", board_fn=lambda: board)
        async with app.run_test():
            ind = app.query_one("#autopilot-indicator", dashboard.Static)
            text = str(ind.render())
            self.assertIn("building", text)
            self.assertNotIn("autopilot on", text)

    async def test_empty_board_leaves_the_search_input_unfocused(self):
        # With no card to focus, on_mount blurs the auto-focused search input
        # so the app-level keys (`g`/`q`/`/`) still fire on an empty board.
        empty = {"root": "/x", "generated_at": time.time(), "epics": [],
                 "groups": []}
        app = dashboard.BoardApp(root="/x", board_fn=lambda: empty)
        async with app.run_test():
            inp = app.query_one("#board-search-input", dashboard.SearchInput)
            self.assertFalse(inp.has_focus)


class FilterStripChromeTest(unittest.IsolatedAsyncioTestCase):
    """The filter strip's chrome (delivery-dashboard board-filter-strip spec):
    a row between the header bar and the lanes carrying full-board totals, the
    filter chips with a ``+ filter`` control, and the shipped-this-week /
    synced-ago stats repainted each refresh."""

    def _strip(self, app):
        return app.query_one("#filter-strip")

    async def test_strip_sits_between_the_header_bar_and_the_lanes(self):
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test():
            ids = [w.id for w in app.screen.children]
            self.assertIn("filter-strip", ids)
            self.assertLess(ids.index("header-bar"), ids.index("filter-strip"))
            self.assertLess(ids.index("filter-strip"), ids.index("body"))

    async def test_strip_holds_totals_chips_add_and_stat_labels(self):
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test():
            strip = self._strip(app)
            totals = strip.query_one("#board-totals", dashboard.Static)
            # Full board: 3 members across 1 epic under 1 initiative.
            self.assertEqual(str(totals.render()),
                             "3 specs · 1 epics · 1 initiatives")
            self.assertTrue(strip.query("#filter-chips"))
            self.assertTrue(strip.query("#filter-add"))
            self.assertTrue(strip.query("#board-shipped"))
            self.assertTrue(strip.query("#board-synced"))

    async def test_totals_stay_full_board_while_a_chip_narrows(self):
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test() as pilot:
            totals = app.query_one("#board-totals", dashboard.Static)
            self.assertEqual(str(totals.render()),
                             "3 specs · 1 epics · 1 initiatives")
            app.filters = [("risk", "high")]
            await app._render_lanes()
            await pilot.pause()
            # The chip narrows the visible board, but the totals report the
            # full board unchanged.
            self.assertEqual(str(totals.render()),
                             "3 specs · 1 epics · 1 initiatives")

    async def test_refresh_repaints_the_shipped_and_synced_stats(self):
        now = _dt.datetime.now(_dt.timezone.utc)
        events = [
            {"slug": "a", "ship_ts": now},
            {"slug": "b", "ship_ts": now},
        ]
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test():
            with mock.patch.object(dashboard.mtr, "collect_ship_events",
                                   return_value=events):
                await app.refresh_board()
            expected = dashboard.shipped_this_week(events)
            self.assertEqual(expected, 2)
            shipped = app.query_one("#board-shipped", dashboard.Static)
            self.assertEqual(str(shipped.render()),
                             "▲ %d shipped this week" % expected)
            synced = app.query_one("#board-synced", dashboard.Static)
            self.assertIsNotNone(app._last_sync)
            self.assertEqual(str(synced.render()),
                             dashboard._sync_label(app._last_sync))
            self.assertTrue(str(synced.render()).startswith("synced "))
            self.assertNotEqual(str(synced.render()), "synced ?")


# ---------------------------------------------------------------------------
# Grouping mode — epic / initiative / none
# ---------------------------------------------------------------------------

class GroupModeCyclingTest(unittest.IsolatedAsyncioTestCase):
    """The three-state grouping mode (delivery-dashboard board-epic-grouping
    spec): ``epic`` by default, cycled ``epic`` → ``initiative`` → ``none`` →
    ``epic`` by the footer-bound ``g`` key, repainting the lanes at each step."""

    async def test_group_mode_defaults_to_epic(self):
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test():
            self.assertEqual(app.group_mode, "epic")

    async def test_g_cycles_the_mode_and_repaints_at_each_step(self):
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test() as pilot:
            lane = app.query_one("#lane-building", dashboard.Lane)
            before = set(lane.query(dashboard.TaskCard))
            self.assertTrue(before)
            await pilot.press("g")
            self.assertEqual(app.group_mode, "initiative")
            after = set(lane.query(dashboard.TaskCard))
            # A mode change repaints, so the lane's card widgets are remounted.
            self.assertNotEqual(before, after)
            await pilot.press("g")
            self.assertEqual(app.group_mode, "none")
            await pilot.press("g")
            self.assertEqual(app.group_mode, "epic")


class InitiativeModeGroupingTest(unittest.IsolatedAsyncioTestCase):
    """Initiative mode groups each lane's cards by initiative (delivery-
    dashboard board-epic-grouping spec): epics sharing one initiative sit
    under a single collapsible titled ``<slug> [<status>]`` plus the muted
    ` (N)` per-lane count suffix, epics carrying no ``Initiative:`` collect
    under a ``workspace`` group; epic actions are epic-scoped, so an
    initiative header never opens anything on click."""

    async def test_shared_initiative_and_workspace_groups_no_controls(self):
        app = dashboard.BoardApp(root="/x",
                                 board_fn=_initiative_grouped_board)
        async with app.run_test() as pilot:
            await pilot.press("g")  # epic -> initiative
            self.assertEqual(app.group_mode, "initiative")
            lane = app.query_one("#lane-ready", dashboard.Lane)
            groups = list(lane.query(Collapsible))
            titles = [g.title for g in groups]
            # The shared initiative holds two cards, the workspace bucket one —
            # each count rides the title as a muted ` (N)` suffix.
            self.assertIn("init [active] [$fg-muted](2)[/]", titles)
            self.assertIn("workspace [$fg-muted](1)[/]", titles)
            init_group = next(g for g in groups
                              if g.title.startswith("init [active]"))
            self.assertEqual(
                sorted(c.member["slug"]
                       for c in init_group.query(dashboard.TaskCard)),
                ["m-ep1", "m-ep2"])
            ws_group = next(g for g in groups
                            if g.title.startswith("workspace"))
            self.assertEqual(
                [c.member["slug"] for c in ws_group.query(dashboard.TaskCard)],
                ["m-ep3"])

    async def test_initiative_groups_clear_the_docked_lane_header(self):
        # Initiative-mode groups carry `.epic-group` but mount straight into
        # the lane, not into an `EpicGroupRow` — the only parent declaring the
        # `group`/`menu` layers the epic-mode float uses. Scoping that layer to
        # `.epic-group-row .epic-group` keeps these groups in normal flow, so
        # they start below the docked `.lane-header` band instead of being laid
        # out under it with their title row painted over (delivery-dashboard
        # board-epic-grouping spec: the header is the group's first row).
        app = dashboard.BoardApp(root="/x",
                                 board_fn=_initiative_grouped_board)
        async with app.run_test() as pilot:
            await pilot.press("g")  # epic -> initiative
            await pilot.pause()
            lane = app.query_one("#lane-ready", dashboard.Lane)
            header = lane.query_one(".lane-header")
            groups = list(lane.query(Collapsible))
            self.assertTrue(groups, "no initiative group to check")
            for group in groups:
                self.assertFalse(
                    group.region.overlaps(header.region),
                    "%r region %r is laid out under the docked lane header %r"
                    % (group.id, group.region, header.region))


class BoardSearchTest(unittest.IsolatedAsyncioTestCase):
    """Live member search from the controls strip (delivery-dashboard
    board-search spec): ``/`` focuses the input, typing filters the lanes
    with the matched slug span highlighted and a live match count, and
    ``escape``/``✕`` clear it. Exercised over ``_two_epic_board`` — ep1/m1
    and ep2/m2, both in the READY lane under initiative ``init``."""

    def _ready(self, app):
        return app.query_one("#lane-ready", dashboard.Lane)

    def _ready_slugs(self, app):
        return sorted(c.member["slug"]
                      for c in self._ready(app).query(dashboard.TaskCard))

    async def _set_query(self, app, pilot, query):
        inp = app.query_one("#board-search-input", dashboard.SearchInput)
        inp.value = query
        await pilot.pause()

    async def test_slash_focuses_the_search_input(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test() as pilot:
            card = next(iter(app.query(dashboard.TaskCard)))
            card.focus()
            await pilot.pause()
            await pilot.press("slash")
            inp = app.query_one("#board-search-input", dashboard.SearchInput)
            self.assertTrue(inp.has_focus)

    async def test_typing_a_member_slug_query_mounts_only_matching_cards(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test() as pilot:
            await self._set_query(app, pilot, "m1")
            self.assertEqual(self._ready_slugs(app), ["m1"])

    async def test_an_epic_slug_match_keeps_that_epics_members_mounted(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test() as pilot:
            # "ep2" hits only ep2's slug — m2 (whose slug lacks it) stays,
            # m1 (in ep1) drops.
            await self._set_query(app, pilot, "ep2")
            self.assertEqual(self._ready_slugs(app), ["m2"])

    async def test_a_slug_matched_card_carries_the_accent_highlight(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test() as pilot:
            await self._set_query(app, pilot, "m1")
            card = next(c for c in self._ready(app).query(dashboard.TaskCard)
                        if c.member["slug"] == "m1")
            self.assertIn("[$accent]", card._card_text())

    async def test_an_epic_only_match_renders_without_a_slug_highlight(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test() as pilot:
            await self._set_query(app, pilot, "ep2")
            card = next(c for c in self._ready(app).query(dashboard.TaskCard)
                        if c.member["slug"] == "m2")
            self.assertNotIn("[$accent]", card._card_text())

    async def test_the_match_count_reports_matches_and_blanks_when_cleared(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test() as pilot:
            count = app.query_one("#board-search-count", dashboard.Static)
            self.assertEqual(str(count.render()), "")
            await self._set_query(app, pilot, "m1")
            self.assertEqual(str(count.render()), "1 match")
            await self._set_query(app, pilot, "m")
            self.assertEqual(str(count.render()), "2 matches")
            await self._set_query(app, pilot, "")
            self.assertEqual(str(count.render()), "")

    async def test_escape_in_the_input_restores_the_full_board(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test() as pilot:
            await self._set_query(app, pilot, "m1")
            self.assertEqual(self._ready_slugs(app), ["m1"])
            inp = app.query_one("#board-search-input", dashboard.SearchInput)
            inp.focus()
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()
            self.assertEqual(self._ready_slugs(app), ["m1", "m2"])
            self.assertEqual(inp.value, "")

    async def test_the_clear_control_restores_the_full_board(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test(size=(120, 24)) as pilot:
            await self._set_query(app, pilot, "m1")
            self.assertEqual(self._ready_slugs(app), ["m1"])
            clear = app.query_one("#board-search-clear", Button)
            await pilot.click(clear)
            await pilot.pause()
            self.assertEqual(self._ready_slugs(app), ["m1", "m2"])

    async def test_a_fully_filtered_epic_mounts_no_group_header(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test() as pilot:
            self.assertEqual(app.group_mode, "epic")
            await self._set_query(app, pilot, "m1")
            # ep1 keeps its group header; ep2 (fully filtered) mounts none in
            # any lane.
            self.assertTrue(app.query("#epic-group-ready-ep1"))
            self.assertFalse(app.query("#epic-group-ready-ep2"))

    async def test_unchanged_refresh_under_a_query_retains_card_instances(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test() as pilot:
            await self._set_query(app, pilot, "m1")
            before = set(app.query(dashboard.TaskCard))
            self.assertTrue(before)
            await app.refresh_board()
            await pilot.pause()
            after = set(app.query(dashboard.TaskCard))
            self.assertEqual(before, after)

    async def test_refresh_after_the_count_label_is_removed_does_not_raise(self):
        # An interval-timer refresh can fire during app teardown, after the
        # count label has been unmounted; `_render_lanes` must query the label
        # empty-safely rather than raise `NoMatches` (regression: an
        # unconditional `query_one("#board-search-count")` failed a teardown-
        # time tick — CI run 30809175419).
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test() as pilot:
            label = app.query_one("#board-search-count", dashboard.Static)
            await label.remove()
            await pilot.pause()
            self.assertFalse(app.query("#board-search-count"))
            await app.refresh_board()  # must not raise NoMatches


def _split_lane_board():
    """Two epics under one initiative, each with one member in a *different*
    lane — ep1/m1 READY, ep2/m2 UNPLANNED — so an epic chip that excludes ep2
    empties the UNPLANNED lane (exercising the emptied-lane empty-state branch)
    while ep1 keeps its READY group header."""
    init = {"slug": "init", "status": "active"}
    ep1 = {
        "slug": "ep1", "status": "active", "theme": None, "initiative": init,
        "members": [{"slug": "m1", "description": "d", "risk": "low",
                     "state": "ready", "location": "/x", "actions": ["run"],
                     "session_id": None}],
        "heartbeat": None, "report": None,
    }
    ep2 = {
        "slug": "ep2", "status": "active", "theme": None, "initiative": init,
        "members": [{"slug": "m2", "description": "d", "risk": "high",
                     "state": "unplanned", "location": "/x",
                     "actions": ["plan"], "session_id": None}],
        "heartbeat": None, "report": None,
    }
    return {
        "root": "/x", "generated_at": time.time(),
        "epics": [ep1, ep2],
        "groups": [{"initiative": init, "epics": [ep1, ep2]}],
    }


class FilterStripLaneTest(unittest.IsolatedAsyncioTestCase):
    """Filter chips narrow the mounted lanes (delivery-dashboard
    board-filter-strip spec), composed with the live search and folded into
    the diff-aware signatures. Driven by setting ``app.filters`` and awaiting
    ``_render_lanes``."""

    def _slugs(self, app):
        return sorted(c.member["slug"]
                      for c in app.query(dashboard.TaskCard))

    async def test_a_risk_chip_mounts_only_matching_members(self):
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test() as pilot:
            self.assertEqual(self._slugs(app), ["driver", "fresh", "rdy"])
            app.filters = [("risk", "high")]
            await app._render_lanes()
            await pilot.pause()
            # Only the high-risk member (`fresh`) survives.
            self.assertEqual(self._slugs(app), ["fresh"])

    async def test_chips_compose_with_the_search_query(self):
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test() as pilot:
            app.filters = [("risk", "low")]
            app.search_query = "driver"
            await app._render_lanes()
            await pilot.pause()
            # `driver` is low-risk (chip) and matches the query — kept.
            self.assertEqual(self._slugs(app), ["driver"])
            # A query the low-risk member fails empties the board even though
            # the chip alone would keep it — both must keep a member.
            app.search_query = "rdy"
            await app._render_lanes()
            await pilot.pause()
            self.assertEqual(self._slugs(app), [])

    async def test_an_epic_chip_excludes_the_epic_and_empties_its_lane(self):
        app = dashboard.BoardApp(root="/x", board_fn=_split_lane_board)
        async with app.run_test() as pilot:
            self.assertEqual(app.group_mode, "epic")
            app.filters = [("epic", "ep1")]
            await app._render_lanes()
            await pilot.pause()
            # ep2 is fully excluded — no group header for it in any lane.
            self.assertFalse(app.query("#epic-group-unplanned-ep2"))
            self.assertEqual(self._slugs(app), ["m1"])
            # The UNPLANNED lane, emptied of ep2/m2, shows its empty-state text.
            unplanned = app.query_one("#lane-unplanned", dashboard.Lane)
            empties = unplanned.query(".lane-empty")
            self.assertTrue(empties)
            self.assertIn("nothing unplanned", str(empties.first().render()))

    def test_lane_signature_differs_when_only_filters_differ(self):
        cards = [("ep1", "active", {"slug": "m1", "state": "ready"}, None)]
        sig_none = dashboard._lane_signature(cards, "epic", "", None, ())
        sig_filtered = dashboard._lane_signature(
            cards, "epic", "", None, (("risk", "high"),))
        self.assertNotEqual(sig_none, sig_filtered)

    async def test_steady_chips_retain_cards_and_a_chip_change_repaints(self):
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test() as pilot:
            app.filters = [("risk", "high")]
            await app._render_lanes()
            await pilot.pause()
            before = set(app.query(dashboard.TaskCard))
            self.assertTrue(before)
            # An unchanged refresh under the same chips retains the instances.
            await app.refresh_board()
            await pilot.pause()
            self.assertEqual(set(app.query(dashboard.TaskCard)), before)
            # A chip change repaints — the mounted set now differs.
            app.filters = []
            await app._render_lanes()
            await pilot.pause()
            self.assertEqual(self._slugs(app), ["driver", "fresh", "rdy"])


class FilterPickerTest(unittest.IsolatedAsyncioTestCase):
    """The filter picker and chip lifecycle (delivery-dashboard
    board-filter-strip spec): ``f`` (and the ``+ filter`` control) pushes a
    modal ``FilterPickerScreen`` of the not-yet-active options, ``escape``
    cancels, selecting an option adds a removable chip that narrows the lanes,
    and pressing a chip removes it and restores its members. Exercised over
    ``_kanban_board`` (low/medium/high-risk members)."""

    def _slugs(self, app):
        return sorted(c.member["slug"]
                      for c in app.query(dashboard.TaskCard))

    def _picker_options(self, screen):
        # The picker composes one option Button per `_filter_options` entry,
        # each carrying its `(chip_kind, chip_value)`.
        return [(b.chip_kind, b.chip_value)
                for b in screen.query(Button)
                if getattr(b, "chip_kind", None) is not None]

    def _chip_buttons(self, app):
        chips = app.query_one("#filter-chips")
        return [b for b in chips.query(Button)
                if getattr(b, "chip_kind", None) is not None]

    async def test_f_pushes_the_picker_listing_the_available_options(self):
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test() as pilot:
            await pilot.press("f")
            await pilot.pause()
            self.assertIsInstance(app.screen, dashboard.FilterPickerScreen)
            # The picker lists exactly `_filter_options`, in order.
            self.assertEqual(
                self._picker_options(app.screen),
                dashboard._filter_options(app.board, app.filters))

    async def test_active_chips_are_absent_from_the_picker(self):
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test() as pilot:
            app.filters = [("risk", "high")]
            await pilot.press("f")
            await pilot.pause()
            options = self._picker_options(app.screen)
            self.assertNotIn(("risk", "high"), options)
            # The other risk tiers remain on offer.
            self.assertIn(("risk", "medium"), options)

    async def test_f_is_inert_while_a_modal_is_open(self):
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test() as pilot:
            await app.push_screen(ModalScreen())
            await pilot.pause()
            top = app.screen
            app.action_add_filter()
            await pilot.pause()
            # No picker was pushed; the open modal is undisturbed.
            self.assertIs(app.screen, top)
            self.assertNotIsInstance(
                app.screen, dashboard.FilterPickerScreen)

    async def test_escape_dismisses_the_picker_without_adding(self):
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test() as pilot:
            await pilot.press("f")
            await pilot.pause()
            self.assertIsInstance(app.screen, dashboard.FilterPickerScreen)
            await pilot.press("escape")
            await pilot.pause()
            self.assertNotIsInstance(
                app.screen, dashboard.FilterPickerScreen)
            self.assertEqual(app.filters, [])

    async def test_selecting_an_option_adds_a_chip_and_filters(self):
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("f")
            await pilot.pause()
            option = next(b for b in app.screen.query(Button)
                          if getattr(b, "chip_value", None) == "high")
            await pilot.click(option)
            await pilot.pause()
            # The chip is recorded and the picker dismissed.
            self.assertIn(("risk", "high"), app.filters)
            self.assertNotIsInstance(
                app.screen, dashboard.FilterPickerScreen)
            # A removable chip button is mounted in the strip.
            self.assertTrue(any(
                b.chip_kind == "risk" and b.chip_value == "high"
                for b in self._chip_buttons(app)))
            # The lanes now show only the high-risk member.
            self.assertEqual(self._slugs(app), ["fresh"])

    async def test_pressing_a_chip_removes_it_and_restores_members(self):
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test(size=(120, 40)) as pilot:
            await app.apply_filter("risk", "high")
            await pilot.pause()
            self.assertEqual(self._slugs(app), ["fresh"])
            chip = next(b for b in self._chip_buttons(app)
                        if b.chip_value == "high")
            await pilot.click(chip)
            await pilot.pause()
            self.assertEqual(app.filters, [])
            self.assertEqual(self._slugs(app), ["driver", "fresh", "rdy"])

    async def test_the_filter_add_control_opens_the_picker(self):
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test(size=(120, 40)) as pilot:
            add = app.query_one("#filter-add", Button)
            await pilot.click(add)
            await pilot.pause()
            self.assertIsInstance(app.screen, dashboard.FilterPickerScreen)


class BoardCommandPaletteTest(unittest.IsolatedAsyncioTestCase):
    """The command palette populated with board commands (delivery-dashboard
    board-command-palette spec): ``ctrl+p`` opens textual's palette,
    ``get_system_commands`` yields exactly the board's own commands in place
    of the stock set (a grouping-cycle command + quit, plus clear-search while
    a query is active), a modal screen offers only quit, and the footer
    advertises the ``^p`` key. Exercised over ``_two_epic_board`` — ep1/m1 and
    ep2/m2, both in the READY lane."""

    def _ready_slugs(self, app):
        lane = app.query_one("#lane-ready", dashboard.Lane)
        return sorted(c.member["slug"]
                      for c in lane.query(dashboard.TaskCard))

    def _titles(self, app, screen):
        return [c.title for c in app.get_system_commands(screen)]

    async def _set_query(self, app, pilot, query):
        inp = app.query_one("#board-search-input", dashboard.SearchInput)
        inp.value = query
        await pilot.pause()

    async def test_ctrl_p_pushes_the_command_palette_screen(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test() as pilot:
            await pilot.press("ctrl+p")
            await pilot.pause()
            self.assertIsInstance(app.screen, CommandPalette)

    async def test_board_screen_lists_grouping_metrics_and_quit_only(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test() as pilot:
            await pilot.pause()
            titles = self._titles(app, app.screen)
            self.assertEqual(
                set(titles), {"Cycle grouping", "Delivery metrics", "Quit"})
            joined = " ".join(titles).lower()
            self.assertNotIn("theme", joined)
            self.assertNotIn("keys", joined)
            self.assertNotIn("screenshot", joined)

    async def test_delivery_metrics_command_pushes_the_metrics_screen(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test() as pilot:
            await pilot.pause()
            cmd = next(c for c in app.get_system_commands(app.screen)
                       if c.title == "Delivery metrics")
            cmd.callback()
            await pilot.pause()
            self.assertIsInstance(app.screen, dashboard.MetricsScreen)

    async def test_clear_search_command_appears_only_with_a_query(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test() as pilot:
            await pilot.pause()
            self.assertNotIn("Clear search", self._titles(app, app.screen))
            await self._set_query(app, pilot, "m1")
            self.assertIn("Clear search", self._titles(app, app.screen))
            await self._set_query(app, pilot, "")
            self.assertNotIn("Clear search", self._titles(app, app.screen))

    async def test_a_modal_screen_offers_only_quit(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test() as pilot:
            await pilot.pause()
            titles = self._titles(app, ModalScreen())
            self.assertEqual(titles, ["Quit"])

    async def test_grouping_command_advances_the_mode(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test() as pilot:
            await pilot.pause()
            self.assertEqual(app.group_mode, "epic")
            cmd = next(c for c in app.get_system_commands(app.screen)
                       if c.title == "Cycle grouping")
            await cmd.callback()
            await pilot.pause()
            self.assertEqual(app.group_mode, "initiative")

    async def test_clear_search_command_callback_restores_the_board(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test() as pilot:
            await self._set_query(app, pilot, "m1")
            self.assertEqual(self._ready_slugs(app), ["m1"])
            cmd = next(c for c in app.get_system_commands(app.screen)
                       if c.title == "Clear search")
            await cmd.callback()
            await pilot.pause()
            self.assertEqual(app.search_query, "")
            self.assertEqual(self._ready_slugs(app), ["m1", "m2"])

    async def test_clear_filters_command_appears_only_with_chips(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test() as pilot:
            await pilot.pause()
            self.assertNotIn("Clear filters", self._titles(app, app.screen))
            await app.apply_filter("epic", "ep1")
            self.assertIn("Clear filters", self._titles(app, app.screen))
            await app._clear_filters()
            self.assertNotIn("Clear filters", self._titles(app, app.screen))

    async def test_clear_filters_command_callback_restores_the_board(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test() as pilot:
            await app.apply_filter("epic", "ep1")
            await pilot.pause()
            self.assertEqual(self._ready_slugs(app), ["m1"])
            cmd = next(c for c in app.get_system_commands(app.screen)
                       if c.title == "Clear filters")
            await cmd.callback()
            await pilot.pause()
            self.assertEqual(app.filters, [])
            # Every member's card is mounted again.
            self.assertEqual(self._ready_slugs(app), ["m1", "m2"])
            # The chip row is emptied of chip buttons (only `+ filter` remains).
            chips = app.query_one("#filter-chips")
            self.assertFalse([b for b in chips.query(Button)
                              if getattr(b, "chip_kind", None) is not None])

    def test_bindings_advertise_a_visible_ctrl_p_palette_key(self):
        binding = next(
            (b for b in dashboard.BoardApp.BINDINGS
             if getattr(b, "action", None) == "command_palette"), None)
        self.assertIsNotNone(binding)
        self.assertEqual(binding.key, "ctrl+p")
        self.assertEqual(binding.key_display, "^p")
        self.assertTrue(binding.show)


# ---------------------------------------------------------------------------
# Delivery-metrics screen: the `m`-key modal, its four sections rendered off
# the UI thread through the `_apply_data` seam, and its dismissal controls
# (delivery-dashboard board-metrics-view spec)
# ---------------------------------------------------------------------------

def _metrics_data():
    """A full delivery-metrics assembly (a ``metrics.derive`` dict plus
    ``ship_events``) with every section populated — the injected ``data_fn``
    payload for exercising ``MetricsScreen._apply_data`` without touching git
    or waiting on the thread worker."""
    return {
        "metrics": {
            "deployment_days": {
                "per_week": [{"week": "2026-W30", "count": 2},
                             {"week": "2026-W31", "count": 3}],
                "dora_band": "weekly",
            },
            "throughput": {
                "per_week": [{"week": "2026-W30", "count": 1},
                             {"week": "2026-W31", "count": 4}],
                "total": 5,
            },
            "lead_time": {"median": 3600, "p85": 7200, "n": 5},
            "cycle_time": {"median": 200, "p50": 200, "p85": 300,
                           "p95": 300, "n": 3},
            "change_failures": {"rate": 0.1},
            "outcomes": {"rework_rate": 0.2},
            "flow": {
                "series": [
                    {"ts": "2026-08-01T00:00:00Z",
                     "by_state": {"archived": 2, "active": 2}},
                    {"ts": "2026-08-02T00:00:00Z",
                     "by_state": {"ready": 1, "unplanned": 3}},
                ],
                "n": 2,
            },
        },
        "ship_events": [
            {"slug": "a", "ship_ts": __import__("datetime").datetime(
                2026, 8, 1, tzinfo=__import__("datetime").timezone.utc),
             "seconds": 100},
            {"slug": "b", "ship_ts": __import__("datetime").datetime(
                2026, 8, 2, tzinfo=__import__("datetime").timezone.utc),
             "seconds": 300},
        ],
    }


class MetricsScreenTest(unittest.IsolatedAsyncioTestCase):
    """The board's delivery-metrics modal (delivery-dashboard
    board-metrics-view spec): ``m`` pushes it (and is inert over an open
    modal), the four sections populate through the ``_apply_data`` seam behind
    the computing placeholder, a failing assembly never raises, and ``Escape``
    or the ✕ control dismisses it."""

    async def test_m_pushes_the_metrics_screen(self):
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test() as pilot:
            await pilot.press("m")
            await pilot.pause()
            self.assertIsInstance(app.screen, dashboard.MetricsScreen)

    def test_bindings_advertise_a_visible_m_key(self):
        binding = next(
            (b for b in dashboard.BoardApp.BINDINGS
             if getattr(b, "action", None) == "show_metrics"), None)
        self.assertIsNotNone(binding)
        self.assertEqual(binding.key, "m")
        self.assertTrue(binding.show)

    async def test_m_is_inert_while_a_modal_is_open(self):
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test() as pilot:
            # Open an unrelated modal, then fire the metrics action.
            await app.push_screen(ModalScreen())
            await pilot.pause()
            top = app.screen
            app.action_show_metrics()
            await pilot.pause()
            # No metrics screen was pushed; the open modal is undisturbed.
            self.assertIs(app.screen, top)
            self.assertNotIsInstance(app.screen, dashboard.MetricsScreen)

    async def test_apply_data_populates_the_four_sections(self):
        data = _metrics_data()
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test() as pilot:
            screen = dashboard.MetricsScreen(root="/x", data_fn=lambda: data)
            await app.push_screen(screen)
            await pilot.pause()
            # The apply seam swaps the placeholder for the four sections
            # in place, without the screen being reopened.
            screen._apply_data(data)
            await pilot.pause()
            self.assertEqual(list(screen.query("#metrics-computing")), [])
            for section_id in ("#metrics-dora", "#metrics-runchart",
                               "#metrics-scatter", "#metrics-cfd"):
                self.assertTrue(
                    len(list(screen.query(section_id))) == 1,
                    "missing section %s" % section_id)

    async def test_failing_assembly_never_raises(self):
        def boom():
            raise RuntimeError("git blew up")

        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test() as pilot:
            screen = dashboard.MetricsScreen(root="/x", data_fn=boom)
            await app.push_screen(screen)
            await pilot.pause()
            # The compute seam swallows the failure rather than raising.
            self.assertIsNone(screen._compute())
            # Applying the failed (None) result leaves the screen rendered
            # with an unavailable notice, no traceback.
            screen._apply_data(None)
            await pilot.pause()
            self.assertIsInstance(app.screen, dashboard.MetricsScreen)
            text = "\n".join(str(w.render())
                             for w in screen.query(dashboard.Static))
            self.assertIn("unavailable", text.lower())

    async def test_escape_dismisses_back_to_the_board(self):
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test() as pilot:
            await pilot.press("m")
            await pilot.pause()
            self.assertIsInstance(app.screen, dashboard.MetricsScreen)
            await pilot.press("escape")
            await pilot.pause()
            self.assertNotIsInstance(app.screen, dashboard.MetricsScreen)

    async def test_close_control_dismisses_back_to_the_board(self):
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("m")
            await pilot.pause()
            self.assertIsInstance(app.screen, dashboard.MetricsScreen)
            close_button = app.screen.query_one("#close-metrics", Button)
            await pilot.click(close_button)
            await pilot.pause()
            self.assertNotIsInstance(app.screen, dashboard.MetricsScreen)


# ---------------------------------------------------------------------------
# Spec-detail modal: bigger container, epic-status header, spec-file tabset,
# clickable close control
# ---------------------------------------------------------------------------

def _detail_board(root, member_slug, epic_status="active", location=None):
    """A board with one epic (status ``epic_status``) holding a single
    member ``member_slug`` in the ``ready`` lane — for exercising the
    rebuilt ``MemberDetailScreen`` against a real content-dir ``root`` so
    ``change_artifacts`` resolves real on-disk files. ``location`` overrides
    the member's worktree-aware hosting directory (default: ``root``), so a
    change that lives only under ``.worktrees/<slug>`` can be exercised."""
    epic = {
        "slug": "ep", "status": epic_status, "theme": None,
        "initiative": None,
        "members": [{"slug": member_slug, "description": "d", "risk": "high",
                    "state": "ready", "location": location or root,
                    "actions": ["run"], "session_id": None}],
        "heartbeat": None, "report": None,
    }
    return {"root": root, "generated_at": time.time(), "epics": [epic],
            "groups": [{"initiative": None, "epics": [epic]}]}


class SpecDetailModalTest(DashboardTestBase, unittest.IsolatedAsyncioTestCase):
    """The spec-detail modal (delivery-dashboard board-tui spec) rebuilds
    ``MemberDetailScreen`` into: a container occupying most of the viewport,
    a header naming the change and its epic's status, a horizontal rule, and
    below it a tabbed view of the change's on-disk spec artifacts (or a
    not-yet-planned notice) — dismissed by a clickable close control (in
    addition to ``Escape``)."""

    def _plant_artifacts(self, slug, base=None):
        base = base or self.root
        _write(os.path.join(base, ".shipd", "planned", slug, "plan.md"),
               "# %s plan\n" % slug)
        _write(os.path.join(base, ".shipd", "planned", slug, "specs",
                            "delivery-dashboard", "spec.md"),
               "# %s spec\n" % slug)
        _write(os.path.join(base, ".shipd", "planned", slug, "tasks.md"),
               "# %s tasks\n" % slug)

    async def _open_detail(self, pilot, app, slug):
        card = _find_card(app, slug)
        card.focus()
        await pilot.pause()
        await pilot.press("enter")

    async def test_modal_container_is_larger_than_the_old_fixed_box(self):
        self._plant_artifacts("documented")
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _detail_board(self.root, "documented"))
        async with app.run_test() as pilot:
            await self._open_detail(pilot, app, "documented")
            container = app.screen.query_one(dashboard.Container)
            # The old fixed box was `width: 60` (columns); the new one is
            # `width: 80%` of the (80-column) test harness viewport.
            self.assertGreater(container.region.width, 60)
            self.assertEqual(container.styles.width.value, 80)

    async def test_header_names_change_and_epic_status(self):
        self._plant_artifacts("documented")
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _detail_board(self.root, "documented",
                                           epic_status="active"))
        async with app.run_test() as pilot:
            await self._open_detail(pilot, app, "documented")
            header_text = "\n".join(
                str(w.content) for w in app.screen.query(dashboard.Static))
            self.assertIn("documented", header_text)
            self.assertIn("high", header_text)  # risk
            self.assertIn("ready", header_text)  # state
            self.assertIn("epic: ep [active]", header_text)

    async def test_tabbed_view_lists_discovered_artifacts(self):
        self._plant_artifacts("documented")
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _detail_board(self.root, "documented"))
        async with app.run_test() as pilot:
            await self._open_detail(pilot, app, "documented")
            tabs = app.screen.query_one(TabbedContent)
            labels = [t.label_text for t in tabs.query(Tab)]
            # Exactly one spec dir is planted, so it's labelled just "Spec"
            # (the "Spec: <cap>" form only kicks in with more than one).
            self.assertEqual(labels, ["Plan", "Spec", "Tasks"])

    async def test_unplanned_change_shows_notice_and_no_tabset(self):
        # No `.shipd/planned/undocumented/` directory is planted.
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _detail_board(self.root, "undocumented"))
        async with app.run_test() as pilot:
            await self._open_detail(pilot, app, "undocumented")
            self.assertEqual(list(app.screen.query(TabbedContent)), [])
            notice_text = "\n".join(
                str(w.content) for w in app.screen.query(dashboard.Static))
            self.assertIn("not yet planned", notice_text.lower())

    async def test_worktree_planned_member_renders_its_artifacts(self):
        # The change lives only under `.worktrees/<slug>` (the member's
        # `location`); the app root carries no `.shipd/planned/<slug>`.
        worktree = os.path.join(self.root, ".worktrees", "documented")
        self._plant_artifacts("documented", base=worktree)
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _detail_board(
                self.root, "documented", location=worktree))
        async with app.run_test() as pilot:
            await self._open_detail(pilot, app, "documented")
            tabs = app.screen.query_one(TabbedContent)
            labels = [t.label_text for t in tabs.query(Tab)]
            self.assertEqual(labels, ["Plan", "Spec", "Tasks"])

    async def test_worktree_location_without_change_shows_notice(self):
        # The recorded location holds no change (e.g. worktree removed), so
        # the modal degrades to the not-yet-planned notice without error.
        worktree = os.path.join(self.root, ".worktrees", "documented")
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _detail_board(
                self.root, "documented", location=worktree))
        async with app.run_test() as pilot:
            await self._open_detail(pilot, app, "documented")
            self.assertEqual(list(app.screen.query(TabbedContent)), [])
            notice_text = "\n".join(
                str(w.content) for w in app.screen.query(dashboard.Static))
            self.assertIn("not yet planned", notice_text.lower())

    async def test_clicking_close_button_dismisses_the_modal(self):
        self._plant_artifacts("documented")
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _detail_board(self.root, "documented"))
        async with app.run_test() as pilot:
            await self._open_detail(pilot, app, "documented")
            self.assertIsInstance(app.screen, dashboard.MemberDetailScreen)
            close_button = app.screen.query_one("#close-detail", Button)
            await pilot.click(close_button)
            self.assertNotIsInstance(app.screen, dashboard.MemberDetailScreen)


class LiveArtifactMountTest(DashboardTestBase, unittest.IsolatedAsyncioTestCase):
    """The spec-detail modal is live while a member is driven (delivery-
    dashboard modal-live-artifacts spec): a no-artifact member with a live
    stage shows the stage-aware notice, and a refresh tick swaps the notice
    for the tabbed artifact view the moment the artifacts appear — without the
    modal being closed and reopened — while leaving already-mounted tabs
    untouched."""

    def _push(self, app, entry, location=None):
        member = {"slug": "documented", "description": "d", "risk": "high",
                  "state": "driving", "location": location or self.root,
                  "actions": [], "session_id": None}
        app.push_screen(
            dashboard.MemberDetailScreen("ep", member, entry, "active"))

    def _plant(self, slug, base=None):
        base = base or self.root
        _write(os.path.join(base, ".shipd", "planned", slug, "plan.md"),
               "# %s plan\n" % slug)
        _write(os.path.join(base, ".shipd", "planned", slug, "tasks.md"),
               "# %s tasks\n" % slug)

    async def test_driving_member_shows_stage_aware_notice(self):
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _detail_board(self.root, "documented"))
        async with app.run_test() as pilot:
            self._push(app, {"slug": "documented", "state": "driving",
                             "stage": "plan", "attempt": 1})
            await pilot.pause()
            self.assertEqual(list(app.screen.query(TabbedContent)), [])
            notice = app.screen.query_one("#artifact-notice", dashboard.Static)
            self.assertIn("plan in progress (plan#1)", str(notice.render()))

    async def test_refresh_swaps_notice_for_tabs_on_same_screen(self):
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _detail_board(self.root, "documented"))
        async with app.run_test() as pilot:
            self._push(app, {"slug": "documented", "state": "driving",
                             "stage": "plan", "attempt": 1})
            await pilot.pause()
            screen = app.screen
            self.assertTrue(screen.query("#artifact-notice"))
            # Artifacts appear on disk; a refresh tick must mount the tabs on
            # this same open screen object.
            self._plant("documented")
            screen._refresh_activity()
            await pilot.pause()
            self.assertIs(app.screen, screen)
            self.assertEqual(list(screen.query("#artifact-notice")), [])
            tabs = screen.query_one(TabbedContent)
            labels = [t.label_text for t in tabs.query(Tab)]
            self.assertEqual(labels, ["Plan", "Tasks"])

    async def test_further_refresh_leaves_mounted_tabs_unchanged(self):
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _detail_board(self.root, "documented"))
        async with app.run_test() as pilot:
            self._push(app, {"slug": "documented", "state": "driving",
                             "stage": "plan", "attempt": 1})
            await pilot.pause()
            screen = app.screen
            self._plant("documented")
            screen._refresh_activity()
            await pilot.pause()
            tabs = screen.query_one(TabbedContent)
            # A further tick must not remount — the same widget identity stays.
            screen._refresh_activity()
            await pilot.pause()
            self.assertIs(screen.query_one(TabbedContent), tabs)


# ---------------------------------------------------------------------------
# Interaction parity: focus highlight, Enter -> detail modal, key bindings
# ---------------------------------------------------------------------------

def _card(app, lane_name, slug):
    """The mounted :class:`dashboard.TaskCard` for ``slug`` in ``lane_name``."""
    lane = app.query_one("#lane-%s" % lane_name, dashboard.Lane)
    return next(c for c in lane.query(dashboard.TaskCard)
               if c.member["slug"] == slug)


class InteractionTest(unittest.IsolatedAsyncioTestCase):
    async def test_focused_card_shows_focused_state(self):
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test() as pilot:
            driver_card = _card(app, "building", "driver")
            driver_card.focus()
            await pilot.pause()
            self.assertTrue(driver_card.has_focus)
            # An unfocused card in another lane stays unfocused.
            rdy_card = _card(app, "ready", "rdy")
            self.assertFalse(rdy_card.has_focus)

    async def test_enter_on_focused_card_pushes_member_detail_modal(self):
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test() as pilot:
            driver_card = _card(app, "building", "driver")
            driver_card.focus()
            await pilot.pause()
            await pilot.press("enter")
            self.assertIsInstance(app.screen, ModalScreen)
            self.assertEqual(app.screen.member["slug"], "driver")

    async def test_group_toggle_and_quit_bindings_are_registered(self):
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test():
            keys = set(app.screen.active_bindings.keys())
            self.assertIn("q", keys)
            self.assertIn("g", keys)


# ---------------------------------------------------------------------------
# One-row task rows: risk glyphs, live stage, shipped check, and row CSS
# ---------------------------------------------------------------------------

def _bare_card(risk, state="ready", entry=None, search_query=""):
    """Construct a bare :class:`TaskCard` for exercising ``_card_text`` —
    ``risk`` omitted (``None``) drops the ``risk`` key entirely."""
    member = {"slug": "sl", "state": state, "actions": []}
    if risk is not None:
        member["risk"] = risk
    return dashboard.TaskCard("ep", member, entry or {}, "active",
                              search_query=search_query)


class TaskCardRowTest(unittest.TestCase):
    """One-row task rows carry a risk-coloured ``●`` glyph and the slug, the
    live stage while driving, and a subtle ``✓`` in the shipped lane — the
    glyph/text form and the stripped-down row CSS (delivery-dashboard
    board-tui / board-shipd-theme spec)."""

    def test_high_risk_glyph(self):
        self.assertEqual(_bare_card("high")._card_text(),
                         "[$risk-high]●[/] sl")

    def test_medium_risk_glyph(self):
        self.assertEqual(_bare_card("medium")._card_text(),
                         "[$risk-medium]●[/] sl")

    def test_low_risk_glyph(self):
        self.assertEqual(_bare_card("low")._card_text(), "[$risk-low]●[/] sl")

    def test_missing_risk_glyph_is_muted(self):
        self.assertEqual(_bare_card(None)._card_text(), "[$fg-muted]●[/] sl")

    def test_unknown_risk_glyph_is_muted(self):
        self.assertEqual(_bare_card("bogus")._card_text(),
                         "[$fg-muted]●[/] sl")

    def test_driving_row_appends_stage_in_muted_tier(self):
        card = _bare_card("low", state="active",
                          entry={"state": "driving", "stage": "build"})
        self.assertEqual(card._card_text(),
                         "[$risk-low]●[/] sl[$fg-muted] · build[/]")

    def test_shipped_row_renders_the_dim_check_and_no_risk_glyph(self):
        card = _bare_card("high", state="archived")
        self.assertEqual(card._card_text(), "[$fg-subtle]✓[/] sl")
        self.assertNotIn("●", card._card_text())

    def test_active_query_still_wraps_the_matched_slug_span(self):
        card = _bare_card("high", search_query="sl")
        text = card._card_text()
        self.assertIn("[$accent]", text)
        self.assertIn("[$risk-high]●[/]", text)

    def test_rejected_row_renders_the_warning_glyph_and_state_label(self):
        card = _bare_card("high", state="active",
                          entry={"state": "rejected", "reason": "bad"})
        self.assertEqual(card._card_text(),
                         "[$text-error]⚠[/] sl[$fg-muted] · rejected[/]")

    def test_needs_human_row_renders_the_stop_glyph_and_state_label(self):
        card = _bare_card("high", state="active",
                          entry={"state": "needs-human"})
        self.assertEqual(card._card_text(),
                         "[$text-error]⛔[/] sl[$fg-muted] · needs-human[/]")

    def test_stale_row_renders_the_dagger_glyph_and_death_age(self):
        card = _bare_card("low", state="active",
                          entry={"state": "driving", "stage": "died 8h ago",
                                "stale": True})
        self.assertEqual(
            card._card_text(),
            "[$text-error]†[/] sl[$fg-muted] · stale (died 8h ago)[/]")

    def test_drafted_row_renders_the_info_glyph_in_the_accent_tier(self):
        # A drafted member (delivery-dashboard board-drafted-member spec) is
        # informational, not parked: its `◇` takes the accent tier, never the
        # error colour, even though its change is already archived.
        card = _bare_card("high", state="archived",
                          entry={"state": "drafted"})
        self.assertEqual(card._card_text(),
                         "[$accent]◇[/] sl[$fg-muted] · drafted[/]")
        self.assertNotIn("[$text-error]", card._card_text())
        # The modal's matching state chip has an accent-tier class to wear.
        self.assertIn(".badge-accent", dashboard.BoardApp.CSS)

    def test_live_build_row_appends_the_build_stage_in_muted_tier(self):
        card = _bare_card("low", state="archived")
        card.member["build_heartbeat"] = {
            "slug": "sl", "kind": "build", "state": "running",
            "stage": "review", "updated_at": time.time()}
        self.assertEqual(card._card_text(),
                         "[$risk-low]●[/] sl[$fg-muted] · review[/]")

    def test_row_css_drops_accent_bars_and_margin_adds_height_one(self):
        css = dashboard.BoardApp.CSS
        block = re.search(r"\bTaskCard\s*\{[^}]*\}", css).group(0)
        self.assertIn("height: 1", block)
        self.assertNotIn("border-left", block)
        self.assertNotIn("margin", block)
        # No per-risk classes survive anywhere in the widget CSS.
        self.assertIsNone(re.search(r"TaskCard\.risk-", css))
        self.assertIsNone(re.search(r"\.risk-(low|medium|high)\b", css))
        # The focus highlight is retained.
        self.assertIn("TaskCard:focus", css)


class TaskCardRowMountedTest(unittest.IsolatedAsyncioTestCase):
    async def test_high_risk_card_markup_resolves_when_mounted(self):
        # The custom `$risk-*` theme variables must resolve in Content markup
        # the same way the `[$text-error]✗` stall marker already does —
        # rendering a mounted high-risk card raises nothing and paints the
        # glyph.
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test():
            lane = app.query_one("#lane-unplanned", dashboard.Lane)
            card = next(c for c in lane.query(dashboard.TaskCard)
                        if c.member["slug"] == "fresh")
            self.assertEqual(card.member["risk"], "high")
            rendered = str(card.render())
            self.assertIn("●", rendered)
            self.assertIn("fresh", rendered)


# ---------------------------------------------------------------------------
# Tinted per-lane header bands
# ---------------------------------------------------------------------------

class LaneHeaderBandTest(unittest.IsolatedAsyncioTestCase):
    """Each lane carries a one-row tinted header band (a ``.lane-header``
    Static) coloured through its ``$lane-<name>`` theme variable, replacing
    the former border title (delivery-dashboard board-tui spec)."""

    async def test_each_lane_carries_a_lane_header_static_named_for_the_lane(
            self):
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test():
            for name in _LANE_NAMES:
                lane = app.query_one("#lane-%s" % name, dashboard.Lane)
                headers = list(lane.query(".lane-header"))
                self.assertEqual(len(headers), 1)
                self.assertIsInstance(headers[0], dashboard.Static)
                self.assertIn(name.upper(), str(headers[0].render()))

    async def test_lane_border_title_is_no_longer_set(self):
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test():
            for name in _LANE_NAMES:
                lane = app.query_one("#lane-%s" % name, dashboard.Lane)
                self.assertIsNone(lane.border_title)

    def test_css_defines_a_docked_lane_header_band(self):
        css = dashboard.BoardApp.CSS
        block = re.search(r"\.lane-header\s*\{[^}]*\}", css).group(0)
        self.assertIn("dock: top", block)

    def test_css_tints_each_lane_header_with_its_lane_variable(self):
        css = dashboard.BoardApp.CSS
        for name in _LANE_NAMES:
            block = re.search(
                r"#lane-%s\s+\.lane-header\s*\{[^}]*\}" % name, css)
            self.assertIsNotNone(block, "no #lane-%s .lane-header block" % name)
            body = block.group(0)
            self.assertIn("background: $lane-%s" % name, body)
            self.assertIn("color: $lane-%s" % name, body)

    async def test_lane_header_survives_a_content_repaint(self):
        boards = [_kanban_board()]
        app = dashboard.BoardApp(root="/x", board_fn=lambda: boards[-1])
        async with app.run_test() as pilot:
            lane = app.query_one("#lane-building", dashboard.Lane)
            header_before = lane.query_one(".lane-header", dashboard.Static)
            card_ids_before = {id(c) for c in lane.query(dashboard.TaskCard)}
            self.assertTrue(card_ids_before)
            # Change the building lane's content: ship its driving member so
            # it leaves the lane, flipping the lane's signature and forcing a
            # repaint that remounts the lane's cards.
            changed = _kanban_board()
            changed["epics"][0]["heartbeat"]["roster"][0]["state"] = "shipped"
            boards.append(changed)
            await app.refresh_board()
            await pilot.pause()
            header_after = lane.query_one(".lane-header", dashboard.Static)
            self.assertIs(header_after, header_before)
            card_ids_after = {id(c) for c in lane.query(dashboard.TaskCard)}
            self.assertNotEqual(card_ids_before, card_ids_after)


# ---------------------------------------------------------------------------
# Per-lane empty-state texts
# ---------------------------------------------------------------------------

class LaneEmptyStateTest(unittest.IsolatedAsyncioTestCase):
    """A lane mounting no member rows — an empty board region or a search
    that filters every member out — shows its own per-lane empty-state text
    (delivery-dashboard board-tui spec). ``_kanban_board`` leaves the
    ``review`` and ``shipped`` lanes empty."""

    async def test_empty_lane_mounts_its_empty_state_text(self):
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test():
            for name in ("review", "shipped"):
                lane = app.query_one("#lane-%s" % name, dashboard.Lane)
                empties = list(lane.query(".lane-empty"))
                self.assertEqual(len(empties), 1)
                self.assertIn(dashboard.LANE_EMPTY_TEXTS[name],
                              str(empties[0].render()))
                self.assertFalse(list(lane.query(dashboard.TaskCard)))

    async def test_empty_state_replaced_when_a_member_maps_into_the_lane(self):
        boards = [_kanban_board()]
        app = dashboard.BoardApp(root="/x", board_fn=lambda: boards[-1])
        async with app.run_test() as pilot:
            review = app.query_one("#lane-review", dashboard.Lane)
            self.assertEqual(len(list(review.query(".lane-empty"))), 1)
            # Move the driving member into its review stage → the review lane.
            changed = _kanban_board()
            changed["epics"][0]["heartbeat"]["roster"][0]["stage"] = "review"
            boards.append(changed)
            await app.refresh_board()
            await pilot.pause()
            self.assertFalse(list(review.query(".lane-empty")))
            self.assertTrue(list(review.query(dashboard.TaskCard)))

    async def test_search_matching_no_member_shows_the_empty_text(self):
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test() as pilot:
            inp = app.query_one("#board-search-input", dashboard.SearchInput)
            inp.value = "zzznomatch"
            await pilot.pause()
            ready = app.query_one("#lane-ready", dashboard.Lane)
            self.assertFalse(list(ready.query(dashboard.TaskCard)))
            empties = list(ready.query(".lane-empty"))
            self.assertEqual(len(empties), 1)
            self.assertIn(dashboard.LANE_EMPTY_TEXTS["ready"],
                          str(empties[0].render()))


# ---------------------------------------------------------------------------
# Collapse parity: shipped-lane per-epic groups
# ---------------------------------------------------------------------------

def _two_epic_board():
    """A board with one initiative holding two epics, each with its own
    member — for exercising per-epic grouping where a sibling epic's group
    must stay expanded while another folds."""
    ep1 = {
        "slug": "ep1", "status": "active", "theme": "obs",
        "initiative": {"slug": "init", "status": "active"},
        "members": [
            {"slug": "m1", "description": "d", "risk": "low",
             "state": "ready", "location": "/x", "actions": ["run"],
             "session_id": None},
        ],
        "heartbeat": None, "report": None,
    }
    ep2 = {
        "slug": "ep2", "status": "active", "theme": "perf",
        "initiative": {"slug": "init", "status": "active"},
        "members": [
            {"slug": "m2", "description": "d", "risk": "low",
             "state": "ready", "location": "/x", "actions": ["run"],
             "session_id": None},
        ],
        "heartbeat": None, "report": None,
    }
    return {
        "root": "/x", "generated_at": time.time(),
        "epics": [ep1, ep2],
        "groups": [{"initiative": {"slug": "init", "status": "active"},
                    "epics": [ep1, ep2]}],
    }


async def _open_epic_detail(pilot, app, lane_name, slug):
    """Open an epic group header's detail modal (delivery-dashboard board-
    epic-grouping spec): click its title off the leading collapse-arrow cell
    (``Offset(6, 0)`` clears the arrow+pad at columns 0-1) and return the
    pushed screen. The pause lets layout settle so the title's region is
    final before the click resolves its coordinates."""
    group = app.query_one(
        "#epic-group-%s-%s" % (lane_name, slug), Collapsible)
    title = group.query_one("CollapsibleTitle")
    await pilot.pause()
    await pilot.click(title, offset=Offset(6, 0))
    return app.screen


def _initiative_grouped_board():
    """Three epics with one ready member each in the READY lane — ep1/ep2
    share initiative ``init``, ep3 carries none — for exercising initiative-
    mode grouping (delivery-dashboard board-epic-grouping spec)."""
    def _epic(slug, initiative):
        return {
            "slug": slug, "status": "active", "theme": None,
            "initiative": initiative,
            "members": [{"slug": "m-%s" % slug, "description": "d",
                         "risk": "low", "state": "ready", "location": "/x",
                         "actions": ["run"], "session_id": None}],
            "heartbeat": None, "report": None,
        }
    init = {"slug": "init", "status": "active"}
    ep1 = _epic("ep1", init)
    ep2 = _epic("ep2", init)
    ep3 = _epic("ep3", None)
    return {
        "root": "/x", "generated_at": time.time(),
        "epics": [ep1, ep2, ep3],
        "groups": [{"initiative": init, "epics": [ep1, ep2]},
                   {"initiative": None, "epics": [ep3]}],
    }


def _stalled_board(status="active"):
    """A board with one epic whose run has *finished* while a member sits
    parked ``needs-human`` — a stalled epic, for exercising the group-header
    ✗ marker and the epic-detail warning/Retry block. The parked member lands
    in the ``building`` lane (``_member_column``)."""
    epic = {
        "slug": "ep1", "status": status, "theme": "obs", "initiative": None,
        "members": [
            {"slug": "m1", "description": "d", "risk": "high",
             "state": "active", "location": "/x/.worktrees/m1",
             "actions": [], "session_id": None},
        ],
        "heartbeat": {
            "epic": "ep1", "state": "finished", "seq": 2,
            "updated_at": time.time(),
            "roster": [{"slug": "m1", "state": "needs-human",
                        "stage": "worktree",
                        "reason": "worktree creation failed"}],
        },
        "report": None,
    }
    return {
        "root": "/x", "generated_at": time.time(), "epics": [epic],
        "groups": [{"initiative": None, "epics": [epic]}],
    }


def _shipped_board():
    """A board with two epics of different status, each holding one shipped
    member and one ready member — for exercising the SHIPPED lane's per-epic
    collapsible grouping (the ``ready`` members stay flat in their own lane)."""
    es1 = {
        "slug": "es1", "status": "complete", "theme": None,
        "initiative": None,
        "members": [
            {"slug": "shipped1", "description": "d", "risk": "low",
             "state": "archived", "location": "/x", "actions": ["open"],
             "session_id": "sess-1"},
            {"slug": "rdy1", "description": "d", "risk": "low",
             "state": "ready", "location": "/x", "actions": ["run"],
             "session_id": None},
        ],
        "heartbeat": None, "report": None,
    }
    es2 = {
        "slug": "es2", "status": "active", "theme": None,
        "initiative": None,
        "members": [
            {"slug": "shipped2", "description": "d", "risk": "low",
             "state": "archived", "location": "/x", "actions": [],
             "session_id": None},
        ],
        "heartbeat": None, "report": None,
    }
    return {
        "root": "/x", "generated_at": time.time(),
        "epics": [es1, es2],
        "groups": [{"initiative": None, "epics": [es1, es2]}],
    }


def _one_epic_two_ready_board():
    """One epic with two ``ready`` members — both land in the READY lane, so
    its single group header carries the per-lane count 2."""
    epic = {
        "slug": "ep", "status": "active", "theme": "obs",
        "initiative": {"slug": "init", "status": "active"},
        "members": [
            {"slug": "m1", "description": "d", "risk": "low",
             "state": "ready", "location": "/x", "actions": ["run"],
             "session_id": None},
            {"slug": "m2", "description": "d", "risk": "high",
             "state": "ready", "location": "/x", "actions": ["run"],
             "session_id": None},
        ],
        "heartbeat": None, "report": None,
    }
    return {
        "root": "/x", "generated_at": time.time(), "epics": [epic],
        "groups": [{"initiative": {"slug": "init", "status": "active"},
                    "epics": [epic]}],
    }


def _worktree_hosted_epic_board():
    """One epic hosted under a worktree root — its ``location`` is not the
    board root, so its group header must carry the ``[worktree]`` marker."""
    board = _one_epic_two_ready_board()
    board["epics"][0]["location"] = "/x/.worktrees/epic-ep"
    return board


class WorktreeEpicGroupHeaderTest(unittest.IsolatedAsyncioTestCase):
    """The TUI epic group header marks a worktree-hosted epic (delivery-
    dashboard board-aggregation): the ``[worktree]`` marker is *painted*, not
    swallowed as content markup, and a root-hosted epic carries none.

    Written test-first; expected to FAIL until the marker lands in
    ``dashboard.py`` (task 3.4)."""

    async def test_group_header_paints_the_worktree_marker(self):
        app = dashboard.BoardApp(root="/x",
                                 board_fn=_worktree_hosted_epic_board)
        async with app.run_test(size=(200, 24)) as pilot:
            await pilot.pause()
            group = app.query_one("#epic-group-ready-ep", Collapsible)
            title = group.query_one("CollapsibleTitle")
            self.assertIn("[worktree]", _painted_line(app, title).text)

    async def test_root_hosted_group_header_has_no_marker(self):
        app = dashboard.BoardApp(root="/x", board_fn=_one_epic_two_ready_board)
        async with app.run_test(size=(200, 24)) as pilot:
            await pilot.pause()
            group = app.query_one("#epic-group-ready-ep", Collapsible)
            title = group.query_one("CollapsibleTitle")
            self.assertNotIn("worktree", _painted_line(app, title).text)


_OVERLONG_EPIC_SLUG = (
    "a-very-long-epic-slug-that-is-wide-enough-to-overflow-any-narrow-lane")


def _overlong_title_board():
    """A board whose single epic carries a slug long enough (``~68`` chars)
    that its rendered header title overflows a narrow lane — the regression
    fixture for the header's own-space ellipsis (delivery-dashboard
    board-epic-grouping spec: "An overlong title ellipsizes inside its own
    space"). No menu control is involved any more — the title alone must
    absorb the overflow."""
    epic = {
        "slug": _OVERLONG_EPIC_SLUG, "status": "active", "theme": None,
        "initiative": None,
        "members": [
            {"slug": "m1", "description": "d", "risk": "low",
             "state": "unplanned", "location": "/x", "actions": [],
             "session_id": None},
        ],
        "heartbeat": None, "report": None,
    }
    return {
        "root": "/x", "generated_at": time.time(),
        "epics": [epic],
        "groups": [{"initiative": None, "epics": [epic]}],
    }


class OneRowEpicGroupHeaderTest(unittest.IsolatedAsyncioTestCase):
    """The epic group header is a single terminal row — no top-border row
    above the title, no trailing padding row below the contents — and its
    title carries the count of that epic's cards in the lane (delivery-
    dashboard board-epic-grouping spec)."""

    def test_epic_group_css_removes_the_top_border_and_bottom_padding(self):
        css = dashboard.BoardApp.CSS
        block = re.search(r"\.epic-group\s*\{[^}]*\}", css).group(0)
        self.assertIn("border-top: none", block)
        self.assertIn("padding-bottom: 0", block)
        contents = re.search(r"\.epic-group\s+Contents\s*\{[^}]*\}", css)
        self.assertIsNotNone(contents, "no .epic-group Contents block")
        self.assertIn("padding: 0", contents.group(0))

    async def test_count_renders_as_a_muted_title_suffix(self):
        app = dashboard.BoardApp(root="/x", board_fn=_one_epic_two_ready_board)
        async with app.run_test(size=(200, 24)) as pilot:
            await pilot.pause()
            group = app.query_one("#epic-group-ready-ep", Collapsible)
            title = group.query_one("CollapsibleTitle")
            # The per-lane card count is a muted ` (N)` suffix inside the title,
            # not a separate trailing element (delivery-dashboard board-epic-
            # grouping spec) — no `.epic-count` Static survives anywhere.
            self.assertTrue(group.title.endswith("[$fg-muted](2)[/]"))
            self.assertFalse(app.query(".epic-count"))
            strip = _painted_line(app, title)
            self.assertIn("(2)", strip.text)
            fg_muted = Color.parse(app.get_css_variables()["fg-muted"]).rgb
            self.assertEqual(_segment_color(strip, "(2)"), fg_muted)

    async def test_member_cards_keep_the_lane_content_width(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test(size=(200, 24)):
            group = app.query_one("#epic-group-ready-ep1", Collapsible)
            lane = app.query_one("#lane-ready", dashboard.Lane)
            # The group's collapsible box spans the lane's full scrollable
            # content width — no header control narrows it now that the
            # header carries nothing but the collapse arrow and the title
            # (delivery-dashboard board-epic-grouping spec).
            self.assertEqual(
                group.region.width, lane.scrollable_content_region.width)

    async def test_overlong_title_ellipsizes_inside_its_own_space(self):
        # A narrow terminal (60 cols across 5 lanes) forces the title well
        # below the ~68-char slug's natural width — with no menu control
        # left to blame, the title alone must absorb the overflow, in both
        # the expanded and collapsed states (delivery-dashboard board-epic-
        # grouping spec).
        app = dashboard.BoardApp(root="/x", board_fn=_overlong_title_board)
        async with app.run_test(size=(60, 24)) as pilot:
            await pilot.pause()
            lane = app.query_one("#lane-unplanned", dashboard.Lane)
            group = app.query_one(".epic-group", Collapsible)
            title = group.query_one("CollapsibleTitle")
            for collapsed in (False, True):
                group.collapsed = collapsed
                await pilot.pause()
                strip = _painted_line(app, title)
                self.assertIn("…", strip.text)
                # The title never overflows past the lane's own scrollable
                # content bounds — it ellipsizes inside its own space rather
                # than spilling past the lane, whether expanded or collapsed.
                self.assertLessEqual(
                    title.content_region.right,
                    lane.scrollable_content_region.right)
                self.assertGreaterEqual(
                    title.region.x, lane.scrollable_content_region.x)


class EpicGroupingTest(unittest.IsolatedAsyncioTestCase):
    """Per-epic grouping generalises across every lane (delivery-dashboard
    board-epic-grouping spec) — replacing the old shipped-lane-only
    Collapsible grouping. ``_two_epic_board`` puts both epics' members in
    the ``ready`` lane (each ``state: ready``, no live heartbeat)."""

    async def test_two_epics_in_one_lane_render_two_collapsible_groups(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test():
            lane = app.query_one("#lane-ready", dashboard.Lane)
            groups = list(lane.query(Collapsible))
            self.assertEqual(len(groups), 2)
            ep1_group = next(g for g in groups if "ep1" in g.title)
            ep2_group = next(g for g in groups if "ep2" in g.title)
            self.assertEqual(
                [c.member["slug"]
                 for c in ep1_group.query(dashboard.TaskCard)], ["m1"])
            self.assertEqual(
                [c.member["slug"]
                 for c in ep2_group.query(dashboard.TaskCard)], ["m2"])

    async def test_group_header_names_epic_status_and_initiative(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test():
            lane = app.query_one("#lane-ready", dashboard.Lane)
            ep1_group = next(g for g in lane.query(Collapsible)
                             if "ep1" in g.title)
            self.assertIn("active", ep1_group.title)
            self.assertIn("init", ep1_group.title)

    async def test_stalled_epic_group_header_carries_the_marker(self):
        app = dashboard.BoardApp(root="/x", board_fn=_stalled_board)
        async with app.run_test():
            group = app.query_one("#epic-group-building-ep1", Collapsible)
            self.assertIn("✗", group.title)
            self.assertIn("[$text-error]", group.title)

    async def test_non_stalled_epic_group_header_has_no_marker(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test():
            lane = app.query_one("#lane-ready", dashboard.Lane)
            ep1_group = next(g for g in lane.query(Collapsible)
                             if "ep1" in g.title)
            self.assertNotIn("✗", ep1_group.title)

    async def test_none_mode_renders_flat_no_collapsible(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test() as pilot:
            await pilot.press("g")  # epic -> initiative
            await pilot.press("g")  # initiative -> none
            self.assertEqual(app.group_mode, "none")
            lane = app.query_one("#lane-ready", dashboard.Lane)
            self.assertEqual(list(lane.query(Collapsible)), [])
            slugs = {c.member["slug"] for c in lane.query(dashboard.TaskCard)}
            self.assertEqual(slugs, {"m1", "m2"})

    async def test_collapsing_one_epic_group_hides_only_its_cards(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test() as pilot:
            ep1_group = app.query_one("#epic-group-ready-ep1", Collapsible)
            ep2_group = app.query_one("#epic-group-ready-ep2", Collapsible)
            ep1_group.collapsed = True
            await pilot.pause()
            ep1_contents = ep1_group.query_one(Collapsible.Contents)
            ep2_contents = ep2_group.query_one(Collapsible.Contents)
            self.assertFalse(ep1_contents.display)
            self.assertTrue(ep2_contents.display)
            self.assertFalse(ep2_group.collapsed)


class EpicHeaderClickRoutingTest(unittest.IsolatedAsyncioTestCase):
    """The epic group header carries no menu control — the title itself
    routes the click (delivery-dashboard board-epic-grouping spec): the
    leading collapse-arrow cell toggles the group and opens nothing, while a
    click anywhere else on the title opens the epic-detail modal without
    touching the collapsed state."""

    async def test_clicking_the_title_off_the_arrow_opens_epic_detail(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test(size=(200, 24)) as pilot:
            group = app.query_one("#epic-group-ready-ep1", Collapsible)
            title = group.query_one("CollapsibleTitle")
            self.assertFalse(group.collapsed)
            await pilot.pause()
            await pilot.click(title, offset=Offset(6, 0))
            await pilot.pause()
            self.assertIsInstance(app.screen, dashboard.EpicDetailScreen)
            self.assertEqual(app.screen.epic_slug, "ep1")
            self.assertFalse(group.collapsed)

    async def test_clicking_the_arrow_cell_toggles_and_opens_nothing(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test(size=(200, 24)) as pilot:
            group = app.query_one("#epic-group-ready-ep1", Collapsible)
            title = group.query_one("CollapsibleTitle")
            self.assertFalse(group.collapsed)
            await pilot.pause()
            await pilot.click(title, offset=Offset(1, 0))
            await pilot.pause()
            self.assertTrue(group.collapsed)
            self.assertNotIsInstance(app.screen, dashboard.EpicDetailScreen)

    async def test_epic_header_carries_no_menu_button(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test(size=(200, 24)):
            self.assertFalse(list(app.query(".epic-menu-button")))


class EpicDetailRunControlGateTest(unittest.IsolatedAsyncioTestCase):
    """The epic-detail modal's **Run epic** control — its new home now that
    the header ``≡`` menu is gone — is gated on the epic being **runnable**:
    status ``ready``/``active`` with at least one ``unplanned``/``ready``
    member (delivery-dashboard board-epic-grouping spec,
    ``epic_is_runnable``). A non-runnable epic's modal offers no Run control
    at all, so it can never be run from the board."""

    async def test_runnable_epic_detail_offers_run_that_pushes_confirm(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test(size=(120, 24)) as pilot:
            app.push_screen(dashboard.EpicDetailScreen("ep1"))
            await pilot.pause()
            run_button = app.screen.query_one("#epic-run", Button)
            await pilot.click(run_button)
            self.assertIsInstance(app.screen, dashboard.EpicRunConfirmScreen)
            self.assertEqual(app.screen.epic_slug, "ep1")

    async def test_non_runnable_epic_detail_has_no_run_control(self):
        # es1 is `complete` (status guard fails despite a `ready` member);
        # neither it nor es2 (an `active` epic whose only member is
        # `archived` — no drivable member) offers a Run control.
        app = dashboard.BoardApp(root="/x", board_fn=_shipped_board)
        async with app.run_test(size=(120, 24)) as pilot:
            app.push_screen(dashboard.EpicDetailScreen("es1"))
            await pilot.pause()
            self.assertFalse(list(app.screen.query("#epic-run")))


def _long_slug_shipped_board():
    """One epic whose single archived member carries a slug far wider than a
    lane card at ``(120, 24)`` — the fixture for the blank-card ellipsis guard
    (delivery-dashboard lane-row-presentation spec: "A long slug ellipsizes
    instead of blanking"). ``archived`` lands it in the SHIPPED lane, so the
    card carries the ``✓`` glyph before the slug."""
    ep = {
        "slug": "ep", "status": "active", "theme": None, "initiative": None,
        "members": [
            {"slug": "a-long-shipped-slug-that-overflows", "description": "d",
             "risk": "low", "state": "archived", "location": "/x",
             "actions": ["open"], "session_id": None}],
        "heartbeat": None, "report": None,
    }
    return {
        "root": "/x", "generated_at": time.time(), "epics": [ep],
        "groups": [{"initiative": None, "epics": [ep]}],
    }


class LaneRowPresentationTest(unittest.IsolatedAsyncioTestCase):
    """The lane rows' chrome polish (delivery-dashboard lane-row-presentation
    spec): each group's panel band reaches its divider with no lane-
    ``$surface`` gap after the last card, and an overlong card slug
    ellipsizes on one painted line instead of wrapping onto a cropped blank
    row."""

    async def test_group_row_band_reaches_the_divider(self):
        app = dashboard.BoardApp(root="/x", board_fn=_shipped_board)
        async with app.run_test(size=(120, 24)) as pilot:
            await pilot.pause()
            panel = Color.parse(app.get_css_variables()["panel"]).rgb
            group = app.query_one("#epic-group-shipped-es1", Collapsible)
            row = group.parent
            # The full row box carries the panel band down to the divider — no
            # lane `$surface` gap between the last card and the border.
            self.assertEqual(row.styles.background.rgb, panel)
            self.assertEqual(row.styles.background.a, 1.0)
            self.assertGreaterEqual(row.region.height, group.region.height)

    async def test_overlong_card_slug_ellipsizes_not_blank(self):
        app = dashboard.BoardApp(root="/x", board_fn=_long_slug_shipped_board)
        async with app.run_test(size=(120, 24)) as pilot:
            await pilot.pause()
            card = list(app.query(dashboard.TaskCard))[0]
            strip = _painted_line(app, card)
            visible = strip.text.strip()
            slug = card.member["slug"]
            # The painted line is the ✓ glyph, the slug's visible prefix, and
            # an ellipsis — never a bare glyph with the slug wrapped onto a
            # cropped second line the height-1 card discards.
            self.assertTrue(visible.startswith("✓ "))
            self.assertTrue(visible.endswith("…"))
            self.assertIn(slug[:4], strip.text)


def _epic_detail_board(root, slug, status="active", theme=None,
                       initiative=None, members=(), heartbeat=None):
    """A board holding one epic with the given ``members`` — each
    ``(slug, risk, state)`` triple — for exercising the epic-detail modal.
    ``root`` is a real directory (not ``"/x"``) so :func:`dashboard.
    epic_markdown` can resolve an on-disk ``epics/<slug>/epic.md`` planted
    alongside it via ``_make_epic``. An optional ``heartbeat`` dict lets a
    caller exercise the stalled-epic warning/Retry block."""
    epic = {
        "slug": slug, "status": status, "theme": theme,
        "initiative": initiative,
        "members": [{"slug": mslug, "description": "d", "risk": risk,
                    "state": state, "location": root, "actions": [],
                    "session_id": None}
                   for mslug, risk, state in members],
        "heartbeat": heartbeat, "report": None,
    }
    return {"root": root, "generated_at": time.time(), "epics": [epic],
            "groups": [{"initiative": initiative, "epics": [epic]}]}


class EpicDetailModalTest(DashboardTestBase, unittest.IsolatedAsyncioTestCase):
    """The epic-detail modal a click on the epic group header's title (off
    the collapse arrow) pushes (delivery-dashboard board-epic-grouping
    spec): a large centred ``Container`` naming the epic's
    slug/status/theme/initiative, a list of its member specs (each with
    state and risk), and its ``epic.md`` overview rendered as ``Markdown``
    — dismissed by ``Escape`` or a click on the ``✕`` close control, without
    disturbing the group's collapsed state."""

    async def _open_detail(self, pilot, lane_name, slug):
        # Reached by clicking the header title off the collapse arrow
        # (delivery-dashboard board-epic-grouping spec).
        await _open_epic_detail(pilot, self.app_, lane_name, slug)

    async def test_choosing_view_pushes_epic_detail_no_collapse_change(
            self):
        _make_epic(self.root, "ep1", [("m1", "d", "low")])
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _epic_detail_board(
                self.root, "ep1", members=[("m1", "low", "ready")]))
        self.app_ = app
        async with app.run_test(size=(120, 24)) as pilot:
            group = app.query_one("#epic-group-ready-ep1", Collapsible)
            self.assertFalse(group.collapsed)
            await self._open_detail(pilot, "ready", "ep1")
            self.assertIsInstance(app.screen, dashboard.EpicDetailScreen)
            self.assertFalse(group.collapsed)

    async def test_modal_names_epic_and_lists_members_with_state_and_risk(
            self):
        _make_epic(self.root, "ep1", [("m1", "d", "low")])
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _epic_detail_board(
                self.root, "ep1", status="active",
                members=[("m1", "high", "ready"),
                        ("m2", "low", "unplanned")]))
        self.app_ = app
        async with app.run_test(size=(120, 24)) as pilot:
            await self._open_detail(pilot, "ready", "ep1")
            # Render each Static the way Textual actually paints it (not
            # its raw pre-render content) so a bracketed value swallowed
            # as Rich markup — e.g. "[low]" parsed as a style tag — would
            # be caught here even though it is still present verbatim in
            # the unrendered string.
            rendered = "\n".join(
                str(w.render()) for w in app.screen.query(dashboard.Static))
            self.assertIn("ep1", rendered)
            # The status now rides a badge chip below the title bar
            # (board-modal-chrome), no longer bracketed in the title.
            self.assertIn("active", rendered)
            self.assertIn("m1", rendered)
            self.assertIn("[high]", rendered)
            self.assertIn("ready", rendered)
            self.assertIn("m2", rendered)
            self.assertIn("[low]", rendered)
            self.assertIn("unplanned", rendered)

    async def test_markdown_widget_present_when_epic_md_exists(self):
        _make_epic(self.root, "ep1", [("m1", "d", "low")])
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _epic_detail_board(
                self.root, "ep1", members=[("m1", "low", "ready")]))
        self.app_ = app
        async with app.run_test(size=(120, 24)) as pilot:
            await self._open_detail(pilot, "ready", "ep1")
            self.assertTrue(list(app.screen.query(dashboard.Markdown)))

    async def test_close_button_dismisses_the_modal(self):
        _make_epic(self.root, "ep1", [("m1", "d", "low")])
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _epic_detail_board(
                self.root, "ep1", members=[("m1", "low", "ready")]))
        self.app_ = app
        async with app.run_test(size=(120, 24)) as pilot:
            await self._open_detail(pilot, "ready", "ep1")
            self.assertIsInstance(app.screen, dashboard.EpicDetailScreen)
            close_button = app.screen.query_one(
                "#epic-detail-close", Button)
            await pilot.click(close_button)
            self.assertNotIsInstance(app.screen, dashboard.EpicDetailScreen)

    async def test_escape_dismisses_the_modal(self):
        _make_epic(self.root, "ep1", [("m1", "d", "low")])
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _epic_detail_board(
                self.root, "ep1", members=[("m1", "low", "ready")]))
        self.app_ = app
        async with app.run_test(size=(120, 24)) as pilot:
            await self._open_detail(pilot, "ready", "ep1")
            self.assertIsInstance(app.screen, dashboard.EpicDetailScreen)
            await pilot.press("escape")
            self.assertNotIsInstance(app.screen, dashboard.EpicDetailScreen)


class WorktreeEpicDetailOverviewTest(DashboardTestBase,
                                     unittest.IsolatedAsyncioTestCase):
    """The epic-detail modal reads its overview markdown from the epic's own
    hosting root (delivery-dashboard board-aggregation), so an epic authored
    inside a ``.worktrees/<name>`` worktree renders its ``epic.md`` instead of
    the not-found notice.

    Written test-first; expected to FAIL until the call site passes
    ``epic["location"]`` (task 3.4)."""

    async def test_overview_renders_a_worktree_hosted_epic_markdown(self):
        wt = os.path.join(self.root, ".worktrees", "epic-ep1")
        _make_epic(wt, "ep1", [("m1", "d", "low")])
        board = _epic_detail_board(self.root, "ep1",
                                   members=[("m1", "low", "ready")])
        board["epics"][0]["location"] = os.path.abspath(wt)
        app = dashboard.BoardApp(root=self.root, board_fn=lambda: board)
        self.app_ = app
        async with app.run_test(size=(120, 24)) as pilot:
            await _open_epic_detail(pilot, app, "ready", "ep1")
            self.assertIsInstance(app.screen, dashboard.EpicDetailScreen)
            self.assertTrue(list(app.screen.query(dashboard.Markdown)))
            rendered = "\n".join(
                str(w.render()) for w in app.screen.query(dashboard.Static))
            self.assertNotIn("epic file not found", rendered)

    async def test_overview_still_reports_a_missing_epic_file(self):
        # No epic.md anywhere: the not-found notice, not a Markdown widget.
        board = _epic_detail_board(self.root, "ep1",
                                   members=[("m1", "low", "ready")])
        board["epics"][0]["location"] = os.path.abspath(self.root)
        app = dashboard.BoardApp(root=self.root, board_fn=lambda: board)
        self.app_ = app
        async with app.run_test(size=(120, 24)) as pilot:
            await _open_epic_detail(pilot, app, "ready", "ep1")
            self.assertFalse(list(app.screen.query(dashboard.Markdown)))


class CompactControlTest(DashboardTestBase, unittest.IsolatedAsyncioTestCase):
    """Every compact control renders exactly one row high (delivery-dashboard
    board-epic-grouping spec: the three modal close (``✕``) controls share
    the compact, button-evident chrome — no default three-row Button box)."""

    async def test_member_detail_close_is_one_row_high(self):
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _detail_board(self.root, "documented"))
        async with app.run_test(size=(120, 24)) as pilot:
            card = _find_card(app, "documented")
            card.focus()
            await pilot.pause()
            await pilot.press("enter")
            close = app.screen.query_one("#close-detail", Button)
            self.assertEqual(close.region.height, 1)
            self.assertEqual(close.region.width, 3)

    async def test_epic_detail_close_is_one_row_high(self):
        _make_epic(self.root, "ep1", [("m1", "d", "low")])
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _epic_detail_board(
                self.root, "ep1", members=[("m1", "low", "ready")]))
        async with app.run_test(size=(120, 24)) as pilot:
            await _open_epic_detail(pilot, app, "ready", "ep1")
            close = app.screen.query_one("#epic-detail-close", Button)
            self.assertEqual(close.region.height, 1)
            self.assertEqual(close.region.width, 3)

    async def test_epic_run_confirm_close_is_one_row_high(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test(size=(120, 24)) as pilot:
            await _open_epic_detail(pilot, app, "ready", "ep1")
            run_button = app.screen.query_one("#epic-run", Button)
            await pilot.click(run_button)
            close = app.screen.query_one("#epic-run-close", Button)
            self.assertEqual(close.region.height, 1)
            self.assertEqual(close.region.width, 3)


class ModalChromeTest(DashboardTestBase, unittest.IsolatedAsyncioTestCase):
    """The Shipd modal chrome the three board modals carry (delivery-dashboard
    board-modal-chrome spec): an accent title bar with the inline ``✕`` close,
    a badge meta row of theme-tinted chips, lane badges on epic member rows,
    and a one-row muted footer key-hint line per modal."""

    SPEC_HINTS = "⇥ tabs · j/k scroll · o editor · y copy · esc close"
    EPIC_HINTS = "j/k scroll · o editor · y copy · esc close"
    CONFIRM_HINTS = "esc close"

    def _push_member(self, app, entry=None, risk="high"):
        member = {"slug": "documented", "description": "d", "risk": risk,
                  "state": "ready", "location": self.root,
                  "actions": [], "session_id": None}
        app.push_screen(
            dashboard.MemberDetailScreen("ep", member, entry or {}, "active"))

    async def test_spec_detail_title_bar_carries_the_inline_close(self):
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _detail_board(self.root, "documented"))
        async with app.run_test(size=(120, 24)) as pilot:
            self._push_member(app)
            await pilot.pause()
            bar = app.screen.query_one(".modal-title-bar")
            self.assertIsInstance(bar.query_one("#close-detail", Button), Button)

    async def test_epic_detail_title_bar_carries_the_inline_close(self):
        _make_epic(self.root, "ep1", [("m1", "d", "low")])
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _epic_detail_board(
                self.root, "ep1", members=[("m1", "low", "ready")]))
        async with app.run_test(size=(120, 24)) as pilot:
            app.push_screen(dashboard.EpicDetailScreen("ep1"))
            await pilot.pause()
            bar = app.screen.query_one(".modal-title-bar")
            self.assertIsInstance(
                bar.query_one("#epic-detail-close", Button), Button)

    async def test_run_confirm_title_bar_carries_the_inline_close(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test(size=(120, 24)) as pilot:
            app.push_screen(dashboard.EpicRunConfirmScreen("ep1"))
            await pilot.pause()
            bar = app.screen.query_one(".modal-title-bar")
            self.assertIsInstance(
                bar.query_one("#epic-run-close", Button), Button)

    async def test_spec_detail_badge_row_while_driving(self):
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _detail_board(self.root, "documented"))
        async with app.run_test(size=(120, 24)) as pilot:
            self._push_member(app, entry={"slug": "documented",
                                          "state": "driving", "stage": "build"})
            await pilot.pause()
            # risk chip (member risk high), lane chip (driving/build → building),
            # and a muted live-stage chip naming the stage.
            self.assertTrue(app.screen.query(".badge-risk-high"))
            self.assertTrue(app.screen.query(".badge-lane-building"))
            muted = "\n".join(
                str(w.render()) for w in app.screen.query(".badge-muted"))
            self.assertIn("build", muted)

    async def test_unrated_member_badge_row_omits_the_risk_chip(self):
        # A member dict carrying no risk key renders no risk chip and no `?`
        # placeholder; its row's first chip is the lane chip (board-modal-chrome
        # "An unrated member's modal omits the risk chip" scenario).
        member = {"slug": "documented", "description": "d",
                  "state": "ready", "location": self.root,
                  "actions": [], "session_id": None}
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _detail_board(self.root, "documented"))
        async with app.run_test(size=(120, 24)) as pilot:
            app.push_screen(
                dashboard.MemberDetailScreen("ep", member, {}, "active"))
            await pilot.pause()
            badges = list(app.screen.query(".modal-badge-row .modal-badge"))
            self.assertFalse(
                app.screen.query(".badge-risk-high")
                or app.screen.query(".badge-risk-medium")
                or app.screen.query(".badge-risk-low"))
            self.assertFalse(
                any("?" in str(b.render()) for b in badges))
            self.assertIn("badge-lane-ready", badges[0].classes)

    async def test_epic_detail_badge_row_shows_status_theme_initiative(self):
        _make_epic(self.root, "ep1", [("m1", "d", "low")])
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _epic_detail_board(
                self.root, "ep1", status="active", theme="ux",
                initiative={"slug": "look-feel"},
                members=[("m1", "low", "ready")]))
        async with app.run_test(size=(120, 24)) as pilot:
            app.push_screen(dashboard.EpicDetailScreen("ep1"))
            await pilot.pause()
            chips = "\n".join(
                str(w.render()) for w in app.screen.query(".badge-muted"))
            self.assertIn("active", chips)
            self.assertIn("ux", chips)
            self.assertIn("look-feel", chips)

    async def test_epic_member_rows_carry_a_lane_badge(self):
        _make_epic(self.root, "ep1", [("m1", "d", "low")])
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _epic_detail_board(
                self.root, "ep1",
                members=[("m1", "high", "ready"), ("m2", "low", "unplanned")]))
        async with app.run_test(size=(120, 24)) as pilot:
            app.push_screen(dashboard.EpicDetailScreen("ep1"))
            await pilot.pause()
            rows = list(app.screen.query(dashboard.EpicMemberRow))
            self.assertEqual(len(rows), 2)
            for row in rows:
                lane = dashboard._member_column(row.member, row.entry)
                self.assertTrue(
                    row.query(".badge-lane-%s" % lane),
                    "row %s lacks its badge-lane-%s" % (row.member["slug"], lane))

    async def test_spec_detail_footer_hint_line(self):
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _detail_board(self.root, "documented"))
        async with app.run_test(size=(120, 24)) as pilot:
            self._push_member(app)
            await pilot.pause()
            hints = app.screen.query_one(".modal-footer-hints")
            self.assertEqual(str(hints.render()), self.SPEC_HINTS)

    async def test_epic_detail_footer_hint_line(self):
        _make_epic(self.root, "ep1", [("m1", "d", "low")])
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _epic_detail_board(
                self.root, "ep1", members=[("m1", "low", "ready")]))
        async with app.run_test(size=(120, 24)) as pilot:
            app.push_screen(dashboard.EpicDetailScreen("ep1"))
            await pilot.pause()
            hints = app.screen.query_one(".modal-footer-hints")
            self.assertEqual(str(hints.render()), self.EPIC_HINTS)

    async def test_run_confirm_footer_hint_line(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test(size=(120, 24)) as pilot:
            app.push_screen(dashboard.EpicRunConfirmScreen("ep1"))
            await pilot.pause()
            hints = app.screen.query_one(".modal-footer-hints")
            self.assertEqual(str(hints.render()), self.CONFIRM_HINTS)

    def test_modal_title_bar_css_uses_accent_background(self):
        blocks = {
            "MemberDetailScreen": dashboard.MemberDetailScreen.CSS,
            "EpicDetailScreen": dashboard.EpicDetailScreen.CSS,
            "EpicRunConfirmScreen": dashboard.EpicRunConfirmScreen.CSS,
        }
        for name, css in blocks.items():
            block = re.search(r"\.modal-title-bar\s*\{[^}]*\}", css)
            self.assertIsNotNone(
                block, "%s lacks a .modal-title-bar CSS rule" % name)
            self.assertIn("background: $accent", block.group(0))

    async def test_focused_active_tab_is_a_solid_accent_block(self):
        # board-modal-chrome "The focused active tab stays readable" scenario:
        # while the artifact tab strip has focus, the active Tab renders dark
        # bold text (the theme background tone) on a solid accent block — never
        # the light-on-accent block-cursor default. Unfocused, the active tab
        # keeps its themed accent-text-on-non-accent-background look.
        self._plant_artifacts("documented")
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _detail_board(self.root, "documented"))
        async with app.run_test(size=(120, 24)) as pilot:
            self._push_member(app)
            await pilot.pause()
            cssvars = app.get_css_variables()
            accent = Color.parse(cssvars["accent"]).rgb
            background = Color.parse(cssvars["background"]).rgb
            tabs = app.screen.query_one(Tabs)
            # Unfocused: park focus off the strip and confirm the active tab is
            # not painted the solid accent block (the existing themed state).
            app.set_focus(app.screen.query_one("#close-detail", Button))
            await pilot.pause()
            active = app.screen.query_one("Tab.-active", Tab)
            self.assertNotEqual(active.styles.background.rgb, accent)
            # Focused: the active tab becomes dark bold text on solid accent.
            app.set_focus(tabs)
            await pilot.pause()
            active = app.screen.query_one("Tab.-active", Tab)
            self.assertEqual(active.styles.background.rgb, accent)
            self.assertEqual(active.styles.background.a, 1.0)
            self.assertEqual(active.styles.color.rgb, background)
            self.assertTrue(active.styles.text_style.bold)

    def _plant_artifacts(self, slug, base=None):
        base = base or self.root
        _write(os.path.join(base, ".shipd", "planned", slug, "plan.md"),
               "# %s plan\n" % slug)
        _write(os.path.join(base, ".shipd", "planned", slug, "specs",
                            "delivery-dashboard", "spec.md"),
               "# %s spec\n" % slug)
        _write(os.path.join(base, ".shipd", "planned", slug, "tasks.md"),
               "# %s tasks\n" % slug)


class ParkedMemberModalTest(DashboardTestBase, unittest.IsolatedAsyncioTestCase):
    """The spec-detail modal's badge row and reason callout for a parked
    member (delivery-dashboard board-parked-member-signal spec): an
    error-tier state chip in place of the muted live-stage chip, and — when
    the entry carries a ``reason`` — a tinted accent-bar callout above the
    artifact tabs, the member-level analogue of the epic stall banner."""

    def _push_member(self, app, entry=None, state="active"):
        member = {"slug": "documented", "description": "d", "risk": "high",
                  "state": state, "location": self.root,
                  "actions": [], "session_id": None}
        app.push_screen(
            dashboard.MemberDetailScreen("ep", member, entry or {}, "active"))

    async def test_rejected_member_shows_state_chip_and_reason_callout(self):
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _detail_board(self.root, "documented"))
        async with app.run_test(size=(120, 24)) as pilot:
            self._push_member(app, entry={"slug": "documented",
                                          "state": "rejected",
                                          "stage": "gate",
                                          "reason": "context insufficient"})
            await pilot.pause()
            chip = app.screen.query_one(".badge-error")
            self.assertEqual(str(chip.render()), "rejected")
            muted = "\n".join(
                str(w.render()) for w in app.screen.query(".badge-muted"))
            self.assertNotIn("stage:", muted)
            callout = app.screen.query_one("#member-signal-callout")
            self.assertIn("context insufficient",
                          str(callout.query_one(".signal-reason").render()))

    async def test_needs_human_member_with_no_reason_shows_no_callout(self):
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _detail_board(self.root, "documented"))
        async with app.run_test(size=(120, 24)) as pilot:
            self._push_member(app, entry={"slug": "documented",
                                          "state": "needs-human"})
            await pilot.pause()
            chip = app.screen.query_one(".badge-error")
            self.assertEqual(str(chip.render()), "needs-human")
            self.assertEqual(list(app.screen.query("#member-signal-callout")),
                             [])

    async def test_driving_member_keeps_the_live_stage_chip(self):
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _detail_board(self.root, "documented"))
        async with app.run_test(size=(120, 24)) as pilot:
            self._push_member(app, entry={"slug": "documented",
                                          "state": "driving",
                                          "stage": "build"})
            await pilot.pause()
            muted = "\n".join(
                str(w.render()) for w in app.screen.query(".badge-muted"))
            self.assertIn("stage: build", muted)
            self.assertEqual(list(app.screen.query(".badge-error")), [])
            self.assertEqual(list(app.screen.query("#member-signal-callout")),
                             [])


class LiveBuildMemberModalTest(DashboardTestBase,
                               unittest.IsolatedAsyncioTestCase):
    """The spec-detail modal of a member placed by a live interactive build
    heartbeat (delivery-dashboard board-live-build-lane spec): the muted
    ``stage:`` chip is derived from that heartbeat when no roster stage chip
    or parked signal applies, and the lane badge follows
    :func:`_member_column` into ``review``."""

    def _push_member(self, app, stage, entry=None, state="archived"):
        member = {"slug": "documented", "description": "d", "risk": "high",
                  "state": state, "location": self.root,
                  "actions": [], "session_id": None,
                  "build_heartbeat": {"slug": "documented", "kind": "build",
                                      "state": "running", "stage": stage,
                                      "updated_at": time.time()}}
        app.push_screen(
            dashboard.MemberDetailScreen("ep", member, entry or {}, "active"))

    async def test_live_build_member_shows_stage_chip_and_review_lane(self):
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _detail_board(self.root, "documented"))
        async with app.run_test(size=(120, 24)) as pilot:
            self._push_member(app, "review")
            await pilot.pause()
            muted = "\n".join(
                str(w.render()) for w in app.screen.query(".badge-muted"))
            self.assertIn("stage: review", muted)
            self.assertTrue(app.screen.query(".badge-lane-review"))
            self.assertEqual(list(app.screen.query(".badge-error")), [])

    async def test_parked_signal_still_wins_over_the_build_stage_chip(self):
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _detail_board(self.root, "documented"))
        async with app.run_test(size=(120, 24)) as pilot:
            self._push_member(app, "review",
                              entry={"slug": "documented",
                                     "state": "needs-human"})
            await pilot.pause()
            chip = app.screen.query_one(".badge-error")
            self.assertEqual(str(chip.render()), "needs-human")
            muted = "\n".join(
                str(w.render()) for w in app.screen.query(".badge-muted"))
            self.assertNotIn("stage:", muted)


class ControlHierarchyTest(DashboardTestBase, unittest.IsolatedAsyncioTestCase):
    """The board's two-tier control hierarchy (delivery-dashboard
    board-control-hierarchy spec): primary controls render a solid accent
    background with dark bold labels, secondary controls the hover-background
    elevation with muted text; the active grouping mode is a solid accent
    block and inactive modes sit on the hover background; and a modal title
    bar's inline ``✕`` renders its dark glyph directly on the accent bar."""

    async def test_confirm_yes_is_primary_no_is_secondary(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test(size=(120, 24)) as pilot:
            app.push_screen(dashboard.EpicRunConfirmScreen("ep1"))
            await pilot.pause()
            cssvars = app.get_css_variables()
            accent = Color.parse(cssvars["accent"]).rgb
            background = Color.parse(cssvars["background"]).rgb
            bg_hover = Color.parse(cssvars["bg-hover"]).rgb
            fg_muted = Color.parse(cssvars["fg-muted"]).rgb
            yes = app.screen.query_one("#epic-run-yes", Button)
            self.assertIn("button-primary", yes.classes)
            self.assertEqual(yes.styles.background.rgb, accent)
            self.assertEqual(yes.styles.color.rgb, background)
            self.assertTrue(yes.styles.text_style.bold)
            no = app.screen.query_one("#epic-run-no", Button)
            self.assertIn("button-secondary", no.classes)
            self.assertEqual(no.styles.background.rgb, bg_hover)
            self.assertEqual(no.styles.color.rgb, fg_muted)

    async def test_active_mode_is_a_solid_accent_block(self):
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test(size=(120, 24)) as pilot:
            await pilot.pause()
            cssvars = app.get_css_variables()
            accent = Color.parse(cssvars["accent"]).rgb
            background = Color.parse(cssvars["background"]).rgb
            bg_hover = Color.parse(cssvars["bg-hover"]).rgb
            fg_muted = Color.parse(cssvars["fg-muted"]).rgb
            active = app.query_one("#group-mode-epic", Button)
            self.assertTrue(active.has_class("mode-active"))
            self.assertEqual(active.styles.background.rgb, accent)
            self.assertEqual(active.styles.color.rgb, background)
            self.assertTrue(active.styles.text_style.bold)
            inactive = app.query_one("#group-mode-initiative", Button)
            self.assertFalse(inactive.has_class("mode-active"))
            self.assertEqual(inactive.styles.background.rgb, bg_hover)
            self.assertEqual(inactive.styles.color.rgb, fg_muted)

    async def test_title_bar_close_renders_on_the_accent_bar(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test(size=(120, 24)) as pilot:
            app.push_screen(dashboard.EpicRunConfirmScreen("ep1"))
            await pilot.pause()
            cssvars = app.get_css_variables()
            accent = Color.parse(cssvars["accent"]).rgb
            background = Color.parse(cssvars["background"]).rgb
            bar = app.screen.query_one(".modal-title-bar")
            close = bar.query_one("#epic-run-close", Button)
            # Park focus off the close (it auto-focuses on open, where the
            # dimmed-accent focus scheme applies — asserted separately) so this
            # asserts the base accent-bar chrome the ✕ carries unfocused.
            app.set_focus(app.screen.query_one("#epic-run-no", Button))
            await pilot.pause()
            self.assertEqual(close.styles.background.rgb, accent)
            self.assertEqual(close.styles.color.rgb, background)


def _painted_line(app, widget, y=0):
    """The compositor-painted strip for ``widget``'s ``y``-th line, cropped to
    the widget's on-screen columns — the *painted* pixels, not the pre-layout
    content string. This reveals a card whose content word-wrapped onto a
    cropped second line (the blank-card bug), which ``widget.render()`` hides
    because its content string still looks intact."""
    region, _clip = app.screen._compositor.visible_widgets[widget]
    strips = app.screen._compositor.render_strips()
    return strips[region.y + y].crop(region.x, region.x + region.width)


def _segment_color(strip, needle):
    """The truecolor RGB of the first painted segment in ``strip`` whose text
    contains ``needle`` (``None`` when the match is unstyled or absent)."""
    for seg in strip._segments:
        if needle in seg.text:
            style = seg.style
            if style and style.color:
                return style.color.get_truecolor()
            return None
    return None


def assert_chrome_contained(test, screen):
    """The reusable chrome-containment sweep (delivery-dashboard
    modal-chrome-containment spec): assert every modal chrome widget on
    ``screen`` — each ``Button``, each ``.modal-badge`` chip, and each
    ``.modal-title-text`` — renders fully inside the screen's ``Container``
    with a nonzero region, and that badge chips stay content-sized (narrower
    than half the container row) rather than stretching to the row width and
    pushing their siblings outside the modal. A chrome element escaping its
    container fails here — the guard the GraphOption, group-header, and
    modal-badge default-width regressions all lacked."""
    container = screen.query_one(dashboard.Container)
    creg = container.region
    half = creg.width / 2
    titles = list(screen.query(".modal-title-text"))
    for widget in list(screen.query(Button)) + titles:
        reg = widget.region
        test.assertGreater(reg.width, 0, "%r has zero width" % widget)
        test.assertGreater(reg.height, 0, "%r has zero height" % widget)
        test.assertTrue(
            creg.contains_region(reg),
            "%r region %r escapes container %r" % (widget, reg, creg))
    for badge in screen.query(".modal-badge"):
        reg = badge.region
        test.assertGreater(reg.width, 0, "badge %r has zero width" % badge)
        test.assertTrue(
            creg.contains_region(reg),
            "badge %r region %r escapes container %r" % (badge, reg, creg))
        test.assertLess(
            reg.width, half,
            "badge %r width %d is not narrower than half the row (%r)"
            % (badge, reg.width, half))
    # The accent title bar and its inline ✕ close control must not overhang the
    # container's content region — their right edge stays within the right edge
    # of the padded content rows below (modal-chrome-containment).
    content_right = container.content_region.right
    for bar in screen.query(".modal-title-bar"):
        test.assertLessEqual(
            bar.region.right, content_right,
            "title bar %r right %d overhangs container content right %d"
            % (bar.region, bar.region.right, content_right))
        for close in bar.query(Button):
            test.assertLessEqual(
                close.region.right, content_right,
                "close control %r right %d overhangs container content right %d"
                % (close.region, close.region.right, content_right))


def assert_board_rows_contained(test, app):
    """The board-screen chrome sweep (delivery-dashboard lane-row-presentation
    spec), the lane-row analogue of :func:`assert_chrome_contained`: for every
    lane, assert each :class:`EpicGroupRow`'s buttons sit inside the lane's
    ``scrollable_content_region`` (never spilling past the lane border), and
    every visible :class:`TaskCard`'s painted first line begins with the ✓/●
    glyph and the slug's visible prefix — catching the wrap-blank bug where an
    overlong slug wraps onto a cropped second line, leaving the painted line a
    bare glyph.

    It additionally carries the stable-scrollbar-gutter invariant (delivery-
    dashboard lane-scrollbar-gutter spec): where a lane's vertical scrollbar is
    displayed, every group-header button's region stays disjoint from the
    scrollbar's region (no button ever shares the scrollbar's column); and
    lanes of equal outer width have an equal ``scrollable_content_region``
    width, so a scrolling lane never differs in content width from a
    non-scrolling sibling — content width is a constant of the lane, not a
    function of scroll state."""
    for lane in app.query(dashboard.Lane):
        region = lane.scrollable_content_region
        scrollbar = (lane.vertical_scrollbar.region
                     if lane.show_vertical_scrollbar else None)
        for row in lane.query(dashboard.EpicGroupRow):
            for button in row.query(Button):
                reg = button.region
                test.assertGreater(reg.width, 0, "%r has zero width" % button)
                test.assertTrue(
                    region.contains_region(reg),
                    "%r region %r escapes lane %s content region %r"
                    % (button, reg, lane.lane_name, region))
                if scrollbar is not None:
                    test.assertFalse(
                        reg.overlaps(scrollbar),
                        "%r region %r overlaps lane %s scrollbar region %r"
                        % (button, reg, lane.lane_name, scrollbar))
    by_outer_width = {}
    for lane in app.query(dashboard.Lane):
        by_outer_width.setdefault(lane.size.width, []).append(lane)
    for outer_width, lanes in by_outer_width.items():
        content_widths = {l.scrollable_content_region.width for l in lanes}
        test.assertEqual(
            len(content_widths), 1,
            "lanes of outer width %d disagree on content width %r "
            "(scroll state leaked into content width): %r"
            % (outer_width, sorted(content_widths),
               {l.lane_name: (l.show_vertical_scrollbar,
                              l.scrollable_content_region.width)
                for l in lanes}))
    visible = app.screen._compositor.visible_widgets
    for card in app.query(dashboard.TaskCard):
        if card not in visible:
            continue
        painted = _painted_line(app, card).text.strip()
        slug = card.member["slug"]
        # glyph + space + at least one slug character — never a bare glyph
        # with the slug wrapped onto a discarded second line.
        test.assertRegex(
            painted, r"^[✓●] .",
            "card %r painted only %r — slug prefix invisible" % (slug, painted))
        body = painted[2:].rstrip("…")
        test.assertTrue(
            slug.startswith(body),
            "card painted body %r is not a prefix of slug %r" % (body, slug))


class ModalChromeContainmentTest(
        DashboardTestBase, unittest.IsolatedAsyncioTestCase):
    """The chrome-containment guard (delivery-dashboard modal-chrome-
    containment spec): the reusable :func:`assert_chrome_contained` sweep run
    against all four modal screens (spec-detail, epic-detail, run-confirmation,
    graph config), plus the badge chips sizing to content and the focused ✕
    keeping the accent bar's dimmed-accent scheme."""

    def _push_member(self, app, risk="low", entry=None):
        member = {"slug": "documented", "description": "d", "risk": risk,
                  "state": "ready", "location": self.root,
                  "actions": [], "session_id": None}
        app.push_screen(
            dashboard.MemberDetailScreen("ep", member, entry or {}, "active"))

    async def test_spec_detail_all_four_chips_visible_and_content_sized(self):
        # A member with a risk (low), a derived lane (driving → building), a
        # live stage (plan#1), and an epic renders all four chips inside the
        # modal, each sized to its text plus padding.
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _detail_board(self.root, "documented"))
        async with app.run_test(size=(120, 40)) as pilot:
            self._push_member(
                app, risk="low",
                entry={"slug": "documented", "state": "driving",
                       "stage": "plan", "attempt": 1})
            await pilot.pause()
            badges = list(
                app.screen.query(".modal-badge-row .modal-badge"))
            self.assertEqual(len(badges), 4)
            self.assertTrue(app.screen.query(".badge-risk-low"))
            self.assertTrue(app.screen.query(".badge-lane-building"))
            muted = "\n".join(
                str(w.render()) for w in app.screen.query(".badge-muted"))
            self.assertIn("plan#1", muted)
            self.assertIn("epic", muted)
            assert_chrome_contained(self, app.screen)

    async def test_epic_detail_chips_and_member_lane_chips_contained(self):
        _make_epic(self.root, "ep1", [("m1", "d", "low")])
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _epic_detail_board(
                self.root, "ep1", status="active", theme="ux",
                initiative={"slug": "look-feel"},
                members=[("m1", "high", "ready"),
                        ("m2", "low", "unplanned")]))
        async with app.run_test(size=(120, 40)) as pilot:
            app.push_screen(dashboard.EpicDetailScreen("ep1"))
            await pilot.pause()
            # Both member rows contribute a lane chip to the swept badges.
            self.assertEqual(
                len(list(app.screen.query(dashboard.EpicMemberRow))), 2)
            assert_chrome_contained(self, app.screen)

    async def test_run_confirmation_chrome_contained(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test(size=(120, 40)) as pilot:
            app.push_screen(dashboard.EpicRunConfirmScreen("ep1"))
            await pilot.pause()
            assert_chrome_contained(self, app.screen)

    async def test_graph_config_chrome_contained(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test(size=(120, 40)) as pilot:
            app.push_screen(dashboard.GraphConfigScreen())
            await pilot.pause()
            assert_chrome_contained(self, app.screen)

    async def test_focused_close_keeps_the_dimmed_accent_scheme(self):
        # While the accent title bar's ✕ holds focus it keeps the dimmed
        # accent (like hover), never the theme's default focused-Button color.
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _detail_board(self.root, "documented"))
        async with app.run_test(size=(120, 40)) as pilot:
            self._push_member(app)
            await pilot.pause()
            accent_dim = Color.parse(
                app.get_css_variables()["accent-dim"]).rgb
            close = app.screen.query_one("#close-detail", Button)
            app.set_focus(close)
            await pilot.pause()
            self.assertEqual(close.styles.background.rgb, accent_dim)


def _board_sweep_board():
    """Two epics sharing one initiative, their members spread across the
    unplanned/ready/shipped lanes — the multi-epic, multi-lane fixture the
    board-screen chrome sweep runs over (delivery-dashboard lane-row-
    presentation spec). Ready members make each epic runnable (run + open
    controls); archived members land in the SHIPPED lane's ``✓`` cards. One
    member's slug is far wider than a lane at width 120, so the narrow-width
    sweep exercises the wrap-blank guard — it paints a cropped bare glyph
    without the ellipsis fix, an ellipsized prefix with it."""
    def _m(slug, state, actions=None):
        return {"slug": slug, "description": "d", "risk": "low",
                "state": state, "location": "/x", "actions": actions or [],
                "session_id": None}
    init = {"slug": "init", "status": "active"}
    ep1 = {"slug": "ep1", "status": "active", "theme": None, "initiative": init,
           "members": [_m("a-deliberately-long-unplanned-slug", "unplanned",
                          ["plan"]),
                       _m("m2", "ready", ["run"]), _m("s1", "archived")],
           "heartbeat": None, "report": None}
    ep2 = {"slug": "ep2", "status": "active", "theme": None, "initiative": init,
           "members": [_m("m3", "ready", ["run"]), _m("s2", "archived")],
           "heartbeat": None, "report": None}
    return {"root": "/x", "generated_at": time.time(), "epics": [ep1, ep2],
            "groups": [{"initiative": init, "epics": [ep1, ep2]}]}


class BoardRowsContainedTest(unittest.IsolatedAsyncioTestCase):
    """The board-screen chrome sweep runs at two terminal widths (delivery-
    dashboard lane-row-presentation spec: "The board sweep guards lane rows at
    multiple widths"): every group-header button stays inside its lane's
    scrollable content region and every card's painted line begins with its
    slug prefix — the regression guard the blank-card wrap bug lacked."""

    async def test_board_rows_contained_at_wide_width(self):
        app = dashboard.BoardApp(root="/x", board_fn=_board_sweep_board)
        async with app.run_test(size=(160, 40)) as pilot:
            await pilot.pause()
            assert_board_rows_contained(self, app)

    async def test_board_rows_contained_at_narrow_width(self):
        app = dashboard.BoardApp(root="/x", board_fn=_board_sweep_board)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            assert_board_rows_contained(self, app)


def _gutter_board(n_shipped, n_ready=1):
    """A one-epic board whose SHIPPED lane holds ``n_shipped`` archived
    members and whose READY lane holds ``n_ready`` runnable members — the
    knob the lane-scrollbar-gutter tests turn to drive a lane between the
    non-scrolling and scrolling states at a fixed terminal size."""
    def _m(slug, state, actions=None):
        return {"slug": slug, "description": "d", "risk": "low",
                "state": state, "location": "/x", "actions": actions or [],
                "session_id": None}
    init = {"slug": "init", "status": "active"}
    members = [_m("r%d" % i, "ready", ["run"]) for i in range(n_ready)]
    members += [_m("s%d" % i, "archived") for i in range(n_shipped)]
    ep = {"slug": "ep1", "status": "active", "theme": None, "initiative": init,
          "members": members, "heartbeat": None, "report": None}
    return {"root": "/x", "generated_at": time.time(), "epics": [ep],
            "groups": [{"initiative": init, "epics": [ep]}]}


class LaneScrollbarGutterTest(unittest.IsolatedAsyncioTestCase):
    """The stable lane scrollbar gutter (delivery-dashboard lane-scrollbar-
    gutter spec): a lane reserves its vertical scrollbar's column permanently,
    so content width is a constant of the lane rather than a function of
    scroll state — growth that makes the scrollbar appear never reflows the
    rows, and a non-scrolling lane's content width equals a scrolling
    sibling's."""

    async def test_growth_into_scrolling_keeps_shipped_content_width(self):
        # Grow the shipped lane via refresh_board() from a state where it does
        # not scroll to one where it does; its scrollable content width must be
        # identical before and after (the gutter, reserved either way, absorbs
        # the scrollbar instead of the content reflowing).
        state = {"b": _gutter_board(n_shipped=1)}
        app = dashboard.BoardApp(root="/x", board_fn=lambda: state["b"])
        async with app.run_test(size=(140, 20)) as pilot:
            await pilot.pause()
            shipped = app.query_one("#lane-shipped", dashboard.Lane)
            self.assertFalse(shipped.show_vertical_scrollbar)
            before = shipped.scrollable_content_region.width
            assert_board_rows_contained(self, app)
            state["b"] = _gutter_board(n_shipped=40)
            await app.refresh_board()
            await pilot.pause()
            shipped = app.query_one("#lane-shipped", dashboard.Lane)
            self.assertTrue(shipped.show_vertical_scrollbar)
            after = shipped.scrollable_content_region.width
            self.assertEqual(
                before, after,
                "shipped content width reflowed from %d to %d when its "
                "scrollbar appeared" % (before, after))
            assert_board_rows_contained(self, app)

    async def test_scrolling_and_non_scrolling_lanes_share_content_width(self):
        # At one terminal size, a scrolling SHIPPED lane and a non-scrolling
        # READY lane of the same outer width have equal content width — the
        # gutter is reserved whether or not the lane scrolls.
        app = dashboard.BoardApp(
            root="/x", board_fn=lambda: _gutter_board(n_shipped=40))
        async with app.run_test(size=(140, 20)) as pilot:
            await pilot.pause()
            shipped = app.query_one("#lane-shipped", dashboard.Lane)
            ready = app.query_one("#lane-ready", dashboard.Lane)
            self.assertTrue(shipped.show_vertical_scrollbar)
            self.assertFalse(ready.show_vertical_scrollbar)
            # The lanes are laid out at the same outer width (both `1fr`),
            # so equal content width is the invariant, not a coincidence.
            self.assertEqual(ready.size.width, shipped.size.width)
            self.assertEqual(
                ready.scrollable_content_region.width,
                shipped.scrollable_content_region.width,
                "non-scrolling ready lane content width %d differs from "
                "scrolling shipped lane content width %d"
                % (ready.scrollable_content_region.width,
                   shipped.scrollable_content_region.width))



class ModalKeysTest(DashboardTestBase, unittest.IsolatedAsyncioTestCase):
    """The detail modals' key map (board-modal-chrome spec): ``y`` copies the
    modal's subject slug via the app clipboard, ``⇥`` cycles the spec-detail
    artifact tabs (wrapping), ``j``/``k`` scroll the active content pane, and
    ``o`` opens the active artifact in the editor via the pure
    :func:`dashboard.build_editor_launch` handed to the App's ``_spawn_launch``
    seam — a no-op when the modal shows no on-disk artifact."""

    def _plant_artifacts(self, slug, base=None):
        base = base or self.root
        _write(os.path.join(base, ".shipd", "planned", slug, "plan.md"),
               "# %s plan\n" % slug)
        _write(os.path.join(base, ".shipd", "planned", slug, "specs",
                            "delivery-dashboard", "spec.md"),
               "# %s spec\n" % slug)
        _write(os.path.join(base, ".shipd", "planned", slug, "tasks.md"),
               "# %s tasks\n" % slug)

    def _push_member(self, app, slug="documented"):
        member = {"slug": slug, "description": "d", "risk": "high",
                  "state": "ready", "location": self.root,
                  "actions": [], "session_id": None}
        app.push_screen(
            dashboard.MemberDetailScreen("ep", member, {}, "active"))

    async def test_y_copies_the_member_slug(self):
        self._plant_artifacts("documented")
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _detail_board(self.root, "documented"))
        async with app.run_test(size=(120, 24)) as pilot:
            copied = []
            app.copy_to_clipboard = copied.append
            self._push_member(app)
            await pilot.pause()
            await pilot.press("y")
            self.assertEqual(copied, ["documented"])

    async def test_y_copies_the_epic_slug(self):
        _make_epic(self.root, "ep1", [("m1", "d", "low")])
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _epic_detail_board(
                self.root, "ep1", members=[("m1", "low", "ready")]))
        async with app.run_test(size=(120, 24)) as pilot:
            copied = []
            app.copy_to_clipboard = copied.append
            app.push_screen(dashboard.EpicDetailScreen("ep1"))
            await pilot.pause()
            await pilot.press("y")
            self.assertEqual(copied, ["ep1"])

    async def test_tab_cycles_the_artifact_tabs_and_wraps(self):
        self._plant_artifacts("documented")
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _detail_board(self.root, "documented"))
        async with app.run_test(size=(120, 24)) as pilot:
            self._push_member(app)
            await pilot.pause()
            tabs = app.screen.query_one(TabbedContent)
            seen = [tabs.active]
            for _ in range(3):
                await pilot.press("tab")
                await pilot.pause()
                seen.append(tabs.active)
            # Three artifact tabs (Plan/Spec/Tasks): the first three actives are
            # distinct and the fourth wraps back to the first.
            self.assertEqual(len(set(seen[:3])), 3)
            self.assertEqual(seen[0], seen[3])

    async def test_j_then_k_scrolls_the_active_pane(self):
        self._plant_artifacts("documented")
        # Overflow the active (Plan) pane so it has somewhere to scroll.
        _write(os.path.join(self.root, ".shipd", "planned", "documented",
                            "plan.md"),
               "# plan\n\n" + "\n".join("line %d" % i for i in range(200)))
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _detail_board(self.root, "documented"))
        async with app.run_test(size=(120, 24)) as pilot:
            self._push_member(app)
            await pilot.pause()
            tabs = app.screen.query_one(TabbedContent)
            scroller = tabs.get_pane(tabs.active).query_one(VerticalScroll)
            self.assertEqual(scroller.scroll_offset.y, 0)
            await pilot.press("j")
            await pilot.pause()
            down = scroller.scroll_offset.y
            self.assertGreater(down, 0)
            await pilot.press("k")
            await pilot.pause()
            self.assertLess(scroller.scroll_offset.y, down)

    async def test_o_opens_the_active_artifact_in_the_editor(self):
        self._plant_artifacts("documented")
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _detail_board(self.root, "documented"))
        async with app.run_test(size=(120, 24)) as pilot:
            launches = []
            app._spawn_launch = launches.append
            self._push_member(app)
            await pilot.pause()
            with mock.patch.dict(os.environ, {"EDITOR": "nano"}):
                await pilot.press("o")
            plan_path = os.path.join(self.root, ".shipd", "planned",
                                     "documented", "plan.md")
            self.assertEqual(
                launches, [dashboard.build_editor_launch(plan_path, "nano")])

    async def test_o_in_epic_detail_opens_the_epic_markdown(self):
        _make_epic(self.root, "ep1", [("m1", "d", "low")])
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _epic_detail_board(
                self.root, "ep1", members=[("m1", "low", "ready")]))
        async with app.run_test(size=(120, 24)) as pilot:
            launches = []
            app._spawn_launch = launches.append
            app.push_screen(dashboard.EpicDetailScreen("ep1"))
            await pilot.pause()
            with mock.patch.dict(os.environ, {"EDITOR": "nano"}):
                await pilot.press("o")
            epic_path = os.path.join(self.root, ".shipd", "epics", "ep1",
                                     "epic.md")
            self.assertEqual(
                launches, [dashboard.build_editor_launch(epic_path, "nano")])

    async def test_o_in_epic_detail_opens_a_worktree_hosted_epic_markdown(self):
        # The epic was authored inside its own worktree, so `o` must open the
        # file under that worktree's content dir — the very file the overview
        # renders — not a nonexistent path under the board root
        # (delivery-dashboard board-aggregation).
        wt = os.path.join(self.root, ".worktrees", "epic-ep1")
        _make_epic(wt, "ep1", [("m1", "d", "low")])
        board = _epic_detail_board(self.root, "ep1",
                                   members=[("m1", "low", "ready")])
        board["epics"][0]["location"] = os.path.abspath(wt)
        app = dashboard.BoardApp(root=self.root, board_fn=lambda: board)
        async with app.run_test(size=(120, 24)) as pilot:
            launches = []
            app._spawn_launch = launches.append
            app.push_screen(dashboard.EpicDetailScreen("ep1"))
            await pilot.pause()
            with mock.patch.dict(os.environ, {"EDITOR": "nano"}):
                await pilot.press("o")
            epic_path = os.path.join(os.path.abspath(wt), ".shipd", "epics",
                                     "ep1", "epic.md")
            self.assertEqual(
                launches, [dashboard.build_editor_launch(epic_path, "nano")])

    async def test_o_in_epic_detail_is_a_no_op_when_the_epic_file_is_absent(
            self):
        # No epic.md anywhere: `o` spawns nothing and the modal stays open.
        board = _epic_detail_board(self.root, "ep1",
                                   members=[("m1", "low", "ready")])
        board["epics"][0]["location"] = os.path.abspath(self.root)
        app = dashboard.BoardApp(root=self.root, board_fn=lambda: board)
        async with app.run_test(size=(120, 24)) as pilot:
            launches = []
            app._spawn_launch = launches.append
            app.push_screen(dashboard.EpicDetailScreen("ep1"))
            await pilot.pause()
            await pilot.press("o")
            self.assertEqual(launches, [])
            self.assertIsInstance(app.screen, dashboard.EpicDetailScreen)

    async def test_o_with_the_notice_showing_is_a_no_op(self):
        # No artifacts planted for "undocumented", so the modal shows the
        # not-yet-planned notice — `o` spawns nothing and the modal stays open.
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _detail_board(self.root, "undocumented"))
        async with app.run_test(size=(120, 24)) as pilot:
            launches = []
            app._spawn_launch = launches.append
            self._push_member(app, slug="undocumented")
            await pilot.pause()
            await pilot.press("o")
            self.assertEqual(launches, [])
            self.assertIsInstance(app.screen, dashboard.MemberDetailScreen)


def _stalled_detail_hb():
    """A finished heartbeat parking one member ``needs-human`` — the stall
    signal the epic-detail warning/Retry block keys on."""
    return {"epic": "ep1", "state": "finished", "seq": 2,
            "updated_at": time.time(),
            "roster": [{"slug": "m1", "state": "needs-human",
                        "stage": "worktree",
                        "reason": "worktree creation failed"}]}


class StalledEpicDetailTest(DashboardTestBase, unittest.IsolatedAsyncioTestCase):
    """A stalled epic's detail modal (delivery-dashboard board-stall-signal
    spec) warns per parked member and offers a Retry that dispatches the same
    detached epic-level run the group header's run control does; a non-stalled
    epic's modal carries neither."""

    async def _push_detail(self, app):
        await app.push_screen(dashboard.EpicDetailScreen("ep1"))
        await app.workers.wait_for_complete()

    async def test_stalled_modal_warns_per_member_in_error_banner(self):
        _make_epic(self.root, "ep1", [("m1", "d", "high")])
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _epic_detail_board(
                self.root, "ep1", members=[("m1", "high", "active")],
                heartbeat=_stalled_detail_hb()))
        async with app.run_test(size=(120, 40)) as pilot:
            await self._push_detail(app)
            await pilot.pause()
            cssvars = app.get_css_variables()
            error = Color.parse(cssvars["error"]).rgb
            text_error = Color.parse(cssvars["text-error"]).rgb
            warning = Color.parse(cssvars["warning"]).rgb
            fg_muted = Color.parse(cssvars["fg-muted"]).rgb
            fg_subtle = Color.parse(cssvars["fg-subtle"]).rgb
            # The banner is a tinted panel — the error color at 10% alpha for
            # the background, never a solid error block with white text — with
            # a solid one-cell error bar down its left edge.
            banner = app.screen.query_one("#epic-stall-banner", dashboard.Horizontal)
            self.assertEqual(banner.styles.background.rgb, error)
            self.assertAlmostEqual(banner.styles.background.a, 0.1, places=2)
            bar = banner.query_one(".stall-accent-bar", dashboard.Static)
            self.assertEqual(bar.styles.background.rgb, error)
            self.assertEqual(bar.styles.background.a, 1.0)
            self.assertEqual(bar.styles.width.value, 1)
            # Header row: bold error-colored STALLED beside a right-aligned
            # muted parked summary.
            title = banner.query_one(".stall-title", dashboard.Static)
            self.assertEqual(str(title.render()), "STALLED")
            self.assertTrue(title.styles.text_style.bold)
            self.assertEqual(title.styles.color.rgb, text_error)
            summary = banner.query_one(".stall-summary", dashboard.Static)
            self.assertEqual(
                str(summary.render()), "1 member(s) parked · needs-human")
            self.assertEqual(summary.styles.color.rgb, fg_muted)
            # One member row: slug in the default foreground, muted stage, and
            # the reason as a warning-colored chip on a 10% warning tint.
            row = banner.query_one(".stall-member-row", dashboard.Horizontal)
            row_text = "\n".join(
                str(w.render()) for w in row.query(dashboard.Static))
            self.assertIn("m1", row_text)
            self.assertIn("worktree", row_text)
            chip = row.query_one(".stall-reason-chip", dashboard.Static)
            self.assertEqual(str(chip.render()), "worktree creation failed")
            self.assertEqual(chip.styles.color.rgb, warning)
            self.assertEqual(chip.styles.background.rgb, warning)
            self.assertAlmostEqual(chip.styles.background.a, 0.1, places=2)
            # A muted reassurance line stating retry is safe.
            note = banner.query_one(".stall-note", dashboard.Static)
            self.assertEqual(str(note.render()), dashboard._STALL_NOTE)
            self.assertEqual(note.styles.color.rgb, fg_muted)
            # Action row: the primary Retry control rendering its full label
            # (never the 3-cell compact-button truncation) beside a subtle
            # right-aligned parked-age label.
            retry = banner.query_one("#epic-retry", Button)
            self.assertEqual(str(retry.label), "Retry run")
            self.assertIn("button-primary", retry.classes)
            self.assertNotIn("compact-button", retry.classes)
            age = banner.query_one(".stall-age", dashboard.Static)
            rendered_age = str(age.render())
            self.assertTrue(rendered_age.startswith("parked "))
            self.assertTrue(rendered_age.endswith(" ago"))
            self.assertEqual(age.styles.color.rgb, fg_subtle)

    async def test_retry_dispatches_epic_run_and_dismisses(self):
        _make_epic(self.root, "ep1", [("m1", "d", "high")])
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _epic_detail_board(
                self.root, "ep1", members=[("m1", "high", "active")],
                heartbeat=_stalled_detail_hb()))
        async with app.run_test(size=(120, 40)) as pilot:
            calls = []
            app.dispatch_epic_run = calls.append
            await self._push_detail(app)
            await pilot.pause()
            retry = app.screen.query_one("#epic-retry", Button)
            await pilot.click(retry)
            self.assertEqual(calls, ["ep1"])
            self.assertNotIsInstance(app.screen, dashboard.EpicDetailScreen)

    async def test_non_stalled_modal_has_no_warning_or_retry(self):
        _make_epic(self.root, "ep1", [("m1", "d", "low")])
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _epic_detail_board(
                self.root, "ep1", members=[("m1", "low", "ready")]))
        async with app.run_test(size=(120, 40)) as pilot:
            await self._push_detail(app)
            await pilot.pause()
            rendered = "\n".join(
                str(w.render()) for w in app.screen.query(dashboard.Static))
            self.assertNotIn("STALLED", rendered)
            self.assertFalse(app.screen.query("#epic-stall-banner"))
            self.assertFalse(app.screen.query("#epic-retry"))


class EpicMemberRowDrilldownTest(DashboardTestBase, unittest.IsolatedAsyncioTestCase):
    """Clicking a member row in the epic-detail modal drills into that
    change's own spec-detail modal (epic-detail-drilldown change): the row
    is a clickable, focusable `EpicMemberRow` whose *rendered* text still
    carries the risk in brackets (guards against the Rich-markup swallow bug
    a bare `[low]` label triggers without `markup=False`), and clicking it
    pushes `MemberDetailScreen` on top of the still-present `EpicDetailScreen`
    — `Escape` on the member modal pops back to the epic modal, not the
    board."""

    async def _open_detail(self, pilot, lane_name, slug):
        # The epic-detail modal is reached by clicking the group header's
        # title off the collapse arrow (delivery-dashboard board-epic-
        # grouping spec).
        await _open_epic_detail(pilot, self.app_, lane_name, slug)

    async def test_member_rows_are_epic_member_row_with_risk_and_state_rendered(
            self):
        _make_epic(self.root, "ep1", [("m1", "d", "low")])
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _epic_detail_board(
                self.root, "ep1", status="active",
                members=[("m1", "high", "ready"),
                        ("m2", "low", "unplanned")]))
        self.app_ = app
        async with app.run_test(size=(120, 30)) as pilot:
            await self._open_detail(pilot, "ready", "ep1")
            rows = list(app.screen.query(dashboard.EpicMemberRow))
            self.assertEqual(len(rows), 2)
            # Assert on the *rendered* output, not the raw label string —
            # a bareword bracket like "[high]" is Rich markup and gets
            # swallowed from the paint unless the widget sets markup=False.
            # The row is now a Horizontal carrying a lane badge ahead of its
            # `.epic-member-text` Static (board-modal-chrome), so the text
            # renders from that child, not the container row itself.
            rendered = "\n".join(
                str(r.query_one(".epic-member-text", dashboard.Static).render())
                for r in rows)
            self.assertIn("m1", rendered)
            self.assertIn("[high]", rendered)
            self.assertIn("ready", rendered)
            self.assertIn("m2", rendered)
            self.assertIn("[low]", rendered)
            self.assertIn("unplanned", rendered)
            # The row is a Horizontal now; without `height: auto` it would
            # inherit the container default (1fr) and stretch to fill the
            # member list instead of hugging its single line.
            for row in rows:
                self.assertEqual(row.region.height, 1)

    async def test_clicking_a_member_row_stacks_member_detail_over_epic_detail(
            self):
        _make_epic(self.root, "ep1", [("m1", "d", "low")])
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _epic_detail_board(
                self.root, "ep1", members=[("m1", "low", "ready")]))
        self.app_ = app
        async with app.run_test(size=(120, 30)) as pilot:
            await self._open_detail(pilot, "ready", "ep1")
            epic_screen = app.screen
            self.assertIsInstance(epic_screen, dashboard.EpicDetailScreen)
            row = app.screen.query_one(dashboard.EpicMemberRow)
            await pilot.click(row)
            self.assertIsInstance(app.screen, dashboard.MemberDetailScreen)
            self.assertEqual(app.screen.member["slug"], "m1")
            # The epic-detail modal is still on the stack, beneath the
            # member modal — this is a push, not a replace.
            self.assertIn(epic_screen, app.screen_stack)
            self.assertIs(app.screen_stack[-2], epic_screen)

            await pilot.press("escape")
            self.assertIsInstance(app.screen, dashboard.EpicDetailScreen)
            self.assertIs(app.screen, epic_screen)


class EpicRunControlTest(unittest.IsolatedAsyncioTestCase):
    """The epic-detail modal's **Run epic** control opens a confirmation
    modal rather than dispatching immediately (delivery-dashboard board-
    epic-grouping spec) — the wiring the removed hierarchy panel's ``r`` key
    used to own now routes through the epic-detail modal into
    :class:`dashboard.EpicRunConfirmScreen`; the epic-level run fires only on
    its Yes control."""

    def _capture(self, app):
        launches = []
        app._spawn_launch = launches.append
        return launches

    async def _open_confirm(self, pilot, app, lane_name, epic_slug):
        # Re-entered via the header title: open the epic-detail modal, then
        # activate its Run epic control, which pushes the confirmation modal.
        await _open_epic_detail(pilot, app, lane_name, epic_slug)
        run_button = app.screen.query_one("#epic-run", Button)
        await pilot.click(run_button)

    async def test_choosing_run_pushes_confirm_modal_no_dispatch(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test(size=(120, 24)) as pilot:
            launches = self._capture(app)
            group = app.query_one("#epic-group-ready-ep1", Collapsible)
            self.assertFalse(group.collapsed)
            await self._open_confirm(pilot, app, "ready", "ep1")
            self.assertIsInstance(app.screen, dashboard.EpicRunConfirmScreen)
            # No epic-level run has been dispatched yet.
            self.assertEqual(launches, [])
            # Opening the modal must not also collapse the group.
            self.assertFalse(group.collapsed)

    async def test_confirm_modal_shows_exact_prompt_text(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test(size=(120, 24)) as pilot:
            await self._open_confirm(pilot, app, "ready", "ep1")
            prompt_text = "\n".join(
                str(w.content) for w in app.screen.query(dashboard.Static))
            self.assertIn(
                "This will deliver the full epic, are you sure you want "
                "to continue?", prompt_text)

    async def test_yes_dispatches_exactly_one_epic_run_and_dismisses(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test(size=(120, 24)) as pilot:
            launches = self._capture(app)
            await self._open_confirm(pilot, app, "ready", "ep1")
            yes = app.screen.query_one("#epic-run-yes", Button)
            await pilot.click(yes)
            self.assertEqual(len(launches), 1)
            launch = launches[0]
            self.assertEqual(launch["mode"], "detach")
            self.assertIn("ep1", launch["argv"])
            self.assertNotIn("--member", launch["argv"])
            self.assertNotIsInstance(
                app.screen, dashboard.EpicRunConfirmScreen)

    async def test_no_dismisses_the_modal_with_zero_dispatches(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test(size=(120, 24)) as pilot:
            launches = self._capture(app)
            await self._open_confirm(pilot, app, "ready", "ep1")
            no = app.screen.query_one("#epic-run-no", Button)
            await pilot.click(no)
            self.assertEqual(launches, [])
            self.assertNotIsInstance(
                app.screen, dashboard.EpicRunConfirmScreen)

    async def test_close_control_dismisses_the_modal_with_zero_dispatches(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test(size=(120, 24)) as pilot:
            launches = self._capture(app)
            await self._open_confirm(pilot, app, "ready", "ep1")
            close = app.screen.query_one("#epic-run-close", Button)
            await pilot.click(close)
            self.assertEqual(launches, [])
            self.assertNotIsInstance(
                app.screen, dashboard.EpicRunConfirmScreen)

    async def test_escape_dismisses_the_modal_with_zero_dispatches(self):
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test(size=(120, 24)) as pilot:
            launches = self._capture(app)
            await self._open_confirm(pilot, app, "ready", "ep1")
            await pilot.press("escape")
            self.assertEqual(launches, [])
            self.assertNotIsInstance(
                app.screen, dashboard.EpicRunConfirmScreen)


class ShippedGroupCollapseTest(unittest.IsolatedAsyncioTestCase):
    def _group(self, app, slug):
        return app.query_one("#epic-group-shipped-%s" % slug, Collapsible)

    async def test_collapsing_a_shipped_group_hides_its_cards(self):
        app = dashboard.BoardApp(root="/x", board_fn=_shipped_board)
        async with app.run_test() as pilot:
            es1_group = self._group(app, "es1")
            es2_group = self._group(app, "es2")
            self.assertFalse(es1_group.collapsed)
            es1_group.collapsed = True
            await pilot.pause()
            es1_contents = es1_group.query_one(Collapsible.Contents)
            es2_contents = es2_group.query_one(Collapsible.Contents)
            # es1's cards are hidden; es2's group (and its cards) stay shown.
            self.assertFalse(es1_contents.display)
            self.assertTrue(es2_contents.display)
            self.assertFalse(es2_group.collapsed)

    async def test_group_headers_carry_grouping_class_no_status_colour(self):
        # The epic-group styling is a uniform gray/black scheme, not
        # per-epic-status colour (delivery-dashboard board-epic-grouping
        # spec) — the old ``Collapsible.status-*`` title-colour scheme is
        # gone.
        app = dashboard.BoardApp(root="/x", board_fn=_shipped_board)
        async with app.run_test():
            es1_group = self._group(app, "es1")
            es2_group = self._group(app, "es2")
            for group in (es1_group, es2_group):
                self.assertIn("epic-group", group.classes)
                self.assertFalse(
                    any(c.startswith("status-") for c in group.classes))


# ---------------------------------------------------------------------------
# RUN/PLAN/OPEN action dispatch — through the unchanged pure launch builders
# ---------------------------------------------------------------------------

def _actions_board():
    """A board with one epic holding four members, each pre-annotated with
    its eligible actions (mirroring the aggregation's output, matching the
    other App fixtures' convention of setting ``actions`` directly rather
    than recomputing it) — for exercising the App's RUN/PLAN/OPEN dispatch."""
    epic = {
        "slug": "ep", "status": "active", "theme": None,
        "initiative": None,
        "members": [
            {"slug": "fresh", "description": "d", "risk": "low",
             "state": "unplanned", "location": "/x", "actions": ["plan"],
             "session_id": None},
            {"slug": "rdy", "description": "d", "risk": "medium",
             "state": "ready", "location": "/x", "actions": ["run"],
             "session_id": None},
            {"slug": "parked", "description": "d", "risk": "high",
             "state": "rejected", "location": "/x", "actions": ["open"],
             "session_id": "sess-9"},
            {"slug": "driving", "description": "d", "risk": "low",
             "state": "active", "location": "/x", "actions": [],
             "session_id": "sess-live"},
        ],
        "heartbeat": {
            "epic": "ep", "state": "running", "seq": 1,
            "updated_at": time.time(),
            "roster": [{"slug": "driving", "state": "driving",
                        "stage": "build", "session_id": "sess-live"}],
        },
        "report": None,
    }
    return {
        "root": "/repo", "generated_at": time.time(),
        "epics": [epic],
        "groups": [{"initiative": None, "epics": [epic]}],
    }


def _find_card(app, slug):
    """The mounted :class:`dashboard.TaskCard` for ``slug``, wherever its
    lane placed it."""
    for card in app.query(dashboard.TaskCard):
        if card.member["slug"] == slug:
            return card
    return None


class ActionDispatchTest(unittest.IsolatedAsyncioTestCase):
    """A focused card's RUN/PLAN/OPEN key resolves through the same pure
    launch builders as the ``board``-verb tests — captured here via the
    App's ``_spawn_launch`` seam instead of actually spawning a process."""

    def _capture(self, app):
        launches = []
        app._spawn_launch = launches.append
        return launches

    async def test_plan_under_tmux_builds_tmux_new_window(self):
        app = dashboard.BoardApp(root="/repo", board_fn=_actions_board)
        async with app.run_test() as pilot:
            launches = self._capture(app)
            with mock.patch.dict(os.environ, {"TMUX": "/tmp/tmux-1/default"}):
                _find_card(app, "fresh").focus()
                await pilot.pause()
                await pilot.press("l")
            self.assertEqual(len(launches), 1)
            launch = launches[0]
            self.assertEqual(launch["mode"], "tmux")
            self.assertEqual(launch["argv"][:2], ["tmux", "new-window"])
            joined = " ".join(launch["argv"])
            self.assertIn("/s:plan", joined)
            self.assertIn("fresh", joined)

    async def test_run_builds_detached_single_member_driver_argv(self):
        app = dashboard.BoardApp(root="/repo", board_fn=_actions_board)
        async with app.run_test() as pilot:
            launches = self._capture(app)
            _find_card(app, "rdy").focus()
            await pilot.pause()
            await pilot.press("r")
            self.assertEqual(len(launches), 1)
            launch = launches[0]
            self.assertEqual(launch["mode"], "detach")
            self.assertIn("--member", launch["argv"])
            self.assertEqual(
                launch["argv"][launch["argv"].index("--member") + 1], "rdy")

    async def test_open_on_parked_card_builds_resume_argv(self):
        app = dashboard.BoardApp(root="/repo", board_fn=_actions_board)
        async with app.run_test() as pilot:
            launches = self._capture(app)
            _find_card(app, "parked").focus()
            await pilot.pause()
            await pilot.press("o")
            self.assertEqual(len(launches), 1)
            launch = launches[0]
            self.assertIn("--resume", launch["argv"])
            self.assertIn("sess-9", launch["argv"])

    async def test_open_is_absent_while_driving(self):
        app = dashboard.BoardApp(root="/repo", board_fn=_actions_board)
        async with app.run_test() as pilot:
            launches = self._capture(app)
            _find_card(app, "driving").focus()
            await pilot.pause()
            await pilot.press("o")
            self.assertEqual(launches, [])


# ---------------------------------------------------------------------------
# Live auto-refresh: the interval timer re-aggregates and repaints
# ---------------------------------------------------------------------------

def _one_member_board(state):
    epic = {
        "slug": "ep", "status": "active", "theme": None, "initiative": None,
        "members": [{"slug": "m", "description": "d", "risk": "low",
                    "state": state, "location": "/x", "actions": [],
                    "session_id": None}],
        "heartbeat": None, "report": None,
    }
    return {"root": "/x", "generated_at": time.time(), "epics": [epic],
            "groups": [{"initiative": None, "epics": [epic]}]}


class LiveRefreshTest(unittest.IsolatedAsyncioTestCase):
    async def test_interval_refresh_reflects_new_member_state(self):
        # The first call seeds the initial mount; the second (and later)
        # calls simulate the underlying heartbeat/report having changed by
        # the time the interval timer fires again.
        calls = {"n": 0}

        def board_fn():
            calls["n"] += 1
            return _one_member_board("unplanned" if calls["n"] == 1
                                     else "ready")

        # A short interval so the harness's real timer fires promptly.
        app = dashboard.BoardApp(root="/x", interval=0.05, board_fn=board_fn)
        async with app.run_test() as pilot:
            unplanned = app.query_one("#lane-unplanned", dashboard.Lane)
            self.assertTrue(list(unplanned.query(dashboard.TaskCard)))

            await pilot.pause(0.2)  # let the interval timer fire at least once

            ready = app.query_one("#lane-ready", dashboard.Lane)
            self.assertTrue(list(ready.query(dashboard.TaskCard)))
            self.assertFalse(list(unplanned.query(dashboard.TaskCard)))


# ---------------------------------------------------------------------------
# Diff-aware refresh: pure signature helpers + no-repaint / partial-repaint
# behavior of the mounted App
# ---------------------------------------------------------------------------

def _one_card_board(state="ready", stage=None, actions=()):
    """A board with one epic holding a single member ``m``; when ``stage`` is
    given the member is live-driving with that stage (so it lands in
    ``building``/``review`` regardless of ``state``), otherwise its lane
    follows ``state`` — for exercising `_lane_signature`'s sensitivity to
    state/stage/actions."""
    heartbeat = None
    if stage is not None:
        heartbeat = {"epic": "ep", "state": "running", "seq": 1,
                     "updated_at": time.time(),
                     "roster": [{"slug": "m", "state": "driving",
                                "stage": stage}]}
    epic = {
        "slug": "ep", "status": "active", "theme": None, "initiative": None,
        "members": [{"slug": "m", "description": "d", "risk": "low",
                    "state": state, "location": "/x",
                    "actions": list(actions), "session_id": None}],
        "heartbeat": heartbeat, "report": None,
    }
    return {"root": "/x", "generated_at": time.time(), "epics": [epic],
            "groups": [{"initiative": None, "epics": [epic]}]}


def _two_lane_board(mover_state):
    """A board with one epic holding two members: ``mover`` (whose lane
    tracks ``mover_state``) and ``stayer`` (always live-driving the build
    stage, so always in ``building``) — for exercising that moving one
    member's lane leaves an unrelated lane's cards untouched."""
    epic = {
        "slug": "ep", "status": "active", "theme": None, "initiative": None,
        "members": [
            {"slug": "mover", "description": "d", "risk": "low",
             "state": mover_state, "location": "/x", "actions": [],
             "session_id": None},
            {"slug": "stayer", "description": "d", "risk": "low",
             "state": "active", "location": "/x", "actions": [],
             "session_id": "s1"},
        ],
        "heartbeat": {"epic": "ep", "state": "running", "seq": 1,
                      "updated_at": time.time(),
                      "roster": [{"slug": "stayer", "state": "driving",
                                 "stage": "build"}]},
        "report": None,
    }
    return {"root": "/x", "generated_at": time.time(), "epics": [epic],
            "groups": [{"initiative": None, "epics": [epic]}]}


class LaneContentsTest(unittest.TestCase):
    """`_lane_contents` is the pure data `_render_lanes` mounts — one
    ordered list of card specs per lane, with the ``shipped`` lane's cards
    still grouped per epic (consecutive by epic slug, in board order)."""

    def test_orders_members_into_lanes_and_groups_shipped_by_epic(self):
        contents = dashboard._lane_contents(_shipped_board())
        ready_slugs = [member["slug"] for _, _, member, _ in contents["ready"]]
        self.assertEqual(ready_slugs, ["rdy1"])
        shipped = [(epic_slug, member["slug"])
                  for epic_slug, _, member, _ in contents["shipped"]]
        self.assertEqual(shipped, [("es1", "shipped1"), ("es2", "shipped2")])

    def test_kanban_board_lanes_hold_the_right_members(self):
        contents = dashboard._lane_contents(_kanban_board())
        for lane_name, slug in (("building", "driver"), ("ready", "rdy"),
                                ("unplanned", "fresh")):
            slugs = [member["slug"] for _, _, member, _ in contents[lane_name]]
            self.assertEqual(slugs, [slug])
        self.assertEqual(contents["review"], [])
        self.assertEqual(contents["shipped"], [])


class LaneSignatureTest(unittest.TestCase):
    """`_lane_signature` is a hashable, order-sensitive digest of a lane's
    card specs plus the current grouping mode — equal across
    structurally-identical boards under the same mode, and sensitive to
    exactly the fields the render depends on (lane/state/stage/actions/
    group_mode)."""

    def _sig(self, board, lane_name, group_mode="epic", search_query=""):
        # Derive the epic-slug -> initiative-identity map exactly as
        # `_render_lanes` does, so the signature folds in what the group
        # headers render.
        initiative_by_epic = {
            epic.get("slug"): (
                (epic["initiative"].get("slug"),
                 epic["initiative"].get("status"))
                if epic.get("initiative") else None)
            for epic in board.get("epics", [])}
        return dashboard._lane_signature(
            dashboard._lane_contents(board)[lane_name], group_mode,
            search_query, initiative_by_epic)

    def test_equal_for_an_unchanged_board(self):
        for lane_name in ("unplanned", "ready", "building", "shipped"):
            self.assertEqual(self._sig(_kanban_board(), lane_name),
                             self._sig(_kanban_board(), lane_name))

    def test_differs_when_lane_membership_changes(self):
        empty = self._sig(_one_card_board(state="unplanned"), "ready")
        occupied = self._sig(_one_card_board(state="ready"), "ready")
        self.assertNotEqual(empty, occupied)

    def test_differs_when_stage_changes(self):
        building_sig = lambda stage: self._sig(
            _one_card_board(stage=stage), "building")
        self.assertNotEqual(building_sig("build"), building_sig("test"))

    def _build_board(self, stage, updated_at=None):
        """A one-member board whose ``active`` member carries an interactive
        build heartbeat at ``stage``, stamped ``updated_at`` (default: now).
        The member lands in ``building`` either way — live by the heartbeat,
        and by the plain state mapping once it ages out — so a signature
        difference can only come from the folded-in build stage."""
        board = _one_card_board(state="active")
        board["epics"][0]["members"][0]["build_heartbeat"] = {
            "slug": "m", "kind": "build", "state": "running", "stage": stage,
            "updated_at": time.time() if updated_at is None else updated_at}
        return board

    def _building_sig(self, board):
        # Guard that lane membership itself is unchanged, so the assertions
        # below test the folded build stage rather than a card appearing or
        # vanishing from the lane.
        self.assertEqual(len(dashboard._lane_contents(board)["building"]), 1)
        return self._sig(board, "building")

    def test_differs_when_the_live_build_stage_changes(self):
        # An `implement` -> `verify` transition keeps the member in
        # `building`; without the build stage in the signature the lane never
        # repaints and the card's stage suffix freezes (board-live-build-lane).
        self.assertNotEqual(self._building_sig(self._build_board("implement")),
                            self._building_sig(self._build_board("verify")))

    def test_differs_when_the_build_heartbeat_ages_out(self):
        # The liveness flip alone must repaint: the stale card's fallback lane
        # is also `building`, so otherwise a dead build keeps a phantom
        # `· implement` suffix forever.
        stale_at = time.time() - dashboard.BUILD_FRESH_SECONDS - 1
        self.assertNotEqual(
            self._building_sig(self._build_board("implement")),
            self._building_sig(self._build_board("implement",
                                                 updated_at=stale_at)))

    def test_differs_across_the_three_modes(self):
        board = _kanban_board()
        sigs = {self._sig(board, "building", group_mode=mode)
                for mode in ("epic", "initiative", "none")}
        self.assertEqual(len(sigs), 3)

    def test_differs_when_an_epics_initiative_changes(self):
        # Re-tagging the epic to another initiative (or an initiative status
        # change) redraws the group headers, so the signature must differ
        # while a grouping mode is active — and stay equal in flat `none`
        # mode, which renders no initiative.
        plain = _one_card_board(state="ready")
        tagged = _one_card_board(state="ready")
        tagged["epics"][0]["initiative"] = {"slug": "init", "status": "active"}
        for mode in ("epic", "initiative"):
            self.assertNotEqual(
                self._sig(plain, "ready", group_mode=mode),
                self._sig(tagged, "ready", group_mode=mode))
        self.assertEqual(self._sig(plain, "ready", group_mode="none"),
                         self._sig(tagged, "ready", group_mode="none"))

    def test_differs_when_actions_change(self):
        ready_sig = lambda actions: self._sig(
            _one_card_board(state="ready", actions=actions), "ready")
        self.assertNotEqual(ready_sig(("run",)), ready_sig(()))

    def test_equal_for_an_unchanged_board_under_the_same_query(self):
        for lane_name in ("unplanned", "ready", "building", "shipped"):
            self.assertEqual(
                self._sig(_kanban_board(), lane_name, search_query="rdy"),
                self._sig(_kanban_board(), lane_name, search_query="rdy"))

    def test_differs_when_only_the_query_changes(self):
        board = _kanban_board()
        self.assertNotEqual(
            self._sig(board, "ready", search_query="rdy"),
            self._sig(board, "ready", search_query="other"))

    def test_differs_when_only_the_entry_state_changes(self):
        # A needs-human -> driving flip at the same stage must repaint so the
        # stall marker never strands, even though the member's own state and
        # the entry's stage are unchanged.
        member = {"slug": "m", "state": "active", "actions": []}
        cards = lambda entry_state: [
            ("ep", "active", member, {"state": entry_state, "stage": "build"})]
        self.assertNotEqual(
            dashboard._lane_signature(cards("needs-human"), "epic", ""),
            dashboard._lane_signature(cards("driving"), "epic", ""))

    def test_differs_when_a_member_flips_from_driving_to_rejected(self):
        # A parked flip (delivery-dashboard board-parked-member-signal spec)
        # must repaint the lane carrying the card's signal glyph/state label,
        # even at the same stage — the existing entry-state sensitivity
        # already covers this (`entry.get("state")` folds into the
        # signature), documented here for the parked case specifically.
        member = {"slug": "m", "state": "active", "actions": []}
        cards = lambda entry_state: [
            ("ep", "active", member, {"state": entry_state, "stage": "gate"})]
        self.assertNotEqual(
            dashboard._lane_signature(cards("driving"), "epic", ""),
            dashboard._lane_signature(cards("rejected"), "epic", ""))


class SearchHelpersTest(unittest.TestCase):
    """`_search_matches` and `_highlight_slug` are the pure search primitives
    the board's live filter is built from (delivery-dashboard board-search
    spec) — a case-insensitive substring test over the three slugs, and an
    accent-markup wrap of the first matched span."""

    def test_matches_on_member_slug_case_insensitively(self):
        self.assertTrue(dashboard._search_matches(
            "OARD", "ep", None, "board-search"))

    def test_matches_on_epic_slug(self):
        self.assertTrue(dashboard._search_matches(
            "ep", "epic-one", None, "member"))

    def test_matches_on_initiative_slug(self):
        self.assertTrue(dashboard._search_matches(
            "shipd", "epic", {"slug": "shipd-ui"}, "member"))

    def test_empty_or_whitespace_query_matches_everything(self):
        self.assertTrue(dashboard._search_matches("", "ep", None, "m"))
        self.assertTrue(dashboard._search_matches("   ", "ep", None, "m"))

    def test_non_matching_query_is_false(self):
        self.assertFalse(dashboard._search_matches(
            "zzz", "epic", {"slug": "init"}, "member"))

    def test_none_initiative_never_matches(self):
        # A None initiative contributes no field to match against — a query
        # that hits nothing else stays False.
        self.assertFalse(dashboard._search_matches(
            "init", "epic", None, "member"))

    def test_highlight_wraps_the_first_matched_span_in_accent(self):
        self.assertEqual(
            dashboard._highlight_slug("board-search", "search"),
            "board-[$accent]search[/]")

    def test_highlight_is_case_insensitive_but_preserves_slug_case(self):
        self.assertEqual(
            dashboard._highlight_slug("Board-Search", "board"),
            "[$accent]Board[/]-Search")

    def test_highlight_only_wraps_the_first_occurrence(self):
        self.assertEqual(
            dashboard._highlight_slug("ab-ab", "ab"),
            "[$accent]ab[/]-ab")

    def test_highlight_returns_slug_unchanged_for_empty_query(self):
        self.assertEqual(dashboard._highlight_slug("board", ""), "board")
        self.assertEqual(dashboard._highlight_slug("board", "   "), "board")

    def test_highlight_returns_slug_unchanged_when_no_match(self):
        self.assertEqual(dashboard._highlight_slug("board", "zzz"), "board")


class NoRepaintTest(unittest.IsolatedAsyncioTestCase):
    """The regression this change fixes: an unchanged-board refresh must not
    tear down and remount lanes it didn't need to."""

    async def test_unchanged_refresh_retains_same_card_instances(self):
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test() as pilot:
            before = set(app.query(dashboard.TaskCard))
            self.assertTrue(before)
            await app.refresh_board()
            await pilot.pause()
            after = set(app.query(dashboard.TaskCard))
            self.assertEqual(before, after)

    async def test_unchanged_refresh_keeps_a_collapsed_shipped_group_collapsed(
            self):
        app = dashboard.BoardApp(root="/x", board_fn=_shipped_board)
        async with app.run_test() as pilot:
            group = app.query_one("#epic-group-shipped-es1", Collapsible)
            group.collapsed = True
            await pilot.pause()
            await app.refresh_board()
            await pilot.pause()
            group_after = app.query_one("#epic-group-shipped-es1", Collapsible)
            self.assertIs(group, group_after)
            self.assertTrue(group_after.collapsed)

    async def test_unchanged_refresh_keeps_a_collapsed_epic_group_collapsed(
            self):
        # The same guarantee, generalised beyond the (formerly special-
        # cased) shipped lane — a collapsed group in any grouped lane
        # survives an unchanged-board refresh (delivery-dashboard board-tui
        # spec: "A collapsed epic group survives refresh").
        app = dashboard.BoardApp(root="/x", board_fn=_two_epic_board)
        async with app.run_test() as pilot:
            group = app.query_one("#epic-group-ready-ep1", Collapsible)
            group.collapsed = True
            await pilot.pause()
            await app.refresh_board()
            await pilot.pause()
            group_after = app.query_one("#epic-group-ready-ep1", Collapsible)
            self.assertIs(group, group_after)
            self.assertTrue(group_after.collapsed)

    async def test_moving_member_lane_rebuilds_only_affected_lanes(self):
        calls = {"n": 0}

        def board_fn():
            calls["n"] += 1
            return _two_lane_board(
                "unplanned" if calls["n"] == 1 else "ready")

        app = dashboard.BoardApp(root="/x", board_fn=board_fn)
        async with app.run_test() as pilot:
            building_before = set(
                app.query_one("#lane-building", dashboard.Lane)
                   .query(dashboard.TaskCard))
            self.assertTrue(building_before)

            await app.refresh_board()
            await pilot.pause()

            building_after = set(
                app.query_one("#lane-building", dashboard.Lane)
                   .query(dashboard.TaskCard))
            self.assertEqual(building_before, building_after)
            self.assertFalse(list(
                app.query_one("#lane-unplanned", dashboard.Lane)
                   .query(dashboard.TaskCard)))
            ready_slugs = [c.member["slug"] for c in
                          app.query_one("#lane-ready", dashboard.Lane)
                             .query(dashboard.TaskCard)]
            self.assertEqual(ready_slugs, ["mover"])


class ShipdThemeTests(unittest.IsolatedAsyncioTestCase):
    """The Shipd design-system palette is registered as a custom ``textual``
    theme (``shipd``) and activated on startup, and its lane/risk colors are
    exposed as named theme variables — the single palette source that the
    widget CSS references (delivery-dashboard board-shipd-theme spec)."""

    async def test_shipd_theme_registered_and_active(self):
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test():
            self.assertEqual(app.theme, "shipd")
            self.assertIn("shipd", app.available_themes)

    def test_theme_exposes_lane_and_risk_variables(self):
        variables = dashboard.SHIPD_THEME.variables
        self.assertEqual(variables["lane-unplanned"], "#8888A0")
        self.assertEqual(variables["lane-ready"], "#4DA6FF")
        self.assertEqual(variables["lane-building"], "#FF8C42")
        self.assertEqual(variables["lane-review"], "#9B7FFF")
        self.assertEqual(variables["lane-shipped"], "#3DCC8E")
        self.assertEqual(variables["risk-high"], "#FF8C42")
        self.assertEqual(variables["risk-medium"], "#C6FF4E")
        self.assertEqual(variables["risk-low"], "#55556A")
        for key in ("shipd-border", "shipd-border-strong", "bg-hover",
                    "bg-active", "accent-dim", "fg-muted", "fg-subtle"):
            self.assertIn(key, variables)

    async def test_scrollbar_variables_pin_the_muted_tones(self):
        # The theme overrides textual's accent-derived scrollbar colors: the
        # resolved CSS variables pin the thumb/hover/active/track/corner to the
        # design system's muted border tones (board-scrollbar-theme spec).
        app = dashboard.BoardApp(root="/x", board_fn=_kanban_board)
        async with app.run_test():
            cssvars = app.get_css_variables()
            self.assertEqual(
                Color.parse(cssvars["scrollbar"]).rgb,
                Color.parse("#3E3E52").rgb)
            for key in ("scrollbar-hover", "scrollbar-active"):
                self.assertEqual(
                    Color.parse(cssvars[key]).rgb,
                    Color.parse("#55556A").rgb)
            for key in ("scrollbar-background", "scrollbar-background-hover",
                        "scrollbar-background-active", "scrollbar-corner-color"):
                self.assertEqual(
                    Color.parse(cssvars[key]).rgb,
                    Color.parse("#1C1C26").rgb)

    def test_widget_css_carries_no_hard_coded_colors(self):
        blocks = {
            "BoardApp": dashboard.BoardApp.CSS,
            "MemberDetailScreen": dashboard.MemberDetailScreen.CSS,
            "EpicRunConfirmScreen": dashboard.EpicRunConfirmScreen.CSS,
            "EpicDetailScreen": dashboard.EpicDetailScreen.CSS,
        }
        for name, css in blocks.items():
            self.assertIsNone(
                re.search(r"#[0-9a-fA-F]{3,8}\b", css),
                "%s.CSS carries a hex color literal" % name)
            self.assertIsNone(
                re.search(r"\b(black|white)\b", css),
                "%s.CSS carries a named color token" % name)
            self.assertIsNone(
                re.search(r"\bround\b", css),
                "%s.CSS carries a round border style" % name)

    def test_board_css_uses_theme_surfaces_for_epic_groups(self):
        css = dashboard.BoardApp.CSS
        row = re.search(r"\.epic-group-row\s*\{[^}]*\}", css).group(0)
        self.assertIn("$shipd-border", row)
        group = re.search(r"\.epic-group\s*\{[^}]*\}", css).group(0)
        self.assertIn("background: $panel", group)


# ---------------------------------------------------------------------------
# Session-activity charts: shared fixture helpers
# ---------------------------------------------------------------------------

_BLOCKS = "▁▂▃▄▅▆▇█"


def _activity_rec(msg_id, ts, output):
    return {"type": "assistant", "timestamp": ts,
            "message": {"id": msg_id, "model": "m",
                        "usage": {"output_tokens": output}}}


class ActivityFixtureBase(unittest.IsolatedAsyncioTestCase):
    """Base for the activity-chart tests: an isolated CLAUDE_CONFIG_DIR plus a
    helper that writes a session transcript at the exact path the build-report
    resolvers expect for a member location. The real ~/.claude is never read."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="activity-root-")
        self.config = tempfile.mkdtemp(prefix="activity-cfg-")
        self._old_cfg = os.environ.get("CLAUDE_CONFIG_DIR")
        os.environ["CLAUDE_CONFIG_DIR"] = self.config

    def tearDown(self):
        if self._old_cfg is None:
            os.environ.pop("CLAUDE_CONFIG_DIR", None)
        else:
            os.environ["CLAUDE_CONFIG_DIR"] = self._old_cfg
        shutil.rmtree(self.root, ignore_errors=True)
        shutil.rmtree(self.config, ignore_errors=True)

    def _write_transcript(self, location, session_id, records):
        tdir = os.path.join(self.config, "projects", br.project_slug(location))
        os.makedirs(tdir, exist_ok=True)
        path = os.path.join(tdir, session_id + ".jsonl")
        with open(path, "a", encoding="utf-8") as fh:
            for r in records:
                fh.write(json.dumps(r) + "\n")
        return path


def _throughput_board(root, *, driving, session_id="sess-live"):
    """A one-epic, one-member board where the member is (or isn't) driving.
    When driving, its heartbeat roster entry and member row carry
    ``session_id`` and the member's ``location`` is ``root`` — so the header
    chart's MultiTail resolves its transcript under the isolated config dir."""
    entry = {"slug": "m", "state": "driving" if driving else "needs-human",
             "stage": "build", "attempt": 1}
    if driving:
        entry["session_id"] = session_id
    member = {"slug": "m", "description": "d", "risk": "low",
              "state": "active", "location": root, "actions": [],
              "session_id": session_id if driving else None}
    epic = {"slug": "ep", "status": "active", "theme": None,
            "initiative": None, "members": [member],
            "heartbeat": {"epic": "ep", "state": "running", "seq": 1,
                          "updated_at": time.time(), "roster": [entry]},
            "report": None}
    return {"root": root, "generated_at": time.time(), "epics": [epic],
            "groups": [{"initiative": None, "epics": [epic]}]}


class HeaderThroughputChartTest(ActivityFixtureBase):
    """The board header carries a live 15-column throughput chart summed across
    driving members' sessions (delivery-dashboard board-throughput-chart)."""

    async def test_driving_session_renders_throughput(self):
        self._write_transcript(
            self.root, "sess-live",
            [_activity_rec("a", "2026-01-01T00:00:10Z", 5000)])
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _throughput_board(self.root, driving=True))
        async with app.run_test():
            chart = app.query_one(dashboard.HeaderChart)
            chart._tick()
            text = str(chart.render())
            self.assertTrue(any(b in text for b in _BLOCKS),
                            "expected non-blank eighth-block cells")
            self.assertIn(br.fmt_tokens(5000), text)  # newest bucket value

    async def test_no_driving_members_render_blank(self):
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _throughput_board(self.root, driving=False))
        async with app.run_test():
            chart = app.query_one(dashboard.HeaderChart)
            chart._tick()  # must not raise
            text = str(chart.render())
            self.assertFalse(any(b in text for b in _BLOCKS),
                             "expected blank cells with no driving session")

    async def test_clicking_chart_opens_config_dialog(self):
        app = dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _throughput_board(self.root, driving=False))
        async with app.run_test(size=(120, 24)) as pilot:
            chart = app.query_one(dashboard.HeaderChart)
            await pilot.click(chart)
            self.assertIsInstance(app.screen, dashboard.GraphConfigScreen)


class GraphConfigDialogTest(ActivityFixtureBase):
    """The graph config dialog (delivery-dashboard graph-config-dialog): a
    3-row throughput chart with detail plus three segmented setting rows whose
    values arrow keys change, applied immediately to the app's chart state."""

    def _app(self):
        return dashboard.BoardApp(
            root=self.root,
            board_fn=lambda: _throughput_board(self.root, driving=False))

    async def _open_dialog(self, app, pilot):
        app.push_screen(dashboard.GraphConfigScreen())
        await pilot.pause()

    async def test_dialog_shows_three_setting_rows(self):
        app = self._app()
        async with app.run_test() as pilot:
            await self._open_dialog(app, pilot)
            rows = app.screen.query(".graph-setting-row")
            self.assertEqual(len(rows), 3)

    async def test_arrow_keys_move_selection_and_change_window(self):
        app = self._app()
        async with app.run_test() as pilot:
            await self._open_dialog(app, pilot)
            self.assertEqual(app.chart_state["bucket_seconds"], 3)
            # Move the row selection down then back up to the window row, then
            # step its value right to 90s (6-second buckets).
            await pilot.press("down")
            await pilot.press("up")
            await pilot.press("right")
            self.assertEqual(app.chart_state["bucket_seconds"], 6)

    async def test_height_governs_header_form(self):
        app = self._app()
        async with app.run_test(size=(120, 24)) as pilot:
            await self._open_dialog(app, pilot)
            # Move to the height row (second) and switch to "1 row".
            await pilot.press("down")
            await pilot.press("right")
            self.assertEqual(app.chart_state["rows"], 1)
            header = app.query_one(dashboard.HeaderChart)
            self.assertEqual(len(str(header.render()).split("\n")), 1)
            dialog_chart = app.screen.query_one(
                "#graph-dialog-chart", dashboard.ActivityChart)
            self.assertEqual(len(str(dialog_chart.render()).split("\n")), 3)

    async def test_escape_dismisses(self):
        app = self._app()
        async with app.run_test() as pilot:
            await self._open_dialog(app, pilot)
            self.assertIsInstance(app.screen, dashboard.GraphConfigScreen)
            await pilot.press("escape")
            await pilot.pause()
            self.assertNotIsInstance(app.screen, dashboard.GraphConfigScreen)

    async def test_every_option_is_visible_and_clickable(self):
        app = self._app()
        async with app.run_test(size=(120, 24)) as pilot:
            await self._open_dialog(app, pilot)
            # Every option of every setting row has a visible (non-empty)
            # region — the old width:100% pushed siblings to zero width.
            options = list(app.screen.query(dashboard.GraphOption))
            self.assertEqual(len(options), 3 + 2 + 2)
            for opt in options:
                self.assertGreater(opt.region.width, 0)
                self.assertGreater(opt.region.height, 0)
            # Clicking a non-selected option (3m -> 12-second buckets) applies.
            three_m = next(
                o for o in options
                if o.setting_key == "bucket_seconds" and o.setting_value == 12)
            await pilot.click(three_m)
            self.assertEqual(app.chart_state["bucket_seconds"], 12)

    async def test_close_control_dismisses(self):
        app = self._app()
        async with app.run_test(size=(120, 24)) as pilot:
            await self._open_dialog(app, pilot)
            self.assertIsInstance(app.screen, dashboard.GraphConfigScreen)
            close = app.screen.query_one("#graph-config-close", Button)
            await pilot.click(close)
            await pilot.pause()
            self.assertNotIsInstance(app.screen, dashboard.GraphConfigScreen)

    async def test_repeated_opens_never_stack(self):
        app = self._app()
        async with app.run_test(size=(120, 24)) as pilot:
            chart = app.query_one(dashboard.HeaderChart)
            # Two clicks in quick succession must leave exactly one dialog.
            chart.on_click(None)
            await pilot.pause()
            chart.on_click(None)
            await pilot.pause()
            stacked = sum(
                isinstance(s, dashboard.GraphConfigScreen)
                for s in app.screen_stack)
            self.assertEqual(stacked, 1)
            # A single Escape returns to the board.
            await pilot.press("escape")
            await pilot.pause()
            self.assertNotIsInstance(app.screen, dashboard.GraphConfigScreen)


class MemberModalActivityTest(ActivityFixtureBase):
    """The spec-detail modal shows a live activity panel between its header and
    its tabs for a member whose session transcript resolves (delivery-dashboard
    session-activity-timeline), and no panel when none does."""

    def _board(self):
        return _throughput_board(self.root, driving=False)

    def _push(self, app, member, entry):
        app.push_screen(
            dashboard.MemberDetailScreen("ep", member, entry, "active"))

    @staticmethod
    def _screen_text(app):
        return "\n".join(
            str(w.render()) for w in app.screen.query(dashboard.Static))

    async def test_driving_member_shows_live_chart(self):
        self._write_transcript(self.root, "sess-live", [
            _activity_rec("a", "2026-01-01T00:00:10Z", 400),
            _activity_rec("b", "2026-01-01T00:01:00Z", 300),
        ])
        member = {"slug": "m", "risk": "low", "state": "active",
                  "location": self.root, "session_id": "sess-live",
                  "actions": ["open"]}
        entry = {"slug": "m", "state": "driving", "stage": "build",
                 "attempt": 1, "session_id": "sess-live"}
        app = dashboard.BoardApp(root=self.root, board_fn=self._board)
        async with app.run_test() as pilot:
            self._push(app, member, entry)
            await pilot.pause()
            self.assertTrue(app.screen.query("#member-activity-chart"))
            text = self._screen_text(app)
            self.assertTrue(any(b in text for b in _BLOCKS),
                            "expected eighth-block cells in the panel")
            self.assertIn("session 700", text)  # session token total

    async def test_no_session_no_panel(self):
        member = {"slug": "m", "risk": "low", "state": "rejected",
                  "location": self.root, "session_id": None, "actions": []}
        entry = {"slug": "m", "state": "needs-human"}
        app = dashboard.BoardApp(root=self.root, board_fn=self._board)
        async with app.run_test() as pilot:
            self._push(app, member, entry)
            await pilot.pause()
            self.assertEqual(
                list(app.screen.query("#member-activity-chart")), [])

    async def test_refresh_handler_updates_panel(self):
        self._write_transcript(self.root, "sess-live", [
            _activity_rec("a", "2026-01-01T00:00:10Z", 400)])
        member = {"slug": "m", "risk": "low", "state": "active",
                  "location": self.root, "session_id": "sess-live",
                  "actions": ["open"]}
        entry = {"slug": "m", "state": "driving", "session_id": "sess-live"}
        app = dashboard.BoardApp(root=self.root, board_fn=self._board)
        async with app.run_test() as pilot:
            self._push(app, member, entry)
            await pilot.pause()
            self.assertIn("session 400", self._screen_text(app))
            # Append a new record and invoke the screen's refresh handler.
            self._write_transcript(self.root, "sess-live", [
                _activity_rec("b", "2026-01-01T00:01:00Z", 300)])
            app.screen._refresh_activity()
            await pilot.pause()
            self.assertIn("session 700", self._screen_text(app))

    def _plant_tasks(self, slug, done, total):
        """Write a ``tasks.md`` under the member's location with ``done`` of
        ``total`` checkboxes checked, so ``count_tasks`` resolves the progress."""
        path = os.path.join(self.root, ".shipd", "planned", slug, "tasks.md")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        lines = ["- [x] done %d" % i for i in range(done)]
        lines += ["- [ ] todo %d" % i for i in range(total - done)]
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")

    @staticmethod
    def _progress_text(app):
        widgets = list(app.screen.query("#member-activity-progress"))
        return str(widgets[0].render()) if widgets else None

    async def test_progress_line_shows_elapsed_and_task_progress(self):
        self._write_transcript(self.root, "sess-live", [
            _activity_rec("a", "2026-01-01T00:00:10Z", 400)])
        self._plant_tasks("m", done=4, total=11)
        member = {"slug": "m", "risk": "low", "state": "active",
                  "location": self.root, "session_id": "sess-live",
                  "actions": ["open"]}
        entry = {"slug": "m", "state": "driving", "stage": "build",
                 "attempt": 1, "session_id": "sess-live",
                 "started_at": time.time() - 125}
        app = dashboard.BoardApp(root=self.root, board_fn=self._board)
        async with app.run_test() as pilot:
            self._push(app, member, entry)
            await pilot.pause()
            text = self._progress_text(app)
            self.assertIsNotNone(text, "progress line should be mounted")
            self.assertIn("elapsed", text)
            self.assertIn("4/11", text)

    async def test_one_row_gap_separates_detail_from_tabs(self):
        # A driving member with a resolvable session (activity panel + detail
        # line) and an on-disk tasks.md (so the artifact TabbedContent renders):
        # a one-row gap must separate the detail line from the tab strip.
        self._write_transcript(self.root, "sess-live", [
            _activity_rec("a", "2026-01-01T00:00:10Z", 400)])
        self._plant_tasks("m", done=4, total=11)
        member = {"slug": "m", "risk": "low", "state": "active",
                  "location": self.root, "session_id": "sess-live",
                  "actions": ["open"]}
        entry = {"slug": "m", "state": "driving", "session_id": "sess-live"}
        app = dashboard.BoardApp(root=self.root, board_fn=self._board)
        async with app.run_test(size=(120, 40)) as pilot:
            self._push(app, member, entry)
            await pilot.pause()
            detail = app.screen.query_one("#member-activity-detail")
            tabs = app.screen.query_one(TabbedContent)
            self.assertGreaterEqual(
                tabs.region.y - detail.region.bottom, 1,
                "expected a one-row gap between the detail line (%r) and the "
                "artifact tabs (%r)" % (detail.region, tabs.region))

    async def test_missing_started_at_omits_elapsed(self):
        self._write_transcript(self.root, "sess-live", [
            _activity_rec("a", "2026-01-01T00:00:10Z", 400)])
        self._plant_tasks("m", done=4, total=11)
        member = {"slug": "m", "risk": "low", "state": "active",
                  "location": self.root, "session_id": "sess-live",
                  "actions": ["open"]}
        entry = {"slug": "m", "state": "driving", "stage": "build",
                 "attempt": 1, "session_id": "sess-live"}
        app = dashboard.BoardApp(root=self.root, board_fn=self._board)
        async with app.run_test() as pilot:
            self._push(app, member, entry)
            await pilot.pause()
            text = self._progress_text(app)
            self.assertIsNotNone(text, "progress line should be mounted")
            self.assertNotIn("elapsed", text)
            self.assertIn("4/11", text)  # tasks still shown


# ---------------------------------------------------------------------------
# Standalone changes on the board (delivery-dashboard board-standalone-changes)
# ---------------------------------------------------------------------------

def _standalone_board(state="active"):
    """A board carrying one standalone change (no epic) — with ``state:
    active`` it maps to the ``building`` lane — and no epics/groups, exercising
    the standalone group rendering in isolation."""
    standalone = [{"slug": "solo", "description": "", "risk": None,
                   "state": state, "location": "/x", "actions": []}]
    return {
        "root": "/x", "generated_at": time.time(),
        "epics": [], "groups": [], "standalone": standalone,
    }


class StandaloneBoardAggregationTest(DashboardTestBase):
    """``build_board`` discovers standalone changes — those planned outside any
    epic — and exposes them on a top-level ``standalone`` list with empty
    actions, excluding any slug adopted into an epic's stub table (delivery-
    dashboard board-standalone-changes spec)."""

    def test_standalone_worktree_change_appears_with_empty_actions(self):
        _plan(self.root, "solo", "active",
              rel=os.path.join(".worktrees", "solo"))
        board = dashboard.build_board(self.root)
        by_slug = {s["slug"]: s for s in board["standalone"]}
        self.assertIn("solo", by_slug)
        solo = by_slug["solo"]
        self.assertEqual(solo["state"], "active")
        self.assertEqual(solo["actions"], [])
        self.assertTrue(solo["location"].endswith("solo"))
        self.assertIn(".worktrees", solo["location"])

    def test_epic_member_slug_is_not_double_listed_as_standalone(self):
        _make_epic(self.root, "ep", [("adopted", "a member", "low")],
                   status="active")
        _plan(self.root, "adopted", "active",
              rel=os.path.join(".worktrees", "adopted"))
        board = dashboard.build_board(self.root)
        self.assertNotIn(
            "adopted", {s["slug"] for s in board["standalone"]})
        self.assertIn(
            "adopted",
            {m["slug"] for e in board["epics"] for m in e["members"]})


class StandaloneRenderTest(unittest.IsolatedAsyncioTestCase):
    """Standalone changes render as normal cards under a ``standalone`` group
    (epic mode) or flat (none mode), the group header carries the count but no
    run/open controls, and standalone content folds into the diff-aware lane
    signatures (delivery-dashboard board-standalone-changes spec)."""

    async def test_epic_mode_standalone_group_carries_count_no_controls(self):
        app = dashboard.BoardApp(root="/x", board_fn=_standalone_board)
        async with app.run_test(size=(120, 24)):
            group = app.query_one(
                "#epic-group-building-standalone", Collapsible)
            # The count rides the title as a muted ` (1)` suffix (delivery-
            # dashboard board-epic-grouping spec), so no `.epic-count` element
            # trails the group.
            self.assertTrue(group.title.startswith("standalone"))
            self.assertTrue(group.title.endswith("[$fg-muted](1)[/]"))
            self.assertFalse(app.query(".epic-count"))
            self.assertEqual(
                [c.member["slug"] for c in group.query(dashboard.TaskCard)],
                ["solo"])

    async def test_none_mode_renders_standalone_cards_flat(self):
        app = dashboard.BoardApp(root="/x", board_fn=_standalone_board)
        async with app.run_test() as pilot:
            await pilot.press("g")  # epic -> initiative
            await pilot.press("g")  # initiative -> none
            self.assertEqual(app.group_mode, "none")
            lane = app.query_one("#lane-building", dashboard.Lane)
            self.assertFalse(lane.query(Collapsible))
            self.assertEqual(
                [c.member["slug"] for c in lane.query(dashboard.TaskCard)],
                ["solo"])

    async def test_removing_a_standalone_change_repaints_the_lane(self):
        state = {"board": _standalone_board()}
        app = dashboard.BoardApp(root="/x", board_fn=lambda: state["board"])
        async with app.run_test():
            lane = app.query_one("#lane-building", dashboard.Lane)
            self.assertTrue(
                any(c.member["slug"] == "solo"
                    for c in lane.query(dashboard.TaskCard)))
            sig_before = app._lane_sigs["building"]
            gone = _standalone_board()
            gone["standalone"] = []
            state["board"] = gone
            await app.refresh_board()
            self.assertNotEqual(app._lane_sigs["building"], sig_before)
            self.assertFalse(
                any(c.member["slug"] == "solo"
                    for c in lane.query(dashboard.TaskCard)))


class StandaloneModalTest(unittest.IsolatedAsyncioTestCase):
    """A standalone card opens the standard spec-detail modal, resolving its
    artifacts from the change's worktree hosting location (delivery-dashboard
    board-standalone-changes spec)."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="standalone-modal-test-")
        self._base_home = tempfile.mkdtemp(prefix="standalone-home-")
        self._old_home = os.environ.get("HOME")
        os.environ["HOME"] = self._base_home

    def tearDown(self):
        if self._old_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = self._old_home
        shutil.rmtree(self._base_home, ignore_errors=True)
        shutil.rmtree(self.root, ignore_errors=True)

    async def test_standalone_card_resolves_artifacts_from_worktree(self):
        wt = os.path.join(self.root, ".worktrees", "solo")
        change_dir = os.path.join(wt, ".shipd", "planned", "solo")
        _write(os.path.join(change_dir, "plan.md"),
               "# solo\nStatus: active\n\n## Idea\n\nx\n")
        _write(os.path.join(change_dir, "specs", "cap", "spec.md"),
               "# cap spec\n")
        _write(os.path.join(change_dir, "tasks.md"), "## 1\n- [ ] 1.1 x\n")
        app = dashboard.BoardApp(
            root=self.root, board_fn=lambda: dashboard.build_board(self.root))
        async with app.run_test(size=(120, 24)) as pilot:
            lane = app.query_one("#lane-building", dashboard.Lane)
            card = next(c for c in lane.query(dashboard.TaskCard)
                        if c.member["slug"] == "solo")
            await pilot.click(card)
            self.assertIsInstance(app.screen, dashboard.MemberDetailScreen)
            self.assertEqual(app.screen.member["slug"], "solo")
            labels = [a["label"] for a in app.screen._artifacts]
            self.assertIn("Plan", labels)
            self.assertIn("Tasks", labels)


if __name__ == "__main__":
    unittest.main()
