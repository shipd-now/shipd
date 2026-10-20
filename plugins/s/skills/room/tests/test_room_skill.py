#!/usr/bin/env python3
"""Tests for the ``/s:room`` skill — its ``SKILL.md``, harness body, docs,
and registrations.

These pin the properties the skill has to keep however its wording is
edited: the verb order of the loop, an explicit ``--state`` on every reply,
the stop list, the foreground-only ``watch`` rule, the prose-only boundary,
the two renders of the harness body, the registration surfaces, and a
lint-clean how-to. ``harness_bodies`` is imported from the build scripts the
way ``test_harness_bodies.py`` imports it.
"""

import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
REPO_ROOT = os.path.normpath(os.path.join(PLUGIN_ROOT, "..", ".."))
BUILD_SCRIPTS = os.path.join(PLUGIN_ROOT, "skills", "build", "scripts")
if BUILD_SCRIPTS not in sys.path:
    sys.path.insert(0, BUILD_SCRIPTS)

import harness_bodies as hb  # noqa: E402

SKILL_PATH = os.path.join(PLUGIN_ROOT, "skills", "room", "SKILL.md")
DOCS_LINT = os.path.join(PLUGIN_ROOT, "skills", "document", "scripts",
                         "docs_lint.py")
DOC_PATH = os.path.join(REPO_ROOT, "docs", "pr-room.md")
IDENTITY_DOC_PATH = os.path.join(REPO_ROOT, "docs", "agent-identity.md")
REFS = "R"


