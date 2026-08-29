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
import spec_status as ss  # noqa: E402


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


class BoardLaneTest(unittest.TestCase):
    """The shared state→lane projection ``spec_status.board_lane`` (spec-status
    epic-status-verbs): a member's lane derives from its state alone, and the
    dashboard's ``flow_lane`` consumes the very same function so the board and
    the epic report cannot drift. Pure — driven by direct import, no CLI.

    Written test-first; expected to FAIL until ``board_lane`` lands in
    ``spec_status.py`` (task 1.2)."""

    def test_archived_is_shipped(self):
        self.assertEqual(ss.board_lane("archived"), "shipped")

    def test_ready_is_ready(self):
        self.assertEqual(ss.board_lane("ready"), "ready")

    def test_unplanned_is_unplanned(self):
        self.assertEqual(ss.board_lane("unplanned"), "unplanned")

    def test_every_other_state_is_building(self):
        for state in ("draft", "active", "complete", "verified", "rejected",
                      "?"):
            self.assertEqual(ss.board_lane(state), "building", state)

    # ``dashboard.flow_lane``'s delegation to this projection is asserted in
    # ``tests_textual/test_dashboard.py`` — importing ``dashboard`` needs
    # ``textual``, which this stdlib-only suite never installs.


class EpicVerbTest(SpecStatusTestBase):
    """The three epic status verbs (spec-status epic-status-verbs):
    ``epic-show``, ``epic-sync``, ``epic-set-status``.

    Written test-first; expected to FAIL until the verbs land in
    ``spec_status.py`` (task 2.2)."""

    def make_epic(self, slug, status="draft", metadata=None, rows=None,
                  root=None):
        """Write .shipd/epics/<slug>/epic.md with a conforming header and stub
        table. ``metadata`` is a list of ``Key: value`` header lines; ``rows``
        is a list of (slug, description, (r1, r2, r3, r4)) tuples. ``root``
        defaults to the invocation root — pass a worktree root to author the
        epic there instead."""
        edir = os.path.join(root if root is not None else self.root,
                            ".shipd", "epics", slug)
        os.makedirs(edir, exist_ok=True)
        if rows is None:
            rows = [("csv-export", "Export as CSV",
                     ("low", "medium", "low", "low"))]
        table = [
            "| Change | Description | Code | Integration | Unknowns | Risk |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for rslug, desc, ratings in rows:
            # An empty ``ratings`` emits a row with no rating cells at all —
            # the "row carries no rating" fixture the report renders as `?`.
            table.append("| %s |" % " | ".join([rslug, desc] + list(ratings)))
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

    def make_worktree_epic(self, worktree, slug, status="ready", metadata=None,
                           rows=None):
        """Author an epic inside ``.worktrees/<worktree>``'s content directory —
        an epic born in its own worktree, invisible to a root-only probe — and
        return that worktree root."""
        wt = os.path.join(self.root, ".worktrees", worktree)
        os.makedirs(wt, exist_ok=True)
        if rows is None:
            rows = [("member-a", "A", ("low",) * 4)]
        self.make_epic(slug, status=status, metadata=metadata, rows=rows,
                       root=wt)
        return wt

    def make_broken_worktree(self, worktree):
        """A worktree whose content-directory configuration cannot be read."""
        wt = os.path.join(self.root, ".worktrees", worktree)
        os.makedirs(wt, exist_ok=True)
        with open(os.path.join(wt, ".shipd-config.json"), "w",
                  encoding="utf-8") as fh:
            fh.write("{not valid json")
        return wt

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

    # -- the board-shaped epic report --------------------------------------

    LANES = ("UNPLANNED", "READY", "BUILDING", "SHIPPED")

    def lane_headers(self, out):
        """The report's ``<LANE> (<count>)`` header lines, in order."""
        return [ln for ln in out.splitlines()
                if ln.split(" ")[0] in self.LANES and not ln.startswith(" ")]

    def member_line(self, out, slug):
        """The indented member row for ``slug``, or None when absent."""
        for line in out.splitlines():
            if line.startswith("  ") and line.split()[:1] == [slug]:
                return line
        return None

    def member_state(self, out, slug):
        """The state field of ``slug``'s member row (None when it has none)."""
        line = self.member_line(out, slug)
        return None if line is None else line.split()[1]

    def lane_of(self, out, slug):
        """The lane header ``slug``'s member row falls under."""
        lane = None
        for line in out.splitlines():
            if not line.startswith(" ") and line.split(" ")[0] in self.LANES:
                lane = line.split(" ")[0]
            elif line.startswith("  ") and line.split()[:1] == [slug]:
                return lane
        return None

    def test_epic_show_keeps_status_and_metadata_header(self):
        # Byte-compatible with the pre-report epic-show: the status line first,
        # then the epic's metadata lines.
        self.make_epic(
            "reporting-overhaul", status="active",
            metadata=["Theme: reliability", "Initiative: mvp-readiness"],
            rows=[("csv-export", "CSV", ("low",) * 4)])
        r = self.cli("epic-show", "reporting-overhaul")
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = r.stdout.splitlines()
        self.assertEqual(lines[0], "reporting-overhaul: active")
        self.assertEqual(lines[1], "Theme: reliability")
        self.assertEqual(lines[2], "Initiative: mvp-readiness")

    def test_epic_show_groups_members_into_board_lanes(self):
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
        self.assertEqual(r.returncode, 0, r.stderr)
        out = r.stdout
        self.assertEqual(self.lane_of(out, "csv-export"), "SHIPPED")
        self.assertEqual(self.lane_of(out, "pdf-export"), "BUILDING")
        self.assertEqual(self.lane_of(out, "new-thing"), "UNPLANNED")
        self.assertEqual(self.member_state(out, "csv-export"), "archived")
        self.assertEqual(self.member_state(out, "pdf-export"), "active")
        self.assertEqual(self.member_state(out, "new-thing"), "unplanned")

    def test_epic_show_lanes_print_in_board_order_with_counts(self):
        self.make_epic(
            "e", status="active",
            rows=[("csv-export", "CSV", ("low",) * 4),
                  ("new-thing", "TBD", ("low",) * 4)])
        self.make_completed("csv-export")
        r = self.cli("epic-show", "e")
        self.assertEqual(r.returncode, 0, r.stderr)
        # Board order, every lane present — empty ones included.
        self.assertEqual(
            self.lane_headers(r.stdout),
            ["UNPLANNED (1)", "READY (0)", "BUILDING (0)", "SHIPPED (1)"])

    def test_epic_show_empty_lane_has_no_member_lines(self):
        self.make_epic(
            "e", status="ready",
            rows=[("new-thing", "TBD", ("low",) * 4)])
        r = self.cli("epic-show", "e")
        lines = r.stdout.splitlines()
        idx = lines.index("READY (0)")
        # The next line is the following lane header, not a member row.
        self.assertEqual(lines[idx + 1], "BUILDING (0)")

    def test_epic_show_reports_shipped_progress(self):
        rows = [("m-%d" % i, "M%d" % i, ("low",) * 4) for i in range(7)]
        self.make_epic("e", status="active", rows=rows)
        self.make_completed("m-0")
        self.make_completed("m-1")
        r = self.cli("epic-show", "e")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("shipped 2/7", r.stdout.splitlines())

    def test_epic_show_member_line_carries_risk_rating(self):
        # The risk is the stub table's last rating cell.
        self.make_epic(
            "e", status="ready",
            rows=[("member-a", "A", ("low", "medium", "low", "high"))])
        r = self.cli("epic-show", "e")
        line = self.member_line(r.stdout, "member-a")
        self.assertIsNotNone(line)
        self.assertEqual(line.split(), ["member-a", "unplanned", "risk", "high"])

    def test_epic_show_member_without_ratings_reports_question_mark_risk(self):
        self.make_epic("e", status="ready", rows=[("member-a", "A", ())])
        r = self.cli("epic-show", "e")
        line = self.member_line(r.stdout, "member-a")
        self.assertIsNotNone(line)
        self.assertEqual(line.split(), ["member-a", "unplanned", "risk", "?"])

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

    # -- epic-sync's token breakdown aggregation ---------------------------

    def make_completed_tasks(self, slug, table=None, date="2026-01-01"):
        """An archived change whose ``tasks.md`` optionally ends with a
        ``## Token usage breakdown`` section. ``table`` is a list of
        ``(tool, calls, output)`` rows; ``None`` writes no section at all."""
        cdir = os.path.join(self.root, ".shipd", "completed",
                            "%s-%s" % (date, slug))
        os.makedirs(cdir, exist_ok=True)
        body = "## 1. Work\n\n- [x] 1.1 [req: r] Do it\n"
        if table is not None:
            lines = ["## Token usage breakdown", "",
                     "| Tool | Calls | Output tokens |", "| --- | --- | --- |"]
            total_calls = 0
            total_output = 0
            for tool, calls, output in table:
                total_calls += calls
                total_output += output
                lines.append("| %s | %d | %d |" % (tool, calls, output))
            lines.append("| **Total** | %d | %d |" % (total_calls, total_output))
            body += "\n" + "\n".join(lines) + "\n"
        with open(os.path.join(cdir, "tasks.md"), "w", encoding="utf-8") as fh:
            fh.write(body)
        return cdir

    def test_epic_sync_sums_member_tables_into_the_epic(self):
        self.make_epic(
            "e", status="active",
            rows=[("member-a", "A", ("low",) * 4),
                  ("member-b", "B", ("low",) * 4)])
        self.make_completed_tasks("member-a", table=[("Bash", 1, 100)])
        self.make_completed_tasks("member-b", table=[("Bash", 1, 100)])
        r = self.cli("epic-sync", "e")
        self.assertEqual(r.returncode, 0)
        text = self.read_epic("e")
        self.assertIn("## Token usage breakdown", text)
        self.assertIn("| Bash | 2 | 200 |", text)
        self.assertIn("| **Total** | 2 | 200 |", text)
        # The section is trailing: nothing follows it.
        self.assertLess(text.index("## Changes"),
                        text.index("## Token usage breakdown"))

    def test_epic_sync_breakdown_is_idempotent(self):
        self.make_epic(
            "e", status="active",
            rows=[("member-a", "A", ("low",) * 4),
                  ("member-b", "B", ("low",) * 4)])
        self.make_completed_tasks("member-a", table=[("Bash", 1, 100),
                                                     ("Read", 2, 40)])
        self.make_completed_tasks("member-b", table=[("Bash", 1, 100)])
        self.cli("epic-sync", "e")
        first = self.read_epic("e")
        self.cli("epic-sync", "e")
        self.assertEqual(self.read_epic("e"), first)

    def test_epic_sync_member_without_a_table_contributes_nothing(self):
        self.make_epic(
            "e", status="active",
            rows=[("member-a", "A", ("low",) * 4),
                  ("member-b", "B", ("low",) * 4)])
        self.make_completed_tasks("member-a", table=[("Bash", 1, 100)])
        self.make_completed_tasks("member-b", table=None)
        r = self.cli("epic-sync", "e")
        self.assertEqual(r.returncode, 0)
        text = self.read_epic("e")
        self.assertIn("| Bash | 1 | 100 |", text)
        self.assertIn("| **Total** | 1 | 100 |", text)

    def test_epic_sync_removes_the_section_when_no_member_has_a_table(self):
        self.make_epic(
            "e", status="active",
            rows=[("member-a", "A", ("low",) * 4)])
        self.make_completed_tasks("member-a", table=[("Bash", 1, 100)])
        self.cli("epic-sync", "e")
        self.assertIn("## Token usage breakdown", self.read_epic("e"))
        # The member's table goes away; the epic's section goes with it.
        self.make_completed_tasks("member-a", table=None)
        r = self.cli("epic-sync", "e")
        self.assertEqual(r.returncode, 0)
        text = self.read_epic("e")
        self.assertNotIn("## Token usage breakdown", text)
        self.assertIn("## Changes", text)

    def test_epic_sync_preserves_sections_after_a_prose_heading(self):
        # The literal heading appears mid-prose in ## Introduction, with real
        # sections after it. The rewrite must not treat that as the trailing
        # section and swallow ## Decisions / ## Design / ## Changes.
        self.write_epic_raw("e", (
            "# e\n"
            "Status: active\n\n"
            "## Introduction\n\n"
            "Why it matters. The build writes a section titled\n"
            "## Token usage breakdown\n"
            "into every change's tasks.md.\n\n"
            "### Non-goals\n\n- Not that.\n\n"
            "## Decisions\n\nWhy.\n\n"
            "## Design\n\nHow.\n\n"
            "## Changes\n\n"
            "| Change | Description | Code | Integration | Unknowns | Risk |\n"
            "| --- | --- | --- | --- | --- | --- |\n"
            "| member-a | A | low | low | low | low |\n"))
        self.make_completed_tasks("member-a", table=[("Bash", 1, 100)])
        r = self.cli("epic-sync", "e")
        self.assertEqual(r.returncode, 0)
        text = self.read_epic("e")
        for section in ("## Introduction", "### Non-goals", "## Decisions",
                        "## Design", "## Changes"):
            self.assertIn(section, text)
        self.assertIn("| member-a | A | low | low | low | low |", text)
        # The generated table is appended as the trailing section, after the
        # prose mention — which is left exactly where it was.
        self.assertIn("| Bash | 1 | 100 |", text)
        self.assertLess(text.index("## Changes"), text.rindex("| Bash | 1 | 100 |"))
        self.assertTrue(text.rstrip().endswith("| **Total** | 1 | 100 |"))
        # And a re-run is still idempotent against that document.
        first = self.read_epic("e")
        self.cli("epic-sync", "e")
        self.assertEqual(self.read_epic("e"), first)

    def test_epic_sync_ignores_a_members_prose_heading(self):
        # The same conservative rule on the read side: a member's tasks.md that
        # mentions the heading mid-document contributes nothing, rather than
        # parsing whatever follows.
        self.make_epic(
            "e", status="active", rows=[("member-a", "A", ("low",) * 4)])
        cdir = os.path.join(self.root, ".shipd", "completed",
                            "2026-01-01-member-a")
        os.makedirs(cdir, exist_ok=True)
        with open(os.path.join(cdir, "tasks.md"), "w", encoding="utf-8") as fh:
            fh.write("## Token usage breakdown\n\nnot a table at all\n\n"
                     "## 1. Work\n\n- [x] 1.1 [req: r] Do it\n")
        r = self.cli("epic-sync", "e")
        self.assertEqual(r.returncode, 0)
        self.assertNotIn("## Token usage breakdown", self.read_epic("e"))

    def test_epic_sync_draft_epic_file_untouched_by_the_breakdown(self):
        self.make_epic(
            "e", status="draft",
            rows=[("member-a", "A", ("low",) * 4)])
        self.make_completed_tasks("member-a", table=[("Bash", 1, 100)])
        before = self.read_epic("e")
        r = self.cli("epic-sync", "e")
        self.assertEqual(r.stdout.strip(), "draft")
        self.assertEqual(self.read_epic("e"), before)

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

    Exercised through ``epic-show``, whose board-shaped report carries one
    member row per stub member, naming its derived state.

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
        self.assertEqual(self.member_state(r.stdout, "member-a"), "ready")

    def test_worktree_derived_member_is_marked(self):
        self.make_epic(
            "e", status="ready", rows=[("member-a", "A", ("low",) * 4)])
        self.make_worktree_change("member-a", "member-a", "ready")
        r = self.cli("epic-show", "e")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(
            self.member_line(r.stdout, "member-a").endswith(" [worktree]"),
            r.stdout)

    def test_invocation_root_member_is_not_marked(self):
        self.make_epic(
            "e", status="ready", rows=[("member-a", "A", ("low",) * 4)])
        self.make_change("member-a", status="active")
        r = self.cli("epic-show", "e")
        self.assertNotIn("[worktree]", r.stdout)

    def test_invocation_root_wins_over_worktree(self):
        self.make_epic(
            "e", status="ready", rows=[("member-a", "A", ("low",) * 4)])
        self.make_change("member-a", status="active")
        self.make_worktree_change("member-a", "member-a", "rejected")
        r = self.cli("epic-show", "e")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.member_state(r.stdout, "member-a"), "active")

    def test_member_absent_everywhere_is_unplanned(self):
        self.make_epic(
            "e", status="ready", rows=[("member-a", "A", ("low",) * 4)])
        # A worktree exists but carries no change for this slug, so the probe
        # must fall through every candidate before landing on `unplanned`.
        self.make_worktree_change("member-a", "some-other-change", "active")
        r = self.cli("epic-show", "e")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.member_state(r.stdout, "member-a"), "unplanned")

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
        self.assertEqual(self.member_state(r.stdout, "member-a"), "unplanned")


