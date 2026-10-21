#!/usr/bin/env python3
"""Tests for ``shipd room run --repo`` (room_run_repo.py).

Every GitHub call goes through ``FakeRepoGh`` (one ``FakeGh`` per pull
request), every turn through a ``FakeRunner``, and the loop ends through a
``FakeSleep`` that raises ``KeyboardInterrupt``: no ``gh`` process, no
network, no real harness session, and no real sleeping.
"""

import fcntl
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import unittest.mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "scripts")))

import room_run_repo  # noqa: E402
from test_room import (  # noqa: E402
    FakeClock, FakeGh, FakeSleep, RoomTestBase, _run, msg_comment)
from test_room_run import (  # noqa: E402
    FakePreflight, FakeRunner, RunTestBase, waiting)

LOGIN = "rev-b-login"


class FakeRepoGh:
    """A ``gh`` seam over several pull requests: one ``FakeGh`` per number
    handles the per-PR calls, while ``pr list`` and ``api user`` are answered
    here. ``fail_next`` scripts failures by args prefix."""

    def __init__(self, login=LOGIN, repo="o/r"):
        self.login = login
        self.repo = repo
        self.fakes = {}
        self.listing = []
        self.calls = []
        self.failures = []
        self._stamp = 0

    def add_pr(self, number, comments=(), author="someone", state="OPEN",
               in_list=True):
        self.fakes[number] = FakeGh(
            number=number, repo=self.repo, comments=list(comments),
            login=self.login, pr_author=author, state=state)
        if in_list:
            self.listing.append({
                "number": number,
                "url": "https://github.com/%s/pull/%d" % (self.repo, number),
                "author": {"login": author},
                "updatedAt": "2026-01-01T00:00:%02dZ" % self._tick()})
        return self.fakes[number]

    def _tick(self):
        self._stamp += 1
        return self._stamp

    def touch(self, number, comment=None):
        """Add ``comment`` to PR ``number`` and bump its ``updatedAt``."""
        if comment is not None:
            self.fakes[number].comments.append(comment)
        for entry in self.listing:
            if entry["number"] == number:
                entry["updatedAt"] = "2026-01-01T00:01:%02dZ" % self._tick()

    def fail_next(self, prefix, stderr, times=1):
        self.failures.append([list(prefix), stderr, times])

    def reads(self, number):
        """How many times PR ``number``'s issue comments were read."""
        needle = "repos/%s/issues/%d/comments?per_page=100" % (
            self.repo, number)
        return sum(1 for args, _inp in self.fakes[number].calls
                   if needle in args and "-X" not in args)

    def __call__(self, args, input=None):
        args = list(args)
        self.calls.append((args, input))
        for failure in self.failures:
            prefix, stderr, times = failure
            if times > 0 and args[:len(prefix)] == prefix:
                failure[2] -= 1
                return 1, "", stderr
        if args[:2] == ["pr", "list"]:
            return 0, json.dumps(self.listing), ""
        if args == ["api", "user"]:
            return 0, json.dumps({"login": self.login}), ""
        if args[:2] == ["pr", "view"]:
            return self.fakes[int(args[2])](args, input)
        for arg in args:
            match = re.match(r"repos/[^/]+/[^/]+/(?:issues|pulls)/(\d+)/",
                             arg)
            if match:
                return self.fakes[int(match.group(1))](args, input)
        raise AssertionError("unexpected gh call: %r" % (args,))


class StopAfter(FakeSleep):
    """A ``FakeSleep`` that runs ``hooks[n]`` on the n-th sleep and raises
    ``KeyboardInterrupt`` on the ``limit``-th."""

    def __init__(self, limit, hooks=None):
        super().__init__()
        self.limit = limit
        self.hooks = hooks or {}

    def __call__(self, seconds):
        self.calls.append(seconds)
        hook = self.hooks.get(len(self.calls))
        if hook is not None:
            hook()
        if len(self.calls) >= self.limit:
            raise KeyboardInterrupt


