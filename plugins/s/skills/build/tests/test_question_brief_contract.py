#!/usr/bin/env python3
"""Shipped-text tests pinning the shared question brief: the reference exists
with its doc-type marker and part names, and every skill that asks the user a
question (its SKILL.md mentions the dialog tool) and its harness body point to
it. The roster is computed, so a skill that gains its first dialog fails until
it adds the pointer. A last test bans the retired phrases that put a whole
multi-question round into one dialog."""

import glob
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
POINTER = "skills/document/references/question-brief.md"
REFERENCE = os.path.join(PLUGIN, "skills", "document", "references", "question-brief.md")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _roster():
    """Return {skill: (skill_md_path, body_path_or_None)} for asking skills."""
    out = {}
    for path in sorted(glob.glob(os.path.join(PLUGIN, "skills", "*", "SKILL.md"))):
        if "AskUserQuestion" not in _read(path):
            continue
        skill = os.path.basename(os.path.dirname(path))
        body = os.path.join(PLUGIN, "harness", "bodies", skill + ".md")
        out[skill] = (path, body if os.path.exists(body) else None)
    return out


class QuestionBriefContractTest(unittest.TestCase):
    def test_reference_exists_with_marker(self):
        self.assertTrue(os.path.exists(REFERENCE))
        text = _read(REFERENCE)
        self.assertEqual(text.splitlines()[0], "<!-- doc-type: reference -->")

    def test_reference_names_its_parts(self):
        text = _read(REFERENCE)
        for heading in ("The four parts", "Where the brief goes", "Worked examples"):
            self.assertIn(heading, text)

    def test_roster_is_large_enough(self):
        self.assertGreaterEqual(len(_roster()), 14)

    def test_every_asking_skill_and_body_points_to_the_reference(self):
        for skill, (path, body) in _roster().items():
            with self.subTest(skill=skill, kind="SKILL.md"):
                self.assertIn(POINTER, _read(path))
            if body:
                with self.subTest(skill=skill, kind="body"):
                    self.assertIn(POINTER, _read(body))

    def test_no_multi_question_dialog_phrases(self):
        banned = (
            "single AskUserQuestion call",
            "Put the whole round in a single question dialog",
            "Put each round in a single question dialog",
            "Put both questions in a single question dialog",
        )
        for skill, (path, body) in _roster().items():
            for kind, f in (("SKILL.md", path), ("body", body)):
                if not f:
                    continue
                text = _read(f)
                for phrase in banned:
                    with self.subTest(skill=skill, kind=kind, phrase=phrase):
                        self.assertNotIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
