#!/usr/bin/env python3
"""Tests for the harness-adapter registry — ``harness_registry.py``'s feature
vocabulary and per-harness entries, plus the read-only ``shipd harness`` verbs
over them.

The registry is declared data, not detected capability, so the structural
invariants below *are* its validation: nothing else checks that an entry's
``features`` stay inside the vocabulary or that a generated-file pattern
carries its ``{command}`` placeholder. The researched paths of the entries a
later generation step depends on most are pinned individually, so a silent
edit to one shows up here rather than in generated output.

The verb tests drive the real binary by path through a subprocess, from a
throwaway cwd with an isolated ``HOME`` — the ``test_shipd_cli.py`` style — so
the shebang and exec bit are exercised, and so the "writes nothing" claim is
checked against a directory the suite owns.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
PLUGIN_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
BIN = os.path.join(PLUGIN_ROOT, "bin", "shipd")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import harness_registry as hr  # noqa: E402

KEBAB_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# The dialects an entry may declare; only ``yaml`` emits frontmatter fields.
DIALECTS = ("yaml", "markdown-headers", "conventions-file")

ENTRY_KEYS = {"id", "name", "repo_pattern", "user_dir", "dialect",
              "frontmatter", "features"}


class FeatureVocabularyTest(unittest.TestCase):
    def test_features_are_the_fixed_first_cut_vocabulary(self):
        self.assertEqual(
            hr.FEATURES,
            ("subagents", "question-dialogs", "file-references",
             "background-tasks"))


class EntryShapeTest(unittest.TestCase):
    def test_ids_are_unique_kebab_case(self):
        ids = [entry["id"] for entry in hr.HARNESSES]
        self.assertEqual(len(ids), len(set(ids)), "duplicate harness id")
        for harness_id in ids:
            self.assertRegex(harness_id, KEBAB_RE)

    def test_ids_accessor_matches_the_entry_order(self):
        self.assertEqual(hr.ids(),
                         tuple(entry["id"] for entry in hr.HARNESSES))

    def test_every_entry_carries_exactly_the_registry_keys(self):
        for entry in hr.HARNESSES:
            with self.subTest(harness=entry.get("id")):
                self.assertEqual(set(entry), ENTRY_KEYS)
                self.assertIn(entry["dialect"], DIALECTS)
                self.assertTrue(entry["name"])

    def test_features_are_a_subset_of_the_vocabulary(self):
        for entry in hr.HARNESSES:
            with self.subTest(harness=entry["id"]):
                self.assertTrue(
                    set(entry["features"]) <= set(hr.FEATURES),
                    "%s declares features outside FEATURES: %r"
                    % (entry["id"], entry["features"]))

    def test_repo_patterns_carry_the_command_placeholder(self):
        # Every dialect but `conventions-file` writes one file per command, so
        # its pattern must vary with the command; a `conventions-file` pattern
        # is a literal single-file path and must *not* carry the placeholder.
        for entry in hr.HARNESSES:
            if entry["repo_pattern"] is None:
                continue
            with self.subTest(harness=entry["id"]):
                if entry["dialect"] == "conventions-file":
                    self.assertNotIn("{command}", entry["repo_pattern"])
                else:
                    self.assertIn("{command}", entry["repo_pattern"])

    def test_non_yaml_dialects_declare_no_frontmatter(self):
        for entry in hr.HARNESSES:
            if entry["dialect"] == "yaml":
                continue
            with self.subTest(harness=entry["id"]):
                self.assertEqual(entry["frontmatter"], ())


class ResearchedPathsTest(unittest.TestCase):
    def test_cursor_pattern(self):
        self.assertEqual(hr.get("cursor")["repo_pattern"],
                         ".cursor/commands/shipd-{command}.md")

    def test_github_copilot_pattern_is_a_prompt_file(self):
        self.assertTrue(
            hr.get("github-copilot")["repo_pattern"].endswith(".prompt.md"),
            hr.get("github-copilot")["repo_pattern"])

    def test_codex_is_user_global_only(self):
        entry = hr.get("codex")
        self.assertIsNone(entry["repo_pattern"])
        self.assertIn("~/.codex/prompts", entry["user_dir"])

    def test_claude_code_declares_the_full_vocabulary(self):
        self.assertEqual(set(hr.get("claude-code")["features"]),
                         set(hr.FEATURES))

    def test_opencode_paths(self):
        entry = hr.get("opencode")
        self.assertEqual(entry["repo_pattern"],
                         ".opencode/commands/shipd-{command}.md")
        self.assertEqual(entry["user_dir"], "~/.config/opencode/commands/")
        self.assertEqual(entry["dialect"], "yaml")
        self.assertEqual(entry["frontmatter"], ("description",))
        self.assertEqual(entry["features"],
                         ("subagents", "file-references"))

    def test_pi_paths(self):
        entry = hr.get("pi")
        self.assertEqual(entry["repo_pattern"],
                         ".pi/prompts/shipd-{command}.md")
        self.assertEqual(entry["user_dir"], "~/.pi/agent/prompts/")
        self.assertEqual(entry["dialect"], "yaml")
        self.assertEqual(entry["frontmatter"],
                         ("description", "argument-hint"))
        self.assertEqual(entry["features"], ("file-references",))

    def test_pi_and_oh_my_pi_are_separate(self):
        self.assertIn("oh-my-pi", hr.ids())
        self.assertIn("pi", hr.ids())
        self.assertNotEqual(hr.get("oh-my-pi")["repo_pattern"],
                            hr.get("pi")["repo_pattern"])

    def test_aider_is_a_single_conventions_file(self):
        entry = hr.get("aider")
        self.assertEqual(entry["repo_pattern"], "shipd-conventions.md")
        self.assertEqual(entry["dialect"], "conventions-file")
        self.assertIsNone(entry["user_dir"])
        self.assertEqual(entry["features"], ())


class GetTest(unittest.TestCase):
    def test_unknown_id_is_none(self):
        self.assertIsNone(hr.get("no-such-harness"))
        self.assertNotIn("no-such-harness", hr.ids())

    def test_known_id_round_trips(self):
        for harness_id in hr.ids():
            with self.subTest(harness=harness_id):
                self.assertEqual(hr.get(harness_id)["id"], harness_id)


class HarnessVerbTest(unittest.TestCase):
    """``shipd harness`` — an in-binary read verb over the registry."""

    def setUp(self):
        self.cwd = tempfile.mkdtemp(prefix="shipd-harness-cwd-")
        self.home = tempfile.mkdtemp(prefix="shipd-harness-home-")

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)
        shutil.rmtree(self.cwd, ignore_errors=True)

    def cli(self, *args):
        env = dict(os.environ)
        env["HOME"] = self.home
        return subprocess.run([BIN, *args], capture_output=True, text=True,
                              cwd=self.cwd, env=env)

    def test_list_names_every_harness(self):
        for args in ((), ("list",)):
            with self.subTest(args=args):
                r = self.cli("harness", *args)
                self.assertEqual(r.returncode, 0, r.stderr)
                for harness_id in hr.ids():
                    self.assertIn(harness_id, r.stdout)

    def test_show_prints_one_entry(self):
        r = self.cli("harness", "show", "cursor")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(".cursor/commands/shipd-{command}.md", r.stdout)
        self.assertIn("yaml", r.stdout)

    def test_json_list_is_machine_readable(self):
        r = self.cli("harness", "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        entries = json.loads(r.stdout)
        self.assertEqual(len(entries), len(hr.HARNESSES))
        self.assertEqual(tuple(entry["id"] for entry in entries), hr.ids())

    def test_json_show_is_one_entry(self):
        r = self.cli("harness", "show", "cursor", "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        entry = json.loads(r.stdout)
        self.assertEqual(entry["id"], "cursor")
        self.assertEqual(entry["repo_pattern"],
                         ".cursor/commands/shipd-{command}.md")

    def test_unknown_id_is_a_single_error_line(self):
        r = self.cli("harness", "show", "no-such-harness")
        self.assertNotEqual(r.returncode, 0)
        lines = [line for line in r.stderr.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1, r.stderr)
        self.assertTrue(lines[0].startswith("Error: "), lines[0])
        self.assertIn("no-such-harness", lines[0])

    def test_the_verb_writes_nothing(self):
        before = sorted(os.listdir(self.cwd))
        self.assertEqual(self.cli("harness").returncode, 0)
        self.assertEqual(self.cli("harness", "show", "cursor").returncode, 0)
        self.assertEqual(sorted(os.listdir(self.cwd)), before)
        self.assertEqual(before, [])


if __name__ == "__main__":
    unittest.main()
