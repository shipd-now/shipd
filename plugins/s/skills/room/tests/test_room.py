#!/usr/bin/env python3
"""Tests for room.py — the ``shipd room`` verbs over a PR's comment thread.

Every GitHub call goes through the injectable ``gh`` runner, so the suite
drives ``room.main(argv, gh=FakeGh(...))`` against a stateful fake: no ``gh``
process is spawned and no network is reached. ``HOME`` is pointed at an empty
directory and ``SHIPD_ROOM_AGENT`` is cleared for every run, so neither the
real home config nor the caller's environment leaks into a test.
"""

import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
import unittest.mock
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
sys.path.insert(0, SCRIPTS)

import room  # noqa: E402
import room_schema  # noqa: E402

MODULE_PATH = os.path.join(SCRIPTS, "room.py")
MANIFEST = os.path.normpath(
    os.path.join(HERE, "..", "..", "..", ".claude-plugin", "plugin.json"))
CONTEXT = "o/r#7"


class FakeGh:
    """A stateful fake of the ``gh`` CLI seam.

    Call signature mirrors the production runner: ``gh(args, input=None) ->
    (returncode, stdout, stderr)`` where ``args`` is everything after ``gh``.
    Issue comments and review comments are held separately and served as
    ``pages`` slurped page arrays; a POST appends an issue comment, a PATCH
    replaces one's body. ``fail`` names an args prefix answered with
    ``(1, "", "boom")``.
    """

    def __init__(self, number=7, repo="o/r", comments=None,
                 review_comments=None, pages=1, fail=None):
        self.number = number
        self.repo = repo
        self.comments = [dict(c) for c in (comments or [])]
        self.review_comments = [dict(c) for c in (review_comments or [])]
        self.pages = pages
        self.fail = list(fail) if fail is not None else None
        self.calls = []                 # list of (args, input)
        ids = [c["id"] for c in self.comments + self.review_comments]
        self._next_id = max(ids + [999]) + 1

    # -- helpers ------------------------------------------------------------

    def _slurp(self, items):
        """``items`` split into ``self.pages`` page arrays, as ``--slurp``
        returns a paginated listing."""
        count = max(1, self.pages)
        size = -(-len(items) // count) if items else 0
        pages = [items[i * size:(i + 1) * size] for i in range(count)] \
            if size else [[] for _ in range(count)]
        return json.dumps(pages)

    def posts(self):
        """The parsed bodies of every recorded POST, in order."""
        return [json.loads(inp)["body"] for args, inp in self.calls
                if "POST" in args]

    def patches(self):
        """``(comment_id, body)`` for every recorded PATCH, in order."""
        out = []
        for args, inp in self.calls:
            if "PATCH" in args:
                path = next(a for a in args if a.startswith("repos/"))
                out.append((int(path.rsplit("/", 1)[1]),
                            json.loads(inp)["body"]))
        return out

    # -- dispatch -----------------------------------------------------------

    def __call__(self, args, input=None):
        args = list(args)
        self.calls.append((args, input))
        if self.fail is not None and args[:len(self.fail)] == self.fail:
            return 1, "", "boom"
        if args[:2] == ["pr", "view"]:
            return 0, json.dumps({
                "number": self.number,
                "url": "https://github.com/%s/pull/%d" % (self.repo,
                                                          self.number)}), ""
        if args[:2] == ["repo", "view"]:
            return 0, json.dumps({"nameWithOwner": self.repo}), ""
        if args[0] != "api":
            raise AssertionError("unexpected gh call: %r" % (args,))
        issue_list = "repos/%s/issues/%d/comments?per_page=100" % (
            self.repo, self.number)
        review_list = "repos/%s/pulls/%d/comments?per_page=100" % (
            self.repo, self.number)
        if "-X" not in args:
            assert "--paginate" in args, args
            assert "--slurp" in args, args
            if issue_list in args:
                return 0, self._slurp(self.comments), ""
            if review_list in args:
                return 0, self._slurp(self.review_comments), ""
            raise AssertionError("unexpected gh api read: %r" % (args,))
        method = args[args.index("-X") + 1]
        payload = json.loads(input)
        if method == "POST":
            assert "repos/%s/issues/%d/comments" % (
                self.repo, self.number) in args, args
            comment = {
                "id": self._next_id,
                "user": {"login": "bot"},
                "body": payload["body"],
                "html_url": "https://github.com/%s/pull/%d#issuecomment-%d"
                            % (self.repo, self.number, self._next_id),
            }
            self._next_id += 1
            self.comments.append(comment)
            return 0, json.dumps(comment), ""
        if method == "PATCH":
            path = next(a for a in args if a.startswith("repos/"))
            comment_id = int(path.rsplit("/", 1)[1])
            for comment in self.comments:
                if comment["id"] == comment_id:
                    comment["body"] = payload["body"]
                    return 0, json.dumps(comment), ""
            return 1, "", "HTTP 404: Not Found"
        raise AssertionError("unexpected gh api method: %r" % (args,))


def _run(argv, gh, env=None):
    """Run ``room.main(argv, gh=gh)`` and return ``(code, stdout, stderr)``.

    ``HOME`` is an empty temp directory and ``SHIPD_ROOM_AGENT`` is unset
    unless ``env`` supplies it; a ``SystemExit`` (argparse usage) is caught
    and its code returned."""
    home = tempfile.mkdtemp(prefix="room-test-home-")
    try:
        environ = {k: v for k, v in os.environ.items()
                   if k != "SHIPD_ROOM_AGENT"}
        environ["HOME"] = home
        environ.update(env or {})
        out, err = io.StringIO(), io.StringIO()
        with unittest.mock.patch.dict(os.environ, environ, clear=True), \
                redirect_stdout(out), redirect_stderr(err):
            try:
                code = room.main(list(argv), gh=gh)
            except SystemExit as exc:
                code = exc.code if isinstance(exc.code, int) else 1
        return code, out.getvalue(), err.getvalue()
    finally:
        shutil.rmtree(home, ignore_errors=True)


def card_comment(comment_id, name, skills=(), harness="", version="",
                 description="", login="bot"):
    """An issue comment carrying an agent card marker."""
    card = room_schema.AgentCard(name=name, skills=tuple(skills),
                                 harness=harness, version=version,
                                 description=description)
    return {"id": comment_id, "user": {"login": login},
            "body": room_schema.render_comment(card),
            "html_url": "https://example/%d" % comment_id}


def msg_comment(comment_id, agent, text="hi", task_id=None, login="bot",
                **metadata):
    """An issue comment carrying a Message marker."""
    metadata.setdefault("state", "submitted")
    message = room_schema.Message(
        role="agent", parts=({"kind": "text", "text": text},),
        context_id=CONTEXT, agent=agent, task_id=task_id,
        metadata=metadata)
    return {"id": comment_id, "user": {"login": login},
            "body": room_schema.render_comment(message),
            "html_url": "https://example/%d" % comment_id}


def human_comment(comment_id, text, login="person"):
    return {"id": comment_id, "user": {"login": login}, "body": text,
            "html_url": "https://example/%d" % comment_id}


def first_marker(body):
    """The parsed object held by ``body``'s first-line marker."""
    first_line = body.splitlines()[0]
    return room_schema.parse_comment(first_line)


class RoomTestBase(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="room-test-root-")
        self.addCleanup(shutil.rmtree, self.root, True)

    def room(self, gh, *argv, env=None):
        """Run a verb with ``--root`` pinned to an empty temp dir."""
        return _run(list(argv) + ["--root", self.root], gh, env=env)


class GhSeamTest(RoomTestBase):
    """room-gh-seam: every GitHub call goes through the runner, comments are
    paged and flattened, and failures are one Error line."""

    def test_list_reads_every_slurped_page(self):
        gh = FakeGh(comments=[
            card_comment(100, "codex-a", harness="codex"),
            msg_comment(101, "codex-a", text="opener"),
            card_comment(102, "claude-b", harness="claude"),
            msg_comment(103, "claude-b", text="second opener"),
        ], pages=2)
        code, out, err = self.room(gh, "list", "7", "--agent", "codex-a")
        self.assertEqual(code, 0, err)
        self.assertIn("codex-a", out)
        self.assertIn("claude-b", out)
        self.assertIn("#101", out)
        self.assertIn("#103", out)
        reads = [args for args, _inp in gh.calls
                 if args[0] == "api" and "-X" not in args]
        self.assertEqual(len(reads), 2)
        for args in reads:
            self.assertIn("--paginate", args)
            self.assertIn("--slurp", args)

    def test_review_comments_join_the_union_ordered_by_id(self):
        # The gate's finding tasks live on review comments; a review comment
        # with a lower id than an issue comment still sorts first.
        gh = FakeGh(
            comments=[msg_comment(200, "claude-b", text="reply", task_id=50,
                                  state="working", round=2)],
            review_comments=[msg_comment(50, "gate", text="finding",
                                         state="input-required", round=1,
                                         to="claude-b")])
        code, out, err = self.room(gh, "list", "7", "--json",
                                   "--agent", "codex-a")
        self.assertEqual(code, 0, err)
        data = json.loads(out)
        self.assertEqual(len(data["tasks"]), 1)
        task = data["tasks"][0]
        self.assertEqual(task["id"], 50)
        self.assertEqual(task["messages"], 2)
        self.assertEqual(task["state"], "working")
        self.assertEqual(task["last_agent"], "claude-b")

    def test_failed_pr_view_is_one_error_line(self):
        gh = FakeGh(fail=["pr", "view"])
        code, out, err = self.room(gh, "list", "7", "--agent", "codex-a")
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        lines = err.splitlines()
        self.assertEqual(len(lines), 1, err)
        self.assertTrue(lines[0].startswith("Error: "), err)

    def test_missing_gh_binary_is_one_error_line(self):
        # The default runner reports an unrunnable gh as a failed call, not
        # a traceback (room-gh-seam).
        missing = FileNotFoundError(2, "No such file or directory", "gh")
        with unittest.mock.patch.object(room.subprocess, "run",
                                        side_effect=missing):
            code, out, err = self.room(None, "list", "7",
                                       "--agent", "codex-a")
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        lines = err.splitlines()
        self.assertEqual(len(lines), 1, err)
        self.assertTrue(lines[0].startswith("Error: "), err)
        self.assertIn("could not run gh", err)

    def test_malformed_marker_is_skipped_with_a_warning(self):
        gh = FakeGh(comments=[
            card_comment(100, "codex-a"),
            human_comment(101, "<!-- shipd-room {not json} -->\n\nbroken"),
            msg_comment(102, "codex-a", text="fine"),
        ])
        code, out, err = self.room(gh, "list", "7", "--agent", "codex-a")
        self.assertEqual(code, 0, err)
        self.assertIn("WARNING: comment 101:", err)
        self.assertIn("codex-a", out)
        self.assertIn("#102", out)
        self.assertNotIn("#101", out)

    def test_module_imports_only_stdlib_and_named_siblings(self):
        with open(MODULE_PATH, encoding="utf-8") as fh:
            source = fh.read()
        allowed = {"room_schema", "spec_common", "cli_common"}
        imported = set()
        for match in re.finditer(
                r"^\s*(?:import|from)\s+([A-Za-z_][\w]*)", source,
                re.MULTILINE):
            imported.add(match.group(1))
        for name in sorted(imported):
            self.assertTrue(
                name in allowed or name in sys.stdlib_module_names,
                "room.py imports non-stdlib module %r" % name)
        for name in sorted(allowed):
            self.assertIn(name, imported)


class JoinTest(RoomTestBase):
    """room-join-verb and room-agent-identity: the card upsert and the
    agent-name resolution order."""

    def _manifest_version(self):
        with open(MANIFEST, encoding="utf-8") as fh:
            return json.load(fh)["version"]

    def test_first_join_posts_the_card(self):
        gh = FakeGh()
        code, out, err = self.room(gh, "join", "7", "--agent", "codex-a",
                                   "--skill", "review-finding",
                                   "--harness", "codex")
        self.assertEqual(code, 0, err)
        posts = gh.posts()
        self.assertEqual(len(posts), 1)
        self.assertTrue(posts[0].splitlines()[0].startswith(
            "<!-- shipd-room-card "))
        card = first_marker(posts[0])
        self.assertIsInstance(card, room_schema.AgentCard)
        self.assertEqual(card.name, "codex-a")
        self.assertEqual(card.skills, ("review-finding",))
        self.assertEqual(card.harness, "codex")
        self.assertEqual(card.version, self._manifest_version())
        data = json.loads(out)
        self.assertEqual(data["agent"], "codex-a")
        self.assertEqual(data["comment"], gh.comments[-1]["id"])
        self.assertEqual(data["url"], gh.comments[-1]["html_url"])
        self.assertIn("joined %s as codex-a" % CONTEXT, err)

    def test_second_join_patches_the_same_comment(self):
        gh = FakeGh()
        self.room(gh, "join", "7", "--agent", "codex-a")
        card_id = gh.comments[-1]["id"]
        code, out, err = self.room(gh, "join", "7", "--agent", "codex-a",
                                   "--description", "x")
        self.assertEqual(code, 0, err)
        self.assertEqual(len(gh.posts()), 1)
        patches = gh.patches()
        self.assertEqual(len(patches), 1)
        self.assertEqual(patches[0][0], card_id)
        self.assertEqual(first_marker(patches[0][1]).description, "x")
        self.assertEqual(json.loads(out)["comment"], card_id)
        code, out, err = self.room(gh, "list", "7", "--json",
                                   "--agent", "codex-a")
        self.assertEqual(code, 0, err)
        self.assertEqual(len(json.loads(out)["cards"]), 1)

    def test_no_agent_name_is_a_usage_error(self):
        gh = FakeGh()
        code, out, err = self.room(gh, "join", "7")
        self.assertEqual(code, 2)
        self.assertIn("usage:", err)
        for source in ("--agent", "SHIPD_ROOM_AGENT", "room.agent"):
            self.assertIn(source, err)
        self.assertEqual(gh.calls, [])

    def test_environment_supplies_the_name(self):
        gh = FakeGh()
        code, _out, err = self.room(gh, "join", "7",
                                    env={"SHIPD_ROOM_AGENT": "codex-a"})
        self.assertEqual(code, 0, err)
        self.assertEqual(first_marker(gh.posts()[0]).name, "codex-a")

    def test_config_supplies_the_name(self):
        with open(os.path.join(self.root, ".shipd-config.json"), "w",
                  encoding="utf-8") as fh:
            json.dump({"room": {"agent": "claude-cfg"}}, fh)
        gh = FakeGh()
        code, _out, err = self.room(gh, "join", "7")
        self.assertEqual(code, 0, err)
        self.assertEqual(first_marker(gh.posts()[0]).name, "claude-cfg")

    def test_flag_beats_environment(self):
        gh = FakeGh()
        code, _out, err = self.room(gh, "join", "7", "--agent", "flag-a",
                                    env={"SHIPD_ROOM_AGENT": "env-a"})
        self.assertEqual(code, 0, err)
        self.assertEqual(first_marker(gh.posts()[0]).name, "flag-a")


class ListTest(RoomTestBase):
    """room-list-verb: the text and JSON reports."""

    def _room(self):
        return FakeGh(comments=[
            card_comment(100, "codex-a", skills=("review-finding",),
                         harness="codex", version="0.6.291"),
            card_comment(101, "claude-b", harness="claude"),
            msg_comment(102, "codex-a", text="please check",
                        state="input-required", round=1, to="claude-b"),
        ])

    def test_text_lists_cards_and_the_open_task(self):
        code, out, err = self.room(self._room(), "list", "7",
                                   "--agent", "codex-a")
        self.assertEqual(code, 0, err)
        lines = out.splitlines()
        self.assertEqual(lines[0], "room %s" % CONTEXT)
        self.assertIn("cards:", lines)
        self.assertIn("tasks:", lines)
        card_lines = [l for l in lines if l.strip().startswith(
            ("codex-a ", "claude-b "))]
        self.assertEqual(len(card_lines), 2, out)
        self.assertIn("harness codex", card_lines[0])
        self.assertIn("review-finding", card_lines[0])
        self.assertIn("0.6.291", card_lines[0])
        self.assertIn("#102  input-required  from codex-a  to claude-b  "
                      "round 1  last codex-a", out)

    def test_json_carries_cards_and_tasks(self):
        code, out, err = self.room(self._room(), "list", "7", "--json",
                                   "--agent", "codex-a")
        self.assertEqual(code, 0, err)
        data = json.loads(out)
        self.assertEqual(data["context"], CONTEXT)
        self.assertEqual([c["name"] for c in data["cards"]],
                         ["codex-a", "claude-b"])
        self.assertEqual(len(data["tasks"]), 1)
        task = data["tasks"][0]
        self.assertEqual(set(task), {"id", "state", "opener", "to", "round",
                                     "reason", "last_agent", "skill",
                                     "messages"})
        self.assertEqual(task["id"], 102)
        self.assertEqual(task["state"], "input-required")
        self.assertEqual(task["opener"], "codex-a")
        self.assertEqual(task["to"], "claude-b")
        self.assertEqual(task["round"], 1)
        self.assertEqual(task["last_agent"], "codex-a")
        self.assertEqual(task["messages"], 1)

    def test_skill_is_shown_when_set(self):
        gh = FakeGh(comments=[msg_comment(102, "codex-a", text="x",
                                          skill="review-finding")])
        code, out, err = self.room(gh, "list", "7", "--agent", "codex-a")
        self.assertEqual(code, 0, err)
        self.assertIn("to -  round 1  last codex-a  skill review-finding",
                      out)

    def test_human_comments_are_not_tasks(self):
        gh = FakeGh(comments=[human_comment(100, "looks good"),
                              human_comment(101, "ship it")])
        code, out, err = self.room(gh, "list", "7", "--agent", "codex-a")
        self.assertEqual(code, 0, err)
        lines = out.splitlines()
        self.assertEqual(lines, ["room %s" % CONTEXT, "cards:", "  (none)",
                                 "tasks:", "  (none)"])


def _joined(*extra):
    """Issue comments: cards for ``codex-a`` and ``claude-b``, then ``extra``."""
    return [card_comment(1, "codex-a"), card_comment(2, "claude-b")] + \
        list(extra)


class MessageTest(RoomTestBase):
    """room-message-verb: opening and advancing tasks, transitions, the cap."""

    def _open_task(self, state="input-required", round=1, agent="codex-a",
                   to="claude-b"):
        return msg_comment(10, agent, text="please check", state=state,
                           round=round, to=to)

    def _posted(self, gh):
        posts = gh.posts()
        self.assertEqual(len(posts), 1, posts)
        return first_marker(posts[0])

    def test_addressed_opener_starts_at_input_required(self):
        gh = FakeGh(comments=_joined())
        code, out, err = self.room(gh, "message", "7", "--new", "--to",
                                   "claude-b", "please check",
                                   "--agent", "codex-a")
        self.assertEqual(code, 0, err)
        msg = self._posted(gh)
        self.assertIsNone(msg.task_id)
        self.assertEqual(msg.agent, "codex-a")
        self.assertEqual(msg.role, "agent")
        self.assertEqual(msg.context_id, CONTEXT)
        self.assertEqual(msg.text, "please check")
        self.assertEqual(msg.metadata, {"round": 1, "state": "input-required",
                                        "to": "claude-b"})
        data = json.loads(out)
        self.assertEqual(data["task"], data["comment"])
        self.assertEqual(data["comment"], gh.comments[-1]["id"])
        self.assertEqual(data["state"], "input-required")
        self.assertEqual(data["round"], 1)
        self.assertEqual(data["url"], gh.comments[-1]["html_url"])

    def test_unaddressed_opener_is_submitted(self):
        gh = FakeGh(comments=_joined())
        code, _out, err = self.room(gh, "message", "7", "--new", "hello",
                                    "--agent", "codex-a")
        self.assertEqual(code, 0, err)
        self.assertEqual(self._posted(gh).metadata,
                         {"round": 1, "state": "submitted"})

    def test_opener_skill_is_recorded(self):
        gh = FakeGh(comments=_joined())
        code, _out, err = self.room(gh, "message", "7", "--new", "--skill",
                                    "review-finding", "hello",
                                    "--agent", "codex-a")
        self.assertEqual(code, 0, err)
        self.assertEqual(self._posted(gh).metadata["skill"],
                         "review-finding")

    def test_reply_advances_the_round_for_the_other_party(self):
        gh = FakeGh(comments=_joined(self._open_task()))
        code, out, err = self.room(gh, "message", "7", "--task", "10",
                                   "--to", "codex-a", "--state", "completed",
                                   "done", "--agent", "claude-b")
        self.assertEqual(code, 0, err)
        msg = self._posted(gh)
        self.assertEqual(msg.task_id, 10)
        self.assertEqual(msg.metadata, {"round": 2, "state": "completed",
                                        "to": "codex-a"})
        data = json.loads(out)
        self.assertEqual(data["task"], 10)
        self.assertEqual(data["round"], 2)

    def test_reply_without_state_or_to_is_working(self):
        gh = FakeGh(comments=_joined(self._open_task()))
        code, _out, err = self.room(gh, "message", "7", "--task", "10",
                                    "on it", "--agent", "claude-b")
        self.assertEqual(code, 0, err)
        self.assertEqual(self._posted(gh).metadata,
                         {"round": 2, "state": "working"})

    def test_reply_with_to_and_no_state_is_input_required(self):
        gh = FakeGh(comments=_joined(self._open_task()))
        code, _out, err = self.room(gh, "message", "7", "--task", "10",
                                    "--to", "codex-a", "question?",
                                    "--agent", "claude-b")
        self.assertEqual(code, 0, err)
        self.assertEqual(self._posted(gh).metadata,
                         {"round": 2, "state": "input-required",
                          "to": "codex-a"})

    def test_environment_supplies_the_posting_agent(self):
        gh = FakeGh(comments=_joined(self._open_task()))
        code, _out, err = self.room(gh, "message", "7", "--task", "10", "ok",
                                    env={"SHIPD_ROOM_AGENT": "claude-b"})
        self.assertEqual(code, 0, err)
        self.assertEqual(self._posted(gh).agent, "claude-b")

    def test_new_task_at_a_non_opening_state_names_the_opening_states(self):
        gh = FakeGh(comments=_joined())
        code, _out, err = self.room(gh, "message", "7", "--new", "--state",
                                    "working", "hi", "--agent", "codex-a")
        self.assertEqual(code, 1)
        self.assertEqual(gh.posts(), [])
        self.assertIn("Error: a new task opens at submitted or "
                      "input-required, not working", err)
        self.assertNotIn("None", err)

    def test_unknown_task_is_not_found(self):
        gh = FakeGh(comments=_joined(self._open_task()))
        code, _out, err = self.room(gh, "message", "7", "--task", "99", "x",
                                    "--agent", "claude-b")
        self.assertEqual(code, 1)
        self.assertEqual(gh.posts(), [])
        self.assertIn("Error: task 99 not found on %s" % CONTEXT, err)

    def test_terminal_task_refuses_a_reply(self):
        gh = FakeGh(comments=_joined(self._open_task(state="completed")))
        code, _out, err = self.room(gh, "message", "7", "--task", "10",
                                    "more", "--agent", "claude-b")
        self.assertEqual(code, 1)
        self.assertEqual(gh.posts(), [])
        self.assertIn("Error: task 10 is completed; no transition to "
                      "working", err)

    def test_terminal_task_fails_before_the_cap(self):
        gh = FakeGh(comments=_joined(self._open_task(state="completed",
                                                     round=6)))
        code, _out, err = self.room(gh, "message", "7", "--task", "10",
                                    "more", "--agent", "claude-b",
                                    "--max-rounds", "6")
        self.assertEqual(code, 1)
        self.assertEqual(gh.posts(), [])
        self.assertIn("no transition", err)

    def test_cap_posts_failed_and_exits_one(self):
        gh = FakeGh(comments=_joined(self._open_task(round=6)))
        code, out, err = self.room(gh, "message", "7", "--task", "10",
                                   "again", "--agent", "claude-b",
                                   "--max-rounds", "6")
        self.assertEqual(code, 1)
        msg = self._posted(gh)
        self.assertEqual(msg.task_id, 10)
        self.assertEqual(msg.metadata, {"reason": "round-cap", "round": 7,
                                        "state": "failed"})
        self.assertEqual(msg.text, "round cap (6) reached")
        self.assertIn("Error: round cap reached on task 10 — posted failed "
                      "(round-cap)", err)
        self.assertEqual(out, "")

    def test_cap_comes_from_config(self):
        with open(os.path.join(self.root, ".shipd-config.json"), "w",
                  encoding="utf-8") as fh:
            json.dump({"room": {"max_rounds": 1}}, fh)
        gh = FakeGh(comments=_joined(self._open_task(round=1)))
        code, _out, err = self.room(gh, "message", "7", "--task", "10",
                                    "again", "--agent", "claude-b")
        self.assertEqual(code, 1)
        self.assertEqual(self._posted(gh).metadata["reason"], "round-cap")

    def test_same_agent_keeps_the_round_under_the_cap(self):
        gh = FakeGh(comments=_joined(self._open_task(round=6)))
        code, _out, err = self.room(gh, "message", "7", "--task", "10",
                                    "follow-up", "--agent", "codex-a",
                                    "--max-rounds", "6")
        self.assertEqual(code, 0, err)
        self.assertEqual(self._posted(gh).metadata["round"], 6)

    def test_unjoined_agent_cannot_post(self):
        gh = FakeGh(comments=[card_comment(2, "claude-b")])
        code, _out, err = self.room(gh, "message", "7", "--new", "hi",
                                    "--agent", "codex-a")
        self.assertEqual(code, 1)
        self.assertEqual(gh.posts(), [])
        self.assertIn("Error: agent 'codex-a' has not joined %s — run shipd "
                      "room join" % CONTEXT, err)


class CloseTest(RoomTestBase):
    """room-close-verb: the terminal message, with no round cap."""

    def _room(self, state="input-required", round=1):
        return FakeGh(comments=_joined(msg_comment(
            10, "codex-a", text="please check", state=state, round=round,
            to="claude-b")))

    def test_default_close_completes(self):
        gh = self._room()
        code, out, err = self.room(gh, "close", "7", "--task", "10",
                                   "--agent", "claude-b")
        self.assertEqual(code, 0, err)
        posts = gh.posts()
        self.assertEqual(len(posts), 1)
        msg = first_marker(posts[0])
        self.assertEqual(msg.task_id, 10)
        self.assertEqual(msg.metadata, {"round": 2, "state": "completed"})
        self.assertNotIn("reason", msg.metadata)
        self.assertEqual(msg.text, "closed: completed")
        data = json.loads(out)
        self.assertEqual(data["task"], 10)
        self.assertEqual(data["state"], "completed")
        self.assertEqual(data["round"], 2)
        self.assertEqual(data["comment"], gh.comments[-1]["id"])

    def test_close_with_a_reason_at_the_cap_still_posts(self):
        gh = self._room(round=6)
        code, _out, err = self.room(gh, "close", "7", "--task", "10",
                                    "--state", "failed", "--reason",
                                    "stalled", "--agent", "claude-b",
                                    "--max-rounds", "6")
        self.assertEqual(code, 0, err)
        msg = first_marker(gh.posts()[0])
        self.assertEqual(msg.metadata, {"reason": "stalled", "round": 7,
                                        "state": "failed"})
        self.assertEqual(msg.text, "closed: failed — stalled")

    def test_close_on_a_canceled_task_has_no_transition(self):
        gh = self._room(state="canceled")
        code, _out, err = self.room(gh, "close", "7", "--task", "10",
                                    "--agent", "claude-b")
        self.assertEqual(code, 1)
        self.assertEqual(gh.posts(), [])
        self.assertIn("Error: task 10 is canceled; no transition to "
                      "completed", err)

    def test_unjoined_agent_cannot_close(self):
        gh = self._room()
        code, _out, err = self.room(gh, "close", "7", "--task", "10",
                                    "--agent", "stranger")
        self.assertEqual(code, 1)
        self.assertEqual(gh.posts(), [])
        self.assertIn("has not joined", err)
