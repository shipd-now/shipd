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
                 review_comments=None, pages=1, fail=None, state="OPEN",
                 delete_fail=False, login="bot", user_fail=False,
                 threads=None):
        self.threads = [dict(t) for t in (threads or [])]
        self.login = login
        self.user_fail = user_fail
        self.number = number
        self.state = state
        self.delete_fail = delete_fail
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

    def pr_views(self):
        """The args of every recorded ``gh pr view`` call."""
        return [a for a, _inp in self.calls if a[:2] == ["pr", "view"]]

    def repo_views(self):
        """The args of every recorded ``gh repo view`` call."""
        return [a for a, _inp in self.calls if a[:2] == ["repo", "view"]]

    def user_calls(self):
        """How many times ``gh api user`` was read."""
        return sum(1 for args, _inp in self.calls if args == ["api", "user"])

    def posts(self):
        """The parsed bodies of every recorded POST, in order."""
        return [json.loads(inp)["body"] for args, inp in self.calls
                if "POST" in args]

    def graphql_calls(self):
        """``(kind, variables)`` for every recorded ``gh api graphql`` call,
        ``kind`` being ``lookup`` or ``mutation``."""
        out = []
        for args, _inp in self.calls:
            if args[:2] == ["api", "graphql"]:
                fields = self._fields(args)
                kind = ("mutation" if "resolveReviewThread" in
                        fields.get("query", "") else "lookup")
                out.append((kind, fields))
        return out

    def mutations(self):
        """The ``threadId`` of every resolve mutation, in order."""
        return [f["threadId"] for kind, f in self.graphql_calls()
                if kind == "mutation"]

    @staticmethod
    def _fields(args):
        fields = {}
        for i, arg in enumerate(args):
            if arg in ("-f", "-F") and i + 1 < len(args):
                key, _, val = args[i + 1].partition("=")
                fields[key] = val
        return fields

    def issue_posts(self):
        """The bodies of every POST on the issues endpoint, in order."""
        return [json.loads(inp)["body"] for args, inp in self.calls
                if "POST" in args and any(
                    a.startswith("repos/") and "/issues/" in a
                    for a in args)]

    def review_posts(self):
        """``(in_reply_to, body)`` of every POST on the pulls endpoint."""
        out = []
        for args, inp in self.calls:
            if "POST" in args and any(
                    a.startswith("repos/") and "/pulls/" in a
                    for a in args):
                payload = json.loads(inp)
                out.append((payload.get("in_reply_to"), payload["body"]))
        return out

    def deletes(self):
        """The comment ids of every recorded DELETE, in order."""
        out = []
        for args, _inp in self.calls:
            if "DELETE" in args:
                path = next(a for a in args if a.startswith("repos/"))
                out.append(int(path.rsplit("/", 1)[1]))
        return out

    def delete_paths(self):
        """The API path of every recorded DELETE, in order."""
        return [next(a for a in args if a.startswith("repos/"))
                for args, _inp in self.calls if "DELETE" in args]

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
                "state": self.state,
                "url": "https://github.com/%s/pull/%d" % (self.repo,
                                                          self.number)}), ""
        if args[:2] == ["repo", "view"]:
            return 0, json.dumps({"nameWithOwner": self.repo}), ""
        if args[0] != "api":
            raise AssertionError("unexpected gh call: %r" % (args,))
        if args == ["api", "user"]:
            if self.user_fail:
                return 1, "", "HTTP 401: Bad credentials"
            return 0, json.dumps({"login": self.login}), ""
        if args[:2] == ["api", "graphql"]:
            fields = self._fields(args)
            if "resolveReviewThread" in fields.get("query", ""):
                for thread in self.threads:
                    if thread["id"] == fields.get("threadId"):
                        thread["isResolved"] = True
                        return 0, json.dumps({"data": {
                            "resolveReviewThread": {"thread": {
                                "isResolved": True}}}}), ""
                return 1, "", "no such thread"
            return 0, json.dumps({"data": {"repository": {"pullRequest": {
                "reviewThreads": {"nodes": self.threads}}}}}), ""
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
        if method == "DELETE":
            path = next(a for a in args if a.startswith("repos/"))
            comment_id = int(path.rsplit("/", 1)[1])
            if self.delete_fail:
                return 1, "", "HTTP 403: Forbidden"
            if "/pulls/comments/" in path:
                self.review_comments = [c for c in self.review_comments
                                        if c["id"] != comment_id]
            else:
                self.comments = [c for c in self.comments
                                 if c["id"] != comment_id]
            return 0, "", ""
        payload = json.loads(input)
        if method == "POST":
            review_path = "repos/%s/pulls/%d/comments" % (self.repo,
                                                          self.number)
            if review_path in args:
                comment = {
                    "id": self._next_id,
                    "user": {"login": "bot"},
                    "body": payload["body"],
                    "in_reply_to_id": payload.get("in_reply_to"),
                    "html_url": "https://github.com/%s/pull/%d"
                                "#discussion_r%d" % (
                                    self.repo, self.number, self._next_id),
                }
                self._next_id += 1
                self.review_comments.append(comment)
                return 0, json.dumps(comment), ""
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


def _run(argv, gh, env=None, seams=None):
    """Run ``room.main(argv, gh=gh, **seams)`` and return ``(code, stdout,
    stderr)``.

    ``HOME`` is an empty temp directory and ``SHIPD_ROOM_AGENT`` is unset
    unless ``env`` supplies it; a ``SystemExit`` (argparse usage) is caught
    and its code returned. ``seams`` holds the watch verb's ``sleep`` and
    ``clock`` keyword arguments."""
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
                code = room.main(list(argv), gh=gh, **(seams or {}))
            except SystemExit as exc:
                code = exc.code if isinstance(exc.code, int) else 1
        return code, out.getvalue(), err.getvalue()
    finally:
        shutil.rmtree(home, ignore_errors=True)