class SeqPreflight:
    """A preflight returning scripted results in order, then the last."""

    def __init__(self, *results):
        self.results = list(results)
        self.calls = []

    def __call__(self, cwd):
        self.calls.append(cwd)
        if len(self.results) > 1:
            return self.results.pop(0)
        return self.results[0]


class RepoTestBase(RoomTestBase):
    def setUp(self):
        super().setUp()
        self.state_dir = tempfile.mkdtemp(prefix="room-state-")
        self.addCleanup(shutil.rmtree, self.state_dir, True)
        self.state = os.path.join(self.state_dir, "s.json")

    def run_repo(self, gh, *extra, limit=1, hooks=None, runner=None,
                 preflight=None, clock=None, sleep=None, argv=None,
                 env=None):
        self.sleep = sleep or StopAfter(limit, hooks)
        self.runner = runner or FakeRunner()
        self.preflight = preflight or FakePreflight()
        seams = {"sleep": self.sleep, "clock": clock or FakeClock(),
                 "runner": self.runner, "preflight": self.preflight}
        if argv is None:
            argv = ["run", "--repo", "o/r", "--role", "reviewer",
                    "--agent", "rev-b", "--state", self.state]
        return _run(list(argv) + list(extra) + ["--root", self.root], gh,
                    env=env, seams=seams)

    def summary(self, out):
        lines = out.splitlines()
        self.assertEqual(len(lines), 1, out)
        return json.loads(lines[0])

    def saved(self):
        with open(self.state) as handle:
            return json.load(handle)

    def write_state(self, prs):
        with open(self.state, "w") as handle:
            json.dump({"version": 1, "repo": "o/r", "agent": "rev-b",
                       "prs": prs}, handle)


class RepoModeTest(RepoTestBase):
    """room-run-repo-mode"""

    def test_repo_mode_needs_a_repository(self):
        gh = FakeRepoGh()
        code, out, err = self.run_repo(
            gh, argv=["run", "--role", "reviewer", "--agent", "rev-b"])
        self.assertEqual(code, 2, err)
        self.assertEqual(gh.calls, [])

    def test_repo_mode_refuses_the_author_role(self):
        gh = FakeRepoGh()
        code, out, err = self.run_repo(
            gh, argv=["run", "--repo", "o/r", "--role", "author",
                      "--agent", "a"])
        self.assertEqual(code, 2, err)
        self.assertEqual(gh.calls, [])

    def test_repo_mode_refuses_since(self):
        gh = FakeRepoGh()
        code, out, err = self.run_repo(gh, "--since", "5")
        self.assertEqual(code, 2, err)
        self.assertEqual(gh.calls, [])

    def test_repo_mode_refuses_request_review(self):
        gh = FakeRepoGh()
        code, out, err = self.run_repo(gh, "--request-review", "x")
        self.assertEqual(code, 2, err)
        self.assertEqual(gh.calls, [])

    def test_state_with_a_pr_is_a_usage_error(self):
        gh = FakeRepoGh()
        code, out, err = self.run_repo(
            gh, argv=["run", "7", "--repo", "o/r", "--role", "reviewer",
                      "--agent", "rev-b", "--state", self.state])
        self.assertEqual(code, 2, err)
        self.assertEqual(gh.calls, [])

    def test_unreadable_login_is_one_error(self):
        gh = FakeRepoGh()
        gh.fail_next(["api", "user"], "HTTP 401: Bad credentials", 5)
        code, out, err = self.run_repo(gh)
        self.assertEqual(code, 1, err)
        self.assertEqual(out, "")
        self.assertEqual(err.count("Error:"), 1, err)
        self.assertFalse(os.path.exists(self.state + ".lock"))

    def test_preflight_failure_stops_before_any_state_file(self):
        gh = FakeRepoGh()
        code, out, err = self.run_repo(
            gh, preflight=FakePreflight((False, "OAuth session expired")))
        self.assertEqual(code, 1, err)
        self.assertEqual(out, "")
        self.assertEqual(err.count("Error:"), 1, err)
        self.assertIn("claude auth login", err)
        self.assertFalse(os.path.exists(self.state))
        self.assertFalse(os.path.exists(self.state + ".lock"))
        self.assertEqual(self.runner.calls, [])

    def test_the_agent_env_is_set_for_the_turn(self):
        gh = FakeRepoGh()
        gh.add_pr(7, [waiting(10, to="rev-b")])
        self.run_repo(gh)
        self.assertEqual(self.runner.agents, ["rev-b"])


