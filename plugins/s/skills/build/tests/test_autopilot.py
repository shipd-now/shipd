#!/usr/bin/env python3
"""Tests for autopilot.py — the epic autopilot driver.

Two layers, both free of live sessions: the pure member-selection / report /
dry-run logic here plus (further down) stage execution over injected
runner/gate/command seams. No test spawns a ``claude`` process — every session,
gate, and command boundary is injected.
"""

import json
import os
import shutil
import signal
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
sys.path.insert(0, SCRIPTS)

import autopilot  # noqa: E402
import heartbeat  # noqa: E402
import session_driver  # noqa: E402
import spec_status as ss  # noqa: E402


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

EPIC_HEADER = (
    "| Change | Description | Code | Integration | Unknowns | Risk |\n"
    "| --- | --- | --- | --- | --- | --- |\n")


def _member_row(slug, risk, desc="a member"):
    return "| %s | %s | low | low | low | %s |\n" % (slug, desc, risk)


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def _make_epic(root, slug, rows, status="ready"):
    """Write ``.shipd/epics/<slug>/epic.md`` with a stub table of ``rows`` —
    each a ``(member_slug, risk)`` pair."""
    body = ["# %s\n" % slug, "Status: %s\n" % status, "\n",
            "## Changes\n", "\n", EPIC_HEADER]
    for member, risk in rows:
        body.append(_member_row(member, risk))
    _write(os.path.join(root, ".shipd", "epics", slug, "epic.md"), "".join(body))


def _plant_planned(root, slug, status):
    """Create a planned member change at ``status``."""
    _write(os.path.join(root, ".shipd", "planned", slug, "plan.md"),
           "# %s\nStatus: %s\n\n## Idea\n\nx\n" % (slug, status))


def _plant_archived(root, slug):
    os.makedirs(os.path.join(root, ".shipd", "completed", "001-" + slug),
                exist_ok=True)


class AutopilotTestBase(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="autopilot-test-")
        self._base_home = tempfile.mkdtemp(prefix="autopilot-home-")
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
# Member selection and ordering (pure)
# ---------------------------------------------------------------------------

class SelectionTest(unittest.TestCase):
    def _m(self, slug, risk, state="unplanned", order=0):
        return autopilot.Member(slug=slug, description="", risk=risk,
                                 state=state, order=order)

    def test_orders_risk_ascending_with_table_order_ties(self):
        members = [
            self._m("hi", "high", order=0),
            self._m("lo", "low", order=1),
            self._m("mid", "medium", order=2),
            self._m("lo2", "low", order=3),
        ]
        to_drive, skipped = autopilot.select_and_order(members)
        self.assertEqual([m.slug for m in to_drive],
                         ["lo", "lo2", "mid", "hi"])
        self.assertEqual(skipped, [])

    def test_non_unplanned_members_are_skipped_under_state(self):
        members = [
            self._m("done", "low", state="archived", order=0),
            self._m("go", "low", state="unplanned", order=1),
            self._m("bounced", "high", state="rejected", order=2),
            self._m("building", "medium", state="active", order=3),
        ]
        to_drive, skipped = autopilot.select_and_order(members)
        self.assertEqual([m.slug for m in to_drive], ["go"])
        self.assertEqual({(m.slug, m.state) for m in skipped},
                         {("done", "archived"), ("bounced", "rejected"),
                          ("building", "active")})


# ---------------------------------------------------------------------------
# parse_members reads risk from the stub table
# ---------------------------------------------------------------------------

class ParseMembersTest(AutopilotTestBase):
    def test_reads_risk_and_derives_state(self):
        _make_epic(self.root, "ep",
                   [("m-un", "high"), ("m-rej", "low"), ("m-arch", "medium")])
        _plant_planned(self.root, "m-rej", "rejected")
        _plant_archived(self.root, "m-arch")
        members = autopilot.parse_members(self.root, "ep")
        by = {m.slug: m for m in members}
        self.assertEqual(by["m-un"].risk, "high")
        self.assertEqual(by["m-un"].state, "unplanned")
        self.assertEqual(by["m-rej"].state, "rejected")
        self.assertEqual(by["m-arch"].state, "archived")


# ---------------------------------------------------------------------------
# run(): dry-run, max-members, and report accounting (injected member driver)
# ---------------------------------------------------------------------------

class RunTest(AutopilotTestBase):
    def test_dry_run_drives_nothing(self):
        _make_epic(self.root, "ep", [("a", "low"), ("b", "high")])
        calls = []
        lines = []

        def spy_driver(root, epic, member, pipeline):
            calls.append(member.slug)
            return autopilot.MemberResult(outcome="shipped")

        autopilot.run(self.root, "ep", dry_run=True, member_driver=spy_driver,
                      out=lines.append)
        self.assertEqual(calls, [])  # nothing driven
        text = "\n".join(lines)
        # Member order (risk-ascending) and the resolved pipeline both printed.
        self.assertIn("a", text)
        self.assertIn("b", text)
        self.assertIn("plan", text)

    def test_max_members_reaches_one_rest_unreached(self):
        _make_epic(self.root, "ep",
                   [("a", "low"), ("b", "medium"), ("c", "high")])
        calls = []

        def driver(root, epic, member, pipeline, heartbeat=None):
            calls.append(member.slug)
            return autopilot.MemberResult(outcome="shipped",
                                          pr_url="http://pr/" + member.slug)

        report = autopilot.run(self.root, "ep", max_members=1,
                               member_driver=driver, out=lambda *_: None)
        self.assertEqual(calls, ["a"])  # only the first, lowest-risk member
        self.assertEqual([r["member"] for r in report["shipped"]], ["a"])
        self.assertEqual({r["member"] for r in report["unreached"]},
                         {"b", "c"})

    def test_report_accounts_for_every_member(self):
        _make_epic(self.root, "ep",
                   [("ship", "low"), ("bad", "low"), ("hitl", "medium"),
                    ("later", "high"), ("skip", "low")])
        _plant_planned(self.root, "skip", "rejected")  # already in-flight

        outcomes = {
            "ship": autopilot.MemberResult(outcome="shipped",
                                           pr_url="http://pr/ship"),
            "bad": autopilot.MemberResult(outcome="rejected", stage="gate",
                                          reason="insufficient context"),
            "hitl": autopilot.MemberResult(outcome="needs_human", stage="build",
                                           reason="grade unmet",
                                           session_id="sess-9"),
        }

        def driver(root, epic, member, pipeline, heartbeat=None):
            return outcomes[member.slug]

        report = autopilot.run(self.root, "ep", max_members=3,
                               member_driver=driver, sync_fn=lambda *a, **k: None,
                               out=lambda *_: None)

        self.assertEqual([r["member"] for r in report["shipped"]], ["ship"])
        self.assertEqual(report["shipped"][0]["pr_url"], "http://pr/ship")
        self.assertEqual([r["member"] for r in report["rejected"]], ["bad"])
        self.assertEqual([r["member"] for r in report["needs_human"]], ["hitl"])
        self.assertEqual(report["needs_human"][0]["session_id"], "sess-9")
        self.assertEqual([r["member"] for r in report["skipped"]], ["skip"])
        self.assertEqual([r["member"] for r in report["skipped"]][0], "skip")
        self.assertEqual([r["member"] for r in report["unreached"]], ["later"])

        # Every one of the five members is accounted for exactly once.
        seen = []
        for bucket in ("shipped", "rejected", "needs_human", "skipped",
                       "unreached"):
            seen += [r["member"] for r in report[bucket]]
        self.assertEqual(sorted(seen),
                         ["bad", "hitl", "later", "ship", "skip"])

    def test_rejected_report_entry_carries_session_id(self):
        _make_epic(self.root, "ep", [("bad", "low")])

        def driver(root, epic, member, pipeline, heartbeat=None):
            return autopilot.MemberResult(
                outcome="rejected", stage="gate",
                reason="context insufficient after oracle enrichment",
                session_id="sess-enrich-7")

        report = autopilot.run(self.root, "ep", member_driver=driver,
                               sync_fn=lambda *a, **k: None, out=lambda *_: None)
        self.assertEqual(report["rejected"][0]["session_id"], "sess-enrich-7")

    def test_summary_prints_resume_pointer_for_rejected_with_session(self):
        report = {
            "epic": "ep", "shipped": [], "needs_human": [], "skipped": [],
            "unreached": [],
            "rejected": [{"member": "bad", "stage": "gate",
                          "reason": "context insufficient after oracle "
                                    "enrichment", "session_id": "sess-enrich-7"}],
        }
        lines = []
        autopilot._summarize(report, lines.append)
        text = "\n".join(lines)
        self.assertIn("claude --resume sess-enrich-7", text)

    def test_needs_human_without_session_omits_resume_pointer(self):
        report = {
            "epic": "ep", "shipped": [], "rejected": [], "skipped": [],
            "unreached": [],
            "needs_human": [{"member": "stuck", "stage": "worktree",
                             "reason": "worktree creation failed",
                             "session_id": None}],
        }
        lines = []
        autopilot._summarize(report, lines.append)
        text = "\n".join(lines)
        self.assertIn("needs-human: stuck", text)
        self.assertIn("worktree creation failed", text)
        self.assertNotIn("claude --resume", text)

    def test_needs_human_with_session_keeps_resume_pointer(self):
        report = {
            "epic": "ep", "shipped": [], "rejected": [], "skipped": [],
            "unreached": [],
            "needs_human": [{"member": "stuck", "stage": "build",
                             "reason": "three strikes",
                             "session_id": "sess-9"}],
        }
        lines = []
        autopilot._summarize(report, lines.append)
        self.assertIn("claude --resume sess-9", "\n".join(lines))

    def test_preflight_refuses_non_ready_epic(self):
        _make_epic(self.root, "ep", [("a", "low")], status="draft")
        with self.assertRaises(autopilot.AutopilotError):
            autopilot.run(self.root, "ep", member_driver=lambda *a: None,
                          out=lambda *_: None)


