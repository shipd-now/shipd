#!/usr/bin/env python3
"""Tests for dashboard.py's ``epic_is_runnable`` helper — the dependency-free
predicate that gates the board's per-epic run control (delivery-dashboard
board-epic-grouping spec): a run control renders only for an epic whose
status is ``ready``/``active`` and that has at least one ``unplanned``/
``ready`` member.

``dashboard.py`` top-imports ``textual`` for its App/widget classes, so a
plain ``import dashboard`` normally requires ``textual`` to be installed.
``epic_is_runnable`` is defined near the top of the file, before that
module-scope ``textual`` import, specifically so it stays usable without
``textual`` — mirroring ``change_artifacts`` (see ``test_change_artifacts.py``
for the loader this reuses). This suite MUST pass under system ``python3``
with ``textual`` NOT installed (``tests/`` never installs it; see AGENTS.md
and ``plugins/s/skills/build/tests_textual/`` for the ``textual``-dependent
rendering tests)."""

import importlib.util
import os
import sys
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
        "dashboard_stdlib_probe_runnable", DASHBOARD_PATH)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except ImportError:
        # Expected when `textual` isn't installed — the helpers defined
        # before dashboard.py's module-scope `textual` import already
        # landed in `module.__dict__`.
        pass
    return module


def _epic(status, member_states=()):
    return {
        "slug": "ep1",
        "status": status,
        "members": [{"slug": "m%d" % i, "state": state}
                    for i, state in enumerate(member_states)],
    }


class EpicIsRunnableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dashboard = _load_dashboard_stdlib()

    def test_ready_with_unplanned_member_is_runnable(self):
        epic = _epic("ready", ["unplanned"])
        self.assertTrue(self.dashboard.epic_is_runnable(epic))

    def test_active_with_ready_member_is_runnable(self):
        epic = _epic("active", ["ready"])
        self.assertTrue(self.dashboard.epic_is_runnable(epic))

    def test_ready_with_only_shipped_or_archived_members_is_not_runnable(self):
        epic = _epic("ready", ["shipped", "archived"])
        self.assertFalse(self.dashboard.epic_is_runnable(epic))

    def test_complete_epic_is_not_runnable_even_with_drivable_members(self):
        epic = _epic("complete", ["unplanned", "ready"])
        self.assertFalse(self.dashboard.epic_is_runnable(epic))

    def test_active_with_no_members_is_not_runnable(self):
        epic = _epic("active", [])
        self.assertFalse(self.dashboard.epic_is_runnable(epic))


if __name__ == "__main__":
    unittest.main()
