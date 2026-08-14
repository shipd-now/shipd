#!/usr/bin/env python3
"""Tests for review_gate.py — the mechanical PR poster for /s:review verdicts.

Every network boundary is the injectable ``gh`` command seam; no test spawns a
real ``gh`` process or touches the network. ``FakeGh`` is a stateful dispatcher
that answers the exact ``gh`` invocations the poster makes and records the
writes (status payload, review payloads, comment bodies, protection PATCH) for
assertions.
"""

import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
sys.path.insert(0, SCRIPTS)

import review_gate  # noqa: E402


MARKER = "<!-- am-semantic-review -->"


class FakeGh:
    """A stateful fake of the ``gh`` CLI seam.

    Call signature mirrors the production runner: ``gh(args, input=None) ->
    (returncode, stdout, stderr)`` where ``args`` is everything after ``gh``.
    """

    def __init__(self, *, head_sha="abc123", number=7, repo="o/r",
                 pr_url="https://github.com/o/r/pull/7",
                 default_branch="main", contexts=("ci",),
                 conversation_resolution=False, strict=True,
                 files=None, existing_comments=None, review_fail_times=0,
                 viewer="gate-bot", review_threads=None, commits=None):
        self.head_sha = head_sha
        self.number = number
        self.repo = repo
        self.pr_url = pr_url
        self.default_branch = default_branch
        self.contexts = tuple(contexts)
        self.conversation_resolution = conversation_resolution
        self.strict = strict
        self.files = files if files is not None else []
        self.calls = []                 # list of (args, input)
        self.posted_status = None       # last statuses payload
        self.review_posts = []          # list of parsed review payloads
        self.protect_put = None         # last full-protection PUT body
        self._comments = [dict(c) for c in (existing_comments or [])]
        self._next_comment_id = 1000
        self._review_fail_remaining = review_fail_times
        # Thread model (GraphQL) state. ``viewer`` is the authenticated login —
        # i.e. the account the gate posts as, so gate-authored == root comment
        # authored by ``viewer``. ``review_threads`` is a list of thread dicts
        # (see ``_thread``); ``commits`` is a list of ISO-8601 committedDates.
        self.viewer = viewer
        self.threads = [dict(t, comments=[dict(c) for c in t["comments"]])
                        for t in (review_threads or [])]
        self.commits = list(commits or [])
        self.resolved_thread_ids = []   # thread node ids passed to the mutation
        self.reply_posts = []           # parsed in_reply_to reply payloads

    # -- dispatch -----------------------------------------------------------

    def __call__(self, args, input=None):
        args = list(args)
        self.calls.append((args, input))
        if args[:2] == ["pr", "view"]:
            return 0, json.dumps({"number": self.number,
                                  "headRefOid": self.head_sha,
                                  "url": self.pr_url}), ""
        if args[0] == "repo" and "nameWithOwner" in args:
            return 0, json.dumps({"nameWithOwner": self.repo}), ""
        if args[0] == "repo" and "defaultBranchRef" in args:
            return 0, json.dumps(
                {"defaultBranchRef": {"name": self.default_branch}}), ""
        if args[0] == "api":
            return self._api(args, input)
        return 1, "", "unexpected gh call: %r" % (args,)

    def _method(self, args):
        return args[args.index("-X") + 1] if "-X" in args else "GET"

    def _graphql_fields(self, args):
        """Collect ``-f``/``-F`` ``key=value`` pairs from a ``gh api graphql``
        invocation into a dict."""
        fields = {}
        i = 0
        while i < len(args):
            if args[i] in ("-f", "-F") and i + 1 < len(args):
                key, _, val = args[i + 1].partition("=")
                fields[key] = val
                i += 2
            else:
                i += 1
        return fields

    def _graphql(self, args, input):
        fields = self._graphql_fields(args)
        query = fields.get("query", "")
        if "resolveReviewThread" in query:
            tid = fields.get("threadId")
            hit = next((t for t in self.threads if t["id"] == tid), None)
            if hit is None:
                return 1, "", "no such thread %r" % tid
            hit["isResolved"] = True
            self.resolved_thread_ids.append(tid)
            return 0, json.dumps({"data": {"resolveReviewThread": {
                "thread": {"isResolved": True}}}}), ""
        # Otherwise the reviewThreads listing query.
        nodes = []
        for t in self.threads:
            nodes.append({
                "id": t["id"],
                "isResolved": t["isResolved"],
                "comments": {"nodes": [
                    {"databaseId": c["databaseId"],
                     "author": {"login": c["author"]},
                     "createdAt": c["createdAt"]}
                    for c in t["comments"]]}})
        data = {"data": {
            "viewer": {"login": self.viewer},
            "repository": {"pullRequest": {
                "commits": {"nodes": [
                    {"commit": {"committedDate": d}} for d in self.commits]},
                "reviewThreads": {"nodes": nodes}}}}}
        return 0, json.dumps(data), ""

    def _api(self, args, input):
        endpoint = args[1]
        if endpoint == "graphql":
            return self._graphql(args[2:], input)
        path = endpoint.split("?", 1)[0]
        method = self._method(args)

        # A threaded reply — POST repos/.../pulls/<n>/comments with in_reply_to.
        # Distinct from the issue-comment summary path (repos/.../issues/...).
        if "/pulls/" in path and path.endswith("/comments") and method == "POST":
            payload = json.loads(input)
            root_id = payload.get("in_reply_to")
            target = next((t for t in self.threads
                           if t["comments"]
                           and t["comments"][0]["databaseId"] == root_id), None)
            if target is None:
                return 422, "", "HTTP 422: no such review comment %r" % root_id
            cid = self._next_comment_id
            self._next_comment_id += 1
            target["comments"].append(
                {"databaseId": cid, "author": self.viewer,
                 "createdAt": "2099-01-01T00:00:00Z"})
            reply = {"id": cid, "in_reply_to_id": root_id,
                     "html_url": "%s#discussion_r%d" % (self.pr_url, cid),
                     "body": payload["body"]}
            self.reply_posts.append(reply)
            return 0, json.dumps(reply), ""

        if path.endswith("/protection"):
            if method == "GET":
                # A nested GET-shaped protection object, including a field the
                # verb must preserve untouched across the write.
                return 0, json.dumps({
                    "required_status_checks": {
                        "strict": self.strict, "contexts": list(self.contexts)},
                    "required_conversation_resolution": {
                        "enabled": self.conversation_resolution},
                    "enforce_admins": {"enabled": True},
                    "required_linear_history": {"enabled": True}}), ""
            if method == "PUT":
                payload = json.loads(input)
                self.protect_put = payload
                rsc = payload.get("required_status_checks") or {}
                self.contexts = tuple(rsc.get("contexts") or [])
                self.strict = bool(rsc.get("strict", self.strict))
                self.conversation_resolution = bool(
                    payload.get("required_conversation_resolution"))
                return 0, json.dumps(payload), ""

        if path.endswith("/reviews"):
            payload = json.loads(input)
            self.review_posts.append(payload)
            if self._review_fail_remaining > 0:
                self._review_fail_remaining -= 1
                return 1, "", "HTTP 422: Unprocessable Entity"
            return 0, json.dumps({"id": 55, "state": "COMMENTED"}), ""

        if "/statuses/" in path:
            payload = json.loads(input)
            self.posted_status = payload
            return 0, json.dumps({"id": 1, "state": payload["state"]}), ""

        if path.endswith("/files"):
            return 0, json.dumps(self.files), ""

        if "/issues/comments/" in path:  # PATCH an existing comment in place
            cid = int(path.rsplit("/", 1)[1])
            payload = json.loads(input)
            for c in self._comments:
                if c["id"] == cid:
                    c["body"] = payload["body"]
                    return 0, json.dumps(c), ""
            return 1, "", "no such comment %d" % cid

        if path.endswith("/comments"):
            if method == "GET":
                return 0, json.dumps(self._comments), ""
            payload = json.loads(input)  # POST create
            cid = self._next_comment_id
            self._next_comment_id += 1
            comment = {"id": cid, "body": payload["body"],
                       "html_url": "%s#issuecomment-%d" % (self.pr_url, cid)}
            self._comments.append(comment)
            return 0, json.dumps(comment), ""

        return 1, "", "unhandled api endpoint: %s" % endpoint

    # -- assertion helpers --------------------------------------------------

    def marker_comments(self):
        return [c for c in self._comments if MARKER in c["body"]]

    def summary_body(self):
        marked = self.marker_comments()
        return marked[-1]["body"] if marked else None

    def comment_patch_calls(self):
        return [(a, i) for a, i in self.calls
                if a[0] == "api" and "/issues/comments/" in a[1]
                and "-X" in a and a[a.index("-X") + 1] == "PATCH"]


