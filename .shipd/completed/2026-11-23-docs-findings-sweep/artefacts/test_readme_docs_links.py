#!/usr/bin/env python3
"""Guard the root ``README.md`` (project-readme readme-docs-group-links).

The README is the repository's front page: install, nine docs group links,
and contributor notes. Nothing else tests it, so these checks keep its cap,
its six level-2 headings, its nine group links, and its relative links from
drifting. Stdlib only.
"""

import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
# tests -> build -> skills -> s -> plugins -> repository root
REPO_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", "..", ".."))
README = os.path.join(REPO_ROOT, "README.md")

LINE_CAP = 150

HEADINGS = [
    "## Install",
    "## Documentation",
    "## Structure",
    "## Adding a command",
    "## Adding a skill",
    "## After editing",
]

# The nine docs groups, in order, each with the one page its line links.
GROUPS = [
    ("Start here", "docs/getting-started.md"),
    ("Plan", "docs/plan.md"),
    ("Build", "docs/build.md"),
    ("Epics", "docs/epics.md"),
    ("Review and merge", "docs/semantic-review.md"),
    ("Multi-agent PRs", "docs/multi-agent-pr.md"),
    ("Knowledge", "docs/oracle.md"),
    ("Workspaces", "docs/workspaces.md"),
    ("Configure", "docs/customise.md"),
]

LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
EXTERNAL_RE = re.compile(r"^(https?:|mailto:|#)")


def read_lines(path=README):
    with open(path, encoding="utf-8") as fh:
        return fh.read().splitlines()


def prose_lines(lines):
    """The lines outside fenced code blocks."""
    kept, fenced = [], False
    for line in lines:
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            kept.append(line)
    return kept


def level_two_headings(lines):
    return [line.rstrip() for line in prose_lines(lines)
            if line.startswith("## ")]


def relative_links(lines):
    """Every markdown link target that is neither external nor an anchor."""
    return [target for line in prose_lines(lines)
            for target in LINK_RE.findall(line)
            if not EXTERNAL_RE.match(target)]


def missing_links(lines, root=REPO_ROOT):
    return [target for target in relative_links(lines)
            if not os.path.isfile(os.path.join(root, target.split("#")[0]))]


def group_items(lines):
    """The list items of ``## Documentation`` as ``(bold name, docs links)``."""
    prose = prose_lines(lines)
    start = prose.index("## Documentation") + 1
    end = next((i for i in range(start, len(prose))
                if prose[i].startswith("## ")), len(prose))
    items = []
    for line in prose[start:end]:
        if line.startswith("- "):
            items.append(line)
        elif items and line.startswith("  "):
            items[-1] += " " + line.strip()
    parsed = []
    for item in items:
        name = re.match(r"- \*\*(.+?)\*\*", item)
        links = [t for t in LINK_RE.findall(item) if t.startswith("docs/")]
        parsed.append((name.group(1) if name else None, links))
    return parsed


class ReadmeTest(unittest.TestCase):
    def setUp(self):
        self.lines = read_lines()

    def test_readme_fits_its_line_cap(self):
        self.assertLessEqual(len(self.lines), LINE_CAP)

    def test_level_two_headings_are_the_six_in_order(self):
        self.assertEqual(level_two_headings(self.lines), HEADINGS)

    def test_readme_holds_no_table(self):
        rows = [line for line in prose_lines(self.lines)
                if line.startswith("|")]
        self.assertEqual(rows, [])

    def test_each_group_line_links_its_page(self):
        self.assertEqual(
            group_items(self.lines),
            [(name, [page]) for name, page in GROUPS])

    def test_relative_links_resolve(self):
        self.assertEqual(missing_links(self.lines), [])


class GuardSelfTest(unittest.TestCase):
    """The helpers catch what they exist to catch."""

    def test_a_renamed_heading_is_seen(self):
        lines = [line.replace("## Structure", "## Layout")
                 for line in read_lines()]
        self.assertNotEqual(level_two_headings(lines), HEADINGS)

    def test_a_link_to_a_missing_file_is_seen(self):
        lines = read_lines() + ["See [gone](docs/no-such-page.md)."]
        self.assertEqual(missing_links(lines), ["docs/no-such-page.md"])

    def test_a_retargeted_group_link_is_seen(self):
        lines = [line.replace("(docs/plan.md)", "(docs/build.md)")
                 for line in read_lines()]
        self.assertNotEqual(
            group_items(lines), [(name, [page]) for name, page in GROUPS])


if __name__ == "__main__":
    unittest.main()
