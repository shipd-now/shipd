#!/usr/bin/env python3
"""Tests for ``actions_approval.py`` (actions-approval actions-approval-setting).
Every GitHub call goes through a recording fake runner; nothing here reaches
the network or the real ``gh``."""

import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

import actions_approval as aa  # noqa: E402

NWO = "octo/repo"
ENDPOINT = "repos/octo/repo/actions/permissions/workflow"


def setting(can, perms="read"):
    return json.dumps({"default_workflow_permissions": perms,
                       "can_approve_pull_request_reviews": can})


class FakeGh:
    """A recording ``run(args, stdin=None, cwd=None)`` double. ``reads`` is the
    list of answers successive GETs return (the last repeats); ``put`` is the
    answer to the PUT."""

    def __init__(self, reads, put=(0, "", "")):
        self.reads = list(reads)
        self.put = put
        self.calls = []

    def __call__(self, args, stdin=None, cwd=None):
        args = list(args)
        self.calls.append((args, stdin))
        if args[:2] == ["repo", "view"]:
            return (0, NWO + "\n", "")
        if "-X" in args and args[args.index("-X") + 1] == "PUT":
            return self.put
        answer = self.reads[0]
        if len(self.reads) > 1:
            self.reads.pop(0)
        return answer

    def puts(self):
        return [c for c in self.calls if "PUT" in c[0]]


def run_main(argv, fake):
    lines = []
    code = aa.main(argv + ["--repo", NWO], run=fake, out=lines.append)
    return code, "\n".join(lines)


class ReadTest(unittest.TestCase):
    def test_disabled_setting_is_reported_and_never_written(self):
        fake = FakeGh([(0, setting(False), "")])
        code, out = run_main([], fake)
        self.assertEqual(code, 0)
        self.assertIn("actions-approve: disabled", out)
        self.assertEqual(fake.puts(), [])

    def test_enabled_setting_is_reported(self):
        fake = FakeGh([(0, setting(True), "")])
        code, out = run_main([], fake)
        self.assertEqual(code, 0)
        self.assertIn("actions-approve: enabled", out)

    def test_read_setting_returns_state_and_default_permissions(self):
        fake = FakeGh([(0, setting(False, "write"), "")])
        self.assertEqual(aa.read_setting(NWO, fake), ("disabled", "write"))
        self.assertEqual(fake.calls[0][0], ["api", ENDPOINT])


class AllowTest(unittest.TestCase):
    def test_allow_preserves_the_default_permissions(self):
        fake = FakeGh([(0, setting(False), ""), (0, setting(True), "")])
        code, out = run_main(["allow"], fake)
        self.assertEqual(code, 0)
        puts = fake.puts()
        self.assertEqual(len(puts), 1)
        args, stdin = puts[0]
        self.assertIn(ENDPOINT, args)
        self.assertIn("--input", args)
        self.assertEqual(json.loads(stdin), {
            "default_workflow_permissions": "read",
            "can_approve_pull_request_reviews": True})
        self.assertIn("actions-approve: enabled", out)
        # The setting is re-read after the write.
        self.assertEqual(fake.calls[-1][0], ["api", ENDPOINT])
        self.assertEqual(len(fake.calls), 3)

    def test_allow_carries_write_permissions_unchanged(self):
        fake = FakeGh([(0, setting(False, "write"), ""),
                       (0, setting(True, "write"), "")])
        run_main(["allow"], fake)
        self.assertEqual(json.loads(fake.puts()[0][1])
                         ["default_workflow_permissions"], "write")

    def test_allow_is_a_noop_when_already_enabled(self):
        fake = FakeGh([(0, setting(True), "")])
        code, out = run_main(["allow"], fake)
        self.assertEqual(code, 0)
        self.assertEqual(fake.puts(), [])
        self.assertIn("actions-approve: enabled", out)

    def test_an_unreadable_setting_is_never_written(self):
        for read in ((1, "", "boom"), (0, "not json", ""), (0, "[]", "")):
            fake = FakeGh([read])
            code, out = run_main([], fake)
            self.assertEqual(code, 0)
            self.assertIn("actions-approve: unknown", out)
            fake = FakeGh([read])
            code, out = run_main(["allow"], fake)
            self.assertNotEqual(code, 0)
            self.assertIn("actions-approve: unknown", out)
            self.assertEqual(fake.puts(), [])

    def test_a_write_that_does_not_take_is_reported(self):
        fake = FakeGh([(0, setting(False), ""), (0, setting(False), "")])
        code, out = run_main(["allow"], fake)
        self.assertNotEqual(code, 0)
        self.assertEqual(len(fake.puts()), 1)
        self.assertIn("organization", out.lower())

    def test_a_failed_write_exits_nonzero(self):
        fake = FakeGh([(0, setting(False), "")], put=(1, "", "HTTP 403"))
        code, out = run_main(["allow"], fake)
        self.assertNotEqual(code, 0)
        self.assertIn("403", out)


class UsageTest(unittest.TestCase):
    def test_bad_usage_exits_two(self):
        fake = FakeGh([(0, setting(False), "")])
        self.assertEqual(aa.main(["bogus"], run=fake, out=lambda s: None), 2)
        self.assertEqual(fake.calls, [])

    def test_repository_defaults_to_gh_repo_view(self):
        fake = FakeGh([(0, setting(True), "")])
        lines = []
        self.assertEqual(aa.main([], run=fake, out=lines.append), 0)
        self.assertEqual(fake.calls[0][0][:2], ["repo", "view"])
        self.assertEqual(fake.calls[1][0], ["api", ENDPOINT])


if __name__ == "__main__":
    unittest.main()