class ScriptEntryTest(RepoTestBase):
    """Run as a script, a room error is one ``Error:`` line, not a
    traceback (the lazily imported modules share ``room.RoomError``)."""

    def test_a_failing_gh_is_one_error_line(self):
        bindir = tempfile.mkdtemp(prefix="room-fake-gh-")
        self.addCleanup(shutil.rmtree, bindir, True)
        gh = os.path.join(bindir, "gh")
        with open(gh, "w") as handle:
            handle.write("#!/bin/sh\necho 'gh: boom' >&2\nexit 1\n")
        os.chmod(gh, 0o755)
        env = dict(os.environ)
        env["PATH"] = bindir + os.pathsep + env.get("PATH", "")
        env.pop("SHIPD_ROOM_AGENT", None)
        script = os.path.normpath(
            os.path.join(HERE, "..", "scripts", "room.py"))
        proc = subprocess.run(
            [sys.executable, "-B", script, "run", "--repo", "o/r",
             "--role", "reviewer", "--agent", "rb", "--state", self.state,
             "--root", self.root],
            env=env, capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)
        errors = [l for l in proc.stderr.splitlines()
                  if l.startswith("Error:")]
        self.assertEqual(len(errors), 1, proc.stderr)


class PerPrFormUnchangedTest(RunTestBase):
    def test_per_pr_form_still_ends_on_a_closed_pr(self):
        gh = FakeGh(login="rev", pr_author="mikkel", state="MERGED")
        code, out, err = self.run_verb(
            gh, "7", "--role", "reviewer", "--agent", "rev-b")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.summary(out)["reason"], "closed")


