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


MARKER = "<!-- shipd-semantic-review -->"
LEGACY_MARKER = "<!-- am-semantic-review -->"


class FakeGh:
    """A stateful fake of the ``gh`` CLI seam.

    Call signature mirrors the production runner: ``gh(args, input=None) ->
    (returncode, stdout, stderr)`` where ``args`` is everything after ``gh``.
    """

    def __init__(self, *, head_sha="abc123", number=7, repo="o/r",
                 pr_url="https://github.com/o/r/pull/7",
                 default_branch="main", contexts=("ci",),
                 conversation_resolution=False, strict=True,
                 protection_get_error=None, also_checks=False,
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
        # GitHub's real GET response carries both the legacy ``contexts`` list
        # and the ``checks`` list it derives from a write, alongside each
        # other — never only one. ``also_checks`` reproduces that shape so a
        # test can pin that the reader (which takes ``contexts``) still works
        # once the writer stops sending it.
        self.also_checks = also_checks
        # When set, a ``(rc, stdout, stderr)`` triple the protection GET answers
        # with instead of a protection object — how an unprotected branch (404)
        # or a denied read (403) looks at this seam. A successful PUT clears it:
        # the branch is protected from then on.
        self.protection_get_error = protection_get_error
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
                     "createdAt": c["createdAt"],
                     "body": c.get("body", "")}
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
                 "createdAt": "2099-01-01T00:00:00Z",
                 "body": payload["body"]})
            reply = {"id": cid, "in_reply_to_id": root_id,
                     "html_url": "%s#discussion_r%d" % (self.pr_url, cid),
                     "body": payload["body"]}
            self.reply_posts.append(reply)
            return 0, json.dumps(reply), ""

        if path.endswith("/protection"):
            if method == "GET":
                if self.protection_get_error is not None:
                    return self.protection_get_error
                # A nested GET-shaped protection object, including a field the
                # verb must preserve untouched across the write.
                rsc = {"strict": self.strict, "contexts": list(self.contexts)}
                if self.also_checks:
                    rsc["checks"] = [{"context": c, "app_id": None}
                                     for c in self.contexts]
                return 0, json.dumps({
                    "required_status_checks": rsc,
                    "required_conversation_resolution": {
                        "enabled": self.conversation_resolution},
                    "enforce_admins": {"enabled": True},
                    "required_linear_history": {"enabled": True}}), ""
            if method == "PUT":
                payload = json.loads(input)
                self.protect_put = payload
                rsc = payload.get("required_status_checks") or {}
                self.contexts = tuple(c["context"] for c in rsc.get("checks") or [])
                self.strict = bool(rsc.get("strict", self.strict))
                self.conversation_resolution = bool(
                    payload.get("required_conversation_resolution"))
                self.protection_get_error = None
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
        # Either marker identifies a gate summary comment: a PR predating the
        # rename still carries the legacy one until the next upsert rewrites it.
        return [c for c in self._comments
                if MARKER in c["body"] or LEGACY_MARKER in c["body"]]

    def summary_body(self):
        marked = self.marker_comments()
        return marked[-1]["body"] if marked else None

    def comment_patch_calls(self):
        return [(a, i) for a, i in self.calls
                if a[0] == "api" and "/issues/comments/" in a[1]
                and "-X" in a and a[a.index("-X") + 1] == "PATCH"]

    def comment_create_calls(self):
        """The POST creates of a new issue comment (the non-upsert path)."""
        return [(a, i) for a, i in self.calls
                if a[0] == "api" and a[1].split("?", 1)[0].endswith("/comments")
                and "/issues/" in a[1]
                and "-X" in a and a[a.index("-X") + 1] == "POST"]


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


