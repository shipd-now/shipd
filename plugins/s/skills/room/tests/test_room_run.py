#!/usr/bin/env python3
"""Tests for ``shipd room run`` (room_run.py).

Every GitHub call goes through ``FakeGh`` and every turn through a
``FakeRunner``: no ``gh`` process, no network, and no real harness session.
"""

import fcntl
import json
import os
import shutil
import sys
import tempfile
import unittest
import unittest.mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "scripts")))

import room_claim  # noqa: E402
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


class FakePreflight:
    """The preflight seam: records each ``cwd`` and returns a scripted
    ``(ok, failure)``, so no test starts a real harness session."""

    def __init__(self, result=(True, None)):
        self.result = result
        self.calls = []

    def __call__(self, cwd):
        self.calls.append(cwd)
        return self.result


def waiting(comment_id=10, to="author-a", opener="other"):
    """A task addressed to ``to`` and waiting for its turn."""
    return msg_comment(comment_id, opener, text="please look",
                       state="input-required", round=1, to=to)


def own_task_reply(comment_id=10, agent="rev-b", other="other"):
    """A task ``agent`` opened, answered by ``other`` and waiting on ``agent``."""
    return [msg_comment(comment_id, agent, text="finding",
                        state="input-required", round=1, to=other),
            msg_comment(comment_id + 1, other, task_id=comment_id,
                        text="fixed", state="input-required", round=2,
                        to=agent)]


class RunTestBase(RoomTestBase):
    def run_verb(self, gh, *argv, runner=None, clock=None, sleep=None,
                 env=None, preflight=None):
        seams = {"sleep": sleep or FakeSleep(),
                 "clock": clock or FakeClock(),
                 "runner": runner or FakeRunner(),
                 "preflight": preflight or FakePreflight()}
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

    def test_start_line_names_github_token(self):
        secret = "fake-token-value-run"
        gh = FakeGh(login="rev", pr_author="mikkel")
        env = {k: "" for k in ("GH_TOKEN", "GH_ENTERPRISE_TOKEN",
                               "GITHUB_ENTERPRISE_TOKEN", "GH_CONFIG_DIR",
                               "GH_HOST")}
        env["GITHUB_TOKEN"] = secret
        code, out, err = self.run_verb(
            gh, "7", "--role", "reviewer", "--agent", "rev-b", env=env,
            preflight=FakePreflight((False, "stop here")))
        self.assertIn("room run: acting as @rev (GITHUB_TOKEN)", err)
        self.assertNotIn(secret, out + err)

    def test_signed_out_harness_stops_before_joining(self):
        gh = FakeGh(login="rev", pr_author="mikkel")
        runner = FakeRunner()
        preflight = FakePreflight((False, "session CLI exited 1: Failed to "
                                   "authenticate: OAuth session expired"))
        code, out, err = self.run_verb(
            gh, "7", "--role", "reviewer", "--agent", "rev-b",
            runner=runner, preflight=preflight)
        self.assertEqual(code, 1, err)
        self.assertEqual(out, "")
        self.assertEqual(err.count("Error:"), 1, err)
        self.assertIn("claude auth login", err)
        self.assertEqual(len(preflight.calls), 1)
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


