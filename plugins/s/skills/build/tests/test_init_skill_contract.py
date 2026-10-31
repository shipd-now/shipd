#!/usr/bin/env python3
"""Shipped-text tests pinning the /s:init contract: the skill and its harness
body name the sections and engine verbs; the trigger phrase is claimed by one
skill; the registry files carry the command; the shared needs-setup reference
names the three actions; the constitution starter is commented; and the seven
layout-requiring skills route through the reference and carry none of their
former missing-layout handling."""

import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
ROOT = os.path.normpath(os.path.join(PLUGIN, "..", ".."))
SKILLS_DIR = os.path.join(PLUGIN, "skills")
REFS = os.path.join(SKILLS_DIR, "init", "references")
NEEDS_SETUP = "skills/init/references/needs-setup.md"
ROSTER = ("plan", "epic", "research", "autopilot", "status", "initiative",
          "build")
SECTIONS = ("layout", "config", "workspace", "wiki", "memory", "hooks", "gate")
RETIRED = ("created the first time a change is merged",
           "stop before searching", "ask scaffold-or-stop")


def _read(*parts):
    with open(os.path.join(*parts), encoding="utf-8") as fh:
        return fh.read()


def _norm(text):
    return " ".join(text.split())


class InitSkillContractTest(unittest.TestCase):
    def setUp(self):
        self.skill_raw = _read(SKILLS_DIR, "init", "SKILL.md")
        self.body_raw = _read(PLUGIN, "harness", "bodies", "init.md")
        self.skill = _norm(self.skill_raw)
        self.body = _norm(self.body_raw)

    def test_frontmatter_names_the_skill(self):
        self.assertRegex(self.skill_raw, r"(?m)^name: init$")

    def test_body_has_description_marker(self):
        self.assertRegex(self.body_raw.splitlines()[0],
                         r"^<!-- description: .+ -->$")

    def test_only_init_claims_the_slash_command(self):
        claiming = []
        for name in sorted(
                n for n in os.listdir(SKILLS_DIR)
                if os.path.isfile(os.path.join(SKILLS_DIR, n, "SKILL.md"))):
            if '"/s:init"' in _norm(_read(SKILLS_DIR, name, "SKILL.md")):
                claiming.append(name)
        self.assertEqual(claiming, ["init"])

    def test_registry_files_mention_the_command(self):
        for rel in ("README.md", os.path.join("docs", "cheatsheet.md"),
                    "AGENTS.md"):
            self.assertIn("/s:init", _read(ROOT, rel), rel)

    def test_both_texts_carry_the_vocabulary(self):
        tokens = SECTIONS + ("config set", "spec_status.py init",
                             "init-status", "constitution-starter.md")
        for label, text in (("skill", self.skill), ("body", self.body)):
            for token in tokens:
                self.assertIn(token, text, "%s missing %r" % (label, token))
        self.assertIn("AskUserQuestion", self.skill)

    def test_needs_setup_reference_names_the_actions(self):
        text = _norm(_read(REFS, "needs-setup.md"))
        for token in ("init-status", "--unattended", "action:", "none",
                      "scaffold", "wizard", "/s:init"):
            self.assertIn(token, text)

    def test_constitution_starter_is_commented(self):
        path = os.path.join(REFS, "constitution-starter.md")
        self.assertTrue(os.path.isfile(path))
        self.assertIn("<!--", _read(path))

    def test_roster_points_at_the_reference(self):
        for name in ROSTER:
            for label, text in (
                    ("SKILL.md", _read(SKILLS_DIR, name, "SKILL.md")),
                    ("body", _read(PLUGIN, "harness", "bodies",
                                   name + ".md"))):
                self.assertIn(NEEDS_SETUP, _norm(text),
                              "%s %s lacks the pointer" % (name, label))

    def test_retired_missing_layout_phrases_are_gone(self):
        for name in ROSTER:
            for label, text in (
                    ("SKILL.md", _read(SKILLS_DIR, name, "SKILL.md")),
                    ("body", _read(PLUGIN, "harness", "bodies",
                                   name + ".md"))):
                for phrase in RETIRED:
                    self.assertNotIn(phrase, _norm(text),
                                     "%s %s keeps %r" % (name, label, phrase))


if __name__ == "__main__":
    unittest.main()
