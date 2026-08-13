#!/usr/bin/env python3
"""Tests for spec_status.py — spec lifecycle status and current-spec selection.

The CLI is driven as a black box via subprocess against a throwaway temp repo
root laid out as ``.shipd/planned/<change>/{plan.md,tasks.md}`` and passed
via ``--root`` — never against the real repo change dirs. Mirrors the
subprocess-against-temp-roots style of ``test_claim_task.py``."""

import datetime
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.normpath(os.path.join(HERE, "..", "scripts", "spec_status.py"))

# The check-base tests compute expected content hashes with the very function
# the merge engine (and the verb) use, so a matching ``base:`` in a fixture
# delta stays matching regardless of the hash implementation.
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
import spec_common as sc  # noqa: E402


class SpecStatusTestBase(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="spec-status-test-")
        # Isolate $HOME so config resolution (the content directory, workspace
        # discovery) never reads the real home. Subclasses that drive the CLI
        # with an explicit env override their own HOME on top of this.
        self._base_home = tempfile.mkdtemp(prefix="spec-status-basehome-")
        self._old_home = os.environ.get("HOME")
        os.environ["HOME"] = self._base_home
        # Redirect flow-time-series capture (the write_status hook) to a
        # throwaway dir so no test writes to the real ~/.shipd/builds/flow.jsonl.
        # The CLI subprocesses inherit this env var.
        self.flow_dir = tempfile.mkdtemp(prefix="spec-status-flow-")
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

    def flow_records(self):
        """Every flow.jsonl record captured under this test's flow dir."""
        path = os.path.join(self.flow_dir, "flow.jsonl")
        records = []
        try:
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        records.append(json.loads(line))
        except OSError:
            pass
        return records

    def declare_workspace(self, registry=None, root=None):
        """Declare ``registry`` (default ``{}``) as the ``workspace`` object in
        ``<root>/.shipd-config.json`` — the config-file workspace marker."""
        target = root if root is not None else self.root
        data = {"workspace": registry if registry is not None else {}}
        with open(os.path.join(target, ".shipd-config.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(data, fh)

    # -- fixture helpers ---------------------------------------------------

    def make_change(self, change, status=None, tasks=None):
        """Create .shipd/planned/<change>/ with an optional plan header
        and optional tasks.md body."""
        cdir = os.path.join(self.root, ".shipd", "planned", change)
        os.makedirs(cdir)
        if status is not None:
            with open(os.path.join(cdir, "plan.md"), "w",
                      encoding="utf-8") as fh:
                fh.write("# %s\nStatus: %s\n\n## Idea\nA summary.\n\n"
                         "### Motivation\nBecause.\n\n"
                         "### Details\nThe changes.\n\n"
                         "### Non-goals\nNot that.\n\n"
                         "## Implementation\nCarefully.\n"
                         % (change, status))
        if tasks is not None:
            with open(os.path.join(cdir, "tasks.md"), "w",
                      encoding="utf-8") as fh:
                fh.write(tasks)
        return cdir

    def write_plan(self, change, text):
        cdir = os.path.join(self.root, ".shipd", "planned", change)
        os.makedirs(cdir, exist_ok=True)
        with open(os.path.join(cdir, "plan.md"), "w",
                  encoding="utf-8") as fh:
            fh.write(text)

    def read_plan(self, change):
        path = os.path.join(
            self.root, ".shipd", "planned", change, "plan.md")
        with open(path, encoding="utf-8") as fh:
            return fh.read()

    def make_valid_delta(self, change):
        """Add a lint-clean delta spec so ``lint_change`` reports no errors —
        needed for the transition guards, which require a change to validate
        before ``ready``/``active``/``complete``/``verified`` may be set."""
        specs = os.path.join(
            self.root, ".shipd", "planned", change, "specs", "example")
        os.makedirs(specs, exist_ok=True)
        with open(os.path.join(specs, "spec.md"), "w",
                  encoding="utf-8") as fh:
            fh.write(
                "## ADDED Requirements\n\n"
                "### Requirement: Example\n"
                "id: example\n\n"
                "The system SHALL do a thing.\n\n"
                "#### Scenario: It works\n"
                "- **WHEN** something happens\n"
                "- **THEN** it is handled\n")

    def cli(self, *args):
        return subprocess.run(
            ["python3", SCRIPT, "--root", self.root, *args],
            capture_output=True, text=True)

    def state(self):
        path = os.path.join(self.root, ".shipd", "state.json")
        if not os.path.exists(path):
            return None
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)


class UseCurrentTest(SpecStatusTestBase):
    def test_use_current_round_trip(self):
        self.make_change("dark-mode", status="ready")
        r = self.cli("use", "dark-mode")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "dark-mode")
        self.assertEqual(self.state(), {"current_spec": "dark-mode"})

        cur = self.cli("current")
        self.assertEqual(cur.returncode, 0)
        self.assertEqual(cur.stdout.strip(), "dark-mode")

    def test_current_empty_when_none_selected(self):
        cur = self.cli("current")
        self.assertEqual(cur.returncode, 0)
        self.assertEqual(cur.stdout.strip(), "")

    def test_unknown_change_rejected_and_selection_unchanged(self):
        self.make_change("real-one", status="ready")
        self.assertEqual(self.cli("use", "real-one").returncode, 0)

        bad = self.cli("use", "ghost")
        self.assertEqual(bad.returncode, 1)
        self.assertIn("Error:", bad.stderr)
        # Previous selection is unchanged.
        self.assertEqual(self.state(), {"current_spec": "real-one"})

    def test_completed_change_is_not_selectable(self):
        # Applied changes live in the sibling .shipd/completed/, not .shipd/planned/,
        # so `use` must reject a completed change name.
        os.makedirs(os.path.join(
            self.root, ".shipd", "completed", "2026-07-25-done-change"))
        bad = self.cli("use", "2026-07-25-done-change")
        self.assertEqual(bad.returncode, 1)
        self.assertIn("Error:", bad.stderr)


class ShowTest(SpecStatusTestBase):
    def test_show_status_and_progress(self):
        self.make_change(
            "feat", status="active",
            tasks="## 1\n- [x] 1.1 done\n- [ ] 1.2 todo\n- [~] 1.3 wip\n")
        r = self.cli("show", "feat")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "feat: active (1/3 tasks)")

    def test_show_omits_counts_without_tasks(self):
        self.make_change("feat", status="ready")
        r = self.cli("show", "feat")
        self.assertEqual(r.stdout.strip(), "feat: ready")

    def test_show_question_mark_for_missing_header(self):
        self.write_plan("feat", "no header here at all\n")
        r = self.cli("show", "feat")
        self.assertEqual(r.stdout.strip(), "feat: ?")

    def test_show_defaults_to_selection(self):
        self.make_change("feat", status="draft")
        self.cli("use", "feat")
        r = self.cli("show")
        self.assertEqual(r.stdout.strip(), "feat: draft")


class SetStatusTest(SpecStatusTestBase):
    def test_set_status_rewrites_existing_status(self):
        self.make_change("feat", status="ready")
        self.make_valid_delta("feat")
        r = self.cli("set-status", "active", "feat")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "active")
        self.assertIn("Status: active", self.read_plan("feat"))
        self.assertNotIn("Status: ready", self.read_plan("feat"))

    def test_set_status_invalid_value_writes_nothing(self):
        self.make_change("feat", status="ready")
        self.make_valid_delta("feat")
        before = self.read_plan("feat")
        r = self.cli("set-status", "in-progress", "feat")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Error:", r.stderr)
        self.assertEqual(self.read_plan("feat"), before)

    def test_set_status_inserts_header_when_absent(self):
        # draft has no guards, so a bare plan can still receive a header.
        self.write_plan("feat", "## Why\nreasons\n")
        r = self.cli("set-status", "draft", "feat")
        self.assertEqual(r.returncode, 0)
        text = self.read_plan("feat")
        self.assertTrue(text.startswith("# feat\nStatus: draft\n"))
        self.assertIn("## Why", text)

    def test_set_status_no_selection_errors(self):
        r = self.cli("set-status", "active")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Error:", r.stderr)

    def test_set_status_missing_plan_errors(self):
        # Change dir exists but carries no plan.md → the error names plan.md.
        self.make_change("feat")
        r = self.cli("set-status", "draft", "feat")
        self.assertEqual(r.returncode, 1)
        self.assertIn("plan.md not found for change 'feat'", r.stderr)


class GuardTest(SpecStatusTestBase):
    def test_complete_refused_while_tasks_open(self):
        # 7 of 10 done, 1 in progress → complete is refused (exit 3).
        self.make_change(
            "feat", status="active",
            tasks="## 1\n"
                  "- [x] a [req: example]\n- [x] b [req: example]\n"
                  "- [x] c [req: example]\n- [x] d [req: example]\n"
                  "- [x] e [req: example]\n- [x] f [req: example]\n"
                  "- [x] g [req: example]\n- [ ] h [req: example]\n"
                  "- [ ] i [req: example]\n- [~] j [req: example]\n")
        self.make_valid_delta("feat")
        before = self.read_plan("feat")
        r = self.cli("set-status", "complete", "feat")
        self.assertEqual(r.returncode, 3)
        self.assertTrue(r.stderr.startswith("Refused: "))
        self.assertIn("7/10 done", r.stderr)
        self.assertEqual(self.read_plan("feat"), before)

    def test_ready_refused_when_change_does_not_validate(self):
        # No specs/ dir → lint_change reports errors → ready is refused.
        self.make_change("feat", status="draft")
        before = self.read_plan("feat")
        r = self.cli("set-status", "ready", "feat")
        self.assertEqual(r.returncode, 3)
        self.assertTrue(r.stderr.startswith("Refused: "))
        # The individual validation errors follow the reason line.
        self.assertIn("delta specs", r.stderr)
        self.assertEqual(self.read_plan("feat"), before)

    def test_force_bypasses_guards(self):
        self.make_change(
            "feat", status="active",
            tasks="## 1\n- [x] a\n- [ ] b\n")
        r = self.cli("set-status", "complete", "feat", "--force")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "complete")
        self.assertIn("Status: complete", self.read_plan("feat"))

    def test_force_still_rejects_invalid_value(self):
        self.make_change(
            "feat", status="active",
            tasks="## 1\n- [ ] a\n")
        before = self.read_plan("feat")
        r = self.cli("set-status", "done", "feat", "--force")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Error:", r.stderr)
        self.assertEqual(self.read_plan("feat"), before)

    def test_draft_target_needs_no_guards(self):
        # Structurally invalid (no specs/ dir), but draft has no guards.
        self.make_change("feat", status="active")
        r = self.cli("set-status", "draft", "feat")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "draft")
        self.assertIn("Status: draft", self.read_plan("feat"))


