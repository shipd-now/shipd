#!/usr/bin/env python3
"""Tests for dashboard.py's ``change_artifacts`` helper — the dependency-free
locator that resolves a change's on-disk spec files for the board TUI's
spec-detail modal (delivery-dashboard board-tui spec).

``dashboard.py`` top-imports ``textual`` for its App/widget classes, so a
plain ``import dashboard`` normally requires ``textual`` to be installed.
``change_artifacts`` is defined near the top of the file, before that
module-scope ``textual`` import, specifically so it stays usable without
``textual``: :func:`_load_dashboard_stdlib` below executes the module and
swallows the ``ImportError`` its ``textual`` import raises when the package
is absent, leaving everything defined up to that point — including
``change_artifacts`` — in the module's namespace. This suite MUST pass under
system ``python3`` with ``textual`` NOT installed (``tests/`` never installs
it; see AGENTS.md and ``plugins/s/skills/build/tests_textual/`` for the
``textual``-dependent rendering tests)."""

import importlib.util
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.normpath(os.path.join(HERE, "..", "scripts"))
DASHBOARD_PATH = os.path.join(SCRIPTS_DIR, "dashboard.py")


def _load_dashboard_stdlib():
    """Execute ``dashboard.py`` far enough to capture its dependency-free,
    top-of-file helpers without requiring ``textual``. See the module
    docstring above for why this works."""
    if SCRIPTS_DIR not in sys.path:
        sys.path.insert(0, SCRIPTS_DIR)
    spec = importlib.util.spec_from_file_location(
        "dashboard_stdlib_probe", DASHBOARD_PATH)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except ImportError:
        # Expected when `textual` isn't installed — the helpers defined
        # before dashboard.py's module-scope `textual` import already
        # landed in `module.__dict__`.
        pass
    return module


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


class ChangeArtifactsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dashboard = _load_dashboard_stdlib()

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="change-artifacts-test-")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _make_change_dir(self, rel_dir, slug, *, plan=True, caps=(),
                          tasks=True, body_tag=""):
        """Populate ``<root>/.shipd/<rel_dir>/`` with the requested artifact
        files, each file's text tagged with ``body_tag`` so tests can tell
        which directory's copy was returned. ``rel_dir`` is the change's
        actual on-disk directory relative to the content dir, e.g.
        ``planned/<slug>`` or ``completed/<date>-<slug>``."""
        change_dir = os.path.join(self.root, ".shipd", rel_dir)
        if plan:
            _write(os.path.join(change_dir, "plan.md"),
                   "# %s plan %s\n" % (slug, body_tag))
        for cap in caps:
            _write(os.path.join(change_dir, "specs", cap, "spec.md"),
                   "# %s spec %s\n" % (cap, body_tag))
        if tasks:
            _write(os.path.join(change_dir, "tasks.md"),
                   "# %s tasks %s\n" % (slug, body_tag))
        return change_dir

    def test_returns_ordered_artifacts_for_planned_change(self):
        self._make_change_dir(
            "planned/widget-thing", "widget-thing",
            caps=["delivery-dashboard", "other-capability"],
            body_tag="planned")

        result = self.dashboard.change_artifacts(self.root, "widget-thing")

        labels = [entry["label"] for entry in result]
        self.assertEqual(
            labels,
            ["Plan", "Spec: delivery-dashboard", "Spec: other-capability",
             "Tasks"])
        for entry in result:
            self.assertTrue(os.path.isfile(entry["path"]))
            self.assertIn("planned", entry["text"])

    def test_single_spec_dir_labelled_just_spec(self):
        self._make_change_dir("planned/solo-cap", "solo-cap",
                               caps=["delivery-dashboard"])

        result = self.dashboard.change_artifacts(self.root, "solo-cap")

        labels = [entry["label"] for entry in result]
        self.assertEqual(labels, ["Plan", "Spec", "Tasks"])

    def test_multiple_spec_dirs_sorted_and_labelled_by_capability(self):
        self._make_change_dir(
            "planned/multi-cap", "multi-cap",
            caps=["zeta-capability", "alpha-capability"])

        result = self.dashboard.change_artifacts(self.root, "multi-cap")

        labels = [entry["label"] for entry in result]
        self.assertEqual(
            labels,
            ["Plan", "Spec: alpha-capability", "Spec: zeta-capability",
             "Tasks"])

    def test_only_existing_files_are_included(self):
        self._make_change_dir("planned/partial-change", "partial-change",
                               plan=True, caps=(), tasks=False)

        result = self.dashboard.change_artifacts(self.root, "partial-change")

        labels = [entry["label"] for entry in result]
        self.assertEqual(labels, ["Plan"])

    def test_prefers_planned_over_completed(self):
        slug = "shipped-thing"
        self._make_change_dir("completed/2026-01-01-" + slug, slug,
                               caps=["delivery-dashboard"],
                               body_tag="completed")
        self._make_change_dir("planned/" + slug, slug,
                               caps=["delivery-dashboard"], body_tag="planned")

        result = self.dashboard.change_artifacts(self.root, slug)

        for entry in result:
            self.assertIn("planned", entry["text"])
            self.assertNotIn("completed", entry["text"])

    def test_falls_back_to_newest_completed_when_not_planned(self):
        slug = "archived-thing"
        self._make_change_dir("completed/2025-01-01-" + slug, slug,
                               caps=["delivery-dashboard"], body_tag="older")
        self._make_change_dir("completed/2025-06-01-" + slug, slug,
                               caps=["delivery-dashboard"], body_tag="newer")

        result = self.dashboard.change_artifacts(self.root, slug)

        self.assertTrue(result)
        for entry in result:
            self.assertIn("newer", entry["text"])

    def test_unknown_slug_returns_empty_list(self):
        self.assertEqual(
            self.dashboard.change_artifacts(self.root, "no-such-change"), [])