def card_comment(comment_id, name, skills=(), harness="", version="",
                 description="", login="bot", role=""):
    """An issue comment carrying an agent card marker."""
    card = room_schema.AgentCard(name=name, skills=tuple(skills),
                                 harness=harness, version=version,
                                 description=description, role=role)
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


def review_msg_comment(comment_id, agent, text="hi", task_id=None,
                       login="bot", **metadata):
    """A review comment carrying a Message marker (a finding task's opener
    or a reply on its thread)."""
    return msg_comment(comment_id, agent, text=text, task_id=task_id,
                       login=login, **metadata)


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

    def test_reply_follows_its_opener_across_endpoints(self):
        # room-gh-seam: the union orders by created_at, then id — a lower-id
        # issue-comment reply posted after a review-comment opener follows it.
        opener = msg_comment(900, "gate", text="finding",
                             state="input-required", round=1, to="claude-b")
        opener["created_at"] = "2026-01-01T10:00:00Z"
        reply = msg_comment(50, "claude-b", text="fixed", task_id=900,
                            state="working", round=2)
        reply["created_at"] = "2026-01-01T10:05:00Z"
        gh = FakeGh(comments=[reply], review_comments=[opener])
        code, out, err = self.room(gh, "list", "7", "--json",
                                   "--agent", "codex-a")
        self.assertEqual(code, 0, err)
        tasks = json.loads(out)["tasks"]
        self.assertEqual(len(tasks), 1, tasks)
        self.assertEqual(tasks[0]["id"], 900)
        self.assertEqual(tasks[0]["messages"], 2)
        self.assertEqual(tasks[0]["last_agent"], "claude-b")
        self.assertEqual(tasks[0]["state"], "working")

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

    def test_url_resolves_with_no_repository_lookup(self):
        gh = FakeGh()
        code, out, err = _watch(["https://github.com/o/r/pull/7", "--once",
                                 "--agent", "codex-a", "--root", self.root],
                                gh)
        self.assertEqual(code, 0, err)
        self.assertIn("watch: no actionable task on %s" % CONTEXT, err)
        self.assertEqual(gh.repo_views(), [])
        self.assertTrue(gh.pr_views())
        for args in gh.pr_views():
            self.assertEqual(args[args.index("--repo") + 1], "o/r")

    def test_flag_supplies_the_repository(self):
        gh = FakeGh()
        code, out, err = self.room(gh, "list", "7", "--repo", "o/r",
                                   "--json", "--agent", "codex-a")
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["context"], CONTEXT)
        self.assertEqual(gh.repo_views(), [])
        for args in gh.pr_views():
            self.assertEqual(args[args.index("--repo") + 1], "o/r")

    def test_neither_falls_back_to_the_working_directory(self):
        gh = FakeGh()
        code, out, err = self.room(gh, "list", "7", "--agent", "codex-a")
        self.assertEqual(code, 0, err)
        self.assertEqual(len(gh.repo_views()), 1)
        for args in gh.pr_views():
            self.assertNotIn("--repo", args)

    def test_url_and_flag_naming_different_repositories_are_refused(self):
        gh = FakeGh()
        code, out, err = self.room(
            gh, "list", "https://github.com/o/r/pull/7", "--repo", "x/y",
            "--agent", "codex-a")
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        lines = err.splitlines()
        self.assertEqual(len(lines), 1, err)
        self.assertTrue(lines[0].startswith("Error: "), err)
        self.assertIn("o/r", err)
        self.assertIn("x/y", err)
        self.assertEqual(_reads(gh, "issues"), [])
        self.assertEqual(_reads(gh, "pulls"), [])

    def test_url_and_flag_naming_the_same_repository_agree(self):
        gh = FakeGh()
        code, out, err = self.room(
            gh, "list", "https://github.com/o/r/pull/7", "--repo", "O/R",
            "--agent", "codex-a")
        self.assertEqual(code, 0, err)

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

    def test_join_with_a_role_heads_and_marks_the_card(self):
        gh = FakeGh()
        code, _out, err = self.room(gh, "join", "7", "--agent", "codex-a",
                                    "--role", "author")
        self.assertEqual(code, 0, err)
        body = gh.posts()[0]
        self.assertEqual(first_marker(body).role, "author")
        self.assertIn('"role":"author"', body.splitlines()[0])
        self.assertIn("### \u2615 shipd \u00b7 codex-a \u00b7 author "
                      "(for @bot)", body)
        self.assertEqual(gh.user_calls(), 1)

    def test_unknown_role_is_a_usage_error(self):
        gh = FakeGh()
        code, _out, _err = self.room(gh, "join", "7", "--agent", "codex-a",
                                     "--role", "boss")
        self.assertEqual(code, 2)
        self.assertEqual(gh.posts(), [])

    def test_rejoin_without_a_role_clears_it(self):
        gh = FakeGh()
        self.room(gh, "join", "7", "--agent", "codex-a", "--role", "author")
        code, _out, err = self.room(gh, "join", "7", "--agent", "codex-a")
        self.assertEqual(code, 0, err)
        body = gh.patches()[0][1]
        self.assertNotIn('"role"', body.splitlines()[0])
        self.assertEqual(first_marker(body).role, "")

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

    def _summary_comment(self, comment_id, name, marker):
        base = card_comment(comment_id, name)
        base["body"] = base["body"] + "\n" + marker + "\nReview summary.\n"
        return base

    def _assert_summary_left_alone(self, marker):
        summary = self._summary_comment(6206725970, "semantic-review", marker)
        original = summary["body"]
        gh = FakeGh(number=14, comments=[summary])
        code, out, err = self.room(gh, "join", "14", "--agent",
                                   "semantic-review")
        self.assertEqual(code, 0, err)
        self.assertEqual(gh.patches(), [])
        self.assertEqual(gh.deletes(), [])
        posts = gh.posts()
        self.assertEqual(len(posts), 1)
        self.assertTrue(posts[0].splitlines()[0].startswith(
            "<!-- shipd-room-card "))
        self.assertEqual(first_marker(posts[0]).name, "semantic-review")
        new_id = gh.comments[-1]["id"]
        self.assertNotEqual(new_id, 6206725970)
        self.assertEqual(json.loads(out)["comment"], new_id)
        self.assertEqual(gh.comments[0]["body"], original)
        return gh, new_id

    def test_join_leaves_the_review_summary_alone(self):
        gh, new_id = self._assert_summary_left_alone(
            "<!-- shipd-semantic-review -->")
        code, out, err = self.room(gh, "join", "14", "--agent",
                                   "semantic-review")
        self.assertEqual(code, 0, err)
        patches = gh.patches()
        self.assertEqual(len(patches), 1)
        self.assertEqual(patches[0][0], new_id)
        self.assertEqual(len(gh.posts()), 1)

    def test_join_leaves_the_legacy_summary_alone(self):
        self._assert_summary_left_alone("<!-- am-semantic-review -->")

    def test_card_with_a_second_room_marker_is_not_owned(self):
        mixed = card_comment(1001, "codex-a")
        mixed["body"] += "\n" + msg_comment(1002, "codex-a")["body"]
        gh = FakeGh(comments=[mixed])
        code, _out, err = self.room(gh, "join", "7", "--agent", "codex-a")
        self.assertEqual(code, 0, err)
        self.assertEqual(gh.patches(), [])
        self.assertEqual(len(gh.posts()), 1)

    def test_join_edits_the_owned_card_not_a_foreign_one(self):
        owned = card_comment(1001, "codex-a")
        foreign = self._summary_comment(1002, "codex-a",
                                        "<!-- shipd-semantic-review -->")
        gh = FakeGh(comments=[owned, foreign])
        code, _out, err = self.room(gh, "join", "7", "--agent", "codex-a")
        self.assertEqual(code, 0, err)
        self.assertEqual(gh.posts(), [])
        patches = gh.patches()
        self.assertEqual(len(patches), 1)
        self.assertEqual(patches[0][0], 1001)

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

    def _mixed(self):
        return FakeGh(comments=[
            msg_comment(10, "codex-a", state="completed", to="claude-b"),
            msg_comment(11, "codex-a", state="working", to="claude-b"),
            msg_comment(12, "codex-a", state="input-required",
                        to="claude-b"),
        ])

    def test_open_keeps_only_unfinished_tasks(self):
        code, out, err = self.room(self._mixed(), "list", "7", "--open",
                                   "--json", "--agent", "codex-a")
        self.assertEqual(code, 0, err)
        self.assertEqual([t["id"] for t in json.loads(out)["tasks"]],
                         [11, 12])
        code, out, err = self.room(self._mixed(), "list", "7", "--open",
                                   "--agent", "codex-a")
        self.assertEqual(code, 0, err)
        self.assertIn("#11 ", out)
        self.assertIn("#12 ", out)
        self.assertNotIn("#10 ", out)

    def test_a_clean_room_lists_no_open_task(self):
        gh = FakeGh(comments=[
            msg_comment(10, "codex-a", state="completed", to="claude-b")])
        code, out, err = self.room(gh, "list", "7", "--open", "--json",
                                   "--agent", "codex-a")
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["tasks"], [])

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

    def test_message_heads_with_the_cards_role_and_reads_login_once(self):
        gh = FakeGh(comments=[card_comment(1, "codex-a", role="author"),
                              card_comment(2, "claude-b")])
        code, _out, err = self.room(gh, "message", "7", "--new", "--to",
                                    "claude-b", "hi", "--agent", "codex-a")
        self.assertEqual(code, 0, err)
        self.assertEqual(
            gh.posts()[0].split("\n", 2)[2].splitlines()[0],
            "### \u2615 shipd \u00b7 codex-a \u00b7 author (for @bot)")
        self.assertEqual(gh.user_calls(), 1)

    def test_card_without_a_role_drops_the_role_segment(self):
        gh = FakeGh(comments=_joined())
        code, _out, err = self.room(gh, "message", "7", "--new", "--to",
                                    "claude-b", "hi", "--agent", "codex-a")
        self.assertEqual(code, 0, err)
        self.assertEqual(
            gh.posts()[0].split("\n", 2)[2].splitlines()[0],
            "### \u2615 shipd \u00b7 codex-a (for @bot)")

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