class RejectedStatusTest(SpecStatusTestBase):
    """The sixth lifecycle status ``rejected`` (spec-status
    status-lifecycle-stages, transition-guards, status-cli): the
    context-sufficiency gate's parking state. ``set-status rejected`` carries
    no structural guard, ``sync`` never re-derives a rejected plan, and the
    invalid-value error still names all six statuses.

    Written test-first; expected to FAIL until ``rejected`` joins ``STATUSES``
    in ``spec_status.py`` (task 1.2)."""

    def test_set_status_rejected_needs_no_structural_validity(self):
        # No specs/ dir → the change fails structural validation, yet targeting
        # `rejected` requires nothing, so the write succeeds (exit 0).
        self.make_change("feat", status="draft")
        r = self.cli("set-status", "rejected", "feat")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "rejected")
        self.assertIn("Status: rejected", self.read_plan("feat"))

    def test_sync_leaves_rejected_untouched(self):
        # All tasks done would derive `complete`; a rejected plan is left as-is.
        self.make_change(
            "feat", status="rejected",
            tasks="## 1\n- [x] 1.1 done\n- [x] 1.2 done\n")
        r = self.cli("sync", "feat")
        self.assertEqual(r.stdout.strip(), "rejected")
        self.assertIn("Status: rejected", self.read_plan("feat"))

    def test_set_status_unknown_value_names_all_six(self):
        self.make_change("feat", status="draft")
        before = self.read_plan("feat")
        r = self.cli("set-status", "bogus", "feat")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Error:", r.stderr)
        for status in ("draft", "ready", "active", "complete", "verified",
                       "rejected"):
            self.assertIn(status, r.stderr)
        self.assertEqual(self.read_plan("feat"), before)


class ValidateTest(SpecStatusTestBase):
    def test_validate_ok_on_valid_change(self):
        self.make_change("feat", status="ready")
        self.make_valid_delta("feat")
        r = self.cli("validate", "feat")
        self.assertEqual(r.returncode, 0)
        self.assertIn("OK", r.stdout)

    def test_validate_reports_errors_on_invalid_change(self):
        self.make_change("feat", status="ready")  # no specs/ dir
        r = self.cli("validate", "feat")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("ERROR", r.stderr)


class StatusVerbTest(SpecStatusTestBase):
    def test_status_prints_bare_value(self):
        self.make_change("feat", status="active")
        r = self.cli("status", "feat")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "active")

    def test_status_question_mark_when_missing_or_invalid(self):
        self.write_plan("feat", "no header here at all\n")
        r = self.cli("status", "feat")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "?")

    def test_status_defaults_to_selection(self):
        self.make_change("feat", status="ready")
        self.cli("use", "feat")
        r = self.cli("status")
        self.assertEqual(r.stdout.strip(), "ready")


class SyncTest(SpecStatusTestBase):
    def test_sync_ready_to_active(self):
        self.make_change(
            "feat", status="ready",
            tasks="## 1\n- [x] 1.1 done\n- [ ] 1.2 todo\n")
        r = self.cli("sync", "feat")
        self.assertEqual(r.stdout.strip(), "active")
        self.assertIn("Status: active", self.read_plan("feat"))

    def test_sync_active_to_complete(self):
        self.make_change(
            "feat", status="active",
            tasks="## 1\n- [x] 1.1 done\n- [x] 1.2 done\n")
        r = self.cli("sync", "feat")
        self.assertEqual(r.stdout.strip(), "complete")
        self.assertIn("Status: complete", self.read_plan("feat"))

    def test_sync_demotes_complete_to_active(self):
        # A task was released (back to unchecked) after reaching complete.
        self.make_change(
            "feat", status="complete",
            tasks="## 1\n- [x] 1.1 done\n- [ ] 1.2 todo\n")
        r = self.cli("sync", "feat")
        self.assertEqual(r.stdout.strip(), "active")
        self.assertIn("Status: active", self.read_plan("feat"))

    def test_sync_ready_when_none_started(self):
        self.make_change(
            "feat", status="active",
            tasks="## 1\n- [ ] 1.1 todo\n- [ ] 1.2 todo\n")
        r = self.cli("sync", "feat")
        self.assertEqual(r.stdout.strip(), "ready")

    def test_sync_leaves_draft_untouched(self):
        self.make_change(
            "feat", status="draft",
            tasks="## 1\n- [x] 1.1 done\n- [x] 1.2 done\n")
        r = self.cli("sync", "feat")
        self.assertEqual(r.stdout.strip(), "draft")
        self.assertIn("Status: draft", self.read_plan("feat"))

    def test_sync_leaves_verified_untouched(self):
        self.make_change(
            "feat", status="verified",
            tasks="## 1\n- [ ] 1.1 todo\n- [ ] 1.2 todo\n")
        r = self.cli("sync", "feat")
        self.assertEqual(r.stdout.strip(), "verified")
        self.assertIn("Status: verified", self.read_plan("feat"))

    def test_sync_no_selection_errors(self):
        r = self.cli("sync")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Error:", r.stderr)


class MetadataPreservationTest(SpecStatusTestBase):
    """Header metadata survives status writes and surfaces in ``show``
    (spec-status metadata-preserving-status-writes)."""

    PLAN = ("# feat\nStatus: ready\nProfile: lite\nTheme: reliability\n\n"
            "## Idea\nA summary.\n\n### Motivation\nWhy.\n\n"
            "### Details\nThe changes.\n\n### Non-goals\nNot that.\n\n"
            "## Implementation\nHow.\n")

    def test_set_status_preserves_metadata_byte_for_byte(self):
        self.write_plan("feat", self.PLAN)
        # draft has no guards, so no delta setup is needed.
        r = self.cli("set-status", "draft", "feat")
        self.assertEqual(r.returncode, 0)
        text = self.read_plan("feat")
        self.assertIn("Status: draft", text)
        self.assertNotIn("Status: ready", text)
        # The metadata block is untouched, byte-for-byte.
        self.assertIn("Profile: lite\nTheme: reliability\n", text)

    def test_show_displays_metadata(self):
        self.write_plan("feat", self.PLAN)
        r = self.cli("show", "feat")
        self.assertEqual(r.returncode, 0)
        self.assertIn("Profile: lite", r.stdout)
        self.assertIn("Theme: reliability", r.stdout)


class EpicVerbTest(SpecStatusTestBase):
    """The three epic status verbs (spec-status epic-status-verbs):
    ``epic-show``, ``epic-sync``, ``epic-set-status``.

    Written test-first; expected to FAIL until the verbs land in
    ``spec_status.py`` (task 2.2)."""

    def make_epic(self, slug, status="draft", metadata=None, rows=None):
        """Write .shipd/epics/<slug>/epic.md with a conforming header and stub
        table. ``metadata`` is a list of ``Key: value`` header lines; ``rows``
        is a list of (slug, description, (r1, r2, r3, r4)) tuples."""
        edir = os.path.join(self.root, ".shipd", "epics", slug)
        os.makedirs(edir, exist_ok=True)
        if rows is None:
            rows = [("csv-export", "Export as CSV",
                     ("low", "medium", "low", "low"))]
        table = [
            "| Change | Description | Code | Integration | Unknowns | Risk |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for rslug, desc, ratings in rows:
            table.append("| %s | %s | %s |" % (rslug, desc, " | ".join(ratings)))
        header = ["# %s" % slug, "Status: %s" % status]
        if metadata:
            header.extend(metadata)
        text = ("\n".join(header) + "\n\n"
                "## Introduction\n\nWhy it matters.\n\n"
                "### Non-goals\n\n- Not that.\n\n"
                "## Decisions\n\nWhy.\n\n"
                "## Design\n\nHow.\n\n"
                "## Changes\n\n" + "\n".join(table) + "\n")
        with open(os.path.join(edir, "epic.md"), "w", encoding="utf-8") as fh:
            fh.write(text)
        return edir

    def write_epic_raw(self, slug, text):
        edir = os.path.join(self.root, ".shipd", "epics", slug)
        os.makedirs(edir, exist_ok=True)
        with open(os.path.join(edir, "epic.md"), "w", encoding="utf-8") as fh:
            fh.write(text)

    def read_epic(self, slug):
        with open(os.path.join(self.root, ".shipd", "epics", slug, "epic.md"),
                  encoding="utf-8") as fh:
            return fh.read()

    def make_completed(self, slug, date="2026-01-01"):
        os.makedirs(os.path.join(
            self.root, ".shipd", "completed", "%s-%s" % (date, slug)))

    # -- epic-show ---------------------------------------------------------

    def test_epic_show_lists_status_metadata_and_members(self):
        self.make_epic(
            "reporting-overhaul", status="active",
            metadata=["Theme: reliability", "Initiative: mvp-readiness"],
            rows=[
                ("csv-export", "CSV", ("low", "low", "low", "low")),
                ("pdf-export", "PDF", ("high", "high", "high", "high")),
                ("new-thing", "TBD", ("low", "low", "low", "low")),
            ])
        self.make_completed("csv-export")          # archived
        self.make_change("pdf-export", status="active")  # planned, active
        # new-thing has neither a completed nor a planned dir → unplanned.
        r = self.cli("epic-show", "reporting-overhaul")
        self.assertEqual(r.returncode, 0)
        out = r.stdout
        self.assertIn("reporting-overhaul: active", out)
        self.assertIn("Theme: reliability", out)
        self.assertIn("Initiative: mvp-readiness", out)
        self.assertIn("csv-export: archived", out)
        self.assertIn("pdf-export: active", out)
        self.assertIn("new-thing: unplanned", out)

    # -- epic-sync ---------------------------------------------------------

    def test_epic_sync_ready_when_nothing_started(self):
        self.make_epic(
            "e", status="ready",
            rows=[("member-a", "A", ("low",) * 4),
                  ("member-b", "B", ("low",) * 4)])
        # Both members unplanned → nothing started → ready.
        r = self.cli("epic-sync", "e")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "ready")
        self.assertIn("Status: ready", self.read_epic("e"))

    def test_epic_sync_active_from_one_started_member(self):
        self.make_epic(
            "e", status="ready",
            rows=[("member-a", "A", ("low",) * 4),
                  ("member-b", "B", ("low",) * 4)])
        self.make_change("member-a", status="active")
        r = self.cli("epic-sync", "e")
        self.assertEqual(r.stdout.strip(), "active")
        self.assertIn("Status: active", self.read_epic("e"))

    def test_epic_sync_complete_when_all_archived(self):
        self.make_epic(
            "e", status="active",
            rows=[("member-a", "A", ("low",) * 4),
                  ("member-b", "B", ("low",) * 4)])
        self.make_completed("member-a")
        self.make_completed("member-b")
        r = self.cli("epic-sync", "e")
        self.assertEqual(r.stdout.strip(), "complete")
        self.assertIn("Status: complete", self.read_epic("e"))

    def test_epic_sync_never_touches_draft(self):
        self.make_epic(
            "e", status="draft",
            rows=[("member-a", "A", ("low",) * 4)])
        self.make_completed("member-a")  # would derive complete if not draft
        r = self.cli("epic-sync", "e")
        self.assertEqual(r.stdout.strip(), "draft")
        self.assertIn("Status: draft", self.read_epic("e"))

    # -- epic-set-status ---------------------------------------------------

    def test_epic_set_status_ready_refused_on_invalid_epic(self):
        # An epic missing its ## Changes section fails structural validation.
        self.write_epic_raw(
            "e",
            "# e\nStatus: draft\n\n## Decisions\n\nWhy.\n\n## Design\n\nHow.\n")
        before = self.read_epic("e")
        r = self.cli("epic-set-status", "ready", "e")
        self.assertEqual(r.returncode, 3)
        self.assertTrue(r.stderr.startswith("Refused: "))
        self.assertEqual(self.read_epic("e"), before)

    def test_epic_set_status_invalid_value_exits_one(self):
        # `verified` is not an epic status.
        self.make_epic("e", status="draft")
        before = self.read_epic("e")
        r = self.cli("epic-set-status", "verified", "e")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Error:", r.stderr)
        self.assertEqual(self.read_epic("e"), before)

    def test_epic_set_status_ready_succeeds_on_valid_epic(self):
        self.make_epic("e", status="draft")
        r = self.cli("epic-set-status", "ready", "e")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "ready")
        self.assertIn("Status: ready", self.read_epic("e"))


