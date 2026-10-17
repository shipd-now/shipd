"""Tests for tools/team_merge_test.py, the unkannybanny merge-rules proof
driver. A fake ``Gh`` runner stands in for GitHub: no test touches a network."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import team_merge_test as tmt  # noqa: E402

REPO = tmt.ALLOWED_REPO
SECRET = "tok-SECRET-value-123"
ENV_OK = {"TEAM_TEST_REVIEWER_GH_TOKEN": SECRET}


class FakeGh(tmt.Gh):
    """A ``Gh`` whose subprocess seam is a handler ``(argv, who) -> (code,
    out, err)``; every call is recorded."""

    def __init__(self, handler=None, environ=None):
        super().__init__(environ=ENV_OK if environ is None else environ)
        self.handler = handler or (lambda argv, who: (0, "", ""))
        self.calls = []

    def exec(self, argv, who="author", stdin=None, cwd=None):
        self.calls.append((list(argv), who))
        return self.handler(list(argv), who)


def joined(argv):
    return " ".join(argv)


def good_handler(argv, who):
    """Every preflight prerequisite satisfied."""
    text = joined(argv)
    if argv[:3] == ["gh", "api", "user"]:
        return (0, "mikkel-bergmann\n" if who == "author" else "shipd-now\n", "")
    if "collaborators/shipd-now/permission" in text:
        return (0, "write\n", "")
    if "actions/permissions/workflow" in text:
        return (0, json.dumps({"can_approve_pull_request_reviews": True}), "")
    if "actions/secrets" in text:
        return (0, "COPILOT_GITHUB_TOKEN\n", "")
    if "copilot-review-gate.yml" in text:
        return (0, "env:\n  PR_AUTHOR: ${{ x }}\n", "")
    if ".shipd-config.json" in text:
        return (0, json.dumps({"merge": {"approvals": 2}}), "")
    return (1, "", "unexpected: " + text)


class RepoRefusalTest(unittest.TestCase):
    def test_other_repo_exits_2_before_any_call(self):
        gh = FakeGh(good_handler)
        lines = []
        code = tmt.main(["preflight", "--repo", "mikkel-bergmann/shipd"],
                        gh=gh, out=lines.append)
        self.assertEqual(code, 2)
        self.assertEqual(gh.calls, [])

    def test_every_verb_refuses_other_repo(self):
        for verb in ("preflight", "apply", "run", "report"):
            gh = FakeGh(good_handler)
            code = tmt.main([verb, "--repo", "shipd-now/shipd"],
                            gh=gh, out=lambda _l: None)
            self.assertEqual(code, 2, verb)
            self.assertEqual(gh.calls, [], verb)


class PreflightTest(unittest.TestCase):
    def test_all_ok_exits_0(self):
        gh = FakeGh(good_handler)
        lines = []
        code = tmt.main(["preflight"], gh=gh, out=lines.append)
        self.assertEqual(code, 0, lines)
        self.assertTrue(all(l.startswith("ok ") for l in lines), lines)

    def test_unset_reviewer_env_is_missing_and_exits_3(self):
        gh = FakeGh(good_handler, environ={})
        lines = []
        code = tmt.main(["preflight", "--only", "user"], gh=gh, out=lines.append)
        self.assertEqual(code, 3)
        self.assertTrue(any(l.startswith("missing reviewer-env - ")
                            for l in lines), lines)

    def test_non_collaborator_and_actions_false_are_missing(self):
        def handler(argv, who):
            text = joined(argv)
            if "collaborators/shipd-now/permission" in text:
                return (0, "read\n", "")
            if "actions/permissions/workflow" in text:
                return (0, json.dumps({"can_approve_pull_request_reviews": False}), "")
            return good_handler(argv, who)
        lines = []
        code = tmt.main(["preflight", "--only", "user"], gh=FakeGh(handler),
                        out=lines.append)
        self.assertEqual(code, 3)
        names = [l.split()[1] for l in lines if l.startswith("missing ")]
        self.assertIn("reviewer-collaborator", names)
        self.assertIn("actions-approve", names)

    def test_same_login_is_missing(self):
        def handler(argv, who):
            if argv[:3] == ["gh", "api", "user"]:
                return (0, "mikkel-bergmann\n", "")
            return good_handler(argv, who)
        lines = []
        code = tmt.main(["preflight", "--only", "user"], gh=FakeGh(handler),
                        out=lines.append)
        self.assertEqual(code, 3)
        self.assertTrue(any(l.startswith("missing reviewer-login") for l in lines))

    def test_repo_prep_missing_lines(self):
        def handler(argv, who):
            text = joined(argv)
            if "actions/secrets" in text:
                return (0, "", "")
            if "copilot-review-gate.yml" in text:
                return (1, "", "Not Found")
            if ".shipd-config.json" in text:
                return (0, json.dumps({"valid_themes": []}), "")
            return good_handler(argv, who)
        lines = []
        code = tmt.main(["preflight", "--only", "repo"], gh=FakeGh(handler),
                        out=lines.append)
        self.assertEqual(code, 3)
        names = {l.split()[1] for l in lines if l.startswith("missing ")}
        self.assertEqual(names, {"copilot-secret", "gate-workflow", "merge-block"})

    def test_token_never_printed(self):
        lines = []
        tmt.main(["preflight"], gh=FakeGh(good_handler), out=lines.append)
        self.assertNotIn(SECRET, "\n".join(lines))


class HelperTest(unittest.TestCase):
    def test_redact_replaces_secret_and_token_shapes(self):
        text = "a %s b ghp_abcdefghijklmnopqrstuvwxyz0123 c github_pat_ABC123_def" % SECRET
        out = tmt.redact(text, [SECRET])
        self.assertNotIn(SECRET, out)
        self.assertNotIn("ghp_abc", out)
        self.assertNotIn("github_pat_", out)
        self.assertEqual(out.count("[redacted]"), 3)

    def test_redact_ignores_empty_secret(self):
        self.assertEqual(tmt.redact("plain", ["", None]), "plain")

    def test_classify_probe(self):
        self.assertEqual(tmt.classify_probe(
            "HTTP/2.0 405 Method Not Allowed\n\n{}"), "blocked")
        self.assertEqual(tmt.classify_probe("HTTP/2.0 200 OK\n\n{}"), "merged")
        self.assertEqual(tmt.classify_probe("HTTP/1.1 409 Conflict\n"), "other")
        self.assertEqual(tmt.classify_probe(""), "other")

    def test_approvals_on_head(self):
        reviews = [
            {"user": {"login": "github-actions[bot]"}, "state": "APPROVED",
             "commit_id": "h2", "submitted_at": "2026-01-01T00:00:03Z"},
            {"user": {"login": "shipd-now"}, "state": "APPROVED",
             "commit_id": "h1", "submitted_at": "2026-01-01T00:00:01Z"},
            {"user": {"login": "shipd-now"}, "state": "DISMISSED",
             "commit_id": "h1", "submitted_at": "2026-01-01T00:00:02Z"},
            {"user": {"login": "mikkel-bergmann"}, "state": "APPROVED",
             "commit_id": "h2", "submitted_at": "2026-01-01T00:00:04Z"},
            {"user": {"login": "other"}, "state": "COMMENTED",
             "commit_id": "h2", "submitted_at": "2026-01-01T00:00:05Z"},
        ]
        self.assertEqual(tmt.approvals_on_head(reviews, "h2", "mikkel-bergmann"),
                         ["github-actions[bot]"])
        self.assertEqual(tmt.approvals_on_head(reviews, "h1", "mikkel-bergmann"), [])

    def test_approvals_later_comment_keeps_approval(self):
        reviews = [
            {"user": {"login": "a"}, "state": "APPROVED", "commit_id": "h",
             "submitted_at": "2026-01-01T00:00:01Z"},
            {"user": {"login": "a"}, "state": "COMMENTED", "commit_id": "h",
             "submitted_at": "2026-01-01T00:00:02Z"},
        ]
        self.assertEqual(tmt.approvals_on_head(reviews, "h", "x"), ["a"])


AUTHOR = "mikkel-bergmann"
REVIEWER = "shipd-now"
BOT = "github-actions[bot]"
PR_NUMBER = 7
PR_URL = "https://github.com/%s/pull/%d" % (REPO, PR_NUMBER)


class World:
    """A scripted GitHub: one pull request whose server-side behavior the
    merge rules dictate. ``allow_one`` models a broken rule (one approval is
    enough); ``leak`` puts the reviewer token into a refusal's stderr."""

    def __init__(self, allow_one=False, leak=False):
        self.allow_one, self.leak = allow_one, leak
        self.head, self.state, self.auto = "h1", "OPEN", False
        self.reviews, self.rid, self.pending_views = [], 0, 2
        self.pending_push = self.pr_created = self.empty_commit = False
        self.nhead = 1
        self.add(BOT, "APPROVED", "h1")

    def add(self, login, state, commit):
        self.rid += 1
        self.reviews.append({"id": self.rid, "user": {"login": login},
                             "state": state, "commit_id": commit,
                             "submitted_at": "2026-01-01T00:00:%02dZ" % self.rid})

    def approvals(self):
        return tmt.approvals_on_head(self.reviews, self.head, AUTHOR)

    def need(self):
        return 1 if self.allow_one else 2

    def merge_state(self):
        return "CLEAN" if len(self.approvals()) >= self.need() else "BLOCKED"

    def maybe_automerge(self):
        if self.auto and self.state == "OPEN" and len(self.approvals()) >= self.need():
            self.state = "MERGED"

    def handler(self, argv, who):
        text = " ".join(argv)
        if argv[0] == "git":
            if argv[1] == "commit" and self.pr_created:
                self.empty_commit = "--allow-empty" in argv
                self.pending_push = True
            if argv[1] == "push" and self.pending_push:
                self.pending_push = False
                self.nhead += 1
                self.head, self.pending_views = "h%d" % self.nhead, 2
                for rev in self.reviews:
                    if rev["state"] == "APPROVED":
                        if self.empty_commit:
                            rev["commit_id"] = self.head  # GitHub re-anchors, keeps approval
                        else:
                            rev["state"] = "DISMISSED"
                if not self.empty_commit:
                    self.add(BOT, "APPROVED", self.head)
            return (0, "", "")
        if argv[:3] == ["gh", "pr", "create"]:
            self.pr_created = True
            return (0, PR_URL + "\n", "")
        if argv[:3] == ["gh", "api", "user"]:
            return (0, (REVIEWER if who == "reviewer" else AUTHOR) + "\n", "")
        if argv[:3] == ["gh", "pr", "view"]:
            self.maybe_automerge()
            green = self.pending_views <= 0
            self.pending_views -= 1
            roll = [{"name": "ci", "conclusion": "SUCCESS" if green else ""},
                    {"context": "semantic-review",
                     "state": "SUCCESS" if green else "PENDING"}]
            return (0, json.dumps({
                "headRefOid": self.head, "state": self.state,
                "mergeStateStatus": "MERGED" if self.state == "MERGED"
                else self.merge_state(),
                "autoMergeRequest": {"mergeMethod": "SQUASH"} if self.auto else None,
                "statusCheckRollup": roll, "author": {"login": AUTHOR}}), "")
        if "/merge" in text and "api" in argv:
            if self.merge_state() == "CLEAN" and self.pending_views <= 0:
                self.state = "MERGED"
                return (0, "HTTP/2.0 200 OK\n\n{}", "")
            return (1, "HTTP/2.0 405 Method Not Allowed\n\n{}", "gh: blocked (HTTP 405)")
        if text.startswith("gh api") and "/reviews" in text:
            if "POST" in argv:
                commit = [a for a in argv if a.startswith("commit_id=")][0][10:]
                self.add(REVIEWER if who == "reviewer" else AUTHOR,
                         "APPROVED", commit)
                self.maybe_automerge()
                return (0, "{}", "")
            return (0, "\n".join(json.dumps(r) for r in self.reviews), "")
        if argv[:3] == ["gh", "pr", "review"]:
            err = "GraphQL: Can not approve your own pull request"
            return (1, "", err + (" " + SECRET if self.leak else ""))
        if argv[:3] == ["gh", "pr", "merge"]:
            self.auto = True
            return (0, "", "")
        if "room" in argv and "whoami" in argv:
            if who == "reviewer":
                return (0, json.dumps({"login": REVIEWER, "author": AUTHOR,
                                       "source": "token", "may_approve": True}), "")
            return (1, "", "Error: acting as @%s, who authored it" % AUTHOR)
        if "graphql" in argv:
            return (0, json.dumps({"data": {"repository": {"pullRequest": {
                "reviewThreads": {"nodes": [{"isResolved": True}]}}}}}), "")
        if "doctor" in argv:
            return (0, "ok protection — x\nok merge-rules — x\n"
                       "ok actions-approve — x\ndoctor: ok\n", "")
        if argv[1:3] == ["gate", "rules"] or "rules" in argv:
            return (0, "approvals: config 2, live 2 (ok)\n", "")
        return (1, "", "unexpected: " + text)