class ArtifactNoticeTests(unittest.TestCase):
    """The pure ``artifact_notice(entry)`` helper the spec-detail modal shows
    while a member has no resolvable artifacts (delivery-dashboard
    modal-live-artifacts spec): it names the member's in-flight stage (and
    attempt) when its heartbeat entry carries one, and otherwise falls back to
    the idle "not yet planned" text. Kept in ``dashboard.py``'s pre-textual
    stdlib zone so it is exercised here without ``textual`` installed."""

    @classmethod
    def setUpClass(cls):
        cls.dashboard = _load_dashboard_stdlib()

    def test_stage_with_attempt_names_stage_and_attempt(self):
        self.assertEqual(
            self.dashboard.artifact_notice({"stage": "plan", "attempt": 1}),
            "plan in progress (plan#1) — spec files appear once emitted")

    def test_stage_without_attempt_names_bare_stage(self):
        self.assertEqual(
            self.dashboard.artifact_notice({"stage": "plan"}),
            "plan in progress (plan) — spec files appear once emitted")

    def test_no_stage_falls_back_to_idle_notice(self):
        self.assertEqual(
            self.dashboard.artifact_notice({"state": "ready"}),
            "not yet planned — no spec files")

    def test_empty_entry_falls_back_to_idle_notice(self):
        self.assertEqual(
            self.dashboard.artifact_notice({}),
            "not yet planned — no spec files")


class StandaloneChangesTests(unittest.TestCase):
    """The dependency-free ``standalone_changes(root, epic_member_slugs)``
    discovery helper (delivery-dashboard board-standalone-changes spec): it
    finds change directories under the root's ``planned/`` and under each
    ``.worktrees/<name>/`` whose plan carries no ``Epic:`` line and whose slug
    is in no epic's stub table, returning member-shaped dicts with a
    worktree-aware state and hosting location. Kept in ``dashboard.py``'s
    pre-textual stdlib zone so it is exercised here without ``textual``
    installed."""

    @classmethod
    def setUpClass(cls):
        cls.dashboard = _load_dashboard_stdlib()

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="standalone-changes-test-")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _plan(self, host, rel_dir, slug, *, status="active", epic=None):
        """Write ``<host>/.shipd/<rel_dir>/plan.md`` with the given status and an
        optional ``Epic:`` metadata line, plus a tasks.md so the directory is a
        plausible change."""
        header = ["# %s" % slug, "Status: %s" % status]
        if epic is not None:
            header.append("Epic: %s" % epic)
        header += ["", "## Idea", "", "body\n"]
        _write(os.path.join(host, ".shipd", rel_dir, "plan.md"),
               "\n".join(header))
        _write(os.path.join(host, ".shipd", rel_dir, "tasks.md"),
               "## 1. Tasks\n- [ ] 1.1 do it\n")

    def _by_slug(self, result):
        return {entry["slug"]: entry for entry in result}

    def test_root_planned_standalone_is_returned(self):
        self._plan(self.root, "planned/root-change", "root-change",
                   status="active")

        result = self.dashboard.standalone_changes(self.root, set())

        by_slug = self._by_slug(result)
        self.assertIn("root-change", by_slug)
        entry = by_slug["root-change"]
        self.assertEqual(entry["state"], "active")
        self.assertEqual(entry["description"], "")
        self.assertIsNone(entry["risk"])
        self.assertEqual(entry["location"], os.path.abspath(self.root))

    def test_worktree_planned_standalone_is_returned(self):
        wt = os.path.join(self.root, ".worktrees", "wt-change")
        self._plan(wt, "planned/wt-change", "wt-change", status="ready")

        result = self.dashboard.standalone_changes(self.root, set())

        by_slug = self._by_slug(result)
        self.assertIn("wt-change", by_slug)
        entry = by_slug["wt-change"]
        self.assertEqual(entry["state"], "ready")
        self.assertEqual(entry["location"], os.path.abspath(wt))

    def test_epic_member_slug_is_excluded(self):
        self._plan(self.root, "planned/adopted", "adopted", status="active")

        result = self.dashboard.standalone_changes(self.root, {"adopted"})

        self.assertNotIn("adopted", self._by_slug(result))

    def test_epic_tagged_plan_is_excluded(self):
        self._plan(self.root, "planned/tagged", "tagged", status="active",
                   epic="some-epic")

        result = self.dashboard.standalone_changes(self.root, set())

        self.assertNotIn("tagged", self._by_slug(result))

    def test_malformed_change_dir_is_skipped(self):
        # A planned dir with no plan.md is malformed: it is skipped, and a
        # well-formed sibling is still returned (no raise).
        os.makedirs(os.path.join(self.root, ".shipd", "planned", "broken"))
        self._plan(self.root, "planned/good", "good", status="active")

        result = self.dashboard.standalone_changes(self.root, set())

        by_slug = self._by_slug(result)
        self.assertIn("good", by_slug)
        self.assertNotIn("broken", by_slug)

    def test_worktree_archived_reports_archived_state(self):
        wt = os.path.join(self.root, ".worktrees", "arch-change")
        self._plan(wt, "completed/2026-01-01-arch-change", "arch-change",
                   status="verified")

        result = self.dashboard.standalone_changes(self.root, set())

        by_slug = self._by_slug(result)
        self.assertIn("arch-change", by_slug)
        entry = by_slug["arch-change"]
        self.assertEqual(entry["state"], "archived")
        self.assertEqual(entry["location"], os.path.abspath(wt))


if __name__ == "__main__":
    unittest.main()