class MainCheckoutWarnTest(EpicVerbTest):
    """The main-checkout epic write warning (spec-status
    main-checkout-epic-write-warning): an actual epic-file write in a main
    checkout (root ``.git`` is a directory) prints a one-line stderr warning;
    a linked worktree (``.git`` is a file), a no-op sync, and a root with no
    ``.git`` at all stay silent. Exit codes are never affected.

    Written test-first; expected to FAIL until ``_is_main_checkout`` and the
    warning land in ``spec_status.py`` (task 1.2)."""

    def make_git_dir(self):
        """Shape the temp root as a main checkout: ``.git`` is a directory."""
        os.makedirs(os.path.join(self.root, ".git"), exist_ok=True)

    def make_git_file(self):
        """Shape the temp root as a linked worktree: ``.git`` is a file."""
        with open(os.path.join(self.root, ".git"), "w",
                  encoding="utf-8") as fh:
            fh.write("gitdir: /elsewhere/.git/worktrees/wt\n")

    def test_main_checkout_write_warns(self):
        self.make_git_dir()
        self.make_epic("e", status="draft")
        r = self.cli("epic-set-status", "active", "e")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "active")
        self.assertIn("Warning:", r.stderr)
        self.assertIn("main checkout", r.stderr)
        # The warning names the epic file that was written.
        self.assertIn(
            os.path.join(".shipd", "epics", "e", "epic.md"), r.stderr)
        # One line of warning, not a wall of noise.
        warn_lines = [ln for ln in r.stderr.splitlines()
                      if "Warning:" in ln]
        self.assertEqual(len(warn_lines), 1)
        self.assertIn("Status: active", self.read_epic("e"))

    def test_worktree_write_stays_silent(self):
        self.make_git_file()
        self.make_epic("e", status="draft")
        r = self.cli("epic-set-status", "active", "e")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "active")
        self.assertNotIn("Warning:", r.stderr)
        self.assertIn("Status: active", self.read_epic("e"))

    def test_no_op_sync_stays_silent(self):
        self.make_git_dir()
        # All members unplanned → derives ``ready``; the epic already carries
        # ``ready`` → the sync writes nothing and must stay silent.
        self.make_epic(
            "e", status="ready",
            rows=[("member-a", "A", ("low",) * 4),
                  ("member-b", "B", ("low",) * 4)])
        r = self.cli("epic-sync", "e")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "ready")
        self.assertNotIn("Warning:", r.stderr)

    def test_no_git_at_root_stays_silent(self):
        # setUp's bare temp root has no .git of any kind.
        self.make_epic("e", status="draft")
        r = self.cli("epic-set-status", "active", "e")
        self.assertEqual(r.returncode, 0)
        self.assertNotIn("Warning:", r.stderr)
        self.assertIn("Status: active", self.read_epic("e"))


class MemberStateWorktreeTest(EpicVerbTest):
    """``_member_state`` probes the invocation root's ``planned/`` then each
    ``.worktrees/<name>`` directory, in sorted name order, exactly as
    ``cmd_locate`` does (spec-status epic-status-verbs).

    Exercised through ``epic-show``, which prints one ``<mslug>: <state>``
    line per stub member.

    Written test-first; expected to FAIL until the worktree-aware probe lands
    in ``spec_status.py`` (task 2.2)."""

    def make_worktree_change(self, worktree, change, status):
        """Create .worktrees/<worktree>/.shipd/planned/<change>/plan.md with the
        given status — a change installed under a sibling worktree root."""
        cdir = os.path.join(
            self.root, ".worktrees", worktree, ".shipd", "planned", change)
        os.makedirs(cdir)
        with open(os.path.join(cdir, "plan.md"), "w", encoding="utf-8") as fh:
            fh.write("# %s\nStatus: %s\n\n## Idea\nA summary.\n\n"
                     "### Motivation\nBecause.\n\n### Details\nThe changes.\n\n"
                     "### Non-goals\nNot that.\n\n## Implementation\nCarefully.\n"
                     % (change, status))
        return os.path.join(self.root, ".worktrees", worktree)

    def test_member_planned_only_in_worktree_is_not_unplanned(self):
        self.make_epic(
            "e", status="ready", rows=[("member-a", "A", ("low",) * 4)])
        self.make_worktree_change("member-a", "member-a", "ready")
        r = self.cli("epic-show", "e")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("member-a: ready", r.stdout)

    def test_invocation_root_wins_over_worktree(self):
        self.make_epic(
            "e", status="ready", rows=[("member-a", "A", ("low",) * 4)])
        self.make_change("member-a", status="active")
        self.make_worktree_change("member-a", "member-a", "rejected")
        r = self.cli("epic-show", "e")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("member-a: active", r.stdout)

    def test_member_absent_everywhere_is_unplanned(self):
        self.make_epic(
            "e", status="ready", rows=[("member-a", "A", ("low",) * 4)])
        # A worktree exists but carries no change for this slug, so the probe
        # must fall through every candidate before landing on `unplanned`.
        self.make_worktree_change("member-a", "some-other-change", "active")
        r = self.cli("epic-show", "e")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("member-a: unplanned", r.stdout)

    def test_unreadable_worktree_config_is_skipped(self):
        self.make_epic(
            "e", status="ready", rows=[("member-a", "A", ("low",) * 4)])
        wt = os.path.join(self.root, ".worktrees", "member-a")
        os.makedirs(wt)
        with open(os.path.join(wt, ".shipd-config.json"), "w",
                  encoding="utf-8") as fh:
            fh.write("{not valid json")
        r = self.cli("epic-show", "e")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("member-a: unplanned", r.stdout)


class InitiativeVerbTest(SpecStatusTestBase):
    """The three initiative status verbs (spec-status initiative-status-verbs):
    ``initiative-show``, ``initiative-sync``, ``initiative-set-status``.

    ``self.root`` doubles as the workspace root (its ``.shipd-config.json``
    declares ``workspace`` so ``find_workspace_root`` resolves there); briefs
    live at ``<root>/.shipd/initiatives/<slug>/brief.md``. The no-workspace cases
    simply omit the declaration, and no ancestor of the system temp dir carries
    one."""

    def make_workspace(self):
        self.declare_workspace()

    def write_brief(self, slug, status="open", requirements=None,
                    metadata=None):
        bdir = os.path.join(self.root, ".shipd", "initiatives", slug)
        os.makedirs(bdir, exist_ok=True)
        if requirements is None:
            requirements = ["- [ ] Do it"]
        header = ["# %s" % slug, "Status: %s" % status]
        if metadata:
            header.extend(metadata)
        text = ("\n".join(header) + "\n\nGoal prose.\n\n## Requirements\n\n"
                + "\n".join(requirements) + "\n")
        with open(os.path.join(bdir, "brief.md"), "w", encoding="utf-8") as fh:
            fh.write(text)

    def read_brief(self, slug):
        with open(os.path.join(self.root, ".shipd", "initiatives", slug,
                               "brief.md"), encoding="utf-8") as fh:
            return fh.read()

    # -- initiative-show ---------------------------------------------------

    def test_initiative_show_lists_status_metadata_and_progress(self):
        self.make_workspace()
        self.write_brief(
            "mvp-readiness", status="open", metadata=["Project: alpha"],
            requirements=["- [x] First outcome", "- [ ] Second outcome",
                          "- [ ] Third outcome"])
        r = self.cli("initiative-show", "mvp-readiness")
        self.assertEqual(r.returncode, 0)
        out = r.stdout
        self.assertIn("mvp-readiness: open", out)
        self.assertIn("Project: alpha", out)
        self.assertIn("1/3", out)
        self.assertIn("First outcome", out)
        self.assertIn("Second outcome", out)

    # -- initiative-sync ---------------------------------------------------

    def test_initiative_sync_derives_achieved(self):
        self.make_workspace()
        self.write_brief("mvp-readiness", status="open",
                         requirements=["- [x] a", "- [x] b"])
        r = self.cli("initiative-sync", "mvp-readiness")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "achieved")
        self.assertIn("Status: achieved", self.read_brief("mvp-readiness"))

    def test_initiative_sync_derives_open_when_any_unticked(self):
        self.make_workspace()
        self.write_brief("mvp-readiness", status="achieved",
                         requirements=["- [x] a", "- [ ] b"])
        r = self.cli("initiative-sync", "mvp-readiness")
        self.assertEqual(r.stdout.strip(), "open")
        self.assertIn("Status: open", self.read_brief("mvp-readiness"))

    def test_initiative_sync_never_touches_dropped(self):
        self.make_workspace()
        self.write_brief("mvp-readiness", status="dropped",
                         requirements=["- [x] a", "- [x] b"])
        r = self.cli("initiative-sync", "mvp-readiness")
        self.assertEqual(r.stdout.strip(), "dropped")
        self.assertIn("Status: dropped", self.read_brief("mvp-readiness"))

    # -- initiative-set-status ---------------------------------------------

    def test_initiative_set_status_writes_valid_value(self):
        self.make_workspace()
        self.write_brief("mvp-readiness", status="open")
        r = self.cli("initiative-set-status", "achieved", "mvp-readiness")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "achieved")
        self.assertIn("Status: achieved", self.read_brief("mvp-readiness"))

    def test_initiative_set_status_invalid_value_errors(self):
        self.make_workspace()
        self.write_brief("mvp-readiness", status="open")
        before = self.read_brief("mvp-readiness")
        r = self.cli("initiative-set-status", "pending", "mvp-readiness")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Error:", r.stderr)
        self.assertEqual(self.read_brief("mvp-readiness"), before)

    # -- no workspace ------------------------------------------------------

    def test_verbs_require_a_workspace(self):
        # No marker written → no discoverable workspace from self.root.
        for argv in (["initiative-show", "mvp-readiness"],
                     ["initiative-sync", "mvp-readiness"],
                     ["initiative-set-status", "achieved", "mvp-readiness"]):
            r = self.cli(*argv)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("no workspace", r.stderr.lower())


