#!/usr/bin/env python3
"""Shipped-text tests pinning the harness plan mode guard: the shared
reference exists with its doc-type marker and part names, and every writing
skill's SKILL.md carries the inline clause and the pointer. The roster is
computed as every skill except the read-only five, so a new skill fails until
it adds the clause. The plan skill also names the case in its stop list."""

import glob
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
CLAUSE = "Harness plan mode never replaces this skill's output."
POINTER = "skills/document/references/harness-plan-mode.md"
READ_ONLY = {"duck", "drift", "explain", "memory", "review"}
REFERENCE = os.path.join(PLUGIN, "skills", "document", "references", "harness-plan-mode.md")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _skills():
    """Return {skill: skill_md_path} for every skill."""
    return {
        os.path.basename(os.path.dirname(p)): p
        for p in sorted(glob.glob(os.path.join(PLUGIN, "skills", "*", "SKILL.md")))
    }


class PlanModeGuardContractTest(unittest.TestCase):
    def test_reference_exists_with_marker(self):
        self.assertTrue(os.path.exists(REFERENCE))
        self.assertEqual(_read(REFERENCE).splitlines()[0], "<!-- doc-type: reference -->")

    def test_reference_names_its_parts(self):
        text = _read(REFERENCE)
        for heading in ("The rule", "Read-only steps", "Writes", "What never happens", "The stop message"):
            self.assertIn(heading, text)

    def test_roster_is_large_enough(self):
        roster = {s for s in _skills() if s not in READ_ONLY}
        self.assertGreaterEqual(len(roster), 25)

    def test_every_writing_skill_carries_clause_and_pointer(self):
        for skill, path in _skills().items():
            if skill in READ_ONLY:
                continue
            text = _read(path)
            with self.subTest(skill=skill):
                self.assertIn(CLAUSE, text)
                self.assertIn(POINTER, text)

    def test_read_only_skills_carry_no_clause(self):
        for skill, path in _skills().items():
            if skill in READ_ONLY:
                with self.subTest(skill=skill):
                    self.assertNotIn(CLAUSE, _read(path))

    def test_plan_stop_list_names_harness_plan_mode(self):
        self.assertIn("- **Harness plan mode** —", _read(_skills()["plan"]))


if __name__ == "__main__":
    unittest.main()