class SummaryBrandTest(unittest.TestCase):
    """The summary body opens its visible content with the ☕ brand line, while
    the hidden marker line stays byte-identical so upsert matching is unmoved."""

    BRAND = "**☕ shipd** semantic review"

    def _lines(self, review, unanchored=(), **kw):
        return review_gate.render_summary(review, list(unanchored), **kw).split("\n")

    def test_brand_line_precedes_verdict_header(self):
        for verdict in ("pass", "changes-requested"):
            lines = self._lines(_review(verdict=verdict))
            self.assertEqual(lines[0], MARKER)
            rest = [ln for ln in lines[1:] if ln.strip()]
            self.assertEqual(rest[0], self.BRAND)
            self.assertTrue(rest[1].startswith("## Findings:"))

    def test_brand_line_survives_disposition_and_model(self):
        findings = [{"id": "f1", "severity": "high", "location": "z.py:1",
                     "what": "boom", "why": "w", "fix": "x"}]
        lines = self._lines(_review(verdict="changes-requested",
                                    findings=findings),
                            unanchored=findings,
                            disposition="high-only", model="opus")
        self.assertEqual(lines[0], MARKER)
        rest = [ln for ln in lines[1:] if ln.strip()]
        self.assertEqual(rest[0], self.BRAND)
        self.assertTrue(rest[1].startswith("## Findings:"))

    def test_posted_and_reposted_bodies_both_carry_the_brand(self):
        gh = FakeGh()
        review_gate.post("7", _review(verdict="pass"), gh)
        self.assertIn(self.BRAND, gh.summary_body())
        review_gate.post("7", _review(verdict="pass"), gh)
        self.assertTrue(gh.comment_patch_calls())
        self.assertIn(self.BRAND, gh.summary_body())
        # The machine surfaces stay unbranded.
        self.assertEqual(gh.posted_status["context"], "semantic-review")
        self.assertNotIn("☕", gh.posted_status["context"])
        self.assertNotIn("☕", MARKER)


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


SUGGESTION_FENCE = "```suggestion"


def _finding(location="a.py:5", *, severity="high", what="boom",
             suggestion=None):
    f = {"id": "f1", "severity": severity, "location": location,
         "what": what, "why": "w", "fix": "x"}
    if suggestion is not None:
        f["suggestion"] = suggestion
    return f


def _post_finding(finding, files=None):
    """Post a one-finding red review and hand back the fake, so every
    suggestion assertion runs through the real eligibility gate rather than a
    hand-built call to the renderer."""
    gh = FakeGh(files=files if files is not None
                else [{"filename": "a.py", "patch": PATCH_A}])
    review_gate.post(
        "7", _review(verdict="changes-requested", findings=[finding]), gh)
    return gh


def _inline_comments(gh):
    return gh.review_posts[0]["comments"] if gh.review_posts else []