class WorkspaceShowTest(SpecStatusTestBase):
    """The ``workspace-show`` and ``project-show`` status verbs (spec-status
    workspace-status-verbs).

    ``self.root`` doubles as the workspace root (its ``.shipd-config.json``
    declares ``workspace`` so ``find_workspace_root`` resolves there). Project
    repo paths are workspace-root-relative; a ``(absent)`` annotation marks a
    path that is not a directory on this machine. The no-workspace cases omit
    the declaration, and no ancestor of the system temp dir carries one."""

    def make_workspace(self, registry):
        self.declare_workspace(registry)

    def write_brief(self, slug, status="open", project=None,
                    requirements=None):
        bdir = os.path.join(self.root, ".shipd", "initiatives", slug)
        os.makedirs(bdir, exist_ok=True)
        if requirements is None:
            requirements = ["- [ ] Do it"]
        header = ["# %s" % slug, "Status: %s" % status]
        if project is not None:
            header.append("Project: %s" % project)
        text = ("\n".join(header) + "\n\nGoal prose.\n\n## Requirements\n\n"
                + "\n".join(requirements) + "\n")
        with open(os.path.join(bdir, "brief.md"), "w", encoding="utf-8") as fh:
            fh.write(text)

    def _standard_workspace(self):
        """A workspace declaring project ``alpha`` with one present repo
        (``present-repo``) and one absent repo (``absent-repo``), plus an
        initiative ``mvp-readiness`` scoped ``Project: alpha``."""
        os.makedirs(os.path.join(self.root, "present-repo"), exist_ok=True)
        self.make_workspace({"projects": {
            "alpha": {"repos": ["present-repo", "absent-repo"]}}})
        self.write_brief("mvp-readiness", status="open", project="alpha")

    def write_context(self, slug, text="Steering prose.\n"):
        cdir = os.path.join(self.root, ".shipd", "projects", slug)
        os.makedirs(cdir, exist_ok=True)
        with open(os.path.join(cdir, "context.md"), "w",
                  encoding="utf-8") as fh:
            fh.write(text)

    # -- workspace-show ----------------------------------------------------

    def test_workspace_show_lists_projects_and_initiatives(self):
        self._standard_workspace()
        r = self.cli("workspace-show")
        self.assertEqual(r.returncode, 0)
        out = r.stdout
        self.assertIn(self.root, out)          # the workspace root
        self.assertIn("alpha", out)
        self.assertIn("present-repo", out)
        self.assertIn("absent-repo", out)
        self.assertIn("(absent)", out)         # absent repo annotated
        self.assertIn("context: no", out)
        self.assertIn("mvp-readiness", out)    # initiative with status + scope
        self.assertIn("open", out)
        # The current repo (== ws root) resolves to no declared project.
        self.assertIn("implicit default", out)

    def test_workspace_show_reports_context_present(self):
        self._standard_workspace()
        self.write_context("alpha")
        r = self.cli("workspace-show")
        self.assertEqual(r.returncode, 0)
        self.assertIn("context: yes", r.stdout)

    def test_workspace_show_prints_focus_when_declared(self):
        os.makedirs(os.path.join(self.root, "present-repo"), exist_ok=True)
        self.make_workspace({"focus": "alpha", "projects": {
            "alpha": {"repos": ["present-repo"]}}})
        r = self.cli("workspace-show")
        self.assertEqual(r.returncode, 0)
        self.assertIn("focus", r.stdout)
        self.assertIn("alpha", r.stdout)

    def test_workspace_show_omits_focus_when_absent(self):
        self._standard_workspace()
        r = self.cli("workspace-show")
        self.assertEqual(r.returncode, 0)
        self.assertNotIn("focus", r.stdout)

    def test_workspace_show_annotates_url_entries(self):
        os.makedirs(os.path.join(self.root, "present-repo"), exist_ok=True)
        self.make_workspace({"projects": {
            "alpha": {"repos": [
                {"path": "present-repo",
                 "url": "git@example.com:present.git"}]}}})
        r = self.cli("workspace-show")
        self.assertEqual(r.returncode, 0)
        self.assertIn("present-repo", r.stdout)
        self.assertIn("[url]", r.stdout)

    # -- project-show ------------------------------------------------------

    def test_project_show_annotates_url_and_shows_object_path(self):
        os.makedirs(os.path.join(self.root, "present-repo"), exist_ok=True)
        self.make_workspace({"projects": {
            "alpha": {"repos": [
                "absent-string",
                {"path": "present-repo",
                 "url": "git@example.com:present.git"}]}}})
        r = self.cli("project-show", "alpha")
        self.assertEqual(r.returncode, 0)
        out = r.stdout
        # Object entry's path displays exactly like a string entry.
        self.assertIn("present-repo", out)
        self.assertIn("absent-string", out)
        self.assertIn("[url]", out)

    def test_project_show_lists_repos_context_and_scoped_initiatives(self):
        self._standard_workspace()
        r = self.cli("project-show", "alpha")
        self.assertEqual(r.returncode, 0)
        out = r.stdout
        self.assertIn("present-repo", out)
        self.assertIn("absent-repo", out)
        self.assertIn("(absent)", out)
        self.assertIn("context: no", out)
        self.assertIn("mvp-readiness", out)

    def test_project_show_unknown_slug_errors_naming_declared(self):
        self._standard_workspace()
        r = self.cli("project-show", "beta")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("alpha", r.stderr)       # names the declared slugs

    # -- no workspace ------------------------------------------------------

    def test_verbs_require_a_workspace(self):
        for argv in (["workspace-show"], ["project-show", "alpha"]):
            r = self.cli(*argv)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("no workspace", r.stderr.lower())


class WorkspaceInitTest(SpecStatusTestBase):
    """The ``workspace-init <path>`` verb (spec-status workspace-init-verb).

    Unlike the other workspace verbs, ``workspace-init`` runs precisely when no
    workspace is discoverable, so it takes an explicit positional target rather
    than resolving one. No ancestor of the system temp dir declares one."""

    def marker_path(self, target):
        return os.path.join(target, ".shipd-config.json")

    def test_init_creates_and_prints_root(self):
        target = os.path.join(self.root, "ws")
        os.makedirs(target)
        r = self.cli("workspace-init", target)
        self.assertEqual(r.returncode, 0)
        self.assertIn(target, r.stdout)
        marker = self.marker_path(target)
        self.assertTrue(os.path.isfile(marker))
        with open(marker, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(data["workspace"], {})

    def test_init_refuses_under_existing_workspace(self):
        # A workspace declared at self.root is discoverable from the target.
        self.declare_workspace()
        target = os.path.join(self.root, "nested")
        os.makedirs(target)
        r = self.cli("workspace-init", target)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn(self.root, r.stderr)
        self.assertFalse(os.path.exists(self.marker_path(target)))

    # -- git option --------------------------------------------------------

    MEMBERS_BEGIN = "# >>> shipd-workspace members"
    MEMBERS_END = "# <<< shipd-workspace members"

    def _git_init(self, target):
        subprocess.run(["git", "init", target],
                       capture_output=True, text=True, check=True)

    def test_git_flag_seeds_repo_and_ignore_block(self):
        # A non-git target (the system temp dir is not a git work tree).
        target = os.path.join(self.root, "ws")
        os.makedirs(target)
        r = self.cli("workspace-init", target, "--git")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(os.path.isdir(os.path.join(target, ".git")))
        gi = os.path.join(target, ".gitignore")
        self.assertTrue(os.path.isfile(gi))
        with open(gi, encoding="utf-8") as fh:
            body = fh.read()
        self.assertIn(self.MEMBERS_BEGIN, body)
        self.assertIn(self.MEMBERS_END, body)

    def test_git_flag_inside_work_tree_does_not_reinit_or_duplicate(self):
        # self.root is a git work tree; the target is a directory inside it
        # that already carries the marked block.
        self._git_init(self.root)
        target = os.path.join(self.root, "ws")
        os.makedirs(target)
        with open(os.path.join(target, ".gitignore"), "w",
                  encoding="utf-8") as fh:
            fh.write("%s\n%s\n" % (self.MEMBERS_BEGIN, self.MEMBERS_END))
        r = self.cli("workspace-init", target, "--git")
        self.assertEqual(r.returncode, 0, r.stderr)
        # Already inside a work tree — no nested repository is created.
        self.assertFalse(os.path.isdir(os.path.join(target, ".git")))
        with open(os.path.join(target, ".gitignore"), encoding="utf-8") as fh:
            body = fh.read()
        self.assertEqual(body.count(self.MEMBERS_BEGIN), 1)
        self.assertEqual(body.count(self.MEMBERS_END), 1)

    def test_without_git_flag_no_repo_or_ignore(self):
        target = os.path.join(self.root, "ws")
        os.makedirs(target)
        r = self.cli("workspace-init", target)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(os.path.isdir(os.path.join(target, ".git")))
        self.assertFalse(os.path.exists(os.path.join(target, ".gitignore")))


class ConfigShowTest(SpecStatusTestBase):
    """`config-show` prints the resolved layered configuration: per-key
    provenance, the content directory, and the workspace root or a none-note
    (spec-status config-show-verb). ``$HOME`` is isolated so the real home
    config never leaks in."""

    def setUp(self):
        super().setUp()
        self.home = tempfile.mkdtemp(prefix="spec-status-home-")

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)
        super().tearDown()

    def cli(self, *args):
        env = dict(os.environ)
        env["HOME"] = self.home
        return subprocess.run(
            ["python3", SCRIPT, "--root", self.root, *args],
            capture_output=True, text=True, env=env)

    def _write_config(self, d, payload):
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, ".shipd-config.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(payload, fh)

    def test_defaults_only_succeeds(self):
        r = self.cli("config-show")
        self.assertEqual(r.returncode, 0)
        # Content directory prints as the default `.am`; keys show `default`.
        self.assertIn(".shipd", r.stdout)
        self.assertIn("default", r.stdout)

    def test_per_key_provenance_printed(self):
        self._write_config(self.root, {"valid_themes": ["reliability"]})
        r = self.cli("config-show")
        self.assertEqual(r.returncode, 0)
        self.assertIn("valid_themes", r.stdout)
        # The path of the layer that supplied the key is shown.
        self.assertIn(
            os.path.join(self.root, ".shipd-config.json"), r.stdout)

    def test_content_dir_and_workspace_reported(self):
        self._write_config(self.root, {"workspace": {}, "dir": "specs"})
        r = self.cli("config-show")
        self.assertEqual(r.returncode, 0)
        self.assertIn("specs", r.stdout)   # resolved content dir
        self.assertIn(self.root, r.stdout)  # workspace root reported

    def test_no_workspace_notes_none(self):
        self._write_config(self.root, {"valid_themes": ["x"]})
        r = self.cli("config-show")
        self.assertEqual(r.returncode, 0)
        self.assertIn("none", r.stdout.lower())