class ClaimReplyTest(RoomTestBase):
    """room-message-verb and room-close-verb: a reply on a task the agent
    claimed with ``working`` posts, then deletes its own claim comment."""

    def _room(self, claimer="claude-b", delete_fail=False):
        return FakeGh(delete_fail=delete_fail, comments=_joined(
            msg_comment(10, "codex-a", text="please check",
                        state="input-required", round=1, to="claude-b"),
            msg_comment(30, claimer, text="picked up", task_id=10,
                        state="working", round=1)))

    def test_reply_posts_then_deletes_own_claim(self):
        gh = self._room()
        code, out, err = self.room(gh, "message", "7", "--task", "10",
                                   "--state", "completed", "done",
                                   "--agent", "claude-b")
        self.assertEqual(code, 0, err)
        self.assertEqual(len(gh.posts()), 1)
        self.assertEqual(gh.deletes(), [30])
        kinds = [("POST" if "POST" in a else "DELETE")
                 for a, _i in gh.calls if "-X" in a]
        self.assertEqual(kinds, ["POST", "DELETE"])
        self.assertEqual(json.loads(out)["comment"], gh.comments[-1]["id"])
        self.assertNotIn(30, [c["id"] for c in gh.comments])

    def test_another_agents_claim_is_kept(self):
        gh = self._room(claimer="codex-a")
        code, _out, err = self.room(gh, "message", "7", "--task", "10",
                                    "--state", "completed", "done",
                                    "--agent", "claude-b")
        self.assertEqual(code, 0, err)
        self.assertEqual(len(gh.posts()), 1)
        self.assertEqual(gh.deletes(), [])

    def test_failed_delete_warns_and_exits_zero(self):
        gh = self._room(delete_fail=True)
        code, _out, err = self.room(gh, "message", "7", "--task", "10",
                                    "--state", "completed", "done",
                                    "--agent", "claude-b")
        self.assertEqual(code, 0, err)
        self.assertEqual(len(gh.posts()), 1)
        self.assertIn("warning: could not remove claim comment 30", err)

    def test_close_over_own_claim_deletes_it(self):
        gh = FakeGh(comments=_joined(
            card_comment(3, "copilot-ci"),
            msg_comment(10, "codex-a", text="please check",
                        state="input-required", round=1, to="copilot-ci"),
            msg_comment(30, "copilot-ci", text="picked up by the CI wake",
                        task_id=10, state="working", round=1)))
        code, _out, err = self.room(gh, "close", "7", "--task", "10",
                                    "--state", "failed", "--reason",
                                    "wake-runner-failed",
                                    "--agent", "copilot-ci")
        self.assertEqual(code, 0, err)
        self.assertEqual(len(gh.posts()), 1)
        self.assertEqual(gh.deletes(), [30])


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

    def test_failed_login_read_still_posts_with_a_warning(self):
        gh = self._room()
        gh.user_fail = True
        code, _out, err = self.room(gh, "close", "7", "--task", "10",
                                    "--agent", "claude-b")
        self.assertEqual(code, 0, err)
        self.assertIn("warning:", err)
        body = gh.posts()[0]
        self.assertIn("### \u2615 shipd \u00b7 claude-b", body)
        self.assertNotIn("(for @", body)

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