class SuggestionTest(unittest.TestCase):
    """A confident, contiguous whole-line replacement that anchors carries a
    committable ```suggestion block; every other shape degrades to prose."""

    # The eligible shape the degradation cases below vary one field of.
    OK = {"confident": True, "start_line": 5, "end_line": 5,
          "lines": ["    return None"]}

    def _degrades(self, suggestion):
        """Assert a suggestion shape still renders an ordinary inline comment:
        prose, today's single-line anchor, and no fenced block."""
        comment = _inline_comments(_post_finding(_finding(
            suggestion=suggestion)))[0]
        self.assertNotIn(SUGGESTION_FENCE, comment["body"])
        self.assertEqual((comment["path"], comment["line"]), ("a.py", 5))
        self.assertNotIn("start_line", comment)

    def test_confident_whole_line_fix_becomes_committable(self):
        comment = _inline_comments(_post_finding(_finding(
            suggestion=dict(self.OK))))[0]
        self.assertIn("```suggestion\n    return None\n```", comment["body"])
        # A single-line replacement keeps the single-`line` anchor shape.
        self.assertEqual((comment["path"], comment["line"]), ("a.py", 5))
        self.assertEqual(comment["side"], "RIGHT")

    def test_multi_line_replacement_carries_every_line(self):
        comment = _inline_comments(_post_finding(_finding(suggestion={
            "confident": True, "start_line": 3, "end_line": 5,
            "lines": ["one", "two", "three"]})))[0]
        self.assertIn("```suggestion\none\ntwo\nthree\n```", comment["body"])
        # The comment spans the replaced range: GitHub applies a suggestion to
        # the lines its comment covers.
        self.assertEqual((comment["start_line"], comment["line"]), (3, 5))
        self.assertEqual((comment["start_side"], comment["side"]),
                         ("RIGHT", "RIGHT"))

    def test_a_replacement_may_change_the_line_count(self):
        # len(lines) need not equal the range: a fix may add or remove lines.
        comment = _inline_comments(_post_finding(_finding(suggestion={
            "confident": True, "start_line": 3, "end_line": 5,
            "lines": ["collapsed"]})))[0]
        self.assertIn("```suggestion\ncollapsed\n```", comment["body"])
        self.assertEqual((comment["start_line"], comment["line"]), (3, 5))

    def test_unanchorable_confident_fix_is_folded_and_carries_no_suggestion(
            self):
        gh = _post_finding(_finding(location="b.py:99", suggestion={
            "confident": True, "start_line": 99, "end_line": 99,
            "lines": ["fixed"]}))
        self.assertEqual(_inline_comments(gh), [])
        body = gh.summary_body()
        self.assertIn("Additional findings", body)
        self.assertNotIn(SUGGESTION_FENCE, body)

    def test_partial_line_replacement_renders_no_suggestion(self):
        # A column key declares an edit inside a line, which a whole-line
        # suggestion cannot express.
        self._degrades(dict(self.OK, start_column=4, end_column=12))
        self._degrades(dict(self.OK, end_column=12))

    def test_unconfident_replacement_renders_no_suggestion(self):
        self._degrades(dict(self.OK, confident=False))
        self._degrades({k: v for k, v in self.OK.items() if k != "confident"})
        self._degrades(dict(self.OK, confident="true"))

    def test_malformed_or_discontiguous_ranges_render_no_suggestion(self):
        self._degrades({k: v for k, v in self.OK.items() if k != "lines"})
        self._degrades(dict(self.OK, lines=[]))
        self._degrades(dict(self.OK, lines="one line"))
        self._degrades(dict(self.OK, start_line=5, end_line=3))
        self._degrades(dict(self.OK, start_line="5"))
        self._degrades({k: v for k, v in self.OK.items() if k != "end_line"})

    def test_a_range_leaving_the_diff_renders_no_suggestion(self):
        # PATCH_A makes a.py:1–5 commentable; 6 and 7 are outside it, and a
        # comment spanning them would be rejected by GitHub outright.
        self._degrades(dict(self.OK, start_line=5, end_line=7))

    def test_suggestion_body_still_opens_with_the_severity_marker(self):
        for sev in ("high", "medium", "low"):
            comment = _inline_comments(_post_finding(_finding(
                severity=sev, suggestion=dict(self.OK))))[0]
            self.assertIn(SUGGESTION_FENCE, comment["body"])
            self.assertEqual(review_gate.parse_severity(comment["body"]), sev)

    def test_a_finding_without_a_suggestion_is_unchanged(self):
        comment = _inline_comments(_post_finding(_finding()))[0]
        self.assertNotIn(SUGGESTION_FENCE, comment["body"])
        self.assertEqual((comment["path"], comment["line"]), ("a.py", 5))
        self.assertNotIn("start_line", comment)


