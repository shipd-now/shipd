#!/usr/bin/env python3
"""Tests for ``merge_rules.py`` — the ``shipd gate rules`` engine
(shipd-cli gate-rules-verb). Every GitHub call goes through a recording fake
runner; nothing here reaches the network or the real ``gh``."""

import copy
import io
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

import merge_rules as mr  # noqa: E402
import spec_common as sc  # noqa: E402

NWO = "octo/repo"
OWNED_ID = 4242
MAIN_ID = 7


class FakeGh:
    """A recording ``run(args, stdin=None, cwd=None)`` double. ``items`` is the
    ruleset list the list endpoint returns; ``details`` maps id -> detail."""

    def __init__(self, items=None, details=None, fail=None):
        self.items = items if items is not None else []
        self.details = details or {}
        self.fail = fail or {}
        self.calls = []

    def __call__(self, args, stdin=None, cwd=None):
        args = list(args)
        self.calls.append((args, stdin))
        if args[:2] == ["repo", "view"]:
            return (0, NWO + "\n", "")
        path = next((a for a in args if a.startswith("repos/")), "")
        method = "GET"
        if "-X" in args:
            method = args[args.index("-X") + 1]
        key = (method, path.split("?")[0])
        if key in self.fail:
            return (1, "", self.fail[key])
        if method == "GET" and path.startswith("repos/%s/rulesets?" % NWO):
            return (0, json.dumps(self.items), "")
        if method == "GET":
            rid = int(path.rsplit("/", 1)[1])
            return (0, json.dumps(self.details[rid]), "")
        return (0, json.dumps({"id": OWNED_ID}), "")

    def writes(self):
        return [(a, s) for a, s in self.calls if "-X" in a]

    def paths(self):
        return [a for args, _ in self.calls for a in args
                if a.startswith("repos/")]


def _item(rid, name, source="Repository"):
    return {"id": rid, "name": name, "source_type": source}


def _detail(rid, name, merge=None, **overrides):
    body = mr.desired_ruleset(merge or dict(sc.DEFAULT_MERGE))
    body["name"] = name
    body["id"] = rid
    body.update(overrides)
    return body


def _run(argv, fake, root=None):
    out = []
    code = mr.main(argv, run=fake, out=out.append)
    return code, "\n".join(out)


class DesiredRulesetTest(unittest.TestCase):
    def test_default_body_shape(self):
        body = mr.desired_ruleset(dict(sc.DEFAULT_MERGE))
        self.assertEqual(body["name"], "shipd merge rules")
        self.assertEqual(body["target"], "branch")
        self.assertEqual(body["enforcement"], "active")
        self.assertEqual(body["conditions"],
                         {"ref_name": {"include": ["~DEFAULT_BRANCH"],
                                       "exclude": []}})
        self.assertEqual(body["bypass_actors"], [])
        rules = {r["type"]: r["parameters"] for r in body["rules"]}
        self.assertEqual(rules["pull_request"], {
            "required_approving_review_count": 2,
            "dismiss_stale_reviews_on_push": True,
            "require_code_owner_review": False,
            "require_last_push_approval": True,
            "required_review_thread_resolution": True})
        self.assertNotIn("allowed_merge_methods", rules["pull_request"])
        self.assertEqual(rules["required_status_checks"], {
            "required_status_checks": [{"context": "ci"},
                                       {"context": "semantic-review"}],
            "strict_required_status_checks_policy": False})

    def test_empty_checks_omit_the_status_rule(self):
        merge = dict(sc.DEFAULT_MERGE, required_checks=[])
        body = mr.desired_ruleset(merge)
        self.assertEqual([r["type"] for r in body["rules"]], ["pull_request"])