# ---------------------------------------------------------------------------
# Epic close-out sync (_default_sync_fn over a faked _run_command)
# ---------------------------------------------------------------------------


class _FakeRunCommand:
    """Records (argv, cwd) calls and returns scripted (rc, out, err) tuples."""

    def __init__(self, results):
        self.calls = []
        self.results = list(results)

    def __call__(self, cmd, cwd):
        self.calls.append((cmd, cwd))
        if self.results:
            return self.results.pop(0)
        return 0, "", ""


class CloseOutSyncTest(unittest.TestCase):
    def run_sync(self, results):
        fake = _FakeRunCommand(results)
        original = autopilot._run_command
        autopilot._run_command = fake
        lines = []
        try:
            autopilot._default_sync_fn("/repo", "ep", lines.append)
        finally:
            autopilot._run_command = original
        return fake, lines

    def test_close_out_worktree_is_created_fresh(self):
        # The close-out must never adopt a stale local change/epic-close-<slug>
        # branch left by an earlier run, so the helper carries --fresh.
        fake, _lines = self.run_sync(
            [(0, "", ""), (0, "active", ""), (0, "", "")])
        self.assertEqual(
            fake.calls[0][0],
            [autopilot.WORKTREE_SH, "epic-close-ep", "--fresh"])

    def test_sync_invocation_places_root_before_subcommand(self):
        fake, _lines = self.run_sync(
            [(0, "", ""), (0, "active", ""), (0, "", "")])
        argv = fake.calls[1][0]
        self.assertIn("--root", argv)
        self.assertIn("epic-sync", argv)
        self.assertLess(argv.index("--root"), argv.index("epic-sync"))

    def test_noop_sync_removes_worktree_and_branch(self):
        wt = os.path.join("/repo", ".worktrees", "epic-close-ep")
        fake, _lines = self.run_sync(
            [(0, "", ""), (0, "active", ""), (0, "", "")])
        flat = [c[0] for c in fake.calls if isinstance(c[0], list)]
        self.assertIn(["git", "worktree", "remove", wt], flat)
        self.assertIn(["git", "branch", "-D", "change/epic-close-ep"], flat)

    def test_written_sync_names_worktree_and_keeps_it(self):
        wt = os.path.join("/repo", ".worktrees", "epic-close-ep")
        fake, lines = self.run_sync(
            [(0, "", ""), (0, "complete", ""),
             (0, " M .shipd/epics/ep/epic.md\n", "")])
        self.assertTrue(any(wt in ln for ln in lines))
        flat = [c[0] for c in fake.calls if isinstance(c[0], list)]
        self.assertNotIn(["git", "worktree", "remove", wt], flat)

    def test_failed_worktree_creation_skips_sync(self):
        fake, lines = self.run_sync([(1, "", "boom")])
        self.assertEqual(len(fake.calls), 1)
        self.assertTrue(
            any("epic close-out skipped" in ln for ln in lines))

    def test_failed_sync_keeps_worktree(self):
        wt = os.path.join("/repo", ".worktrees", "epic-close-ep")
        fake, _lines = self.run_sync(
            [(0, "", ""), (2, "", "usage: spec_status.py ...")])
        self.assertEqual(len(fake.calls), 2)
        flat = [c[0] for c in fake.calls if isinstance(c[0], list)]
        self.assertNotIn(["git", "worktree", "remove", wt], flat)


# ---------------------------------------------------------------------------
# Per-member stage execution (injected runner / gate / command seams)
# ---------------------------------------------------------------------------

def _member(slug="m", risk="low"):
    return autopilot.Member(slug=slug, description="", risk=risk,
                            state="unplanned", order=0)


class _Seams:
    """Configurable fakes for the drive_member seams."""

    def __init__(self, gate_rc=0, gate_rcs=None, session_plan=None,
                 session_build=None, session_review=None, session_enrich=None):
        self.commands = []          # list of (cmd, cwd)
        self.gate_calls = []        # list of (member, cwd)
        self.sessions = []          # list of (stage, member, prompt)
        # Every session call's full argument record: one dict per call carrying
        # the stage plus the per-stage knobs the driver resolved for it.
        self.session_calls = []
        self.gate_rc = gate_rc
        # ``gate_rcs`` (when given) is a per-call sequence; the last value
        # sticks once exhausted, so the gate is deterministic across re-runs.
        self.gate_rcs = list(gate_rcs) if gate_rcs is not None else None
        # Each may be a callable(attempt)->(ok, sid, failure) or None (default ok).
        self.session_plan = session_plan
        self.session_build = session_build
        self.session_review = session_review
        self.session_enrich = session_enrich
        self._counts = {}

    def command_fn(self, cmd, cwd):
        self.commands.append((cmd, cwd))
        # The real worktree helper creates the member's worktree directory;
        # mirror that so the vanished-worktree detection has a dir to lose.
        if isinstance(cmd, list) and cmd and cmd[0] == autopilot.WORKTREE_SH:
            os.makedirs(os.path.join(cwd, ".worktrees", cmd[1]), exist_ok=True)
            return 0, "", ""
        # The final-resolution PR probe: answer merged by default, so a
        # full pass ships unless a test overrides this fake to say otherwise.
        if isinstance(cmd, list) and cmd[:3] == ["gh", "pr", "view"]:
            return 0, "http://pr/m\tMERGED\n", ""
        return 0, "", ""

    def gate_fn(self, member, cwd):
        self.gate_calls.append((member, cwd))
        if self.gate_rcs:
            rc = self.gate_rcs[0]
            if len(self.gate_rcs) > 1:
                self.gate_rcs = self.gate_rcs[1:]
            return rc
        return self.gate_rc

    def session_fn(self, stage, member, cwd, prompt, timeout, max_resumes,
                   on_session=None, model=None):
        self.sessions.append((stage, member, prompt))
        self.session_calls.append(
            {"stage": stage, "timeout": timeout, "max_resumes": max_resumes,
             "model": model})
        n = self._counts.get(stage, 0) + 1
        self._counts[stage] = n
        behavior = (self.session_plan if stage == "plan"
                    else self.session_build if stage == "build"
                    else self.session_review if stage == "review"
                    else self.session_enrich if stage == "enrich" else None)
        result = behavior(n) if behavior is not None else (
            True, "sess-%s-%d" % (stage, n), None)
        # Mirror the real seam: surface the session id mid-drive.
        if on_session is not None and result[1] is not None:
            on_session(result[1])
        return result

    def drive(self, pipeline, root, member=None, **kwargs):
        return autopilot.drive_member(
            root, "ep", member or _member(), pipeline,
            session_fn=self.session_fn, gate_fn=self.gate_fn,
            command_fn=self.command_fn, out=lambda *_: None, **kwargs)