def _read(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def _flat(text):
    """``text`` with every whitespace run collapsed to one space, so a
    sentence wrapped across lines still matches."""
    return re.sub(r"\s+", " ", text)


class SkillLoopTest(unittest.TestCase):
    """room-skill-loop."""

    def setUp(self):
        self.text = _read(SKILL_PATH)

    def test_verbs_appear_in_loop_order(self):
        verbs = ("join", "list", "watch", "message", "close")
        firsts = []
        for verb in verbs:
            found = [i for i in (self.text.find("shipd room %s" % verb),
                                 self.text.find('shipd" room %s' % verb))
                     if i >= 0]
            self.assertTrue(found, "SKILL.md never names room %s" % verb)
            firsts.append(min(found))
        self.assertEqual(firsts, sorted(firsts),
                         "verbs first appear out of order: %r"
                         % list(zip(verbs, firsts)))

    def test_default_card_skills_and_timeout(self):
        flat = _flat(self.text)
        self.assertIn("--skill review-finding --skill question --skill status",
                      flat)
        self.assertIn("--timeout 540", flat)
        self.assertNotIn("--timeout 600", flat)

    def test_tool_call_timeout_exceeds_watch_timeout(self):
        flat = _flat(self.text)
        self.assertIn("its own timeout above 540 seconds", flat)
        self.assertIn("600000", flat)

    def test_every_message_carries_a_state(self):
        lines = [ln for ln in self.text.splitlines()
                 if re.search(r'shipd"? room message', ln)]
        self.assertTrue(lines, "SKILL.md names no room message invocation")
        for line in lines:
            self.assertIn("--state", line,
                          "room message without --state: %r" % line)


    def test_stay_invocation_and_re_entry(self):
        flat = _flat(self.text)
        self.assertIn("/s:room [<pr>] [stay]", flat)
        self.assertRegex(flat, r"(?i)with `stay`.{0,200}re-enters `watch`")


class SkillStopsTest(unittest.TestCase):
    """room-skill-stops."""

    def setUp(self):
        self.flat = _flat(_read(SKILL_PATH)).lower()

    def test_closed_room_stop(self):
        self.assertIn("room closed", self.flat)
        self.assertIn("`closed` line", self.flat)

    def test_empty_watch_stop(self):
        self.assertIn("empty stdout", self.flat)
        self.assertIn("cursor", self.flat)

    def test_round_cap_stop(self):
        self.assertIn("round cap", self.flat)

    def test_watch_is_foreground_only(self):
        self.assertIn("foreground", self.flat)
        self.assertIn("never runs `watch` in the background", self.flat)


    def test_unresolved_tasks_are_reported_on_a_closed_room(self):
        self.assertIn("`open` array", self.flat)
        self.assertIn("unresolved", self.flat)

    def test_every_verb_receives_the_url_or_repo(self):
        self.assertIn("--repo", self.flat)
        self.assertIn("pull request url", self.flat)


class SkillMergeRuleTest(unittest.TestCase):
    """room-skill-merge-rule."""

    def test_skill_states_the_merge_rule(self):
        flat = _flat(_read(SKILL_PATH))
        for needle in ("gh pr merge", "list <pr> --open", "reviewer",
                       "working", "input-required"):
            self.assertIn(needle, flat)

    def test_harness_body_and_reference_carry_the_rule(self):
        out = hb.render("room", ("background-tasks",), refs_dir=REFS)
        for needle in ("--open", "gh pr merge"):
            self.assertIn(needle, out)
        ref = _flat(_read(os.path.join(PLUGIN_ROOT, "harness", "references",
                                       "room.md")))
        for needle in ("--open", "gh pr merge", "unresolved", "`open`"):
            self.assertIn(needle, ref)


class SkillNoCodeTest(unittest.TestCase):
    """room-skill-no-code."""

    def test_no_code_rule_names_the_hand_offs(self):
        flat = _flat(_read(SKILL_PATH))
        self.assertIn("/s:fix", flat)
        self.assertIn("/s:plan", flat)
        self.assertRegex(flat.lower(),
                         r"never edit, commit, or push|never edits, commits, "
                         r"or pushes")

    def test_author_may_fix_a_finding_under_a_guard(self):
        flat = _flat(_read(SKILL_PATH))
        for needle in ("author", "review-finding", "headRefName",
                       "author.login", "isCrossRepository",
                       "git push", "--force", "/s:fix", "/s:plan",
                       "never edits, commits, or pushes code"):
            self.assertIn(needle, flat)

    def test_harness_body_carries_the_author_rule(self):
        out = hb.render("room", ("background-tasks",), refs_dir=REFS)
        for needle in ("author", "headRefName", "author.login",
                       "isCrossRepository", "/s:fix", "/s:plan"):
            self.assertIn(needle, out)
        ref = _flat(_read(os.path.join(PLUGIN_ROOT, "harness", "references", "room.md")))
        for needle in ("author.login", "isCrossRepository"):
            self.assertIn(needle, ref)


class BodyRenderTest(unittest.TestCase):
    """room-skill-body."""

    def test_bare_harness_reads_once(self):
        out = hb.render("room", (), refs_dir=REFS)
        self.assertIn("shipd room list", out)
        self.assertNotIn("shipd room watch", out)

    def test_background_harness_watches(self):
        out = hb.render("room", ("background-tasks",), refs_dir=REFS)
        self.assertIn("shipd room watch", out)
        self.assertIn("--timeout 540", out)
        self.assertNotIn("--timeout 600", out)
        self.assertIn("540 seconds", out)

    def test_reference_and_doc_use_the_540_timeout(self):
        for path in (os.path.join(PLUGIN_ROOT, "harness", "references",
                                  "room.md"), DOC_PATH):
            text = _read(path)
            self.assertIn("--timeout 540", text, path)
            self.assertNotIn("--timeout 600", text, path)


class DocsTest(unittest.TestCase):
    """room-skill-docs."""

    def test_registration_surfaces_name_the_skill(self):
        for rel in ("AGENTS.md", "README.md", os.path.join("docs",
                                                            "cheatsheet.md")):
            self.assertIn("/s:room", _read(os.path.join(REPO_ROOT, rel)),
                          "%s does not name /s:room" % rel)

    def test_doc_lints_clean(self):
        result = subprocess.run(
            [sys.executable, DOCS_LINT, DOC_PATH],
            cwd=REPO_ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0,
                         result.stdout + result.stderr)


class ReviewerReviewTest(unittest.TestCase):
    """room-skill-reviewer-review."""

    HARNESS_BODY = os.path.join(PLUGIN_ROOT, "harness", "bodies", "room.md")
    REFERENCE = os.path.join(PLUGIN_ROOT, "harness", "references", "room.md")
    RUN_DOC = os.path.join(REPO_ROOT, "docs", "room-run.md")

    def test_skill_names_the_review_command_and_its_options(self):
        text = _read(SKILL_PATH)
        for needle in ("/s:review", "status=auto", "room-agent=",
                       "room-to=", "last_agent"):
            self.assertIn(needle, text)
        self.assertLess(text.index("shipd room whoami"),
                        text.index("/s:review"))

    def test_skill_states_both_status_cases_and_forbids_a_freeform_review(self):
        text = _read(SKILL_PATH)
        for needle in ("semantic-review", "gh pr review",
                       ".github/workflows/copilot-review-gate.yml"):
            self.assertIn(needle, text)

    def test_harness_body_and_reference_carry_the_rule(self):
        rendered = hb.render("room", ("background-tasks",), refs_dir=REFS)
        for label, text in (("body", rendered),
                            ("reference", _read(self.REFERENCE))):
            for needle in ("/s:review", "status=auto", "room-to=",
                           "copilot-review-gate.yml"):
                self.assertIn(needle, text, "%s lacks %s" % (label, needle))

    def test_the_how_to_names_the_branded_review_and_both_status_cases(self):
        text = _read(self.RUN_DOC)
        for needle in ("/s:review", "semantic-review",
                       "copilot-review-gate.yml"):
            self.assertIn(needle, text)


class SkillIdentityTest(unittest.TestCase):
    """room-skill-identity-check and agent-identity-docs-version."""

    def test_every_surface_names_whoami(self):
        for path in (SKILL_PATH,
                     os.path.join(PLUGIN_ROOT, "harness", "bodies", "room.md"),
                     os.path.join(PLUGIN_ROOT, "harness", "references",
                                  "room.md")):
            self.assertIn("shipd room whoami", _read(path), path)

    def test_identity_doc_lints_clean(self):
        result = subprocess.run(
            [sys.executable, DOCS_LINT, IDENTITY_DOC_PATH],
            cwd=REPO_ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0,
                         result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
