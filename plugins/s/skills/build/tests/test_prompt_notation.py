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
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.normpath(os.path.join(HERE, "..", ".."))
REPO_ROOT = os.path.normpath(os.path.join(SKILLS_DIR, "..", "..", ".."))

# The emission reference's `base:` hash recipe (shipd-plan
# base-hash-through-the-engine) and the scripts dir its documented command
# calls into.
EMISSION_MD = os.path.join(SKILLS_DIR, "plan", "references", "emission.md")
BUILD_SCRIPTS_DIR = os.path.join(SKILLS_DIR, "build", "scripts")
BASE_HASH_HEADING = "### `base:` hashes for MODIFIED / REMOVED"

sys.path.insert(0, BUILD_SCRIPTS_DIR)
import spec_common as sc  # noqa: E402

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


def _base_hash_command():
    """Extract the fenced ```bash command from the emission reference's
    `base:` hash section (the text between its heading and the next
    heading)."""
    with open(EMISSION_MD, encoding="utf-8") as fh:
        text = fh.read()
    start = text.index(BASE_HASH_HEADING)
    rest = text[start + len(BASE_HASH_HEADING):]
    next_heading = re.search(r"^#{2,3} ", rest, re.MULTILINE)
    section = rest[:next_heading.start()] if next_heading else rest
    fence = re.search(r"```bash\n(.*?)```", section, re.DOTALL)
    if fence is None:
        raise AssertionError(
            "no ```bash fenced command found under %r in %s"
            % (BASE_HASH_HEADING, EMISSION_MD))
    return fence.group(1)


class BaseHashReferenceTest(unittest.TestCase):
    """Guards the emission reference's `base:` hash recipe (shipd-plan
    base-hash-through-the-engine) by **executing** the command it documents,
    not by pattern-matching its text — a textual match would pass on a
    command that still cannot run, which is the defect this guards against."""

    def test_documented_command_runs_and_prints_the_content_hash(self):
        capability, requirement_id = "spec-status", "status-cli"
        master_path = os.path.join(
            REPO_ROOT, ".shipd", "verified", capability, "spec.md")
        with open(master_path, encoding="utf-8") as fh:
            master = sc.parse_spec(fh.read())
        req = next(r for r in master.requirements if r.id == requirement_id)
        expected = sc.content_hash(req)

        command = _base_hash_command()
        env = dict(os.environ)
        env["CLAUDE_PLUGIN_ROOT"] = os.path.join(REPO_ROOT, "plugins", "s")
        env["CAP"] = capability
        env["ID"] = requirement_id
        result = subprocess.run(
            ["bash", "-c", command], cwd=REPO_ROOT, env=env,
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), expected)


if __name__ == "__main__":
    unittest.main()