class StageExecutionTest(AutopilotTestBase):
    PGB = [{"stage": "plan"}, {"stage": "gate"}, {"stage": "build"}]

    def test_full_pass_ships_via_helper_worktree(self):
        s = _Seams()
        result = s.drive(self.PGB, self.root)
        self.assertEqual(result.outcome, "shipped")
        # The worktree came from the plugin's worktree helper.
        first_cmd = s.commands[0][0]
        self.assertEqual(first_cmd, [autopilot.WORKTREE_SH, "m"])
        self.assertEqual([st for st, _m, _p in s.sessions], ["plan", "build"])
        self.assertEqual(len(s.gate_calls), 1)

    def test_full_pass_with_unmerged_pr_parks_needs_human_at_merge(self):
        # The pipeline completes with the worktree still present, but the PR
        # it opened has not merged: this is a stalled/timed-out ship, not a
        # success, so the member parks rather than recording `shipped`.
        s = _Seams()

        def command_fn(cmd, cwd):
            s.commands.append((cmd, cwd))
            if isinstance(cmd, list) and cmd and cmd[0] == autopilot.WORKTREE_SH:
                os.makedirs(os.path.join(cwd, ".worktrees", cmd[1]),
                            exist_ok=True)
                return 0, "", ""
            if isinstance(cmd, list) and cmd[:3] == ["gh", "pr", "view"]:
                return 0, "http://pr/m\tOPEN\n", ""
            return 0, "", ""

        result = autopilot.drive_member(
            self.root, "ep", _member(), self.PGB,
            session_fn=s.session_fn, gate_fn=s.gate_fn,
            command_fn=command_fn, out=lambda *_: None)
        self.assertEqual(result.outcome, "needs_human")
        self.assertNotEqual(result.outcome, "shipped")
        self.assertEqual(result.stage, "merge")
        self.assertEqual(result.pr_url, "http://pr/m")
        self.assertEqual(result.session_id, "sess-build-1")  # last session
        # This is the worktree-present path, not the vanished-worktree one.
        self.assertTrue(
            os.path.isdir(os.path.join(self.root, ".worktrees", "m")))

    def test_gate_exit_2_parks_rejected_after_one_enrichment(self):
        # A persistent context rejection parks the member — but only after the
        # single oracle-backed enrichment attempt and its re-gate.
        s = _Seams(gate_rc=2)
        result = s.drive(self.PGB, self.root)
        self.assertEqual(result.outcome, "rejected")
        self.assertEqual(result.stage, "gate")
        self.assertEqual(len(s.gate_calls), 2)  # initial rejection + re-gate
        # One enrichment session ran between them; build never did.
        self.assertEqual([st for st, _m, _p in s.sessions], ["plan", "enrich"])

    def test_skipped_gate_runs_no_gate(self):
        s = _Seams()
        pipeline = [{"stage": "plan"}, {"stage": "gate", "skip": True},
                    {"stage": "build"}]
        result = s.drive(pipeline, self.root)
        self.assertEqual(result.outcome, "shipped")
        self.assertEqual(s.gate_calls, [])

    def test_replaced_build_runs_command_not_session(self):
        s = _Seams()
        pipeline = [{"stage": "plan"}, {"stage": "gate"},
                    {"stage": "build",
                     "replace": {"command": "touch built.txt",
                                 "fallback": "skip"}}]
        result = s.drive(pipeline, self.root)
        self.assertEqual(result.outcome, "shipped")
        # The build ran as a command, not a session.
        self.assertIn("touch built.txt", [c for c, _cwd in s.commands])
        self.assertEqual([st for st, _m, _p in s.sessions], ["plan"])

    def test_custom_step_runs_in_worktree_at_position(self):
        s = _Seams()
        pipeline = [{"stage": "plan"}, {"stage": "gate"}, {"stage": "build"},
                    {"custom": "smoke", "command": "echo hi"},
                    {"stage": "review"}]
        result = s.drive(pipeline, self.root)
        self.assertEqual(result.outcome, "shipped")
        worktree = os.path.join(self.root, ".worktrees", "m")
        custom = [(c, cwd) for c, cwd in s.commands if c == "echo hi"]
        self.assertEqual(custom, [("echo hi", worktree)])

    def test_tools_binding_appears_in_prompt(self):
        s = _Seams()
        pipeline = [{"stage": "plan",
                     "tools": [{"name": "web-search", "fallback": "builtin"}]},
                    {"stage": "gate"}, {"stage": "build"}]
        s.drive(pipeline, self.root)
        plan_prompt = next(p for st, _m, p in s.sessions if st == "plan")
        self.assertIn("web-search", plan_prompt)
        self.assertIn("builtin", plan_prompt)

    def test_stage_fails_twice_then_passes(self):
        def plan_behavior(attempt):
            if attempt < 3:
                return False, "sess-p%d" % attempt, "boom %d" % attempt
            return True, "sess-p3", None

        s = _Seams(session_plan=plan_behavior)
        result = s.drive(self.PGB, self.root)
        self.assertEqual(result.outcome, "shipped")
        # Plan was retried to a third, passing attempt; build then ran.
        plan_sessions = [st for st, _m, _p in s.sessions if st == "plan"]
        self.assertEqual(len(plan_sessions), 3)
        self.assertIn("build", [st for st, _m, _p in s.sessions])

    def test_three_failures_park_needs_human_with_last_session(self):
        def build_behavior(attempt):
            return False, "sess-b%d" % attempt, "grade unmet %d" % attempt

        s = _Seams(session_build=build_behavior)
        result = s.drive(self.PGB, self.root)
        self.assertEqual(result.outcome, "needs_human")
        self.assertEqual(result.stage, "build")
        self.assertIsNotNone(result.reason)
        self.assertEqual(result.session_id, "sess-b3")  # the most recent
        # Exactly three build attempts.
        build_sessions = [st for st, _m, _p in s.sessions if st == "build"]
        self.assertEqual(len(build_sessions), 3)


# ---------------------------------------------------------------------------
# Per-stage driver knobs: an entry's `autopilot` block replaces the fixed
# three-strike budget and the run-global session budgets for that stage
# (epic-autopilot per-stage-driver-knobs, three-strike-parking,
# oracle-gate-enrichment).
# ---------------------------------------------------------------------------

class StageKnobsTest(AutopilotTestBase):
    PGB = [{"stage": "plan"}, {"stage": "gate"}, {"stage": "build"}]

    def _pipeline(self, build_entry):
        return [{"stage": "plan"}, {"stage": "gate"}, build_entry]

    def test_one_attempt_build_parks_on_first_failure(self):
        def build_behavior(attempt):
            return False, "sess-b%d" % attempt, "grade unmet %d" % attempt

        s = _Seams(session_build=build_behavior)
        result = s.drive(
            self._pipeline({"stage": "build", "autopilot": {"attempts": 1}}),
            self.root)
        self.assertEqual(result.outcome, "needs_human")
        self.assertEqual(result.stage, "build")
        self.assertEqual(result.session_id, "sess-b1")
        self.assertEqual(
            [st for st, _m, _p in s.sessions if st == "build"], ["build"])

    def test_two_attempts_let_a_second_try_succeed(self):
        def build_behavior(attempt):
            if attempt == 1:
                return False, "sess-b1", "transient"
            return True, "sess-b%d" % attempt, None

        s = _Seams(session_build=build_behavior)
        result = s.drive(
            self._pipeline({"stage": "build", "autopilot": {"attempts": 2}}),
            self.root)
        self.assertEqual(result.outcome, "shipped")
        self.assertEqual(
            len([st for st, _m, _p in s.sessions if st == "build"]), 2)

    def test_custom_step_attempts_govern_its_command_retries(self):
        s = _Seams()

        def command_fn(cmd, cwd):
            s.commands.append((cmd, cwd))
            if isinstance(cmd, list) and cmd and cmd[0] == autopilot.WORKTREE_SH:
                os.makedirs(os.path.join(cwd, ".worktrees", cmd[1]),
                            exist_ok=True)
                return 0, "", ""
            if cmd == "false":
                return 1, "", "nope"
            if isinstance(cmd, list) and cmd[:3] == ["gh", "pr", "view"]:
                return 0, "http://pr/m\tMERGED\n", ""
            return 0, "", ""

        pipeline = self.PGB + [
            {"custom": "smoke", "command": "false",
             "autopilot": {"attempts": 1}}]
        result = autopilot.drive_member(
            self.root, "ep", _member(), pipeline,
            session_fn=s.session_fn, gate_fn=s.gate_fn,
            command_fn=command_fn, out=lambda *_: None)
        self.assertEqual(result.outcome, "needs_human")
        self.assertEqual(result.stage, "custom:smoke")
        self.assertEqual([c for c, _cwd in s.commands].count("false"), 1)

    def test_gate_attempts_govern_the_engine_loop(self):
        # A non-rejection gate fault normally gets three strikes; one attempt
        # parks after the single call.
        s = _Seams(gate_rc=1)
        pipeline = [{"stage": "plan"},
                    {"stage": "gate", "autopilot": {"attempts": 1}},
                    {"stage": "build"}]
        result = s.drive(pipeline, self.root)
        self.assertEqual(result.outcome, "needs_human")
        self.assertEqual(result.stage, "gate")
        self.assertEqual(len(s.gate_calls), 1)

    def test_gate_attempts_govern_the_enrichment_loop(self):
        # `eco`'s single-enrichment doctrine: one gate call, at most one
        # enrichment session, then the member parks rejected.
        def enrich_behavior(attempt):
            return False, "sess-enrich-%d" % attempt, "session crashed"

        s = _Seams(gate_rcs=[2, 2], session_enrich=enrich_behavior)
        pipeline = [{"stage": "plan"},
                    {"stage": "gate", "autopilot": {"attempts": 1}},
                    {"stage": "build"}]
        result = s.drive(pipeline, self.root)
        self.assertEqual(result.outcome, "rejected")
        self.assertEqual(result.stage, "gate")
        self.assertEqual(len(s.gate_calls), 1)  # the rejection; no re-gate
        self.assertEqual(
            [st for st, _m, _p in s.sessions if st == "enrich"], ["enrich"])
        self.assertEqual(result.session_id, "sess-enrich-1")
        self.assertNotIn("build", [st for st, _m, _p in s.sessions])

    def test_per_stage_timeout_and_max_resumes_override_the_run_globals(self):
        s = _Seams()
        pipeline = [{"stage": "plan",
                     "autopilot": {"timeout": 42, "max_resumes": 0}},
                    {"stage": "gate"}, {"stage": "build"}]
        s.drive(pipeline, self.root, timeout=999, max_resumes=7)
        by_stage = {c["stage"]: c for c in s.session_calls}
        self.assertEqual(by_stage["plan"]["timeout"], 42)
        self.assertEqual(by_stage["plan"]["max_resumes"], 0)
        # A stage without an override keeps the run-global budgets.
        self.assertEqual(by_stage["build"]["timeout"], 999)
        self.assertEqual(by_stage["build"]["max_resumes"], 7)

    def test_enrichment_sessions_use_the_gate_entrys_budgets(self):
        s = _Seams(gate_rcs=[2, 0])
        pipeline = [{"stage": "plan"},
                    {"stage": "gate",
                     "autopilot": {"timeout": 60, "max_resumes": 1}},
                    {"stage": "build"}]
        s.drive(pipeline, self.root, timeout=999, max_resumes=7)
        enrich = next(c for c in s.session_calls if c["stage"] == "enrich")
        self.assertEqual(enrich["timeout"], 60)
        self.assertEqual(enrich["max_resumes"], 1)


