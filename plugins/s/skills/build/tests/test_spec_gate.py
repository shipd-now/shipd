#!/usr/bin/env python3
"""Tests for spec_gate.py — the context-sufficiency gate (context-gate
capability: context-gate-verb, context-sufficiency-checks,
ephemeral-insufficiency-report).

The gate is driven as a black box via subprocess against a throwaway temp repo
root laid out as ``.shipd/planned/<change>/{plan.md,specs/<cap>/spec.md,tasks.md}``
(and ``.shipd/verified/<cap>/spec.md`` masters), passed via ``--root`` — never
against the real repo change dirs. Mirrors the subprocess-against-temp-roots
style of ``test_spec_status.py``.

Written test-first; expected to FAIL until ``spec_gate.py`` lands (task 2.2)."""

import os
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.normpath(os.path.join(HERE, "..", "scripts", "spec_gate.py"))

CLEAN_DELTA = (
    "## ADDED Requirements\n\n"
    "### Requirement: Widget\n"
    "id: widget\n\n"
    "The system SHALL widget.\n\n"
    "#### Scenario: It works\n"
    "- **WHEN** something happens\n"
    "- **THEN** it is handled\n")

CLEAN_PLAN = (
    "# %s\n"
    "Status: %s\n\n"
    "## Idea\n\n"
    "A one-sentence summary.\n\n"
    "### Motivation\n\n"
    "Because reasons.\n\n"
    "### Details\n\n"
    "The concrete changes.\n\n"
    "### Non-goals\n\n"
    "Not that.\n\n"
    "## Implementation\n\n"
    "Carefully.\n")

CLEAN_TASKS = "# Tasks\n\n- [ ] 1.1 [req: widget] Do the widget.\n"


class SpecGateTestBase(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="spec-gate-test-")
        # Isolate $HOME so config resolution never reads the real home.
        self._base_home = tempfile.mkdtemp(prefix="spec-gate-basehome-")
        self._old_home = os.environ.get("HOME")
        os.environ["HOME"] = self._base_home
        # Redirect flow-time-series capture (the gate's promote/reject goes
        # through write_status) to a throwaway dir so no test writes to the real
        # ~/.shipd/builds/flow.jsonl. Subprocesses inherit this env var.
        self.flow_dir = tempfile.mkdtemp(prefix="spec-gate-flow-")
        self._old_flow = os.environ.get("AM_FLOW_LOG_DIR")
        os.environ["AM_FLOW_LOG_DIR"] = self.flow_dir

    def tearDown(self):
        if self._old_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = self._old_home
        if self._old_flow is None:
            os.environ.pop("AM_FLOW_LOG_DIR", None)
        else:
            os.environ["AM_FLOW_LOG_DIR"] = self._old_flow
        shutil.rmtree(self.flow_dir, ignore_errors=True)
        shutil.rmtree(self._base_home, ignore_errors=True)
        shutil.rmtree(self.root, ignore_errors=True)

    # -- fixture helpers ---------------------------------------------------

    def _change_dir(self, change):
        return os.path.join(self.root, ".shipd", "planned", change)

    def write_plan(self, change, text):
        cdir = self._change_dir(change)
        os.makedirs(cdir, exist_ok=True)
        with open(os.path.join(cdir, "plan.md"), "w", encoding="utf-8") as fh:
            fh.write(text)

    def write_tasks(self, change, text):
        cdir = self._change_dir(change)
        os.makedirs(cdir, exist_ok=True)
        with open(os.path.join(cdir, "tasks.md"), "w", encoding="utf-8") as fh:
            fh.write(text)

    def write_delta(self, change, capability, text):
        ddir = os.path.join(self._change_dir(change), "specs", capability)
        os.makedirs(ddir, exist_ok=True)
        with open(os.path.join(ddir, "spec.md"), "w", encoding="utf-8") as fh:
            fh.write(text)

    def write_master(self, capability, text):
        vdir = os.path.join(self.root, ".shipd", "verified", capability)
        os.makedirs(vdir, exist_ok=True)
        with open(os.path.join(vdir, "spec.md"), "w", encoding="utf-8") as fh:
            fh.write(text)

    def make_clean_change(self, change, status="draft"):
        """A fully lint-clean, context-clean ADDED-only change: the gate passes
        it. Individual tests then perturb exactly one facet."""
        self.write_plan(change, CLEAN_PLAN % (change, status))
        self.write_delta(change, "widget", CLEAN_DELTA)
        self.write_tasks(change, CLEAN_TASKS)

    def read_plan(self, change):
        with open(os.path.join(self._change_dir(change), "plan.md"),
                  encoding="utf-8") as fh:
            return fh.read()

    def cli(self, *args):
        return subprocess.run(
            ["python3", SCRIPT, "--root", self.root, *args],
            capture_output=True, text=True)

    def out(self, r):
        return r.stdout + r.stderr