def run_world(world, out_dir, environ=None):
    gh = FakeGh(world.handler, environ=environ)
    lines = []
    code = tmt.main(["run", "--out", out_dir, "--root", out_dir],
                    gh=gh, out=lines.append, sleep=lambda _s: None)
    return code, gh, lines


class RunTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = tmp.name

    def evidence(self):
        with open(os.path.join(self.dir, "evidence.json")) as handle:
            return json.load(handle)

    def test_full_pass_proves_a_to_e(self):
        world = World()
        code, gh, lines = run_world(world, self.dir)
        self.assertEqual(code, 0, lines)
        ev = self.evidence()
        self.assertEqual(ev["result"], "pass")
        self.assertEqual(ev["pr_url"], PR_URL)
        records = ev["records"]
        self.assertTrue(records and all(r["ok"] for r in records), records)
        for r in records:
            self.assertEqual(set(r), {"id", "claim", "observed", "ok", "at"})
        for proof in "abcde":
            self.assertTrue(any(r["id"].startswith(proof + "-") for r in records), proof)
        self.assertEqual(world.state, "MERGED")
        self.assertEqual(world.approvals(), sorted([BOT, REVIEWER]))

    def test_auto_merge_armed_last_with_one_approval(self):
        world = World()
        code, gh, _lines = run_world(world, self.dir)
        self.assertEqual(code, 0)
        calls = [(" ".join(a), who) for a, who in gh.calls]
        arm = next(i for i, (c, _w) in enumerate(calls)
                   if c.startswith("gh pr merge") and "--auto" in c)
        reviewer_approvals = [i for i, (c, w) in enumerate(calls)
                              if w == "reviewer" and "POST" in c and "/reviews" in c]
        self.assertEqual(len(reviewer_approvals), 2)
        self.assertLess(reviewer_approvals[0], arm)
        self.assertLess(arm, reviewer_approvals[1])
        armed = next(r for r in self.evidence()["records"]
                     if r["id"] == "d-auto-merge-armed-open")
        self.assertIn("OPEN", armed["observed"])

    def test_push_dismisses_before_rearming(self):
        world = World()
        code, _gh, _l = run_world(world, self.dir)
        self.assertEqual(code, 0)
        recs = {r["id"]: r for r in self.evidence()["records"]}
        self.assertIn("DISMISSED", recs["b-push-dismisses"]["observed"])
        self.assertIn("405", recs["b-probe-after-push"]["observed"])

    def test_failing_step_stops_and_leaves_evidence(self):
        world = World(allow_one=True)
        code, gh, lines = run_world(world, self.dir)
        self.assertEqual(code, 1)
        ev = self.evidence()
        self.assertEqual(ev["result"], "fail")
        self.assertFalse(ev["records"][-1]["ok"])
        self.assertTrue(all(r["ok"] for r in ev["records"][:-1]))
        self.assertFalse([1 for a, w in gh.calls if w == "reviewer"
                          and "/reviews" in " ".join(a) and "POST" in a])
        self.assertFalse([1 for a, _w in gh.calls if a[:3] == ["gh", "pr", "merge"]])
        self.assertFalse([1 for a, _w in gh.calls if a[:3] == ["gh", "pr", "close"]])

    def test_resume_after_empty_push_keeps_approvals(self):
        world = World()
        world.add(REVIEWER, "APPROVED", "h1")
        world.pr_created = True
        world.pending_push = world.empty_commit = True
        world.handler(["git", "push"], "author")  # the empty push the first run made
        self.assertEqual(world.head, "h2")
        evidence = {"repo": REPO, "pr_url": PR_URL, "pr_number": PR_NUMBER,
                    "branch": "team-merge-test/20260101-000000", "result": "fail",
                    "started": "t", "finished": "t", "records": [
                        {"id": "a-two-approvals-clean", "claim": "c", "observed": "o",
                         "ok": True, "at": "t"},
                        {"id": "b-push-dismisses", "claim": "c", "observed": "not DISMISSED",
                         "ok": False, "at": "t"}]}
        with open(os.path.join(self.dir, "evidence.json"), "w") as handle:
            json.dump(evidence, handle)
        gh = FakeGh(world.handler)
        code = tmt.main(["run", "--resume", "--out", self.dir, "--root", self.dir],
                        gh=gh, out=lambda _l: None, sleep=lambda _s: None)
        self.assertEqual(code, 0)
        ev = self.evidence()
        ids = [r["id"] for r in ev["records"]]
        self.assertIn("b-empty-push-keeps-approvals", ids)
        self.assertIn("b-push-dismisses", ids)
        self.assertEqual(ev["result"], "pass")
        self.assertTrue(all(r["ok"] for r in ev["records"]))
        self.assertEqual(world.state, "MERGED")

    def test_resume_refuses_without_the_expected_failure(self):
        world = World()
        code, _gh, _l = run_world(world, self.dir)
        self.assertEqual(code, 0)
        code2 = tmt.main(["run", "--resume", "--out", self.dir, "--root", self.dir],
                         gh=FakeGh(world.handler), out=lambda _l: None,
                         sleep=lambda _s: None)
        self.assertEqual(code2, 1)

    def test_evidence_never_holds_the_token(self):
        world = World(leak=True)
        code, _gh, lines = run_world(world, self.dir)
        self.assertEqual(code, 0)
        raw = open(os.path.join(self.dir, "evidence.json")).read()
        self.assertNotIn(SECRET, raw)
        self.assertNotIn(SECRET, "\n".join(lines))
        self.assertIn("[redacted]", raw)


