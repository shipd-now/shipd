#!/usr/bin/env python3
"""Tests that generic skill and harness markdown names no specific harness
(shipd-interaction harness-neutral-skill-prose).

shipd generates its skills for several harnesses, so prose in the generic
markdown must not say `Claude`. This test scans every `*.md` under
`plugins/s/skills/` and `plugins/s/harness/` line by line and fails on the
case-sensitive word `Claude`. The case-sensitive match leaves working
lowercase commands (`claude plugin update`) and upper-case variables
(`CLAUDE_PLUGIN_ROOT`) alone: the scope is prose only.

`plugins/s/harness/references/autopilot.md` is the one platform-specific file
and is skipped.
"""

import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.normpath(os.path.join(HERE, "..", ".."))
PLUGIN_DIR = os.path.normpath(os.path.join(SKILLS_DIR, ".."))
REPO_ROOT = os.path.normpath(os.path.join(PLUGIN_DIR, "..", ".."))

SCAN_DIRS = (SKILLS_DIR, os.path.join(PLUGIN_DIR, "harness"))

# Platform-specific files, exempt from the scan.
ALLOWED = ("plugins/s/harness/references/autopilot.md",)

CLAUDE_WORD = re.compile(r"\bClaude\b")


def _relpath(path):
    return os.path.relpath(path, REPO_ROOT).replace(os.sep, "/")


def _markdown_files():
    for root in SCAN_DIRS:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames.sort()
            for name in sorted(filenames):
                if name.endswith(".md"):
                    yield os.path.join(dirpath, name)


class HarnessNeutralProseTest(unittest.TestCase):
    def test_no_claude_in_generic_markdown(self):
        offenders = []
        for path in _markdown_files():
            rel = _relpath(path)
            if rel in ALLOWED:
                continue
            with open(path, encoding="utf-8") as fh:
                for number, line in enumerate(fh, 1):
                    if CLAUDE_WORD.search(line):
                        offenders.append(f"{rel}:{number}")
        self.assertEqual(
            offenders, [], "Claude named in generic prose:\n" + "\n".join(offenders)
        )

    def test_regex_scope(self):
        self.assertTrue(CLAUDE_WORD.search("is in Claude Code plan mode"))
        self.assertFalse(CLAUDE_WORD.search("${CLAUDE_PLUGIN_ROOT}"))
        self.assertFalse(CLAUDE_WORD.search("claude plugin update s@shipd"))


if __name__ == "__main__":
    unittest.main()