def _task(**kw):
    """A ``room_schema.Task`` with defaults for every field ``kw`` omits: an
    ``input-required`` task from ``codex-a`` to ``claude-b`` at round 1."""
    fields = dict(id=10, context_id=CONTEXT, opener="codex-a", skill=None,
                  messages=[], state="input-required", to="claude-b",
                  round=1, reason=None, last_agent="codex-a")
    fields.update(kw)
    return room_schema.Task(**fields)


class ActionableTest(unittest.TestCase):
    """room-actionable-predicate: the pure is-it-my-turn rule."""

    def test_addressed_task_is_actionable_for_its_addressee_only(self):
        task = _task()
        self.assertTrue(room.is_actionable(task, "claude-b"))
        self.assertFalse(room.is_actionable(task, "codex-a"))
        self.assertFalse(room.is_actionable(task, "other"))

    def test_unaddressed_task_matches_by_skill(self):
        task = _task(to=None, skill="review-finding")
        self.assertTrue(room.is_actionable(task, "claude-b",
                                           ("review-finding",)))
        self.assertFalse(room.is_actionable(task, "claude-b", ()))
        self.assertFalse(room.is_actionable(task, "claude-b"))

    def test_own_last_message_is_never_actionable(self):
        task = _task(last_agent="claude-b")
        self.assertFalse(room.is_actionable(task, "claude-b"))

    def test_terminal_and_working_tasks_are_skipped(self):
        tasks = [_task(id=i, state=state) for i, state in enumerate(
            ("completed", "failed", "canceled", "working", "submitted"),
            start=10)]
        self.assertEqual(room.actionable_tasks(tasks, "claude-b"), [])

    def test_results_are_ordered_by_id(self):
        tasks = [_task(id=30), _task(id=10, state="working"), _task(id=20),
                 _task(id=5, to=None, skill="review-finding")]
        got = room.actionable_tasks(tasks, "claude-b", ("review-finding",))
        self.assertEqual([t.id for t in got], [5, 20, 30])


class RoomReadSplitTest(unittest.TestCase):
    """room-watch-verb: the one-fetch room read split into the paginated
    fetch, the parse, and the last-comment lookup ``watch`` needs."""

    def _gh(self):
        return FakeGh(comments=[
            card_comment(100, "codex-a", harness="codex"),
            msg_comment(101, "codex-a", text="please check",
                        state="input-required", round=1, to="claude-b"),
            card_comment(102, "claude-b", harness="claude"),
            msg_comment(103, "claude-b", text="on it", task_id=101,
                        state="working", round=2),
        ], review_comments=[
            msg_comment(104, "gate", text="finding", state="input-required",
                        round=1, to="claude-b"),
        ], pages=2)

    def test_read_comments_flattens_the_slurped_pages_in_order(self):
        gh = self._gh()
        comments = room._read_comments(gh, "o/r", 7)
        self.assertEqual([c["id"] for c in comments],
                         [100, 101, 102, 103, 104])
        self.assertTrue(all(isinstance(c, dict) for c in comments))
        self.assertEqual([room._endpoint(c) for c in comments],
                         ["issue"] * 4 + ["review"])
        reads = [args for args, _inp in gh.calls if args[0] == "api"]
        self.assertEqual(len(reads), 2)

    def test_room_from_comments_matches_read_room(self):
        gh = self._gh()
        cards, tasks, _raw, _comments = room._read_room(gh, "o/r", 7)
        got_cards, got_tasks = room._room_from_comments(
            room._read_comments(self._gh(), "o/r", 7))
        self.assertEqual(got_cards, cards)
        self.assertEqual(got_tasks, tasks)
        self.assertEqual([t.id for t in got_tasks], [101, 104])

    def test_last_comment_is_the_last_reply_or_the_opener(self):
        comments = room._read_comments(self._gh(), "o/r", 7)
        _cards, tasks = room._room_from_comments(comments)
        by_id = {t.id: t for t in tasks}
        self.assertEqual(room._last_comment(comments, by_id[101])["id"], 103)
        self.assertEqual(room._last_comment(comments, by_id[104])["id"], 104)


class FakeClock:
    """A monotonic clock: each call returns the current time, then advances
    it by ``step`` seconds."""

    def __init__(self, step=0.0, start=0.0):
        self.step = step
        self.now = start
        self.calls = 0

    def __call__(self):
        value = self.now
        self.now += self.step
        self.calls += 1
        return value


class FakeSleep:
    """A ``sleep`` that never sleeps: it records each argument and runs
    ``callback(call_number)`` (1-based) when one is given."""

    def __init__(self, callback=None):
        self.callback = callback
        self.calls = []

    def __call__(self, seconds):
        self.calls.append(seconds)
        if self.callback is not None:
            self.callback(len(self.calls))