class EpicDiscoveryTest(EpicVerbTest):
    """The shared root-first epic discovery seam (spec-status
    epic-status-verbs, delivery-dashboard board-aggregation):
    ``_epic_hosting_root`` and ``all_epic_slugs_with_roots`` probe the
    invocation root first, then each ``.worktrees/<name>`` directory in sorted
    name order, resolving each candidate's content directory independently and
    skipping unreadable ones. Driven by direct import — the seam is a library
    function both the status CLI and the dashboard consume.

    Written test-first; expected to FAIL until the seam lands in
    ``spec_status.py`` (task 1.2)."""

    # -- _epic_hosting_root -------------------------------------------------

    def test_hosting_root_is_the_invocation_root_when_it_hosts(self):
        self.make_epic("e1", status="ready")
        self.assertEqual(ss._epic_hosting_root(self.root, "e1"), self.root)

    def test_invocation_root_wins_over_a_worktree_copy(self):
        self.make_epic("e1", status="ready")
        self.make_worktree_epic("wt-a", "e1")
        self.assertEqual(ss._epic_hosting_root(self.root, "e1"), self.root)

    def test_hosting_root_falls_through_to_the_worktree(self):
        wt = self.make_worktree_epic("wt-a", "e1")
        self.assertEqual(ss._epic_hosting_root(self.root, "e1"), wt)

    def test_first_hosting_worktree_in_sorted_order_wins(self):
        self.make_worktree_epic("wt-b", "e1")
        first = self.make_worktree_epic("wt-a", "e1")
        self.assertEqual(ss._epic_hosting_root(self.root, "e1"), first)

    def test_hosting_root_is_none_when_no_candidate_hosts(self):
        self.make_worktree_epic("wt-a", "other")
        self.assertIsNone(ss._epic_hosting_root(self.root, "e1"))

    def test_unreadable_worktree_config_is_skipped(self):
        self.make_broken_worktree("wt-a")
        wt = self.make_worktree_epic("wt-b", "e1")
        self.assertEqual(ss._epic_hosting_root(self.root, "e1"), wt)

    def test_unreadable_worktree_config_alone_yields_none(self):
        self.make_broken_worktree("wt-a")
        self.assertIsNone(ss._epic_hosting_root(self.root, "e1"))

    # -- all_epic_slugs_with_roots ------------------------------------------

    def test_root_epics_sort_first_then_worktree_only_epics(self):
        self.make_epic("r-b", status="ready")
        self.make_epic("r-a", status="ready")
        wt_z = self.make_worktree_epic("wt-z", "w-z")
        wt_a = self.make_worktree_epic("wt-a", "w-a")
        self.assertEqual(
            ss.all_epic_slugs_with_roots(self.root),
            [("r-a", self.root), ("r-b", self.root),
             ("w-a", wt_a), ("w-z", wt_z)])

    def test_a_duplicated_slug_is_listed_once_from_the_root(self):
        self.make_epic("e1", status="ready")
        self.make_worktree_epic("wt-a", "e1")
        self.assertEqual(ss.all_epic_slugs_with_roots(self.root),
                         [("e1", self.root)])

    def test_a_slug_in_two_worktrees_takes_the_sorted_first(self):
        self.make_worktree_epic("wt-b", "e1")
        first = self.make_worktree_epic("wt-a", "e1")
        self.assertEqual(ss.all_epic_slugs_with_roots(self.root),
                         [("e1", first)])

    def test_an_unreadable_worktree_config_does_not_break_the_listing(self):
        self.make_epic("e1", status="ready")
        self.make_broken_worktree("wt-a")
        wt = self.make_worktree_epic("wt-b", "w-1")
        self.assertEqual(ss.all_epic_slugs_with_roots(self.root),
                         [("e1", self.root), ("w-1", wt)])

    def test_an_empty_workspace_lists_nothing(self):
        self.assertEqual(ss.all_epic_slugs_with_roots(self.root), [])


class EpicShowWorktreeHostTest(EpicVerbTest):
    """``epic-show`` resolves an epic hosted only under a ``.worktrees/<name>``
    worktree and marks it with a ``worktree: <name>`` line directly after the
    metadata lines, while the mutating verbs stay invocation-root-only
    (spec-status epic-status-verbs).

    Written test-first; expected to FAIL until the resolution lands in
    ``spec_status.py`` (task 2.4)."""

    def test_epic_show_resolves_a_worktree_hosted_epic(self):
        self.make_worktree_epic(
            "epic-shipd-port", "shipd-port", status="active",
            rows=[("csv-export", "CSV", ("low",) * 4),
                  ("new-thing", "TBD", ("high",) * 4)])
        self.make_completed("csv-export")
        r = self.cli("epic-show", "shipd-port")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = r.stdout
        self.assertEqual(out.splitlines()[0], "shipd-port: active")
        self.assertIn("shipped 1/2", out.splitlines())
        self.assertEqual(self.lane_of(out, "csv-export"), "SHIPPED")
        self.assertEqual(self.lane_of(out, "new-thing"), "UNPLANNED")

    def test_worktree_line_follows_the_metadata_lines(self):
        self.make_worktree_epic(
            "epic-shipd-port", "shipd-port", status="active",
            metadata=["Theme: reliability", "Initiative: mvp-readiness"])
        r = self.cli("epic-show", "shipd-port")
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = r.stdout.splitlines()
        self.assertEqual(lines[0], "shipd-port: active")
        self.assertEqual(lines[1], "Theme: reliability")
        self.assertEqual(lines[2], "Initiative: mvp-readiness")
        self.assertEqual(lines[3], "worktree: epic-shipd-port")

    def test_worktree_line_names_the_hosting_worktree_without_metadata(self):
        self.make_worktree_epic("epic-shipd-port", "shipd-port", status="ready")
        r = self.cli("epic-show", "shipd-port")
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = r.stdout.splitlines()
        self.assertEqual(lines[0], "shipd-port: ready")
        self.assertEqual(lines[1], "worktree: epic-shipd-port")

    def test_a_root_hosted_epic_carries_no_worktree_line(self):
        self.make_epic("e", status="ready", metadata=["Theme: reliability"])
        r = self.cli("epic-show", "e")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("worktree:", r.stdout)

    def test_the_invocation_root_copy_wins_and_carries_no_marker(self):
        self.make_epic("shipd-port", status="ready",
                       rows=[("member-a", "A", ("low",) * 4)])
        self.make_worktree_epic("epic-shipd-port", "shipd-port",
                                status="complete")
        r = self.cli("epic-show", "shipd-port")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.splitlines()[0], "shipd-port: ready")
        self.assertNotIn("worktree:", r.stdout)

    def test_show_fallback_matches_epic_show_for_a_worktree_epic(self):
        self.make_worktree_epic(
            "epic-shipd-port", "shipd-port", status="active",
            metadata=["Theme: reliability"],
            rows=[("csv-export", "CSV", ("low",) * 4)])
        show = self.cli("show", "shipd-port")
        epic_show = self.cli("epic-show", "shipd-port")
        self.assertEqual(show.returncode, 0, show.stderr)
        self.assertEqual(epic_show.returncode, 0, epic_show.stderr)
        # Byte-identical: one renderer serves both verbs, worktrees included.
        self.assertEqual(show.stdout, epic_show.stdout)

    def test_an_epic_in_no_candidate_still_errors(self):
        self.make_worktree_epic("epic-other", "other", status="ready")
        r = self.cli("epic-show", "shipd-port")
        self.assertEqual(r.returncode, 1)
        self.assertIn("epic 'shipd-port' not found", r.stderr)

    # -- the mutating verbs stay invocation-root-only ----------------------

    def test_epic_set_status_refuses_a_worktree_hosted_epic(self):
        wt = self.make_worktree_epic("epic-shipd-port", "shipd-port",
                                     status="draft")
        path = os.path.join(wt, ".shipd", "epics", "shipd-port", "epic.md")
        with open(path, encoding="utf-8") as fh:
            before = fh.read()
        r = self.cli("epic-set-status", "ready", "shipd-port")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("epic 'shipd-port' not found", r.stderr)
        with open(path, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), before)

    def test_epic_sync_refuses_a_worktree_hosted_epic(self):
        self.make_worktree_epic("epic-shipd-port", "shipd-port",
                                status="ready")
        r = self.cli("epic-sync", "shipd-port")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("epic 'shipd-port' not found", r.stderr)


