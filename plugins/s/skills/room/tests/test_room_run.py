#!/usr/bin/env python3
"""Tests for ``shipd room run`` (room_run.py).

Every GitHub call goes through ``FakeGh`` and every turn through a
``FakeRunner``: no ``gh`` process, no network, and no real harness session.
"""

import json
import os
import sys
import unittest
import unittest.mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "scripts")))

import room_run  # noqa: E402
from test_room import (  # noqa: E402
    FakeClock, FakeGh, FakeSleep, RoomTestBase, _run, card_comment,
    first_marker, msg_comment)

URL = "https://github.com/o/r/pull/7"


class FakeRunner:
    """The turn runner seam: records each call and the agent env var, returns
    scripted ``(ok, failure, session_id)`` results, and optionally runs a
    ``hook(call_number)`` that mutates the fake GitHub."""

    def __init__(self, results=None, hook=None):
        self.results = list(results or [])
        self.hook = hook
        self.calls = []
        self.agents = []

    def __call__(self, prompt, cwd, resume_id, turn_index):
        self.calls.append((prompt, cwd, resume_id, turn_index))
        self.agents.append(os.environ.get("SHIPD_ROOM_AGENT"))
        if self.hook is not None:
            self.hook(len(self.calls))
        if self.results:
            return self.results.pop(0)
        return True, None, "s-1"


def waiting(comment_id=10, to="author-a", opener="other"):
    """A task addressed to ``to`` and waiting for its turn."""
    return msg_comment(comment_id, opener, text="please look",
                       state="input-required", round=1, to=to)


class RunTestBase(RoomTestBase):
    def run_verb(self, gh, *argv, runner=None, clock=None, sleep=None,
                 env=None):
        seams = {"sleep": sleep or FakeSleep(),
                 "clock": clock or FakeClock(),
                 "runner": runner or FakeRunner()}
        return _run(["run"] + list(argv) + ["--root", self.root], gh,
                    env=env, seams=seams)

    def summary(self, out):
        lines = out.splitlines()
        self.assertEqual(len(lines), 1, out)
        return json.loads(lines[0])


class RunStartTest(RunTestBase):
    def test_reviewer_on_the_authors_account_is_refused(self):
        gh = FakeGh(comments=[waiting(to="rev-b")], login="Mikkel",
                    pr_author="mikkel")
        runner = FakeRunner()
        code, out, err = self.run_verb(
            gh, "7", "--role", "reviewer", "--agent", "rev-b",
            runner=runner)
        self.assertEqual(code, 1, err)
        self.assertEqual(out, "")
        self.assertEqual(err.count("Error:"), 1, err)
        self.assertEqual(gh.posts(), [])
        self.assertEqual(runner.calls, [])

    def test_unreadable_login_is_one_error(self):
        gh = FakeGh(user_fail=True)
        code, out, err = self.run_verb(
            gh, "7", "--role", "author", "--agent", "a")
        self.assertEqual(code, 1, err)
        self.assertEqual(err.count("Error:"), 1, err)
        self.assertEqual(gh.posts(), [])

    def test_author_off_the_authors_account_warns_and_continues(self):
        gh = FakeGh(login="other-login", pr_author="mikkel", state="MERGED")
        code, out, err = self.run_verb(
            gh, "7", "--role", "author", "--agent", "a")
        self.assertEqual(code, 0, err)
        self.assertIn("warning", err)
        self.assertEqual(len(gh.posts()), 1)

    def test_card_is_joined_once_with_role_and_default_skills(self):
        gh = FakeGh(login="reviewer-b", pr_author="mikkel", state="MERGED")
        code, out, err = self.run_verb(
            gh, "7", "--role", "reviewer", "--agent", "rev-b")
        self.assertEqual(code, 0, err)
        posts = gh.posts()
        self.assertEqual(len(posts), 1)
        card = first_marker(posts[0])
        self.assertEqual(card.role, "reviewer")
        self.assertEqual(tuple(card.skills),
                         ("review-finding", "question", "status"))
        self.assertEqual(card.harness, "claude")
        self.assertEqual(self.summary(out)["reason"], "closed")

    def test_unknown_harness_is_a_usage_error_before_any_gh_call(self):
        gh = FakeGh()
        code, out, err = self.run_verb(
            gh, "7", "--role", "author", "--agent", "a",
            "--harness", "nope")
        self.assertEqual(code, 2)
        self.assertEqual(gh.calls, [])

    def test_missing_role_is_a_usage_error(self):
        gh = FakeGh()
        code, out, err = self.run_verb(gh, "7", "--agent", "a")
        self.assertEqual(code, 2)
        self.assertEqual(gh.calls, [])