RULESET = {
    "id": 9, "name": "shipd merge rules", "enforcement": "active",
    "bypass_actors": [],
    "rules": [
        {"type": "pull_request", "parameters": {
            "required_approving_review_count": 2,
            "dismiss_stale_reviews_on_push": True,
            "require_last_push_approval": True,
            "required_review_thread_resolution": True}},
        {"type": "required_status_checks", "parameters": {
            "required_status_checks": [{"context": "ci"},
                                       {"context": "semantic-review"}]}}]}


class ApplyTest(unittest.TestCase):
    def handler_for(self, detail):
        def handler(argv, who):
            text = " ".join(argv)
            if "gate" in argv and "apply" in argv:
                return (0, "updated ruleset\n", "")
            if text.endswith("/rulesets"):
                return (0, json.dumps([{"id": 9, "name": "shipd merge rules"}]), "")
            if "/rulesets/9" in text:
                return (0, json.dumps(detail), "")
            return (1, "", "unexpected " + text)
        return handler

    def test_apply_asserts_live_ruleset(self):
        lines = []
        code = tmt.main(["apply"], gh=FakeGh(self.handler_for(RULESET)),
                        out=lines.append)
        self.assertEqual(code, 0, lines)

    def test_apply_fails_on_weak_ruleset(self):
        weak = json.loads(json.dumps(RULESET))
        weak["rules"][0]["parameters"]["required_approving_review_count"] = 1
        weak["bypass_actors"] = [{"actor_id": 5}]
        lines = []
        code = tmt.main(["apply"], gh=FakeGh(self.handler_for(weak)),
                        out=lines.append)
        self.assertEqual(code, 1)
        text = "\n".join(lines)
        self.assertIn("FAIL", text)

    def test_check_ruleset_rows(self):
        rows = tmt.check_ruleset(RULESET)
        self.assertTrue(rows and all(ok for _c, _o, ok in rows))


