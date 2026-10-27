#!/usr/bin/env python3
"""Unit tests for the ``oracle-lookup <term>...`` status verb (spec-status
oracle-lookup-verb): ladder order, citation markers, advisory tags, not-evidence
pending list, INSUFFICIENT line, and the output cap."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
STATUS = os.path.join(SCRIPTS, "spec_status.py")

QUEUE_BLOCK = (
    "## q-%s\n- Asked: 2026-01-01 [test]\n- Question: %s\n- Options: a; b\n"
    "- Recommendation: a\n- Answer: %s\n\n")


class OracleLookupTestBase(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="oracle-root-")
        self.home = tempfile.mkdtemp(prefix="oracle-home-")
        self.root = os.path.realpath(self.root)
        self.home = os.path.realpath(self.home)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)
        shutil.rmtree(self.home, ignore_errors=True)

    def declare_workspace(self, path=None, extra=None):
        path = path or self.root
        os.makedirs(path, exist_ok=True)
        cfg = {"workspace": {}}
        cfg.update(extra or {})
        with open(os.path.join(path, ".shipd-config.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(cfg, fh)

    def store(self, ws=None):
        return os.path.join(ws or self.root, ".shipd", "wiki")

    def page(self, store, slug, text):
        pages = os.path.join(store, "wiki")
        os.makedirs(pages, exist_ok=True)
        with open(os.path.join(pages, slug + ".md"), "w",
                  encoding="utf-8") as fh:
            fh.write(text)

    def queue(self, store, text):
        os.makedirs(store, exist_ok=True)
        with open(os.path.join(store, "queue.md"), "w",
                  encoding="utf-8") as fh:
            fh.write("# Queue\n\n" + text)

    def write(self, path, text):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)

    def lookup(self, *terms, root=None):
        env = dict(os.environ)
        env["HOME"] = self.home
        return subprocess.run(
            ["python3", "-B", STATUS, "--root", root or self.root,
             "oracle-lookup", *terms],
            capture_output=True, text=True, env=env)


class OracleLookupTest(OracleLookupTestBase):
    def test_personal_prints_first_with_marker(self):
        self.declare_workspace()
        pstore = os.path.join(self.home, ".shipd-memory", "wiki")
        self.page(pstore, "mine", "Prefer squash merges always.\n")
        self.page(self.store(), "shared", "Prefer squash merges here.\n")
        res = self.lookup("squash", "merges")
        self.assertEqual(res.returncode, 0, res.stderr)
        out = res.stdout
        self.assertIn("[[mine]] (personal)", out)
        self.assertIn("[[shared]] —", out)
        self.assertLess(out.index("[[mine]] (personal)"),
                        out.index("[[shared]]"))

    def test_absent_personal_store_is_skipped(self):
        self.declare_workspace()
        res = self.lookup("alpha", "beta")
        self.assertEqual(res.returncode, 0)
        self.assertIn("personal: skipped", res.stdout.splitlines()[0])

    def test_inherited_marker_for_outer_workspace(self):
        self.declare_workspace()
        inner = os.path.join(self.root, "inner")
        self.declare_workspace(inner)
        self.page(self.store(), "outer-page", "Always rebase before merging.\n")
        res = self.lookup("rebase", "merging", root=inner)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("[[outer-page]] (inherited %s)" % self.root, res.stdout)

    def test_answered_queue_block_is_evidence_pending_is_not(self):
        self.declare_workspace()
        store = self.store()
        self.queue(store,
                   QUEUE_BLOCK % ("done-one", "Which cache backend wins?",
                                  "Use redis for the cache backend")
                   + QUEUE_BLOCK % ("open-one", "Which cache backend next?",
                                    "pending"))
        res = self.lookup("cache", "backend")
        out = res.stdout
        head, _, tail = out.partition("== pending queue")
        self.assertIn("queue q-done-one", head)
        self.assertNotIn("q-open-one", head)
        self.assertIn("q-open-one", tail)
        self.assertNotIn("q-done-one", tail)

    def test_advisory_tag(self):
        self.declare_workspace()
        self.queue(self.store(),
                   QUEUE_BLOCK % ("adv", "Which linter config?",
                                  "advisory: use strict linter config"))
        res = self.lookup("linter", "config")
        self.assertIn("queue q-adv [advisory] —", res.stdout)

    def test_advisory_page_tag(self):
        self.declare_workspace()
        self.page(self.store(), "adv-page",
                  "Authority: advisory\n\nUse tabs for indentation always.\n")
        res = self.lookup("tabs", "indentation")
        self.assertIn("[[adv-page]] [advisory]", res.stdout)

    def test_base_store_is_searched_and_marked(self):
        base = os.path.join(self.home, "basewiki")
        self.declare_workspace(extra={"wiki_base": base})
        self.page(base, "basepage", "Release trains ship every Tuesday.\n")
        res = self.lookup("release", "tuesday")
        self.assertIn("[[basepage]] (base)", res.stdout)
        self.assertIn("base: %s" % base, res.stdout.splitlines()[0])

    def test_verified_paragraph_cites_capability_and_id(self):
        self.declare_workspace()
        self.write(os.path.join(self.root, ".shipd", "verified", "widgets",
                                "spec.md"),
                   "# widgets\n\n### Requirement: Foo\nid: foo-bar\n\n"
                   "The widget SHALL frobnicate every gizmo.\n")
        res = self.lookup("frobnicate", "gizmo")
        self.assertIn("verified/widgets (foo-bar) —", res.stdout)

    def test_epic_sections_only(self):
        self.declare_workspace()
        self.write(os.path.join(self.root, ".shipd", "epics", "e1", "epic.md"),
                   "# e1\n\n## Notes\n\nzebra quokka outside.\n\n"
                   "## Decisions\n\nzebra quokka inside.\n")
        res = self.lookup("zebra", "quokka")
        self.assertIn("epic/e1", res.stdout)
        self.assertIn("inside", res.stdout)
        self.assertNotIn("outside", res.stdout)

    def test_bare_repo_fallback_store(self):
        os.makedirs(os.path.join(self.root, ".shipd"))
        self.page(self.store(), "fb", "Fallback holds the lantern policy.\n")
        res = self.lookup("fallback", "lantern")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("[[fb]] —", res.stdout)

    def test_no_match_ends_with_insufficient(self):
        self.declare_workspace()
        res = self.lookup("zzz-none", "qqq-none")
        self.assertEqual(res.returncode, 0)
        self.assertEqual(res.stdout.splitlines()[-1],
                         "no evidence found — verdict INSUFFICIENT")

    def test_single_term_matches_alone_two_terms_need_both(self):
        self.declare_workspace()
        self.page(self.store(), "p", "Only mango here.\n")
        self.assertIn("[[p]]", self.lookup("mango").stdout)
        self.assertNotIn("[[p]]", self.lookup("mango", "papaya").stdout)

    def test_cap_per_rung_and_total_with_omitted_line(self):
        self.declare_workspace()
        for i in range(30):
            self.page(self.store(), "page-%02d" % i,
                      ("alpha beta filler %s " % ("x" * 380)) * 1 + "\n")
        res = self.lookup("alpha", "beta")
        out = res.stdout
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertLessEqual(out.count("[[page-"), 4)
        self.assertLessEqual(len(out), 6000)
        self.assertRegex(out.splitlines()[-1],
                         r"^… \d+ more matches omitted$")

    def test_snippet_is_verbatim_substring_with_collapsed_whitespace(self):
        self.declare_workspace()
        self.page(self.store(), "ws", "alpha   beta\n  gamma line\n")
        res = self.lookup("alpha", "beta")
        self.assertIn('"alpha beta gamma line"', res.stdout)


if __name__ == "__main__":
    unittest.main()