class RepoPollTest(RepoTestBase):
    """room-run-repo-poll"""

    def test_each_pr_gets_its_own_session(self):
        gh = FakeRepoGh()
        gh.add_pr(7, [waiting(10, to="rev-b")])
        gh.add_pr(9, [waiting(20, to="rev-b")])
        runner = FakeRunner([(True, None, "s-7"), (True, None, "s-9"),
                             (True, None, "s-7b")])
        code, out, err = self.run_repo(
            gh, limit=3, runner=runner,
            hooks={1: lambda: gh.touch(7, waiting(30, to="rev-b"))})
        self.assertEqual(code, 130, err)
        calls = runner.calls
        self.assertEqual(len(calls), 3, err)
        self.assertEqual(calls[0][2], None)
        self.assertIn("https://github.com/o/r/pull/7", calls[0][0])
        self.assertEqual(calls[1][2], None)
        self.assertIn("https://github.com/o/r/pull/9", calls[1][0])
        self.assertEqual(calls[2][2], "s-7")
        self.assertIn("https://github.com/o/r/pull/7", calls[2][0])
        self.assertTrue(calls[0][0].startswith("/s:room "))
        self.assertIn("role reviewer, skills review-finding, question, "
                      "status", calls[0][0])
        self.assertEqual(calls[0][1], self.root)

    def test_an_author_login_match_skips_the_pr(self):
        gh = FakeRepoGh(login=LOGIN)
        gh.add_pr(7, [waiting(10, to="rev-b")], author="REV-B-LOGIN")
        code, out, err = self.run_repo(gh, limit=3)
        self.assertEqual(code, 130, err)
        self.assertEqual(self.runner.calls, [])
        self.assertEqual(gh.fakes[7].posts(), [])
        self.assertEqual(gh.fakes[7].calls, [])
        self.assertEqual(err.count("#7"), 1, err)

    def test_a_pr_without_a_task_for_the_agent_costs_no_turn(self):
        gh = FakeRepoGh()
        gh.add_pr(7, [waiting(10, to="someone-else")])
        code, out, err = self.run_repo(gh, limit=2)
        self.assertEqual(self.runner.calls, [])
        self.assertEqual(gh.fakes[7].posts(), [])

    def test_an_unchanged_pr_is_not_re_read(self):
        gh = FakeRepoGh()
        gh.add_pr(7, [])
        self.run_repo(gh, limit=3)
        self.assertEqual(gh.reads(7), 1)

    def test_a_changed_pr_is_read_again(self):
        gh = FakeRepoGh()
        gh.add_pr(7, [])
        self.run_repo(gh, limit=3, hooks={1: lambda: gh.touch(7)})
        self.assertEqual(gh.reads(7), 2)

    def test_the_card_is_posted_once_per_process(self):
        gh = FakeRepoGh()
        gh.add_pr(7, [waiting(10, to="rev-b")])
        self.run_repo(
            gh, limit=3,
            hooks={1: lambda: gh.touch(7, waiting(30, to="rev-b"))})
        self.assertEqual(len(self.runner.calls), 2)
        cards = [c for c in gh.fakes[7].calls if "POST" in c[0]]
        self.assertEqual(len(cards), 1)
        self.assertEqual(gh.fakes[7].patches(), [])

    def test_the_pr_list_call_is_exact(self):
        gh = FakeRepoGh()
        self.run_repo(gh)
        listed = [a for a, _i in gh.calls if a[:2] == ["pr", "list"]]
        self.assertEqual(listed[0], [
            "pr", "list", "--repo", "o/r", "--state", "open", "--json",
            "number,url,author,updatedAt", "--limit", "100"])

    def test_prs_are_visited_in_ascending_number(self):
        gh = FakeRepoGh()
        gh.add_pr(9, [waiting(20, to="rev-b")])
        gh.add_pr(7, [waiting(10, to="rev-b")])
        self.run_repo(gh)
        self.assertIn("/pull/7", self.runner.calls[0][0])
        self.assertIn("/pull/9", self.runner.calls[1][0])