class RunClaimTest(RunTestBase):
    """room-review-claim, room-review-claim-permission,
    room-review-claim-cleanup in PR mode"""

    HEAD = "d" * 40
    ARGV = ("7", "--role", "reviewer", "--agent", "rev-b")

    def gh(self, **kwargs):
        kwargs.setdefault("login", "rev")
        kwargs.setdefault("pr_author", "mikkel")
        kwargs.setdefault("head", self.HEAD)
        return FakeGh(**kwargs)

    def prefix(self):
        return room_claim.claim_prefix(7, "rev-b", self.HEAD)

    def test_a_won_claim_runs_the_turn_and_releases_it(self):
        gh = self.gh(comments=[waiting(to="rev-b")])
        runner = FakeRunner()
        code, out, err = self.run_verb(
            gh, *self.ARGV, "--max-turns", "1", runner=runner)
        self.assertEqual(code, 0, err)
        self.assertEqual(len(runner.calls), 1)
        self.assertEqual(self.summary(out)["turns"], 1)
        self.assertEqual(gh.claims.status_states()[0],
                         ("room-review/rev-b", "pending"))
        self.assertEqual(gh.claims.tip_info(self.prefix() + "/1")["state"],
                         "released")

    def test_a_held_claim_runs_no_turn_and_watches_from_the_same_cursor(self):
        gh = self.gh(comments=[waiting(to="rev-b")])
        gh.claims.seed(7, "rev-b", self.HEAD, 1, "other:1:abcd", "beat",
                       age=10)
        runner = FakeRunner()
        sleep = FakeSleep()
        code, out, err = self.run_verb(
            gh, *self.ARGV, "--budget", "100", "--interval", "5",
            runner=runner, clock=FakeClock(step=10), sleep=sleep)
        self.assertEqual(code, 0, err)
        self.assertEqual(runner.calls, [])
        self.assertIn("is claimed by other:1:abcd; skipping", err)
        self.assertIn(5, sleep.calls)
        summary = self.summary(out)
        self.assertEqual(summary["turns"], 0)
        self.assertEqual(summary["cursor"], "0:0")

    def test_a_done_claim_advances_the_cursor_without_a_turn(self):
        gh = self.gh(comments=[waiting(to="rev-b")])
        gh.claims.seed(7, "rev-b", self.HEAD, 1, "other", "done")
        runner = FakeRunner()
        code, out, err = self.run_verb(
            gh, *self.ARGV, "--budget", "100", "--interval", "5",
            runner=runner, clock=FakeClock(step=10))
        self.assertEqual(runner.calls, [])
        summary = self.summary(out)
        self.assertEqual(summary["turns"], 0)
        self.assertNotEqual(summary["cursor"], "0:0")

    def test_a_turn_on_the_agents_own_task_runs_without_a_claim(self):
        gh = self.gh(comments=own_task_reply())
        gh.claims.seed(7, "rev-b", self.HEAD, 1, "other", "done")
        runner = FakeRunner()
        code, out, err = self.run_verb(
            gh, *self.ARGV, "--max-turns", "1", runner=runner)
        self.assertEqual(code, 0, err)
        self.assertEqual(len(runner.calls), 1)
        self.assertEqual(gh.claims.writes(), [])
        self.assertEqual(gh.claims.statuses, [])

    def test_no_push_permission_refuses_a_reviewer_before_joining(self):
        gh = self.gh(comments=[waiting(to="rev-b")])
        gh.claims.push = False
        runner = FakeRunner()
        code, out, err = self.run_verb(gh, *self.ARGV, runner=runner)
        self.assertEqual(code, 1, err)
        self.assertEqual(out, "")
        errors = [l for l in err.splitlines() if l.startswith("Error:")]
        self.assertEqual(len(errors), 1, err)
        self.assertIn("@rev", errors[0])
        self.assertIn("o/r", errors[0])
        self.assertEqual(gh.posts(), [])
        self.assertEqual(runner.calls, [])

    def test_no_push_permission_refuses_a_ci_run_too(self):
        gh = self.gh()
        gh.claims.push = False
        code, out, err = self.run_verb(
            gh, "7", "--role", "ci", "--agent", "ci-a")
        self.assertEqual(code, 1, err)
        self.assertEqual(gh.posts(), [])

    def test_an_author_run_is_not_refused_for_permission(self):
        gh = self.gh(state="MERGED", login="mikkel")
        gh.claims.push = False
        code, out, err = self.run_verb(
            gh, "7", "--role", "author", "--agent", "author-a")
        self.assertEqual(code, 0, err)
        self.assertNotIn("push permission", err)

    def test_an_author_turn_makes_no_claim_call(self):
        gh = self.gh(comments=[waiting(to="author-a")], login="mikkel")
        code, out, err = self.run_verb(
            gh, "7", "--role", "author", "--agent", "author-a",
            "--max-turns", "1")
        self.assertEqual(code, 0, err)
        self.assertEqual(gh.claims.writes(), [])

    def test_a_closed_room_deletes_the_claim_refs_of_the_pr(self):
        gh = self.gh(state="MERGED")
        gh.claims.seed(7, "rev-b", self.HEAD, 1, "x", "done")
        gh.claims.seed(7, "rev-b", self.HEAD, 2, "x", "released")
        gh.claims.seed(9, "rev-b", "e" * 40, 1, "x", "done")
        code, out, err = self.run_verb(gh, *self.ARGV)
        self.assertEqual(code, 0, err)
        self.assertEqual(self.summary(out)["reason"], "closed")
        self.assertEqual(gh.claims.under("shipd/claims/pr-7/"), [])
        self.assertEqual(len(gh.claims.under("shipd/claims/pr-9/")), 1)

    def test_a_failed_claim_delete_warns_and_the_run_still_ends(self):
        gh = self.gh(state="MERGED")
        gh.claims.seed(7, "rev-b", self.HEAD, 1, "x", "done")
        gh.claims.fail.append([["DELETE"], "HTTP 403"])
        code, out, err = self.run_verb(gh, *self.ARGV)
        self.assertEqual(code, 0, err)
        self.assertIn("warning:", err)


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
                seams={"sleep": FakeSleep(), "clock": FakeClock(),
                       "preflight": FakePreflight()})
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
                   "runner": runner, "preflight": FakePreflight()})
        self.assertEqual(code, 1, err)
        summary = self.summary(out)
        self.assertEqual(summary["reason"], "watch-failed")
        self.assertIn("boom", summary["failure"])
        self.assertEqual(err.count("Error:"), 1, err)
        self.assertEqual(runner.calls, [])


