#!/usr/bin/env python3
"""Tests for the marker-gated docs lint step in ``.github/workflows/ci.yml``.

The workflow is read as text and its named step's ``run:`` body extracted by a
tiny indentation-based reader (:func:`extract_run`): the engine is stdlib-only,
so no YAML parser is available and none is introduced. The reader understands
exactly the shape this repository's ``ci.yml`` is authored in.

Two kinds of assertion, after ``test_ci_action.py``:

* *structural* — the workflow carries the step, directly after ``Lint
  in-flight changes``, and the step names ``docs_lint.py`` and exempts
  ``docs/retros/``;
* *executable* — the step's ``run:`` body is executed verbatim under ``bash
  -e`` in fixture trees that hold a fabricated ``docs/`` directory plus a copy
  of the real ``docs_lint.py`` at its repository-relative path. That proves the
  command the workflow encodes actually gates, rather than merely that
  ``ci.yml`` mentions the script.
"""

import os
import re
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
# tests -> document -> skills -> s -> plugins -> repository root
REPO_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", "..", ".."))
CI_YML = os.path.join(REPO_ROOT, ".github", "workflows", "ci.yml")

STEP_NAME = "Lint marker-carrying docs"
PRIOR_STEP_NAME = "Lint in-flight changes"

# Where the fixture tree keeps its copy of the linter, so the step's encoded
# path resolves against the fixture rather than this checkout.
LINT_REL = os.path.join(
    "plugins", "s", "skills", "document", "scripts", "docs_lint.py")

SKIP_NOTICE = "no marker-carrying docs; skipping"

# ---------------------------------------------------------------------------
# Fixture documents
# ---------------------------------------------------------------------------

CLEAN_DOC = """<!-- doc-type: concept -->

# Widget

A widget holds one job. The engine reads it once. Nothing else touches it.
"""

# A marker the filter must select even though its type is unknown, so the lint
# reports it instead of the filter hiding it.
UNKNOWN_TYPE_DOC = """<!-- doc-type: bogus -->

# Widget

A widget holds one job.
"""

# The same marker behind leading whitespace, which `docs_lint.py` accepts.
INDENTED_MARKER_DOC = "  " + UNKNOWN_TYPE_DOC

# A well-formed marker over a sentence past the 25-word descriptive cap.
OVER_CAP_DOC = """<!-- doc-type: concept -->

# Widget

A widget holds exactly one job and the engine reads it once and nothing else
touches it and that is the whole of the arrangement for now, truly, honestly.
"""

NO_MARKER_DOC = """# Widget

A widget holds one job.
"""


def _indent(line):
    return len(line) - len(line.lstrip(" "))


def read_ci():
    with open(CI_YML, encoding="utf-8") as handle:
        return handle.read()


def step_names(text):
    """Every step name in the workflow, in file order."""
    names = []
    for line in text.splitlines():
        match = re.match(r"^\s*-\s+name:\s*(.+?)\s*$", line)
        if match and _indent(line) == 6:
            names.append(match.group(1))
    return names


def extract_run(text, name):
    """The dedented ``run:`` block body of the step called ``name``.

    Returns ``None`` when the workflow carries no such step, or the step
    carries no block ``run:``.
    """
    lines = text.splitlines()
    start = None
    for number, line in enumerate(lines):
        if _indent(line) == 6 and line.strip() == "- name: %s" % name:
            start = number + 1
            break
    if start is None:
        return None

    body = []
    run_indent = None
    for line in lines[start:]:
        if run_indent is None:
            if line.strip() and _indent(line) <= 6:
                return None  # the next step began first
            if _indent(line) == 8 and re.match(r"^\s*run:\s*\|-?\s*$", line):
                run_indent = 10
            continue
        if not line.strip():
            body.append("")
            continue
        if _indent(line) < run_indent:
            break
        body.append(line[run_indent:])
    if run_indent is None:
        return None
    while body and not body[-1].strip():
        body.pop()
    return "\n".join(body) + "\n" if body else ""


def write(path, text):
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return path