class EpicFallbackTest(EpicVerbTest):
    """``status``/``show`` fall back to the epic when their argument names no
    change but an epic of that slug exists (spec-status status-cli): ``status``
    prints the epic's status value, ``show`` prints the board-shaped report
    ``epic-show`` prints. A name matching neither keeps printing ``?``.

    Written test-first; expected to FAIL until the fallback lands in
    ``spec_status.py`` (task 3.2)."""

    def test_status_falls_back_to_the_epic(self):
        self.make_epic("shipd-port", status="active",
                       rows=[("member-a", "A", ("low",) * 4)])
        r = self.cli("status", "shipd-port")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "active")

    def test_show_falls_back_to_the_epic_report(self):
        self.make_epic(
            "shipd-port", status="active",
            metadata=["Theme: reliability"],
            rows=[("csv-export", "CSV", ("low",) * 4),
                  ("new-thing", "TBD", ("high",) * 4)])
        self.make_completed("csv-export")
        show = self.cli("show", "shipd-port")
        epic_show = self.cli("epic-show", "shipd-port")
        self.assertEqual(show.returncode, 0, show.stderr)
        self.assertEqual(epic_show.returncode, 0, epic_show.stderr)
        # Byte-identical: one renderer serves both verbs.
        self.assertEqual(show.stdout, epic_show.stdout)
        self.assertIn("shipd-port: active", show.stdout)

    def test_a_change_of_the_same_name_still_wins(self):
        self.make_epic("overlap", status="active",
                       rows=[("member-a", "A", ("low",) * 4)])
        self.make_change("overlap", status="ready")
        r = self.cli("status", "overlap")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "ready")

    def test_status_falls_back_to_a_worktree_hosted_epic(self):
        # The epic was authored in its own worktree and has not merged yet, so
        # the invocation root's content dir does not carry it at all.
        self.make_worktree_epic("epic-shipd-port", "shipd-port",
                                status="active")
        r = self.cli("status", "shipd-port")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "active")

    def test_show_falls_back_to_a_worktree_hosted_epic_report(self):
        self.make_worktree_epic(
            "epic-shipd-port", "shipd-port", status="active",
            rows=[("csv-export", "CSV", ("low",) * 4),
                  ("new-thing", "TBD", ("high",) * 4)])
        self.make_completed("csv-export")
        r = self.cli("show", "shipd-port")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = r.stdout
        self.assertEqual(out.splitlines()[0], "shipd-port: active")
        self.assertIn("shipped 1/2", out.splitlines())
        self.assertEqual(self.lane_of(out, "csv-export"), "SHIPPED")
        self.assertEqual(self.lane_of(out, "new-thing"), "UNPLANNED")

    def test_the_invocation_root_epic_wins_over_a_worktree_copy(self):
        self.make_epic("shipd-port", status="ready",
                       rows=[("member-a", "A", ("low",) * 4)])
        self.make_worktree_epic("epic-shipd-port", "shipd-port",
                                status="complete")
        r = self.cli("status", "shipd-port")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "ready")

    def test_neither_change_nor_epic_stays_a_question_mark(self):
        r = self.cli("status", "no-such-thing")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "?")

    def test_a_name_in_no_candidate_stays_a_question_mark(self):
        # A worktree exists and hosts an epic of its own, so the probe walks
        # every candidate before falling through to `?`.
        self.make_worktree_epic("epic-other", "other", status="ready")
        self.make_broken_worktree("epic-broken")
        r = self.cli("status", "no-such-thing")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "?")

    def test_show_of_neither_change_nor_epic_is_unchanged(self):
        r = self.cli("show", "no-such-thing")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "no-such-thing: ?")


class WorkspaceReportTest(EpicVerbTest):
    """The workspace board report (spec-status workspace-board-report):
    ``show`` with no name given and no spec selected reports the whole
    delivery board — a totals line, ``shipped <n>/<m>``, and the four board
    lanes with an epic column on the non-shipped rows and per-epic rollups
    under ``SHIPPED``. ``status`` keeps its no-selection error.

    Written test-first; expected to FAIL until the report lands in
    ``spec_status.py`` (tasks 2.2/2.3)."""

    def make_worktree_change(self, worktree, change, status):
        """Create .worktrees/<worktree>/.shipd/planned/<change>/plan.md with the
        given status — a change installed under a sibling worktree root."""
        cdir = os.path.join(
            self.root, ".worktrees", worktree, ".shipd", "planned", change)
        os.makedirs(cdir)
        with open(os.path.join(cdir, "plan.md"), "w", encoding="utf-8") as fh:
            fh.write("# %s\nStatus: %s\n\n## Idea\nA summary.\n" % (
                change, status))
        return os.path.join(self.root, ".worktrees", worktree)

    def make_worktree_completed(self, worktree, change, date="2026-01-01"):
        """Archive ``change`` under a sibling worktree root — the only shape in
        which a standalone change reads ``archived`` (discovery walks the root's
        ``planned/`` dirs and the worktree names)."""
        cdir = os.path.join(
            self.root, ".worktrees", worktree, ".shipd", "completed",
            "%s-%s" % (date, change))
        os.makedirs(cdir)
        with open(os.path.join(cdir, "plan.md"), "w", encoding="utf-8") as fh:
            fh.write("# %s\nStatus: verified\n\n## Idea\nA summary.\n" % change)

    # -- report accessors --------------------------------------------------

    def report(self):
        r = self.cli("show")
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def rows_in(self, out, lane):
        """The indented rows printed under the ``lane`` header."""
        rows, current = [], None
        for line in out.splitlines():
            if line and not line.startswith(" ") \
                    and line.split(" ")[0] in self.LANES:
                current = line.split(" ")[0]
            elif line.startswith("  ") and current == lane:
                rows.append(line)
        return rows

    def row_for(self, out, member):
        """``(lane, row)`` for the row whose member column is ``member``."""
        for lane in self.LANES:
            for row in self.rows_in(out, lane):
                fields = row.split()
                if len(fields) > 1 and fields[1] == member:
                    return lane, row
        return None, None

    # -- the header lines --------------------------------------------------

    def test_bare_show_prints_totals_and_all_four_lanes(self):
        self.make_epic("e1", status="ready",
                       metadata=["Initiative: mvp-readiness"],
                       rows=[("m1", "A", ("low",) * 4),
                             ("m2", "B", ("low",) * 4)])
        self.make_epic("e2", status="ready",
                       metadata=["Initiative: mvp-readiness"],
                       rows=[("m3", "C", ("low",) * 4)])
        out = self.report()
        lines = out.splitlines()
        self.assertEqual(lines[0], "3 specs · 2 epics · 1 initiatives")
        self.assertEqual(lines[1], "shipped 0/3")
        self.assertEqual(lines[2], "")
        self.assertEqual(
            self.lane_headers(out),
            ["UNPLANNED (3)", "READY (0)", "BUILDING (0)", "SHIPPED (0)"])

    def test_totals_count_epic_members_not_standalone(self):
        self.make_epic("e1", status="ready",
                       rows=[("m1", "A", ("low",) * 4)])
        self.make_change("solo", status="active")
        lines = self.report().splitlines()
        # `solo` is not a spec in the totals line, but it is a rendered row.
        self.assertEqual(lines[0], "1 specs · 1 epics · 0 initiatives")
        self.assertEqual(lines[1], "shipped 0/2")

    def test_shipped_line_counts_members_and_standalone(self):
        self.make_epic("e1", status="active",
                       rows=[("m1", "A", ("low",) * 4),
                             ("m2", "B", ("low",) * 4)])
        self.make_completed("m1")
        self.make_change("solo", status="active")
        self.assertEqual(self.report().splitlines()[1], "shipped 1/3")

    def test_empty_workspace_reports_zeroes(self):
        out = self.report()
        lines = out.splitlines()
        self.assertEqual(lines[0], "0 specs · 0 epics · 0 initiatives")
        self.assertEqual(lines[1], "shipped 0/0")
        self.assertEqual(
            self.lane_headers(out),
            ["UNPLANNED (0)", "READY (0)", "BUILDING (0)", "SHIPPED (0)"])

    # -- the non-shipped rows ----------------------------------------------

    def test_member_row_carries_its_epic_state_and_risk(self):
        self.make_epic("e1", status="ready",
                       rows=[("m1", "A", ("low", "medium", "low", "high"))])
        lane, row = self.row_for(self.report(), "m1")
        self.assertEqual(lane, "UNPLANNED")
        self.assertEqual(row.split(), ["e1", "m1", "unplanned", "risk", "high"])

    def test_member_row_without_ratings_reports_question_mark_risk(self):
        self.make_epic("e1", status="ready", rows=[("m1", "A", ())])
        _lane, row = self.row_for(self.report(), "m1")
        self.assertEqual(row.split(), ["e1", "m1", "unplanned", "risk", "?"])

    def test_worktree_derived_member_row_is_marked(self):
        self.make_epic("e1", status="ready",
                       rows=[("m1", "A", ("low",) * 4)])
        self.make_worktree_change("m1", "m1", "ready")
        lane, row = self.row_for(self.report(), "m1")
        self.assertEqual(lane, "READY")
        self.assertEqual(
            row.split(), ["e1", "m1", "ready", "risk", "low", "[worktree]"])

    def test_invocation_root_member_row_is_not_marked(self):
        self.make_epic("e1", status="active",
                       rows=[("m1", "A", ("low",) * 4)])
        self.make_change("m1", status="active")
        out = self.report()
        self.assertNotIn("[worktree]", out)
        lane, row = self.row_for(out, "m1")
        self.assertEqual(lane, "BUILDING")
        self.assertEqual(row.split(), ["e1", "m1", "active", "risk", "low"])

    def test_standalone_change_folds_in_under_standalone(self):
        self.make_change("solo", status="active")
        lane, row = self.row_for(self.report(), "solo")
        self.assertEqual(lane, "BUILDING")
        self.assertEqual(
            row.split(), ["standalone", "solo", "active", "risk", "?"])

    def test_worktree_hosted_standalone_row_is_marked(self):
        self.make_worktree_change("solo", "solo", "ready")
        lane, row = self.row_for(self.report(), "solo")
        self.assertEqual(lane, "READY")
        self.assertEqual(
            row.split(),
            ["standalone", "solo", "ready", "risk", "?", "[worktree]"])

    # -- the shipped lane --------------------------------------------------

    def test_shipped_lane_rolls_up_per_epic(self):
        self.make_epic("e1", status="active",
                       rows=[("m1", "A", ("low",) * 4),
                             ("m2", "B", ("low",) * 4)])
        self.make_epic("e2", status="active",
                       rows=[("m3", "C", ("low",) * 4)])
        for slug in ("m1", "m2", "m3"):
            self.make_completed(slug)
        out = self.report()
        self.assertEqual([row.strip() for row in self.rows_in(out, "SHIPPED")],
                         ["e1 (2)", "e2 (1)"])
        # Rollups only — never a flat member row.
        self.assertIsNone(self.row_for(out, "m1")[1])
        self.assertIn("SHIPPED (3)", self.lane_headers(out))

    def test_shipped_lane_appends_standalone_rollup_last(self):
        self.make_epic("e1", status="active",
                       rows=[("m1", "A", ("low",) * 4)])
        self.make_completed("m1")
        self.make_worktree_completed("solo", "solo")
        out = self.report()
        self.assertEqual([row.strip() for row in self.rows_in(out, "SHIPPED")],
                         ["e1 (1)", "standalone (1)"])
        self.assertEqual(out.splitlines()[1], "shipped 2/2")

    # -- worktree-authored epics -------------------------------------------

    def test_worktree_authored_epic_counts_in_the_totals(self):
        self.make_epic("e1", status="ready",
                       metadata=["Initiative: mvp-readiness"],
                       rows=[("m1", "A", ("low",) * 4)])
        self.make_worktree_epic(
            "epic-shipd-port", "shipd-port", status="ready",
            metadata=["Initiative: shipd-dx"],
            rows=[("m2", "B", ("low",) * 4),
                  ("m3", "C", ("low",) * 4)])
        lines = self.report().splitlines()
        self.assertEqual(lines[0], "3 specs · 2 epics · 2 initiatives")
        self.assertEqual(lines[1], "shipped 0/3")

    def test_worktree_authored_epic_members_render_under_their_lanes(self):
        self.make_worktree_epic(
            "epic-shipd-port", "shipd-port", status="active",
            rows=[("m1", "A", ("low", "low", "low", "high")),
                  ("m2", "B", ("low",) * 4)])
        self.make_completed("m2")
        out = self.report()
        lane, row = self.row_for(out, "m1")
        self.assertEqual(lane, "UNPLANNED")
        self.assertEqual(
            row.split(), ["shipd-port", "m1", "unplanned", "risk", "high"])
        self.assertEqual([r.strip() for r in self.rows_in(out, "SHIPPED")],
                         ["shipd-port (1)"])

    def test_a_duplicated_epic_slug_is_counted_once_from_the_root(self):
        self.make_epic("shipd-port", status="ready",
                       rows=[("m1", "A", ("low",) * 4)])
        self.make_worktree_epic(
            "epic-shipd-port", "shipd-port", status="active",
            rows=[("m1", "A", ("low",) * 4),
                  ("m2", "B", ("low",) * 4)])
        lines = self.report().splitlines()
        # The root's copy — one member, not the worktree's two.
        self.assertEqual(lines[0], "1 specs · 1 epics · 0 initiatives")
        self.assertIsNone(self.row_for(self.report(), "m2")[1])

    def test_an_unreadable_worktree_config_does_not_break_the_report(self):
        self.make_epic("e1", status="ready",
                       rows=[("m1", "A", ("low",) * 4)])
        self.make_broken_worktree("epic-broken")
        self.make_worktree_epic("epic-shipd-port", "shipd-port", status="ready",
                                rows=[("m2", "B", ("low",) * 4)])
        lines = self.report().splitlines()
        self.assertEqual(lines[0], "2 specs · 2 epics · 0 initiatives")

    # -- fail-soft and the untouched neighbours ------------------------------

    def test_unreadable_epic_file_is_skipped(self):
        self.make_epic("e1", status="ready",
                       rows=[("m1", "A", ("low",) * 4)])
        # An `epic.md` that is a directory: the read raises OSError, and the
        # report skips that epic rather than failing.
        os.makedirs(os.path.join(self.root, ".shipd", "epics", "broken",
                                 "epic.md"))
        out = self.report()
        self.assertEqual(out.splitlines()[0], "1 specs · 1 epics · 0 initiatives")
        self.assertEqual(self.row_for(out, "m1")[0], "UNPLANNED")

    def test_a_selection_wins_over_the_workspace_report(self):
        self.make_epic("e1", status="ready",
                       rows=[("m1", "A", ("low",) * 4)])
        self.make_change("feat", status="draft")
        self.cli("use", "feat")
        r = self.cli("show")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "feat: draft")

    def test_bare_status_without_a_selection_still_errors(self):
        self.make_epic("e1", status="ready",
                       rows=[("m1", "A", ("low",) * 4)])
        r = self.cli("status")
        self.assertEqual(r.returncode, 1)
        self.assertIn("no change given and no spec selected", r.stderr)


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