def _watch(argv, gh, sleep=None, clock=None):
    """Run ``room.main(["watch", ...], gh=gh, sleep=..., clock=...)``; returns
    ``(code, stdout, stderr)``. The seams default to fakes, so no test ever
    sleeps for real."""
    seams = {"sleep": sleep if sleep is not None else FakeSleep(),
             "clock": clock if clock is not None else FakeClock()}
    return _run(["watch"] + list(argv), gh, seams=seams)


def _reads(gh, endpoint="issues"):
    """The recorded comment reads of one endpoint (``issues`` or ``pulls``)."""
    return [args for args, _inp in gh.calls
            if args[0] == "api" and "-X" not in args
            and "/%s/" % endpoint in args[1]]


class WatchTestBase(RoomTestBase):
    def watch(self, gh, *argv, sleep=None, clock=None):
        """Run ``watch 7`` with ``--root`` pinned to an empty temp dir."""
        return _watch(["7"] + list(argv) + ["--root", self.root], gh,
                      sleep=sleep, clock=clock)

    def lines(self, out):
        return [json.loads(line) for line in out.splitlines()]


class WatchTest(WatchTestBase):
    """room-watch-verb and room-watch-exit: the poll loop, the cursor, and
    the exits."""

    def _two_tasks(self):
        return [
            msg_comment(10, "codex-a", text="please check",
                        state="input-required", round=1, to="claude-b"),
            msg_comment(11, "claude-b", text="your turn",
                        state="input-required", round=1, to="codex-a"),
        ]

    def test_first_poll_surfaces_the_backlog_and_exits(self):
        gh = FakeGh(comments=self._two_tasks())
        sleep = FakeSleep()
        code, out, err = self.watch(gh, "--agent", "claude-b", sleep=sleep)
        self.assertEqual(code, 0, err)
        lines = self.lines(out)
        self.assertEqual(len(lines), 1, out)
        line = lines[0]
        for key in ("task", "comment", "text", "url", "context", "cursor"):
            self.assertIn(key, line)
        for key in ("id", "state", "opener", "to", "round", "reason",
                    "last_agent", "skill", "messages"):
            self.assertIn(key, line)
        self.assertEqual(line["task"], 10)
        self.assertEqual(line["id"], 10)
        self.assertEqual(line["comment"], 10)
        self.assertEqual(line["text"], "please check")
        self.assertEqual(line["url"], "https://example/10")
        self.assertEqual(line["context"], CONTEXT)
        self.assertEqual(line["cursor"], "11:0")
        self.assertEqual(out.splitlines()[0],
                         json.dumps(line, sort_keys=True))
        self.assertEqual(len(_reads(gh, "issues")), 1)
        self.assertEqual(len(_reads(gh, "pulls")), 1)
        self.assertEqual(sleep.calls, [])

    def test_reply_is_the_comment_and_text_of_the_line(self):
        gh = FakeGh(comments=[
            msg_comment(10, "codex-a", text="please check",
                        state="input-required", round=1, to="codex-a"),
            msg_comment(12, "codex-b", text="over to you", task_id=10,
                        state="input-required", round=2, to="claude-b"),
        ])
        code, out, err = self.watch(gh, "--agent", "claude-b")
        self.assertEqual(code, 0, err)
        line = self.lines(out)[0]
        self.assertEqual((line["task"], line["comment"], line["text"]),
                         (10, 12, "over to you"))
        self.assertEqual(line["url"], "https://example/12")

    def test_cursor_hides_what_was_already_seen(self):
        for since in ("10:0", "10"):
            with self.subTest(since=since):
                gh = FakeGh(comments=self._two_tasks())
                code, out, err = self.watch(gh, "--agent", "claude-b",
                                            "--since", since, "--once")
                self.assertEqual(code, 0, err)
                self.assertEqual(out, "")

    def test_review_task_is_judged_by_the_review_component(self):
        gh = FakeGh(
            comments=[human_comment(100, "a human note")],
            review_comments=[msg_comment(40, "gate", text="finding",
                                         state="input-required", round=1,
                                         to="claude-b")])
        code, out, err = self.watch(gh, "--agent", "claude-b",
                                    "--since", "100:39", "--once")
        self.assertEqual(code, 0, err)
        lines = self.lines(out)
        self.assertEqual([l["task"] for l in lines], [40])
        self.assertEqual(lines[0]["cursor"], "100:40")
        gh = FakeGh(comments=list(gh.comments),
                    review_comments=list(gh.review_comments))
        code, out, err = self.watch(gh, "--agent", "claude-b",
                                    "--since", "100:40", "--once")
        self.assertEqual(code, 0, err)
        self.assertEqual(out, "")

    def test_skill_match_without_a_card_is_empty(self):
        gh = FakeGh(comments=[msg_comment(
            10, "gate", text="finding", state="input-required", round=1,
            skill="review-finding")])
        code, out, err = self.watch(gh, "--agent", "claude-b", "--once")
        self.assertEqual(code, 0, err)
        self.assertEqual(out, "")
        self.assertNotIn("Error:", err)

    def test_skill_match_with_a_card_is_surfaced(self):
        gh = FakeGh(comments=[
            card_comment(1, "claude-b", skills=("review-finding",)),
            msg_comment(10, "gate", text="finding", state="input-required",
                        round=1, skill="review-finding")])
        code, out, err = self.watch(gh, "--agent", "claude-b", "--once")
        self.assertEqual(code, 0, err)
        self.assertEqual([l["task"] for l in self.lines(out)], [10])

    def test_a_task_becomes_actionable_on_a_later_poll(self):
        gh = FakeGh(comments=[card_comment(1, "claude-b")])

        def arrive(call):
            if call == 2:
                gh.comments.append(msg_comment(
                    20, "codex-a", text="now you", state="input-required",
                    round=1, to="claude-b"))

        sleep = FakeSleep(arrive)
        code, out, err = self.watch(gh, "--agent", "claude-b", sleep=sleep)
        self.assertEqual(code, 0, err)
        self.assertEqual(sleep.calls, [30.0, 30.0])
        self.assertEqual(len(_reads(gh, "issues")), 3)
        self.assertEqual([l["task"] for l in self.lines(out)], [20])

    def test_once_with_nothing_exits_zero_and_empty(self):
        gh = FakeGh(comments=self._two_tasks())
        code, out, err = self.watch(gh, "--agent", "codex-b", "--once")
        self.assertEqual(code, 0, err)
        self.assertEqual(out, "")
        self.assertEqual(err.splitlines()[-1],
                         "watch: no actionable task on %s (cursor 11:0)"
                         % CONTEXT)

    def test_timeout_ends_the_watch(self):
        gh = FakeGh(comments=self._two_tasks())
        sleep = FakeSleep()
        code, out, err = self.watch(gh, "--agent", "codex-b", "--timeout",
                                    "60", "--interval", "20", sleep=sleep,
                                    clock=FakeClock(step=25))
        self.assertEqual(code, 0, err)
        self.assertEqual(out, "")
        # The clock reads 0 at the start, then 25, 50, 75 after each poll.
        self.assertEqual(sleep.calls, [20.0, 20.0])
        self.assertEqual(len(_reads(gh, "issues")), 3)
        self.assertEqual(len(_reads(gh, "pulls")), 3)
        self.assertIn("watch: no actionable task on %s" % CONTEXT, err)

    def test_merged_pull_request_closes_the_watch(self):
        for state, word in (("MERGED", "merged"), ("CLOSED", "closed")):
            gh = FakeGh(comments=[msg_comment(
                10, "codex-a", state="completed", to="claude-b")],
                state=state)
            sleep = FakeSleep()
            code, out, err = self.watch(gh, "--agent", "codex-b",
                                        sleep=sleep)
            self.assertEqual(code, 0, err)
            self.assertEqual(self.lines(out), [
                {"closed": word, "context": CONTEXT, "cursor": "10:0",
                 "open": []}])
            self.assertEqual(err.splitlines()[-1],
                             "watch: %s is %s; the room is closed"
                             % (CONTEXT, word))
            self.assertNotIn("unresolved", err)
            self.assertEqual(sleep.calls, [])

    def test_closed_line_lists_unresolved_tasks(self):
        gh = FakeGh(comments=[
            msg_comment(10, "codex-a", state="input-required",
                        to="claude-b", skill="review-finding"),
            msg_comment(11, "codex-a", state="completed", to="claude-b"),
        ], state="MERGED")
        code, out, err = self.watch(gh, "--agent", "codex-b")
        self.assertEqual(code, 0, err)
        line = self.lines(out)[-1]
        self.assertEqual(line["open"], [{
            "task": 10, "state": "input-required", "to": "claude-b",
            "skill": "review-finding"}])
        errs = err.splitlines()
        self.assertEqual(errs[-2],
                         "watch: 1 unresolved task(s): #10 input-required")
        self.assertEqual(errs[-1],
                         "watch: %s is merged; the room is closed" % CONTEXT)

    def test_state_read_carries_the_repository(self):
        gh = FakeGh()
        code, out, err = _watch(["https://github.com/o/r/pull/7", "--once",
                                 "--agent", "codex-a", "--root", self.root],
                                gh)
        self.assertEqual(code, 0, err)
        states = [a for a in gh.pr_views() if "state" in a]
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0][:3], ["pr", "view", "7"])
        self.assertEqual(states[0][states[0].index("--repo") + 1], "o/r")

    def test_surfaced_task_prints_before_the_closed_line(self):
        gh = FakeGh(comments=self._two_tasks(), state="MERGED")
        code, out, err = self.watch(gh, "--agent", "claude-b")
        self.assertEqual(code, 0, err)
        lines = self.lines(out)
        self.assertEqual(len(lines), 2, out)
        self.assertEqual(lines[0]["task"], 10)
        self.assertEqual(lines[1]["closed"], "merged")

    def test_open_pull_request_keeps_the_timeout_behavior(self):
        gh = FakeGh(comments=self._two_tasks(), state="OPEN")
        code, out, err = self.watch(gh, "--agent", "codex-b", "--once")
        self.assertEqual(code, 0, err)
        self.assertEqual(out, "")
        self.assertIn("watch: no actionable task", err)

    def test_failed_read_is_fatal(self):
        gh = FakeGh(comments=self._two_tasks(),
                    fail=["api", "repos/o/r/issues/7/comments?per_page=100"])
        sleep = FakeSleep()
        code, out, err = self.watch(gh, "--agent", "claude-b", sleep=sleep)
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        lines = err.splitlines()
        self.assertEqual(len(lines), 1, err)
        self.assertTrue(lines[0].startswith("Error: "), err)
        self.assertEqual(sleep.calls, [])

    def test_interval_must_be_positive(self):
        for interval in ("0", "-5"):
            with self.subTest(interval=interval):
                gh = FakeGh()
                code, _out, err = self.watch(gh, "--agent", "claude-b",
                                             "--interval", interval)
                self.assertEqual(code, 2)
                self.assertIn("usage:", err)
                self.assertEqual(gh.calls, [])

    def test_bad_cursor_is_a_usage_error(self):
        gh = FakeGh()
        code, _out, err = self.watch(gh, "--agent", "claude-b",
                                     "--since", "x:y")
        self.assertEqual(code, 2)
        self.assertIn("usage:", err)

    def test_keyboard_interrupt_exits_130_without_a_traceback(self):
        def interrupted(args, input=None):
            raise KeyboardInterrupt

        code, out, err = self.watch(interrupted, "--agent", "claude-b")
        self.assertEqual(code, 130)
        self.assertEqual(out, "")
        self.assertEqual(err, "")