# ---------------------------------------------------------------------------
# Model tiers on driven sessions: a declared `model` resolves through the
# stdlib tier authority and reaches the session as a concrete `--model`
# (epic-autopilot stage-model-resolution).
# ---------------------------------------------------------------------------

class SessionModelTierTest(AutopilotTestBase):
    def _models(self, session_calls):
        return {c["stage"]: c["model"] for c in session_calls}

    def test_session_tier_inherits_the_cli_default(self):
        s = _Seams()
        pipeline = [{"stage": "plan", "model": "session"},
                    {"stage": "gate"}, {"stage": "build"}]
        s.drive(pipeline, self.root)
        models = self._models(s.session_calls)
        self.assertIsNone(models["plan"])   # no --model flag at all
        self.assertIsNone(models["build"])  # a bare entry declares nothing

    def test_below_tier_resolves_against_the_ladder_top(self):
        s = _Seams()
        pipeline = [{"stage": "plan"}, {"stage": "gate"},
                    {"stage": "build", "model": "tier-below"}]
        s.drive(pipeline, self.root)
        self.assertEqual(self._models(s.session_calls)["build"], "opus")

    def test_run_anchor_shifts_the_resolution(self):
        s = _Seams()
        pipeline = [{"stage": "plan"}, {"stage": "gate"},
                    {"stage": "build", "model": "tier-below"}]
        s.drive(pipeline, self.root, session_model="sonnet")
        self.assertEqual(self._models(s.session_calls)["build"], "haiku")

    def test_concrete_id_passes_through_to_the_session(self):
        s = _Seams()
        pipeline = [{"stage": "plan", "model": "claude-fable-5"},
                    {"stage": "gate"}, {"stage": "build"}]
        s.drive(pipeline, self.root)
        self.assertEqual(self._models(s.session_calls)["plan"],
                         "claude-fable-5")

    def test_enrichment_uses_the_gate_entrys_model(self):
        s = _Seams(gate_rcs=[2, 0])
        pipeline = [{"stage": "plan"},
                    {"stage": "gate", "model": "tier-below"},
                    {"stage": "build"}]
        s.drive(pipeline, self.root)
        self.assertEqual(self._models(s.session_calls)["enrich"], "opus")

    def test_run_member_and_run_accept_the_anchor(self):
        # The anchor is a run-level control both entry points thread through.
        _make_epic(self.root, "ep", [("a", "low")])
        seen = {}

        def driver(root, epic, member, pipeline, heartbeat=None):
            return autopilot.MemberResult(outcome="shipped",
                                          pr_url="http://pr/a")

        autopilot.run(self.root, "ep", member_driver=driver,
                      sync_fn=lambda *a, **k: seen.setdefault("sync", True),
                      session_model="sonnet", out=lambda *_: None)
        autopilot.run_member(
            self.root, "ep", "a", session_model="sonnet",
            driver=lambda: autopilot.MemberResult(outcome="shipped",
                                                  pr_url="http://pr/a"),
            out=lambda *_: None)


class TierAnchorVisibilityTest(AutopilotTestBase):
    """The acting model-tier anchor is visible, never implicit: printed in the
    dry run and recorded in the run report (epic-autopilot
    stage-model-resolution)."""

    def _dry_run_text(self, **kwargs):
        lines = []
        autopilot.run(self.root, "ep", dry_run=True, out=lines.append,
                      **kwargs)
        return "\n".join(lines)

    def test_dry_run_prints_the_default_anchor(self):
        _make_epic(self.root, "ep", [("a", "low")])
        text = self._dry_run_text()
        self.assertIn("Model tier anchor:", text)
        anchor_line = next(l for l in text.splitlines()
                           if l.startswith("Model tier anchor:"))
        self.assertIn("fable", anchor_line)  # the ladder top

    def test_dry_run_prints_the_named_anchor(self):
        _make_epic(self.root, "ep", [("a", "low")])
        anchor_line = next(
            l for l in self._dry_run_text(session_model="sonnet").splitlines()
            if l.startswith("Model tier anchor:"))
        self.assertIn("sonnet", anchor_line)

    def test_run_report_records_the_anchor(self):
        _make_epic(self.root, "ep", [("a", "low")])

        def driver(root, epic, member, pipeline, heartbeat=None):
            return autopilot.MemberResult(outcome="shipped",
                                          pr_url="http://pr/a")

        report = autopilot.run(
            self.root, "ep", member_driver=driver, session_model="sonnet",
            sync_fn=lambda *a, **k: None, out=lambda *_: None)
        self.assertEqual(report["tier_anchor"], "sonnet")
        path = os.path.join(self.root, ".shipd", "autopilot", "ep-report.json")
        with open(path, encoding="utf-8") as fh:
            self.assertEqual(json.load(fh)["tier_anchor"], "sonnet")

    def test_run_report_records_the_default_anchor(self):
        _make_epic(self.root, "ep", [("a", "low")])

        def driver(root, epic, member, pipeline, heartbeat=None):
            return autopilot.MemberResult(outcome="shipped",
                                          pr_url="http://pr/a")

        report = autopilot.run(self.root, "ep", member_driver=driver,
                               sync_fn=lambda *a, **k: None,
                               out=lambda *_: None)
        self.assertEqual(report["tier_anchor"], "fable")

    def test_run_member_report_records_the_anchor(self):
        _make_epic(self.root, "ep", [("a", "low")])
        autopilot.run_member(
            self.root, "ep", "a", session_model="sonnet",
            driver=lambda: autopilot.MemberResult(outcome="shipped",
                                                  pr_url="http://pr/a"),
            out=lambda *_: None)
        path = os.path.join(self.root, ".shipd", "autopilot", "ep-report.json")
        with open(path, encoding="utf-8") as fh:
            self.assertEqual(json.load(fh)["tier_anchor"], "sonnet")


class ProductionSessionModelTest(unittest.TestCase):
    """The production session seam turns a resolved model into the driven
    CLI's ``--model`` argument — and omits the flag entirely when None."""

    def _extra_args_for(self, model):
        captured = {}

        def fake_run_turn(prompt, cwd, resume_id=None, timeout=None,
                          claude_bin=None, extra_args=None):
            captured["extra"] = list(extra_args or [])
            return True, None, "sess-1"

        real = session_driver.run_turn
        session_driver.run_turn = fake_run_turn
        try:
            session_fn = autopilot._make_session_fn("claude")
            session_fn("custom", "m", os.getcwd(), "do it", 10, 0,
                       model=model)
        finally:
            session_driver.run_turn = real
        return captured["extra"]

    def test_resolved_model_becomes_a_model_flag(self):
        extra = self._extra_args_for("opus")
        self.assertIn("--model", extra)
        self.assertEqual(extra[extra.index("--model") + 1], "opus")

    def test_no_model_passes_no_flag(self):
        self.assertNotIn("--model", self._extra_args_for(None))


# ---------------------------------------------------------------------------
# Stale-worktree reclaim: an `already exists` create failure is healed by a
# guarded remove + merged-only branch delete + one retried create.
# ---------------------------------------------------------------------------

class _ReclaimCommands:
    """Scripted ``command_fn`` for the reclaim path. Records every argv and
    returns per-command results, mirroring the real worktree helper's directory
    side effects: a successful create (re)makes ``.worktrees/<slug>`` and a
    successful guarded remove deletes it, so the drive can proceed afterwards."""

    def __init__(self, root, slug, create_results, remove=(0, "", ""),
                 show_ref=(0, "", ""), branch_del=(0, "", "")):
        self.root = root
        self.slug = slug
        self.create_results = list(create_results)
        self.remove = remove
        self.show_ref = show_ref
        self.branch_del = branch_del
        self.calls = []

    def __call__(self, cmd, cwd):
        self.calls.append(cmd)
        wt = os.path.join(self.root, ".worktrees", self.slug)
        if cmd == [autopilot.WORKTREE_SH, self.slug]:
            rc, out, err = (self.create_results.pop(0)
                            if self.create_results else (0, "", ""))
            if rc == 0:
                os.makedirs(wt, exist_ok=True)
            return rc, out, err
        if cmd[:2] == ["env", "SHIPD_WORKTREE_IDLE_MINUTES=0"]:
            if self.remove[0] == 0:
                shutil.rmtree(wt, ignore_errors=True)
            return self.remove
        if cmd[:2] == ["git", "show-ref"]:
            return self.show_ref
        if cmd[:3] == ["git", "branch", "-d"]:
            return self.branch_del
        if cmd[:3] == ["gh", "pr", "view"]:
            return 0, "http://pr/m\tMERGED\n", ""
        return 0, "", ""


