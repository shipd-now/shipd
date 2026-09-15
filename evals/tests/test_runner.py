"""Unit tests for the eval harness runner (`evals/run.py`).

These exercise the runner's pure-ish logic — case discovery, structural
grading, and pass-rate aggregation — against prebaked directory trees. They do
NOT invoke a live `claude` session; the end-to-end path is covered by the
harness's own `--keep-scratch` verification task, not here.

Grading shells out to the host repo's `spec_lint.py`, so the tests build real
lint-clean (and lint-dirty) change trees and point the grader at this repo as
the host checkout.
"""

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

    def test_absent_expect_json_is_structural(self):
        case_dir = os.path.join(self.tmp_path, "some-case")
        os.makedirs(case_dir)
        self.assertEqual(run.read_expect(case_dir), "structural")

    def test_expect_json_without_grader_key_is_structural(self):
        case_dir = os.path.join(self.tmp_path, "some-case")
        os.makedirs(case_dir)
        _write(os.path.join(case_dir, "expect.json"), "{}\n")
        self.assertEqual(run.read_expect(case_dir), "structural")

    def test_expect_json_behavior_grader(self):
        case_dir = os.path.join(self.tmp_path, "some-case")
        os.makedirs(case_dir)
        _write(os.path.join(case_dir, "expect.json"),
              '{"grader": "behavior"}\n')
        self.assertEqual(run.read_expect(case_dir), "behavior")

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
# Derived baseline prompt
# ---------------------------------------------------------------------------

class BaselinePromptTests(unittest.TestCase):

    def test_strips_leading_skill_token(self):
        text = ("/s:fix The report CLI prints its rows in the wrong "
                "order.\nSecond line stays.\n")
        result = run.baseline_prompt(text)
        self.assertEqual(
            result,
            "The report CLI prints its rows in the wrong order.\n"
            "Second line stays.\n")

    def test_strips_a_different_skill_token(self):
        text = "/s:plan Add a CSV export button.\nMore detail here.\n"
        result = run.baseline_prompt(text)
        self.assertEqual(
            result, "Add a CSV export button.\nMore detail here.\n")

    def test_no_skill_token_raises(self):
        text = "Just a plain request with no skill token.\n"
        with self.assertRaises(ValueError) as ctx:
            run.baseline_prompt(text)
        self.assertIn("/s:", str(ctx.exception))


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


class SummarizeArmTests(unittest.TestCase):
    """Exercises ``summarize`` against the ``(case, arm)``-keyed results shape
    a multi-arm run produces, alongside the legacy plain-case-name shape
    :class:`SummarizeTests` covers above."""

    def test_single_arm_mapping_renders_like_today(self):
        """A results mapping carrying only one arm — even when keyed by the
        new ``(case, arm)`` tuple shape — renders byte-identically to the
        legacy plain-case-name shape: the default single-arm invocation is
        unchanged."""
        legacy_lines, legacy_code = run.summarize(
            {"a": [_res(True), _res(True), _res(False)]})
        tupled_lines, tupled_code = run.summarize(
            {("a", "treatment"): [_res(True), _res(True), _res(False)]})
        self.assertEqual(tupled_lines, legacy_lines)
        self.assertEqual(tupled_code, legacy_code)

    def test_two_arm_mapping_renders_one_labelled_row_per_arm(self):
        results = {
            ("a", "treatment"): [_res(True), _res(True)],
            ("a", "baseline"): [_res(False), _res(False)],
        }
        lines, _code = run.summarize(results)
        treatment_rows = [ln for ln in lines
                          if "a" in ln and "treatment" in ln]
        baseline_rows = [ln for ln in lines
                         if "a" in ln and "baseline" in ln]
        self.assertEqual(len(treatment_rows), 1)
        self.assertEqual(len(baseline_rows), 1)
        self.assertIn("2/2", treatment_rows[0])
        self.assertIn("0/2", baseline_rows[0])

    def test_all_pass_treatment_all_fail_baseline_exits_zero(self):
        results = {
            ("fix-report-drift", "treatment"): [_res(True), _res(True)],
            ("fix-report-drift", "baseline"): [_res(False), _res(False)],
        }
        _lines, code = run.summarize(results)
        self.assertEqual(code, 0)

    def test_failing_treatment_exits_nonzero_whatever_baseline_did(self):
        for baseline_runs in ([_res(True), _res(True)],
                              [_res(False), _res(False)]):
            with self.subTest(baseline_runs=baseline_runs):
                results = {
                    ("fix-report-drift", "treatment"):
                        [_res(True), _res(False)],
                    ("fix-report-drift", "baseline"): baseline_runs,
                }
                _lines, code = run.summarize(results)
                self.assertNotEqual(code, 0)