class WorkspaceShowChainTest(SpecStatusTestBase):
    """``workspace-show``'s registry provenance when the project registry
    falls through the workspace chain (spec-status workspace-status-verbs,
    shipd-workspace workspace-chain-facilities). ``self.root`` is the outer
    workspace; ``self.inner`` nests beneath it and ``self.repo`` (under
    ``self.inner``) is where the verb runs from."""

    def setUp(self):
        super().setUp()
        self.inner = os.path.join(self.root, "nested")
        os.makedirs(self.inner, exist_ok=True)
        self.repo = os.path.join(self.inner, "repo")
        os.makedirs(self.repo, exist_ok=True)

    def cli_at(self, cwd, *args):
        return subprocess.run(
            ["python3", SCRIPT, "--root", cwd, *args],
            capture_output=True, text=True)

    def test_nested_workspace_with_no_projects_inherits_the_outer_registry(self):
        self.declare_workspace({"projects": {
            "alpha": {"repos": ["present-repo"]}}})  # outer, at self.root
        os.makedirs(os.path.join(self.root, "present-repo"), exist_ok=True)
        self.declare_workspace(root=self.inner)  # inner declares no projects

        r = self.cli_at(self.repo, "workspace-show")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("alpha", r.stdout)
        self.assertIn("present-repo", r.stdout)
        # Provenance names the outer root exactly (full-line match, since the
        # outer root is a path *prefix* of the inner one — a plain substring
        # check would pass even without real provenance).
        lines = r.stdout.splitlines()
        self.assertIn("registry: %s" % self.root, lines)

    def test_nested_workspace_with_own_projects_shows_only_its_own(self):
        self.declare_workspace({"projects": {
            "alpha": {"repos": ["outer-repo"]}}})  # outer, at self.root
        os.makedirs(os.path.join(self.root, "outer-repo"), exist_ok=True)
        os.makedirs(os.path.join(self.inner, "inner-repo"), exist_ok=True)
        self.declare_workspace(
            {"projects": {"beta": {"repos": ["inner-repo"]}}},
            root=self.inner)  # inner declares its own projects

        r = self.cli_at(self.repo, "workspace-show")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("beta", r.stdout)
        self.assertIn("inner-repo", r.stdout)
        self.assertNotIn("alpha", r.stdout)
        self.assertNotIn("outer-repo", r.stdout)
        # No provenance line: the effective registry is the workspace's own.
        lines = r.stdout.splitlines()
        self.assertFalse(any(line.startswith("registry: ") for line in lines))


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

    # -- nested option -------------------------------------------------------

    def test_nested_flag_creates_under_an_enclosing_workspace(self):
        # A workspace declared at self.root is discoverable from the target.
        self.declare_workspace()
        target = os.path.join(self.root, "nested")
        os.makedirs(target)
        r = self.cli("workspace-init", target, "--nested")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(target, r.stdout)
        self.assertIn(self.root, r.stdout)
        marker = self.marker_path(target)
        self.assertTrue(os.path.isfile(marker))
        with open(marker, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(data["workspace"], {})

    def test_bare_verb_still_refuses_under_an_enclosing_workspace(self):
        self.declare_workspace()
        target = os.path.join(self.root, "nested")
        os.makedirs(target)
        r = self.cli("workspace-init", target)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn(self.root, r.stderr)
        self.assertFalse(os.path.exists(self.marker_path(target)))


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
        # Content directory prints as the default `.shipd`; keys show `default`.
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

    # -- nested chain --------------------------------------------------------

    def cli_at(self, cwd, *args):
        env = dict(os.environ)
        env["HOME"] = self.home
        return subprocess.run(
            ["python3", SCRIPT, "--root", cwd, *args],
            capture_output=True, text=True, env=env)

    def test_nested_chain_reports_nearest_root_and_chain_line(self):
        self._write_config(self.root, {"workspace": {}})
        inner = os.path.join(self.root, "nested")
        self._write_config(inner, {"workspace": {}})
        repo = os.path.join(inner, "repo")
        os.makedirs(repo, exist_ok=True)
        r = self.cli_at(repo, "config-show")
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = r.stdout.splitlines()
        self.assertIn("workspace: %s" % inner, lines)
        self.assertIn("chain: %s, %s" % (inner, self.root), lines)

    def test_single_member_chain_prints_no_chain_line(self):
        self._write_config(self.root, {"workspace": {}})
        r = self.cli("config-show")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("chain:", r.stdout)


class PipelineShowTest(SpecStatusTestBase):
    """`pipeline-show` prints the effective autonomous pipeline: one line per
    resolved entry plus the provenance of the key, `[default]` when no layer
    declares it (spec-status pipeline-show-verb). The verb requires neither a
    workspace nor a selected change. Rendering a *declared* pipeline resolves
    it through the pydantic schema, so those cases live in
    ``tests_pydantic/test_pipeline_show.py`` and this suite keeps passing with
    pydantic absent. ``$HOME`` is isolated so the real home config never leaks
    in."""

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

    def test_defaults_only_prints_six_stages_and_default(self):
        # No layer declares the key, no workspace, no selected change.
        r = self.cli("pipeline-show")
        self.assertEqual(r.returncode, 0, r.stderr)
        for stage in ("research", "epic", "plan", "gate", "build", "review"):
            self.assertIn(stage, r.stdout)
        self.assertIn("[default]", r.stdout)

    def test_expand_default_prints_bare_stage_json_without_pydantic(self):
        # `--expand default` resolves no config and needs no third-party
        # package: the JSON is the exact value a config may declare as a list.
        r = self.cli("pipeline-show", "--expand", "default")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(
            json.loads(r.stdout),
            [{"stage": name} for name in sc.PIPELINE_STAGES])
        self.assertIn("\n  ", r.stdout)   # indented, not one compact line

    def test_expand_unknown_preset_lists_known_names(self):
        r = self.cli("pipeline-show", "--expand", "turbo")
        self.assertNotEqual(r.returncode, 0)
        combined = r.stdout + r.stderr
        self.assertIn("turbo", combined)
        for name in ("basic", "default", "eco"):
            self.assertIn(name, combined)

    def test_json_defaults_only_emits_source_and_entries(self):
        # The machine contract: exactly one JSON object, `source` the raw
        # provenance value (`default`, undecorated) and `entries` the resolved
        # entries as dicts carrying exactly the keys each entry declared.
        r = self.cli("pipeline-show", "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        payload = json.loads(r.stdout)
        self.assertEqual(payload["source"], "default")
        self.assertEqual(
            payload["entries"], [{"stage": name} for name in sc.PIPELINE_STAGES])

    def test_json_expand_matches_flagless_expand(self):
        # `--expand <preset> --json` keeps the entry-list array contract: the
        # flag is accepted so a machine consumer can uniformly pass it.
        flagless = self.cli("pipeline-show", "--expand", "default")
        flagged = self.cli("pipeline-show", "--expand", "default", "--json")
        self.assertEqual(flagged.returncode, 0, flagged.stderr)
        self.assertEqual(flagged.stdout, flagless.stdout)
        self.assertEqual(
            json.loads(flagged.stdout),
            [{"stage": name} for name in sc.PIPELINE_STAGES])

    def test_text_mode_unchanged_without_the_flag(self):
        # Adding the flag must not disturb the human rendering.
        r = self.cli("pipeline-show")
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = r.stdout.splitlines()
        self.assertEqual(lines[0], "pipeline (source: [default]):")
        self.assertEqual(
            lines[1:],
            ["  %d. %s" % (i, name)
             for i, name in enumerate(sc.PIPELINE_STAGES, 1)])


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

    def make_archived_change(self, change, date, body="Archived idea.\n"):
        """Create `.shipd/completed/<date>-<change>/` with a plan, one delta
        spec, and tasks — the shape `spec_merge.py` leaves behind."""
        cdir = os.path.join(
            self.root, ".shipd", "completed", "%s-%s" % (date, change))
        specs = os.path.join(cdir, "specs", "example")
        os.makedirs(specs)
        with open(os.path.join(cdir, "plan.md"), "w", encoding="utf-8") as fh:
            fh.write("# %s\nStatus: verified\n\n## Idea\n%s" % (change, body))
        with open(os.path.join(specs, "spec.md"), "w",
                  encoding="utf-8") as fh:
            fh.write("## ADDED Requirements\n\n"
                     "### Requirement: Example\nid: example\n\n"
                     "The system SHALL do a thing.\n")
        with open(os.path.join(cdir, "tasks.md"), "w",
                  encoding="utf-8") as fh:
            fh.write("# Tasks\n\n- [x] 1.1 [req: *] Did the thing.\n")
        return cdir

    def test_cat_change_falls_back_to_completed_archive(self):
        """A change present only under `completed/<date>-<slug>/` still prints
        (spec-io mediated-read-verb)."""
        self.make_archived_change("my-change", "2026-08-14")
        r = self.cli("cat", "change", "my-change")
        self.assertEqual(r.returncode, 0, r.stderr)
        adir = os.path.join(".shipd", "completed", "2026-08-14-my-change")
        for sep in ("--- " + os.path.join(adir, "plan.md"),
                    "--- " + os.path.join(adir, "specs", "example", "spec.md"),
                    "--- " + os.path.join(adir, "tasks.md")):
            self.assertIn(sep, r.stdout)
        self.assertIn("Archived idea", r.stdout)
        self.assertIn("Requirement: Example", r.stdout)
        self.assertIn("Did the thing", r.stdout)

    def test_cat_change_prefers_the_newest_archive(self):
        """With several archives of one slug the lexicographically last (newest
        date prefix) wins."""
        self.make_archived_change("my-change", "2026-01-01", "Older idea.\n")
        self.make_archived_change("my-change", "2026-02-02", "Newer idea.\n")
        r = self.cli("cat", "change", "my-change")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("2026-02-02-my-change", r.stdout)
        self.assertNotIn("2026-01-01-my-change", r.stdout)
        self.assertIn("Newer idea", r.stdout)
        self.assertNotIn("Older idea", r.stdout)

    def test_cat_change_prefers_planned_over_the_archive(self):
        """`planned/<slug>/` resolves first; the archive is only a fallback."""
        self.make_change("my-change", status="active")
        self.make_archived_change("my-change", "2026-08-14")
        r = self.cli("cat", "change", "my-change")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(
            "--- " + os.path.join(".shipd", "planned", "my-change", "plan.md"),
            r.stdout)
        self.assertNotIn("2026-08-14-my-change", r.stdout)

    def test_cat_change_lists_one_artefact(self):
        """`cat change` lists a single artefact's path and size after the
        artifact content, printing no content of its own (spec-io
        mediated-read-verb)."""
        cdir = self.make_change(
            "my-change", status="draft",
            tasks="# Tasks\n\n- [ ] 1.1 [req: *] Do the thing.\n")
        self.make_valid_delta("my-change")
        adir = os.path.join(cdir, "artefacts")
        os.makedirs(adir)
        apath = os.path.join(adir, "policy.md")
        with open(apath, "w", encoding="utf-8") as fh:
            fh.write("Policy text.\n")
        size = os.path.getsize(apath)
        r = self.cli("cat", "change", "my-change")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("--- artefacts", r.stdout)
        rel = os.path.join(
            ".shipd", "planned", "my-change", "artefacts", "policy.md")
        self.assertIn("%s (%d bytes)" % (rel, size), r.stdout)
        self.assertNotIn("Policy text.", r.stdout)
        # The artefacts listing comes after the existing artifact output.
        self.assertLess(
            r.stdout.index("Do the thing"), r.stdout.index("--- artefacts"))

    def test_cat_change_lists_artefacts_sorted(self):
        """Two artefacts are listed sorted by path."""
        cdir = self.make_change(
            "my-change", status="draft",
            tasks="# Tasks\n\n- [ ] 1.1 [req: *] Do the thing.\n")
        self.make_valid_delta("my-change")
        adir = os.path.join(cdir, "artefacts")
        os.makedirs(adir)
        with open(os.path.join(adir, "zeta.md"), "w",
                  encoding="utf-8") as fh:
            fh.write("Z.\n")
        with open(os.path.join(adir, "alpha.md"), "w",
                  encoding="utf-8") as fh:
            fh.write("A.\n")
        r = self.cli("cat", "change", "my-change")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertLess(
            r.stdout.index("alpha.md"), r.stdout.index("zeta.md"))

    def test_cat_change_nested_artefact_uses_full_path(self):
        """A nested artefact's listed path includes its subdirectory."""
        cdir = self.make_change(
            "my-change", status="draft",
            tasks="# Tasks\n\n- [ ] 1.1 [req: *] Do the thing.\n")
        self.make_valid_delta("my-change")
        adir = os.path.join(cdir, "artefacts", "sub")
        os.makedirs(adir)
        apath = os.path.join(adir, "notes.md")
        with open(apath, "w", encoding="utf-8") as fh:
            fh.write("Notes.\n")
        size = os.path.getsize(apath)
        r = self.cli("cat", "change", "my-change")
        self.assertEqual(r.returncode, 0, r.stderr)
        rel = os.path.join(
            ".shipd", "planned", "my-change", "artefacts", "sub", "notes.md")
        self.assertIn("%s (%d bytes)" % (rel, size), r.stdout)

    def test_cat_change_artefacts_skips_unreadable_entry(self):
        """A dangling symlink under artefacts/ is skipped, not raised: the
        mediated read is a listing aid and must never fail on a change that
        lints clean (spec-io mediated-read-verb)."""
        cdir = self.make_change(
            "my-change", status="draft",
            tasks="# Tasks\n\n- [ ] 1.1 [req: *] Do the thing.\n")
        self.make_valid_delta("my-change")
        adir = os.path.join(cdir, "artefacts")
        os.makedirs(adir)
        with open(os.path.join(adir, "policy.md"), "w",
                  encoding="utf-8") as fh:
            fh.write("Policy text.\n")
        os.symlink("/nonexistent/target", os.path.join(adir, "dangling.md"))
        r = self.cli("cat", "change", "my-change")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("--- artefacts", r.stdout)
        self.assertIn("policy.md (", r.stdout)
        self.assertNotIn("dangling.md", r.stdout)

    def test_cat_change_without_artefacts_has_no_header(self):
        """A change with no `artefacts/` directory prints no such header."""
        self.make_change(
            "my-change", status="draft",
            tasks="# Tasks\n\n- [ ] 1.1 [req: *] Do the thing.\n")
        self.make_valid_delta("my-change")
        r = self.cli("cat", "change", "my-change")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("--- artefacts", r.stdout)

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
                "## Speakers\n\n- Ada — product lead\n\n"
                "## Intents\n\n### Explain the signal\n\nClear [1].\n\n"
                "## Sources\n\n1. [00:14:22.4] Ada: clear.\n")
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
            "- Asked: 2026-07-30 teach-session\n"
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


class WikiChainTest(SpecStatusTestBase):
    """Chain-aware ``cat wiki`` (spec-status wiki-status-verbs, shipd-wiki
    wiki-store-layout): reads resolve across the workspace chain, nearest
    first. ``self.root`` is the outer workspace; ``self.inner`` nests beneath
    it and ``self.repo`` (under ``self.inner``) is where the verb runs from."""

    def setUp(self):
        super().setUp()
        self.declare_workspace()  # outer workspace at self.root
        self.assertEqual(self.cli("wiki-init").returncode, 0)
        self.inner = os.path.join(self.root, "nested")
        os.makedirs(self.inner, exist_ok=True)
        self.declare_workspace(root=self.inner)  # nested workspace
        self.repo = os.path.join(self.inner, "repo")
        os.makedirs(self.repo, exist_ok=True)

    def cli_at(self, cwd, *args):
        return subprocess.run(
            ["python3", SCRIPT, "--root", cwd, *args],
            capture_output=True, text=True)

    def wiki_of(self, ws_root):
        return os.path.join(ws_root, ".shipd", "wiki")

    def write_page(self, ws_root, slug, text):
        pages = os.path.join(self.wiki_of(ws_root), "wiki")
        os.makedirs(pages, exist_ok=True)
        with open(os.path.join(pages, slug + ".md"), "w",
                  encoding="utf-8") as fh:
            fh.write(text)

    def write_wiki_file(self, ws_root, name, text):
        with open(os.path.join(self.wiki_of(ws_root), name), "w",
                  encoding="utf-8") as fh:
            fh.write(text)

    def init_inner_store(self):
        r = self.cli_at(self.inner, "wiki-init")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_page_held_only_by_outer_store_prints_from_there(self):
        self.write_page(self.root, "conventions", "# Conventions\n\nOuter.\n")
        r = self.cli_at(self.repo, "cat", "wiki", "conventions")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Outer.", r.stdout)
        sep = os.path.relpath(
            os.path.join(self.wiki_of(self.root), "wiki", "conventions.md"),
            self.repo)
        self.assertIn("--- %s" % sep, r.stdout)

    def test_page_held_by_both_prints_the_inner_one(self):
        self.init_inner_store()
        self.write_page(self.root, "conventions", "# Conventions\n\nOuter.\n")
        self.write_page(self.inner, "conventions", "# Conventions\n\nInner.\n")
        r = self.cli_at(self.repo, "cat", "wiki", "conventions")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Inner.", r.stdout)
        self.assertNotIn("Outer.", r.stdout)
        sep = os.path.relpath(
            os.path.join(self.wiki_of(self.inner), "wiki", "conventions.md"),
            self.repo)
        self.assertIn("--- %s" % sep, r.stdout)

    def test_cat_wiki_index_aggregates_every_chain_store_nearest_first(self):
        self.init_inner_store()
        self.write_wiki_file(
            self.root, "index.md", "# Index\n\n- [[a]] — Outer page.\n")
        self.write_wiki_file(
            self.inner, "index.md", "# Index\n\n- [[b]] — Inner page.\n")
        r = self.cli_at(self.repo, "cat", "wiki", "index")
        self.assertEqual(r.returncode, 0, r.stderr)
        inner_sep = os.path.relpath(
            os.path.join(self.wiki_of(self.inner), "index.md"), self.repo)
        outer_sep = os.path.relpath(
            os.path.join(self.wiki_of(self.root), "index.md"), self.repo)
        inner_pos = r.stdout.find("--- %s" % inner_sep)
        outer_pos = r.stdout.find("--- %s" % outer_sep)
        self.assertNotEqual(inner_pos, -1)
        self.assertNotEqual(outer_pos, -1)
        self.assertLess(inner_pos, outer_pos)
        self.assertIn("Outer page.", r.stdout)
        self.assertIn("Inner page.", r.stdout)

    def test_cat_wiki_queue_aggregates_every_chain_store_nearest_first(self):
        self.init_inner_store()
        self.write_wiki_file(self.root, "queue.md", "# Queue\n\nOuter queue.\n")
        self.write_wiki_file(self.inner, "queue.md", "# Queue\n\nInner queue.\n")
        r = self.cli_at(self.repo, "cat", "wiki", "queue")
        self.assertEqual(r.returncode, 0, r.stderr)
        inner_sep = os.path.relpath(
            os.path.join(self.wiki_of(self.inner), "queue.md"), self.repo)
        outer_sep = os.path.relpath(
            os.path.join(self.wiki_of(self.root), "queue.md"), self.repo)
        inner_pos = r.stdout.find("--- %s" % inner_sep)
        outer_pos = r.stdout.find("--- %s" % outer_sep)
        self.assertNotEqual(inner_pos, -1)
        self.assertNotEqual(outer_pos, -1)
        self.assertLess(inner_pos, outer_pos)
        self.assertIn("Outer queue.", r.stdout)
        self.assertIn("Inner queue.", r.stdout)

    def test_page_held_only_by_outer_store_annotates_inherited_provenance(self):
        self.write_page(self.root, "conventions", "# Conventions\n\nOuter.\n")
        r = self.cli_at(self.repo, "cat", "wiki", "conventions")
        self.assertEqual(r.returncode, 0, r.stderr)
        sep = os.path.relpath(
            os.path.join(self.wiki_of(self.root), "wiki", "conventions.md"),
            self.repo)
        self.assertIn(
            "--- %s  (inherited %s)" % (sep, self.root), r.stdout)

    def test_page_held_by_nearest_store_has_no_annotation(self):
        self.init_inner_store()
        self.write_page(self.inner, "conventions", "# Conventions\n\nInner.\n")
        r = self.cli_at(self.repo, "cat", "wiki", "conventions")
        self.assertEqual(r.returncode, 0, r.stderr)
        sep = os.path.relpath(
            os.path.join(self.wiki_of(self.inner), "wiki", "conventions.md"),
            self.repo)
        self.assertIn("--- %s\n" % sep, r.stdout)
        self.assertNotIn("inherited", r.stdout)

    def test_cat_wiki_index_annotates_only_inherited_store(self):
        self.init_inner_store()
        self.write_wiki_file(
            self.root, "index.md", "# Index\n\n- [[a]] — Outer page.\n")
        self.write_wiki_file(
            self.inner, "index.md", "# Index\n\n- [[b]] — Inner page.\n")
        r = self.cli_at(self.repo, "cat", "wiki", "index")
        self.assertEqual(r.returncode, 0, r.stderr)
        inner_sep = os.path.relpath(
            os.path.join(self.wiki_of(self.inner), "index.md"), self.repo)
        outer_sep = os.path.relpath(
            os.path.join(self.wiki_of(self.root), "index.md"), self.repo)
        self.assertIn("--- %s\n" % inner_sep, r.stdout)
        self.assertIn(
            "--- %s  (inherited %s)" % (outer_sep, self.root), r.stdout)

    def test_cat_wiki_log_reads_nearest_store_only(self):
        self.init_inner_store()
        self.write_wiki_file(self.root, "log.md", "# Log\n\nOuter log.\n")
        self.write_wiki_file(self.inner, "log.md", "# Log\n\nInner log.\n")
        r = self.cli_at(self.repo, "cat", "wiki", "log")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Inner log.", r.stdout)
        self.assertNotIn("Outer log.", r.stdout)

    def test_cat_wiki_schema_reads_nearest_store_only(self):
        self.init_inner_store()
        self.write_wiki_file(self.root, "schema.md", "# Schema\n\nOuter.\n")
        self.write_wiki_file(self.inner, "schema.md", "# Schema\n\nInner.\n")
        r = self.cli_at(self.repo, "cat", "wiki", "schema")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Inner.", r.stdout)
        self.assertNotIn("Outer.", r.stdout)

    def test_cat_wiki_log_held_only_by_outer_store_annotates_inherited(self):
        # self.inner's own store is never initialized, so `log` resolves to
        # the outer store — an inherited read, which must carry the
        # provenance annotation like the page and index/queue branches do.
        self.write_wiki_file(self.root, "log.md", "# Log\n\nOuter log.\n")
        r = self.cli_at(self.repo, "cat", "wiki", "log")
        self.assertEqual(r.returncode, 0, r.stderr)
        sep = os.path.relpath(
            os.path.join(self.wiki_of(self.root), "log.md"), self.repo)
        self.assertIn(
            "--- %s  (inherited %s)" % (sep, self.root), r.stdout)

    def test_cat_wiki_log_held_by_nearest_store_has_no_annotation(self):
        self.init_inner_store()
        self.write_wiki_file(self.inner, "log.md", "# Log\n\nInner log.\n")
        r = self.cli_at(self.repo, "cat", "wiki", "log")
        self.assertEqual(r.returncode, 0, r.stderr)
        sep = os.path.relpath(
            os.path.join(self.wiki_of(self.inner), "log.md"), self.repo)
        self.assertIn("--- %s\n" % sep, r.stdout)
        self.assertNotIn("inherited", r.stdout)

    def test_cat_wiki_missing_page_reports_nearest_store_not_outer(self):
        # self.inner's own store is never initialized, so the nearest
        # workspace's store (self.inner) is where a missing page should be
        # reported — not the outer store that happens to exist on disk.
        r = self.cli_at(self.repo, "cat", "wiki", "nope")
        self.assertNotEqual(r.returncode, 0)
        expected = os.path.join(self.wiki_of(self.inner), "wiki", "nope.md")
        self.assertIn(expected, r.stderr)
        outer = os.path.join(self.wiki_of(self.root), "wiki", "nope.md")
        self.assertNotIn(outer, r.stderr)


class WikiShowChainTest(SpecStatusTestBase):
    """``wiki-show``'s ``chain:`` line and absent-nearest-store handling
    (spec-status wiki-status-verbs, shipd-config wiki-base-key). ``self.root``
    is the outer workspace; ``self.inner`` nests beneath it and ``self.repo``
    (under ``self.inner``) is where the verb runs from. Unlike
    ``WikiChainTest``, no store is scaffolded in ``setUp`` — each test seeds
    exactly what it needs."""

    def setUp(self):
        super().setUp()
        self.declare_workspace()  # outer workspace at self.root
        self.inner = os.path.join(self.root, "nested")
        os.makedirs(self.inner, exist_ok=True)
        self.declare_workspace(root=self.inner)  # nested workspace
        self.repo = os.path.join(self.inner, "repo")
        os.makedirs(self.repo, exist_ok=True)

    def cli_at(self, cwd, *args):
        return subprocess.run(
            ["python3", SCRIPT, "--root", cwd, *args],
            capture_output=True, text=True)

    def wiki_of(self, ws_root):
        return os.path.join(ws_root, ".shipd", "wiki")

    def test_chain_line_names_inherited_store_when_one_exists(self):
        self.assertEqual(self.cli_at(self.root, "wiki-init").returncode, 0)
        self.assertEqual(self.cli_at(self.inner, "wiki-init").returncode, 0)
        r = self.cli_at(self.repo, "wiki-show")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("chain: %s" % self.wiki_of(self.root), r.stdout)

    def test_chain_line_is_none_with_no_inherited_member(self):
        # A single-member chain: only the nearest (inner) workspace has a
        # store; there is no enclosing store to inherit.
        self.assertEqual(self.cli_at(self.inner, "wiki-init").returncode, 0)
        r = self.cli_at(self.repo, "wiki-show")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("chain: none", r.stdout)

    def test_chain_line_is_none_under_personal(self):
        r = self.cli_at(self.repo, "wiki-init", "--personal")
        self.assertEqual(r.returncode, 0, r.stderr)
        r = self.cli_at(self.repo, "wiki-show", "--personal")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("chain: none", r.stdout)

    def test_base_none_when_wiki_base_points_at_a_chain_store(self):
        self.assertEqual(self.cli_at(self.root, "wiki-init").returncode, 0)
        with open(os.path.join(self.inner, ".shipd-config.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(
                {"workspace": {}, "wiki_base": self.wiki_of(self.root)}, fh)
        self.assertEqual(self.cli_at(self.inner, "wiki-init").returncode, 0)
        r = self.cli_at(self.repo, "wiki-show")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("base: none", r.stdout)

    def test_absent_nearest_store_reports_absent_and_still_exits_zero(self):
        # Only the outer workspace holds a store; the inner (nearest) does
        # not.
        self.assertEqual(self.cli_at(self.root, "wiki-init").returncode, 0)
        r = self.cli_at(self.repo, "wiki-show")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("absent", r.stdout.lower())
        self.assertIn(self.wiki_of(self.inner), r.stdout)
        self.assertIn("chain: %s" % self.wiki_of(self.root), r.stdout)

    def test_exits_non_zero_only_when_no_chain_member_holds_a_store(self):
        r = self.cli_at(self.repo, "wiki-show")
        self.assertNotEqual(r.returncode, 0)


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
                     "--origin", "teach-session")
        self.assertEqual(r.returncode, 0, r.stderr)
        queue = self.queue_text()
        self.assertIn("## q-stale-cache", queue)
        self.assertIn("Is the cache stale?", queue)
        self.assertIn("yes | no", queue)
        self.assertIn("Recommendation: yes", queue)
        self.assertIn("teach-session", queue)
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


class WikiQueueAddChainTest(SpecStatusTestBase):
    """``wiki-queue-add`` scaffolds the nearest workspace's store rather than
    erroring, even when only an enclosing chain member holds one (shipd-wiki
    wiki-store-layout). ``self.root`` is the outer workspace (holding a wiki
    store); ``self.inner`` nests beneath it with no store of its own."""

    def setUp(self):
        super().setUp()
        self.declare_workspace()  # outer workspace at self.root
        self.assertEqual(self.cli("wiki-init").returncode, 0)
        self.inner = os.path.join(self.root, "nested")
        os.makedirs(self.inner, exist_ok=True)
        self.declare_workspace(root=self.inner)  # nested workspace, no store

    def cli_at(self, cwd, *args):
        return subprocess.run(
            ["python3", SCRIPT, "--root", cwd, *args],
            capture_output=True, text=True)

    def wiki_of(self, ws_root):
        return os.path.join(ws_root, ".shipd", "wiki")

    def test_scaffolds_the_nearest_store_and_leaves_the_outer_untouched(self):
        outer_queue = os.path.join(self.wiki_of(self.root), "queue.md")
        with open(outer_queue, encoding="utf-8") as fh:
            outer_before = fh.read()
        self.assertFalse(os.path.isdir(self.wiki_of(self.inner)))

        r = self.cli_at(self.inner, "wiki-queue-add", "stale-cache",
                         "--question", "Is the cache stale?",
                         "--options", "yes | no",
                         "--recommendation", "yes")
        self.assertEqual(r.returncode, 0, r.stderr)

        inner_queue = os.path.join(self.wiki_of(self.inner), "queue.md")
        self.assertTrue(os.path.isfile(inner_queue))
        with open(inner_queue, encoding="utf-8") as fh:
            inner_after = fh.read()
        self.assertIn("## q-stale-cache", inner_after)
        self.assertIn("Is the cache stale?", inner_after)

        with open(outer_queue, encoding="utf-8") as fh:
            outer_after = fh.read()
        self.assertEqual(outer_after, outer_before)  # byte-identical


class WikiQueueAnswerTest(SpecStatusTestBase):
    """The ``wiki-queue-answer <slug> --answer "<text>"`` verb (shipd-wiki
    wiki-queue-answer-verb, wiki-autocommit): it writes a user's answer into a
    still-pending queue block. ``self.root`` doubles as the workspace root; the
    store lives at ``<root>/.shipd/wiki/``."""

    def queue_text(self):
        with open(os.path.join(self.root, ".shipd", "wiki", "queue.md"),
                  encoding="utf-8") as fh:
            return fh.read()

    def make_store(self):
        self.declare_workspace()
        self.cli("wiki-init")

    def add_block(self, slug):
        r = self.cli("wiki-queue-add", slug,
                     "--question", "Q?", "--options", "a | b",
                     "--recommendation", "a")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_pending_block_is_answered(self):
        self.make_store()
        self.add_block("retention")
        r = self.cli("wiki-queue-answer", "retention",
                     "--answer", "prune after one release")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "q-retention")
        queue = self.queue_text()
        self.assertIn("- Answer: prune after one release", queue)
        self.assertNotIn("Answer: pending", queue)

    def test_answer_leaves_other_blocks_pending(self):
        self.make_store()
        self.add_block("retention")
        self.add_block("cache-ttl")
        r = self.cli("wiki-queue-answer", "retention", "--answer", "one release")
        self.assertEqual(r.returncode, 0, r.stderr)
        queue = self.queue_text()
        self.assertIn("- Answer: one release", queue)
        self.assertEqual(queue.count("- Answer: pending"), 1)

    def test_missing_block_errors(self):
        self.make_store()
        self.add_block("retention")
        before = self.queue_text()
        r = self.cli("wiki-queue-answer", "no-such-entry", "--answer", "x")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("q-no-such-entry", r.stderr)
        self.assertEqual(self.queue_text(), before)  # byte-identical

    def test_already_answered_block_refused(self):
        self.make_store()
        self.add_block("retention")
        self.assertEqual(
            self.cli("wiki-queue-answer", "retention",
                     "--answer", "one release").returncode, 0)
        before = self.queue_text()
        r = self.cli("wiki-queue-answer", "retention", "--answer", "two releases")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("q-retention", r.stderr)
        self.assertIn("answered", r.stderr.lower())
        self.assertEqual(self.queue_text(), before)  # byte-identical

    def test_requires_workspace(self):
        r = self.cli("wiki-queue-answer", "retention", "--answer", "x")
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

    def _head_files(self):
        r = subprocess.run(
            ["git", "-C", self.root, "show", "--name-only", "--format=", "HEAD"],
            capture_output=True, text=True, check=True)
        return sorted(p for p in r.stdout.split("\n") if p.strip())

    def test_answer_commits_only_queue_md(self):
        self.make_store()
        self.add_block("retention")
        self._init_git()
        before = self._commit_count()
        r = self.cli("wiki-queue-answer", "retention", "--answer", "one release")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self._commit_count(), before + 1)
        self.assertEqual(self._head_files(), [".shipd/wiki/queue.md"])

    def test_refused_answer_makes_no_commit(self):
        self.make_store()
        self.add_block("retention")
        self._init_git()
        before = self._commit_count()
        r = self.cli("wiki-queue-answer", "no-such-entry", "--answer", "x")
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(self._commit_count(), before)

    def test_non_git_store_answers_without_git(self):
        self.make_store()
        self.add_block("retention")
        r = self.cli("wiki-queue-answer", "retention", "--answer", "one release")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("- Answer: one release", self.queue_text())
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


