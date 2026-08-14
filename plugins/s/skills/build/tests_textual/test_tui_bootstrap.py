#!/usr/bin/env python3
"""Tests for tui_bootstrap.py's skip-when-present path, with `textual`
actually installed.

Requires `textual` (``pip install -r requirements.txt``) — this suite lives
apart from ``plugins/s/skills/build/tests/`` (which asserts the
missing-``textual`` path via injected seams, never installing anything)
because it exercises the real "already importable" branch end to end: with
`textual` present, ``ensure_textual`` must do no venv work at all, and
importing/using ``dashboard`` must work normally.
"""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
sys.path.insert(0, SCRIPTS)

import tui_bootstrap  # noqa: E402
import dashboard  # noqa: E402


class SkipWhenTextualPresentTest(unittest.TestCase):
    def test_ensure_textual_does_no_venv_work(self):
        calls = {"venv_has_textual": 0, "run": 0, "execv": 0}

        def _venv_has_textual(_vpy):
            calls["venv_has_textual"] += 1
            return False

        def _run(_cmd):
            calls["run"] += 1
            raise AssertionError("run should not be called")

        def _execv(*_a):
            calls["execv"] += 1
            raise AssertionError("execv should not be called")

        # `has_textual` defaults to the real probe, and `textual` really is
        # importable in this suite's environment — so this exercises the
        # actual skip-when-present branch, not a faked one.
        tui_bootstrap.ensure_textual(
            ["dashboard.py", "tui"], os.path.join(SCRIPTS, "dashboard.py"),
            venv_has_textual=_venv_has_textual, run=_run, execv=_execv)

        self.assertEqual(calls, {"venv_has_textual": 0, "run": 0, "execv": 0})

    def test_dashboard_module_imports_and_runs_normally(self):
        # `import dashboard` above already proved the import succeeds; confirm
        # the module is actually usable (its App class is defined).
        self.assertTrue(hasattr(dashboard, "BoardApp"))


if __name__ == "__main__":
    unittest.main()