class ReportTest(unittest.TestCase):
    EVIDENCE = {
        "repo": REPO, "pr_url": PR_URL, "result": "pass",
        "started": "2026-10-17T10:00:00Z", "finished": "2026-10-17T10:09:00Z",
        "records": [
            {"id": "a-one-approval-blocks", "claim": "one approval blocks",
             "observed": "PUT merge -> 405 | BLOCKED", "ok": True,
             "at": "2026-10-17T10:01:00Z"},
            {"id": "d-merged", "claim": "auto-merge lands", "observed": "MERGED",
             "ok": False, "at": "2026-10-17T10:08:00Z"}]}

    def test_render_report(self):
        text = tmt.render_report(self.EVIDENCE)
        self.assertTrue(text.startswith("# "))
        self.assertIn(PR_URL, text)
        self.assertIn("a-one-approval-blocks", text)
        self.assertIn("pass", text)
        self.assertIn("\\|", text)
        for line in text.splitlines():
            self.assertNotIn("ghp_", line)

    def test_report_verb_writes_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "evidence.json")
            dst = os.path.join(tmp, "retro.md")
            with open(src, "w") as handle:
                json.dump(self.EVIDENCE, handle)
            code = tmt.main(["report", "--evidence", src, "--output", dst],
                            gh=FakeGh(), out=lambda _l: None)
            self.assertEqual(code, 0)
            self.assertIn(PR_URL, open(dst).read())


if __name__ == "__main__":
    unittest.main()
