#!/usr/bin/env python3
"""The external-loader manifest (``plugins/s/external-loaders.json``) lists
the shipd files and ``##`` headings that loaders outside this repo read by
name. This test fails when a listed file or heading disappears, so a rename
tells its author that it breaks a loader."""

import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
MANIFEST = os.path.join(PLUGIN, "external-loaders.json")

H2_RE = re.compile(r"^## (.+?)\s*$")


def _load():
    with open(MANIFEST, encoding="utf-8") as fh:
        return json.load(fh)


def _h2_headings(path):
    """The ``##`` headings of a markdown file, outside code fences."""
    headings = []
    fenced = False
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.lstrip().startswith("```"):
                fenced = not fenced
            elif not fenced:
                m = H2_RE.match(line)
                if m:
                    headings.append(m.group(1))
    return headings


class ExternalLoaderManifestTest(unittest.TestCase):
    def test_manifest_lists_the_headless_reference(self):
        paths = [f["path"] for f in _load()["files"]]
        self.assertIn("skills/ask/references/headless.md", paths)

    def test_manifest_lists_the_review_skill(self):
        paths = [f["path"] for f in _load()["files"]]
        self.assertIn("skills/review/SKILL.md", paths)
        self.assertIn("skills/review/references/linters.md", paths)

    def test_manifest_lists_the_plan_authoring_reference(self):
        entries = {f["path"]: f for f in _load()["files"]}
        entry = entries["skills/plan/references/authoring.md"]
        self.assertEqual(
            entry["headings"],
            ["Motivation", "Non-goals", "Implementation decisions",
             "Requirements", "Scenarios", "Tasks", "Placeholders", "Size"])

    def test_authoring_reference_has_exactly_its_headings_in_order(self):
        path = os.path.join(PLUGIN, "skills", "plan", "references",
                            "authoring.md")
        self.assertEqual(
            _h2_headings(path),
            ["Motivation", "Non-goals", "Implementation decisions",
             "Requirements", "Scenarios", "Tasks", "Placeholders", "Size"])

    def test_authoring_reference_is_engine_neutral(self):
        path = os.path.join(PLUGIN, "skills", "plan", "references",
                            "authoring.md")
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        self.assertNotIn("```", text)
        self.assertNotIn("~~~", text)
        self.assertNotIn("${CLAUDE_PLUGIN_ROOT}", text)

    def test_every_entry_is_well_formed(self):
        for entry in _load()["files"]:
            self.assertIsInstance(entry.get("path"), str)
            # An empty list means the loader reads the whole file.
            self.assertIsInstance(entry.get("headings"), list, entry)
            self.assertFalse(os.path.isabs(entry["path"]), entry["path"])

    def test_every_listed_file_exists(self):
        for entry in _load()["files"]:
            path = os.path.join(PLUGIN, entry["path"])
            self.assertTrue(
                os.path.isfile(path),
                "%s is read by an external loader (%s); removing or moving "
                "it breaks that loader" % (entry["path"], entry.get("loader")))

    def test_every_listed_heading_exists(self):
        for entry in _load()["files"]:
            path = os.path.join(PLUGIN, entry["path"])
            if not os.path.isfile(path):
                continue
            found = _h2_headings(path)
            for heading in entry["headings"]:
                self.assertIn(
                    heading, found,
                    "## %s in %s is read by an external loader (%s); "
                    "renaming or removing it breaks that loader"
                    % (heading, entry["path"], entry.get("loader")))


if __name__ == "__main__":
    unittest.main()