class StaleWorktreeReclaimTest(AutopilotTestBase):
    PGB = [{"stage": "plan"}, {"stage": "gate"}, {"stage": "build"}]
    ALREADY = "error: /repo/.worktrees/m already exists"

    def _leftover(self):
        os.makedirs(os.path.join(self.root, ".worktrees", "m"), exist_ok=True)

    def _drive(self, command_fn):
        s = _Seams()
        return autopilot.drive_member(
            self.root, "ep", _member(), self.PGB,
            session_fn=s.session_fn, gate_fn=s.gate_fn,
            command_fn=command_fn, out=lambda *_: None)

    def test_clean_leftover_reclaimed_then_drive_proceeds(self):
        self._leftover()
        cmd = _ReclaimCommands(
            self.root, "m",
            create_results=[(1, "", self.ALREADY), (0, "", "")])
        result = self._drive(cmd)
        self.assertEqual(result.outcome, "shipped")
        # The reclaim sequence ran, in order, through the command seam.
        self.assertIn(
            ["env", "SHIPD_WORKTREE_IDLE_MINUTES=0", autopilot.WORKTREE_SH,
             "remove", "m"], cmd.calls)
        self.assertIn(
            ["git", "show-ref", "--verify", "--quiet",
             "refs/heads/change/m"], cmd.calls)
        self.assertIn(["git", "branch", "-d", "change/m"], cmd.calls)
        # Create was issued twice: the failing original and the retry.
        creates = [c for c in cmd.calls if c == [autopilot.WORKTREE_SH, "m"]]
        self.assertEqual(len(creates), 2)

    def test_guard_refusal_parks_with_refusal_reason(self):
        self._leftover()
        refusal = ("refusing to remove /repo/.worktrees/m — work in progress:\n"
                   "  - dirty: tracked changes present")
        cmd = _ReclaimCommands(
            self.root, "m",
            create_results=[(1, "", self.ALREADY)],
            remove=(2, "", refusal))
        result = self._drive(cmd)
        self.assertEqual(result.outcome, "needs_human")
        self.assertEqual(result.stage, "worktree")
        self.assertIn("dirty: tracked changes present", result.reason)
        # No branch delete and no retried create after the refusal.
        self.assertNotIn(["git", "branch", "-d", "change/m"], cmd.calls)
        creates = [c for c in cmd.calls if c == [autopilot.WORKTREE_SH, "m"]]
        self.assertEqual(len(creates), 1)

    def test_unmerged_branch_delete_parks_with_delete_reason(self):
        self._leftover()
        delete_err = "error: the branch 'change/m' is not fully merged."
        cmd = _ReclaimCommands(
            self.root, "m",
            create_results=[(1, "", self.ALREADY)],
            branch_del=(1, "", delete_err))
        result = self._drive(cmd)
        self.assertEqual(result.outcome, "needs_human")
        self.assertEqual(result.stage, "worktree")
        self.assertIn("not fully merged", result.reason)
        # The branch was left in place — no retried create.
        creates = [c for c in cmd.calls if c == [autopilot.WORKTREE_SH, "m"]]
        self.assertEqual(len(creates), 1)

    def test_other_create_failure_parks_without_reclaim(self):
        cmd = _ReclaimCommands(
            self.root, "m",
            create_results=[(1, "", "error: something else went wrong")])
        result = self._drive(cmd)
        self.assertEqual(result.outcome, "needs_human")
        self.assertEqual(result.stage, "worktree")
        self.assertIn("something else went wrong", result.reason)
        # No reclaim command was issued at all.
        self.assertNotIn(
            ["env", "SHIPD_WORKTREE_IDLE_MINUTES=0", autopilot.WORKTREE_SH,
             "remove", "m"], cmd.calls)
        self.assertFalse(any(c[:1] == ["git"] for c in cmd.calls))
        creates = [c for c in cmd.calls if c == [autopilot.WORKTREE_SH, "m"]]
        self.assertEqual(len(creates), 1)


# ---------------------------------------------------------------------------
# Targeted single-member drive: enter the pipeline at the member's stage
# ---------------------------------------------------------------------------

class TargetedDriveTest(AutopilotTestBase):
    def test_ready_member_enters_at_build(self):
        # A ready (planned, lint-clean) member enters at build: plan and gate
        # are skipped, and it is driven through to its terminal outcome.
        _make_epic(self.root, "ep", [("a", "low")])
        _plant_planned(self.root, "a", "ready")
        s = _Seams()
        result = autopilot.drive_single_member(
            self.root, "ep", "a", session_fn=s.session_fn,
            gate_fn=s.gate_fn, command_fn=s.command_fn, out=lambda *_: None)
        self.assertEqual(result.outcome, "shipped")
        self.assertEqual([st for st, _m, _p in s.sessions],
                         ["build", "review"])
        self.assertEqual(s.gate_calls, [])  # gate skipped

    def test_unplanned_member_enters_at_plan(self):
        # An unplanned member enters at plan; no other member is driven.
        _make_epic(self.root, "ep", [("a", "low"), ("b", "low")])
        s = _Seams()
        result = autopilot.drive_single_member(
            self.root, "ep", "a", session_fn=s.session_fn,
            gate_fn=s.gate_fn, command_fn=s.command_fn, out=lambda *_: None)
        self.assertEqual(result.outcome, "shipped")
        self.assertEqual([st for st, _m, _p in s.sessions],
                         ["plan", "build", "review"])
        # Only member "a" was driven — never "b".
        self.assertTrue(all(m == "a" for _st, m, _p in s.sessions))

    def test_entry_stage_maps_lifecycle_to_pipeline_stage(self):
        self.assertEqual(autopilot.entry_stage("unplanned"), "plan")
        self.assertEqual(autopilot.entry_stage("ready"), "build")

    def test_run_member_writes_heartbeat_and_report(self):
        # The board-observable wrapper seeds the epic heartbeat with just this
        # member and writes a one-member report.
        _make_epic(self.root, "ep", [("a", "low"), ("b", "low")])
        _plant_planned(self.root, "a", "ready")

        def driver():
            return autopilot.MemberResult(outcome="shipped", pr_url="http://pr/a")

        result = autopilot.run_member(self.root, "ep", "a", driver=driver,
                                      out=lambda *_: None)
        self.assertEqual(result.outcome, "shipped")
        hb_path = os.path.join(self.root, ".shipd", "autopilot",
                               "ep-heartbeat.json")
        with open(hb_path, encoding="utf-8") as fh:
            hb = json.load(fh)
        self.assertEqual(hb["state"], "finished")
        self.assertEqual([r["slug"] for r in hb["roster"]], ["a"])
        report_path = os.path.join(self.root, ".shipd", "autopilot",
                                   "ep-report.json")
        with open(report_path, encoding="utf-8") as fh:
            report = json.load(fh)
        self.assertEqual([r["member"] for r in report["shipped"]], ["a"])

    def test_run_member_rejects_an_in_flight_member(self):
        _make_epic(self.root, "ep", [("a", "low")])
        _plant_planned(self.root, "a", "rejected")  # not unplanned/ready
        with self.assertRaises(autopilot.AutopilotError):
            autopilot.run_member(self.root, "ep", "a", out=lambda *_: None)

    def test_member_cli_flag_routes_to_run_member(self):
        _make_epic(self.root, "ep", [("a", "low")])
        calls = {}
        orig = autopilot.run_member

        def fake(root, epic, slug, **kwargs):
            calls["route"] = (epic, slug)
            return autopilot.MemberResult(outcome="shipped")

        autopilot.run_member = fake
        try:
            rc = autopilot.main(["ep", "--root", self.root, "--member", "a"])
        finally:
            autopilot.run_member = orig
        self.assertEqual(rc, 0)
        self.assertEqual(calls["route"], ("ep", "a"))

    def test_no_member_cli_flag_routes_to_run(self):
        _make_epic(self.root, "ep", [("a", "low")])
        seen = {}
        orig = autopilot.run

        def fake(root, epic, **kwargs):
            seen["epic"] = epic
            return {}

        autopilot.run = fake
        try:
            rc = autopilot.main(["ep", "--root", self.root, "--dry-run"])
        finally:
            autopilot.run = orig
        self.assertEqual(rc, 0)
        self.assertEqual(seen["epic"], "ep")

    def test_auto_selection_is_untouched_by_a_normal_run(self):
        # A normal epic run (no targeted member) still selects and orders the
        # unplanned set risk-ascending, exactly as before.
        _make_epic(self.root, "ep",
                   [("hi", "high"), ("lo", "low"), ("mid", "medium")])
        order = []

        def driver(root, epic, member, pipeline, heartbeat=None):
            order.append(member.slug)
            return autopilot.MemberResult(outcome="shipped", pr_url="x")

        autopilot.run(self.root, "ep", member_driver=driver,
                      sync_fn=lambda *a, **k: None, out=lambda *_: None)
        self.assertEqual(order, ["lo", "mid", "hi"])