class PipelineShowTest(SpecStatusTestBase):
    """`pipeline-show` prints the effective autonomous pipeline: one line per
    resolved entry (form + bindings with fallbacks) plus the provenance of the
    key, `[default]` when no layer declares it; invalid pipelines print every
    validation error and exit non-zero (spec-status pipeline-show-verb). The
    verb requires neither a workspace nor a selected change. ``$HOME`` is
    isolated so the real home config never leaks in."""

    def setUp(self):
        super().setUp()
        self.home = tempfile.mkdtemp(prefix="spec-status-home-")

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)
        super().tearDown()

    def cli(self, *args):
        env = dict(os.environ)
        env["HOME"] = self.home
        return subprocess.run(
            ["python3", SCRIPT, "--root", self.root, *args],
            capture_output=True, text=True, env=env)

    def _write_config(self, d, payload):
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, ".shipd-config.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(payload, fh)

    def test_defaults_only_prints_six_stages_and_default(self):
        # No layer declares the key, no workspace, no selected change.
        r = self.cli("pipeline-show")
        self.assertEqual(r.returncode, 0, r.stderr)
        for stage in ("research", "epic", "plan", "gate", "build", "review"):
            self.assertIn(stage, r.stdout)
        self.assertIn("[default]", r.stdout)

    def test_declared_pipeline_prints_skip_bindings_and_path(self):
        # A repo config with a skipped gate and a replaced review carrying a
        # fallback; the supplying config path is named as provenance.
        self._write_config(self.root, {"autonomous-pipeline": [
            {"stage": "plan"},
            {"stage": "gate", "skip": True},
            {"stage": "build"},
            {"stage": "review",
             "replace": {"command": "my-ci review", "fallback": "builtin"}},
        ]})
        r = self.cli("pipeline-show")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = r.stdout.lower()
        self.assertIn("skip", out)             # gate shown as skipped
        self.assertIn("review", r.stdout)      # the replaced stage
        self.assertIn("builtin", r.stdout)     # its fallback
        # provenance names the supplying config file, not `[default]`.
        self.assertIn(
            os.path.join(self.root, ".shipd-config.json"), r.stdout)
        self.assertNotIn("[default]", r.stdout)

    def test_tool_binding_and_fallback_printed(self):
        self._write_config(self.root, {"autonomous-pipeline": [
            {"stage": "plan",
             "tools": [{"name": "mcp:sourcebot", "fallback": "builtin"}]},
        ]})
        r = self.cli("pipeline-show")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("mcp:sourcebot", r.stdout)
        self.assertIn("builtin", r.stdout)

    def test_invalid_pipeline_prints_every_error_and_exits_nonzero(self):
        self._write_config(self.root, {"autonomous-pipeline": [
            {"stage": "deploy"},
            {"custom": "Bad_Name", "command": "x"},
        ]})
        r = self.cli("pipeline-show")
        self.assertNotEqual(r.returncode, 0)
        combined = r.stdout + r.stderr
        self.assertIn("deploy", combined)      # the unknown stage
        self.assertIn("Bad_Name", combined)    # the non-kebab custom name

    def test_runs_without_workspace_or_change(self):
        # A declared, valid pipeline resolves with no workspace declared and no
        # change selected.
        self._write_config(self.root, {"autonomous-pipeline": [
            {"stage": "plan"}, {"stage": "build"}]})
        r = self.cli("pipeline-show")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("plan", r.stdout)
        self.assertIn("build", r.stdout)


class EpicSetInitiativeTest(SpecStatusTestBase):
    """`epic-set-initiative <epic> <initiative>` writes/replaces exactly one
    `Initiative:` header line, preserving other header metadata and body
    (spec-status epic-set-initiative-verb). ``$HOME`` isolated so config
    resolution never reads the real home."""

    def setUp(self):
        super().setUp()
        self.home = tempfile.mkdtemp(prefix="spec-status-home-")

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)
        super().tearDown()

    def cli(self, *args):
        env = dict(os.environ)
        env["HOME"] = self.home
        return subprocess.run(
            ["python3", SCRIPT, "--root", self.root, *args],
            capture_output=True, text=True, env=env)

    def make_epic(self, slug, metadata=None):
        edir = os.path.join(self.root, ".shipd", "epics", slug)
        os.makedirs(edir, exist_ok=True)
        header = ["# %s" % slug, "Status: draft"]
        if metadata:
            header.extend(metadata)
        text = ("\n".join(header) + "\n\n"
                "## Introduction\n\nWhy it matters.\n\n"
                "### Non-goals\n\n- Not that.\n\n"
                "## Decisions\n\nWhy.\n\n"
                "## Design\n\nHow.\n\n"
                "## Changes\n\n"
                "| Change | Description | Code | Integration | Unknowns | Risk |\n"
                "| --- | --- | --- | --- | --- | --- |\n"
                "| csv-export | Export as CSV | low | medium | low | low |\n")
        with open(os.path.join(edir, "epic.md"), "w", encoding="utf-8") as fh:
            fh.write(text)
        return edir

    def read_epic(self, slug):
        with open(os.path.join(self.root, ".shipd", "epics", slug, "epic.md"),
                  encoding="utf-8") as fh:
            return fh.read()

    def _initiative_lines(self, text):
        return [ln for ln in text.splitlines()
                if ln.startswith("Initiative:")]

    def test_writes_initiative_preserving_metadata_and_body(self):
        self.make_epic("reporting-overhaul", metadata=["Theme: reliability"])
        r = self.cli("epic-set-initiative", "reporting-overhaul",
                     "mvp-readiness")
        self.assertEqual(r.returncode, 0)
        text = self.read_epic("reporting-overhaul")
        self.assertIn("Theme: reliability", text)
        self.assertEqual(self._initiative_lines(text),
                         ["Initiative: mvp-readiness"])
        self.assertIn("## Introduction", text)   # body preserved

    def test_replaces_existing_initiative_single_line(self):
        self.make_epic("reporting-overhaul",
                       metadata=["Initiative: old-goal"])
        r = self.cli("epic-set-initiative", "reporting-overhaul",
                     "new-goal")
        self.assertEqual(r.returncode, 0)
        text = self.read_epic("reporting-overhaul")
        self.assertEqual(self._initiative_lines(text),
                         ["Initiative: new-goal"])

    def test_unknown_epic_errors(self):
        r = self.cli("epic-set-initiative", "no-such-epic", "mvp-readiness")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no-such-epic", r.stderr)

    def test_non_kebab_value_errors(self):
        self.make_epic("reporting-overhaul")
        r = self.cli("epic-set-initiative", "reporting-overhaul", "Not_Kebab")
        self.assertNotEqual(r.returncode, 0)
        # The epic file is left untouched.
        self.assertEqual(
            self._initiative_lines(self.read_epic("reporting-overhaul")), [])