class PassPathTest(SpecGateTestBase):
    def test_passing_gate_promotes_draft_to_ready(self):
        self.make_clean_change("feat", status="draft")
        r = self.cli("feat")
        self.assertEqual(r.returncode, 0, self.out(r))
        self.assertIn("Status: ready", self.read_plan("feat"))
        self.assertNotIn("Status: draft", self.read_plan("feat"))

    def test_passing_gate_leaves_ready(self):
        self.make_clean_change("feat", status="ready")
        r = self.cli("feat")
        self.assertEqual(r.returncode, 0, self.out(r))
        self.assertIn("Status: ready", self.read_plan("feat"))

    def test_passing_gate_removes_stale_section(self):
        # A clean change carrying a stale gate section from an earlier run.
        self.make_clean_change("feat", status="draft")
        self.write_plan(
            "feat",
            "# feat\nStatus: draft\n\n"
            "## Context insufficient\n\n"
            "Some earlier stale summary.\n\n- Old finding.\n\n"
            "## Idea\n\nA one-sentence summary.\n\n"
            "### Motivation\n\nBecause reasons.\n\n"
            "### Details\n\nThe concrete changes.\n\n"
            "### Non-goals\n\nNot that.\n\n"
            "## Implementation\n\nCarefully.\n")
        r = self.cli("feat")
        self.assertEqual(r.returncode, 0, self.out(r))
        text = self.read_plan("feat")
        self.assertNotIn("## Context insufficient", text)
        self.assertNotIn("Old finding", text)
        self.assertIn("Status: ready", text)

    def test_new_file_in_existing_directory_passes(self):
        # A backticked task path whose parent directory exists is the new-file
        # case: no file-reference finding, gate passes.
        os.makedirs(os.path.join(self.root, "plugins", "am"))
        self.make_clean_change("feat", status="draft")
        self.write_tasks(
            "feat",
            "# Tasks\n\n"
            "- [ ] 1.1 [req: widget] Create `plugins/s/brandnew.py`.\n")
        r = self.cli("feat")
        self.assertEqual(r.returncode, 0, self.out(r))
        self.assertIn("Status: ready", self.read_plan("feat"))

    def test_word_bounded_marker_negative_passes(self):
        # `subtodo` embeds `todo` but is not a word-bounded marker, so it is not
        # a placeholder finding: the gate passes.
        self.make_clean_change("feat", status="draft")
        self.write_tasks(
            "feat",
            "# Tasks\n\n- [ ] 1.1 [req: widget] Refactor the subtodo helper.\n")
        r = self.cli("feat")
        self.assertEqual(r.returncode, 0, self.out(r))


class UnknownChangeTest(SpecGateTestBase):
    def test_unknown_change_is_general_error(self):
        r = self.cli("no-such-change")
        self.assertEqual(r.returncode, 1)
        # Nothing was created for the phantom change.
        self.assertFalse(os.path.isdir(self._change_dir("no-such-change")))


class PlaceholderCheckTest(SpecGateTestBase):
    MARKERS = ["TBD", "TODO", "FIXME", "XXX", "???", "OPEN QUESTION"]

    def test_each_marker_rejects(self):
        for i, marker in enumerate(self.MARKERS):
            change = "marker-%d" % i
            self.make_clean_change(change, status="draft")
            self.write_tasks(
                change,
                "# Tasks\n\n- [ ] 1.1 [req: widget] Handle %s here.\n" % marker)
            with self.subTest(marker=marker):
                r = self.cli(change)
                self.assertEqual(r.returncode, 2, self.out(r))
                self.assertIn(marker, self.out(r))
                self.assertIn("tasks.md", self.out(r))
                self.assertIn("Status: rejected", self.read_plan(change))

    def test_marker_is_case_insensitive(self):
        self.make_clean_change("feat", status="draft")
        self.write_tasks(
            "feat",
            "# Tasks\n\n- [ ] 1.1 [req: widget] please handle todo items.\n")
        r = self.cli("feat")
        self.assertEqual(r.returncode, 2, self.out(r))
        self.assertIn("TODO", self.out(r))

    def test_marker_in_plan_names_plan(self):
        self.make_clean_change("feat", status="draft")
        self.write_plan(
            "feat",
            "# feat\nStatus: draft\n\n## Idea\n\nBecause TODO reasons.\n\n"
            "### Non-goals\n\nNot that.\n\n## Implementation\n\nCarefully.\n")
        r = self.cli("feat")
        self.assertEqual(r.returncode, 2, self.out(r))
        self.assertIn("plan.md", self.out(r))