class RelatedTest(SpecStatusTestBase):
    """`related <term> [<term>...]` ranks the spec library's artifacts by
    case-insensitive term-hit count (spec-status related-verb), printing one
    keyed block per match — ``kind``/``slug``/``score``/``path`` — in
    descending score order, capped at ten blocks with a remainder line, or one
    JSON array with ``--json``.

    ``self.root`` doubles as the workspace root in the wiki cases; the
    no-workspace cases simply omit the declaration, so the wiki surface must
    degrade silently."""

    # -- fixture helpers ---------------------------------------------------

    def make_verified(self, slug, text):
        vdir = os.path.join(self.root, ".shipd", "verified", slug)
        os.makedirs(vdir, exist_ok=True)
        with open(os.path.join(vdir, "spec.md"), "w", encoding="utf-8") as fh:
            fh.write(text)
        return os.path.join(".shipd", "verified", slug, "spec.md")

    def make_planned(self, slug, plan="", tasks=None, delta=None):
        cdir = os.path.join(self.root, ".shipd", "planned", slug)
        os.makedirs(cdir, exist_ok=True)
        with open(os.path.join(cdir, "plan.md"), "w", encoding="utf-8") as fh:
            fh.write(plan)
        if tasks is not None:
            with open(os.path.join(cdir, "tasks.md"), "w",
                      encoding="utf-8") as fh:
                fh.write(tasks)
        if delta is not None:
            sdir = os.path.join(cdir, "specs", "example")
            os.makedirs(sdir, exist_ok=True)
            with open(os.path.join(sdir, "spec.md"), "w",
                      encoding="utf-8") as fh:
                fh.write(delta)
        return os.path.join(".shipd", "planned", slug)

    def make_completed(self, slug, date, plan="", tasks=None, delta=None):
        name = "%s-%s" % (date, slug)
        cdir = os.path.join(self.root, ".shipd", "completed", name)
        os.makedirs(cdir, exist_ok=True)
        with open(os.path.join(cdir, "plan.md"), "w", encoding="utf-8") as fh:
            fh.write(plan)
        if tasks is not None:
            with open(os.path.join(cdir, "tasks.md"), "w",
                      encoding="utf-8") as fh:
                fh.write(tasks)
        if delta is not None:
            sdir = os.path.join(cdir, "specs", "example")
            os.makedirs(sdir, exist_ok=True)
            with open(os.path.join(sdir, "spec.md"), "w",
                      encoding="utf-8") as fh:
                fh.write(delta)
        return os.path.join(".shipd", "completed", name)

    def make_research(self, slug, text):
        rdir = os.path.join(self.root, ".shipd", "research", slug)
        os.makedirs(rdir, exist_ok=True)
        with open(os.path.join(rdir, "report.md"), "w",
                  encoding="utf-8") as fh:
            fh.write(text)
        return os.path.join(".shipd", "research", slug, "report.md")

    def make_epic(self, slug, text):
        edir = os.path.join(self.root, ".shipd", "epics", slug)
        os.makedirs(edir, exist_ok=True)
        with open(os.path.join(edir, "epic.md"), "w", encoding="utf-8") as fh:
            fh.write(text)
        return os.path.join(".shipd", "epics", slug, "epic.md")

    def make_wiki_page(self, slug, text):
        pages = os.path.join(self.root, ".shipd", "wiki", "wiki")
        os.makedirs(pages, exist_ok=True)
        with open(os.path.join(pages, slug + ".md"), "w",
                  encoding="utf-8") as fh:
            fh.write(text)
        return os.path.join(".shipd", "wiki", "wiki", slug + ".md")

    # -- output parsing ----------------------------------------------------

    def blocks(self, stdout):
        """Split the verb's stdout into a list of {key: value} dicts, one per
        blank-line-separated keyed block (the trailing remainder line, which
        carries no ``key: value`` pairs, is skipped)."""
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

    def remainder(self, stdout):
        """The trailing line naming the un-printed matches, or None."""
        lines = [ln for ln in stdout.strip().splitlines() if ln.strip()]
        if lines and ":" not in lines[-1]:
            return lines[-1]
        return None

    # -- ranking -----------------------------------------------------------

    def test_matches_print_ranked_keyed_blocks(self):
        vpath = self.make_verified(
            "reporting",
            "# reporting\n\nThe system SHALL export. Export again.\n"
            "A third export here.\n")
        cpath = self.make_completed(
            "old-work", "2026-08-14",
            plan="# old-work\nStatus: verified\n\n## Idea\nOne export.\n")
        r = self.cli("related", "export")
        self.assertEqual(r.returncode, 0, r.stderr)
        blocks = self.blocks(r.stdout)
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0]["kind"], "verified")
        self.assertEqual(blocks[0]["slug"], "reporting")
        self.assertEqual(blocks[0]["score"], "3")
        self.assertEqual(blocks[0]["path"], vpath)
        # The completed slug prints with its YYYY-MM-DD- prefix stripped, so it
        # feeds `cat change <slug>` directly.
        self.assertEqual(blocks[1]["kind"], "completed")
        self.assertEqual(blocks[1]["slug"], "old-work")
        self.assertEqual(blocks[1]["score"], "1")
        self.assertEqual(blocks[1]["path"], cpath)

    def test_matching_is_case_insensitive_and_sums_over_terms(self):
        self.make_verified("reporting", "# reporting\n\nEXPORT the Ledger.\n")
        r = self.cli("related", "export", "ledger")
        self.assertEqual(r.returncode, 0, r.stderr)
        blocks = self.blocks(r.stdout)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["score"], "2")

    def test_score_sums_over_a_changes_files(self):
        """A planned change's plan, tasks, and delta specs all count toward the
        one artifact's score."""
        ppath = self.make_planned(
            "dark-mode",
            plan="# dark-mode\n\nAn export.\n",
            tasks="- [ ] 1.1 Wire the export.\n",
            delta="### Requirement: Export\nid: export\n")
        r = self.cli("related", "export")
        self.assertEqual(r.returncode, 0, r.stderr)
        blocks = self.blocks(r.stdout)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["kind"], "planned")
        self.assertEqual(blocks[0]["slug"], "dark-mode")
        self.assertEqual(blocks[0]["score"], "4")
        self.assertEqual(blocks[0]["path"], ppath)

    def test_research_and_epic_surfaces_are_searched(self):
        rpath = self.make_research(
            "payment-apis", "# Payment APIs\n\nExport support is broad [1].\n")
        epath = self.make_epic(
            "reporting-overhaul",
            "# reporting-overhaul\nStatus: draft\n\n## Introduction\n"
            "Export, then export again.\n")
        r = self.cli("related", "export")
        self.assertEqual(r.returncode, 0, r.stderr)
        by_kind = {b["kind"]: b for b in self.blocks(r.stdout)}
        self.assertEqual(sorted(by_kind), ["epic", "research"])
        self.assertEqual(by_kind["epic"]["slug"], "reporting-overhaul")
        self.assertEqual(by_kind["epic"]["score"], "2")
        self.assertEqual(by_kind["epic"]["path"], epath)
        self.assertEqual(by_kind["research"]["slug"], "payment-apis")
        self.assertEqual(by_kind["research"]["score"], "1")
        self.assertEqual(by_kind["research"]["path"], rpath)

    def test_non_matching_artifacts_are_dropped(self):
        self.make_verified("reporting", "# reporting\n\nAn export.\n")
        self.make_verified("auth", "# auth\n\nA login.\n")
        r = self.cli("related", "export")
        self.assertEqual(r.returncode, 0, r.stderr)
        blocks = self.blocks(r.stdout)
        self.assertEqual([b["slug"] for b in blocks], ["reporting"])

    def test_ties_break_by_kind_then_slug(self):
        self.make_verified("zeta", "export\n")
        self.make_verified("alpha", "export\n")
        self.make_epic("omega", "export\n")
        r = self.cli("related", "export")
        self.assertEqual(r.returncode, 0, r.stderr)
        blocks = self.blocks(r.stdout)
        self.assertEqual([(b["kind"], b["slug"]) for b in blocks],
                         [("epic", "omega"), ("verified", "alpha"),
                          ("verified", "zeta")])

    # -- cap ---------------------------------------------------------------

    def test_output_caps_at_ten_with_a_remainder_line(self):
        for n in range(1, 13):
            self.make_verified("cap-%02d" % n, "export\n")
        r = self.cli("related", "export")
        self.assertEqual(r.returncode, 0, r.stderr)
        blocks = self.blocks(r.stdout)
        self.assertEqual(len(blocks), 10)
        self.assertEqual([b["slug"] for b in blocks],
                         ["cap-%02d" % n for n in range(1, 11)])
        line = self.remainder(r.stdout)
        self.assertIsNotNone(line, r.stdout)
        self.assertIn("2", line)
        self.assertIn("more", line)

    def test_no_remainder_line_at_ten_or_fewer(self):
        for n in range(1, 11):
            self.make_verified("cap-%02d" % n, "export\n")
        r = self.cli("related", "export")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(len(self.blocks(r.stdout)), 10)
        self.assertIsNone(self.remainder(r.stdout))

    # -- JSON --------------------------------------------------------------

    def test_json_is_one_array_of_objects(self):
        vpath = self.make_verified("reporting", "export export\n")
        cpath = self.make_completed(
            "old-work", "2026-08-14", plan="One export.\n")
        r = self.cli("related", "export", "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(
            json.loads(r.stdout),
            [{"kind": "verified", "slug": "reporting", "score": 2,
              "path": vpath},
             {"kind": "completed", "slug": "old-work", "score": 1,
              "path": cpath}])

    def test_json_caps_at_ten_too(self):
        for n in range(1, 13):
            self.make_verified("cap-%02d" % n, "export\n")
        r = self.cli("related", "export", "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        rows = json.loads(r.stdout)
        self.assertEqual([row["slug"] for row in rows],
                         ["cap-%02d" % n for n in range(1, 11)])

    # -- errors and degradation --------------------------------------------

    def test_no_match_is_a_single_error_line(self):
        self.make_verified("reporting", "An export.\n")
        r = self.cli("related", "zzz-no-such-term")
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")
        lines = [ln for ln in r.stderr.strip().splitlines() if ln.strip()]
        self.assertEqual(len(lines), 1, r.stderr)
        self.assertTrue(lines[0].startswith("Error:"), lines[0])
        self.assertIn("zzz-no-such-term", lines[0])

    def test_no_match_in_json_mode_still_errors(self):
        r = self.cli("related", "zzz-no-such-term", "--json")
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")
        self.assertIn("Error:", r.stderr)

    def test_at_least_one_term_is_required(self):
        r = self.cli("related")
        self.assertEqual(r.returncode, 2)

    def test_absent_workspace_skips_the_wiki_silently(self):
        """No workspace is discoverable from the temp root, so the wiki surface
        is skipped without an error and every other surface still prints."""
        self.make_verified("reporting", "An export.\n")
        r = self.cli("related", "export")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stderr, "")
        self.assertNotIn("workspace", r.stdout.lower())
        self.assertEqual([b["slug"] for b in self.blocks(r.stdout)],
                         ["reporting"])

    def test_wiki_pages_match_when_a_workspace_resolves(self):
        self.declare_workspace()
        wpath = self.make_wiki_page(
            "export-conventions", "# Export conventions\n\nExport nightly.\n")
        r = self.cli("related", "export")
        self.assertEqual(r.returncode, 0, r.stderr)
        blocks = self.blocks(r.stdout)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["kind"], "wiki")
        self.assertEqual(blocks[0]["slug"], "export-conventions")
        self.assertEqual(blocks[0]["score"], "2")
        self.assertEqual(blocks[0]["path"], wpath)

    def test_missing_corpus_directories_are_skipped(self):
        """An empty content directory — no verified/, planned/, completed/,
        research/, or epics/ — is a clean no-match, not a crash."""
        os.makedirs(os.path.join(self.root, ".shipd"), exist_ok=True)
        r = self.cli("related", "export")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Error:", r.stderr)


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

    def snapshot_content(self):
        """Return a {path: bytes} snapshot of every file under the content
        directory so a test can assert the verb wrote nothing."""
        snap = {}
        content = os.path.join(self.root, ".shipd")
        for dirpath, _dirs, files in os.walk(content):
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
        before = self.snapshot_content()
        r = self.cli("check-base", "feat")
        self.assertEqual(r.returncode, 4, r.stdout + r.stderr)
        after = self.snapshot_content()
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