class WatchRoundCapTest(WatchTestBase):
    """room-watch-round-cap: a capped task is failed (with a card) or warned
    about (without one), never surfaced, and the poll carries on."""

    def _capped(self):
        return msg_comment(10, "codex-a", text="again?",
                           state="input-required", round=6, to="claude-b")

    def test_cap_posts_failed_and_keeps_polling(self):
        gh = FakeGh(comments=[card_comment(1, "claude-b"), self._capped()])
        code, out, err = self.watch(gh, "--agent", "claude-b", "--once",
                                    "--max-rounds", "6")
        self.assertEqual(code, 0, err)
        self.assertEqual(out, "")
        posts = gh.posts()
        self.assertEqual(len(posts), 1, posts)
        msg = first_marker(posts[0])
        self.assertEqual(msg.task_id, 10)
        self.assertEqual(msg.agent, "claude-b")
        self.assertEqual(msg.context_id, CONTEXT)
        self.assertEqual(msg.metadata, {"reason": "round-cap", "round": 7,
                                        "state": "failed"})
        self.assertEqual(msg.text, "round cap (6) reached")
        self.assertIn("task 10: round cap reached — posted failed "
                      "(round-cap)", err)
        self.assertIn("watch: no actionable task on %s" % CONTEXT, err)

    def test_cap_post_is_headed_and_reads_login_once(self):
        gh = FakeGh(comments=[card_comment(1, "claude-b", role="reviewer"),
                              self._capped(),
                              msg_comment(11, "codex-a", text="again?",
                                          state="input-required", round=6,
                                          to="claude-b")])
        code, _out, err = self.watch(gh, "--agent", "claude-b", "--once",
                                     "--max-rounds", "6")
        self.assertEqual(code, 0, err)
        posts = gh.posts()
        self.assertEqual(len(posts), 2, posts)
        for body in posts:
            self.assertIn("### \u2615 shipd \u00b7 claude-b \u00b7 reviewer "
                          "(for @bot)", body)
        self.assertEqual(gh.user_calls(), 1)

    def test_cap_without_a_card_is_a_warning(self):
        gh = FakeGh(comments=[self._capped()])
        code, out, err = self.watch(gh, "--agent", "claude-b", "--once",
                                    "--max-rounds", "6")
        self.assertEqual(code, 0, err)
        self.assertEqual(out, "")
        self.assertEqual(gh.posts(), [])
        self.assertIn("WARNING: task 10: round cap reached; join the room "
                      "to close it", err)

    def test_cap_without_a_card_warns_once_per_watch(self):
        gh = FakeGh(comments=[self._capped()])
        sleep = FakeSleep()
        code, out, err = self.watch(gh, "--agent", "claude-b",
                                    "--max-rounds", "6", "--timeout", "60",
                                    sleep=sleep, clock=FakeClock(step=25))
        self.assertEqual(code, 0, err)
        self.assertGreaterEqual(len(_reads(gh)), 2)
        self.assertEqual(out, "")
        self.assertEqual(gh.posts(), [])
        self.assertEqual(err.count("WARNING: task 10: round cap reached; "
                                   "join the room to close it"), 1, err)

    def test_task_below_the_cap_is_still_surfaced(self):
        gh = FakeGh(comments=[
            card_comment(1, "claude-b"), self._capped(),
            msg_comment(11, "codex-a", text="fresh", state="input-required",
                        round=1, to="claude-b")])
        code, out, err = self.watch(gh, "--agent", "claude-b", "--once",
                                    "--max-rounds", "6")
        self.assertEqual(code, 0, err)
        self.assertEqual([l["task"] for l in self.lines(out)], [11])
        self.assertEqual(len(gh.posts()), 1)


