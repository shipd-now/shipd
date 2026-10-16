#!/usr/bin/env python3
"""Tests for the ``/s:pr`` skill — its ``SKILL.md``, harness body, caller
edits, and registrations (shipd-pr pr-skill-writes, pr-callers).

``harness_bodies`` is imported from the build scripts the way
``test_room_skill.py`` imports it.
"""

import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
REPO_ROOT = os.path.normpath(os.path.join(PLUGIN_ROOT, "..", ".."))
BUILD_SCRIPTS = os.path.join(PLUGIN_ROOT, "skills", "build", "scripts")
if BUILD_SCRIPTS not in sys.path:
    sys.path.insert(0, BUILD_SCRIPTS)

import harness_bodies as hb  # noqa: E402

SKILL_PATH = os.path.join(PLUGIN_ROOT, "skills", "pr", "SKILL.md")
BUILD_SKILL = os.path.join(PLUGIN_ROOT, "skills", "build", "SKILL.md")
REFS = "R"
FILL = "gh pr create --fill"


def _read(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def _flat(text):
    return re.sub(r"\s+", " ", text)


class SkillWritesTest(unittest.TestCase):
    """pr-skill-writes."""

    def setUp(self):
        self.text = _read(SKILL_PATH)
        self.flat = _flat(self.text)

    def test_names_heading_lint_and_create_step(self):
        for needle in ("## ☕ Shipd Pull Request", "docs_lint.py",
                       "--body-file", "gh pr edit",
                       "/s:pr [--ticket <id>] [--draft] [--base <ref>]",
                       "<!-- doc-type: concept -->", "pr_title.py"):
            self.assertIn(needle, self.flat, needle)

    def test_frontmatter_names_the_skill(self):
        self.assertRegex(self.text, r"(?m)^name: pr$")

    def test_leaves_push_and_merge_to_callers(self):
        self.assertNotIn("git push", self.text)
        self.assertNotIn("gh pr merge", self.text)


class CallersTest(unittest.TestCase):
    """pr-callers."""

    def test_no_bare_fill_remains(self):
        offenders = []
        plugin_files = []
        for base, dirs, files in os.walk(PLUGIN_ROOT):
            dirs[:] = [d for d in dirs
                       if d not in ("tests", "__pycache__", ".git")]
            plugin_files.extend(os.path.join(base, f) for f in files)
        plugin_files.append(os.path.join(REPO_ROOT, "AGENTS.md"))
        for path in plugin_files:
            try:
                text = _read(path)
            except (UnicodeDecodeError, OSError):
                continue
            if FILL in _flat(text):
                offenders.append(os.path.relpath(path, REPO_ROOT))
        self.assertEqual(offenders, [])

    def test_draft_section_passes_the_flag(self):
        text = _read(BUILD_SKILL)
        start = text.index("### Draft mode")
        end = text.index("\n### ", start + 1)
        self.assertIn("/s:pr --draft", text[start:end])

    def test_registrations_name_the_skill(self):
        for rel in ("AGENTS.md", "README.md",
                    os.path.join("docs", "cheatsheet.md")):
            self.assertIn("/s:pr", _read(os.path.join(REPO_ROOT, rel)),
                          "%s does not name /s:pr" % rel)

    def test_body_renders(self):
        for flags in ((), ("background-tasks",)):
            out = hb.render("pr", flags, refs_dir=REFS)
            self.assertIn("/s:pr", out)


if __name__ == "__main__":
    unittest.main()