class JsonOutputTest(WorkspaceReportTest):
    """The ``--json`` machine-output flag on ``status``, ``show``, and
    ``epic-show`` (spec-status json-output): one JSON document on stdout,
    derived from the same data the text renderer prints, with the flagless
    text output unchanged.

    Written test-first; expected to FAIL until the flag lands in
    ``spec_status.py`` (task 1.2)."""

    def json_out(self, *args):
        """Run the CLI, assert a clean exit, and parse stdout as one JSON
        document (the whole of stdout — nothing else may be printed)."""
        r = self.cli(*args)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    # -- status ------------------------------------------------------------

    def test_status_json_reports_a_change(self):
        self.make_change("feat", status="active")
        self.assertEqual(
            self.json_out("status", "feat", "--json"),
            {"name": "feat", "kind": "change", "status": "active"})

    def test_status_json_reports_the_epic_fallback(self):
        self.make_epic("reporting", status="active",
                       rows=[("m1", "A", ("low",) * 4)])
        self.assertEqual(
            self.json_out("status", "reporting", "--json"),
            {"name": "reporting", "kind": "epic", "status": "active"})

    def test_status_json_carries_question_mark_for_a_missing_header(self):
        self.write_plan("feat", "no header here at all\n")
        self.assertEqual(
            self.json_out("status", "feat", "--json"),
            {"name": "feat", "kind": "change", "status": "?"})

    def test_status_text_is_unchanged_without_the_flag(self):
        self.make_change("feat", status="active")
        r = self.cli("status", "feat")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "active\n")

    # -- show, on a change --------------------------------------------------

    def test_show_json_on_a_change_carries_task_counts(self):
        self.make_change(
            "feat", status="active",
            tasks="## 1\n- [x] 1.1 done\n- [ ] 1.2 todo\n- [~] 1.3 wip\n")
        self.assertEqual(
            self.json_out("show", "feat", "--json"),
            {"name": "feat", "kind": "change", "status": "active",
             "tasks": {"done": 1, "in_progress": 1, "total": 3},
             "metadata": {}})

    def test_show_json_tasks_are_null_without_a_checklist(self):
        self.make_change("feat", status="ready")
        self.assertEqual(
            self.json_out("show", "feat", "--json"),
            {"name": "feat", "kind": "change", "status": "ready",
             "tasks": None, "metadata": {}})

    def test_show_json_carries_the_plan_metadata(self):
        self.write_plan(
            "feat",
            "# feat\nStatus: ready\nEpic: reporting\nTheme: reliability\n\n"
            "## Idea\nA summary.\n")
        data = self.json_out("show", "feat", "--json")
        self.assertEqual(data["metadata"],
                         {"Epic": "reporting", "Theme": "reliability"})

    # -- repeated metadata keys (`Fixes:` is repeatable) ---------------------

    def test_repeated_metadata_key_keeps_every_text_line(self):
        # `Fixes:` is explicitly repeatable (shipd-spec-format
        # plan-header-metadata), so the flagless report must print one line per
        # occurrence — collapsing the pairs into a dict would drop all but the
        # last.
        self.write_plan(
            "feat",
            "# feat\nStatus: ready\nFixes: board-theme\nFixes: board-search\n\n"
            "## Idea\nA summary.\n")
        r = self.cli("show", "feat")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(
            r.stdout,
            "feat: ready\nFixes: board-theme\nFixes: board-search\n")

    def test_repeated_metadata_key_becomes_an_array_in_json(self):
        self.write_plan(
            "feat",
            "# feat\nStatus: ready\nFixes: board-theme\nFixes: board-search\n"
            "Theme: reliability\n\n## Idea\nA summary.\n")
        data = self.json_out("show", "feat", "--json")
        # A repeated key groups into its values in file order; a key appearing
        # once stays a plain string.
        self.assertEqual(data["metadata"],
                         {"Fixes": ["board-theme", "board-search"],
                          "Theme": "reliability"})

    def test_interleaved_repeated_keys_keep_their_file_order_in_text(self):
        # The pairs are ordered, not grouped, in the data layer — so a repeated
        # key split by another key still renders in file order.
        self.write_plan(
            "feat",
            "# feat\nStatus: ready\nFixes: board-theme\nTheme: reliability\n"
            "Fixes: board-search\n\n## Idea\nA summary.\n")
        r = self.cli("show", "feat")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(
            r.stdout,
            "feat: ready\nFixes: board-theme\nTheme: reliability\n"
            "Fixes: board-search\n")
        data = self.json_out("show", "feat", "--json")
        self.assertEqual(data["metadata"]["Fixes"],
                         ["board-theme", "board-search"])

    def test_epic_report_keeps_every_metadata_line(self):
        # The epic header reuses the plan header grammar, so its metadata is
        # carried as ordered pairs too — one text line per pair, in file order.
        self.make_epic("e", status="ready",
                       metadata=["Theme: reliability",
                                 "Initiative: mvp-readiness"])
        r = self.cli("epic-show", "e")
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = r.stdout.splitlines()
        self.assertEqual(lines[1], "Theme: reliability")
        self.assertEqual(lines[2], "Initiative: mvp-readiness")
        data = self.json_out("epic-show", "e", "--json")
        self.assertEqual(data["metadata"],
                         {"Theme": "reliability",
                          "Initiative": "mvp-readiness"})

    def test_epic_report_keeps_a_repeated_metadata_key(self):
        # A key occurring twice in an epic header renders one text line per
        # occurrence (collapsing the pairs would drop the first) and groups
        # into its values in file order on the JSON path.
        self.make_epic("e", status="ready",
                       metadata=["Theme: reliability", "Theme: velocity",
                                 "Initiative: mvp-readiness"])
        r = self.cli("epic-show", "e")
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = r.stdout.splitlines()
        self.assertEqual(lines[1:4],
                         ["Theme: reliability", "Theme: velocity",
                          "Initiative: mvp-readiness"])
        data = self.json_out("epic-show", "e", "--json")
        self.assertEqual(data["metadata"],
                         {"Theme": ["reliability", "velocity"],
                          "Initiative": "mvp-readiness"})

    def test_show_text_on_a_change_is_unchanged_without_the_flag(self):
        self.make_change(
            "feat", status="active",
            tasks="## 1\n- [x] 1.1 done\n- [ ] 1.2 todo\n- [~] 1.3 wip\n")
        r = self.cli("show", "feat")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "feat: active (1/3 tasks)\n")

    # -- show, the epic fallback -------------------------------------------

    def test_show_json_epic_fallback_matches_epic_show_json(self):
        self.make_epic("reporting", status="active",
                       metadata=["Theme: reliability"],
                       rows=[("m1", "A", ("low",) * 4)])
        self.assertEqual(self.json_out("show", "reporting", "--json"),
                         self.json_out("epic-show", "reporting", "--json"))

    # -- show, the workspace report ----------------------------------------

    def test_bare_show_json_is_the_workspace_report(self):
        self.make_epic("e1", status="ready",
                       metadata=["Initiative: mvp-readiness"],
                       rows=[("m1", "A", ("low",) * 4),
                             ("m2", "B", ("low",) * 4)])
        self.make_epic("e2", status="ready",
                       metadata=["Initiative: mvp-readiness"],
                       rows=[("m3", "C", ("low",) * 4)])
        self.make_change("solo", status="active")
        data = self.json_out("show", "--json")
        self.assertEqual(data["kind"], "workspace")
        self.assertEqual(data["totals"],
                         {"specs": 3, "epics": 2, "initiatives": 1})
        self.assertEqual(data["shipped"], {"done": 0, "total": 4})
        self.assertEqual(sorted(data["lanes"]),
                         ["building", "ready", "shipped", "unplanned"])
        self.assertEqual(
            data["lanes"]["building"],
            [{"epic": "standalone", "slug": "solo", "state": "active",
              "risk": "?", "worktree": False}])
        self.assertEqual([row["slug"] for row in data["lanes"]["unplanned"]],
                         ["m1", "m2", "m3"])
        self.assertEqual([row["epic"] for row in data["lanes"]["unplanned"]],
                         ["e1", "e1", "e2"])

    def test_bare_show_json_totals_match_the_text_report(self):
        self.make_epic("e1", status="ready", rows=[("m1", "A", ("low",) * 4)])
        self.make_change("solo", status="active")
        data = self.json_out("show", "--json")
        self.assertEqual(self.report().splitlines()[0],
                         "%d specs · %d epics · %d initiatives"
                         % (data["totals"]["specs"], data["totals"]["epics"],
                            data["totals"]["initiatives"]))

    def test_bare_show_json_shipped_lane_carries_member_rows(self):
        self.make_epic("e1", status="active",
                       rows=[("m1", "A", ("low",) * 4)])
        self.make_completed("m1")
        data = self.json_out("show", "--json")
        self.assertEqual(data["shipped"], {"done": 1, "total": 1})
        self.assertEqual(
            data["lanes"]["shipped"],
            [{"epic": "e1", "slug": "m1", "state": "archived",
              "risk": "low", "worktree": False}])

    def test_bare_show_json_marks_a_worktree_hosted_row(self):
        self.make_epic("e1", status="ready", rows=[("m1", "A", ("low",) * 4)])
        self.make_worktree_change("m1", "m1", "ready")
        data = self.json_out("show", "--json")
        self.assertEqual(
            data["lanes"]["ready"],
            [{"epic": "e1", "slug": "m1", "state": "ready",
              "risk": "low", "worktree": True}])

    def test_bare_show_text_is_unchanged_without_the_flag(self):
        self.make_epic("e1", status="ready", rows=[("m1", "A", ("low",) * 4)])
        out = self.report()
        lines = out.splitlines()
        self.assertEqual(lines[0], "1 specs · 1 epics · 0 initiatives")
        self.assertEqual(lines[1], "shipped 0/1")
        self.assertEqual(lines[2], "")
        self.assertEqual(
            self.lane_headers(out),
            ["UNPLANNED (1)", "READY (0)", "BUILDING (0)", "SHIPPED (0)"])
        self.assertEqual(lines[4], "  %-20s %-22s %-12s risk %s"
                         % ("e1", "m1", "unplanned", "low"))

    # -- epic-show ----------------------------------------------------------

    def test_epic_show_json_carries_status_metadata_and_lanes(self):
        self.make_epic(
            "reporting", status="active",
            metadata=["Theme: reliability", "Initiative: mvp-readiness"],
            rows=[("csv-export", "CSV", ("low",) * 4),
                  ("pdf-export", "PDF", ("high",) * 4),
                  ("new-thing", "TBD", ("low", "low", "low", "medium"))])
        self.make_completed("csv-export")
        self.make_change("pdf-export", status="active")
        data = self.json_out("epic-show", "reporting", "--json")
        self.assertEqual(data["name"], "reporting")
        self.assertEqual(data["kind"], "epic")
        self.assertEqual(data["status"], "active")
        self.assertEqual(data["metadata"],
                         {"Theme": "reliability",
                          "Initiative": "mvp-readiness"})
        self.assertIsNone(data["worktree"])
        self.assertEqual(data["shipped"], {"done": 1, "total": 3})
        self.assertEqual(sorted(data["lanes"]),
                         ["building", "ready", "shipped", "unplanned"])
        self.assertEqual(
            data["lanes"]["shipped"],
            [{"slug": "csv-export", "state": "archived", "risk": "low",
              "worktree": False}])
        self.assertEqual(
            data["lanes"]["building"],
            [{"slug": "pdf-export", "state": "active", "risk": "high",
              "worktree": False}])
        self.assertEqual(
            data["lanes"]["unplanned"],
            [{"slug": "new-thing", "state": "unplanned", "risk": "medium",
              "worktree": False}])
        self.assertEqual(data["lanes"]["ready"], [])

    def test_epic_show_json_member_without_ratings_reports_question_mark(self):
        self.make_epic("e", status="ready", rows=[("member-a", "A", ())])
        data = self.json_out("epic-show", "e", "--json")
        self.assertEqual(data["lanes"]["unplanned"][0]["risk"], "?")

    def test_epic_show_json_names_the_hosting_worktree(self):
        self.make_worktree_epic(
            "epic-shipd-port", "shipd-port", status="active",
            rows=[("member-a", "A", ("low",) * 4)])
        data = self.json_out("epic-show", "shipd-port", "--json")
        self.assertEqual(data["worktree"], "epic-shipd-port")

    def test_epic_show_json_marks_a_worktree_derived_member(self):
        self.make_epic("e", status="ready",
                       rows=[("member-a", "A", ("low",) * 4)])
        self.make_worktree_change("member-a", "member-a", "ready")
        data = self.json_out("epic-show", "e", "--json")
        self.assertEqual(
            data["lanes"]["ready"],
            [{"slug": "member-a", "state": "ready", "risk": "low",
              "worktree": True}])

    def test_epic_show_text_is_unchanged_without_the_flag(self):
        self.make_epic("e", status="active",
                       metadata=["Theme: reliability"],
                       rows=[("member-a", "A", ("low", "low", "low", "high"))])
        r = self.cli("epic-show", "e")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(
            r.stdout,
            "e: active\nTheme: reliability\nshipped 0/1\n\n"
            "UNPLANNED (1)\n"
            "  %-22s %-12s risk %s\n"
            "READY (0)\nBUILDING (0)\nSHIPPED (0)\n"
            % ("member-a", "unplanned", "high"))

    # -- errors are unaffected by the flag ----------------------------------

    def test_status_json_on_an_unknown_name_matches_the_flagless_form(self):
        plain = self.cli("status", "no-such-thing")
        flagged = self.cli("status", "no-such-thing", "--json")
        self.assertEqual(plain.returncode, flagged.returncode)
        # A name matching nothing is a change with no plan: `?` either way.
        self.assertEqual(plain.stdout.strip(), "?")
        self.assertEqual(json.loads(flagged.stdout)["status"], "?")

    def test_a_fatal_error_still_prints_to_stderr_with_the_flag(self):
        r = self.cli("epic-show", "no-such-epic", "--json")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(r.stdout, "")
        self.assertIn("Error:", r.stderr)
        # Byte-identical to the flagless refusal.
        plain = self.cli("epic-show", "no-such-epic")
        self.assertEqual(r.stderr, plain.stderr)