def request_posts(gh):
    """The parsed Messages posted with no task id, i.e. the tasks the run
    opened, in order."""
    out = []
    for body in gh.posts():
        parsed = first_marker(body)
        if getattr(parsed, "task_id", 0) is None and \
                getattr(parsed, "metadata", None) is not None:
            out.append(parsed)
    return out


class RunRequestReviewTest(RunTestBase):
    ARGV = ("7", "--role", "author", "--agent", "author-a")

    def test_kick_off_opens_one_review_task(self):
        gh = FakeGh(head="abc1234def", state="MERGED")
        code, out, err = self.run_verb(
            gh, *self.ARGV, "--request-review", "reviewer-b")
        self.assertEqual(code, 0, err)
        posts = gh.posts()
        self.assertEqual(len(posts), 2, posts)
        task = first_marker(posts[1])
        self.assertIsNone(task.task_id)
        self.assertEqual(task.to, "reviewer-b")
        self.assertEqual(task.skill, "review-finding")
        self.assertEqual(task.state, "input-required")
        self.assertEqual(task.metadata["head"], "abc1234def")
        self.summary(out)

    def test_an_existing_request_is_not_repeated(self):
        gh = FakeGh(
            comments=[msg_comment(10, "author-a", text="review please",
                                  state="input-required", round=1,
                                  to="reviewer-b")],
            head="abc1234def", state="MERGED")
        code, out, err = self.run_verb(
            gh, *self.ARGV, "--request-review", "reviewer-b")
        self.assertEqual(code, 0, err)
        self.assertEqual(len(gh.posts()), 1)

    def test_a_repeated_name_opens_one_task(self):
        gh = FakeGh(head="abc1234def", state="MERGED")
        code, out, err = self.run_verb(
            gh, *self.ARGV, "--request-review", "reviewer-b",
            "--request-review", "reviewer-b")
        self.assertEqual(code, 0, err)
        self.assertEqual(len(request_posts(gh)), 1)

    def test_usage_errors_make_no_gh_call(self):
        gh = FakeGh()
        code, _out, _err = self.run_verb(
            gh, "7", "--role", "reviewer", "--agent", "rev-b",
            "--request-review", "x")
        self.assertEqual(code, 2)
        self.assertEqual(gh.calls, [])
        gh = FakeGh()
        code, _out, _err = self.run_verb(
            gh, *self.ARGV, "--request-review", "author-a")
        self.assertEqual(code, 2)
        self.assertEqual(gh.calls, [])


