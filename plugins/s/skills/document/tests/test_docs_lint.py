#!/usr/bin/env python3
"""Tests for docs_lint.py — the mechanical half of the shipd documentation
standard.

The lint is a pure file-in/findings-out CLI: every test writes a markdown
fixture into a temporary directory, calls ``docs_lint.main(argv)`` with stdout
captured, and asserts on the printed findings and the exit code. Nothing here
spawns a subprocess or touches the repository's real ``docs/`` tree.

The rules under test come from the change's Implementation decision: errors for
a missing or unknown doc-type marker, an over-cap file, an over-long sentence
(25 words descriptive, 20 words procedural), a paragraph over six sentences,
and a second mermaid fence; a warning — never an error — for passive voice.
"""

import contextlib
import io
import os
import re
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
sys.path.insert(0, SCRIPTS)

import docs_lint  # noqa: E402


def words(count, start=1):
    """``count`` distinct one-token words, so a sentence's length is exact."""
    return " ".join("word%02d" % n for n in range(start, start + count))


def filler(lines):
    """``lines`` lines of one-sentence paragraphs separated by blank lines.

    Padding a fixture past its line cap must not trip any other rule, so the
    filler alternates a short active sentence with a blank line: every
    paragraph holds exactly one sentence.
    """
    out = []
    while len(out) < lines:
        out.append("The engine reads the file.")
        out.append("")
    return out[:lines]