class RepoStateTest(RepoTestBase):
    """room-run-repo-state"""

    def test_a_restart_resumes_from_the_stored_cursor_and_session(self):
        gh = FakeRepoGh()
        gh.add_pr(7, [waiting(1003, to="rev-b")])
        self.write_state({"7": {"cursor": "1005:0", "session_id": "s-7"}})
        runner = FakeRunner([(True, None, "s-7b")])
        code, out, err = self.run_repo(
            gh, limit=3, runner=runner,
            hooks={1: lambda: gh.touch(7, waiting(1010, to="rev-b"))})
        self.assertEqual(code, 130, err)
        self.assertEqual(len(runner.calls), 1, err)
        self.assertEqual(runner.calls[0][2], "s-7")
        entry = self.saved()["prs"]["7"]
        self.assertEqual(entry["session_id"], "s-7b")
        self.assertEqual(entry["cursor"], "1010:0")

    def test_the_state_file_shape_and_atomic_write(self):
        gh = FakeRepoGh()
        gh.add_pr(7, [waiting(10, to="rev-b")])
        with unittest.mock.patch("os.replace",
                                 wraps=os.replace) as replace:
            self.run_repo(gh, runner=FakeRunner([(True, None, "s-7")]))
        self.assertTrue(replace.called)
        data = self.saved()
        self.assertEqual(data["version"], 1)
        self.assertEqual(data["repo"], "o/r")
        self.assertEqual(data["agent"], "rev-b")
        self.assertEqual(data["prs"]["7"]["session_id"], "s-7")
        self.assertEqual(data["prs"]["7"]["cursor"], "10:0")
        self.assertEqual(os.listdir(self.state_dir).count("s.json"), 1)
        self.assertEqual(
            [n for n in os.listdir(self.state_dir)
             if n not in ("s.json", "s.json.lock")], [])

    def test_a_closed_pr_is_pruned(self):
        gh = FakeRepoGh()
        gh.add_pr(7, [])
        self.write_state({"5": {"cursor": "1:0", "session_id": "s-5"},
                          "7": {"cursor": "1:0", "session_id": "s-7"}})
        self.run_repo(gh)
        self.assertEqual(sorted(self.saved()["prs"]), ["7"])

    def test_a_second_runner_is_refused(self):
        gh = FakeRepoGh()
        gh.add_pr(7, [waiting(10, to="rev-b")])
        with open(self.state + ".lock", "w") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            code, out, err = self.run_repo(gh)
        self.assertEqual(code, 1, err)
        self.assertEqual(out, "")
        self.assertEqual(err.count("Error:"), 1, err)
        self.assertIn(self.state, err)
        self.assertEqual(gh.fakes[7].posts(), [])
        self.assertEqual(self.runner.calls, [])

    def test_a_malformed_state_file_warns_and_starts_empty(self):
        gh = FakeRepoGh()
        gh.add_pr(7, [waiting(10, to="rev-b")])
        with open(self.state, "w") as handle:
            handle.write("{not json")
        code, out, err = self.run_repo(gh)
        self.assertEqual(code, 130, err)
        self.assertIn("warning", err)
        self.assertEqual(len(self.runner.calls), 1)

    def test_the_default_state_path(self):
        with unittest.mock.patch.dict(os.environ, {"HOME": "/h"}):
            self.assertEqual(
                room_run_repo.default_state_path("o/r", "rev-b"),
                "/h/.shipd/room-run/o/r/rev-b.json")