class SummarizeRefusalTests(unittest.TestCase):
    """Exercises ``summarize``'s distinction between a refused run — a
    baseline-bearing arm turned away before any session spawned, because
    nothing was measured — and a baseline arm that actually ran and failed,
    which is the expected, informative outcome of a working comparison."""

    def test_refused_baseline_only_rows_exit_nonzero(self):
        refused = run.RunResult(
            False,
            "case 'plan-csv-export': baseline arm refused — grader is "
            "'structural', which only a plugin session can produce; the "
            "comparison would carry no information",
            refused=True)
        results = {("plan-csv-export", "baseline"): [refused, refused]}
        _lines, code = run.summarize(results)
        self.assertNotEqual(code, 0)

    def test_all_pass_treatment_all_fail_baseline_that_ran_exits_zero(self):
        """A baseline arm that genuinely ran (``refused`` False, the
        default) and failed every run must still exit 0 alongside an
        all-pass treatment — this is the case the fix must not regress."""
        results = {
            ("fix-report-drift", "treatment"): [_res(True), _res(True)],
            ("fix-report-drift", "baseline"): [_res(False), _res(False)],
        }
        _lines, code = run.summarize(results)
        self.assertEqual(code, 0)


# ---------------------------------------------------------------------------
# Session turn command construction (arm selection)
# ---------------------------------------------------------------------------

def _stub_completed_process(stdout='{"type": "result", "session_id": "s1"}'):
    return subprocess.CompletedProcess(
        args=[], returncode=0, stdout=stdout, stderr="")


class RunTurnCommandTests(TmpPathTestCase):
    """Exercises the command ``_run_turn`` builds for each arm, with
    ``subprocess.run`` monkeypatched so no real ``claude`` process is
    spawned."""

    def _capture_cmd(self, **run_turn_kwargs):
        captured = {}

        def fake_run(cmd, **kwargs):
            captured["cmd"] = cmd
            captured["kwargs"] = kwargs
            return _stub_completed_process()

        with mock.patch.object(run.subprocess, "run", fake_run):
            run._run_turn(
                "hello", self.tmp_path, host_repo=REPO_ROOT,
                **run_turn_kwargs)
        return captured

    def test_treatment_arm_includes_plugin_dir(self):
        captured = self._capture_cmd()
        self.assertIn("--plugin-dir", captured["cmd"])

    def test_baseline_arm_omits_plugin_dir(self):
        captured = self._capture_cmd(arm="baseline")
        self.assertNotIn("--plugin-dir", captured["cmd"])

    def test_cwd_permission_mode_and_output_format_identical_across_arms(self):
        treatment = self._capture_cmd()
        baseline = self._capture_cmd(arm="baseline")
        self.assertEqual(
            treatment["kwargs"]["cwd"], baseline["kwargs"]["cwd"])
        self.assertEqual(treatment["kwargs"]["cwd"], self.tmp_path)

        def _drop_plugin_dir(cmd):
            if "--plugin-dir" not in cmd:
                return list(cmd)
            i = cmd.index("--plugin-dir")
            return cmd[:i] + cmd[i + 2:]

        self.assertEqual(
            _drop_plugin_dir(treatment["cmd"]), baseline["cmd"])
        for flag in ("--permission-mode", "--output-format"):
            self.assertIn(flag, treatment["cmd"])
            self.assertIn(flag, baseline["cmd"])
            t_i = treatment["cmd"].index(flag)
            b_i = baseline["cmd"].index(flag)
            self.assertEqual(
                treatment["cmd"][t_i + 1], baseline["cmd"][b_i + 1])


# ---------------------------------------------------------------------------
# Arm refusal — baseline arm requires a behavior-graded case
# ---------------------------------------------------------------------------