class FindingThreadReplyTest(RoomTestBase):
    """room-finding-thread-reply: a finding task's messages reply on its
    review thread; every other task stays on issue comments."""

    def _finding(self, **extra):
        return review_msg_comment(
            900, "semantic-review", text="finding", state="input-required",
            round=1, to="claude-b", skill="review-finding", **extra)

    def _gh(self, claim=False, **kwargs):
        review = [self._finding()]
        if claim:
            review.append(review_msg_comment(
                950, "claude-b", text="on it", task_id=900,
                state="working", round=1))
        return FakeGh(comments=[card_comment(2, "claude-b"),
                                card_comment(3, "semantic-review")],
                      review_comments=review, **kwargs)

    def test_working_claim_replies_on_the_thread(self):
        gh = self._gh()
        code, _out, err = self.room(gh, "message", "7", "--task", "900",
                                    "--state", "working", "looking",
                                    "--agent", "claude-b")
        self.assertEqual(code, 0, err)
        self.assertEqual(gh.issue_posts(), [])
        posts = gh.review_posts()
        self.assertEqual(len(posts), 1, posts)
        self.assertEqual(posts[0][0], 900)
        self.assertEqual(first_marker(posts[0][1]).task_id, 900)
        self.assertTrue(any(
            "repos/o/r/pulls/7/comments" in args
            for args, _inp in gh.calls if "POST" in args))

    def test_reply_drops_the_claim_through_the_pulls_endpoint(self):
        gh = self._gh(claim=True)
        code, _out, err = self.room(
            gh, "message", "7", "--task", "900", "--state", "input-required",
            "--to", "semantic-review", "why?", "--agent", "claude-b")
        self.assertEqual(code, 0, err)
        kinds = [("POST" if "POST" in args else "DELETE")
                 for args, _inp in gh.calls
                 if "POST" in args or "DELETE" in args]
        self.assertEqual(kinds, ["POST", "DELETE"])
        self.assertEqual(len(gh.review_posts()), 1)
        self.assertEqual(gh.delete_paths(), ["repos/o/r/pulls/comments/950"])

    def test_issue_task_reply_stays_on_issue_comments(self):
        gh = FakeGh(comments=_joined(msg_comment(
            10, "codex-a", text="please check", state="input-required",
            round=1, to="claude-b")))
        code, _out, err = self.room(gh, "message", "7", "--task", "10",
                                    "--state", "working", "ok",
                                    "--agent", "claude-b")
        self.assertEqual(code, 0, err)
        self.assertEqual(gh.review_posts(), [])
        self.assertEqual(len(gh.issue_posts()), 1)
        self.assertTrue(any(
            "repos/o/r/issues/7/comments" in args
            for args, _inp in gh.calls if "POST" in args))

    def test_message_round_cap_posts_failed_on_the_thread(self):
        gh = FakeGh(
            comments=[card_comment(2, "claude-b")],
            review_comments=[review_msg_comment(
                900, "semantic-review", text="finding",
                state="input-required", round=6, to="claude-b",
                skill="review-finding")])
        code, _out, err = self.room(gh, "message", "7", "--task", "900",
                                    "again", "--agent", "claude-b",
                                    "--max-rounds", "6")
        self.assertEqual(code, 1)
        self.assertEqual(gh.issue_posts(), [])
        posts = gh.review_posts()
        self.assertEqual(len(posts), 1, posts)
        self.assertEqual(posts[0][0], 900)
        self.assertEqual(first_marker(posts[0][1]).metadata["reason"],
                         "round-cap")

    def test_watch_round_cap_posts_failed_on_the_thread(self):
        gh = FakeGh(
            comments=[card_comment(2, "claude-b")],
            review_comments=[review_msg_comment(
                900, "semantic-review", text="finding",
                state="input-required", round=1, to="claude-b",
                skill="review-finding")])
        code, _out, err = _watch(["7", "--agent", "claude-b", "--once",
                                  "--max-rounds", "1", "--root", self.root],
                                 gh)
        self.assertEqual(code, 0, err)
        self.assertEqual(gh.issue_posts(), [])
        posts = gh.review_posts()
        self.assertEqual(len(posts), 1, posts)
        self.assertEqual(posts[0][0], 900)
        self.assertEqual(first_marker(posts[0][1]).metadata["state"],
                         "failed")