class WorkflowStepTest(unittest.TestCase):
    """The workflow declares the gate (docs-ci-marker-gate)."""

    def setUp(self):
        self.assertTrue(os.path.isfile(CI_YML), "no workflow at %s" % CI_YML)
        self.text = read_ci()
        self.run = extract_run(self.text, STEP_NAME)

    def test_step_exists_with_a_run_block(self):
        self.assertIsNotNone(
            self.run, "ci.yml carries no %r step with a `run: |` block"
            % STEP_NAME)

    def test_step_follows_the_in_flight_lint(self):
        names = step_names(self.text)
        self.assertIn(STEP_NAME, names)
        self.assertIn(PRIOR_STEP_NAME, names)
        self.assertEqual(
            names.index(STEP_NAME), names.index(PRIOR_STEP_NAME) + 1,
            "the docs lint step does not sit directly after %r"
            % PRIOR_STEP_NAME)

    def test_step_runs_the_linter_and_exempts_retros(self):
        self.assertIsNotNone(self.run)
        self.assertIn("docs_lint.py", self.run)
        self.assertIn("docs/retros/", self.run)


class EncodedCommandTest(unittest.TestCase):
    """The encoded command gates for real (docs-ci-marker-gate)."""

    def setUp(self):
        self.assertTrue(os.path.isfile(CI_YML), "no workflow at %s" % CI_YML)
        self.run = extract_run(read_ci(), STEP_NAME)
        self.assertIsNotNone(
            self.run, "ci.yml carries no %r step with a `run: |` block"
            % STEP_NAME)
        self.tmp = tempfile.mkdtemp(prefix="shipd-docs-ci-gate-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.script = write(os.path.join(self.tmp, "step.sh"), self.run)

    def make_tree(self, name, docs):
        """A fixture repository holding ``docs`` (a path-to-text mapping) and
        a copy of the real linter at its repository-relative path."""
        root = os.path.join(self.tmp, name)
        os.makedirs(os.path.join(root, "docs"))
        target = os.path.join(root, LINT_REL)
        os.makedirs(os.path.dirname(target))
        shutil.copyfile(os.path.join(REPO_ROOT, LINT_REL), target)
        for relative, text in docs.items():
            write(os.path.join(root, relative), text)
        return root

    def run_step(self, root):
        proc = subprocess.run(
            ["bash", "-e", self.script], cwd=root,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return proc.returncode, proc.stdout.decode("utf-8", "replace")

    def test_marker_doc_with_an_unknown_type_fails(self):
        root = self.make_tree(
            "unknown", {os.path.join("docs", "widget.md"): UNKNOWN_TYPE_DOC})
        code, out = self.run_step(root)
        self.assertNotEqual(code, 0, out)
        self.assertIn("bogus", out)

    def test_marker_doc_breaking_the_standard_fails(self):
        root = self.make_tree(
            "overcap", {os.path.join("docs", "widget.md"): OVER_CAP_DOC})
        code, out = self.run_step(root)
        self.assertNotEqual(code, 0, out)
        self.assertIn("cap", out)

    def test_indented_marker_is_still_selected(self):
        """The filter is lenient where the linter is, so a marker behind
        leading whitespace is checked rather than skipped."""
        root = self.make_tree(
            "indented",
            {os.path.join("docs", "widget.md"): INDENTED_MARKER_DOC})
        code, out = self.run_step(root)
        self.assertNotEqual(code, 0, out)

    def test_clean_marker_doc_passes(self):
        root = self.make_tree(
            "clean", {os.path.join("docs", "widget.md"): CLEAN_DOC})
        code, out = self.run_step(root)
        self.assertEqual(code, 0, out)
        self.assertNotIn(SKIP_NOTICE, out)

    def test_nested_marker_doc_is_selected(self):
        root = self.make_tree(
            "nested",
            {os.path.join("docs", "guides", "widget.md"): UNKNOWN_TYPE_DOC})
        code, out = self.run_step(root)
        self.assertNotEqual(code, 0, out)

    def test_no_marker_docs_skips_and_passes(self):
        root = self.make_tree(
            "unmarked", {os.path.join("docs", "widget.md"): NO_MARKER_DOC})
        code, out = self.run_step(root)
        self.assertEqual(code, 0, out)
        self.assertIn(SKIP_NOTICE, out)

    def test_retros_are_exempt(self):
        root = self.make_tree(
            "retros",
            {os.path.join("docs", "retros", "bad.md"): UNKNOWN_TYPE_DOC})
        code, out = self.run_step(root)
        self.assertEqual(code, 0, out)
        self.assertIn(SKIP_NOTICE, out)


if __name__ == "__main__":
    unittest.main()