class CatTest(SpecStatusTestBase):
    """`cat change|verified|epic|initiative <slug>` prints the named artifact's
    content, each file preceded by a `--- <relpath>` separator (spec-io
    mediated-read-verb). ``$HOME`` isolated so config resolution never reads the
    real home."""

    def setUp(self):
        super().setUp()
        self.home = tempfile.mkdtemp(prefix="spec-status-home-")

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)
        super().tearDown()

    def cli(self, *args):
        env = dict(os.environ)
        env["HOME"] = self.home
        return subprocess.run(
            ["python3", SCRIPT, "--root", self.root, *args],
            capture_output=True, text=True, env=env)

    def declare_workspace(self):
        with open(os.path.join(self.root, ".shipd-config.json"), "w",
                  encoding="utf-8") as fh:
            json.dump({"workspace": {}}, fh)

    def test_cat_change_prints_plan_deltas_tasks(self):
        self.make_change(
            "my-change", status="draft",
            tasks="# Tasks\n\n- [ ] 1.1 [req: *] Do the thing.\n")
        self.make_valid_delta("my-change")
        r = self.cli("cat", "change", "my-change")
        self.assertEqual(r.returncode, 0, r.stderr)
        sep_plan = "--- " + os.path.join(
            ".shipd", "planned", "my-change", "plan.md")
        sep_delta = "--- " + os.path.join(
            ".shipd", "planned", "my-change", "specs", "example", "spec.md")
        sep_tasks = "--- " + os.path.join(
            ".shipd", "planned", "my-change", "tasks.md")
        for sep in (sep_plan, sep_delta, sep_tasks):
            self.assertIn(sep, r.stdout)
        self.assertIn("## Idea", r.stdout)                 # plan content
        self.assertIn("Requirement: Example", r.stdout)    # delta content
        self.assertIn("Do the thing", r.stdout)            # tasks content

    def test_cat_verified(self):
        vdir = os.path.join(self.root, ".shipd", "verified", "auth")
        os.makedirs(vdir)
        with open(os.path.join(vdir, "spec.md"), "w", encoding="utf-8") as fh:
            fh.write("# auth\n\n### Requirement: Login\nid: login\n\n"
                     "The system SHALL log in.\n")
        r = self.cli("cat", "verified", "auth")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(
            "--- " + os.path.join(".shipd", "verified", "auth", "spec.md"),
            r.stdout)
        self.assertIn("Requirement: Login", r.stdout)

    def test_cat_epic(self):
        edir = os.path.join(self.root, ".shipd", "epics", "reporting-overhaul")
        os.makedirs(edir)
        with open(os.path.join(edir, "epic.md"), "w", encoding="utf-8") as fh:
            fh.write("# reporting-overhaul\nStatus: draft\n\n## Introduction\n")
        r = self.cli("cat", "epic", "reporting-overhaul")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Introduction", r.stdout)

    def test_cat_initiative(self):
        self.declare_workspace()
        bdir = os.path.join(self.root, ".shipd", "initiatives", "my-goal")
        os.makedirs(bdir)
        with open(os.path.join(bdir, "brief.md"), "w", encoding="utf-8") as fh:
            fh.write("# my-goal\nStatus: open\n\n## Requirements\n\n- [ ] Do\n")
        r = self.cli("cat", "initiative", "my-goal")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("## Requirements", r.stdout)

    def test_cat_research(self):
        rdir = os.path.join(self.root, ".shipd", "research", "payment-apis")
        os.makedirs(rdir)
        with open(os.path.join(rdir, "report.md"), "w",
                  encoding="utf-8") as fh:
            fh.write("# Payment API landscape\n\nStripe leads [1].\n\n"
                     "## Sources\n\n1. Stripe — https://stripe.com\n")
        r = self.cli("cat", "research", "payment-apis")
        self.assertEqual(r.returncode, 0, r.stderr)
        sep = "--- " + os.path.join(
            ".shipd", "research", "payment-apis", "report.md")
        self.assertIn(sep, r.stdout)
        # Exactly one separator line precedes the single report file.
        self.assertEqual(
            len([ln for ln in r.stdout.splitlines()
                 if ln.startswith("--- ")]), 1)
        self.assertIn("Payment API landscape", r.stdout)

    def test_cat_unknown_research_errors(self):
        r = self.cli("cat", "research", "no-such-report")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no-such-report", r.stderr)

    def test_cat_video(self):
        vdir = os.path.join(self.root, ".shipd", "video", "board-walkthrough")
        os.makedirs(vdir)
        with open(os.path.join(vdir, "brief.md"), "w",
                  encoding="utf-8") as fh:
            fh.write(
                "# Board walkthrough\nVideo: board-walkthrough.mp4\n\n"
                "## Speakers\n\n- Mikk — product lead\n\n"
                "## Intents\n\n### Explain the signal\n\nClear [1].\n\n"
                "## Sources\n\n1. [00:14:22.4] Mikk: clear.\n")
        r = self.cli("cat", "video", "board-walkthrough")
        self.assertEqual(r.returncode, 0, r.stderr)
        sep = "--- " + os.path.join(
            ".shipd", "video", "board-walkthrough", "brief.md")
        self.assertIn(sep, r.stdout)
        # Exactly one separator line precedes the single brief file.
        self.assertEqual(
            len([ln for ln in r.stdout.splitlines()
                 if ln.startswith("--- ")]), 1)
        self.assertIn("Board walkthrough", r.stdout)

    def test_cat_unknown_video_errors(self):
        r = self.cli("cat", "video", "no-such-brief")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no-such-brief", r.stderr)

    def test_cat_unknown_change_errors(self):
        r = self.cli("cat", "change", "ghost")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("ghost", r.stderr)

    def test_cat_unknown_epic_errors(self):
        r = self.cli("cat", "epic", "no-such-epic")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no-such-epic", r.stderr)


class WikiVerbTest(SpecStatusTestBase):
    """The wiki status verbs (spec-status wiki-status-verbs): ``wiki-init``,
    ``wiki-show``, and ``cat wiki``.

    ``self.root`` doubles as the workspace root (its ``.shipd-config.json``
    declares ``workspace`` so ``find_workspace_root`` resolves there); the store
    lives at ``<root>/.shipd/wiki/``. The no-workspace case omits the
    declaration."""

    def wiki(self):
        return os.path.join(self.root, ".shipd", "wiki")

    def write_page(self, slug, text):
        pages = os.path.join(self.wiki(), "wiki")
        os.makedirs(pages, exist_ok=True)
        with open(os.path.join(pages, slug + ".md"), "w",
                  encoding="utf-8") as fh:
            fh.write(text)

    def write_wiki_file(self, name, text):
        with open(os.path.join(self.wiki(), name), "w",
                  encoding="utf-8") as fh:
            fh.write(text)

    # -- wiki-init ---------------------------------------------------------

    def test_wiki_init_scaffolds_the_layout(self):
        self.declare_workspace()
        r = self.cli("wiki-init")
        self.assertEqual(r.returncode, 0, r.stderr)
        w = self.wiki()
        for name in ("schema.md", "index.md", "log.md", "queue.md"):
            self.assertTrue(os.path.isfile(os.path.join(w, name)), name)
        self.assertTrue(os.path.isdir(os.path.join(w, "sources")))
        self.assertTrue(os.path.isdir(os.path.join(w, "wiki")))
        with open(os.path.join(w, "log.md"), encoding="utf-8") as fh:
            log = fh.read()
        self.assertRegex(log, r"##\s+\[\d{4}-\d{2}-\d{2}\]\s+.+\|")

    def test_wiki_init_seeds_a_lint_clean_store(self):
        # The freshly seeded store passes `--wiki` lint (empty catalog, no
        # pages, a valid dated log entry, an empty queue).
        self.declare_workspace()
        self.assertEqual(self.cli("wiki-init").returncode, 0)
        lint = os.path.normpath(
            os.path.join(HERE, "..", "scripts", "spec_lint.py"))
        r = subprocess.run(
            ["python3", lint, "--wiki", "--root", self.root],
            capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_wiki_init_refuses_second_run(self):
        self.declare_workspace()
        self.assertEqual(self.cli("wiki-init").returncode, 0)
        r = self.cli("wiki-init")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("exist", r.stderr.lower())

    def test_wiki_init_requires_workspace(self):
        r = self.cli("wiki-init")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no workspace", r.stderr.lower())

    # -- wiki-show ---------------------------------------------------------

    def test_wiki_show_reports_store_health(self):
        self.declare_workspace()
        self.cli("wiki-init")
        self.write_page("welcome", "# Welcome\n\nHello.\n")
        self.write_wiki_file(
            "index.md", "# Index\n\n- [[welcome]] — The welcome page.\n")
        self.write_wiki_file(
            "queue.md",
            "# Queue\n\n## q-stale-cache\n"
            "- Asked: 2026-07-30 teach-mikk\n"
            "- Question: Is it stale?\n"
            "- Options: yes | no\n"
            "- Recommendation: yes\n"
            "- Answer: pending\n")
        r = self.cli("wiki-show")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = r.stdout
        self.assertIn(self.wiki(), out)          # store root
        self.assertIn("1", out)                  # page count
        self.assertIn("pending", out.lower())    # pending-question count
        self.assertRegex(out, r"##\s+\[\d{4}-\d{2}-\d{2}\]")  # last log entry

    def test_wiki_show_requires_workspace(self):
        r = self.cli("wiki-show")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no workspace", r.stderr.lower())

    # -- wiki-show base: line ---------------------------------------------

    def declare_with_base(self, wiki_base):
        """Declare a workspace whose config also carries ``wiki_base``."""
        with open(os.path.join(self.root, ".shipd-config.json"), "w",
                  encoding="utf-8") as fh:
            json.dump({"workspace": {}, "wiki_base": wiki_base}, fh)

    def test_wiki_show_reports_present_base(self):
        base = os.path.join(self.root, "base-store")
        os.makedirs(base)
        self.declare_with_base(base)
        self.cli("wiki-init")
        r = self.cli("wiki-show")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("base: %s (present)" % base, r.stdout)

    def test_wiki_show_reports_absent_base(self):
        base = os.path.join(self.root, "missing-base")
        self.declare_with_base(base)
        self.cli("wiki-init")
        r = self.cli("wiki-show")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("base: %s (absent)" % base, r.stdout)

    def test_wiki_show_reports_none_when_undeclared(self):
        self.declare_workspace()
        self.cli("wiki-init")
        r = self.cli("wiki-show")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("base: none", r.stdout)

    def test_wiki_show_self_referential_base_is_none(self):
        self.declare_with_base(self.wiki())
        self.cli("wiki-init")
        r = self.cli("wiki-show")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("base: none", r.stdout)

    def test_wiki_show_malformed_base_errors(self):
        self.declare_with_base("relative/base")
        self.cli("wiki-init")
        r = self.cli("wiki-show")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("wiki_base", r.stderr)

    # -- cat wiki ----------------------------------------------------------

    def test_cat_wiki_reads_page(self):
        self.declare_workspace()
        self.cli("wiki-init")
        self.write_page("welcome", "# Welcome\n\nHello there.\n")
        r = self.cli("cat", "wiki", "welcome")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Hello there.", r.stdout)
        self.assertIn("welcome.md", r.stdout)  # `--- <relpath>` separator

    def test_cat_wiki_reserved_slug_reads_top_level_file(self):
        self.declare_workspace()
        self.cli("wiki-init")
        for slug, name in (("index", "index.md"), ("log", "log.md"),
                           ("queue", "queue.md"), ("schema", "schema.md")):
            r = self.cli("cat", "wiki", slug)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn(name, r.stdout)

    def test_cat_wiki_unknown_slug_errors(self):
        self.declare_workspace()
        self.cli("wiki-init")
        r = self.cli("cat", "wiki", "nonexistent")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("nonexistent", r.stderr)


class WikiQueueAddTest(SpecStatusTestBase):
    """The ``wiki-queue-add <q-slug>`` verb (spec-status wiki-status-verbs,
    shipd-wiki wiki-question-queue). ``self.root`` doubles as the workspace root;
    the store lives at ``<root>/.shipd/wiki/``."""

    def queue_text(self):
        with open(os.path.join(self.root, ".shipd", "wiki", "queue.md"),
                  encoding="utf-8") as fh:
            return fh.read()

    def test_wiki_queue_add_appends_block(self):
        self.declare_workspace()
        self.cli("wiki-init")
        r = self.cli("wiki-queue-add", "stale-cache",
                     "--question", "Is the cache stale?",
                     "--options", "yes | no",
                     "--recommendation", "yes",
                     "--origin", "teach-mikk")
        self.assertEqual(r.returncode, 0, r.stderr)
        queue = self.queue_text()
        self.assertIn("## q-stale-cache", queue)
        self.assertIn("Is the cache stale?", queue)
        self.assertIn("yes | no", queue)
        self.assertIn("Recommendation: yes", queue)
        self.assertIn("teach-mikk", queue)
        self.assertIn("Answer: pending", queue)
        self.assertIn("Asked: %s" % datetime.date.today().isoformat(), queue)

    def test_wiki_queue_add_without_origin_still_dates_asked(self):
        self.declare_workspace()
        self.cli("wiki-init")
        r = self.cli("wiki-queue-add", "cache-ttl",
                     "--question", "What TTL?",
                     "--options", "5m | 1h",
                     "--recommendation", "5m")
        self.assertEqual(r.returncode, 0, r.stderr)
        queue = self.queue_text()
        self.assertIn("## q-cache-ttl", queue)
        self.assertIn("Asked: %s" % datetime.date.today().isoformat(), queue)
        self.assertIn("Answer: pending", queue)

    def test_wiki_queue_add_duplicate_slug_refused(self):
        self.declare_workspace()
        self.cli("wiki-init")
        args = ("wiki-queue-add", "stale-cache",
                "--question", "Q?", "--options", "a | b",
                "--recommendation", "a")
        self.assertEqual(self.cli(*args).returncode, 0)
        before = self.queue_text()
        r = self.cli(*args)
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(self.queue_text(), before)  # byte-identical

    def test_wiki_queue_add_requires_workspace(self):
        r = self.cli("wiki-queue-add", "stale-cache",
                     "--question", "Q?", "--options", "a | b",
                     "--recommendation", "a")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no workspace", r.stderr.lower())

    # -- Auto-commit (shipd-wiki wiki-autocommit) --

    def _git(self, *args):
        subprocess.run(["git", "-C", self.root, *args],
                       capture_output=True, text=True, check=True)

    def _init_git(self):
        subprocess.run(["git", "init", "-q", self.root],
                       capture_output=True, text=True, check=True)
        self._git("config", "user.email", "test@example.com")
        self._git("config", "user.name", "Test")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "baseline")

    def _commit_count(self):
        r = subprocess.run(
            ["git", "-C", self.root, "rev-list", "--count", "HEAD"],
            capture_output=True, text=True, check=True)
        return int(r.stdout.strip())

    def _head_subject(self):
        r = subprocess.run(
            ["git", "-C", self.root, "log", "-1", "--format=%s"],
            capture_output=True, text=True, check=True)
        return r.stdout.strip()

    def _head_files(self):
        r = subprocess.run(
            ["git", "-C", self.root, "show", "--name-only", "--format=", "HEAD"],
            capture_output=True, text=True, check=True)
        return sorted(p for p in r.stdout.split("\n") if p.strip())

    def test_wiki_queue_add_commits_only_queue_md(self):
        self.declare_workspace()
        self.cli("wiki-init")
        self._init_git()
        before = self._commit_count()
        r = self.cli("wiki-queue-add", "stale-cache",
                     "--question", "Is the cache stale?",
                     "--options", "yes | no",
                     "--recommendation", "yes")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self._commit_count(), before + 1)
        self.assertEqual(self._head_subject(), "shipd-wiki: queue-add q-stale-cache")
        self.assertEqual(self._head_files(), [".shipd/wiki/queue.md"])

    def test_wiki_queue_add_duplicate_makes_no_commit(self):
        self.declare_workspace()
        self.cli("wiki-init")
        self._init_git()
        args = ("wiki-queue-add", "stale-cache",
                "--question", "Q?", "--options", "a | b",
                "--recommendation", "a")
        self.assertEqual(self.cli(*args).returncode, 0)
        after_first = self._commit_count()
        r = self.cli(*args)
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(self._commit_count(), after_first)

    def test_wiki_queue_add_non_git_appends_without_git(self):
        self.declare_workspace()
        self.cli("wiki-init")
        r = self.cli("wiki-queue-add", "stale-cache",
                     "--question", "Q?", "--options", "a | b",
                     "--recommendation", "a")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("## q-stale-cache", self.queue_text())
        self.assertFalse(os.path.exists(os.path.join(self.root, ".git")))


