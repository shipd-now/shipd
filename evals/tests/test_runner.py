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
import sys

import pytest

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
    scratch = os.path.join(str(tmp_path), "scratch")
    os.makedirs(os.path.join(scratch, ".shipd", "planned"))
    return scratch


# ---------------------------------------------------------------------------
# Case discovery
# ---------------------------------------------------------------------------

def test_discovers_valid_cases(tmp_path):
    cases = os.path.join(str(tmp_path), "cases")
    _make_case(cases, "alpha")
    _make_case(cases, "beta")
    found = run.discover_cases(cases)
    assert [c.name for c in found] == ["alpha", "beta"]
    alpha = found[0]
    assert alpha.prompt_path == os.path.join(cases, "alpha", "prompt.md")
    assert alpha.fixture_path == os.path.join(cases, "alpha", "fixture")


def test_skips_case_missing_prompt(tmp_path):
    cases = os.path.join(str(tmp_path), "cases")
    _make_case(cases, "good")
    _make_case(cases, "no_prompt", with_prompt=False)
    assert [c.name for c in run.discover_cases(cases)] == ["good"]


def test_skips_case_missing_fixture(tmp_path):
    cases = os.path.join(str(tmp_path), "cases")
    _make_case(cases, "good")
    _make_case(cases, "no_fixture", with_fixture=False)
    assert [c.name for c in run.discover_cases(cases)] == ["good"]


def test_case_filter_selects_one(tmp_path):
    cases = os.path.join(str(tmp_path), "cases")
    _make_case(cases, "alpha")
    _make_case(cases, "beta")
    found = run.discover_cases(cases, case_filter="beta")
    assert [c.name for c in found] == ["beta"]


def test_case_filter_no_match_is_empty(tmp_path):
    cases = os.path.join(str(tmp_path), "cases")
    _make_case(cases, "alpha")
    assert run.discover_cases(cases, case_filter="nope") == []


# ---------------------------------------------------------------------------
# Grading
# ---------------------------------------------------------------------------

def test_grade_passes_clean_ready_change(tmp_path):
    scratch = _empty_scratch(tmp_path)
    _write_change(scratch, "demo", status="ready")
    result = run.grade(scratch, host_repo=REPO_ROOT)
    assert result.passed, result.failure
    assert result.failure is None


def test_grade_fails_no_change(tmp_path):
    scratch = _empty_scratch(tmp_path)
    result = run.grade(scratch, host_repo=REPO_ROOT)
    assert not result.passed
    assert ".shipd/planned" in result.failure


def test_grade_fails_two_changes(tmp_path):
    scratch = _empty_scratch(tmp_path)
    _write_change(scratch, "demo", status="ready")
    _write_change(scratch, "other", status="ready")
    result = run.grade(scratch, host_repo=REPO_ROOT)
    assert not result.passed
    assert "one change" in result.failure


def test_grade_fails_lint_error(tmp_path):
    scratch = _empty_scratch(tmp_path)
    _write_change(scratch, "demo", status="ready")
    # Corrupt the delta so the linter rejects it (requirement with no scenario).
    _write(os.path.join(scratch, ".shipd", "planned", "demo",
                        "specs", "widget", "spec.md"),
           "# demo — delta\n\n"
           "## ADDED Requirements\n\n"
           "### Requirement: Broken\n"
           "id: broken\n\n"
           "The system SHALL do nothing well.\n")
    result = run.grade(scratch, host_repo=REPO_ROOT)
    assert not result.passed
    assert "lint" in result.failure.lower()
    assert os.path.join(".shipd", "planned", "demo") in result.failure


def test_grade_fails_draft_status(tmp_path):
    scratch = _empty_scratch(tmp_path)
    _write_change(scratch, "demo", status="draft")
    result = run.grade(scratch, host_repo=REPO_ROOT)
    assert not result.passed
    assert "ready" in result.failure
    assert os.path.join(".shipd", "planned", "demo") in result.failure


# ---------------------------------------------------------------------------
# Grading — worktree-aware search space
# ---------------------------------------------------------------------------

def test_grade_passes_worktree_change(tmp_path):
    """A session following the worktree convention emits its only change under
    ``<scratch>/.worktrees/<change>/.shipd/planned/`` — the grader must find and
    pass it, linting against the worktree tree."""
    scratch = _empty_scratch(tmp_path)
    _write_worktree_change(scratch, "demo", status="ready")
    result = run.grade(scratch, host_repo=REPO_ROOT)
    assert result.passed, result.failure
    assert result.failure is None


def test_grade_fails_change_in_root_and_worktree(tmp_path):
    """One change at the root and another in a worktree is two changes across
    the sanctioned locations — the run fails and both paths are named."""
    scratch = _empty_scratch(tmp_path)
    _write_change(scratch, "root_change", status="ready")
    _write_worktree_change(scratch, "wt_change", status="ready")
    result = run.grade(scratch, host_repo=REPO_ROOT)
    assert not result.passed
    assert "root_change" in result.failure
    assert "wt_change" in result.failure


def test_grade_fails_no_change_names_both_locations(tmp_path):
    """With no change anywhere, the widened failure message names both the
    scratch root and the worktree location it inspected."""
    scratch = _empty_scratch(tmp_path)
    result = run.grade(scratch, host_repo=REPO_ROOT)
    assert not result.passed
    assert ".shipd/planned" in result.failure
    assert "worktree" in result.failure.lower()


