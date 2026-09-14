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

# Matches one `## References` table row naming a reference file, capturing
# its filename and the "Load when" cell text, e.g.
# "| `${CLAUDE_PLUGIN_ROOT}/skills/review/references/spec-aware.md` | ... |".
TABLE_ROW_RE = re.compile(
    r"^\|\s*`?\$\{CLAUDE_PLUGIN_ROOT\}/skills/review/references/"
    r"([\w-]+\.md)`?\s*\|\s*(.+?)\s*\|\s*$",
    re.MULTILINE)

# Lowercased tokens too generic to count as evidence two sentences agree.
STOPWORDS = frozenset((
    "this", "that", "when", "only", "file", "reads", "skill", "which",
    "with", "been", "they", "from", "into",
))

MIN_SHARED_CONTENT_WORDS = 3


def _read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _content_words(text):
    """Lowercased alphabetic tokens of length >= 4, minus STOPWORDS.

    Backticks and other punctuation fall out for free: only letter runs are
    matched, so "`--json`" yields "json" and "poster's" yields "poster".
    """
    return {
        word.lower()
        for word in re.findall(r"[A-Za-z]+", text)
        if len(word) >= 4 and word.lower() not in STOPWORDS
    }


def _reference_condition_sentence(path):
    """The paragraph directly under the level-1 title in a reference file.

    Same region `test_each_reference_opens_with_title_and_condition` already
    inspects: the non-blank lines after the title, up to the next blank
    line, joined into one string.
    """
    lines = _read(path).splitlines()
    title_idx = next(i for i, ln in enumerate(lines) if ln.strip())
    condition_lines = []
    for ln in lines[title_idx + 1:]:
        if not ln.strip():
            if condition_lines:
                break
            continue
        condition_lines.append(ln)
    return " ".join(condition_lines)


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


class TableConditionAgreementTest(unittest.TestCase):
    """Pins agreement between a `## References` table cell and its file.

    The table's "Load when" cell is a summary a reviewer reads without
    opening the reference; the reference file states the same condition in
    full. If the cell drifts from the file (as it once did for
    spec-aware.md, dropping the auto-trigger half of the rule), a reader who
    trusts only the table misses the real trigger. This does not require the
    two texts match exactly — only that they share enough substantive
    vocabulary to be recognizably the same condition.
    """

    def test_table_cell_agrees_with_reference_condition(self):
        table_rows = TABLE_ROW_RE.findall(_read(SKILL_MD))
        self.assertTrue(
            table_rows, "expected at least one reference row in the "
            "SKILL.md References table")
        for name, cell in table_rows:
            with self.subTest(reference=name):
                path = os.path.join(REFERENCES_DIR, name)
                sentence = _reference_condition_sentence(path)
                cell_words = _content_words(cell)
                sentence_words = _content_words(sentence)
                shared = cell_words & sentence_words
                self.assertGreaterEqual(
                    len(shared), MIN_SHARED_CONTENT_WORDS,
                    f"{name}: table cell {cell!r} shares only "
                    f"{sorted(shared)} with its file's condition sentence "
                    f"{sentence!r} — need at least "
                    f"{MIN_SHARED_CONTENT_WORDS} shared content words")


if __name__ == "__main__":
    unittest.main()
