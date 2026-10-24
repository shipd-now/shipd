#!/usr/bin/env python3
"""Shipped-text tests pinning the /s:plan-deep contract: the skill and its
harness body cite the one shared rubric path and name the engine verbs, the
ledger marker, and the endings; neither sets a status directly; the trigger
phrase is claimed by exactly one skill; the registry files carry the command;
and only the rubric file owns the Novelty scale."""

import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
ROOT = os.path.normpath(os.path.join(PLUGIN, "..", ".."))
SKILLS_DIR = os.path.join(PLUGIN, "skills")
RUBRIC = os.path.join(SKILLS_DIR, "epic", "references", "risk-rubric.md")


def _read(*parts):
    with open(os.path.join(*parts), encoding="utf-8") as fh:
        return fh.read()


def _norm(text):
    return " ".join(text.split())


REQUIRED = (
    "skills/epic/references/risk-rubric.md", "spec_gate.py", "locate",
    "cat change", "cat epic", "/s:research", "cat research",
    "**Answered by:** USER", "/s:epic <epic> amend", "--preflight",
    "/s:build", "/s:autopilot <epic>",
)
# Split so this file does not itself match the search below.
KEYSTONE = "Someone in our team " + "knows how to do this"


class PlanDeepSkillContractTest(unittest.TestCase):
    def setUp(self):
        self.skill_raw = _read(SKILLS_DIR, "plan-deep", "SKILL.md")
        self.body_raw = _read(PLUGIN, "harness", "bodies", "plan-deep.md")
        self.skill = _norm(self.skill_raw)
        self.body = _norm(self.body_raw)

    def test_frontmatter_names_the_skill(self):
        self.assertRegex(self.skill_raw, r"(?m)^name: plan-deep$")

    def test_both_texts_carry_the_vocabulary(self):
        for label, text in (("skill", self.skill), ("body", self.body)):
            for token in REQUIRED:
                self.assertIn(token, text, "%s missing %r" % (label, token))

    def test_neither_text_sets_a_status(self):
        self.assertNotIn("set-status", self.skill)
        self.assertNotIn("set-status", self.body)

    def test_body_has_description_marker(self):
        self.assertRegex(self.body_raw.splitlines()[0],
                         r"^<!-- description: .+ -->$")

    def test_only_plan_deep_claims_the_slash_command(self):
        claiming = []
        for name in sorted(
                n for n in os.listdir(SKILLS_DIR)
                if os.path.isfile(os.path.join(SKILLS_DIR, n, "SKILL.md"))):
            if '"/s:plan-deep"' in _norm(_read(SKILLS_DIR, name, "SKILL.md")):
                claiming.append(name)
        self.assertEqual(claiming, ["plan-deep"])

    def test_registry_files_mention_the_command(self):
        for rel in ("README.md", os.path.join("docs", "cheatsheet.md"),
                    "AGENTS.md"):
            self.assertIn("/s:plan-deep", _read(ROOT, rel), rel)

    def test_rubric_carries_its_vocabulary(self):
        rubric = _read(RUBRIC)
        for token in ("Novelty", "Relied on by", "rabbit hole"):
            self.assertIn(token, rubric)

    def test_old_rubric_path_is_gone(self):
        self.assertFalse(os.path.exists(
            os.path.join(SKILLS_DIR, "plan-deep", "references", "rubric.md")))

    def test_epic_cites_the_rubric(self):
        path = "skills/epic/references/risk-rubric.md"
        self.assertIn(path, _read(SKILLS_DIR, "epic", "SKILL.md"))
        self.assertIn(
            path, _norm(_read(PLUGIN, "harness", "bodies", "epic.md")))

    def test_only_the_rubric_owns_the_novelty_scale(self):
        owners = []
        for base in (SKILLS_DIR, os.path.join(PLUGIN, "harness")):
            for dirpath, _dirs, files in os.walk(base):
                for fname in files:
                    path = os.path.join(dirpath, fname)
                    try:
                        text = _read(path)
                    except (UnicodeDecodeError, OSError):
                        continue
                    if KEYSTONE in text:
                        owners.append(os.path.normpath(path))
        self.assertEqual(owners, [os.path.normpath(RUBRIC)])


if __name__ == "__main__":
    unittest.main()