class ReviewEventTest(unittest.TestCase):
    """Every review this poster submits is a `COMMENT`. The required
    `semantic-review` status is the merge blocker; a `REQUEST_CHANGES` decision
    would need a human dismissal even after the fix landed, so the event is
    pinned here and cannot drift silently."""

    FINDINGS = [
        _finding(location="a.py:5"),
        _finding(location="b.py:99", severity="medium", what="out of diff"),
        _finding(location="a.py:3", severity="low", what="fixable",
                 suggestion={"confident": True, "start_line": 3,
                             "end_line": 4, "lines": ["one", "two"]}),
    ]

    def _events(self, gh):
        return [p["event"] for p in gh.review_posts]

    def test_the_constant_is_comment(self):
        self.assertEqual(review_gate.REVIEW_EVENT, "COMMENT")

    def test_every_posted_review_submits_comment(self):
        gh = FakeGh(files=[{"filename": "a.py", "patch": PATCH_A}])
        review_gate.post("7", _review(verdict="changes-requested",
                                      findings=self.FINDINGS), gh)
        self.assertEqual(self._events(gh), ["COMMENT"])

    def test_the_retry_without_inline_is_also_a_comment(self):
        gh = FakeGh(files=[{"filename": "a.py", "patch": PATCH_A}],
                    review_fail_times=1)
        review_gate.post("7", _review(verdict="changes-requested",
                                      findings=self.FINDINGS), gh)
        self.assertEqual(self._events(gh), ["COMMENT", "COMMENT"])

    def test_no_disposition_scope_changes_the_event(self):
        for scope in review_gate.DISPOSITIONS:
            gh = FakeGh(files=[{"filename": "a.py", "patch": PATCH_A}])
            review_gate.post("7", _review(verdict="changes-requested",
                                          findings=self.FINDINGS), gh,
                             disposition=scope)
            self.assertEqual(self._events(gh), ["COMMENT"], scope)


class PostDispositionTest(unittest.TestCase):
    """`post --disposition <scope>` maps the commit status by merge policy while
    the summary body and verdict stay severity-honest."""

    HIGH = {"id": "f1", "severity": "high", "location": "z.py:1",
            "what": "high boom", "why": "w", "fix": "x"}
    MEDIUM = {"id": "f2", "severity": "medium", "location": "z.py:2",
              "what": "medium boom", "why": "w", "fix": "x"}
    LOW = {"id": "f3", "severity": "low", "location": "z.py:3",
           "what": "low boom", "why": "w", "fix": "x"}

    def test_all_scope_keeps_verdict_mapping(self):
        gh = FakeGh()
        review_gate.post("7", _review(verdict="pass"), gh, disposition="all")
        self.assertEqual(gh.posted_status["state"], "success")

        gh = FakeGh()
        review_gate.post("7", _review(verdict="changes-requested",
                                      findings=[self.MEDIUM]), gh,
                         disposition="all")
        self.assertEqual(gh.posted_status["state"], "failure")

    def test_omitted_scope_defaults_to_all(self):
        gh = FakeGh()
        review_gate.post(
            "7", _review(verdict="changes-requested", findings=[self.LOW]), gh)
        self.assertEqual(gh.posted_status["state"], "failure")
        # Default scope leaves the summary free of policy provenance.
        self.assertNotIn("Disposition:", gh.summary_body())
        self.assertNotIn("Model:", gh.summary_body())

    def test_high_only_greens_over_medium_and_low(self):
        gh = FakeGh()
        result = review_gate.post(
            "7", _review(verdict="changes-requested",
                         findings=[self.MEDIUM, self.LOW]), gh,
            disposition="high-only")
        self.assertEqual(gh.posted_status["state"], "success")
        self.assertEqual(result["state"], "success")
        # The status description names the acting scope ...
        self.assertIn("high-only", gh.posted_status["description"])
        # ... and the summary stays severity-honest about the findings.
        body = gh.summary_body()
        self.assertIn("Disposition: high-only", body)
        self.assertIn("medium boom", body)
        self.assertIn("low boom", body)
        self.assertIn("Fix required", body)

    def test_high_only_stays_red_on_a_high(self):
        gh = FakeGh()
        review_gate.post(
            "7", _review(verdict="changes-requested",
                         findings=[self.HIGH, self.MEDIUM]), gh,
            disposition="high-only")
        self.assertEqual(gh.posted_status["state"], "failure")
        self.assertIn("Disposition: high-only", gh.summary_body())

    def test_none_is_always_green_and_stays_honest(self):
        gh = FakeGh()
        review_gate.post(
            "7", _review(verdict="changes-requested", findings=[self.HIGH]),
            gh, disposition="none", model="tier-below")
        self.assertEqual(gh.posted_status["state"], "success")
        self.assertIn("none", gh.posted_status["description"])
        body = gh.summary_body()
        self.assertIn("high boom", body)          # the finding is still there
        self.assertIn("Disposition: none", body)
        self.assertIn("Model: tier-below", body)

    def test_model_recorded_verbatim_and_absent_when_omitted(self):
        gh = FakeGh()
        review_gate.post("7", _review(verdict="pass"), gh, model="tier-below")
        self.assertIn("Model: tier-below", gh.summary_body())

        gh = FakeGh()
        review_gate.post("7", _review(verdict="pass"), gh)
        self.assertNotIn("Model:", gh.summary_body())

    def test_cli_passes_disposition_and_model_through(self):
        import tempfile
        gh = FakeGh()
        with tempfile.NamedTemporaryFile("w", suffix=".json",
                                         delete=False) as fh:
            json.dump(_review(verdict="changes-requested",
                              findings=[self.MEDIUM]), fh)
            path = fh.name
        try:
            code, out = _run_main(
                ["post", "7", "--from", path,
                 "--disposition", "high-only", "--model", "tier-two-below"], gh)
        finally:
            os.unlink(path)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["state"], "success")
        self.assertEqual(gh.posted_status["state"], "success")
        self.assertIn("Model: tier-two-below", gh.summary_body())