class LocateTest(SpecStatusTestBase):
    """`locate <change>` probes the invocation root's planned/ then each
    .worktrees/<name> directory, printing one keyed block per match."""

    def make_worktree_change(self, worktree, change, status):
        """Create .worktrees/<worktree>/.shipd/planned/<change>/plan.md with the
        given status — a change installed under a sibling worktree root."""
        cdir = os.path.join(
            self.root, ".worktrees", worktree, ".shipd", "planned", change)
        os.makedirs(cdir)
        with open(os.path.join(cdir, "plan.md"), "w", encoding="utf-8") as fh:
            fh.write("# %s\nStatus: %s\n\n## Idea\nA summary.\n\n"
                     "### Motivation\nBecause.\n\n### Details\nThe changes.\n\n"
                     "### Non-goals\nNot that.\n\n## Implementation\nCarefully.\n"
                     % (change, status))
        return os.path.join(self.root, ".worktrees", worktree)

    def blocks(self, stdout):
        """Split the verb's stdout into a list of {key: value} dicts, one per
        blank-line-separated keyed block."""
        result = []
        for chunk in stdout.strip().split("\n\n"):
            block = {}
            for line in chunk.splitlines():
                if ":" in line:
                    key, _, value = line.partition(":")
                    block[key.strip()] = value.strip()
            if block:
                result.append(block)
        return result

    def test_local_change_is_located(self):
        self.make_change("dark-mode", status="rejected")
        r = self.cli("locate", "dark-mode")
        self.assertEqual(r.returncode, 0, r.stderr)
        blocks = self.blocks(r.stdout)
        self.assertEqual(len(blocks), 1)
        block = blocks[0]
        self.assertEqual(block["change"], "dark-mode")
        self.assertEqual(block["root"], os.path.abspath(self.root))
        self.assertEqual(block["dir"], os.path.join(
            ".shipd", "planned", "dark-mode"))
        self.assertEqual(block["status"], "rejected")

    def test_worktree_change_is_located(self):
        wt = self.make_worktree_change("member-a", "member-a", "rejected")
        r = self.cli("locate", "member-a")
        self.assertEqual(r.returncode, 0, r.stderr)
        blocks = self.blocks(r.stdout)
        self.assertEqual(len(blocks), 1)
        block = blocks[0]
        self.assertEqual(block["change"], "member-a")
        self.assertEqual(block["root"], os.path.abspath(wt))
        self.assertEqual(block["dir"], os.path.join(
            ".shipd", "planned", "member-a"))
        self.assertEqual(block["status"], "rejected")

    def test_local_match_precedes_worktree_matches(self):
        self.make_change("both", status="active")
        wt = self.make_worktree_change("member-a", "both", "rejected")
        r = self.cli("locate", "both")
        self.assertEqual(r.returncode, 0, r.stderr)
        blocks = self.blocks(r.stdout)
        self.assertEqual(len(blocks), 2)
        # The invocation root's own block prints first.
        self.assertEqual(blocks[0]["root"], os.path.abspath(self.root))
        self.assertEqual(blocks[0]["status"], "active")
        self.assertEqual(blocks[1]["root"], os.path.abspath(wt))
        self.assertEqual(blocks[1]["status"], "rejected")

    def test_unknown_change_exits_non_zero(self):
        r = self.cli("locate", "no-such-change")
        self.assertNotEqual(r.returncode, 0)
        # The error names what was probed.
        self.assertIn("no-such-change", r.stderr)
        self.assertIn(os.path.abspath(self.root), r.stderr)

    def test_omitted_argument_falls_back_to_selection(self):
        self.make_change("dark-mode", status="active")
        self.cli("use", "dark-mode")
        r = self.cli("locate")
        self.assertEqual(r.returncode, 0, r.stderr)
        blocks = self.blocks(r.stdout)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["change"], "dark-mode")
        self.assertEqual(blocks[0]["status"], "active")

    def test_no_argument_no_selection_errors(self):
        r = self.cli("locate")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no change given and no spec selected", r.stderr)


