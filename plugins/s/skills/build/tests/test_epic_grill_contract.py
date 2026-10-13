#!/usr/bin/env python3
"""Shipped-text tests pinning the /s:epic-grill prose contracts: the planner
instruction names the member's own worktree, the harness body records the
`**Queued:**` slug its final round depends on, and the plan emission guide
admits the provisional `PLANNER` ledger value. Three more pin the
`**Relied on by:**` field in the planner instruction in `SKILL.md`, the
harness body, and the emission guide. A fourth pins "re-run the consistency
pass" in `SKILL.md` and the harness body."""

import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.normpath(os.path.join(HERE, "..", "..", ".."))


def _read(*parts):
    with open(os.path.join(PLUGIN, *parts), encoding="utf-8") as fh:
        return fh.read()


class EpicGrillContractTest(unittest.TestCase):
    def test_planner_instruction_names_its_own_worktree(self):
        skill = _read("skills", "epic-grill", "SKILL.md")
        self.assertIn("Work in its worktree `.worktrees/<member>`", skill)

    def test_harness_body_records_queued_slug(self):
        body = _read("harness", "bodies", "epic-grill.md")
        self.assertIn("`**Queued:**` when the oracle", body)

    def test_emission_guide_admits_planner_value(self):
        guide = _read("skills", "plan", "references", "emission.md")
        self.assertIn("provisional `PLANNER`", guide)

    def test_skill_planner_instruction_appends_relied_on_by(self):
        skill = _read("skills", "epic-grill", "SKILL.md")
        self.assertIn(
            "append your slug to that entry's `**Relied on by:**` field", skill
        )

    def test_harness_body_names_relied_on_by(self):
        body = _read("harness", "bodies", "epic-grill.md")
        self.assertIn("`**Relied on by:**`", body)

    def test_emission_guide_names_relied_on_by(self):
        guide = _read("skills", "plan", "references", "emission.md")
        self.assertIn("`- **Relied on by:**`", guide)

    def test_amend_gate_reruns_consistency_pass(self):
        skill = _read("skills", "epic-grill", "SKILL.md")
        body = _read("harness", "bodies", "epic-grill.md")
        self.assertIn("re-run the consistency pass", skill)
        self.assertIn("re-run the consistency pass", body)
        self.assertIn("without re-checking again", skill)
        self.assertIn("without re-checking again", " ".join(body.split()))


if __name__ == "__main__":
    unittest.main()