class LintTestCase(unittest.TestCase):
    """Fixture plumbing shared by every lint test."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = self._tmp.name

    def write(self, name, lines):
        path = os.path.join(self.root, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        return path

    def run_lint(self, *paths):
        """Run the CLI over ``paths``; return ``(exit_code, stdout)``."""
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = docs_lint.main(list(paths))
        return code, buf.getvalue()

    def errors(self, out):
        return [ln for ln in out.splitlines() if ": error: " in ln]

    def warnings(self, out):
        return [ln for ln in out.splitlines() if ": warning: " in ln]


class DocTypeMarkerTests(LintTestCase):
    """The first-line marker is the entry gate of the standard."""

    def test_missing_marker_is_an_error(self):
        path = self.write("nomarker.md", [
            "# Title",
            "",
            "The engine reads the file.",
        ])
        code, out = self.run_lint(path)
        self.assertEqual(code, 1)
        self.assertEqual(len(self.errors(out)), 1, out)
        self.assertIn("doc-type", out)

    def test_unknown_marker_value_is_an_error(self):
        path = self.write("unknown.md", [
            "<!-- doc-type: tutorial -->",
            "",
            "The engine reads the file.",
        ])
        code, out = self.run_lint(path)
        self.assertEqual(code, 1)
        self.assertTrue(self.errors(out), out)
        self.assertIn("tutorial", out)

    def test_marker_error_names_file_and_line_one(self):
        path = self.write("nomarker.md", ["# Title"])
        _, out = self.run_lint(path)
        self.assertTrue(
            re.match(r"^%s:1: error: \S" % re.escape(path), out.splitlines()[0]),
            out,
        )


class LineCapTests(LintTestCase):
    """Concept 100, how-to 150, reference 250 — total file lines."""

    def test_concept_over_one_hundred_lines_is_an_error(self):
        path = self.write("concept.md",
                          ["<!-- doc-type: concept -->", ""] + filler(120))
        code, out = self.run_lint(path)
        self.assertEqual(code, 1)
        self.assertTrue(any("100" in ln for ln in self.errors(out)), out)

    def test_how_to_over_one_hundred_fifty_lines_is_an_error(self):
        path = self.write("howto.md",
                          ["<!-- doc-type: how-to -->", ""] + filler(170))
        code, out = self.run_lint(path)
        self.assertEqual(code, 1)
        self.assertTrue(any("150" in ln for ln in self.errors(out)), out)

    def test_reference_over_two_hundred_fifty_lines_is_an_error(self):
        path = self.write("reference.md",
                          ["<!-- doc-type: reference -->", ""] + filler(270))
        code, out = self.run_lint(path)
        self.assertEqual(code, 1)
        self.assertTrue(any("250" in ln for ln in self.errors(out)), out)

    def test_how_to_under_its_own_cap_passes(self):
        """120 lines fails the concept cap but sits inside the how-to cap."""
        path = self.write("howto.md",
                          ["<!-- doc-type: how-to -->", ""] + filler(120))
        code, out = self.run_lint(path)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.errors(out), [])


class SentenceCapTests(LintTestCase):
    """25 words of description, 20 words of instruction."""

    def test_thirty_word_descriptive_sentence_is_an_error(self):
        path = self.write("concept.md", [
            "<!-- doc-type: concept -->",
            "",
            words(30) + ".",
        ])
        code, out = self.run_lint(path)
        self.assertEqual(code, 1)
        errs = self.errors(out)
        self.assertEqual(len(errs), 1, out)
        self.assertIn("25", errs[0])
        self.assertTrue(errs[0].startswith("%s:3: error: " % path), errs[0])

    def test_twenty_five_word_descriptive_sentence_passes(self):
        path = self.write("concept.md", [
            "<!-- doc-type: concept -->",
            "",
            words(25) + ".",
        ])
        code, out = self.run_lint(path)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.errors(out), [])

    def test_twenty_two_word_numbered_item_uses_the_procedural_cap(self):
        """22 words clears the 25-word cap, so an error proves the 20 applied."""
        path = self.write("howto.md", [
            "<!-- doc-type: how-to -->",
            "",
            "1. " + words(22) + ".",
        ])
        code, out = self.run_lint(path)
        self.assertEqual(code, 1)
        errs = self.errors(out)
        self.assertEqual(len(errs), 1, out)
        self.assertIn("20", errs[0])
        self.assertTrue(errs[0].startswith("%s:3: error: " % path), errs[0])

    def test_twenty_word_numbered_item_passes(self):
        """The list marker is not a word, so exactly 20 words is inside the cap."""
        path = self.write("howto.md", [
            "<!-- doc-type: how-to -->",
            "",
            "1. " + words(20) + ".",
        ])
        code, out = self.run_lint(path)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.errors(out), [])


class ParagraphTests(LintTestCase):
    """A paragraph carries at most six sentences; a list is not a paragraph."""

    def test_seven_sentence_paragraph_is_an_error(self):
        path = self.write("concept.md", [
            "<!-- doc-type: concept -->",
            "",
            "The engine reads the file. It parses the marker. It counts the lines. "
            "It splits the prose. It measures each sentence. It groups the "
            "paragraphs. It prints the findings.",
        ])
        code, out = self.run_lint(path)
        self.assertEqual(code, 1)
        errs = self.errors(out)
        self.assertEqual(len(errs), 1, out)
        self.assertIn("6", errs[0])

    def test_six_sentence_paragraph_passes(self):
        path = self.write("concept.md", [
            "<!-- doc-type: concept -->",
            "",
            "The engine reads the file. It parses the marker. It counts the lines. "
            "It splits the prose. It measures each sentence. It prints the findings.",
        ])
        code, out = self.run_lint(path)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.errors(out), [])

    def test_a_long_list_is_not_a_paragraph(self):
        path = self.write("howto.md", [
            "<!-- doc-type: how-to -->",
            "",
        ] + ["%d. Run the step." % n for n in range(1, 9)])
        code, out = self.run_lint(path)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.errors(out), [])


class MermaidTests(LintTestCase):
    """At most one diagram per doc."""

    DIAGRAM = [
        "```mermaid",
        "flowchart TD",
        "  a --> b",
        "```",
    ]

    def test_two_mermaid_fences_is_an_error(self):
        path = self.write("concept.md", [
            "<!-- doc-type: concept -->",
            "",
        ] + self.DIAGRAM + [""] + self.DIAGRAM)
        code, out = self.run_lint(path)
        self.assertEqual(code, 1)
        errs = self.errors(out)
        self.assertEqual(len(errs), 1, out)
        self.assertIn("diagram", errs[0].lower())

    def test_one_mermaid_fence_reports_no_diagram_finding(self):
        path = self.write("concept.md", [
            "<!-- doc-type: concept -->",
            "",
        ] + self.DIAGRAM)
        code, out = self.run_lint(path)
        self.assertEqual(code, 0, out)
        self.assertEqual(
            [ln for ln in out.splitlines() if "diagram" in ln.lower()], [], out)


class CodeFenceTests(LintTestCase):
    """Prose analysis stops at a fence; code is never measured."""

    def test_long_line_inside_a_code_fence_is_not_a_sentence(self):
        path = self.write("reference.md", [
            "<!-- doc-type: reference -->",
            "",
            "```bash",
            words(40) + ".",
            "```",
        ])
        code, out = self.run_lint(path)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.errors(out), [])


class SentenceSplitTests(LintTestCase):
    """Abbreviations and inline code never end a sentence.

    Those two are the only guards. A period followed by whitespace ends a
    sentence whatever case the next word carries — the product's own name is
    lowercase, so a case test would merge every sentence that opens with it.
    """

    def test_abbreviations_and_inline_code_do_not_split_sentences(self):
        """Naive splitting would count nine sentences and report a paragraph.

        The paragraph holds three real sentences whose periods sit inside
        abbreviations (``e.g.``, ``i.e.``, ``etc.``, ``vs.``) and inline-code
        spans (``spec_status.py``), so a correct splitter reports nothing.
        """
        path = self.write("concept.md", [
            "<!-- doc-type: concept -->",
            "",
            "The engine runs `spec_status.py` for a change, e.g. a planned one. "
            "Some verbs, i.e. the mutating ones, refuse a foreign branch, etc. "
            "The build path uses `docs_lint.py` vs. the review path.",
        ])
        code, out = self.run_lint(path)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.errors(out), [])

    def test_a_lowercase_next_word_still_ends_the_sentence(self):
        """Two conforming sentences, the second opening with ``shipd``.

        Merged they run to 27 words, so a splitter that refuses a boundary
        before a lowercase word reports a false 25-word error.
        """
        path = self.write("concept.md", [
            "<!-- doc-type: concept -->",
            "",
            "The engine plans a change and builds it in one worktree. "
            "shipd then merges the change into the master library and "
            "archives the plan for later reference.",
        ])
        code, out = self.run_lint(path)
        self.assertEqual(code, 0, out)
        self.assertEqual(out, "")

    def test_sentences_opening_with_the_product_name_count_separately(self):
        """Seven short sentences, each opening ``shipd``, hit the paragraph cap."""
        path = self.write("concept.md", [
            "<!-- doc-type: concept -->",
            "",
            "shipd plans a change. shipd builds it. shipd verifies it. "
            "shipd merges it. shipd archives it. shipd ships it. "
            "shipd reports it.",
        ])
        code, out = self.run_lint(path)
        self.assertEqual(code, 1)
        errs = self.errors(out)
        self.assertEqual(len(errs), 1, out)
        self.assertIn("6", errs[0])
        self.assertIn("paragraph", errs[0])

    def test_an_inline_code_span_counts_as_one_word(self):
        """`a b c d e f` is one token, so this sentence holds 25 words."""
        path = self.write("concept.md", [
            "<!-- doc-type: concept -->",
            "",
            words(24) + " `w1 w2 w3 w4 w5 w6 w7 w8`.",
        ])
        code, out = self.run_lint(path)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.errors(out), [])


class PassiveVoiceTests(LintTestCase):
    """Passive voice is noisy to detect, so it only ever warns."""

    def test_passive_sentence_warns_and_exits_zero(self):
        path = self.write("concept.md", [
            "<!-- doc-type: concept -->",
            "",
            "The file was created by the engine.",
        ])
        code, out = self.run_lint(path)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.errors(out), [])
        warns = self.warnings(out)
        self.assertEqual(len(warns), 1, out)
        self.assertTrue(warns[0].startswith("%s:3: warning: " % path), warns[0])

    def test_sentence_final_participle_still_warns(self):
        """The participle carries the closing period; the heuristic strips it."""
        path = self.write("concept.md", [
            "<!-- doc-type: concept -->",
            "",
            "The spec is written.",
        ])
        code, out = self.run_lint(path)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.errors(out), [])
        warns = self.warnings(out)
        self.assertEqual(len(warns), 1, out)
        self.assertTrue(warns[0].startswith("%s:3: warning: " % path), warns[0])

    def test_active_sentence_does_not_warn(self):
        path = self.write("concept.md", [
            "<!-- doc-type: concept -->",
            "",
            "The engine creates the file.",
        ])
        code, out = self.run_lint(path)
        self.assertEqual(code, 0, out)
        self.assertEqual(out, "")


class SkippedLineTests(LintTestCase):
    """Headings, tables, and link-reference definitions carry no prose."""

    def test_table_rows_and_headings_are_not_measured(self):
        path = self.write("reference.md", [
            "<!-- doc-type: reference -->",
            "",
            "# " + words(30),
            "",
            "| verb | " + words(30) + " |",
            "| --- | --- |",
            "| show | " + words(30) + " |",
            "",
            "[ref]: https://example.invalid/a/very/long/path/that/never/wraps",
        ])
        code, out = self.run_lint(path)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.errors(out), [])


class CleanDocTests(LintTestCase):
    """A conforming doc prints nothing at all."""

    def test_conforming_doc_is_silent(self):
        path = self.write("concept.md", [
            "<!-- doc-type: concept -->",
            "",
            "# The change lifecycle",
            "",
            "A change lives in one worktree on one branch. The engine plans it, "
            "builds it, then merges it.",
            "",
            "1. Plan the change.",
            "2. Build the change.",
            "3. Ship the change.",
        ])
        code, out = self.run_lint(path)
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_several_files_report_under_their_own_names(self):
        good = self.write("good.md", [
            "<!-- doc-type: concept -->",
            "",
            "The engine reads the file.",
        ])
        bad = self.write("bad.md", [
            "<!-- doc-type: concept -->",
            "",
            words(30) + ".",
        ])
        code, out = self.run_lint(good, bad)
        self.assertEqual(code, 1)
        errs = self.errors(out)
        self.assertEqual(len(errs), 1, out)
        self.assertTrue(errs[0].startswith(bad + ":"), errs[0])


class UsageTests(LintTestCase):
    """Usage and IO problems exit 2, never 1."""

    def test_unreadable_path_exits_two(self):
        missing = os.path.join(self.root, "absent.md")
        code, out = self.run_lint(missing)
        self.assertEqual(code, 2, out)

    def test_no_arguments_exits_two(self):
        code, out = self.run_lint()
        self.assertEqual(code, 2, out)


if __name__ == "__main__":
    unittest.main()