# ---------------------------------------------------------------------------
# Oracle-backed gate enrichment: a single enrichment session on exit 2, re-gate
# ---------------------------------------------------------------------------

class GateEnrichmentTest(AutopilotTestBase):
    PGB = [{"stage": "plan"}, {"stage": "gate"}, {"stage": "build"}]

    def test_enrichment_pass_continues_pipeline(self):
        # Gate exits 2 (rejection), then 0 after enrichment.
        s = _Seams(gate_rcs=[2, 0])
        result = s.drive(self.PGB, self.root)
        self.assertEqual(result.outcome, "shipped")
        # Exactly one enrichment session ran, its prompt naming /s:plan and
        # the oracle agent.
        enrich = [(st, p) for st, _m, p in s.sessions if st == "enrich"]
        self.assertEqual(len(enrich), 1)
        prompt = enrich[0][1]
        self.assertIn("/s:plan", prompt)
        self.assertIn("m", prompt)  # the member slug
        self.assertIn("s:oracle", prompt)
        # The gate ran twice: the initial rejection and the post-enrichment pass.
        self.assertEqual(len(s.gate_calls), 2)
        # The pipeline continued into build.
        self.assertIn("build", [st for st, _m, _p in s.sessions])

    def test_second_rejection_parks_with_session_id(self):
        # Gate exits 2 both before and after the enrichment session.
        s = _Seams(gate_rcs=[2, 2])
        result = s.drive(self.PGB, self.root)
        self.assertEqual(result.outcome, "rejected")
        self.assertEqual(result.stage, "gate")
        self.assertIsNotNone(result.reason)
        self.assertIn("enrich", result.reason.lower())
        self.assertEqual(result.session_id, "sess-enrich-1")
        # Exactly one enrichment session ran, and build never did.
        enrich = [st for st, _m, _p in s.sessions if st == "enrich"]
        self.assertEqual(len(enrich), 1)
        self.assertNotIn("build", [st for st, _m, _p in s.sessions])

    def test_enrichment_session_failure_retries_then_parks(self):
        # The enrichment session errors on every attempt while the worktree
        # still exists. A transient fault must be retried (three strikes)
        # before the member is parked — never parked on the first blip.
        calls = []

        def enrich_behavior(attempt):
            calls.append(attempt)
            return False, "sess-enrich-%d" % attempt, "session crashed"

        s = _Seams(gate_rcs=[2, 2], session_enrich=enrich_behavior)
        result = s.drive(self.PGB, self.root)
        # Parked rejected — never needs-human — with the failure and the
        # exhausted-retries context in the reason.
        self.assertEqual(result.outcome, "rejected")
        self.assertEqual(result.stage, "gate")
        self.assertIn("session crashed", result.reason)
        self.assertIn("3 attempts", result.reason)
        self.assertEqual(result.session_id, "sess-enrich-3")
        # Three enrichment attempts ran; the gate never re-ran after failure.
        enrich = [st for st, _m, _p in s.sessions if st == "enrich"]
        self.assertEqual(len(enrich), 3)
        self.assertEqual(calls, [1, 2, 3])
        self.assertNotIn("build", [st for st, _m, _p in s.sessions])

    def test_enrichment_transient_failure_then_success_continues(self):
        # The fix's core guarantee: a transient CLI/API fault on the first
        # enrichment attempt must not park the member — a later attempt
        # succeeds, the re-gate passes, and the pipeline continues.
        def enrich_behavior(attempt):
            if attempt == 1:
                return False, None, "session CLI exited 1: connection closed"
            return True, "sess-enrich-%d" % attempt, None

        s = _Seams(gate_rcs=[2, 0], session_enrich=enrich_behavior)
        result = s.drive(self.PGB, self.root)
        self.assertEqual(result.outcome, "shipped")
        # Two enrichment attempts ran (one failed, one succeeded); build ran.
        enrich = [st for st, _m, _p in s.sessions if st == "enrich"]
        self.assertEqual(len(enrich), 2)
        self.assertIn("build", [st for st, _m, _p in s.sessions])
        # Gate ran twice: the initial rejection and the post-enrichment pass.
        self.assertEqual(len(s.gate_calls), 2)

    def test_vanished_worktree_during_enrichment_with_merged_pr_ships(self):
        worktree = os.path.join(self.root, ".worktrees", "m")

        def command_fn(cmd, cwd):
            if isinstance(cmd, list) and cmd and cmd[0] == autopilot.WORKTREE_SH:
                os.makedirs(os.path.join(cwd, ".worktrees", cmd[1]),
                            exist_ok=True)
                return 0, "", ""
            if isinstance(cmd, list) and cmd[:3] == ["gh", "pr", "view"]:
                self.assertEqual(cwd, self.root)  # probe from repo root
                return 0, "http://pr/m\tMERGED\n", ""
            return 0, "", ""

        def session_fn(stage, member, cwd, prompt, timeout, max_resumes,
                       on_session=None, model=None):
            if stage == "enrich":
                shutil.rmtree(worktree, ignore_errors=True)
            return True, "sess-%s" % stage, None

        result = autopilot.drive_member(
            self.root, "ep", _member(), self.PGB,
            session_fn=session_fn, gate_fn=lambda *a: 2,
            command_fn=command_fn, out=lambda *_: None)
        self.assertEqual(result.outcome, "shipped")
        self.assertEqual(result.pr_url, "http://pr/m")
        self.assertTrue(result.merged)


# ---------------------------------------------------------------------------
# Review stage: driven after build, graded on the posted semantic-review status
# ---------------------------------------------------------------------------

class ReviewStageTest(AutopilotTestBase):
    PGBR = [{"stage": "plan"}, {"stage": "gate"}, {"stage": "build"},
            {"stage": "review"}]

    def test_review_drives_after_build(self):
        s = _Seams()
        result = s.drive(self.PGBR, self.root)
        self.assertEqual(result.outcome, "shipped")
        # The review stage runs as a driven session, after build.
        self.assertEqual([st for st, _m, _p in s.sessions],
                         ["plan", "build", "review"])

    def test_review_prompt_names_review_and_poster(self):
        s = _Seams()
        s.drive(self.PGBR, self.root)
        review_prompt = next(p for st, _m, p in s.sessions if st == "review")
        self.assertIn("/s:review", review_prompt)
        self.assertIn("review_gate.py", review_prompt)

    def test_review_prompt_names_disposition_loop(self):
        s = _Seams()
        s.drive(self.PGBR, self.root)
        review_prompt = next(p for st, _m, p in s.sessions if st == "review")
        # The disposition loop: implement or reply, then resolve.
        low = review_prompt.lower()
        self.assertIn("implement", low)
        self.assertIn("reply", low)
        self.assertIn("resolve", low)
        self.assertIn("unresolved=0", review_prompt)

    def test_persistent_red_review_parks_needs_human(self):
        def review_behavior(attempt):
            return False, "sess-r%d" % attempt, "status not success %d" % attempt

        s = _Seams(session_review=review_behavior)
        result = s.drive(self.PGBR, self.root)
        self.assertEqual(result.outcome, "needs_human")
        self.assertEqual(result.stage, "review")
        self.assertEqual(result.session_id, "sess-r3")  # most recent
        review_sessions = [st for st, _m, _p in s.sessions if st == "review"]
        self.assertEqual(len(review_sessions), 3)  # three strikes

    def test_skipped_review_is_honored(self):
        s = _Seams()
        pipeline = [{"stage": "plan"}, {"stage": "gate"}, {"stage": "build"},
                    {"stage": "review", "skip": True}]
        result = s.drive(pipeline, self.root)
        self.assertEqual(result.outcome, "shipped")
        self.assertNotIn("review", [st for st, _m, _p in s.sessions])


class OracleAwareSessionTest(unittest.TestCase):
    """The canned resume reply and the build stage prompt route undecided
    points and sub-agent escalations through the ask-mikk oracle."""

    def test_goahead_reply_names_oracle_rung(self):
        reply = autopilot.GOAHEAD_REPLY
        self.assertIn("s:oracle", reply)
        # The compact-question shape: decision, options, recommendation.
        low = reply.lower()
        self.assertIn("decision", low)
        self.assertIn("options", low)
        self.assertIn("recommend", low)
        self.assertIn("ANSWER", reply)
        self.assertIn("INSUFFICIENT", reply)

    def test_build_prompt_routes_question_escalations_through_oracle(self):
        prompt = autopilot._stage_prompt("build", "m", {})
        self.assertIn("s:oracle", prompt)
        self.assertIn("QUESTION:", prompt)


# ---------------------------------------------------------------------------
# Declared stage options reach the stage prompts and the dry-run labels
# (epic-autopilot stage-options-in-prompts).
# ---------------------------------------------------------------------------

