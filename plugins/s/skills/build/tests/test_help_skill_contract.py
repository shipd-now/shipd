#!/usr/bin/env python3
"""Shipped-text tests pinning the /s:help skill: its SKILL.md and harness body
name the three verdicts, the CLI help source, the no-model-memory rule and the
oracle route; the skill is read-only; the docs page, cheatsheet row and
AGENTS.md mention exist."""

import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
REPO = os.path.normpath(os.path.join(PLUGIN, "..", ".."))
SKILL = os.path.join(PLUGIN, "skills", "help", "SKILL.md")
BODY = os.path.join(PLUGIN, "harness", "bodies", "help.md")
NEEDLES = ("Supported", "Partly supported", "Not supported", "shipd --help", "model memory", "/s:ask")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


class HelpSkillContractTest(unittest.TestCase):
    def test_skill_and_body_name_the_contract(self):
        for path in (SKILL, BODY):
            text = _read(path)
            for needle in NEEDLES:
                self.assertIn(needle, text, "%s lacks %r" % (path, needle))

    def test_spec_gap_phrases(self):
        for path in (SKILL, BODY):
            text = " ".join(_read(path).split())
            self.assertIn("no question", text, path)
            self.assertIn("invent", text, path)
            self.assertIn("in the order to run them", text, path)
            self.assertIn("without invoking it", text, path)
            self.assertIn("Open a skill before you name its command", text, path)
        self.assertNotIn("help of the matching verb", " ".join(_read(SKILL).split()))

    def test_skill_announces_version_and_is_dialog_free(self):
        text = _read(SKILL)
        self.assertIn("plugin.json", text)
        self.assertNotIn("AskUserQuestion", text)

    def test_docs_page_exists(self):
        self.assertTrue(os.path.exists(os.path.join(REPO, "docs", "help.md")))

    def test_registrations_name_the_skill(self):
        for rel in ("docs/cheatsheet.md", "AGENTS.md"):
            self.assertIn("/s:help", _read(os.path.join(REPO, rel)), rel)


if __name__ == "__main__":
    unittest.main()
