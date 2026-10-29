#!/usr/bin/env python3
"""Tests that no skill or harness markdown carries the question rejection
workaround (shipd-interaction no-question-rejection-workaround).

The harness bug that delivered a question dialog as a tool rejection no longer
occurs, so this test scans every `*.md` under `plugins/s/skills/` and
`plugins/s/harness/` line by line and fails on the case-insensitive phrases
`rejection recovery`, `rejection-recovery`, and `rejected or interrupted`,
naming each `path:line`.
"""

import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.normpath(os.path.join(HERE, "..", ".."))
PLUGIN_DIR = os.path.normpath(os.path.join(SKILLS_DIR, ".."))
REPO_ROOT = os.path.normpath(os.path.join(PLUGIN_DIR, "..", ".."))

SCAN_DIRS = (SKILLS_DIR, os.path.join(PLUGIN_DIR, "harness"))

PHRASE = re.compile(r"rejection[ -]recovery|rejected or interrupted", re.IGNORECASE)


def _relpath(path):
    return os.path.relpath(path, REPO_ROOT).replace(os.sep, "/")


def _markdown_files():
    for root in SCAN_DIRS:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames.sort()
            for name in sorted(filenames):
                if name.endswith(".md"):
                    yield os.path.join(dirpath, name)


class NoRejectionRecoveryTest(unittest.TestCase):
    def test_no_rejection_recovery_in_markdown(self):
        offenders = []
        for path in _markdown_files():
            rel = _relpath(path)
            with open(path, encoding="utf-8") as fh:
                for number, line in enumerate(fh, 1):
                    if PHRASE.search(line):
                        offenders.append(f"{rel}:{number}")
        self.assertEqual(
            offenders,
            [],
            "question rejection workaround found:\n" + "\n".join(offenders),
        )

    def test_regex_scope(self):
        self.assertTrue(PHRASE.search("## Question rejection recovery"))
        self.assertTrue(PHRASE.search("the question-rejection-recovery roster"))
        self.assertTrue(PHRASE.search("a rejected or interrupted dialog"))
        self.assertFalse(PHRASE.search("a declined dialog is a decline"))


if __name__ == "__main__":
    unittest.main()