class DiffTest(unittest.TestCase):
    def test_matching_detail_has_no_drift(self):
        detail = _detail(OWNED_ID, mr.RULESET_NAME)
        self.assertEqual(mr.diff(dict(sc.DEFAULT_MERGE), detail), [])

    def test_live_members_round_trip(self):
        detail = _detail(OWNED_ID, mr.RULESET_NAME)
        live = mr.live_members(detail)
        self.assertEqual(live["approvals"], 2)
        self.assertEqual(live["required_checks"], ["ci", "semantic-review"])
        self.assertEqual(set(live), set(sc.DEFAULT_MERGE))

    def test_approvals_drift(self):
        detail = _detail(OWNED_ID, mr.RULESET_NAME,
                         merge=dict(sc.DEFAULT_MERGE, approvals=0))
        self.assertEqual(mr.diff(dict(sc.DEFAULT_MERGE), detail),
                         [("approvals", 0, 2)])

    def test_checks_compare_as_sorted_lists(self):
        detail = _detail(OWNED_ID, mr.RULESET_NAME,
                         merge=dict(sc.DEFAULT_MERGE,
                                    required_checks=["semantic-review", "ci"]))
        self.assertEqual(mr.diff(dict(sc.DEFAULT_MERGE), detail), [])

    def test_enforcement_and_ref_drift(self):
        detail = _detail(OWNED_ID, mr.RULESET_NAME, enforcement="disabled")
        detail["conditions"]["ref_name"]["include"] = ["refs/heads/dev"]
        got = dict((m, (l, w)) for m, l, w in
                   mr.diff(dict(sc.DEFAULT_MERGE), detail))
        self.assertEqual(got["enforcement"], ("disabled", "active"))
        self.assertEqual(got["ref_include"],
                         (["refs/heads/dev"], ["~DEFAULT_BRANCH"]))

    def test_order_is_fixed(self):
        detail = _detail(OWNED_ID, mr.RULESET_NAME,
                         merge=dict(sc.DEFAULT_MERGE, approvals=0,
                                    strict=True, dismiss_stale=False))
        names = [m for m, _l, _w in mr.diff(dict(sc.DEFAULT_MERGE), detail)]
        self.assertEqual(names, ["approvals", "dismiss_stale", "strict"])


class VerbTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = os.path.realpath(self._tmp.name)
        home = os.path.join(self.root, "home")
        os.makedirs(home)
        self._old_home = os.environ.get("HOME")
        os.environ["HOME"] = home
        self.addCleanup(self._restore_home)

    def _restore_home(self):
        if self._old_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = self._old_home

    def _argv(self, *words):
        return list(words) + ["--repo", NWO, "--root", self.root]

    def test_apply_creates_when_absent(self):
        fake = FakeGh(items=[])
        code, out = _run(self._argv("apply"), fake)
        self.assertEqual(code, 0, out)
        writes = fake.writes()
        self.assertEqual(len(writes), 1)
        args, stdin = writes[0]
        self.assertEqual(args[args.index("-X") + 1], "POST")
        self.assertIn("repos/%s/rulesets" % NWO, args)
        self.assertIn("--input", args)
        self.assertEqual(json.loads(stdin),
                         mr.desired_ruleset(dict(sc.DEFAULT_MERGE)))
        self.assertIn("created", out)
        self.assertIn(str(OWNED_ID), out)
        self.assertIn("approvals", out)

    def test_apply_updates_only_the_owned_ruleset(self):
        fake = FakeGh(
            items=[_item(MAIN_ID, "main"), _item(OWNED_ID, mr.RULESET_NAME)],
            details={OWNED_ID: _detail(
                OWNED_ID, mr.RULESET_NAME,
                merge=dict(sc.DEFAULT_MERGE, approvals=0))})
        code, out = _run(self._argv("apply"), fake)
        self.assertEqual(code, 0, out)
        writes = fake.writes()
        self.assertEqual(len(writes), 1)
        args, _stdin = writes[0]
        self.assertEqual(args[args.index("-X") + 1], "PUT")
        self.assertIn("repos/%s/rulesets/%d" % (NWO, OWNED_ID), args)
        self.assertIn("approvals: 0 -> 2", out)
        self.assertIn("updated", out)
        for path in fake.paths():
            self.assertNotIn("/%d" % MAIN_ID, path)

    def test_apply_with_no_drift_writes_nothing(self):
        fake = FakeGh(
            items=[_item(OWNED_ID, mr.RULESET_NAME)],
            details={OWNED_ID: _detail(OWNED_ID, mr.RULESET_NAME)})
        code, out = _run(self._argv("apply"), fake)
        self.assertEqual(code, 0, out)
        self.assertEqual(fake.writes(), [])
        self.assertIn("nothing written", out)

    def test_bare_report_marks_differences_and_writes_nothing(self):
        fake = FakeGh(
            items=[_item(OWNED_ID, mr.RULESET_NAME)],
            details={OWNED_ID: _detail(
                OWNED_ID, mr.RULESET_NAME,
                merge=dict(sc.DEFAULT_MERGE, approvals=0))})
        code, out = _run(self._argv(), fake)
        self.assertEqual(code, 0, out)
        self.assertEqual(fake.writes(), [])
        self.assertIn("approvals: config 2, live 0 (differs)", out)
        self.assertIn("dismiss_stale: config true, live true (ok)", out)

    def test_bypass_actor_drift_is_restored(self):
        detail = _detail(OWNED_ID, mr.RULESET_NAME)
        detail["bypass_actors"] = [{"actor_id": 5, "actor_type": "RepositoryRole",
                                    "bypass_mode": "always"}]
        fake = FakeGh(items=[_item(OWNED_ID, mr.RULESET_NAME)],
                      details={OWNED_ID: detail})
        code, out = _run(self._argv(), fake)
        self.assertEqual(code, 0, out)
        self.assertIn("bypass_actors: config 0, live 1 (differs)", out)
        code, out = _run(self._argv("apply"), fake)
        self.assertEqual(code, 0, out)
        writes = fake.writes()
        self.assertEqual(len(writes), 1)
        args, _stdin = writes[0]
        self.assertEqual(args[args.index("-X") + 1], "PUT")
        self.assertIn("repos/%s/rulesets/%d" % (NWO, OWNED_ID), args)
        self.assertIn("bypass_actors: 1 -> 0", out)

    def test_bare_report_with_no_ruleset(self):
        fake = FakeGh(items=[_item(MAIN_ID, "main")])
        code, out = _run(self._argv(), fake)
        self.assertEqual(code, 0, out)
        self.assertEqual(fake.writes(), [])
        self.assertIn("no ruleset", out)

    def test_other_source_rulesets_are_not_owned(self):
        fake = FakeGh(items=[_item(9, mr.RULESET_NAME, source="Organization")])
        code, _out = _run(self._argv("apply"), fake)
        self.assertEqual(code, 0)
        self.assertEqual(fake.writes()[0][0][fake.writes()[0][0].index("-X") + 1],
                         "POST")

    def test_duplicate_name_is_refused(self):
        fake = FakeGh(items=[_item(1, mr.RULESET_NAME),
                             _item(2, mr.RULESET_NAME)])
        err = io.StringIO()
        old, sys.stderr = sys.stderr, err
        try:
            code, _out = _run(self._argv("apply"), fake)
        finally:
            sys.stderr = old
        self.assertEqual(code, 1)
        self.assertEqual(fake.writes(), [])
        self.assertIn("shipd merge rules", err.getvalue())
        self.assertIn("Error:", err.getvalue())

    def test_403_names_admin_permission(self):
        fake = FakeGh(items=[], fail={
            ("POST", "repos/%s/rulesets" % NWO):
                "gh: Must have admin rights to Repository. (HTTP 403)"})
        err = io.StringIO()
        old, sys.stderr = sys.stderr, err
        try:
            code, _out = _run(self._argv("apply"), fake)
        finally:
            sys.stderr = old
        self.assertEqual(code, 1)
        self.assertIn("admin", err.getvalue())

    def test_config_error_exits_one(self):
        with open(os.path.join(self.root, sc.CONFIG_FILENAME), "w") as fh:
            json.dump({"merge": {"approvls": 2}}, fh)
        fake = FakeGh()
        err = io.StringIO()
        old, sys.stderr = sys.stderr, err
        try:
            code, _out = _run(self._argv("apply"), fake)
        finally:
            sys.stderr = old
        self.assertEqual(code, 1)
        self.assertEqual(fake.writes(), [])
        self.assertIn("merge", err.getvalue())

    def test_repo_resolved_through_gh_when_not_given(self):
        fake = FakeGh(items=[])
        code, _out = _run(["--root", self.root], fake)
        self.assertEqual(code, 0)
        self.assertEqual(fake.calls[0][0][:2], ["repo", "view"])

    def test_config_drives_the_body(self):
        with open(os.path.join(self.root, sc.CONFIG_FILENAME), "w") as fh:
            json.dump({"merge": {"approvals": 1, "required_checks": []}}, fh)
        fake = FakeGh(items=[])
        code, _out = _run(self._argv("apply"), fake)
        self.assertEqual(code, 0)
        body = json.loads(fake.writes()[0][1])
        types = {r["type"]: r["parameters"] for r in body["rules"]}
        self.assertEqual(
            types["pull_request"]["required_approving_review_count"], 1)
        self.assertNotIn("required_status_checks", types)


if __name__ == "__main__":
    unittest.main()