class StageOptionPromptTest(unittest.TestCase):
    BUILD_OPTS = {"stage": "build", "validator": False, "telemetry": False,
                  "parallelism": 2, "subagent_model": "tier-two-below"}
    REVIEW_OPTS = {"stage": "review", "disposition": "high-only",
                   "model": "tier-below"}

    def test_build_options_reach_the_build_prompt(self):
        prompt = autopilot._stage_prompt("build", "m", self.BUILD_OPTS)
        low = prompt.lower()
        self.assertIn("validator", low)
        self.assertIn("telemetry", low)
        self.assertIn("2", prompt)          # the sub-agent cap
        self.assertIn("sub-agent", low)
        # The sub-agent model is named as the concrete resolved value with its
        # symbolic provenance alongside.
        self.assertIn("sonnet", prompt)     # tier-two-below from the top
        self.assertIn("tier-two-below", prompt)

    def test_build_subagent_model_resolves_against_the_stage_model(self):
        # The anchor is the build session's own resolved model.
        prompt = autopilot._stage_prompt(
            "build", "m", self.BUILD_OPTS, model_anchor="opus")
        self.assertIn("haiku", prompt)
        self.assertIn("tier-two-below", prompt)

    def test_review_scope_reaches_the_poster_and_the_loop(self):
        prompt = autopilot._stage_prompt("review", "m", self.REVIEW_OPTS)
        self.assertIn("--disposition high-only", prompt)
        self.assertIn("--model tier-below", prompt)
        low = prompt.lower()
        self.assertIn("high-severity", low)
        self.assertIn("autoreply", low)
        self.assertIn("resolve", low)
        self.assertIn("unresolved=0", prompt)

    def test_review_disposition_none_autoreplies_everything(self):
        prompt = autopilot._stage_prompt(
            "review", "m", {"stage": "review", "disposition": "none"})
        self.assertIn("--disposition none", prompt)
        self.assertIn("autoreply", prompt.lower())
        self.assertIn("unresolved=0", prompt)

    def test_review_disposition_all_keeps_todays_loop(self):
        # `all` reaches the poster, but the loop paragraph is today's
        # per-finding judgement — no autoreply.
        prompt = autopilot._stage_prompt(
            "review", "m", {"stage": "review", "disposition": "all"})
        self.assertIn("--disposition all", prompt)
        self.assertIn("implement the suggestion", prompt)
        self.assertNotIn("autoreply", prompt.lower())

    def test_bare_entries_keep_todays_prompts(self):
        build = autopilot._stage_prompt("build", "m", {"stage": "build"})
        self.assertEqual(build, autopilot._stage_prompt("build", "m", {}))
        for token in ("validator", "telemetry", "parallelism", "sub-agent model"):
            self.assertNotIn(token, build.lower())
        review = autopilot._stage_prompt("review", "m", {"stage": "review"})
        self.assertEqual(review, autopilot._stage_prompt("review", "m", {}))
        self.assertNotIn("--disposition", review)
        self.assertNotIn("autoreply", review.lower())


class EntryLabelTest(unittest.TestCase):
    def test_gate_attempts_render_in_the_label(self):
        label = autopilot._entry_label(
            {"stage": "gate", "autopilot": {"attempts": 1}})
        self.assertIn("gate", label)
        self.assertIn("attempts 1", label)

    def test_build_options_render_in_the_label(self):
        label = autopilot._entry_label(
            {"stage": "build", "validator": False, "telemetry": False,
             "parallelism": 2, "subagent_model": "tier-two-below"})
        self.assertIn("validator off", label)
        self.assertIn("telemetry off", label)
        self.assertIn("parallelism 2", label)
        self.assertIn("subagent_model tier-two-below", label)

    def test_review_options_render_in_the_label(self):
        label = autopilot._entry_label(
            {"stage": "review", "model": "tier-below",
             "disposition": "high-only"})
        self.assertIn("model tier-below", label)
        self.assertIn("disposition high-only", label)

    def test_bare_and_skipped_entries_keep_their_labels(self):
        self.assertEqual(autopilot._entry_label({"stage": "plan"}), "plan")
        self.assertEqual(
            autopilot._entry_label({"stage": "gate", "skip": True}),
            "gate [skip]")


class ReviewGradeTest(AutopilotTestBase):
    """The production review grade passes iff the combined status carries a
    `semantic-review` = `success` entry **and** `resolve --check` reports
    `unresolved=0` — a green status with dangling finding threads fails."""

    def _grade(self, *, sha="deadbeef", status_state="success", pr_rc=0,
               unresolved=0):
        def command_fn(cmd, cwd):
            if cmd[:3] == ["gh", "pr", "view"]:
                return pr_rc, sha + "\n", ""
            if cmd[:2] == ["gh", "api"]:
                self.assertIn("commits/%s/status" % sha, " ".join(cmd))
                body = json.dumps({"state": status_state, "statuses": [
                    {"context": "ci", "state": "success"},
                    {"context": "semantic-review", "state": status_state}]})
                return 0, body, ""
            if "resolve" in cmd and "--check" in cmd:
                # The gate's --check exits non-zero above zero unresolved.
                return (0 if unresolved == 0 else 1,
                        "unresolved=%d\n" % unresolved, "")
            return 1, "", "unexpected: %r" % (cmd,)
        return autopilot._review_grade(self.root, "m", command_fn=command_fn)

    def test_passes_on_green_status_and_zero_unresolved(self):
        self.assertTrue(self._grade(status_state="success", unresolved=0)())

    def test_fails_on_green_status_with_unresolved_thread(self):
        self.assertFalse(self._grade(status_state="success", unresolved=1)())

    def test_fails_when_status_not_success(self):
        self.assertFalse(self._grade(status_state="failure")())

    def test_fails_without_a_pr_head(self):
        self.assertFalse(self._grade(pr_rc=1)())


# ---------------------------------------------------------------------------
# Vanished worktree: a driven session removes its own worktree at close-out
# ---------------------------------------------------------------------------

class VanishedWorktreeTest(AutopilotTestBase):
    """A driven build session legitimately merges its PR and removes its own
    worktree while shipping the member; the autopilot must resolve the outcome
    from the repo-root PR instead of crashing or mis-parking."""

    PGBR = [{"stage": "plan"}, {"stage": "gate"}, {"stage": "build"},
            {"stage": "review"}]

    def _seams(self, pr_out):
        """Build (sessions, session_fn, command_fn) whose build session removes
        the member's worktree (as a real close-out does) and whose PR probe on
        the repo root answers with ``pr_out``."""
        worktree = os.path.join(self.root, ".worktrees", "m")
        sessions = []

        def command_fn(cmd, cwd):
            if isinstance(cmd, list) and cmd and cmd[0] == autopilot.WORKTREE_SH:
                os.makedirs(os.path.join(cwd, ".worktrees", cmd[1]),
                            exist_ok=True)
                return 0, "", ""
            if isinstance(cmd, list) and cmd[:3] == ["gh", "pr", "view"]:
                # The probe must run from the repo root, never the dead worktree.
                self.assertEqual(cwd, self.root)
                return 0, pr_out, ""
            return 0, "", ""

        def session_fn(stage, member, cwd, prompt, timeout, max_resumes,
                       on_session=None, model=None):
            sessions.append(stage)
            if stage == "build":
                shutil.rmtree(worktree, ignore_errors=True)
            return True, "sess-%s" % stage, None

        return sessions, session_fn, command_fn

    def test_merged_pr_records_early_ship_and_skips_rest(self):
        sessions, session_fn, command_fn = self._seams("http://pr/m\tMERGED\n")
        result = autopilot.drive_member(
            self.root, "ep", _member(), self.PGBR,
            session_fn=session_fn, gate_fn=lambda *a: 0,
            command_fn=command_fn, out=lambda *_: None)
        self.assertEqual(result.outcome, "shipped")
        self.assertEqual(result.pr_url, "http://pr/m")
        self.assertTrue(result.merged)
        # Review never ran — the vanished worktree was resolved first.
        self.assertEqual(sessions, ["plan", "build"])

    def test_unmerged_pr_parks_needs_human_with_reason_and_session(self):
        sessions, session_fn, command_fn = self._seams("http://pr/m\tOPEN\n")
        result = autopilot.drive_member(
            self.root, "ep", _member(), self.PGBR,
            session_fn=session_fn, gate_fn=lambda *a: 0,
            command_fn=command_fn, out=lambda *_: None)
        self.assertEqual(result.outcome, "needs_human")
        self.assertIn("worktree vanished", result.reason)
        self.assertEqual(result.session_id, "sess-build")  # most recent
        self.assertEqual(sessions, ["plan", "build"])


# ---------------------------------------------------------------------------
# Heartbeat wiring: a seam-based run threads the live heartbeat through
# ---------------------------------------------------------------------------

