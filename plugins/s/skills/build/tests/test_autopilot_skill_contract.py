#!/usr/bin/env python3
"""Shipped-text tests pinning the /s:autopilot prose contracts: the launch
preflight, the pre-build drift step, the park-and-continue failure contract,
the bounded merge wait, and the unattended stage instructions. They hold the
same vocabulary across the skill, its harness body, and its reference, so the
three cannot drift apart."""

import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
REPO = os.path.normpath(os.path.join(PLUGIN, "..", ".."))

PARK_REASONS = (
    "grade-failed",
    "gate-rejected",
    "command-failed",
    "sync-conflict",
    "drift-error",
    "drift-conflict",
    "replan-failed",
)

NO_HUMAN = "No human is available during this run"


def _read(*parts):
    with open(os.path.join(PLUGIN, *parts), encoding="utf-8") as fh:
        return fh.read()


def _read_repo(*parts):
    with open(os.path.join(REPO, *parts), encoding="utf-8") as fh:
        return fh.read()


class AutopilotSkillContractTest(unittest.TestCase):
    def setUp(self):
        self.skill = _read("skills", "autopilot", "SKILL.md")
        self.body = _read("harness", "bodies", "autopilot.md")
        self.reference = _read("harness", "references", "autopilot.md")

    def test_skill_runs_the_launch_preflight(self):
        self.assertIn("--preflight", self.skill)
        self.assertIn("preflight:", self.skill)

    def test_confirmation_is_the_last_question(self):
        self.assertIn("the last question", self.skill)

    def test_skill_names_the_sync_and_drift_measurement(self):
        self.assertIn("git fetch origin main", self.skill)
        self.assertIn("git merge --no-edit origin/main", self.skill)
        self.assertIn(
            'spec_status.py" --root .worktrees/<member> drift <member>'
            " --base origin/main --json",
            self.skill,
        )

    def test_skill_names_the_drift_judgment(self):
        self.assertIn("/s:drift <member> --base origin/main --json", self.skill)
        self.assertIn("verdicts[0].verdict", self.skill)
        for verdict in ("holds", "revise", "conflict"):
            self.assertIn(verdict, self.skill)

    def test_skill_names_the_replan_regate(self):
        self.assertIn("spec_gate.py <member> --base origin/main", self.skill)
        self.assertIn("--check", self.skill)

    def test_skill_states_the_absence_of_a_human(self):
        self.assertIn(NO_HUMAN, self.skill)
        self.assertIn("oracle-lookup", self.skill)
        self.assertNotIn("s:oracle", self.skill)
        self.assertGreaterEqual(self.skill.count(NO_HUMAN), 2)

    def test_skill_parks_with_the_reason_vocabulary(self):
        self.assertIn("--outcome parked", self.skill)
        for reason in PARK_REASONS:
            self.assertIn(reason, self.skill)

    def test_skill_holds_dependents_and_waits_on_merges(self):
        self.assertIn("held by", self.skill)
        self.assertIn("gh pr view change/<dep> --json state", self.skill)
        self.assertIn("60 seconds", self.skill)
        self.assertIn("MERGED", self.skill)
        self.assertIn("CLOSED", self.skill)
        self.assertIn("Parked", self.skill)

    def test_skill_drops_the_ask_contract(self):
        self.assertNotIn("ask, never park", self.skill)
        self.assertNotIn("puts the situation to the user", self.skill)

    def test_body_carries_the_vocabulary(self):
        flat = " ".join(self.body.split())
        for token in ("--preflight", "fail", "parks", "drift", "Parked"):
            self.assertIn(token, flat)

    def test_reference_states_the_prebuild_drift_step(self):
        self.assertIn("## Pre-build drift step", self.reference)
        self.assertIn("park", self.reference)
        self.assertIn("held by", self.reference)
        for reason in PARK_REASONS:
            self.assertIn(reason, self.reference)

    def test_readme_still_lists_the_autopilot_command(self):
        self.assertIn("`/s:autopilot`", _read_repo("README.md"))

    def test_the_harness_text_orders_by_the_waves_mode(self):
        flat_body = " ".join(self.body.split())
        flat_reference = " ".join(self.reference.split())
        for text in (flat_body, flat_reference):
            self.assertIn("--waves", text)
            self.assertNotIn("dry run's order", text)
        self.assertIn("--waves", flat_reference)
        self.assertNotIn("Member order (risk ascending)", flat_reference)


if __name__ == "__main__":
    unittest.main()