class TaskFileReferenceCheckTest(SpecGateTestBase):
    def test_unresolvable_task_path_is_a_finding(self):
        self.make_clean_change("feat", status="draft")
        self.write_tasks(
            "feat",
            "# Tasks\n\n"
            "- [ ] 1.1 [req: widget] Edit `src/engine/missing.py`.\n")
        r = self.cli("feat")
        self.assertEqual(r.returncode, 2, self.out(r))
        self.assertIn("src/engine/missing.py", self.out(r))
        self.assertIn("Status: rejected", self.read_plan("feat"))

    def test_new_file_one_new_directory_deep_passes(self):
        # A new file one new directory deep: the parent directory is missing
        # but the grandparent exists (the new-skill / new-test-tree shape).
        # One new directory level is tolerated: no finding, gate passes.
        os.makedirs(os.path.join(self.root, "plugins", "s", "skills"))
        self.make_clean_change("feat", status="draft")
        self.write_tasks(
            "feat",
            "# Tasks\n\n"
            "- [ ] 1.1 [req: widget] Create "
            "`plugins/s/skills/research/SKILL.md`.\n")
        r = self.cli("feat")
        self.assertEqual(r.returncode, 0, self.out(r))
        self.assertIn("Status: ready", self.read_plan("feat"))

    def test_deep_dangling_path_is_still_a_finding(self):
        # Parent and grandparent both missing: still a finding, and its
        # message names the token and both missing levels.
        self.make_clean_change("feat", status="draft")
        self.write_tasks(
            "feat",
            "# Tasks\n\n"
            "- [ ] 1.1 [req: widget] Edit `src/ghost/nested/missing.py`.\n")
        r = self.cli("feat")
        self.assertEqual(r.returncode, 2, self.out(r))
        self.assertIn("src/ghost/nested/missing.py", self.out(r))
        self.assertIn("parent nor grandparent", self.out(r))
        self.assertIn("Status: rejected", self.read_plan("feat"))


class StaleBaseCheckTest(SpecGateTestBase):
    def test_stale_base_hash_is_a_finding(self):
        # A master exists; the MODIFIED delta's base hash does not match it.
        self.write_master(
            "auth",
            "# auth\n\n### Requirement: Login\nid: login\n\n"
            "The system SHALL log in.\n\n"
            "#### Scenario: Works\n- **WHEN** creds\n- **THEN** in\n")
        self.write_plan("feat", CLEAN_PLAN % ("feat", "draft"))
        self.write_delta(
            "feat", "auth",
            "## MODIFIED Requirements\n\n"
            "### Requirement: Login\n"
            "id: login\n"
            "base: 000000000000\n\n"
            "The system SHALL log in securely.\n\n"
            "#### Scenario: Works\n- **WHEN** creds\n- **THEN** in\n")
        self.write_tasks(
            "feat", "# Tasks\n\n- [ ] 1.1 [req: login] Harden login.\n")
        r = self.cli("feat")
        self.assertEqual(r.returncode, 2, self.out(r))
        self.assertIn("login", self.out(r))
        self.assertIn("Status: rejected", self.read_plan("feat"))


class DeltaTargetCheckTest(SpecGateTestBase):
    def test_modified_against_missing_capability_is_a_finding(self):
        # A MODIFIED delta whose capability has no master spec.
        self.write_plan("feat", CLEAN_PLAN % ("feat", "draft"))
        self.write_delta(
            "feat", "ghost",
            "## MODIFIED Requirements\n\n"
            "### Requirement: Orphan\n"
            "id: orphan-req\n"
            "base: 000000000000\n\n"
            "The system SHALL orphan.\n\n"
            "#### Scenario: Works\n- **WHEN** x\n- **THEN** y\n")
        self.write_tasks(
            "feat", "# Tasks\n\n- [ ] 1.1 [req: orphan-req] Touch orphan.\n")
        r = self.cli("feat")
        self.assertEqual(r.returncode, 2, self.out(r))
        self.assertIn("ghost", self.out(r))
        self.assertIn("Status: rejected", self.read_plan("feat"))

    def test_added_only_new_capability_passes(self):
        # An ADDED-only new capability with no master is legitimate.
        self.make_clean_change("feat", status="draft")
        r = self.cli("feat")
        self.assertEqual(r.returncode, 0, self.out(r))