PATCH_A = (
    "@@ -1,2 +1,6 @@\n"
    " a\n"
    "+b\n"
    "+c\n"
    "+d\n"
    "+e\n"
)


def _review(verdict="pass", effort=2, findings=None, **extra):
    obj = {"verdict": verdict, "effort": effort,
           "findings": findings or [], "could_not_verify": []}
    obj.update(extra)
    return obj


class CommentableLinesTest(unittest.TestCase):
    def test_right_side_lines_from_patch(self):
        patch = (
            "@@ -1,3 +1,4 @@\n"
            " line1\n"
            "-old2\n"
            "+new2\n"
            "+new3\n"
            " line4\n"
        )
        # Context + added lines carry RIGHT-side line numbers; removed do not.
        self.assertEqual(review_gate.commentable_lines(patch), {1, 2, 3, 4})

    def test_multiple_hunks_track_new_line_numbers(self):
        patch = (
            "@@ -1,1 +1,1 @@\n"
            "+top\n"
            "@@ -10,1 +20,2 @@\n"
            " ctx\n"
            "+added\n"
        )
        self.assertEqual(review_gate.commentable_lines(patch), {1, 20, 21})


class PostTest(unittest.TestCase):
    def test_pass_verdict_creates_comment_and_success_status(self):
        gh = FakeGh()
        result = review_gate.post("7", _review(verdict="pass"), gh)
        self.assertEqual(len(gh.marker_comments()), 1)
        self.assertEqual(gh.posted_status["state"], "success")
        self.assertEqual(gh.posted_status["context"], "semantic-review")
        # The status points at the summary comment.
        self.assertEqual(gh.posted_status["target_url"],
                         gh.marker_comments()[0]["html_url"])
        self.assertEqual(result["state"], "success")

    def test_repost_updates_single_marker_comment(self):
        gh = FakeGh()
        review_gate.post("7", _review(verdict="pass"), gh)
        review_gate.post("7", _review(verdict="pass"), gh)
        # Exactly one marker comment survives, and the second run edited it.
        self.assertEqual(len(gh.marker_comments()), 1)
        self.assertTrue(gh.comment_patch_calls())

    def test_red_verdict_anchors_inline_and_folds_out_of_diff(self):
        gh = FakeGh(files=[{"filename": "a.py", "patch": PATCH_A}])
        findings = [
            {"id": "f1", "severity": "high", "location": "a.py:5",
             "what": "boom in a", "why": "w", "fix": "x"},
            {"id": "f2", "severity": "medium", "location": "b.py:99",
             "what": "boom in b", "why": "w", "fix": "x"},
        ]
        review_gate.post(
            "7", _review(verdict="changes-requested", findings=findings), gh)
        self.assertEqual(gh.posted_status["state"], "failure")
        # Exactly one review posted, carrying the in-diff finding inline.
        self.assertEqual(len(gh.review_posts), 1)
        comments = gh.review_posts[0]["comments"]
        self.assertEqual([(c["path"], c["line"]) for c in comments],
                         [("a.py", 5)])
        self.assertEqual(comments[0]["side"], "RIGHT")
        self.assertEqual(gh.review_posts[0]["event"], "COMMENT")
        self.assertEqual(gh.review_posts[0]["commit_id"], gh.head_sha)
        # The out-of-diff finding folded into the summary, not lost.
        body = gh.summary_body()
        self.assertIn("boom in b", body)
        self.assertIn("Additional findings", body)

    def test_review_422_retries_without_inline(self):
        gh = FakeGh(files=[{"filename": "a.py", "patch": PATCH_A}],
                    review_fail_times=1)
        findings = [{"id": "f1", "severity": "high", "location": "a.py:5",
                     "what": "boom", "why": "w", "fix": "x"}]
        review_gate.post(
            "7", _review(verdict="changes-requested", findings=findings), gh)
        # Two review POSTs: the first with inline comments, the retry without.
        self.assertEqual(len(gh.review_posts), 2)
        self.assertTrue(gh.review_posts[0]["comments"])
        self.assertEqual(gh.review_posts[1].get("comments", []), [])
        # After the failure the anchored finding is folded into the summary.
        self.assertIn("boom", gh.summary_body())

    def test_no_findings_posts_no_review(self):
        gh = FakeGh(files=[{"filename": "a.py", "patch": PATCH_A}])
        review_gate.post("7", _review(verdict="pass"), gh)
        self.assertEqual(gh.review_posts, [])


