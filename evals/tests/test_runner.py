"""Unit tests for the eval harness runner (`evals/run.py`).

These exercise the runner's pure-ish logic — case discovery, structural
grading, and pass-rate aggregation — against prebaked directory trees. They do
NOT invoke a live `claude` session; the end-to-end path is covered by the
harness's own `--keep-scratch` verification task, not here.

Grading shells out to the host repo's `spec_lint.py`, so the tests build real
lint-clean (and lint-dirty) change trees and point the grader at this repo as
the host checkout.
"""

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

EVALS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(EVALS_DIR)
sys.path.insert(0, EVALS_DIR)

import run  # noqa: E402


# ---------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------

def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def _make_case(cases_dir, name, with_prompt=True, with_fixture=True):
    """Create a case directory under ``cases_dir``, optionally omitting the
    ``prompt.md`` file or the ``fixture/`` directory to model an invalid case."""
    case_dir = os.path.join(cases_dir, name)
    os.makedirs(case_dir, exist_ok=True)
    if with_prompt:
        _write(os.path.join(case_dir, "prompt.md"), "/s:plan do a thing\n")
    if with_fixture:
        os.makedirs(os.path.join(case_dir, "fixture", ".shipd"), exist_ok=True)
    return case_dir


def _write_change(scratch_dir, name, status="ready"):
    """Write a minimal, lint-clean change under
    ``<scratch>/.shipd/planned/<name>/`` with the given plan status."""
    base = os.path.join(scratch_dir, ".shipd", "planned", name)
    _write(os.path.join(base, "plan.md"),
           "# %s\n"
           "Status: %s\n\n"
           "## Idea\n\n"
           "Add a widget.\n\n"
           "### Motivation\n\n"
           "Because the widget is missing.\n\n"
           "### Details\n\n"
           "Render a widget in the widget capability.\n\n"
           "### Non-goals\n\n"
           "- Nothing else.\n\n"
           "## Implementation\n\n"
           "Wire the widget.\n" % (name, status))
    _write(os.path.join(base, "tasks.md"),
           "# %s — tasks\n\n"
           "- [ ] 1.1 [req: widget-behavior] Build the widget.\n" % name)
    _write(os.path.join(base, "specs", "widget", "spec.md"),
           "# %s — delta\n\n"
           "## ADDED Requirements\n\n"
           "### Requirement: Widget behavior\n"
           "id: widget-behavior\n\n"
           "The system SHALL render a widget.\n\n"
           "#### Scenario: Widget renders\n"
           "- **WHEN** asked to render\n"
           "- **THEN** a widget appears\n" % name)


def _write_worktree_change(scratch_dir, name, status="ready"):
    """Write a minimal, lint-clean change under the sanctioned worktree
    location ``<scratch>/.worktrees/<name>/.shipd/planned/<name>/`` — the tree a
    session following the one-change-one-worktree convention actually emits
    into."""
    worktree = os.path.join(scratch_dir, ".worktrees", name)
    _write_change(worktree, name, status=status)
    return worktree


def _empty_scratch(tmp_path):
    scratch = os.path.join(tmp_path, "scratch")
    os.makedirs(os.path.join(scratch, ".shipd", "planned"))
    return scratch


def _res(passed):
    return run.RunResult(passed=passed, failure=None if passed else "boom")


def _fake_case(tmp_path):
    cases = os.path.join(tmp_path, "cases")
    _make_case(cases, "convo")
    found = run.discover_cases(cases, case_filter="convo")
    return found[0]