def _thread(thread_id, root_id, resolved=False):
    return {"id": thread_id, "isResolved": resolved,
            "comments": {"nodes": [{"databaseId": root_id}]}}


class FindingThreadResolveTest(RoomTestBase):
    """room-finding-thread-resolve: a completed message on a finding task
    resolves its review thread; a failed resolve warns and exits 0."""

    def _gh(self, threads=None, fail=None, issue_task=False):
        if issue_task:
            return FakeGh(comments=_joined(msg_comment(
                10, "codex-a", text="please check", state="input-required",
                round=1, to="claude-b")), threads=threads or [], fail=fail)
        return FakeGh(
            comments=[card_comment(2, "claude-b")],
            review_comments=[review_msg_comment(
                900, "semantic-review", text="finding",
                state="input-required", round=1, to="claude-b",
                skill="review-finding")],
            threads=[_thread("PRRT_1", 900)] if threads is None else threads,
            fail=fail)

    def test_close_completed_replies_then_resolves(self):
        gh = self._gh()
        code, out, err = self.room(gh, "close", "7", "--task", "900",
                                   "Fixed in abc1234", "--agent", "claude-b")
        self.assertEqual(code, 0, err)
        self.assertEqual(len(gh.review_posts()), 1)
        self.assertEqual([k for k, _f in gh.graphql_calls()],
                         ["lookup", "mutation"])
        self.assertEqual(gh.mutations(), ["PRRT_1"])
        self.assertEqual(json.loads(out)["state"], "completed")
        lookup = gh.graphql_calls()[0][1]
        self.assertEqual((lookup["owner"], lookup["name"], lookup["number"]),
                         ("o", "r", "7"))
        self.assertEqual(lookup["query"], room.THREAD_LOOKUP_QUERY)
        last = [args for args, _inp in gh.calls][-1]
        self.assertIn("graphql", last)

    def test_message_completed_resolves(self):
        gh = self._gh()
        code, _out, err = self.room(gh, "message", "7", "--task", "900",
                                    "--state", "completed", "done",
                                    "--agent", "claude-b")
        self.assertEqual(code, 0, err)
        self.assertEqual(gh.mutations(), ["PRRT_1"])

    def test_canceled_does_not_resolve(self):
        gh = self._gh()
        code, _out, err = self.room(gh, "close", "7", "--task", "900",
                                    "--state", "canceled",
                                    "--agent", "claude-b")
        self.assertEqual(code, 0, err)
        self.assertEqual(len(gh.review_posts()), 1)
        self.assertEqual(gh.mutations(), [])

    def test_already_resolved_thread_gets_no_mutation(self):
        gh = self._gh(threads=[_thread("PRRT_1", 900, resolved=True)])
        code, _out, err = self.room(gh, "close", "7", "--task", "900",
                                    "--agent", "claude-b")
        self.assertEqual(code, 0, err)
        self.assertEqual(gh.mutations(), [])
        self.assertNotIn("warning", err)

    def test_failed_mutation_warns_and_exits_zero(self):
        gh = self._gh(fail=["api", "graphql", "-f",
                            "query=%s" % room_schema.RESOLVE_THREAD_MUTATION])
        code, out, err = self.room(gh, "close", "7", "--task", "900",
                                   "--agent", "claude-b")
        self.assertEqual(code, 0, err)
        self.assertIn("warning: could not resolve the review thread for "
                      "task 900", err)
        self.assertEqual(json.loads(out)["task"], 900)

    def test_no_matching_thread_warns_and_exits_zero(self):
        gh = self._gh(threads=[_thread("PRRT_9", 123)])
        code, out, err = self.room(gh, "close", "7", "--task", "900",
                                   "--agent", "claude-b")
        self.assertEqual(code, 0, err)
        self.assertIn("warning: could not resolve the review thread for "
                      "task 900", err)
        self.assertEqual(gh.mutations(), [])
        self.assertEqual(json.loads(out)["state"], "completed")

    def test_issue_task_completed_makes_no_graphql_call(self):
        gh = self._gh(issue_task=True)
        code, _out, err = self.room(gh, "close", "7", "--task", "10",
                                    "--agent", "claude-b")
        self.assertEqual(code, 0, err)
        self.assertEqual(gh.graphql_calls(), [])