class ReportShapeTest(SpecGateTestBase):
    def _section(self, text):
        """Return the lines of the `## Context insufficient` section (between
        its header and the next `## ` heading), or None when absent."""
        lines = text.splitlines()
        idx = next((i for i, ln in enumerate(lines)
                    if ln.strip() == "## Context insufficient"), None)
        if idx is None:
            return None
        out = []
        for ln in lines[idx + 1:]:
            if ln.startswith("## "):
                break
            out.append(ln)
        return out

    def test_report_lands_before_idea_with_summary_and_dotpoints(self):
        self.make_clean_change("feat", status="draft")
        self.write_tasks(
            "feat",
            "# Tasks\n\n- [ ] 1.1 [req: widget] Wire it (TODO decide key).\n")
        r = self.cli("feat")
        self.assertEqual(r.returncode, 2, self.out(r))
        text = self.read_plan("feat")
        lines = text.splitlines()
        sec_idx = next(i for i, ln in enumerate(lines)
                       if ln.strip() == "## Context insufficient")
        idea_idx = next(i for i, ln in enumerate(lines)
                        if ln.strip() == "## Idea")
        status_idx = next(i for i, ln in enumerate(lines)
                          if ln.startswith("Status:"))
        # Section sits after the header metadata and before the Idea.
        self.assertLess(status_idx, sec_idx)
        self.assertLess(sec_idx, idea_idx)
        section = self._section(text)
        # A summary paragraph (a non-empty, non-dotpoint line)...
        self.assertTrue(any(ln.strip() and not ln.lstrip().startswith("-")
                            for ln in section))
        # ...and at least one per-finding dot-point.
        self.assertTrue(any(ln.lstrip().startswith("-") for ln in section))

    def test_regate_replaces_without_accumulating(self):
        self.make_clean_change("feat", status="draft")
        self.write_tasks(
            "feat",
            "# Tasks\n\n- [ ] 1.1 [req: widget] Wire it (TODO decide key).\n")
        first = self.cli("feat")
        self.assertEqual(first.returncode, 2, self.out(first))
        # Re-gate the already-rejected, still-failing plan.
        second = self.cli("feat")
        self.assertEqual(second.returncode, 2, self.out(second))
        text = self.read_plan("feat")
        self.assertEqual(text.count("## Context insufficient"), 1)

    def test_header_title_status_epic_preserved(self):
        # Title and Epic lines survive byte-for-byte; only Status flips to
        # rejected (its own metadata-preserving write).
        self.write_plan(
            "feat",
            "# feat\nStatus: draft\nEpic: reporting-overhaul\n"
            "Theme: reliability\n\n"
            "## Idea\n\nBecause reasons.\n\n"
            "### Non-goals\n\nNot that.\n\n"
            "## Implementation\n\nCarefully.\n")
        self.write_delta("feat", "widget", CLEAN_DELTA)
        self.write_tasks(
            "feat",
            "# Tasks\n\n- [ ] 1.1 [req: widget] Wire it (TODO decide key).\n")
        r = self.cli("feat")
        self.assertEqual(r.returncode, 2, self.out(r))
        text = self.read_plan("feat")
        self.assertIn("# feat\n", text)               # title preserved
        self.assertIn("Epic: reporting-overhaul", text)  # epic preserved
        self.assertIn("Theme: reliability", text)     # metadata preserved
        self.assertIn("Status: rejected", text)
        self.assertNotIn("Status: draft", text)


class MalformedConfigTest(SpecGateTestBase):
    def test_malformed_config_is_one_error_line(self):
        # A `.shipd-config.json` that is not parseable JSON is a user-facing
        # failure: one `Error:` line on stderr, exit 1, never a traceback.
        self.make_clean_change("feat", status="draft")
        with open(os.path.join(self.root, ".shipd-config.json"), "w",
                  encoding="utf-8") as fh:
            fh.write("{ not json")
        r = self.cli("feat")
        self.assertEqual(r.returncode, 1, self.out(r))
        lines = r.stderr.splitlines()
        self.assertEqual(len(lines), 1, r.stderr)
        self.assertTrue(lines[0].startswith("Error: "), r.stderr)
        self.assertNotIn("Traceback", r.stderr)


if __name__ == "__main__":
    unittest.main()