def test_grade_fails_worktree_draft_status(tmp_path):
    """A worktree change not promoted to ready fails on the ready assertion,
    proving the ready check reads the plan from the worktree tree."""
    scratch = _empty_scratch(tmp_path)
    _write_worktree_change(scratch, "demo", status="draft")
    result = run.grade(scratch, host_repo=REPO_ROOT)
    assert not result.passed
    assert "ready" in result.failure
    assert os.path.join(".worktrees", "demo", ".shipd", "planned",
                        "demo") in result.failure


# ---------------------------------------------------------------------------
# Pass-rate aggregation and exit code
# ---------------------------------------------------------------------------

def _res(passed):
    return run.RunResult(passed=passed, failure=None if passed else "boom")


def test_summarize_all_pass_exits_zero():
    results = {"a": [_res(True), _res(True)]}
    lines, code = run.summarize(results)
    assert code == 0
    assert any("2/2" in ln for ln in lines)


def test_summarize_partial_pass_exits_nonzero():
    results = {"a": [_res(True), _res(True), _res(False)]}
    lines, code = run.summarize(results)
    assert code != 0
    assert any("2/3" in ln for ln in lines)


def test_summarize_multi_case_one_failing_exits_nonzero():
    results = {
        "a": [_res(True), _res(True)],
        "b": [_res(True), _res(False)],
    }
    _lines, code = run.summarize(results)
    assert code != 0


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))


# ---------------------------------------------------------------------------
# Conversation loop (fake turn runner — no live session)
# ---------------------------------------------------------------------------

def _fake_case(tmp_path):
    cases = os.path.join(str(tmp_path), "cases")
    _make_case(cases, "convo")
    found = run.discover_cases(cases, case_filter="convo")
    return found[0]


def test_session_id_from_valid_transcript():
    assert run._session_id_from_transcript(
        '{"type": "result", "session_id": "abc-123"}') == "abc-123"


def test_session_id_missing_field():
    assert run._session_id_from_transcript('{"type": "result"}') is None


def test_session_id_non_json():
    assert run._session_id_from_transcript("not json at all") is None


def test_conversation_passes_after_resume(tmp_path):
    """Turn 1 leaves nothing gradable; the loop resumes once with the generic
    reply, the resumed turn produces a clean change, and the run passes."""
    case = _fake_case(tmp_path)
    scratch = _empty_scratch(tmp_path)
    calls = []

    def fake_turn(prompt, scratch_dir, resume_id, turn_index, **kwargs):
        calls.append((prompt, resume_id, turn_index))
        if resume_id is not None:
            _write_change(scratch_dir, "demo", status="ready")
        return True, None, "sess-1"

    ok, failure = run.run_conversation(
        case, scratch, host_repo=REPO_ROOT, turn_runner=fake_turn)
    assert ok and failure is None
    assert len(calls) == 2
    # Turn 1 sends the case prompt with no resume id.
    assert calls[0][1] is None
    # The resumed turn reuses the session and sends the generic reply.
    assert calls[1][1] == "sess-1"
    assert calls[1][0] == run.GOAHEAD_REPLY
    assert run.grade(scratch, host_repo=REPO_ROOT).passed


def test_conversation_resume_cap_bounds_turns(tmp_path):
    """A session that never produces a gradable change stops at the cap."""
    case = _fake_case(tmp_path)
    scratch = _empty_scratch(tmp_path)
    calls = []

    def fake_turn(prompt, scratch_dir, resume_id, turn_index, **kwargs):
        calls.append(turn_index)
        return True, None, "sess-1"

    ok, failure = run.run_conversation(
        case, scratch, host_repo=REPO_ROOT, max_resumes=3,
        turn_runner=fake_turn)
    assert ok and failure is None  # turns all succeeded; grading decides
    assert len(calls) == 4  # 1 initial + 3 resumes
    assert not run.grade(scratch, host_repo=REPO_ROOT).passed


def test_conversation_failing_turn_fails_run(tmp_path):
    case = _fake_case(tmp_path)
    scratch = _empty_scratch(tmp_path)

    def fake_turn(prompt, scratch_dir, resume_id, turn_index, **kwargs):
        if resume_id is not None:
            return False, "session CLI exited 1: boom", None
        return True, None, "sess-1"

    ok, failure = run.run_conversation(
        case, scratch, host_repo=REPO_ROOT, turn_runner=fake_turn)
    assert not ok
    assert "boom" in failure


def test_conversation_stops_without_session_id(tmp_path):
    """No session id in the transcript → no resume is attempted; the final
    grade decides the run."""
    case = _fake_case(tmp_path)
    scratch = _empty_scratch(tmp_path)
    calls = []

    def fake_turn(prompt, scratch_dir, resume_id, turn_index, **kwargs):
        calls.append(turn_index)
        return True, None, None

    ok, failure = run.run_conversation(
        case, scratch, host_repo=REPO_ROOT, turn_runner=fake_turn)
    assert ok and failure is None
    assert len(calls) == 1


def test_conversation_zero_resumes_is_single_shot(tmp_path):
    case = _fake_case(tmp_path)
    scratch = _empty_scratch(tmp_path)
    calls = []

    def fake_turn(prompt, scratch_dir, resume_id, turn_index, **kwargs):
        calls.append(turn_index)
        return True, None, "sess-1"

    ok, _failure = run.run_conversation(
        case, scratch, host_repo=REPO_ROOT, max_resumes=0,
        turn_runner=fake_turn)
    assert ok
    assert len(calls) == 1
