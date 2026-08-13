#!/usr/bin/env python3
"""Tests for session_driver.py — the shared grade-gated resume loop.

These exercise :func:`session_driver.drive` against an injected fake turn
runner — no live ``claude`` session is spawned. The runner contract is
``runner(prompt, cwd, resume_id, turn_index, **kwargs) -> (ok, failure,
session_id)`` and :func:`drive` returns ``(ok, session_id, failure)``.
"""

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
sys.path.insert(0, SCRIPTS)

import session_driver  # noqa: E402


class DriveTest(unittest.TestCase):
    def test_stops_when_grade_passes_on_turn_two(self):
        """The grade passes after the first resumed turn, so exactly two turns
        run and the result is success."""
        calls = []

        def runner(prompt, cwd, resume_id, turn_index, **kwargs):
            calls.append((prompt, resume_id, turn_index))
            return True, None, "sess-%d" % turn_index

        # False before the resume, True once two turns have run.
        def grade_fn():
            return len(calls) >= 2

        ok, session_id, failure = session_driver.drive(
            "go", "/cwd", grade_fn, "reply", max_resumes=4, timeout=1,
            runner=runner)

        self.assertTrue(ok)
        self.assertIsNone(failure)
        self.assertEqual(len(calls), 2)
        # Turn 1 sends the prompt with no resume id.
        self.assertEqual(calls[0], ("go", None, 1))
        # The resumed turn reuses the session and sends the reply text.
        self.assertEqual(calls[1][0], "reply")
        self.assertEqual(calls[1][1], "sess-1")

    def test_exhaustion_returns_last_session_id(self):
        """A grade that never passes exhausts ``max_resumes`` and the result
        carries the final session id for later interactive resume."""
        calls = []

        def runner(prompt, cwd, resume_id, turn_index, **kwargs):
            calls.append(turn_index)
            return True, None, "sess-%d" % turn_index

        ok, session_id, failure = session_driver.drive(
            "go", "/cwd", lambda: False, "reply", max_resumes=4, timeout=1,
            runner=runner)

        self.assertTrue(ok)  # every turn succeeded; grading is the caller's job
        self.assertIsNone(failure)
        self.assertEqual(len(calls), 5)  # 1 initial + 4 resumes
        self.assertEqual(session_id, "sess-5")

    def test_turn_failure_surfaces_ok_false_and_failure(self):
        """A failing turn short-circuits the loop with ``ok=False`` and the
        failure summary."""
        def runner(prompt, cwd, resume_id, turn_index, **kwargs):
            if resume_id is not None:
                return False, "session CLI exited 1: boom", None
            return True, None, "sess-1"

        ok, session_id, failure = session_driver.drive(
            "go", "/cwd", lambda: False, "reply", max_resumes=4, timeout=1,
            runner=runner)

        self.assertFalse(ok)
        self.assertIn("boom", failure)

    def test_on_session_fires_once_with_first_session_id(self):
        """``drive`` invokes the ``on_session`` callback with the session id the
        first time a turn yields one — on turn 1, before the loop ends — and not
        again on later turns that yield fresh ids."""
        seen = []

        def runner(prompt, cwd, resume_id, turn_index, **kwargs):
            return True, None, "sess-%d" % turn_index

        session_driver.drive(
            "go", "/cwd", lambda: False, "reply", max_resumes=3, timeout=1,
            runner=runner, on_session=seen.append)

        # Fired exactly once, carrying the first turn's id — even though later
        # turns produced sess-2, sess-3, sess-4.
        self.assertEqual(seen, ["sess-1"])

    def test_reply_text_passed_to_every_resumed_turn(self):
        """Turn 1 carries the initial prompt; every resumed turn carries the
        reply text."""
        prompts = []

        def runner(prompt, cwd, resume_id, turn_index, **kwargs):
            prompts.append(prompt)
            return True, None, "sess-1"

        session_driver.drive(
            "initial", "/cwd", lambda: False, "the-reply", max_resumes=3,
            timeout=1, runner=runner)

        self.assertEqual(prompts[0], "initial")
        self.assertTrue(all(p == "the-reply" for p in prompts[1:]))
        self.assertEqual(len(prompts), 4)  # 1 initial + 3 resumes


class RunTurnTest(unittest.TestCase):
    def test_missing_cwd_fails_the_turn_without_raising(self):
        """A turn launched in a working directory that no longer exists
        returns a failure naming the directory rather than raising."""
        missing = os.path.join(
            tempfile.gettempdir(), "session-driver-nonexistent-dir-xyz")
        self.assertFalse(os.path.exists(missing))

        ok, failure, session_id = session_driver.run_turn(
            "p", missing, claude_bin="claude-stub-binary")

        self.assertFalse(ok)
        self.assertIsNone(session_id)
        self.assertIn(missing, failure)


class FailureDetailTest(unittest.TestCase):
    """A non-zero ``claude -p`` turn must never surface a blank reason, even
    when the CLI writes its fault to stdout (JSON result) with empty stderr."""

    def test_stderr_last_line_wins(self):
        detail = session_driver._failure_detail(
            '{"result": "ignored"}', "warn: x\nfatal: boom")
        self.assertEqual(detail, "fatal: boom")

    def test_mines_stdout_json_result_when_stderr_blank(self):
        # The real regression: a mid-response connection drop lands in the
        # stdout result with empty stderr.
        stdout = ('{"type": "result", "is_error": true, "result": '
                  '"API Error: Connection closed mid-response."}')
        detail = session_driver._failure_detail(stdout, "")
        self.assertIn("Connection closed mid-response", detail)

    def test_non_json_stdout_tail_when_stderr_blank(self):
        detail = session_driver._failure_detail("line one\nline two", "  ")
        self.assertEqual(detail, "line two")

    def test_blank_both_yields_classified_fallback_not_empty(self):
        detail = session_driver._failure_detail("", "")
        self.assertTrue(detail.strip())
        self.assertIn("transient", detail)


if __name__ == "__main__":
    unittest.main()