class RepoStopTest(RepoTestBase):
    """room-run-repo-stop"""

    def test_a_failed_turn_parks_only_its_pr(self):
        gh = FakeRepoGh()
        gh.add_pr(7, [waiting(10, to="rev-b")])
        gh.add_pr(9, [waiting(20, to="rev-b")])
        runner = FakeRunner([(False, "boom", None), (True, None, "s-9")])
        code, out, err = self.run_repo(
            gh, limit=3, runner=runner,
            hooks={1: lambda: gh.touch(7, waiting(30, to="rev-b"))})
        self.assertEqual(code, 130, err)
        self.assertEqual(len(runner.calls), 2, err)
        self.assertIn("/pull/9", runner.calls[1][0])
        self.assertIn("turn on #7 failed: boom; parked", err)
        self.assertEqual(len(self.preflight.calls), 2)

    def test_an_expired_sign_in_stops_the_run(self):
        gh = FakeRepoGh()
        gh.add_pr(7, [waiting(10, to="rev-b")])
        preflight = SeqPreflight((True, None), (False, "session expired"))
        runner = FakeRunner([(False, "auth failed", None)])
        code, out, err = self.run_repo(
            gh, limit=5, runner=runner, preflight=preflight)
        self.assertEqual(code, 1, err)
        summary = self.summary(out)
        self.assertEqual(summary["reason"], "preflight-failed")
        self.assertEqual(summary["mode"], "repo")
        self.assertIn("session expired", summary["failure"])
        self.assertEqual(err.count("Error:"), 1, err)
        self.assertIn("claude auth login", err)

    def test_a_rate_limit_backs_off(self):
        gh = FakeRepoGh()
        gh.add_pr(7, [])
        gh.fail_next(["pr", "list"], "API rate limit exceeded", 2)
        code, out, err = self.run_repo(
            gh, "--interval", "30", limit=3)
        self.assertEqual(self.sleep.calls, [60, 120, 30])
        self.assertIn("rate limit", err)

    def test_the_backoff_is_capped_at_900(self):
        gh = FakeRepoGh()
        gh.fail_next(["pr", "list"], "API rate limit exceeded", 20)
        self.run_repo(gh, "--interval", "30", limit=12)
        self.assertEqual(max(self.sleep.calls), 900)
        self.assertEqual(self.sleep.calls[:3], [60, 120, 240])

    def test_another_list_error_warns_and_retries(self):
        gh = FakeRepoGh()
        gh.add_pr(7, [waiting(10, to="rev-b")])
        gh.fail_next(["pr", "list"], "boom", 1)
        code, out, err = self.run_repo(
            gh, "--interval", "30", limit=2)
        self.assertEqual(self.sleep.calls, [30, 30])
        self.assertEqual(len(self.runner.calls), 1)
        self.assertIn("warning", err)

    def test_ctrl_c_prints_the_summary(self):
        gh = FakeRepoGh()
        gh.add_pr(7, [waiting(10, to="rev-b")])
        runner = FakeRunner([(True, None, "s-7")])
        code, out, err = self.run_repo(gh, runner=runner)
        self.assertEqual(code, 130, err)
        summary = self.summary(out)
        self.assertEqual(summary["mode"], "repo")
        self.assertEqual(summary["repo"], "o/r")
        self.assertEqual(summary["reason"], "interrupted")
        self.assertEqual(summary["turns"], 1)
        self.assertEqual(summary["prs"]["7"], {
            "turns": 1, "session_id": "s-7", "cursor": "10:0"})
        self.assertEqual(self.saved()["prs"]["7"]["cursor"], "10:0")

    def test_max_turns_parks_a_pr(self):
        gh = FakeRepoGh()
        gh.add_pr(7, [waiting(10, to="rev-b")])
        code, out, err = self.run_repo(
            gh, "--max-turns", "1", limit=4,
            hooks={1: lambda: gh.touch(7, waiting(30, to="rev-b"))})
        self.assertEqual(len(self.runner.calls), 1, err)
        self.assertIn("parked", err)

    def test_the_budget_stops_the_run_when_given(self):
        gh = FakeRepoGh()
        code, out, err = self.run_repo(
            gh, "--budget", "100", limit=10, clock=FakeClock(step=60))
        self.assertEqual(code, 0, err)
        self.assertEqual(self.summary(out)["reason"], "budget")

    def test_no_budget_by_default(self):
        gh = FakeRepoGh()
        code, out, err = self.run_repo(
            gh, limit=4, clock=FakeClock(step=1e6))
        self.assertEqual(code, 130, err)
        self.assertEqual(self.summary(out)["reason"], "interrupted")


class RepoAgentLockTest(RepoTestBase):
    """room-run-agent-lock"""

    def setUp(self):
        super().setUp()
        self.home = tempfile.mkdtemp(prefix="room-lock-home-")
        self.addCleanup(shutil.rmtree, self.home, True)
        lock_dir = os.path.join(self.home, ".shipd", "room-run", "o", "r")
        os.makedirs(lock_dir)
        self.agent_lock = os.path.join(lock_dir, "rev-b.json.lock")

    def assert_refused(self, mode):
        gh = FakeRepoGh()
        gh.add_pr(7, [waiting(10, to="rev-b")])
        with open(self.agent_lock, "a") as handle:
            fcntl.flock(handle, mode | fcntl.LOCK_NB)
            code, out, err = self.run_repo(gh, env={"HOME": self.home})
        self.assertEqual(code, 1, err)
        self.assertEqual(out, "")
        self.assertEqual(err.count("Error:"), 1, err)
        for part in ("rev-b", "o/r", self.agent_lock):
            self.assertIn(part, err)
        self.assertEqual(gh.fakes[7].posts(), [])
        self.assertEqual(self.runner.calls, [])
        self.assertFalse(os.path.exists(self.state + ".lock"))

    def test_a_custom_state_file_does_not_escape_the_agent_lock(self):
        self.assert_refused(fcntl.LOCK_EX)

    def test_a_pr_run_of_the_agent_refuses_repo_mode(self):
        self.assert_refused(fcntl.LOCK_SH)


if __name__ == "__main__":
    unittest.main()