class LocateJsonTest(SpecStatusTestBase):
    """``locate --json`` emits the located blocks as a JSON array (spec-status
    json-output).

    Written test-first; expected to FAIL until the flag lands in
    ``spec_status.py`` (task 1.2)."""

    def make_worktree_change(self, worktree, change, status):
        cdir = os.path.join(
            self.root, ".worktrees", worktree, ".shipd", "planned", change)
        os.makedirs(cdir)
        with open(os.path.join(cdir, "plan.md"), "w", encoding="utf-8") as fh:
            fh.write("# %s\nStatus: %s\n\n## Idea\nA summary.\n"
                     % (change, status))
        return os.path.join(self.root, ".worktrees", worktree)

    def test_locate_json_is_an_array_of_rows(self):
        self.make_change("dark-mode", status="rejected")
        r = self.cli("locate", "dark-mode", "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(
            json.loads(r.stdout),
            [{"change": "dark-mode", "root": os.path.abspath(self.root),
              "dir": os.path.join(".shipd", "planned", "dark-mode"),
              "status": "rejected"}])

    def test_locate_json_lists_root_before_worktree_matches(self):
        self.make_change("both", status="active")
        wt = self.make_worktree_change("member-a", "both", "ready")
        r = self.cli("locate", "both", "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        rows = json.loads(r.stdout)
        self.assertEqual([row["root"] for row in rows],
                         [os.path.abspath(self.root), os.path.abspath(wt)])
        self.assertEqual([row["status"] for row in rows], ["active", "ready"])

    def test_locate_text_is_unchanged_without_the_flag(self):
        self.make_change("dark-mode", status="rejected")
        r = self.cli("locate", "dark-mode")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(
            r.stdout,
            "change: dark-mode\nroot: %s\ndir: %s\nstatus: rejected\n"
            % (os.path.abspath(self.root),
               os.path.join(".shipd", "planned", "dark-mode")))

    def test_locate_json_unknown_change_still_errors(self):
        r = self.cli("locate", "no-such-change", "--json")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(r.stdout, "")
        self.assertIn("Error:", r.stderr)


class WorkspaceShowJsonTest(SpecStatusTestBase):
    """``workspace-show --json`` emits one object mirroring the text report's
    fields (spec-status json-output).

    Written test-first; expected to FAIL until the flag lands in
    ``spec_status.py`` (task 1.2)."""

    def write_brief(self, slug, status="open", project=None):
        bdir = os.path.join(self.root, ".shipd", "initiatives", slug)
        os.makedirs(bdir, exist_ok=True)
        header = ["# %s" % slug, "Status: %s" % status]
        if project is not None:
            header.append("Project: %s" % project)
        with open(os.path.join(bdir, "brief.md"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(header)
                     + "\n\nGoal prose.\n\n## Requirements\n\n- [ ] Do it\n")

    def _standard_workspace(self):
        os.makedirs(os.path.join(self.root, "present-repo"), exist_ok=True)
        self.declare_workspace({"focus": "alpha", "projects": {
            "alpha": {"repos": [
                {"path": "present-repo", "url": "git@example.com:p.git"},
                "absent-repo"]}}})
        self.write_brief("mvp-readiness", status="open", project="alpha")

    def test_workspace_show_json_mirrors_the_text_fields(self):
        self._standard_workspace()
        r = self.cli("workspace-show", "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data["workspace"], self.root)
        self.assertEqual(data["focus"], "alpha")
        self.assertEqual(data["projects"], [
            {"slug": "alpha",
             "repos": [{"path": "present-repo", "present": True,
                        "url": "git@example.com:p.git"},
                       {"path": "absent-repo", "present": False,
                        "url": None}],
             "context": False}])
        self.assertEqual(data["initiatives"], [
            {"slug": "mvp-readiness", "status": "open", "project": "alpha"}])
        self.assertTrue(data["implicit_default_project"])

    def test_workspace_show_json_focus_is_null_when_undeclared(self):
        self.declare_workspace({"projects": {}})
        r = self.cli("workspace-show", "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertIsNone(data["focus"])
        self.assertEqual(data["projects"], [])
        self.assertEqual(data["initiatives"], [])

    def test_workspace_show_text_is_unchanged_without_the_flag(self):
        self._standard_workspace()
        r = self.cli("workspace-show")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(
            r.stdout,
            "workspace: %s\nfocus: alpha\nproject alpha:\n"
            "  repo: present-repo [url]\n  repo: absent-repo (absent)\n"
            "  context: no\ninitiatives:\n"
            "  mvp-readiness: open (Project: alpha)\n"
            "(this repository falls under the implicit default project)\n"
            % self.root)

    def test_workspace_show_json_without_a_workspace_still_errors(self):
        r = self.cli("workspace-show", "--json")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(r.stdout, "")
        self.assertIn("no workspace", r.stderr.lower())


if __name__ == "__main__":
    unittest.main()
