#!/usr/bin/env python3
"""Tests for session_driver.py — the shared grade-gated resume loop.

These exercise :func:`session_driver.drive` against an injected fake turn
runner — no live ``claude`` session is spawned. The runner contract is
``runner(prompt, cwd, resume_id, turn_index, **kwargs) -> (ok, failure,
session_id)`` and :func:`drive` returns ``(ok, session_id, failure)``.
"""

import json
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
            "p", missing, binary="claude-stub-binary")

        self.assertFalse(ok)
        self.assertIsNone(session_id)
        self.assertIn(missing, failure)


class ResultTextTest(unittest.TestCase):
    def test_result_text_from_transcript(self):
        self.assertEqual(
            session_driver.result_text_from_transcript('{"result": "x"}'), "x")
        self.assertEqual(
            session_driver.result_text_from_transcript("not json"), "")
        self.assertEqual(
            session_driver.result_text_from_transcript('{"result": 3}'), "")

    def test_run_turn_result_returns_text_and_run_turn_is_unchanged(self):
        import json
        with tempfile.TemporaryDirectory() as tmp:
            transcript = json.dumps(
                {"session_id": "s1", "result": '{"mode": "change"}'})
            fake = os.path.join(tmp, "fake-claude")
            with open(fake, "w") as fh:
                fh.write("#!/bin/sh\nprintf '%%s' '%s'\n" % transcript)
            os.chmod(fake, 0o755)
            self.assertEqual(
                session_driver.run_turn_result("p", tmp, binary=fake),
                (True, None, "s1", '{"mode": "change"}'))
            self.assertEqual(
                session_driver.run_turn("p", tmp, binary=fake),
                (True, None, "s1"))

    def test_env_overlay_reaches_the_session(self):
        import json
        with tempfile.TemporaryDirectory() as tmp:
            fake = os.path.join(tmp, "fake-claude")
            with open(fake, "w") as fh:
                fh.write("#!/bin/sh\nprintf '{\"session_id\":\"s1\","
                         "\"result\":\"%s\"}' \"$SHIPD_UNATTENDED\"\n")
            os.chmod(fake, 0o755)
            saved = os.environ.pop("SHIPD_UNATTENDED", None)
            try:
                with_env = session_driver.run_turn_result(
                    "p", tmp, binary=fake, env={"SHIPD_UNATTENDED": "1"})
                without = session_driver.run_turn_result(
                    "p", tmp, binary=fake)
            finally:
                if saved is not None:
                    os.environ["SHIPD_UNATTENDED"] = saved
            self.assertEqual(with_env[3], "1")
            self.assertEqual(without[3], "")

    def test_missing_cwd_returns_empty_text(self):
        missing = os.path.join(
            tempfile.gettempdir(), "session-driver-nonexistent-dir-xyz")
        ok, failure, sid, text = session_driver.run_turn_result(
            "p", missing, binary="claude-stub-binary")
        self.assertFalse(ok)
        self.assertEqual(text, "")