class ProtectionPutBodyTest(unittest.TestCase):
    """`_protection_put_body` writes `checks`, not the legacy `contexts` field,
    so a status posted by any source — including a human, not only the app
    pinned to a `contexts` entry — can satisfy the required check."""

    def test_the_write_carries_checks_with_a_null_app_id_and_no_contexts(self):
        current = {"required_status_checks": {"strict": True,
                                               "contexts": ["ci"]}}
        body = review_gate._protection_put_body(
            current, ["ci", "semantic-review"], True)
        rsc = body["required_status_checks"]
        self.assertNotIn("contexts", rsc)
        checks = {c["context"]: c["app_id"] for c in rsc["checks"]}
        self.assertEqual(checks, {"ci": None, "semantic-review": None})

    def test_strict_and_other_fields_are_still_preserved(self):
        current = {"required_status_checks": {"strict": True,
                                               "contexts": ["ci", "lint"]},
                  "enforce_admins": {"enabled": True},
                  "required_linear_history": {"enabled": True}}
        body = review_gate._protection_put_body(
            current, ["ci", "lint", "semantic-review"], True)
        rsc = body["required_status_checks"]
        self.assertTrue(rsc["strict"])
        self.assertEqual({c["context"] for c in rsc["checks"]},
                         {"ci", "lint", "semantic-review"})
        self.assertTrue(body["required_conversation_resolution"])
        self.assertEqual(body["enforce_admins"], True)
        self.assertEqual(body["required_linear_history"], True)

    def test_the_unprotected_branch_creation_path_also_writes_checks(self):
        # `current` is `{}` — an empty protection object — exactly what
        # `protect` builds from when the GET 404s.
        body = review_gate._protection_put_body(
            {}, ["semantic-review"], True, strict_default=False)
        rsc = body["required_status_checks"]
        self.assertNotIn("contexts", rsc)
        self.assertEqual(rsc["checks"], [{"context": "semantic-review",
                                          "app_id": None}])
        self.assertFalse(rsc["strict"])
        self.assertTrue(body["required_conversation_resolution"])


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
        self.assertEqual({c["context"] for c in put["required_status_checks"]["checks"]},
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

    def test_a_get_carrying_both_contexts_and_checks_is_still_idempotent(self):
        # The real GitHub GET response carries `contexts` *and* `checks`
        # alongside each other, not one or the other — confirmed against a
        # live protected branch. The reader (`protect`, at the `contexts` it
        # takes off the GET) is unchanged by this feature and must still see
        # `semantic-review` already required, so this pins that a later
        # reader change cannot silently break idempotence.
        gh = FakeGh(contexts=("ci", "semantic-review"),
                    conversation_resolution=True, also_checks=True)
        result = review_gate.protect(gh)
        self.assertFalse(result["changed"])
        self.assertIsNone(gh.protect_put)


# How the two protection-read failures look at the ``gh`` seam: an unprotected
# branch answers the read with a 404 naming itself, while any other denial is a
# genuine read failure the verb must not paper over.
NOT_PROTECTED = (1, "", "gh: Branch not protected (HTTP 404)\n")
READ_DENIED = (1, "", "gh: Must have admin rights to Repository. (HTTP 403)\n")


class ProtectUnprotectedBranchTest(unittest.TestCase):
    def test_creates_minimal_protection_on_a_404(self):
        gh = FakeGh(protection_get_error=NOT_PROTECTED)
        result = review_gate.protect(gh)
        self.assertTrue(result["changed"])
        self.assertEqual(result["contexts"], ["semantic-review"])
        self.assertTrue(result["conversation_resolution"])
        put = gh.protect_put
        self.assertEqual(put["required_status_checks"],
                         {"strict": False,
                          "checks": [{"context": "semantic-review",
                                     "app_id": None}]})
        self.assertTrue(put["required_conversation_resolution"])
        # Every other protection field is null (or a bare false), never carried
        # over from a protection object that does not exist.
        self.assertFalse(put["enforce_admins"])
        self.assertIsNone(put["required_pull_request_reviews"])
        self.assertIsNone(put["restrictions"])
        for field in ("required_linear_history", "allow_force_pushes",
                      "allow_deletions", "block_creations",
                      "required_signatures", "lock_branch",
                      "allow_fork_syncing"):
            self.assertNotIn(field, put)

    def test_creation_prints_the_resulting_state(self):
        gh = FakeGh(protection_get_error=NOT_PROTECTED)
        lines = []
        review_gate.protect(gh, out=lines.append)
        text = "\n".join(lines)
        self.assertIn("semantic-review", text)
        self.assertIn("conversation resolution required", text)

    def test_second_run_on_the_now_protected_branch_is_a_no_op(self):
        gh = FakeGh(protection_get_error=NOT_PROTECTED)
        review_gate.protect(gh)
        gh.protect_put = None
        result = review_gate.protect(gh)
        self.assertFalse(result["changed"])
        self.assertIsNone(gh.protect_put)

    def test_remove_on_an_unprotected_branch_writes_nothing(self):
        gh = FakeGh(protection_get_error=NOT_PROTECTED)
        result = review_gate.protect(gh, remove=True)
        self.assertFalse(result["changed"])
        self.assertIsNone(gh.protect_put)

    def test_other_read_failures_still_fail_without_writing(self):
        gh = FakeGh(protection_get_error=READ_DENIED)
        with self.assertRaises(review_gate.ReviewGateError) as caught:
            review_gate.protect(gh)
        self.assertIn("HTTP 403", str(caught.exception))
        self.assertIsNone(gh.protect_put)

    def test_existing_protection_keeps_its_strict_setting(self):
        # The creation default (strict false) must not leak onto a branch that
        # is already protected — that path preserves what it read.
        gh = FakeGh(contexts=("ci",), strict=True)
        review_gate.protect(gh)
        self.assertTrue(gh.protect_put["required_status_checks"]["strict"])


def _thread(tid, *, resolved=False, author="gate-bot", created="2024-01-01T00:00:00Z",
            replies=0, root_id=None, body=""):
    """Build a FakeGh review-thread dict: a root comment authored by ``author``
    at ``created`` carrying ``body``, plus ``replies`` follow-up comments."""
    root = {"databaseId": root_id if root_id is not None else 10000 + tid_num(tid),
            "author": author, "createdAt": created, "body": body}
    comments = [root]
    for i in range(replies):
        comments.append({"databaseId": root["databaseId"] + 1 + i,
                         "author": author, "createdAt": created,
                         "body": "a reply"})
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


def _gate_thread(tid, severity, *, what="boom", **kw):
    """A gate-authored thread whose root body is what the poster would render
    for a finding of ``severity`` — so the parser is exercised against the real
    renderer, never a hand-written imitation."""
    body = review_gate._inline_body(
        {"severity": severity, "what": what, "why": "w", "fix": "x"})
    return _thread(tid, body=body, **kw)


class SeverityParseTest(unittest.TestCase):
    def test_round_trips_every_rendered_severity(self):
        for sev in ("high", "medium", "low"):
            body = review_gate._inline_body(
                {"severity": sev, "what": "something", "why": "w", "fix": "x"})
            self.assertEqual(review_gate.parse_severity(body), sev)

    def test_unparseable_body_yields_none(self):
        self.assertIsNone(review_gate.parse_severity("just some prose"))
        self.assertIsNone(review_gate.parse_severity(""))


class AutoreplyTest(unittest.TestCase):
    def test_high_only_replies_below_the_threshold(self):
        threads = [_gate_thread(1, "high"), _gate_thread(2, "medium"),
                   _gate_thread(3, "low")]
        gh = FakeGh(review_threads=threads)
        result = review_gate.autoreply("7", gh, "high-only")
        self.assertEqual(result["replied"], 2)
        # The high thread keeps its lone root comment; the others gained one.
        self.assertEqual(len(threads_from(gh, "T1")["comments"]), 1)
        self.assertEqual(len(threads_from(gh, "T2")["comments"]), 2)
        self.assertEqual(len(threads_from(gh, "T3")["comments"]), 2)
        # Each reply names the acting policy scope.
        for reply in gh.reply_posts:
            self.assertIn("high-only", reply["body"])

    def test_high_only_prints_replied_count(self):
        threads = [_gate_thread(1, "high"), _gate_thread(2, "medium"),
                   _gate_thread(3, "low")]
        gh = FakeGh(review_threads=threads)
        code, out = _run_main(
            ["autoreply", "7", "--disposition", "high-only"], gh)
        self.assertEqual(code, 0)
        self.assertIn("replied=2", out)

    def test_none_replies_to_every_gate_thread(self):
        threads = [_gate_thread(1, "high"), _gate_thread(2, "medium"),
                   _gate_thread(3, "low")]
        gh = FakeGh(review_threads=threads)
        code, out = _run_main(["autoreply", "7", "--disposition", "none"], gh)
        self.assertEqual(code, 0)
        self.assertIn("replied=3", out)
        for tid in ("T1", "T2", "T3"):
            self.assertEqual(len(threads_from(gh, tid)["comments"]), 2)

    def test_none_replies_to_an_unparseable_root_too(self):
        # Under `none` severity is never consulted, so a body the parser cannot
        # read is still covered.
        threads = [_thread(1, body="free-form prose with no marker")]
        gh = FakeGh(review_threads=threads)
        result = review_gate.autoreply("7", gh, "none")
        self.assertEqual(result["replied"], 1)

    def test_rerun_is_idempotent(self):
        threads = [_gate_thread(1, "medium"), _gate_thread(2, "low")]
        gh = FakeGh(review_threads=threads)
        review_gate.autoreply("7", gh, "none")
        code, out = _run_main(["autoreply", "7", "--disposition", "none"], gh)
        self.assertEqual(code, 0)
        self.assertIn("replied=0", out)
        # No thread grew a second reply.
        self.assertEqual(len(threads_from(gh, "T1")["comments"]), 2)
        self.assertEqual(len(threads_from(gh, "T2")["comments"]), 2)

    def test_unparseable_root_is_left_for_judgment(self):
        threads = [_thread(1, body="free-form prose with no marker"),
                   _gate_thread(2, "low")]
        gh = FakeGh(review_threads=threads)
        lines = []
        result = review_gate.autoreply("7", gh, "high-only", out=lines.append)
        self.assertEqual(result["replied"], 1)
        self.assertEqual(result["unparsed"], ["T1"])
        self.assertEqual(len(threads_from(gh, "T1")["comments"]), 1)
        self.assertIn("T1", "\n".join(lines))
        self.assertIn("unparsed", "\n".join(lines))

    def test_never_touches_human_or_resolved_threads(self):
        threads = [_gate_thread(1, "medium", author="a-human"),
                   _gate_thread(2, "medium", resolved=True),
                   _gate_thread(3, "medium", replies=1)]
        gh = FakeGh(review_threads=threads)
        result = review_gate.autoreply("7", gh, "none")
        self.assertEqual(result["replied"], 0)
        self.assertEqual(gh.reply_posts, [])
        self.assertEqual(len(threads_from(gh, "T1")["comments"]), 1)
        self.assertEqual(len(threads_from(gh, "T2")["comments"]), 1)
        self.assertEqual(len(threads_from(gh, "T3")["comments"]), 2)

    def test_body_override_replaces_the_canonical_text(self):
        gh = FakeGh(review_threads=[_gate_thread(1, "low")])
        code, _out = _run_main(
            ["autoreply", "7", "--disposition", "none", "--body", "custom text"],
            gh)
        self.assertEqual(code, 0)
        self.assertEqual(gh.reply_posts[0]["body"], "custom text")

    def test_all_scope_is_rejected_by_the_cli(self):
        # `all` means per-finding judgment; there is nothing to auto-reply.
        gh = FakeGh(review_threads=[_gate_thread(1, "low")])
        with self.assertRaises(SystemExit):
            _run_main(["autoreply", "7", "--disposition", "all"], gh)


class MarkerMigrationTest(unittest.TestCase):
    """The hidden gate marker is `<!-- shipd-semantic-review -->`; the legacy
    `<!-- am-semantic-review -->` is still recognized on every read so a PR that
    predates the rename is edited in place, never duplicated."""

    def test_render_summary_opens_with_the_current_marker(self):
        body = review_gate.render_summary(_review(verdict="pass"), [])
        self.assertEqual(body.split("\n")[0], MARKER)
        self.assertNotIn(LEGACY_MARKER, body)

    def test_legacy_summary_is_patched_not_duplicated(self):
        legacy = {"id": 42,
                  "body": LEGACY_MARKER + "\n\n## Findings: ✅ Ship it\n",
                  "html_url": "https://github.com/o/r/pull/7#issuecomment-42"}
        gh = FakeGh(existing_comments=[legacy])
        review_gate.post("7", _review(verdict="pass"), gh)
        # The pre-rename comment was edited in place — no second summary POSTed.
        self.assertTrue(gh.comment_patch_calls())
        self.assertEqual(gh.comment_create_calls(), [])
        self.assertEqual(len(gh.marker_comments()), 1)
        # ... and the edited body now opens with the current marker only.
        body = gh.summary_body()
        self.assertEqual(body.split("\n")[0], MARKER)
        self.assertNotIn(LEGACY_MARKER, body)

    def test_resolve_recognizes_a_legacy_marker_rooted_thread(self):
        threads = [_thread(1, author="gate-bot", replies=1,
                           body=LEGACY_MARKER + "\n\n**high — boom**")]
        gh = FakeGh(review_threads=threads)
        result = review_gate.resolve("7", gh)
        self.assertEqual(gh.resolved_thread_ids, ["T1"])
        self.assertEqual(result["unresolved"], 0)

    def test_autoreply_recognizes_a_legacy_marker_rooted_thread(self):
        threads = [_thread(1, author="gate-bot",
                           body=LEGACY_MARKER + "\n\n**low — boom**")]
        gh = FakeGh(review_threads=threads)
        result = review_gate.autoreply("7", gh, "none")
        self.assertEqual(result["replied"], 1)
        self.assertEqual(len(threads_from(gh, "T1")["comments"]), 2)


if __name__ == "__main__":
    unittest.main()
