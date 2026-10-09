#!/usr/bin/env python3
"""Shipped-text tests pinning the /s:epic-grill prose contracts: the planner
instruction names the member's own worktree, the harness body records the
`**Queued:**` slug its final round depends on, and the plan emission guide
admits the provisional `PLANNER` ledger value."""

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


if __name__ == "__main__":
    unittest.main()