class ProtectTest(unittest.TestCase):
    def test_adds_context_and_conversation_resolution(self):
        gh = FakeGh(contexts=("ci",), conversation_resolution=False)
        result = review_gate.protect(gh)
        self.assertTrue(result["changed"])
        self.assertEqual(set(gh.contexts), {"ci", "semantic-review"})
        self.assertTrue(gh.conversation_resolution)
        self.assertTrue(result["conversation_resolution"])
        # A second run — now in the desired state — is a no-op (no write).
        gh.protect_put = None
        result2 = review_gate.protect(gh)
        self.assertFalse(result2["changed"])
        self.assertIsNone(gh.protect_put)

    def test_remove_clears_context_and_conversation_resolution(self):
        gh = FakeGh(contexts=("ci", "semantic-review"),
                    conversation_resolution=True)
        result = review_gate.protect(gh, remove=True)
        self.assertTrue(result["changed"])
        self.assertEqual(set(gh.contexts), {"ci"})
        self.assertFalse(gh.conversation_resolution)
        # Idempotent the other direction too.
        gh.protect_put = None
        result2 = review_gate.protect(gh, remove=True)
        self.assertFalse(result2["changed"])
        self.assertIsNone(gh.protect_put)

    def test_idempotent_requires_both_context_and_conversation(self):
        # Context already present but conversation resolution still off — the
        # verb must write to bring conversation resolution on.
        gh = FakeGh(contexts=("ci", "semantic-review"),
                    conversation_resolution=False)
        result = review_gate.protect(gh)
        self.assertTrue(result["changed"])
        self.assertTrue(gh.conversation_resolution)
        self.assertEqual(set(gh.contexts), {"ci", "semantic-review"})

    def test_put_preserves_strict_other_contexts_and_other_fields(self):
        gh = FakeGh(contexts=("ci", "lint"), strict=True)
        review_gate.protect(gh)
        put = gh.protect_put
        self.assertEqual(set(put["required_status_checks"]["contexts"]),
                         {"ci", "lint", "semantic-review"})
        self.assertTrue(put["required_status_checks"]["strict"])
        self.assertTrue(put["required_conversation_resolution"])
        # An unrelated protection field survived the write, translated to the
        # PUT's boolean shape.
        self.assertEqual(put["required_linear_history"], True)
        self.assertEqual(put["enforce_admins"], True)

    def test_output_names_contexts_and_conversation_state(self):
        gh = FakeGh(contexts=("ci",))
        lines = []
        review_gate.protect(gh, out=lines.append)
        text = "\n".join(lines)
        self.assertIn("semantic-review", text)
        self.assertIn("conversation resolution", text)