class RunRereviewTest(RunTestBase):
    ARGV = ("7", "--role", "author", "--agent", "author-a")

    def room_comments(self):
        return [card_comment(5, "reviewer-b", role="reviewer"),
                waiting(10, to="author-a", opener="reviewer-b")]

    def moving_hook(self, gh, head="bbb2222", close=True):
        def hook(_n):
            if head:
                gh.head = head
            if close:
                gh.state = "MERGED"
        return hook

    def test_a_moved_head_opens_one_re_review(self):
        gh = FakeGh(comments=self.room_comments(), head="aaa1111")
        runner = FakeRunner(hook=self.moving_hook(gh))
        code, out, err = self.run_verb(gh, *self.ARGV, runner=runner)
        self.assertEqual(code, 0, err)
        posts = request_posts(gh)
        self.assertEqual(len(posts), 1, gh.posts())
        self.assertEqual(posts[0].agent, "author-a")
        self.assertEqual(posts[0].to, "reviewer-b")
        self.assertEqual(posts[0].skill, "review-finding")
        self.assertEqual(posts[0].metadata["head"], "bbb2222")
        self.assertIn("re-review requested from reviewer-b", err)

    def test_an_existing_request_at_the_new_head_opens_none(self):
        comments = self.room_comments() + [
            msg_comment(11, "author-a", text="again",
                        state="input-required", round=1, to="reviewer-b",
                        skill="review-finding", head="bbb2222")]
        gh = FakeGh(comments=comments, head="aaa1111")
        runner = FakeRunner(hook=self.moving_hook(gh))
        code, out, err = self.run_verb(gh, *self.ARGV, runner=runner)
        self.assertEqual(code, 0, err)
        self.assertEqual(request_posts(gh), [])

    def test_an_unmoved_head_opens_none(self):
        gh = FakeGh(comments=self.room_comments(), head="aaa1111")
        runner = FakeRunner(hook=self.moving_hook(gh, head=None))
        code, out, err = self.run_verb(gh, *self.ARGV, runner=runner)
        self.assertEqual(code, 0, err)
        self.assertEqual(request_posts(gh), [])

    def test_a_reviewer_run_opens_none(self):
        gh = FakeGh(comments=[waiting(10, to="reviewer-b")], login="rev",
                    pr_author="mikkel", head="aaa1111")
        runner = FakeRunner(hook=self.moving_hook(gh))
        code, out, err = self.run_verb(
            gh, "7", "--role", "reviewer", "--agent", "reviewer-b",
            runner=runner)
        self.assertEqual(code, 0, err)
        self.assertEqual(request_posts(gh), [])

    def test_an_unreadable_head_warns_and_the_run_still_ends(self):
        gh = FakeGh(comments=self.room_comments(), head="aaa1111")
        real = gh.__call__

        def flaky(args, input=None):
            if args[:2] == ["pr", "view"] and any(
                    "headRefOid" in a for a in args):
                return 1, "", "boom"
            return real(args, input=input)

        flaky.posts = gh.posts
        runner = FakeRunner(hook=self.moving_hook(gh, head=None))
        code, out, err = _run(
            ["run"] + list(self.ARGV) + ["--root", self.root], flaky,
            seams={"sleep": FakeSleep(), "clock": FakeClock(),
                   "runner": runner, "preflight": FakePreflight()})
        self.assertEqual(code, 0, err)
        self.assertIn("warning: could not read the head", err)
        self.assertEqual(request_posts(gh), [])
        self.assertEqual(self.summary(out)["reason"], "closed")

    def test_a_failed_re_review_post_warns_and_the_run_still_ends(self):
        gh = FakeGh(comments=self.room_comments(), head="aaa1111")
        real = gh.__call__

        def failing(args, input=None):
            # Only the re-review POST fails: it is the one made after the
            # runner hook has moved the head.
            if "POST" in args and gh.head != "aaa1111":
                return 1, "", "boom"
            return real(args, input=input)

        failing.posts = gh.posts
        runner = FakeRunner(hook=self.moving_hook(gh))
        code, out, err = _run(
            ["run"] + list(self.ARGV) + ["--root", self.root], failing,
            seams={"sleep": FakeSleep(), "clock": FakeClock(),
                   "runner": runner, "preflight": FakePreflight()})
        self.assertEqual(code, 0, err)
        self.assertIn("warning: re-review request failed", err)
        self.assertEqual(len(out.strip().splitlines()), 1, out)
        self.assertEqual(self.summary(out)["reason"], "closed")


MARKER = "<!-- shipd-verdict: fix-required -->"


def ci_review(review_id, commit="aaa1111", login="github-actions[bot]",
              body=None):
    """A pull request review as the reviews endpoint serves it."""
    return {"id": review_id, "user": {"login": login}, "commit_id": commit,
            "body": "## Findings: Fix required\n" + MARKER if body is None
            else body,
            "html_url": "%s#pullrequestreview-%d" % (URL, review_id)}