class ArmRefusalTests(TmpPathTestCase):
    """Exercises ``execute_case``'s refusal of a baseline-bearing arm for a
    structural case, and confirms a behavior case proceeds under the same
    arms — with ``run_conversation`` mocked so no real session is spawned."""

    def _structural_case(self):
        cases = os.path.join(self.tmp_path, "cases")
        _make_case(cases, "struct-case")
        found = run.discover_cases(cases, case_filter="struct-case")
        return found[0]

    def _behavior_case(self):
        # A correctly-seeded fixture: the shipped suite passes on its own,
        # and the held-out test fails against the fixture's original code —
        # the shape :func:`check_behavior_fixture`'s sanity check requires,
        # so the mocked ``run_conversation`` is actually reached.
        cases_dir = os.path.join(self.tmp_path, "cases")
        return _write_behavior_case(
            cases_dir, "behave-case",
            fixture_tests={"test_shipped.py": _PASSING_TEST},
            verify_tests={"test_held_out.py": _FAILING_TEST})

    def test_structural_case_refuses_baseline_arm(self):
        case = self._structural_case()
        with mock.patch.object(run, "run_conversation") as spy:
            results = run.execute_case(
                case, runs=2, claude_bin="claude", keep_scratch=False,
                arm="baseline")
        spy.assert_not_called()
        self.assertEqual(len(results), 2)
        for r in results:
            self.assertFalse(r.passed)
            self.assertIn("struct-case", r.failure)
            self.assertIn("structural", r.failure.lower())

    def test_structural_case_refuses_both_arm(self):
        case = self._structural_case()
        with mock.patch.object(run, "run_conversation") as spy:
            results = run.execute_case(
                case, runs=2, claude_bin="claude", keep_scratch=False,
                arm="both")
        spy.assert_not_called()
        self.assertEqual(len(results), 2)
        for r in results:
            self.assertFalse(r.passed)
            self.assertIn("struct-case", r.failure)
            self.assertIn("structural", r.failure.lower())

    def test_behavior_case_proceeds_under_baseline_arm(self):
        case = self._behavior_case()
        with mock.patch.object(
                run, "run_conversation",
                return_value=(True, None)) as spy:
            run.execute_case(
                case, runs=1, claude_bin="claude", keep_scratch=False,
                arm="baseline")
        spy.assert_called_once()

    def test_behavior_case_proceeds_under_both_arm(self):
        case = self._behavior_case()
        with mock.patch.object(
                run, "run_conversation",
                return_value=(True, None)) as spy:
            run.execute_case(
                case, runs=1, claude_bin="claude", keep_scratch=False,
                arm="both")
        spy.assert_called_once()

    def test_behavior_case_with_no_skill_token_refuses_baseline_arm(self):
        """A behavior case whose prompt.md carries no leading /s:<skill>
        token cannot derive a baseline prompt — the run is refused before a
        session is spawned, naming the case."""
        cases_dir = os.path.join(self.tmp_path, "cases")
        case = _write_behavior_case(
            cases_dir, "no-token-case",
            fixture_tests={"test_shipped.py": _PASSING_TEST},
            verify_tests={"test_held_out.py": _PASSING_TEST})
        _write(case.prompt_path, "Just fix the bug, no skill token here.\n")
        with mock.patch.object(run, "run_conversation") as spy:
            results = run.execute_case(
                case, runs=2, claude_bin="claude", keep_scratch=False,
                arm="baseline")
        spy.assert_not_called()
        self.assertEqual(len(results), 2)
        for r in results:
            self.assertFalse(r.passed)
            self.assertIn("no-token-case", r.failure)


class CombinedArmWholeRefusalTests(unittest.TestCase):
    """Exercises the invocation-level refusal of a ``both`` request against a
    structural case, driven through ``main`` rather than ``execute_case``
    directly. ``main`` iterates the concrete arms of ``both`` — treatment,
    then baseline — as separate ``execute_case`` calls; each call decides its
    own refusal in isolation, so the treatment sub-call (for which
    ``_arm_refusal`` always returns ``None``) used to run to completion,
    spawning a real session, before the baseline sub-call refused. The fix
    decides the refusal once for the whole selected arm set, before either
    concrete arm executes, so a structural case's treatment session never
    spawns under ``both`` either."""

    def test_both_arm_refuses_whole_invocation_for_structural_case(self):
        with mock.patch.object(run, "run_conversation") as spy:
            exit_code = run.main(
                ["--case", "plan-csv-export", "--arm", "both"])
        spy.assert_not_called()
        self.assertNotEqual(exit_code, 0)


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


if __name__ == "__main__":
    unittest.main()
