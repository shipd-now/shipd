#!/usr/bin/env python3
"""Budget and shape tests for every skill's frontmatter ``description``.

Claude Code fits the skill listing into a fixed share of the context window
and drops descriptions to make room, so each description stays short: its
harness body one-liner plus its ``Trigger phrases:`` clause, within
``DESCRIPTION_BUDGET`` folded characters.
"""

import glob
import os
import re
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
SKILLS = os.path.normpath(os.path.join(HERE, "..", ".."))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import harness_bodies as hb  # noqa: E402

DESCRIPTION_BUDGET = 300

SHAPE_RE = re.compile(
    r'^(?P<lead>.+) Trigger phrases: '
    r'(?P<p>"[^"]+"(, "[^"]+")*)\.$'
)


def folded_description(path):
    """The frontmatter ``description: >-`` block, folded as YAML folds it.

    Returns None when the frontmatter has no ``description: >-`` block, so the
    shape test can name the skill instead of erroring.
    """
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    lines = text.split("---")[1].split("\n")
    if "description: >-" not in lines:
        return None
    start = lines.index("description: >-")
    parts = []
    for line in lines[start + 1:]:
        if not line.startswith("  "):
            break
        parts.append(line.strip())
    return " ".join(parts).strip()


def skill_descriptions():
    found = {}
    for path in sorted(glob.glob(os.path.join(SKILLS, "*", "SKILL.md"))):
        found[os.path.basename(os.path.dirname(path))] = folded_description(path)
    return found


def over_budget(descriptions):
    return [
        "%s (%d characters)" % (name, len(text))
        for name, text in sorted(descriptions.items())
        if text is not None and len(text) > DESCRIPTION_BUDGET
    ]


def shape_failures(descriptions, one_liner):
    failures = []
    for name, text in sorted(descriptions.items()):
        if text is None:
            failures.append("%s: description is not a folded >- block" % name)
            continue
        match = SHAPE_RE.match(text)
        if match is None:
            failures.append("%s: not '<one-liner> Trigger phrases: ...'" % name)
            continue
        if match.group("lead") != one_liner(name):
            failures.append("%s: lead is not the body one-liner" % name)
        if '"/s:%s"' % name not in match.group("p").split(", "):
            failures.append('%s: missing "/s:%s" phrase' % (name, name))
    return failures


class SkillDescriptionTest(unittest.TestCase):
    def test_skills_found(self):
        self.assertTrue(skill_descriptions())

    def test_every_description_is_within_budget(self):
        failing = over_budget(skill_descriptions())
        self.assertEqual(
            [], failing,
            "over the %d-character budget: %s"
            % (DESCRIPTION_BUDGET, "; ".join(failing)),
        )

    def test_every_description_is_the_body_one_liner_plus_triggers(self):
        failing = shape_failures(skill_descriptions(), hb.description)
        self.assertEqual([], failing, "; ".join(failing))

    def test_a_301_character_description_is_reported(self):
        text = "x" * (DESCRIPTION_BUDGET + 1)
        self.assertEqual(301, len(text))
        failing = over_budget({"fixture": text})
        self.assertEqual(1, len(failing))
        self.assertIn("fixture", failing[0])
        self.assertIn("301", failing[0])

    def test_a_drifted_one_liner_is_reported(self):
        failing = shape_failures(
            {"fixture": 'Old line. Trigger phrases: "/s:fixture".'},
            lambda name: "New line.",
        )
        self.assertEqual(["fixture: lead is not the body one-liner"], failing)

    def test_a_missing_slash_phrase_is_reported(self):
        failing = shape_failures(
            {"fixture": 'Line. Trigger phrases: "fixture".'},
            lambda name: "Line.",
        )
        self.assertEqual(['fixture: missing "/s:fixture" phrase'], failing)

    def test_a_missing_folded_block_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "SKILL.md")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("---\nname: fixture\ndescription: plain\n---\n")
            text = folded_description(path)
        self.assertIsNone(text)
        self.assertEqual([], over_budget({"fixture": text}))
        self.assertEqual(
            ["fixture: description is not a folded >- block"],
            shape_failures({"fixture": text}, lambda name: "Line."),
        )


if __name__ == "__main__":
    unittest.main()