def reviews_reads(gh):
    return [a for a, _i in gh.calls if any(
        x.endswith("/pulls/7/reviews") for x in a)]


class RunCiReviewTest(RunTestBase):
    ARGV = ("7", "--role", "author", "--agent", "author-a")

    def run_ci(self, gh, *extra, runner=None, step=10, argv=None):
        return self.run_verb(
            gh, *(argv or self.ARGV), "--budget", "100", "--interval", "5",
            *extra, runner=runner or FakeRunner(),
            clock=FakeClock(step=step))

    def test_a_fix_required_review_of_the_head_runs_one_turn(self):
        gh = FakeGh(head="aaa1111", reviews=[ci_review(31)])
        runner = FakeRunner()
        code, out, err = self.run_ci(gh, runner=runner)
        self.assertEqual(code, 0, err)
        self.assertEqual(len(runner.calls), 1)
        prompt = runner.calls[0][0]
        self.assertIn("@github-actions[bot]", prompt)
        self.assertIn(URL, prompt)
        self.assertIn("aaa1111", prompt)
        self.assertIn("%s#pullrequestreview-31" % URL, prompt)
        self.assertIn("room run: turn 1 on CI review 31 by "
                      "github-actions[bot]", err)
        self.assertNotIn("no actionable task", err)
        summary = self.summary(out)
        self.assertEqual(summary["turns"], 1)
        self.assertEqual(summary["reason"], "budget")

    BRANDED = "**\u2615 shipd** semantic review\n\n"

    def test_a_branded_fix_required_review_runs_one_turn(self):
        body = (self.BRANDED + "## Findings: \u274c Fix required\n\nBad.\n\n"
                + MARKER + "\n")
        gh = FakeGh(head="aaa1111", reviews=[ci_review(41, body=body)])
        runner = FakeRunner()
        code, _out, err = self.run_ci(gh, runner=runner)
        self.assertEqual(code, 0, err)
        self.assertEqual(len(runner.calls), 1)
        self.assertIn("%s#pullrequestreview-41" % URL, runner.calls[0][0])

    def test_a_branded_ship_it_review_runs_no_turn(self):
        body = (self.BRANDED + "## Findings: \u2705 Ship it\n\n"
                "No problems found.\n\n"
                "<!-- shipd-verdict: ship-it -->\n")
        gh = FakeGh(head="aaa1111", reviews=[ci_review(42, body=body)])
        runner = FakeRunner()
        code, _out, err = self.run_ci(gh, runner=runner)
        self.assertEqual(code, 0, err)
        self.assertEqual(runner.calls, [])

    def test_other_reviews_run_no_turn(self):
        gh = FakeGh(head="aaa1111", reviews=[
            ci_review(1, body="Ship it"),
            ci_review(2, commit="old0000"),
            ci_review(3, login="someone-else")])
        runner = FakeRunner()
        code, out, err = self.run_ci(gh, runner=runner)
        self.assertEqual(code, 0, err)
        self.assertEqual(runner.calls, [])

    def test_a_quoted_marker_on_a_ship_it_review_runs_no_turn(self):
        body = ("## Findings: Ship it\nThe run matches `%s` in prose.\n"
                "<!-- shipd-verdict: ship-it -->\nReviewed 3 files." % MARKER)
        gh = FakeGh(head="aaa1111", reviews=[ci_review(5, body=body)])
        runner = FakeRunner()
        code, out, err = self.run_ci(gh, runner=runner)
        self.assertEqual(code, 0, err)
        self.assertEqual(runner.calls, [])

    def test_the_verdict_line_may_precede_a_footer(self):
        body = "## Findings: Fix required\n%s  \nReviewed 3 files." % MARKER
        gh = FakeGh(head="aaa1111", reviews=[ci_review(6, body=body)])
        runner = FakeRunner()
        self.run_ci(gh, runner=runner)
        self.assertEqual(len(runner.calls), 1)

    def test_the_login_matches_ignoring_case(self):
        gh = FakeGh(head="aaa1111",
                    reviews=[ci_review(4, login="GitHub-Actions[bot]")])
        runner = FakeRunner()
        self.run_ci(gh, runner=runner)
        self.assertEqual(len(runner.calls), 1)

    def test_a_review_is_handled_once(self):
        gh = FakeGh(head="aaa1111", reviews=[ci_review(31), ci_review(32)])
        runner = FakeRunner()
        code, out, err = self.run_ci(gh, runner=runner)
        self.assertEqual(code, 0, err)
        self.assertEqual(len(runner.calls), 1)
        self.assertIn("CI review 32", err)
        self.assertGreater(len(reviews_reads(gh)), 1)

    def test_a_pushed_fix_requests_a_re_review(self):
        gh = FakeGh(head="aaa1111", reviews=[ci_review(31)])

        def hook(_n):
            gh.head = "bbb2222"
            gh.state = "MERGED"

        runner = FakeRunner(hook=hook)
        code, out, err = self.run_ci(
            gh, "--request-review", "reviewer-b", runner=runner)
        self.assertEqual(code, 0, err)
        tasks = [t for t in request_posts(gh) if t.metadata.get("head")
                 == "bbb2222"]
        self.assertEqual(len(tasks), 1, gh.posts())
        self.assertEqual(tasks[0].to, "reviewer-b")

    def test_the_turn_counts_toward_the_cap(self):
        gh = FakeGh(head="aaa1111", reviews=[ci_review(31)])
        runner = FakeRunner()
        code, out, err = self.run_ci(gh, "--max-turns", "1", runner=runner)
        self.assertEqual(code, 0, err)
        self.assertEqual(self.summary(out)["reason"], "turn-cap")

    def test_a_failed_reviews_read_warns_once_and_runs_no_turn(self):
        gh = FakeGh(head="aaa1111", reviews=[ci_review(31)])
        real = gh.__call__

        def flaky(args, input=None):
            if any(a.endswith("/pulls/7/reviews") for a in args):
                return 1, "", "boom"
            return real(args, input=input)

        flaky.posts = gh.posts
        runner = FakeRunner()
        code, out, err = self.run_verb(
            flaky, *self.ARGV, "--budget", "100", "--interval", "5",
            runner=runner, clock=FakeClock(step=10))
        self.assertEqual(code, 0, err)
        self.assertEqual(runner.calls, [])
        self.assertEqual(err.count("could not read the reviews"), 1, err)

    def test_slices_are_four_intervals(self):
        gh = FakeGh(head="aaa1111")
        timeouts = []
        real = room_run.room.cmd_watch

        def spy(ns, *rest):
            timeouts.append(ns.timeout)
            return real(ns, *rest)

        with unittest.mock.patch.object(room_run.room, "cmd_watch", spy):
            self.run_verb(gh, *self.ARGV, "--budget", "100",
                          "--interval", "5", clock=FakeClock(step=1))
        self.assertEqual(timeouts[0], 20)
        self.assertTrue(all(t <= 20 for t in timeouts), timeouts)
        self.assertGreater(len(timeouts), 1)

    def test_a_reviewer_run_never_reads_reviews(self):
        gh = FakeGh(head="aaa1111", reviews=[ci_review(31)], login="rev",
                    pr_author="mikkel")
        runner = FakeRunner()
        code, out, err = self.run_verb(
            gh, "7", "--role", "reviewer", "--agent", "rev-b",
            "--budget", "100", "--interval", "5", runner=runner,
            clock=FakeClock(step=10))
        self.assertEqual(code, 0, err)
        self.assertEqual(reviews_reads(gh), [])
        self.assertEqual(runner.calls, [])

    def test_an_empty_ci_reviewer_still_slices(self):
        gh = FakeGh(head="aaa1111", reviews=[ci_review(31)])
        timeouts = []
        real = room_run.room.cmd_watch

        def spy(ns, *rest):
            timeouts.append(ns.timeout)
            return real(ns, *rest)

        runner = FakeRunner()
        with unittest.mock.patch.object(room_run.room, "cmd_watch", spy):
            code, out, err = self.run_ci(gh, "--ci-reviewer", "",
                                         runner=runner)
        self.assertEqual(code, 0, err)
        self.assertEqual(reviews_reads(gh), [])
        self.assertEqual(runner.calls, [])
        self.assertGreater(len(timeouts), 1)
        self.assertTrue(all(t <= 20 for t in timeouts), timeouts)
        self.assertNotIn("no actionable task", err)
        self.assertEqual(self.summary(out)["reason"], "budget")


