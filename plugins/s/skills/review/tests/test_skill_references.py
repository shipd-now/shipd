#!/usr/bin/env python3
"""Structure tests for the `/s:review` skill's reference split.

`SKILL.md` used to carry every review-time concern inline, including three
sections that only fire on a condition (spec-aware review, `--json` machine
output, and PR posting). This module pins the split: those three sections
live under `references/`, `SKILL.md` names every file there by path, every
named path resolves, each reference states its own load condition, the
hot-path guidance (workflow, severity rubric, difftastic probe) stays inline,
and neither of the other two rubric surfaces (the copilot skill body and the
harness command body) points at a reference path that only resolves relative
to `${CLAUDE_PLUGIN_ROOT}`.

Pure text-structure assertions — no production module is imported, since the
thing under test is prose shape, not code.
"""

import glob
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REVIEW_SKILL_DIR = os.path.normpath(os.path.join(HERE, ".."))
PLUGIN_S_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))

SKILL_MD = os.path.join(REVIEW_SKILL_DIR, "SKILL.md")
REFERENCES_DIR = os.path.join(REVIEW_SKILL_DIR, "references")
COPILOT_SKILL_MD = os.path.join(
    PLUGIN_S_ROOT, "integrations", "copilot", "SKILL.md")
HARNESS_REVIEW_BODY = os.path.join(
    PLUGIN_S_ROOT, "harness", "bodies", "review.md")

MOVED_HEADINGS = (
    "## Machine output mode",
    "## Posting to a PR",
    "## Spec-aware review",
)

# Matches a reference path as SKILL.md is expected to name it, e.g.
# "${CLAUDE_PLUGIN_ROOT}/skills/review/references/spec-aware.md".
REFERENCE_PATH_RE = re.compile(
    r"\$\{CLAUDE_PLUGIN_ROOT\}/skills/review/references/([\w-]+\.md)")

REFERENCES_UNDER_SKILL_RE = re.compile(r"skills/review/references/")


def _read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


class SkillMdStructureTest(unittest.TestCase):
    """Assertions about `SKILL.md` itself."""

    @classmethod
    def setUpClass(cls):
        cls.text = _read(SKILL_MD)
        cls.lines = cls.text.splitlines()

    def test_under_line_ceiling(self):
        self.assertLess(
            len(self.lines), 300,
            "SKILL.md must stay under 300 lines once the references split "
            "out the condition-gated sections")

    def test_no_moved_headings_remain(self):
        for heading in MOVED_HEADINGS:
            self.assertNotIn(
                heading, self.text,
                f"{heading!r} should have moved to a reference file")

    def test_workflow_steps_stayed_inline(self):
        self.assertIn("## Workflow", self.text)
        self.assertIn("### 1. Map the change", self.text)
        self.assertIn("### 7. Check test coverage per finding", self.text)

    def test_severity_rubric_stayed_inline(self):
        self.assertIn("Severity rubric.", self.text)
        self.assertIn("**high**", self.text)
        self.assertIn("**medium**", self.text)
        self.assertIn("**low**", self.text)

    def test_difft_probe_stayed_inline(self):
        self.assertIn("command -v difft", self.text)

    def test_every_reference_file_is_named(self):
        named = set(REFERENCE_PATH_RE.findall(self.text))
        on_disk = {
            os.path.basename(p)
            for p in glob.glob(os.path.join(REFERENCES_DIR, "*.md"))
        }
        missing = on_disk - named
        self.assertFalse(
            missing,
            f"reference file(s) not named in SKILL.md: {sorted(missing)}")

    def test_every_named_reference_path_resolves(self):
        named = set(REFERENCE_PATH_RE.findall(self.text))
        self.assertTrue(named, "SKILL.md should name at least one reference")
        for name in named:
            path = os.path.join(REFERENCES_DIR, name)
            self.assertTrue(
                os.path.isfile(path),
                f"SKILL.md names {name!r}, but {path} does not exist")


class ReferenceFileStructureTest(unittest.TestCase):
    """Each file under `references/` states its own trigger up front."""

    def test_each_reference_opens_with_title_and_condition(self):
        paths = sorted(glob.glob(os.path.join(REFERENCES_DIR, "*.md")))
        self.assertTrue(paths, "expected at least one reference file")
        for path in paths:
            with self.subTest(path=path):
                lines = [ln for ln in _read(path).splitlines()]
                non_blank = [ln for ln in lines if ln.strip()]
                self.assertTrue(non_blank, f"{path} is empty")
                self.assertRegex(
                    non_blank[0], r"^# \S",
                    f"{path} must open with a level-1 title")
                self.assertFalse(
                    non_blank[0].startswith("## "),
                    f"{path} title must be level-1, not level-2")
                rest = "\n".join(non_blank[1:3])
                self.assertRegex(
                    rest, r"[Rr]eads this file",
                    f"{path} must state its load condition directly under "
                    "the title")


class OtherRubricSurfacesUntouchedTest(unittest.TestCase):
    """The copilot skill and the harness review body stay reference-free."""

    def test_copilot_skill_names_no_reference_path(self):
        text = _read(COPILOT_SKILL_MD)
        self.assertNotRegex(text, REFERENCES_UNDER_SKILL_RE)

    def test_harness_review_body_names_no_reference_path(self):
        text = _read(HARNESS_REVIEW_BODY)
        self.assertNotRegex(text, REFERENCES_UNDER_SKILL_RE)


if __name__ == "__main__":
    unittest.main()