def _thread(tid, *, resolved=False, author="gate-bot", created="2024-01-01T00:00:00Z",
            replies=0, root_id=None):
    """Build a FakeGh review-thread dict: a root comment authored by ``author``
    at ``created``, plus ``replies`` follow-up comments."""
    root = {"databaseId": root_id if root_id is not None else 10000 + tid_num(tid),
            "author": author, "createdAt": created}
    comments = [root]
    for i in range(replies):
        comments.append({"databaseId": root["databaseId"] + 1 + i,
                         "author": author, "createdAt": created})
    return {"id": "T%s" % tid, "isResolved": resolved, "comments": comments}


def tid_num(tid):
    try:
        return int(tid)
    except (TypeError, ValueError):
        return abs(hash(tid)) % 1000


def _run_main(argv, gh):
    """Run the CLI ``main`` with a fake gh, capturing (exit_code, stdout)."""
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = review_gate.main(argv, gh=gh)
    return code, buf.getvalue()


class ReplyTest(unittest.TestCase):
    def test_reply_posts_in_reply_to_and_prints_url(self):
        # A gate-authored thread rooted at review comment 12345.
        threads = [_thread(1, author="gate-bot", root_id=12345)]
        gh = FakeGh(review_threads=threads)
        result = review_gate.reply("7", 12345, "Deferred: pagination cap is "
                                   "documented", gh)
        # The reply landed on that root comment via in_reply_to ...
        self.assertEqual(len(gh.reply_posts), 1)
        self.assertEqual(gh.reply_posts[0]["in_reply_to_id"], 12345)
        # ... the thread grew a second comment, and the URL is returned.
        self.assertEqual(len(threads_from(gh, "T1")["comments"]), 2)
        self.assertTrue(result["url"])
        self.assertIn("discussion_r", result["url"])

    def test_reply_to_unknown_comment_exits_nonzero(self):
        gh = FakeGh(review_threads=[_thread(1, root_id=12345)])
        code, _out = _run_main(["reply", "7", "99999", "--body", "x"], gh)
        self.assertNotEqual(code, 0)


    def test_reply_with_non_numeric_comment_id_fails_cleanly(self):
        gh = FakeGh(review_threads=[_thread(1, root_id=12345)])
        code, _out = _run_main(["reply", "7", "abc", "--body", "x"], gh)
        self.assertNotEqual(code, 0)