class _SnapshotHeartbeat(heartbeat.RunHeartbeat):
    """A live heartbeat that also captures a deep copy of every written state,
    so a test can inspect the sequence of file contents a run produced."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.snapshots = []

    def _write(self):
        super()._write()
        self.snapshots.append(json.loads(json.dumps(self._state)))


class HeartbeatWiringTest(AutopilotTestBase):
    def _heartbeat_path(self, epic):
        return os.path.join(self.root, ".shipd", "autopilot",
                            "%s-heartbeat.json" % epic)

    def test_run_threads_heartbeat_through_the_drive(self):
        _make_epic(self.root, "ep", [("a", "low"), ("b", "high")])
        s = _Seams()

        def driver(root, epic, member, pipeline, heartbeat=None):
            return autopilot.drive_member(
                root, epic, member, pipeline, session_fn=s.session_fn,
                gate_fn=s.gate_fn, command_fn=s.command_fn,
                out=lambda *_: None, heartbeat=heartbeat)

        hb = _SnapshotHeartbeat(self.root, "ep")
        autopilot.run(self.root, "ep", member_driver=driver, heartbeat=hb,
                      sync_fn=lambda *a, **k: None, out=lambda *_: None)

        # Run start: the first written state is running with a pending roster.
        first = hb.snapshots[0]
        self.assertEqual(first["state"], "running")
        self.assertEqual({r["state"] for r in first["roster"]}, {"pending"})

        # A driving stage was visible mid-run (some snapshot shows it).
        driving = [
            r for snap in hb.snapshots for r in snap["roster"]
            if r["state"] == "driving" and "stage" in r]
        self.assertTrue(driving)
        self.assertEqual(driving[0]["attempt"], 1)

        # Run end: the on-disk file is finished with both members shipped.
        with open(self._heartbeat_path("ep"), encoding="utf-8") as fh:
            final = json.load(fh)
        self.assertEqual(final["state"], "finished")
        roster = {r["slug"]: r["state"] for r in final["roster"]}
        self.assertEqual(roster, {"a": "shipped", "b": "shipped"})

    def test_dry_run_writes_no_heartbeat(self):
        _make_epic(self.root, "ep", [("a", "low")])
        autopilot.run(self.root, "ep", dry_run=True, out=lambda *_: None)
        self.assertFalse(os.path.exists(self._heartbeat_path("ep")))


class AbortHandlingTest(AutopilotTestBase):
    """A catchably-terminated run (a raised AutopilotError, or the Python form
    of SIGINT, KeyboardInterrupt) leaves the heartbeat at a terminal `aborted`
    state instead of frozen at `running` — while a clean run still ends at
    `finished`, unaltered by the abort-guarding finally."""

    def _heartbeat_path(self, epic):
        return os.path.join(self.root, ".shipd", "autopilot",
                            "%s-heartbeat.json" % epic)

    def _read(self, epic):
        with open(self._heartbeat_path(epic), encoding="utf-8") as fh:
            return json.load(fh)

    def test_run_autopilot_error_mid_drive_leaves_heartbeat_aborted(self):
        _make_epic(self.root, "ep", [("a", "low")])

        def driver(root, epic, member, pipeline, heartbeat=None):
            raise autopilot.AutopilotError("boom")

        with self.assertRaises(autopilot.AutopilotError):
            autopilot.run(self.root, "ep", member_driver=driver,
                          out=lambda *_: None)
        self.assertEqual(self._read("ep")["state"], "aborted")

    def test_run_keyboard_interrupt_mid_drive_leaves_heartbeat_aborted(self):
        _make_epic(self.root, "ep", [("a", "low")])

        def driver(root, epic, member, pipeline, heartbeat=None):
            raise KeyboardInterrupt()

        with self.assertRaises(KeyboardInterrupt):
            autopilot.run(self.root, "ep", member_driver=driver,
                          out=lambda *_: None)
        self.assertEqual(self._read("ep")["state"], "aborted")

    def test_run_clean_finish_is_not_overwritten_by_abort_handling(self):
        _make_epic(self.root, "ep", [("a", "low")])

        def driver(root, epic, member, pipeline, heartbeat=None):
            return autopilot.MemberResult(outcome="shipped", pr_url="http://pr/a")

        autopilot.run(self.root, "ep", member_driver=driver,
                      sync_fn=lambda *a, **k: None, out=lambda *_: None)
        self.assertEqual(self._read("ep")["state"], "finished")

    def test_run_member_autopilot_error_mid_drive_leaves_heartbeat_aborted(self):
        _make_epic(self.root, "ep", [("a", "low")])

        def driver():
            raise autopilot.AutopilotError("boom")

        with self.assertRaises(autopilot.AutopilotError):
            autopilot.run_member(self.root, "ep", "a", driver=driver,
                                 out=lambda *_: None)
        self.assertEqual(self._read("ep")["state"], "aborted")

    def test_run_member_keyboard_interrupt_mid_drive_leaves_heartbeat_aborted(self):
        _make_epic(self.root, "ep", [("a", "low")])

        def driver():
            raise KeyboardInterrupt()

        with self.assertRaises(KeyboardInterrupt):
            autopilot.run_member(self.root, "ep", "a", driver=driver,
                                 out=lambda *_: None)
        self.assertEqual(self._read("ep")["state"], "aborted")

    def test_run_member_clean_finish_is_not_overwritten_by_abort_handling(self):
        _make_epic(self.root, "ep", [("a", "low")])

        def driver():
            return autopilot.MemberResult(outcome="shipped", pr_url="http://pr/a")

        autopilot.run_member(self.root, "ep", "a", driver=driver,
                             out=lambda *_: None)
        self.assertEqual(self._read("ep")["state"], "finished")

    def test_run_sigterm_handler_writes_heartbeat_aborted_once(self):
        # SIGTERM has no default Python exception, so run() installs its own
        # handler; invoking it (as a real signal delivery would) must write
        # the abort exactly once. `_terminate_process` (the handler's
        # re-raise-the-default-disposition step) is stubbed so the test
        # process itself is never sent a real SIGTERM.
        _make_epic(self.root, "ep", [("a", "low")])
        kill_calls = []

        def driver(root, epic, member, pipeline, heartbeat=None):
            sigterm_handler = signal.getsignal(signal.SIGTERM)
            orig_terminate = autopilot._terminate_process
            autopilot._terminate_process = lambda signum: kill_calls.append(signum)
            try:
                sigterm_handler(signal.SIGTERM, None)
            finally:
                autopilot._terminate_process = orig_terminate
            return autopilot.MemberResult(outcome="shipped", pr_url="http://pr/a")

        hb = _SnapshotHeartbeat(self.root, "ep")
        autopilot.run(self.root, "ep", member_driver=driver, heartbeat=hb,
                      sync_fn=lambda *a, **k: None, out=lambda *_: None)

        aborted = [s for s in hb.snapshots if s["state"] == "aborted"]
        self.assertEqual(len(aborted), 1)
        self.assertEqual(kill_calls, [signal.SIGTERM])

    def test_run_member_sigterm_handler_writes_heartbeat_aborted_once(self):
        _make_epic(self.root, "ep", [("a", "low")])
        kill_calls = []

        def driver():
            sigterm_handler = signal.getsignal(signal.SIGTERM)
            orig_terminate = autopilot._terminate_process
            autopilot._terminate_process = lambda signum: kill_calls.append(signum)
            try:
                sigterm_handler(signal.SIGTERM, None)
            finally:
                autopilot._terminate_process = orig_terminate
            return autopilot.MemberResult(outcome="shipped", pr_url="http://pr/a")

        hb = _SnapshotHeartbeat(self.root, "ep")
        autopilot.run_member(self.root, "ep", "a", driver=driver, heartbeat=hb,
                             out=lambda *_: None)

        aborted = [s for s in hb.snapshots if s["state"] == "aborted"]
        self.assertEqual(len(aborted), 1)
        self.assertEqual(kill_calls, [signal.SIGTERM])


class HeartbeatSessionIdTest(AutopilotTestBase):
    """The session id must land on the driving member's roster entry as soon as
    the first driven turn yields one — not only at the terminal outcome — so a
    parked/openable card always has a resume handle while still `driving`."""

    def test_driving_member_carries_session_id_mid_drive(self):
        _make_epic(self.root, "ep", [("a", "low")])

        def command_fn(cmd, cwd):
            if isinstance(cmd, list) and cmd and cmd[0] == autopilot.WORKTREE_SH:
                os.makedirs(os.path.join(cwd, ".worktrees", cmd[1]),
                            exist_ok=True)
            return 0, "", ""

        def session_fn(stage, member, cwd, prompt, timeout, max_resumes,
                       on_session=None, model=None):
            # Turn 1 of the drive yields a session id mid-drive.
            if on_session is not None:
                on_session("sess-%s" % stage)
            return True, "sess-%s" % stage, None

        hb = _SnapshotHeartbeat(self.root, "ep")
        hb.run_started([_member("a")], [], "default")
        autopilot.drive_member(
            self.root, "ep", _member("a"),
            [{"stage": "plan"}, {"stage": "build"}],
            session_fn=session_fn, gate_fn=lambda *a: 0,
            command_fn=command_fn, out=lambda *_: None, heartbeat=hb)

        # Some snapshot shows the member still `driving` AND already carrying
        # its session id — the mid-drive record, before any terminal outcome.
        driving_with_sid = [
            r for snap in hb.snapshots for r in snap["roster"]
            if r["slug"] == "a" and r["state"] == "driving"
            and r.get("session_id")]
        self.assertTrue(driving_with_sid)


if __name__ == "__main__":
    unittest.main()