class WorkspaceSyncTest(SpecStatusTestBase):
    """The ``workspace-sync`` verb (spec-status workspace-sync-verb): keyed
    member blocks plus a gitignore section, ``--json`` records, opt-in
    ``--write-gitignore``, and registry/clone_sources gating. ``self.root``
    doubles as the workspace root; member git repos and candidate sources live
    under it in tempdirs — never a real remote, never the network."""

    MEMBERS_BEGIN = "# >>> shipd-workspace members"
    MEMBERS_END = "# <<< shipd-workspace members"

    def _write_ws(self, registry, extra=None):
        data = dict(extra or {})
        data["workspace"] = registry
        with open(os.path.join(self.root, ".shipd-config.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(data, fh)

    def _git_repo(self, path, url):
        os.makedirs(path, exist_ok=True)
        subprocess.run(["git", "init", "-q", path],
                       capture_output=True, text=True, check=True)
        subprocess.run(["git", "-C", path, "remote", "add", "origin", url],
                       capture_output=True, text=True, check=True)

    def test_plan_prints_blocks_and_exits_zero_with_drift_and_unmaterializable(self):
        # One present git member whose origin drifts, one path-only absent
        # member that is unmaterializable — both are informational, exit 0.
        self._git_repo(os.path.join(self.root, "backend"),
                       "https://example.invalid/OTHER.git")
        self._write_ws({"projects": {"alpha": {"repos": [
            {"path": "backend", "url": "https://example.invalid/backend.git"},
            "docs"]}}})
        r = self.cli("workspace-sync")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = r.stdout
        self.assertIn("member: alpha", out)
        self.assertIn("path: backend", out)
        self.assertIn("path: docs", out)
        self.assertIn("drift:", out)
        self.assertIn("unmaterializable", out)
        self.assertIn("gitignore:", out)

    def test_json_lines_parse_as_objects_with_kind(self):
        self._git_repo(os.path.join(self.root, "backend"),
                       "https://example.invalid/backend.git")
        self._write_ws({"projects": {"alpha": {"repos": [
            {"path": "backend", "url": "https://example.invalid/backend.git"},
            {"path": "web", "url": "https://example.invalid/web.git"}]}}})
        r = self.cli("workspace-sync", "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = [ln for ln in r.stdout.splitlines() if ln.strip()]
        self.assertTrue(lines)
        kinds = []
        for ln in lines:
            obj = json.loads(ln)
            self.assertIn("kind", obj)
            kinds.append(obj["kind"])
        self.assertIn("member", kinds)
        self.assertIn("gitignore", kinds)

    def test_write_gitignore_is_opt_in_and_scoped(self):
        self._write_ws({"projects": {"alpha": {"repos": [
            {"path": "backend", "url": "https://example.invalid/backend.git"}]}}})
        gi_path = os.path.join(self.root, ".gitignore")
        original = ("# my own ignores\nnode_modules/\n\n%s\n%s\n"
                    % (self.MEMBERS_BEGIN, self.MEMBERS_END))
        with open(gi_path, "w", encoding="utf-8") as fh:
            fh.write(original)

        # Flagless run writes nothing.
        r = self.cli("workspace-sync")
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(gi_path, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), original)

        # --write-gitignore rewrites only the marked block.
        r = self.cli("workspace-sync", "--write-gitignore")
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(gi_path, encoding="utf-8") as fh:
            updated = fh.read()
        self.assertIn("backend", updated)
        # Content outside the markers is byte-identical.
        head = updated.split(self.MEMBERS_BEGIN)[0]
        self.assertEqual(head, original.split(self.MEMBERS_BEGIN)[0])
        tail = updated.split(self.MEMBERS_END)[1]
        self.assertEqual(tail, original.split(self.MEMBERS_END)[1])

    def test_malformed_registry_gates_the_verb(self):
        self._write_ws({"projects": {"alpha": {"repos": "not-a-list"}}})
        r = self.cli("workspace-sync")
        self.assertNotEqual(r.returncode, 0)
        combined = r.stdout + r.stderr
        self.assertIn("alpha", combined)       # the validation finding

    def test_malformed_clone_sources_errors_naming_key(self):
        self._write_ws(
            {"projects": {"alpha": {"repos": [
                {"path": "backend", "url": "https://example.invalid/x.git"}]}}},
            extra={"clone_sources": "/not/a/list"})
        r = self.cli("workspace-sync")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("clone_sources", r.stdout + r.stderr)

    def test_no_workspace_errors(self):
        r = self.cli("workspace-sync")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no workspace", r.stderr.lower())


class CheckBaseTest(SpecStatusTestBase):
    """`check-base [change]` compares a planned change's delta specs against the
    current master library (spec-status check-base-verb): read-only, one
    ``<capability>/<id>: <kind>`` finding line per mismatch, exit 0 clean / 4 on
    findings."""

    def make_master(self, capability, body):
        """Write a master spec ``.shipd/verified/<capability>/spec.md`` from a raw
        body (the requirement blocks after the ``# <capability>`` title)."""
        vdir = os.path.join(self.root, ".shipd", "verified", capability)
        os.makedirs(vdir, exist_ok=True)
        with open(os.path.join(vdir, "spec.md"), "w", encoding="utf-8") as fh:
            fh.write("# %s\n\n%s" % (capability, body))

    def make_delta(self, change, capability, body):
        """Write a change delta ``.shipd/planned/<change>/specs/<capability>/
        spec.md`` from a raw body."""
        sdir = os.path.join(
            self.root, ".shipd", "planned", change, "specs", capability)
        os.makedirs(sdir, exist_ok=True)
        with open(os.path.join(sdir, "spec.md"), "w", encoding="utf-8") as fh:
            fh.write(body)

    def master_hash(self, capability, req_id):
        """Return the current content hash of ``req_id`` in the master spec —
        the value a matching delta ``base:`` must carry."""
        path = os.path.join(
            self.root, ".shipd", "verified", capability, "spec.md")
        with open(path, encoding="utf-8") as fh:
            spec = sc.parse_spec(fh.read())
        for req in spec.requirements:
            if req.id == req_id:
                return sc.content_hash(req)
        raise AssertionError("no requirement %r in master %r" % (req_id, capability))

    def snapshot_am(self):
        """Return a {path: bytes} snapshot of every file under ``.am`` so a test
        can assert the verb wrote nothing."""
        snap = {}
        am = os.path.join(self.root, ".shipd")
        for dirpath, _dirs, files in os.walk(am):
            for name in files:
                p = os.path.join(dirpath, name)
                with open(p, "rb") as fh:
                    snap[p] = fh.read()
        return snap

    def test_clean_change_exits_zero(self):
        self.make_master(
            "auth",
            "### Requirement: Login\nid: login\n\nThe system SHALL log in.\n")
        base = self.master_hash("auth", "login")
        self.make_change("feat", status="active")
        self.make_delta(
            "feat", "auth",
            "## MODIFIED Requirements\n\n"
            "### Requirement: Login\nid: login\nbase: %s\n\n"
            "The system SHALL log in.\n\n"
            "#### Scenario: It works\n"
            "- **WHEN** a user signs in\n"
            "- **THEN** access is granted\n\n"
            "## ADDED Requirements\n\n"
            "### Requirement: Logout\nid: logout\n\n"
            "The system SHALL log out.\n\n"
            "#### Scenario: It works\n"
            "- **WHEN** a user signs out\n"
            "- **THEN** the session ends\n" % base)
        r = self.cli("check-base", "feat")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("clean", r.stdout)
        # No finding lines print.
        self.assertNotIn("stale-base", r.stdout)
        self.assertNotIn("id-collision", r.stdout)
        self.assertNotIn("missing-master", r.stdout)

    def test_stale_base_is_reported(self):
        self.make_master(
            "auth",
            "### Requirement: Login\nid: login\n\nThe system SHALL log in.\n")
        actual = self.master_hash("auth", "login")
        self.make_change("feat", status="active")
        self.make_delta(
            "feat", "auth",
            "## MODIFIED Requirements\n\n"
            "### Requirement: Login\nid: login\nbase: deadbeef\n\n"
            "The system SHALL log in with MFA.\n\n"
            "#### Scenario: It works\n"
            "- **WHEN** a user signs in\n"
            "- **THEN** access is granted\n")
        r = self.cli("check-base", "feat")
        self.assertEqual(r.returncode, 4, r.stdout + r.stderr)
        # A stale-base line names the capability, id, and both hashes.
        self.assertIn("auth/login", r.stdout)
        self.assertIn("stale-base", r.stdout)
        self.assertIn("deadbeef", r.stdout)   # expected (the delta's base:)
        self.assertIn(actual, r.stdout)        # actual (the master's hash)

    def test_added_id_collision_is_reported(self):
        self.make_master(
            "auth",
            "### Requirement: Login\nid: login\n\nThe system SHALL log in.\n")
        self.make_change("feat", status="active")
        self.make_delta(
            "feat", "auth",
            "## ADDED Requirements\n\n"
            "### Requirement: Login\nid: login\n\n"
            "The system SHALL log in differently.\n\n"
            "#### Scenario: It works\n"
            "- **WHEN** a user signs in\n"
            "- **THEN** access is granted\n")
        r = self.cli("check-base", "feat")
        self.assertEqual(r.returncode, 4, r.stdout + r.stderr)
        self.assertIn("auth/login", r.stdout)
        self.assertIn("id-collision", r.stdout)

    def test_missing_master_is_reported(self):
        self.make_master(
            "auth",
            "### Requirement: Login\nid: login\n\nThe system SHALL log in.\n")
        self.make_change("feat", status="active")
        self.make_delta(
            "feat", "auth",
            "## MODIFIED Requirements\n\n"
            "### Requirement: Ghost\nid: ghost\nbase: deadbeef\n\n"
            "The system SHALL do a ghostly thing.\n\n"
            "#### Scenario: It works\n"
            "- **WHEN** something happens\n"
            "- **THEN** it is handled\n")
        r = self.cli("check-base", "feat")
        self.assertEqual(r.returncode, 4, r.stdout + r.stderr)
        self.assertIn("auth/ghost", r.stdout)
        self.assertIn("missing-master", r.stdout)

    def test_verb_never_writes(self):
        self.make_master(
            "auth",
            "### Requirement: Login\nid: login\n\nThe system SHALL log in.\n")
        self.make_change("feat", status="active")
        self.make_delta(
            "feat", "auth",
            "## MODIFIED Requirements\n\n"
            "### Requirement: Login\nid: login\nbase: deadbeef\n\n"
            "The system SHALL log in with MFA.\n\n"
            "#### Scenario: It works\n"
            "- **WHEN** a user signs in\n"
            "- **THEN** access is granted\n\n"
            "## ADDED Requirements\n\n"
            "### Requirement: Login\nid: login\n\n"
            "Colliding add.\n\n"
            "#### Scenario: It works\n"
            "- **WHEN** a user signs in\n"
            "- **THEN** access is granted\n")
        before = self.snapshot_am()
        r = self.cli("check-base", "feat")
        self.assertEqual(r.returncode, 4, r.stdout + r.stderr)
        after = self.snapshot_am()
        self.assertEqual(before, after)


class FlowHookTest(SpecStatusTestBase):
    """A status write appends a best-effort full-band flow snapshot
    (delivery-metrics flow-timeseries)."""

    def _seed_bands(self):
        # An epic holding members in unplanned, draft, and archived bands.
        epic = (
            "# e1\nStatus: active\n\n## Changes\n\n"
            "| Change | Description | Risk |\n| --- | --- | --- |\n"
            "| m_unplanned | not started | low |\n"
            "| m_draft | staged | low |\n"
            "| m_archived | shipped | low |\n")
        os.makedirs(os.path.join(self.root, ".shipd", "epics", "e1"))
        with open(os.path.join(self.root, ".shipd", "epics", "e1", "epic.md"),
                  "w", encoding="utf-8") as fh:
            fh.write(epic)
        self.make_change("m_draft", status="draft")
        os.makedirs(os.path.join(
            self.root, ".shipd", "completed", "2026-07-01-m_archived"))

    def test_set_status_appends_full_band_snapshot(self):
        self._seed_bands()
        r = self.cli("set-status", "draft", "m_draft")
        self.assertEqual(r.returncode, 0, r.stderr)
        records = self.flow_records()
        self.assertTrue(records)
        rec = records[-1]
        self.assertEqual(rec["root"], os.path.abspath(self.root))
        states = rec["states"]
        self.assertEqual(states.get("unplanned"), ["m_unplanned"])
        self.assertEqual(states.get("draft"), ["m_draft"])
        self.assertEqual(states.get("archived"), ["m_archived"])

    def test_unwritable_flow_dest_does_not_fail_the_write(self):
        self.make_change("feat", status="ready")
        # Point the flow dir under a regular file so os.makedirs raises.
        blocker = os.path.join(self.root, "blocker")
        with open(blocker, "w", encoding="utf-8") as fh:
            fh.write("x")
        os.environ["AM_FLOW_LOG_DIR"] = os.path.join(blocker, "nope")
        r = self.cli("set-status", "draft", "feat")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Status: draft", self.read_plan("feat"))


if __name__ == "__main__":
    unittest.main()