class RunnerTest(unittest.TestCase):
    """The harness runner registry — argv, transcript parse, prompt rewrite."""

    def test_claude_argv(self):
        argv = session_driver.RUNNERS["claude"]["argv"](
            "claude", "p", "s1", "high", None, "/plugin", None)
        self.assertEqual(argv, [
            "claude", "-p", "p", "--output-format", "json",
            "--plugin-dir", "/plugin", "--permission-mode",
            "bypassPermissions", "--effort", "high", "--resume", "s1"])

    def test_opencode_argv(self):
        argv = session_driver.RUNNERS["opencode"]["argv"](
            "opencode", "p", "s1", "medium", "base/m", None, None)
        self.assertEqual(argv, [
            "opencode", "run", "--format", "json", "--auto",
            "--model", "base/m#medium", "--session", "s1", "p"])

    def test_opencode_parse_reads_the_last_session_and_joins_text(self):
        stdout = "\n".join([
            json.dumps({"type": "step_start", "sessionID": "ses_1"}),
            json.dumps({"type": "text", "sessionID": "ses_1",
                        "part": {"type": "text", "text": "hello"}}),
            json.dumps({"type": "text", "sessionID": "ses_2",
                        "part": {"type": "text", "text": " world"}}),
        ])
        self.assertEqual(session_driver.RUNNERS["opencode"]["parse"](stdout),
                         ("ses_2", "hello world"))

    def test_opencode_parse_ignores_non_text_and_bad_lines(self):
        stdout = "\n".join([
            "not json",
            json.dumps({"type": "tool", "sessionID": "s"}),
            json.dumps({"type": "text", "part": {"text": "x"}}),
        ])
        self.assertEqual(session_driver.RUNNERS["opencode"]["parse"](stdout),
                         ("s", "x"))

    def test_rewrite_maps_the_command_vocabulary(self):
        self.assertEqual(
            session_driver.RUNNERS["opencode"]["rewrite"](
                "Run /s:plan for the change x"),
            "Run /shipd-plan for the change x")
        self.assertEqual(
            session_driver.RUNNERS["claude"]["rewrite"]("Run /s:plan for x"),
            "Run /s:plan for x")

    def test_unknown_harness_raises_a_named_error(self):
        with self.assertRaises(session_driver.UnknownHarnessError) as caught:
            session_driver.runner_for("no-such-harness")
        self.assertIn("no-such-harness", str(caught.exception))

    def test_a_turn_reads_the_opencode_transcript(self):
        with tempfile.TemporaryDirectory() as tmp:
            transcript = json.dumps(
                {"type": "text", "sessionID": "ses_9",
                 "part": {"type": "text", "text": "hi"}})
            data = os.path.join(tmp, "out.jsonl")
            with open(data, "w", encoding="utf-8") as fh:
                fh.write(transcript + "\n")
            fake = os.path.join(tmp, "fake-opencode")
            with open(fake, "w", encoding="utf-8") as fh:
                fh.write("#!/bin/sh\ncat %s\n" % data)
            os.chmod(fake, 0o755)
            ok, failure, session_id, text = session_driver.run_turn_result(
                "p", tmp, harness="opencode", binary=fake)
        self.assertTrue(ok, failure)
        self.assertEqual(session_id, "ses_9")
        self.assertEqual(text, "hi")


class PreflightTest(unittest.TestCase):
    """The sign-in probe — one tiny turn, no resume, no plugin dir."""

    def _fake(self, tmp, stdout, code):
        record = os.path.join(tmp, "args.txt")
        fake = os.path.join(tmp, "fake-claude")
        with open(fake, "w", encoding="utf-8") as fh:
            fh.write("#!/bin/sh\nfor a in \"$@\"; do echo \"$a\" >> %s; done\n"
                     "echo '%s'\nexit %d\n" % (record, stdout, code))
        os.chmod(fake, 0o755)
        return fake, record

    def test_a_signed_in_harness_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake, record = self._fake(
                tmp, '{"session_id": "p-1", "result": "ok"}', 0)
            result = session_driver.preflight(tmp, binary=fake)
            with open(record, encoding="utf-8") as fh:
                args = fh.read().splitlines()
        self.assertEqual(result, (True, None))
        self.assertIn("-p", args)
        self.assertIn(session_driver.PREFLIGHT_PROMPT, args)
        self.assertNotIn("--plugin-dir", args)
        self.assertNotIn("--resume", args)

    def test_a_signed_out_harness_fails_with_the_detail(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake, _ = self._fake(
                tmp, '{"result": "Failed to authenticate"}', 1)
            ok, failure = session_driver.preflight(tmp, binary=fake)
        self.assertFalse(ok)
        self.assertIn("Failed to authenticate", failure)

    def test_every_runner_has_a_login_hint(self):
        for key in session_driver.RUNNERS:
            self.assertTrue(session_driver.login_hint(key), key)
        self.assertEqual(session_driver.login_hint("claude"),
                         "claude auth login")


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