def head_moving_gh(gh, head="bbb2222", on_view=2):
    """Wrap ``gh`` so the fake head moves to ``head`` on the ``on_view``th
    state read -- a push made by someone else while the run watches."""
    real = gh.__call__
    seen = {"n": 0}

    def wrapped(args, input=None):
        if args[:2] == ["pr", "view"] and "state" in args:
            seen["n"] += 1
            if seen["n"] == on_view:
                gh.head = head
        return real(args, input=input)

    wrapped.posts = gh.posts
    return wrapped


class RunAnyPushRereviewTest(RunTestBase):
    ARGV = ("7", "--role", "author", "--agent", "author-a")

    def at_head(self, gh, head="bbb2222"):
        return [t for t in request_posts(gh)
                if t.metadata.get("head") == head]

    def test_a_push_between_slices_opens_one_re_review(self):
        gh = FakeGh(head="aaa1111")
        runner = FakeRunner()
        code, out, err = self.run_verb(
            head_moving_gh(gh), *self.ARGV, "--request-review",
            "reviewer-b", "--budget", "100", "--interval", "5",
            runner=runner, clock=FakeClock(step=10))
        self.assertEqual(code, 0, err)
        self.assertEqual(runner.calls, [])
        tasks = self.at_head(gh)
        self.assertEqual(len(tasks), 1, gh.posts())
        self.assertEqual(tasks[0].to, "reviewer-b")
        self.assertEqual(tasks[0].skill, "review-finding")
        self.assertEqual(len(request_posts(gh)), 2, gh.posts())
        self.assertIn("re-review requested from reviewer-b at bbb2222", err)

    def test_a_push_with_an_empty_ci_reviewer_opens_one_re_review(self):
        gh = FakeGh(head="aaa1111")
        code, out, err = self.run_verb(
            head_moving_gh(gh), *self.ARGV, "--request-review",
            "reviewer-b", "--ci-reviewer", "", "--budget", "100",
            "--interval", "5", clock=FakeClock(step=10))
        self.assertEqual(code, 0, err)
        self.assertEqual(len(self.at_head(gh)), 1, gh.posts())

    def test_the_authors_own_push_is_requested_once(self):
        gh = FakeGh(comments=[card_comment(5, "reviewer-b", role="reviewer"),
                              waiting(10, to="author-a",
                                      opener="reviewer-b")],
                    head="aaa1111")

        def hook(_n):
            gh.head = "bbb2222"

        runner = FakeRunner(hook=hook)
        code, out, err = self.run_verb(
            gh, *self.ARGV, "--budget", "100", "--interval", "5",
            runner=runner, clock=FakeClock(step=10))
        self.assertEqual(code, 0, err)
        self.assertEqual(len(runner.calls), 1)
        tasks = self.at_head(gh)
        self.assertEqual(len(tasks), 1, gh.posts())
        self.assertEqual(tasks[0].to, "reviewer-b")
        self.assertEqual(self.summary(out)["reason"], "budget")

    def test_an_unreadable_start_head_opens_nothing(self):
        gh = FakeGh(head="aaa1111")
        real = head_moving_gh(gh)
        reads = {"n": 0}

        def flaky(args, input=None):
            if args[:2] == ["pr", "view"] and any(
                    "headRefOid" in a for a in args):
                reads["n"] += 1
                if reads["n"] == 1:
                    return 1, "", "boom"
            return real(args, input=input)

        flaky.posts = gh.posts
        code, out, err = self.run_verb(
            flaky, *self.ARGV, "--ci-reviewer", "", "--budget", "100",
            "--interval", "5", clock=FakeClock(step=10))
        self.assertEqual(code, 0, err)
        self.assertEqual(err.count("warning: could not read the head"), 1,
                         err)
        self.assertEqual(request_posts(gh), [])

    def test_a_reviewer_run_opens_nothing_on_a_push(self):
        gh = FakeGh(head="aaa1111", login="rev", pr_author="mikkel")
        runner = FakeRunner()
        code, out, err = self.run_verb(
            head_moving_gh(gh), "7", "--role", "reviewer", "--agent",
            "reviewer-b", "--budget", "100", "--interval", "5",
            runner=runner, clock=FakeClock(step=10))
        self.assertEqual(code, 0, err)
        self.assertEqual(request_posts(gh), [])
        self.assertEqual(runner.calls, [])


