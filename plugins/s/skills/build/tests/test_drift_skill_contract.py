#!/usr/bin/env python3
"""Shipped-text tests pinning the /s:drift contract: the skill and its harness
body name the verb, its flags, the three verdicts, the evidence commands, the
`## Drift verdicts` block, and the exit codes; the skill is read-only; the
trigger phrase is claimed by exactly one skill; and the registry files carry
the `/s:drift` row."""

import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
ROOT = os.path.normpath(os.path.join(PLUGIN, "..", ".."))
SKILLS_DIR = os.path.join(PLUGIN, "skills")


def _read(*parts):
    with open(os.path.join(*parts), encoding="utf-8") as fh:
        return fh.read()


def _norm(text):
    return " ".join(text.split())


REQUIRED = (
    "spec_status.py", "drift", "--epic", "--base", "--json", "holds",
    "revise", "conflict", "## Drift verdicts", "verdicts:", "clean:",
    "skipped:", "cat change", "cat epic", "cat verified",
    "grep -l -w -F", "`0`", "`4`", "`1`", "`2`",
)
FORBIDDEN = ("AskUserQuestion", "subagent", "sub-agent", "git fetch")


class DriftSkillContractTest(unittest.TestCase):
    def setUp(self):
        self.skill_raw = _read(PLUGIN, "skills", "drift", "SKILL.md")
        self.body_raw = _read(PLUGIN, "harness", "bodies", "drift.md")
        self.skill = _norm(self.skill_raw)
        self.body = _norm(self.body_raw)

    def test_frontmatter_names_the_skill(self):
        self.assertRegex(self.skill_raw, r"(?m)^name: drift$")

    def test_both_texts_carry_the_vocabulary(self):
        for label, text in (("skill", self.skill), ("body", self.body)):
            for token in REQUIRED:
                self.assertIn(token, text, "%s missing %r" % (label, token))

    def test_skill_is_read_only_and_dialog_free(self):
        for token in FORBIDDEN:
            self.assertNotIn(token, self.skill)

    def test_body_is_ungated_with_description_marker(self):
        first = self.body_raw.splitlines()[0]
        self.assertRegex(first, r"^<!-- description: .+ -->$")
        self.assertNotIn("<!-- if:", self.body_raw)
        for token in ("subagent", "sub-agent", "AskUserQuestion"):
            self.assertNotIn(token, self.body)

    def test_only_drift_claims_the_slash_command(self):
        claiming = []
        for name in sorted(
                n for n in os.listdir(SKILLS_DIR)
                if os.path.isfile(os.path.join(SKILLS_DIR, n, "SKILL.md"))):
            text = _norm(_read(SKILLS_DIR, name, "SKILL.md"))
            if '"/s:drift"' in text:
                claiming.append(name)
        self.assertEqual(claiming, ["drift"])

    def test_registry_files_mention_the_command(self):
        for rel in ("README.md", os.path.join("docs", "cheatsheet.md"),
                    "AGENTS.md"):
            self.assertIn("/s:drift", _read(ROOT, rel), rel)


if __name__ == "__main__":
    unittest.main()
