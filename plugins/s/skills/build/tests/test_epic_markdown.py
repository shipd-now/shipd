#!/usr/bin/env python3
"""Tests for dashboard.py's ``epic_markdown`` helper — the dependency-free
reader that resolves an epic's ``epics/<slug>/epic.md`` text for the board's
epic-detail modal (delivery-dashboard board-epic-grouping spec).

``dashboard.py`` top-imports ``textual`` for its App/widget classes, so a
plain ``import dashboard`` normally requires ``textual`` to be installed.
``epic_markdown`` is defined near the top of the file, before that
module-scope ``textual`` import, specifically so it stays usable without
``textual`` — mirroring ``change_artifacts``/``epic_is_runnable`` (see
``test_change_artifacts.py`` for the loader this reuses). This suite MUST
pass under system ``python3`` with ``textual`` NOT installed (``tests/``
never installs it; see AGENTS.md and
``plugins/s/skills/build/tests_textual/`` for the ``textual``-dependent
rendering tests)."""

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
        "dashboard_stdlib_probe_epic_markdown", DASHBOARD_PATH)
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


class EpicMarkdownTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dashboard = _load_dashboard_stdlib()

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="epic-markdown-test-")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_returns_epic_md_text_for_existing_epic(self):
        text = "# widget-epic\nStatus: active\n\n## Changes\n"
        _write(os.path.join(self.root, ".shipd", "epics", "widget-epic",
                            "epic.md"), text)

        result = self.dashboard.epic_markdown(self.root, "widget-epic")

        self.assertEqual(result, text)

    def test_returns_none_for_unknown_slug(self):
        self.assertIsNone(
            self.dashboard.epic_markdown(self.root, "no-such-epic"))


if __name__ == "__main__":
    unittest.main()