class RunMissingModuleTest(RunTestBase):
    def test_missing_room_run_fails_with_one_error_line(self):
        gh = FakeGh()
        with unittest.mock.patch.dict(sys.modules, {"room_run": None}):
            code, out, err = self.run_verb(gh, "7", "--role", "reviewer")
        self.assertEqual(code, 1, err)
        self.assertEqual(out, "")
        self.assertEqual(len(err.splitlines()), 1, err)
        self.assertTrue(err.startswith("Error:"), err)
        self.assertIn("room_run", err)
        self.assertIn("shipd room run", err)
        self.assertNotIn("Traceback", err)
        self.assertEqual(gh.calls, [])

    def test_missing_session_driver_fails_with_one_error_line(self):
        gh = FakeGh()
        with unittest.mock.patch.dict(sys.modules, {"session_driver": None}):
            sys.modules.pop("room_run", None)
            code, out, err = self.run_verb(gh, "7", "--role", "reviewer")
        self.assertEqual(code, 1, err)
        self.assertEqual(out, "")
        self.assertEqual(len(err.splitlines()), 1, err)
        self.assertTrue(err.startswith("Error:"), err)
        self.assertIn("session_driver", err)
        self.assertIn("shipd room run", err)
        self.assertNotIn("Traceback", err)
        self.assertEqual(gh.calls, [])

    def test_a_genuine_import_bug_in_room_run_propagates(self):
        import room
        saved_path = list(sys.path)
        saved_mod = sys.modules.pop("room_run", None)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                with open(os.path.join(tmp, "room_run.py"), "w") as fh:
                    fh.write("import shipd_no_such_module_xyz\n")
                sys.path.insert(0, tmp)
                with self.assertRaises(ModuleNotFoundError) as ctx:
                    room.main(["run", "7", "--role", "reviewer",
                               "--root", self.root], gh=FakeGh())
            self.assertEqual(ctx.exception.name, "shipd_no_such_module_xyz")
        finally:
            sys.path[:] = saved_path
            sys.modules.pop("room_run", None)
            if saved_mod is not None:
                sys.modules["room_run"] = saved_mod