class RunLoopTest(RunTestBase):
    def test_two_tasks_resume_one_session(self):
        gh = FakeGh(comments=[waiting(10)])

        def hook(n):
            if n == 1:
                gh.comments.append(waiting(2000))
            else:
                gh.state = "MERGED"

        runner = FakeRunner(hook=hook)
        code, out, err = self.run_verb(
            gh, "7", "--role", "author", "--agent", "author-a",
            runner=runner)
        self.assertEqual(code, 0, err)
        self.assertEqual([c[2] for c in runner.calls], [None, "s-1"])
        for prompt, cwd, _resume, _idx in runner.calls:
            self.assertTrue(
                prompt.startswith("/s:room %s role author" % URL), prompt)
            self.assertEqual(cwd, os.path.abspath(self.root))
        summary = self.summary(out)
        self.assertEqual(summary["turns"], 2)
        self.assertEqual(summary["session_id"], "s-1")
        self.assertEqual(summary["reason"], "closed")
        self.assertEqual(len(gh.posts()), 1)

    def test_prompt_names_role_and_skills(self):
        gh = FakeGh(comments=[waiting(10)])
        runner = FakeRunner()
        self.run_verb(gh, "7", "--role", "author", "--agent", "author-a",
                      "--skill", "alpha", "--skill", "beta",
                      "--max-turns", "1", runner=runner)
        self.assertEqual(runner.calls[0][0],
                         "/s:room %s role author, skills alpha, beta" % URL)

    def test_agent_name_reaches_the_session(self):
        gh = FakeGh(comments=[waiting(10, to="rev-b")], login="rev",
                    pr_author="mikkel")
        runner = FakeRunner()
        code, out, err = self.run_verb(
            gh, "7", "--role", "reviewer", "--agent", "rev-b",
            "--max-turns", "1", runner=runner)
        self.assertEqual(code, 0, err)
        self.assertEqual(runner.agents, ["rev-b"])

    def test_no_task_spends_no_turn(self):
        gh = FakeGh()
        runner = FakeRunner()
        sleep = FakeSleep()
        code, out, err = self.run_verb(
            gh, "7", "--role", "author", "--agent", "author-a",
            "--budget", "60", "--interval", "5", runner=runner,
            clock=FakeClock(step=10), sleep=sleep)
        self.assertEqual(code, 0, err)
        self.assertEqual(runner.calls, [])
        summary = self.summary(out)
        self.assertEqual(summary["turns"], 0)
        self.assertEqual(summary["reason"], "budget")

    def test_default_runner_calls_run_turn_without_env(self):
        gh = FakeGh(comments=[waiting(10)])
        with unittest.mock.patch.object(
                room_run.session_driver, "run_turn",
                return_value=(True, None, "s-1")) as run_turn:
            code, out, err = _run(
                ["run", "7", "--role", "author", "--agent", "author-a",
                 "--max-turns", "1", "--model", "high",
                 "--turn-timeout", "99", "--root", self.root], gh,
                seams={"sleep": FakeSleep(), "clock": FakeClock()})
        self.assertEqual(code, 0, err)
        self.assertEqual(run_turn.call_count, 1)
        args, kwargs = run_turn.call_args
        self.assertNotIn("env", kwargs)
        self.assertEqual(args[1], os.path.abspath(self.root))
        self.assertIsNone(kwargs["resume_id"])
        self.assertEqual(kwargs["timeout"], 99.0)
        self.assertEqual(kwargs["harness"], "claude")
        self.assertEqual(kwargs["effort"], "high")
        self.assertEqual(kwargs["plugin_dir"], room_run.PLUGIN_DIR)
        self.assertEqual(self.summary(out)["session_id"], "s-1")


class RunStopTest(RunTestBase):
    def test_merged_pull_request_ends_the_run(self):
        gh = FakeGh(state="MERGED")
        runner = FakeRunner()
        code, out, err = self.run_verb(
            gh, "7", "--role", "author", "--agent", "author-a",
            runner=runner)
        self.assertEqual(code, 0, err)
        summary = self.summary(out)
        self.assertEqual(summary["reason"], "closed")
        self.assertEqual(summary["closed"], "merged")
        self.assertEqual(summary["context"], "o/r#7")
        self.assertEqual(runner.calls, [])

    def test_closed_pull_request_takes_no_turn_even_with_a_task(self):
        gh = FakeGh(comments=[waiting(10)], state="CLOSED")
        runner = FakeRunner()
        code, out, err = self.run_verb(
            gh, "7", "--role", "author", "--agent", "author-a",
            runner=runner)
        self.assertEqual(code, 0, err)
        self.assertEqual(self.summary(out)["closed"], "closed")
        self.assertEqual(runner.calls, [])

    def test_turn_cap_ends_the_run(self):
        gh = FakeGh(comments=[waiting(10)])
        runner = FakeRunner()
        code, out, err = self.run_verb(
            gh, "7", "--role", "author", "--agent", "author-a",
            "--max-turns", "1", runner=runner)
        self.assertEqual(code, 0, err)
        self.assertEqual(len(runner.calls), 1)
        summary = self.summary(out)
        self.assertEqual(summary["reason"], "turn-cap")
        self.assertEqual(summary["turns"], 1)
        self.assertNotIn("closed", summary)
        self.assertNotIn("failure", summary)

    def test_failed_turn_ends_the_run(self):
        gh = FakeGh(comments=[waiting(10)])
        runner = FakeRunner(results=[
            (False, "session CLI exited 1: boom", None)])
        code, out, err = self.run_verb(
            gh, "7", "--role", "author", "--agent", "author-a",
            runner=runner)
        self.assertEqual(code, 1)
        summary = self.summary(out)
        self.assertEqual(summary["reason"], "turn-failed")
        self.assertEqual(summary["failure"], "session CLI exited 1: boom")
        self.assertEqual(err.count("Error:"), 1, err)

    def test_watch_error_ends_the_run(self):
        gh = FakeGh(comments=[waiting(10)], state="OPEN")
        real = gh.__call__

        calls = {"n": 0}

        def flaky(args, input=None):
            if args[:2] == ["pr", "view"] and "state" in args:
                calls["n"] += 1
                return 1, "", "boom"
            return real(args, input=input)

        runner = FakeRunner()
        code, out, err = _run(
            ["run", "7", "--role", "author", "--agent", "author-a",
             "--root", self.root], flaky,
            seams={"sleep": FakeSleep(), "clock": FakeClock(),
                   "runner": runner})
        self.assertEqual(code, 1, err)
        summary = self.summary(out)
        self.assertEqual(summary["reason"], "watch-failed")
        self.assertIn("boom", summary["failure"])
        self.assertEqual(err.count("Error:"), 1, err)
        self.assertEqual(runner.calls, [])


if __name__ == "__main__":
    unittest.main()