class TmpPathTestCase(unittest.TestCase):
    """Base class providing a fresh per-test directory, mirroring pytest's
    ``tmp_path`` fixture via ``tempfile.TemporaryDirectory``."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.tmp_path = self._tmpdir.name


# ---------------------------------------------------------------------------
# Case discovery
# ---------------------------------------------------------------------------

class CaseDiscoveryTests(TmpPathTestCase):

    def test_discovers_valid_cases(self):
        cases = os.path.join(self.tmp_path, "cases")
        _make_case(cases, "alpha")
        _make_case(cases, "beta")
        found = run.discover_cases(cases)
        self.assertEqual([c.name for c in found], ["alpha", "beta"])
        alpha = found[0]
        self.assertEqual(alpha.prompt_path,
                          os.path.join(cases, "alpha", "prompt.md"))
        self.assertEqual(alpha.fixture_path,
                          os.path.join(cases, "alpha", "fixture"))

    def test_skips_case_missing_prompt(self):
        cases = os.path.join(self.tmp_path, "cases")
        _make_case(cases, "good")
        _make_case(cases, "no_prompt", with_prompt=False)
        self.assertEqual([c.name for c in run.discover_cases(cases)], ["good"])

    def test_skips_case_missing_fixture(self):
        cases = os.path.join(self.tmp_path, "cases")
        _make_case(cases, "good")
        _make_case(cases, "no_fixture", with_fixture=False)
        self.assertEqual([c.name for c in run.discover_cases(cases)], ["good"])

    def test_case_filter_selects_one(self):
        cases = os.path.join(self.tmp_path, "cases")
        _make_case(cases, "alpha")
        _make_case(cases, "beta")
        found = run.discover_cases(cases, case_filter="beta")
        self.assertEqual([c.name for c in found], ["beta"])

    def test_case_filter_no_match_is_empty(self):
        cases = os.path.join(self.tmp_path, "cases")
        _make_case(cases, "alpha")
        self.assertEqual(run.discover_cases(cases, case_filter="nope"), [])


# ---------------------------------------------------------------------------
# Grader selection (expect.json)
# ---------------------------------------------------------------------------

class ReadExpectTests(TmpPathTestCase):
    """``read_expect`` returns a ``(grader, handoff_requirement)`` pair;
    ``handoff_requirement`` is ``None`` for every grader but ``handoff``."""

    def test_absent_expect_json_is_structural(self):
        case_dir = os.path.join(self.tmp_path, "some-case")
        os.makedirs(case_dir)
        self.assertEqual(run.read_expect(case_dir), ("structural", None))

    def test_expect_json_without_grader_key_is_structural(self):
        case_dir = os.path.join(self.tmp_path, "some-case")
        os.makedirs(case_dir)
        _write(os.path.join(case_dir, "expect.json"), "{}\n")
        self.assertEqual(run.read_expect(case_dir), ("structural", None))

    def test_expect_json_behavior_grader(self):
        case_dir = os.path.join(self.tmp_path, "some-case")
        os.makedirs(case_dir)
        _write(os.path.join(case_dir, "expect.json"),
              '{"grader": "behavior"}\n')
        self.assertEqual(run.read_expect(case_dir), ("behavior", None))

    def test_expect_json_handoff_grader(self):
        case_dir = os.path.join(self.tmp_path, "some-case")
        os.makedirs(case_dir)
        _write(os.path.join(case_dir, "expect.json"),
              '{"grader": "handoff", "handoff_requirement": "x"}\n')
        self.assertEqual(run.read_expect(case_dir), ("handoff", "x"))

    def test_expect_json_handoff_without_requirement_raises(self):
        case_dir = os.path.join(self.tmp_path, "no-req-case")
        os.makedirs(case_dir)
        _write(os.path.join(case_dir, "expect.json"),
              '{"grader": "handoff"}\n')
        with self.assertRaises(ValueError) as ctx:
            run.read_expect(case_dir)
        message = str(ctx.exception)
        self.assertIn("no-req-case", message)
        self.assertIn("handoff_requirement", message)

    def test_expect_json_unrecognized_grader_raises(self):
        case_dir = os.path.join(self.tmp_path, "weird-case")
        os.makedirs(case_dir)
        _write(os.path.join(case_dir, "expect.json"),
              '{"grader": "not-a-real-grader"}\n')
        with self.assertRaises(ValueError) as ctx:
            run.read_expect(case_dir)
        message = str(ctx.exception)
        self.assertIn("weird-case", message)
        self.assertIn("not-a-real-grader", message)

    def test_expect_json_unreadable_raises(self):
        case_dir = os.path.join(self.tmp_path, "broken-case")
        os.makedirs(case_dir)
        _write(os.path.join(case_dir, "expect.json"), "{not valid json")
        with self.assertRaises(ValueError) as ctx:
            run.read_expect(case_dir)
        self.assertIn("broken-case", str(ctx.exception))


# ---------------------------------------------------------------------------
# Grading
# ---------------------------------------------------------------------------

class GradingTests(TmpPathTestCase):

    def test_grade_passes_clean_ready_change(self):
        scratch = _empty_scratch(self.tmp_path)
        _write_change(scratch, "demo", status="ready")
        result = run.grade(scratch, host_repo=REPO_ROOT)
        self.assertTrue(result.passed, result.failure)
        self.assertIsNone(result.failure)

    def test_grade_fails_no_change(self):
        scratch = _empty_scratch(self.tmp_path)
        result = run.grade(scratch, host_repo=REPO_ROOT)
        self.assertFalse(result.passed)
        self.assertIn(".shipd/planned", result.failure)

    def test_grade_fails_two_changes(self):
        scratch = _empty_scratch(self.tmp_path)
        _write_change(scratch, "demo", status="ready")
        _write_change(scratch, "other", status="ready")
        result = run.grade(scratch, host_repo=REPO_ROOT)
        self.assertFalse(result.passed)
        self.assertIn("one change", result.failure)

    def test_grade_fails_lint_error(self):
        scratch = _empty_scratch(self.tmp_path)
        _write_change(scratch, "demo", status="ready")
        # Corrupt the delta so the linter rejects it (requirement with no
        # scenario).
        _write(os.path.join(scratch, ".shipd", "planned", "demo",
                            "specs", "widget", "spec.md"),
               "# demo — delta\n\n"
               "## ADDED Requirements\n\n"
               "### Requirement: Broken\n"
               "id: broken\n\n"
               "The system SHALL do nothing well.\n")
        result = run.grade(scratch, host_repo=REPO_ROOT)
        self.assertFalse(result.passed)
        self.assertIn("lint", result.failure.lower())
        self.assertIn(os.path.join(".shipd", "planned", "demo"),
                      result.failure)

    def test_grade_fails_draft_status(self):
        scratch = _empty_scratch(self.tmp_path)
        _write_change(scratch, "demo", status="draft")
        result = run.grade(scratch, host_repo=REPO_ROOT)
        self.assertFalse(result.passed)
        self.assertIn("ready", result.failure)
        self.assertIn(os.path.join(".shipd", "planned", "demo"),
                      result.failure)


# ---------------------------------------------------------------------------
# Grading — worktree-aware search space
# ---------------------------------------------------------------------------

class GradingWorktreeTests(TmpPathTestCase):

    def test_grade_passes_worktree_change(self):
        """A session following the worktree convention emits its only change
        under ``<scratch>/.worktrees/<change>/.shipd/planned/`` — the grader
        must find and pass it, linting against the worktree tree."""
        scratch = _empty_scratch(self.tmp_path)
        _write_worktree_change(scratch, "demo", status="ready")
        result = run.grade(scratch, host_repo=REPO_ROOT)
        self.assertTrue(result.passed, result.failure)
        self.assertIsNone(result.failure)

    def test_grade_fails_change_in_root_and_worktree(self):
        """One change at the root and another in a worktree is two changes
        across the sanctioned locations — the run fails and both paths are
        named."""
        scratch = _empty_scratch(self.tmp_path)
        _write_change(scratch, "root_change", status="ready")
        _write_worktree_change(scratch, "wt_change", status="ready")
        result = run.grade(scratch, host_repo=REPO_ROOT)
        self.assertFalse(result.passed)
        self.assertIn("root_change", result.failure)
        self.assertIn("wt_change", result.failure)

    def test_grade_fails_no_change_names_both_locations(self):
        """With no change anywhere, the widened failure message names both
        the scratch root and the worktree location it inspected."""
        scratch = _empty_scratch(self.tmp_path)
        result = run.grade(scratch, host_repo=REPO_ROOT)
        self.assertFalse(result.passed)
        self.assertIn(".shipd/planned", result.failure)
        self.assertIn("worktree", result.failure.lower())

    def test_grade_fails_worktree_draft_status(self):
        """A worktree change not promoted to ready fails on the ready
        assertion, proving the ready check reads the plan from the worktree
        tree."""
        scratch = _empty_scratch(self.tmp_path)
        _write_worktree_change(scratch, "demo", status="draft")
        result = run.grade(scratch, host_repo=REPO_ROOT)
        self.assertFalse(result.passed)
        self.assertIn("ready", result.failure)
        self.assertIn(os.path.join(".worktrees", "demo", ".shipd", "planned",
                                    "demo"), result.failure)


# ---------------------------------------------------------------------------
# Behavior grading
# ---------------------------------------------------------------------------

_PASSING_TEST = (
    "import unittest\n\n"
    "class T(unittest.TestCase):\n"
    "    def test_ok(self):\n"
    "        self.assertTrue(True)\n")

_FAILING_TEST = (
    "import unittest\n\n"
    "class T(unittest.TestCase):\n"
    "    def test_ok(self):\n"
    "        self.assertTrue(False)\n")


def _write_behavior_case(cases_dir, name, fixture_tests, verify_tests):
    """Create ``<cases_dir>/<name>/fixture/tests/...`` and
    ``<cases_dir>/<name>/verify/...`` from ``{filename: content}`` maps,
    plus a placeholder ``prompt.md``, and return the corresponding
    behavior-graded :class:`run.Case`."""
    case_dir = os.path.join(cases_dir, name)
    _write(os.path.join(case_dir, "prompt.md"), "/s:fix do a thing\n")
    for fname, content in fixture_tests.items():
        _write(os.path.join(case_dir, "fixture", "tests", fname), content)
    for fname, content in verify_tests.items():
        _write(os.path.join(case_dir, "verify", fname), content)
    return run.Case(name=name,
                    prompt_path=os.path.join(case_dir, "prompt.md"),
                    fixture_path=os.path.join(case_dir, "fixture"),
                    grader="behavior")


def _assemble_pre_session_scratch(tmp_path, case):
    """Build a scratch dir holding just the case's shipped ``tests/`` tree,
    mirroring the state ``assemble_scratch`` leaves before any session
    runs."""
    scratch = os.path.join(tmp_path, "scratch-%s" % case.name)
    fixture_tests = os.path.join(case.fixture_path, "tests")
    if os.path.isdir(fixture_tests):
        shutil.copytree(fixture_tests, os.path.join(scratch, "tests"))
    else:
        os.makedirs(os.path.join(scratch, "tests"))
    return scratch


class BehaviorGradingTests(TmpPathTestCase):
    """Exercises ``grade_behavior`` against prebaked case/scratch trees — no
    live session, no real fixture."""

    def _make_case(self, name, fixture_tests, verify_tests):
        cases_dir = os.path.join(self.tmp_path, "cases")
        return _write_behavior_case(cases_dir, name, fixture_tests,
                                    verify_tests)

    def _scratch(self):
        scratch = os.path.join(self.tmp_path, "scratch")
        os.makedirs(scratch, exist_ok=True)
        return scratch

    def test_passing_suite_grades_passed(self):
        case = self._make_case(
            "case-a",
            fixture_tests={"test_shipped.py": _PASSING_TEST},
            verify_tests={"test_held_out.py": _PASSING_TEST})
        result = run.grade_behavior(case, self._scratch())
        self.assertTrue(result.passed, result.failure)

    def test_failing_held_out_test_grades_failed(self):
        case = self._make_case(
            "case-b",
            fixture_tests={"test_shipped.py": _PASSING_TEST},
            verify_tests={"test_held_out.py": _FAILING_TEST})
        result = run.grade_behavior(case, self._scratch())
        self.assertFalse(result.passed)
        self.assertIsNotNone(result.failure)

    def test_broken_shipped_test_grades_failed(self):
        """A shipped test that fails against the session's code — collateral
        breakage — fails the run even though the held-out test passes."""
        case = self._make_case(
            "case-c",
            fixture_tests={"test_shipped.py": _FAILING_TEST},
            verify_tests={"test_held_out.py": _PASSING_TEST})
        result = run.grade_behavior(case, self._scratch())
        self.assertFalse(result.passed)

    def test_weakened_shipped_test_is_restored_and_still_fails(self):
        """A scratch tree whose shipped test was emptied/weakened by the
        session is restored to the fixture's real (failing) content before
        grading, so the weakening cannot rescue the run."""
        case = self._make_case(
            "case-d",
            fixture_tests={"test_shipped.py": _FAILING_TEST},
            verify_tests={"test_held_out.py": _PASSING_TEST})
        scratch = self._scratch()
        # The session emptied/weakened the shipped test in the scratch tree —
        # trivially passing, unlike the fixture's real (failing) content.
        _write(os.path.join(scratch, "tests", "test_shipped.py"),
              _PASSING_TEST)
        result = run.grade_behavior(case, scratch)
        self.assertFalse(result.passed)

    def test_session_authored_test_cannot_fail_a_correct_fix(self):
        """A session that fixes the bug but also writes its own subtly wrong
        regression test is graded on the known file set only — the
        session-authored test is pruned before discovery, not run."""
        case = self._make_case(
            "case-e",
            fixture_tests={"test_shipped.py": _PASSING_TEST},
            verify_tests={"test_held_out.py": _PASSING_TEST})
        scratch = self._scratch()
        # The session added its own test file, subtly wrong.
        _write(os.path.join(scratch, "tests", "test_session_authored.py"),
              _FAILING_TEST)
        result = run.grade_behavior(case, scratch)
        self.assertTrue(result.passed, result.failure)
        self.assertFalse(os.path.exists(
            os.path.join(scratch, "tests", "test_session_authored.py")))


# ---------------------------------------------------------------------------
# Handoff grading
# ---------------------------------------------------------------------------

def _write_handoff_case(cases_dir, name, handoff_requirement="req-id",
                        shipped_test=_PASSING_TEST):
    """Create ``<cases_dir>/<name>/fixture/{src,.shipd,tests}/...`` — a
    minimal handoff fixture whose shipped suite passes against its own
    ``src/`` and content directory (unless ``shipped_test`` is overridden to
    model a mis-seeded fixture) — plus a placeholder ``prompt.md``, and
    return the corresponding handoff-graded :class:`run.Case`."""
    case_dir = os.path.join(cases_dir, name)
    _write(os.path.join(case_dir, "prompt.md"), "/s:fix do a thing\n")
    _write(os.path.join(case_dir, "fixture", "src", "report.py"),
          "VALUE = 1\n")
    _write(os.path.join(case_dir, "fixture", ".shipd", "verified", "x",
                        "spec.md"), "spec text\n")
    _write(os.path.join(case_dir, "fixture", "tests", "test_shipped.py"),
          shipped_test)
    return run.Case(name=name,
                    prompt_path=os.path.join(case_dir, "prompt.md"),
                    fixture_path=os.path.join(case_dir, "fixture"),
                    grader="handoff",
                    handoff_requirement=handoff_requirement)


def _untouched_handoff_scratch(test_case, case):
    """Build a scratch dir via the runner's own ``assemble_scratch`` — the
    real assembly path a live run takes — representing the state a session
    that made no edits at all would leave (before a transcript is written on
    top). Registers cleanup of the assembled tree and its pre-session
    snapshot on ``test_case``."""
    scratch = run.assemble_scratch(case)
    test_case.addCleanup(run.discard_handoff_snapshot, scratch)
    test_case.addCleanup(shutil.rmtree, scratch, ignore_errors=True)
    return scratch


def _write_handoff_transcript(scratch_dir, result_text, turn=None):
    """Write a fake session transcript into ``scratch_dir`` carrying
    ``result_text`` as the session's final ``result`` text, mirroring the
    shape a real turn writes. ``turn=None`` writes turn 1's
    ``eval-transcript.json``; an int N writes the resumed
    ``eval-transcript-turn<N>.json``."""
    name = (run.TRANSCRIPT_NAME if turn is None
            else "eval-transcript-turn%d.json" % turn)
    _write(os.path.join(scratch_dir, name),
          json.dumps({"type": "result", "session_id": "s1",
                      "result": result_text}))


class HandoffGradingTests(TmpPathTestCase):
    """Exercises ``grade_handoff`` against prebaked scratch trees — no live
    session, no real fixture."""

    def _make_case(self, name, handoff_requirement="req-id"):
        cases_dir = os.path.join(self.tmp_path, "cases")
        return _write_handoff_case(cases_dir, name, handoff_requirement)

    def test_untouched_tree_naming_requirement_passes(self):
        case = self._make_case("case-a")
        scratch = _untouched_handoff_scratch(self, case)
        _write_handoff_transcript(
            scratch, "The req-id requirement documents the width; no code "
                     "change is warranted.")
        result = run.grade_handoff(case, scratch)
        self.assertTrue(result.passed, result.failure)

    def test_edited_src_file_fails_naming_path(self):
        case = self._make_case("case-b")
        scratch = _untouched_handoff_scratch(self, case)
        _write(os.path.join(scratch, "src", "report.py"), "VALUE = 2\n")
        _write_handoff_transcript(scratch, "req-id")
        result = run.grade_handoff(case, scratch)
        self.assertFalse(result.passed)
        self.assertIn(os.path.join("src", "report.py"), result.failure)

    def test_edited_content_directory_file_fails_naming_path(self):
        case = self._make_case("case-c")
        scratch = _untouched_handoff_scratch(self, case)
        _write(os.path.join(scratch, ".shipd", "verified", "x", "spec.md"),
              "edited\n")
        _write_handoff_transcript(scratch, "req-id")
        result = run.grade_handoff(case, scratch)
        self.assertFalse(result.passed)
        self.assertIn(
            os.path.join(".shipd", "verified", "x", "spec.md"),
            result.failure)

    def test_transcript_missing_requirement_fails_naming_it(self):
        case = self._make_case("case-d")
        scratch = _untouched_handoff_scratch(self, case)
        _write_handoff_transcript(scratch, "Nothing relevant here.")
        result = run.grade_handoff(case, scratch)
        self.assertFalse(result.passed)
        self.assertIn("req-id", result.failure)

    def test_no_mention_of_destination_skill_still_passes(self):
        """The grader asserts the requirement id only — it never requires
        the session to have named ``/s:plan`` or any other hand-off
        destination."""
        case = self._make_case("case-e")
        scratch = _untouched_handoff_scratch(self, case)
        transcript_text = (
            "The req-id requirement documents the fixed width; the table "
            "is behaving exactly as specified, so no code change is "
            "warranted here.")
        self.assertNotIn("/s:plan", transcript_text)
        _write_handoff_transcript(scratch, transcript_text)
        result = run.grade_handoff(case, scratch)
        self.assertTrue(result.passed, result.failure)

    def test_edited_content_directory_spec_names_the_edited_path(self):
        """Against the real ``fix-spec-wrong`` case, whose assembled
        content directory also carries the injected ``.shipd/README.md``,
        editing only the fixture's own spec must be named exactly — not
        ``.shipd/README.md``, which sorts first and previously always read
        as the diff regardless of what the session actually touched."""
        case = run.discover_cases(
            run.CASES_DIR, case_filter="fix-spec-wrong")[0]
        scratch = _untouched_handoff_scratch(self, case)
        _write(os.path.join(scratch, ".shipd", "verified", "report-output",
                            "spec.md"), "edited\n")
        _write_handoff_transcript(scratch, "report-column-width")
        result = run.grade_handoff(case, scratch)
        self.assertFalse(result.passed)
        self.assertIn(
            os.path.join(".shipd", "verified", "report-output", "spec.md"),
            result.failure)
        self.assertNotIn(os.path.join(".shipd", "README.md"), result.failure)

    def test_missing_requirement_id_names_the_id_not_a_path(self):
        """The mirror case: an untouched real ``fix-spec-wrong`` scratch
        whose transcript omits the requirement id fails naming the id, not
        any content-directory path — including the injected
        ``.shipd/README.md``, which must not be mistaken for a session
        edit."""
        case = run.discover_cases(
            run.CASES_DIR, case_filter="fix-spec-wrong")[0]
        scratch = _untouched_handoff_scratch(self, case)
        _write_handoff_transcript(scratch, "Nothing relevant here.")
        result = run.grade_handoff(case, scratch)
        self.assertFalse(result.passed)
        self.assertIn("report-column-width", result.failure)
        self.assertNotIn("changed since assembly", result.failure)

    def test_rewritten_shipped_test_fails_naming_its_path(self):
        """The unchanged assertion covers the whole scratch tree, not just
        ``src/`` and the content directory: a session that rewrites the
        shipped ``tests/`` file — which would otherwise both hide the real
        change and make the shipped-suite assertion trivially pass — must
        still fail the run, naming the rewritten path."""
        case = self._make_case("case-f")
        scratch = _untouched_handoff_scratch(self, case)
        _write(os.path.join(scratch, "tests", "test_shipped.py"),
              "import unittest\n\n\n"
              "class T(unittest.TestCase):\n"
              "    def test_nop(self):\n"
              "        pass\n")
        _write_handoff_transcript(scratch, "req-id")
        result = run.grade_handoff(case, scratch)
        self.assertFalse(result.passed)
        self.assertIn(
            os.path.join("tests", "test_shipped.py"), result.failure)

    def test_stray_root_file_is_tolerated(self):
        """A new file a session drops at the scratch root — outside
        ``src/`` and outside any ``.shipd/verified/`` or ``.shipd/planned/``
        directory — is tolerated, since the authored-content comparison
        only flags a new file under one of those three locations."""
        case = self._make_case("case-g")
        scratch = _untouched_handoff_scratch(self, case)
        _write(os.path.join(scratch, "NOTES.md"), "stray notes\n")
        _write_handoff_transcript(scratch, "req-id")
        result = run.grade_handoff(case, scratch)
        self.assertTrue(result.passed, result.failure)


# ---------------------------------------------------------------------------
# Handoff grading — authored-content comparison
# ---------------------------------------------------------------------------

class HandoffAuthoredContentGradingTests(TmpPathTestCase):
    """Exercises ``grade_handoff``'s target authored-content comparison:
    engine scaffolding created outside the authored locations is tolerated;
    a new file under ``src/`` or under any ``.shipd/verified/`` or
    ``.shipd/planned/`` directory anywhere in the scratch (including inside
    a worktree) fails, naming it; a rewritten shipped test still fails
    because it was present in the pre-session snapshot. Every scratch here
    is built through the real :func:`run.assemble_scratch`, mirroring what a
    live handoff run actually leaves post-assembly — never a bare fixture
    copy. Written against ``grade_handoff`` before its repair (this is task
    1.1; task 1.2 repairs it), so the scaffolding case is expected to fail
    here — the current whole-tree comparison flags any new file, tooling-
    created or not — while the worktree case already fails today too, since
    any new file anywhere currently fails regardless of location."""

    def _make_case(self, name, handoff_requirement="req-id"):
        cases_dir = os.path.join(self.tmp_path, "cases")
        return _write_handoff_case(cases_dir, name, handoff_requirement)

    def test_engine_scaffolding_outside_authored_locations_passes(self):
        case = self._make_case("case-scaffold")
        scratch = _untouched_handoff_scratch(self, case)
        # Tooling-created scaffolding, none of it under src/ or a
        # .shipd/verified/ or .shipd/planned/ directory.
        _write(os.path.join(scratch, ".shipd", "schema", "case.json"),
              "{}\n")
        _write(os.path.join(scratch, "completed", "2026-01-01-x", "plan.md"),
              "done\n")
        _write(os.path.join(scratch, "research", "r1", "report.md"), "r\n")
        _write(os.path.join(scratch, "shipd.config.example.json"), "{}\n")
        _write_handoff_transcript(scratch, "req-id")
        result = run.grade_handoff(case, scratch)
        self.assertTrue(result.passed, result.failure)

    def test_new_file_under_src_fails_naming_it(self):
        case = self._make_case("case-src")
        scratch = _untouched_handoff_scratch(self, case)
        _write(os.path.join(scratch, "src", "helper.py"), "X = 1\n")
        _write_handoff_transcript(scratch, "req-id")
        result = run.grade_handoff(case, scratch)
        self.assertFalse(result.passed)
        self.assertIn(os.path.join("src", "helper.py"), result.failure)

    def test_new_file_under_planned_at_scratch_root_fails_naming_it(self):
        case = self._make_case("case-planned-root")
        scratch = _untouched_handoff_scratch(self, case)
        _write(os.path.join(scratch, ".shipd", "planned", "x", "plan.md"),
              "Status: draft\n")
        _write_handoff_transcript(scratch, "req-id")
        result = run.grade_handoff(case, scratch)
        self.assertFalse(result.passed)
        self.assertIn(
            os.path.join(".shipd", "planned", "x", "plan.md"),
            result.failure)

    def test_new_file_under_planned_inside_worktree_fails_naming_it(self):
        case = self._make_case("case-planned-wt")
        scratch = _untouched_handoff_scratch(self, case)
        _write(os.path.join(
            scratch, ".worktrees", "x", ".shipd", "planned", "x",
            "plan.md"), "Status: draft\n")
        _write_handoff_transcript(scratch, "req-id")
        result = run.grade_handoff(case, scratch)
        self.assertFalse(result.passed)
        self.assertIn(
            os.path.join(".worktrees", "x", ".shipd", "planned", "x",
                        "plan.md"),
            result.failure)

    def test_rewritten_shipped_test_still_fails(self):
        case = self._make_case("case-rewrite")
        scratch = _untouched_handoff_scratch(self, case)
        _write(os.path.join(scratch, "tests", "test_shipped.py"),
              "import unittest\n\n\n"
              "class T(unittest.TestCase):\n"
              "    def test_nop(self):\n"
              "        pass\n")
        _write_handoff_transcript(scratch, "req-id")
        result = run.grade_handoff(case, scratch)
        self.assertFalse(result.passed)
        self.assertIn(
            os.path.join("tests", "test_shipped.py"), result.failure)


# ---------------------------------------------------------------------------
# Behavior fixture sanity check
# ---------------------------------------------------------------------------

class CheckBehaviorFixtureTests(TmpPathTestCase):
    """Exercises ``check_behavior_fixture`` against prebaked case/scratch
    trees representing the state right after ``assemble_scratch`` — before
    any session runs."""

    def _make_case(self, name, fixture_tests, verify_tests):
        cases_dir = os.path.join(self.tmp_path, "cases")
        return _write_behavior_case(cases_dir, name, fixture_tests,
                                    verify_tests)

    def _scratch_for(self, case):
        return _assemble_pre_session_scratch(self.tmp_path, case)

    def test_correctly_seeded_fixture_has_no_failure(self):
        case = self._make_case(
            "seeded-ok",
            fixture_tests={"test_shipped.py": _PASSING_TEST},
            verify_tests={"test_held_out.py": _FAILING_TEST})
        scratch = self._scratch_for(case)
        self.assertIsNone(run.check_behavior_fixture(case, scratch))

    def test_red_shipped_suite_names_shipped_check(self):
        """A fixture whose own shipped suite does not exit 0 before the
        session fails the sanity check, naming the shipped-suite probe."""
        case = self._make_case(
            "seeded-red-shipped",
            fixture_tests={"test_shipped.py": _FAILING_TEST},
            verify_tests={"test_held_out.py": _FAILING_TEST})
        scratch = self._scratch_for(case)
        failure = run.check_behavior_fixture(case, scratch)
        self.assertIsNotNone(failure)
        self.assertIn("shipped", failure.lower())

    def test_held_out_already_passing_names_held_out_check(self):
        """A fixture whose held-out test already passes against the
        original code fails the sanity check, naming the held-out probe."""
        case = self._make_case(
            "seeded-held-out-passes",
            fixture_tests={"test_shipped.py": _PASSING_TEST},
            verify_tests={"test_held_out.py": _PASSING_TEST})
        scratch = self._scratch_for(case)
        failure = run.check_behavior_fixture(case, scratch)
        self.assertIsNotNone(failure)
        self.assertIn("held-out", failure.lower())


# ---------------------------------------------------------------------------
# Handoff fixture sanity check
# ---------------------------------------------------------------------------

class CheckHandoffFixtureTests(TmpPathTestCase):
    """Exercises ``check_handoff_fixture`` against prebaked case/scratch
    trees representing the state right after ``assemble_scratch`` — before
    any session runs."""

    def _scratch_for(self, case):
        return _untouched_handoff_scratch(self, case)

    def test_passing_shipped_suite_has_no_failure(self):
        cases_dir = os.path.join(self.tmp_path, "cases")
        case = _write_handoff_case(cases_dir, "seeded-ok")
        scratch = self._scratch_for(case)
        self.assertIsNone(run.check_handoff_fixture(case, scratch))

    def test_red_shipped_suite_names_the_check(self):
        """A fixture whose own shipped suite does not exit 0 before the
        session fails the sanity check, naming the check."""
        cases_dir = os.path.join(self.tmp_path, "cases")
        case = _write_handoff_case(
            cases_dir, "seeded-red", shipped_test=_FAILING_TEST)
        scratch = self._scratch_for(case)
        failure = run.check_handoff_fixture(case, scratch)
        self.assertIsNotNone(failure)
        self.assertIn("sanity", failure.lower())


class HandoffFixtureSanityDispatchTests(TmpPathTestCase):
    """Exercises ``execute_case``'s dispatch of the handoff sanity check —
    a failure it reports records the run as failed and spawns no
    session."""

    def test_red_fixture_fails_run_and_spawns_no_session(self):
        cases_dir = os.path.join(self.tmp_path, "cases")
        case = _write_handoff_case(
            cases_dir, "seeded-red", shipped_test=_FAILING_TEST)
        with mock.patch.object(run, "run_conversation") as spy:
            results = run.execute_case(
                case, runs=1, claude_bin="claude", keep_scratch=False)
        spy.assert_not_called()
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].passed)
        self.assertIn("sanity", results[0].failure.lower())


# ---------------------------------------------------------------------------
# Pass-rate aggregation and exit code
# ---------------------------------------------------------------------------

class SummarizeTests(unittest.TestCase):

    def test_summarize_all_pass_exits_zero(self):
        results = {"a": [_res(True), _res(True)]}
        lines, code = run.summarize(results)
        self.assertEqual(code, 0)
        self.assertTrue(any("2/2" in ln for ln in lines))

    def test_summarize_partial_pass_exits_nonzero(self):
        results = {"a": [_res(True), _res(True), _res(False)]}
        lines, code = run.summarize(results)
        self.assertNotEqual(code, 0)
        self.assertTrue(any("2/3" in ln for ln in lines))

    def test_summarize_multi_case_one_failing_exits_nonzero(self):
        results = {
            "a": [_res(True), _res(True)],
            "b": [_res(True), _res(False)],
        }
        _lines, code = run.summarize(results)
        self.assertNotEqual(code, 0)


# ---------------------------------------------------------------------------
# Conversation loop (fake turn runner — no live session)
# ---------------------------------------------------------------------------

class SessionIdTests(unittest.TestCase):

    def test_session_id_from_valid_transcript(self):
        self.assertEqual(
            run._session_id_from_transcript(
                '{"type": "result", "session_id": "abc-123"}'),
            "abc-123")

    def test_session_id_missing_field(self):
        self.assertIsNone(
            run._session_id_from_transcript('{"type": "result"}'))

    def test_session_id_non_json(self):
        self.assertIsNone(run._session_id_from_transcript("not json at all"))


class ConversationLoopTests(TmpPathTestCase):

    def test_conversation_passes_after_resume(self):
        """Turn 1 leaves nothing gradable; the loop resumes once with the
        generic reply, the resumed turn produces a clean change, and the run
        passes."""
        case = _fake_case(self.tmp_path)
        scratch = _empty_scratch(self.tmp_path)
        calls = []

        def fake_turn(prompt, scratch_dir, resume_id, turn_index, **kwargs):
            calls.append((prompt, resume_id, turn_index))
            if resume_id is not None:
                _write_change(scratch_dir, "demo", status="ready")
            return True, None, "sess-1"

        ok, failure = run.run_conversation(
            case, scratch, host_repo=REPO_ROOT, turn_runner=fake_turn)
        self.assertTrue(ok)
        self.assertIsNone(failure)
        self.assertEqual(len(calls), 2)
        # Turn 1 sends the case prompt with no resume id.
        self.assertIsNone(calls[0][1])
        # The resumed turn reuses the session and sends the generic reply.
        self.assertEqual(calls[1][1], "sess-1")
        self.assertEqual(calls[1][0], run.GOAHEAD_REPLY)
        self.assertTrue(run.grade(scratch, host_repo=REPO_ROOT).passed)

    def test_conversation_resume_cap_bounds_turns(self):
        """A session that never produces a gradable change stops at the
        cap."""
        case = _fake_case(self.tmp_path)
        scratch = _empty_scratch(self.tmp_path)
        calls = []

        def fake_turn(prompt, scratch_dir, resume_id, turn_index, **kwargs):
            calls.append(turn_index)
            return True, None, "sess-1"

        ok, failure = run.run_conversation(
            case, scratch, host_repo=REPO_ROOT, max_resumes=3,
            turn_runner=fake_turn)
        self.assertTrue(ok)
        self.assertIsNone(failure)  # turns all succeeded; grading decides
        self.assertEqual(len(calls), 4)  # 1 initial + 3 resumes
        self.assertFalse(run.grade(scratch, host_repo=REPO_ROOT).passed)

    def test_conversation_failing_turn_fails_run(self):
        case = _fake_case(self.tmp_path)
        scratch = _empty_scratch(self.tmp_path)

        def fake_turn(prompt, scratch_dir, resume_id, turn_index, **kwargs):
            if resume_id is not None:
                return False, "session CLI exited 1: boom", None
            return True, None, "sess-1"

        ok, failure = run.run_conversation(
            case, scratch, host_repo=REPO_ROOT, turn_runner=fake_turn)
        self.assertFalse(ok)
        self.assertIn("boom", failure)

    def test_conversation_stops_without_session_id(self):
        """No session id in the transcript → no resume is attempted; the
        final grade decides the run."""
        case = _fake_case(self.tmp_path)
        scratch = _empty_scratch(self.tmp_path)
        calls = []

        def fake_turn(prompt, scratch_dir, resume_id, turn_index, **kwargs):
            calls.append(turn_index)
            return True, None, None

        ok, failure = run.run_conversation(
            case, scratch, host_repo=REPO_ROOT, turn_runner=fake_turn)
        self.assertTrue(ok)
        self.assertIsNone(failure)
        self.assertEqual(len(calls), 1)

    def test_conversation_zero_resumes_is_single_shot(self):
        case = _fake_case(self.tmp_path)
        scratch = _empty_scratch(self.tmp_path)
        calls = []

        def fake_turn(prompt, scratch_dir, resume_id, turn_index, **kwargs):
            calls.append(turn_index)
            return True, None, "sess-1"

        ok, _failure = run.run_conversation(
            case, scratch, host_repo=REPO_ROOT, max_resumes=0,
            turn_runner=fake_turn)
        self.assertTrue(ok)
        self.assertEqual(len(calls), 1)


# ---------------------------------------------------------------------------
# Grader-aware conversation driving
# ---------------------------------------------------------------------------

class GraderAwareDrivingTests(TmpPathTestCase):
    """Exercises the grader-aware resume loop for a behavior-graded case —
    the gate it polls, the reply it sends, and the isolation of its probing
    from the working scratch tree — with a fake turn runner (no live
    session)."""

    def _behavior_case(self, name, fixture_tests, verify_tests):
        cases_dir = os.path.join(self.tmp_path, "cases")
        return _write_behavior_case(cases_dir, name, fixture_tests,
                                    verify_tests)

    def _blank_scratch(self, name="scratch"):
        scratch = os.path.join(self.tmp_path, name)
        os.makedirs(scratch, exist_ok=True)
        return scratch

    def test_gate_is_the_behavior_verdict_not_the_structural_one(self):
        """The scratch tree holds no change directory at all, so the
        structural grade could never pass. The loop still stops after turn 1
        because the gate it actually polls is the behavior grade — both the
        shipped and held-out tests pass — not the structural one."""
        case = self._behavior_case(
            "drift",
            fixture_tests={"test_shipped.py": _PASSING_TEST},
            verify_tests={"test_held_out.py": _PASSING_TEST})
        scratch = self._blank_scratch()
        calls = []

        def fake_turn(prompt, scratch_dir, resume_id, turn_index, **kwargs):
            calls.append(turn_index)
            return True, None, "sess-1"

        ok, failure = run.run_conversation(
            case, scratch, host_repo=REPO_ROOT, turn_runner=fake_turn)
        self.assertTrue(ok)
        self.assertIsNone(failure)
        self.assertEqual(len(calls), 1)
        self.assertFalse(run.grade(scratch, host_repo=REPO_ROOT).passed)

    def test_resume_reply_carries_no_plan_specific_instruction(self):
        """A resumed behavior-graded turn is sent the skill-neutral reply,
        never the plan-specific ``GOAHEAD_REPLY`` that instructs a session to
        emit, lint, and promote a change to ``ready``."""
        case = self._behavior_case(
            "drift",
            fixture_tests={"test_shipped.py": _PASSING_TEST},
            verify_tests={"test_held_out.py": _FAILING_TEST})
        scratch = self._blank_scratch()
        calls = []

        def fake_turn(prompt, scratch_dir, resume_id, turn_index, **kwargs):
            calls.append((prompt, resume_id, turn_index))
            return True, None, "sess-1"

        ok, _failure = run.run_conversation(
            case, scratch, host_repo=REPO_ROOT, max_resumes=1,
            turn_runner=fake_turn)
        self.assertTrue(ok)
        self.assertEqual(len(calls), 2)
        reply = calls[1][0]
        self.assertEqual(reply, run.BEHAVIOR_GOAHEAD_REPLY)
        self.assertNotEqual(reply, run.GOAHEAD_REPLY)
        for word in ("emission", "lint", "promot"):
            self.assertNotIn(word, reply.lower())

    def test_gate_probing_never_leaks_the_held_out_tree_into_scratch(self):
        """Probing the gate mid-conversation must never copy the case's
        held-out ``verify/`` tree into the scratch tree the session is still
        operating in — only a throwaway copy is graded."""
        case = self._behavior_case(
            "drift",
            fixture_tests={"test_shipped.py": _PASSING_TEST},
            verify_tests={"test_held_out.py": _FAILING_TEST})
        scratch = self._blank_scratch()

        def fake_turn(prompt, scratch_dir, resume_id, turn_index, **kwargs):
            return True, None, "sess-1"

        run.run_conversation(
            case, scratch, host_repo=REPO_ROOT, max_resumes=2,
            turn_runner=fake_turn)
        self.assertFalse(os.path.exists(
            os.path.join(scratch, "tests", "test_held_out.py")))


# ---------------------------------------------------------------------------
# Grader-selected gate and reply (structural / behavior / handoff / unknown)
# ---------------------------------------------------------------------------

class GraderSelectedDrivingTests(TmpPathTestCase):
    """Exercises ``run_conversation``'s per-grader selection of its resume
    gate and reply, covering every recognized grader plus an unrecognized
    one, with an injected turn runner (no live session). Written against
    the current behavior-versus-everything-else branch, so the handoff and
    unknown-grader cases below are expected to fail here; task 1b.2 repairs
    ``run_conversation`` to make them pass."""

    def test_handoff_case_sends_one_turn_and_is_not_resumed(self):
        cases_dir = os.path.join(self.tmp_path, "cases")
        case = _write_handoff_case(cases_dir, "handoff-drive")
        scratch = _untouched_handoff_scratch(self, case)
        calls = []

        def fake_turn(prompt, scratch_dir, resume_id, turn_index, **kwargs):
            calls.append((prompt, resume_id, turn_index))
            return True, None, "sess-1"

        ok, failure = run.run_conversation(
            case, scratch, host_repo=REPO_ROOT, turn_runner=fake_turn)
        self.assertTrue(ok, failure)
        self.assertEqual(len(calls), 1)
        # Turn 1 sends the case prompt with no resume id, and no second
        # (resumed) turn is ever sent — a handoff-graded session is never
        # told to continue.
        self.assertIsNone(calls[0][1])

    def test_structural_case_keeps_structural_gate_and_reply(self):
        case = _fake_case(self.tmp_path)
        scratch = _empty_scratch(self.tmp_path)
        calls = []

        def fake_turn(prompt, scratch_dir, resume_id, turn_index, **kwargs):
            calls.append((prompt, resume_id, turn_index))
            if resume_id is not None:
                _write_change(scratch_dir, "demo", status="ready")
            return True, None, "sess-1"

        ok, failure = run.run_conversation(
            case, scratch, host_repo=REPO_ROOT, turn_runner=fake_turn)
        self.assertTrue(ok, failure)
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[1][0], run.GOAHEAD_REPLY)
        self.assertTrue(run.grade(scratch, host_repo=REPO_ROOT).passed)

    def test_behavior_case_keeps_behavior_gate_and_reply(self):
        cases_dir = os.path.join(self.tmp_path, "cases")
        case = _write_behavior_case(
            cases_dir, "behave-drive",
            fixture_tests={"test_shipped.py": _PASSING_TEST},
            verify_tests={"test_held_out.py": _FAILING_TEST})
        scratch = os.path.join(self.tmp_path, "scratch")
        os.makedirs(scratch, exist_ok=True)
        calls = []

        def fake_turn(prompt, scratch_dir, resume_id, turn_index, **kwargs):
            calls.append((prompt, resume_id, turn_index))
            return True, None, "sess-1"

        ok, failure = run.run_conversation(
            case, scratch, host_repo=REPO_ROOT, max_resumes=1,
            turn_runner=fake_turn)
        self.assertTrue(ok, failure)
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[1][0], run.BEHAVIOR_GOAHEAD_REPLY)

    def test_unknown_grader_fails_naming_it_without_driving(self):
        base_case = _fake_case(self.tmp_path)
        case = run.Case(name=base_case.name, prompt_path=base_case.prompt_path,
                        fixture_path=base_case.fixture_path,
                        grader="mystery")
        scratch = _empty_scratch(self.tmp_path)

        def fake_turn(prompt, scratch_dir, resume_id, turn_index, **kwargs):
            self.fail("no turn should be sent for an undriveable grader")

        ok, failure = run.run_conversation(
            case, scratch, host_repo=REPO_ROOT, turn_runner=fake_turn)
        self.assertFalse(ok)
        self.assertIn("mystery", failure)


if __name__ == "__main__":
    unittest.main()