class RunAgentLockTest(RunTestBase):
    """room-run-agent-lock"""

    def setUp(self):
        super().setUp()
        self.home = tempfile.mkdtemp(prefix="room-lock-home-")
        self.addCleanup(shutil.rmtree, self.home, True)
        self.lock_dir = os.path.join(self.home, ".shipd", "room-run", "o",
                                     "r")
        os.makedirs(self.lock_dir)

    def held(self, name, mode=fcntl.LOCK_EX):
        handle = open(os.path.join(self.lock_dir, name), "a")
        self.addCleanup(handle.close)
        fcntl.flock(handle, mode | fcntl.LOCK_NB)
        return handle.name

    def run_pr(self, gh, runner):
        return self.run_verb(gh, "7", "--role", "reviewer", "--agent",
                             "rev-b", runner=runner,
                             env={"HOME": self.home})

    def assert_refused(self, path):
        gh = FakeGh(comments=[waiting(to="rev-b")])
        runner = FakeRunner(hook=lambda n: setattr(gh, "state", "MERGED"))
        code, out, err = self.run_pr(gh, runner)
        self.assertEqual(code, 1, err)
        self.assertEqual(out, "")
        self.assertEqual(err.count("Error:"), 1, err)
        for part in ("rev-b", "o/r", path):
            self.assertIn(part, err)
        self.assertEqual(gh.posts(), [])
        self.assertEqual(runner.calls, [])

    def test_a_repo_runner_of_the_agent_refuses_a_pr_run(self):
        path = self.held("rev-b.json.lock")
        self.assert_refused(path)

    def test_a_pr_run_on_the_same_pr_is_refused(self):
        path = self.held("rev-b.pr-7.lock")
        self.assert_refused(path)

    def test_pr_runs_on_different_prs_coexist(self):
        self.held("rev-b.pr-8.lock")
        self.held("rev-b.json.lock", fcntl.LOCK_SH)
        gh = FakeGh(comments=[waiting(to="rev-b")], head="f" * 40)
        runner = FakeRunner(hook=lambda n: setattr(gh, "state", "MERGED"))
        code, out, err = self.run_pr(gh, runner)
        self.assertEqual(code, 0, err)
        self.assertEqual(len(runner.calls), 1)


if __name__ == "__main__":
    unittest.main()