def threads_from(gh, tid):
    return next(t for t in gh.threads if t["id"] == tid)


class ResolveTest(unittest.TestCase):
    def test_resolves_gate_thread_with_a_reply(self):
        threads = [_thread(1, author="gate-bot", replies=1)]
        gh = FakeGh(review_threads=threads)
        result = review_gate.resolve("7", gh)
        self.assertEqual(gh.resolved_thread_ids, ["T1"])
        self.assertEqual(result["unresolved"], 0)
        self.assertEqual(result["undispositioned"], [])

    def test_resolves_gate_thread_with_a_later_commit(self):
        # One comment, no reply, but the PR gained a commit after the thread.
        threads = [_thread(1, author="gate-bot",
                           created="2024-01-01T00:00:00Z", replies=0)]
        gh = FakeGh(review_threads=threads,
                    commits=["2024-02-01T00:00:00Z"])
        result = review_gate.resolve("7", gh)
        self.assertEqual(gh.resolved_thread_ids, ["T1"])
        self.assertEqual(result["unresolved"], 0)

    def test_refuses_undispositioned_thread(self):
        # One comment, no reply, and no commit after the thread's creation.
        threads = [_thread(1, author="gate-bot",
                           created="2024-03-01T00:00:00Z", replies=0)]
        gh = FakeGh(review_threads=threads,
                    commits=["2024-01-01T00:00:00Z"])
        code, out = _run_main(["resolve", "7"], gh)
        self.assertNotEqual(code, 0)                 # non-zero exit
        self.assertEqual(gh.resolved_thread_ids, [])  # nothing resolved
        self.assertIn("T1", out)                      # listed as undispositioned
        self.assertIn("unresolved=1", out)

    def test_never_touches_human_authored_threads(self):
        threads = [_thread(1, author="a-human", replies=1, resolved=False)]
        gh = FakeGh(review_threads=threads)
        result = review_gate.resolve("7", gh)
        self.assertEqual(gh.resolved_thread_ids, [])  # human thread untouched
        self.assertEqual(result["unresolved"], 0)      # and not counted

    def test_offset_commit_before_thread_is_not_evidence(self):
        # committedDate is a GitTimestamp and keeps the commit's local offset:
        # 13:00+02:00 is 11:00Z, BEFORE the 12:00Z thread, yet the raw string
        # compares as later. The parsed comparison must refuse it as evidence.
        threads = [_thread(1, author="gate-bot",
                           created="2024-01-01T12:00:00Z", replies=0)]
        gh = FakeGh(review_threads=threads,
                    commits=["2024-01-01T13:00:00+02:00"])
        result = review_gate.resolve("7", gh)
        self.assertEqual(gh.resolved_thread_ids, [])
        self.assertEqual(result["unresolved"], 1)

    def test_offset_commit_after_thread_is_evidence(self):
        # 15:00+02:00 is 13:00Z — genuinely after the 12:00Z thread.
        threads = [_thread(1, author="gate-bot",
                           created="2024-01-01T12:00:00Z", replies=0)]
        gh = FakeGh(review_threads=threads,
                    commits=["2024-01-01T15:00:00+02:00"])
        result = review_gate.resolve("7", gh)
        self.assertEqual(gh.resolved_thread_ids, ["T1"])
        self.assertEqual(result["unresolved"], 0)

    def test_check_counts_without_mutating(self):
        threads = [_thread(1, author="gate-bot", replies=0),
                   _thread(2, author="gate-bot", replies=0),
                   _thread(3, author="a-human", replies=0)]
        gh = FakeGh(review_threads=threads)
        code, out = _run_main(["resolve", "7", "--check"], gh)
        self.assertIn("unresolved=2", out)             # two gate threads open
        self.assertNotEqual(code, 0)                   # non-zero above zero
        self.assertEqual(gh.resolved_thread_ids, [])   # --check mutates nothing

    def test_check_exits_zero_only_at_zero(self):
        threads = [_thread(1, author="gate-bot", replies=1, resolved=True)]
        gh = FakeGh(review_threads=threads)
        code, out = _run_main(["resolve", "7", "--check"], gh)
        self.assertIn("unresolved=0", out)
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
