#!/usr/bin/env python3
"""Tests the skill prompts' content-directory path notation
(shipd-config skill-prompt-path-notation).

The content directory is configurable, so a prompt that hardcodes `.shipd/`
would send a skill at the wrong place in a repo that renamed it. The library
resolves this by notation rather than by rewording every mention: a literal
`.shipd/` prefix denotes the *resolved* content directory. This test enforces
that contract line by line over `plugins/s/skills/**/*.md`.

A line carrying `.shipd/` passes when it is self-annotating — a `~/.shipd`
home path, a `$SANDBOX` onboarding path, a `default`-annotated mention, or a
mention naming the content directory — or when its file carries the canonical
notation rule (marker text `denote the repo's resolved content directory`).
`plugins/s/skills/onboard/SKILL.md` is exempt: its sandbox is always created
with the default layout, so its literals are intentionally exact.
"""

import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.normpath(os.path.join(HERE, "..", ".."))
REPO_ROOT = os.path.normpath(os.path.join(SKILLS_DIR, "..", "..", ".."))

# A file carrying this substring declares the notation rule for all its lines.
# Matched against the file's whitespace-collapsed text, so the sentence may wrap
# across lines like any other prose.
MARKER = "denote the repo's resolved content directory"

# Line-level self-annotations: any of these on the line makes it correct as
# written, with no notation rule needed.
LINE_EXEMPTIONS = ("~/.shipd", "$SANDBOX", "default", "content directory")

# Files whose literals are intentionally exact.
FILE_EXEMPTIONS = ("plugins/s/skills/onboard/SKILL.md",)


def _markdown_files():
    for dirpath, dirnames, filenames in os.walk(SKILLS_DIR):
        dirnames.sort()
        for name in sorted(filenames):
            if name.endswith(".md"):
                yield os.path.join(dirpath, name)


def _relpath(path):
    return os.path.relpath(path, REPO_ROOT).replace(os.sep, "/")


class PromptPathNotationTest(unittest.TestCase):
    def test_every_skill_markdown_file_is_scanned(self):
        """Guards the walk itself: if the skills tree moves, the scan below
        would pass vacuously."""
        files = list(_markdown_files())
        self.assertTrue(files, "found no skill markdown files to scan")
        names = {_relpath(p) for p in files}
        self.assertIn("plugins/s/skills/build/SKILL.md", names)

    def test_literal_shipd_paths_are_annotated_or_covered(self):
        offenders = []
        for path in _markdown_files():
            rel = _relpath(path)
            if any(rel.endswith(suffix) for suffix in FILE_EXEMPTIONS):
                continue
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            if MARKER in " ".join(text.split()):
                continue
            for lineno, line in enumerate(text.splitlines(), start=1):
                if ".shipd/" not in line:
                    continue
                if any(token in line for token in LINE_EXEMPTIONS):
                    continue
                offenders.append("{}:{}".format(rel, lineno))
        self.assertEqual(
            [], offenders,
            "skill prompt lines hardcode `.shipd/` without the notation rule "
            "or a self-annotation:\n  " + "\n  ".join(offenders))


if __name__ == "__main__":
    unittest.main()
