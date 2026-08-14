#!/usr/bin/env python3
"""Tests for tui_bootstrap.py — the delivery board's self-provisioning entry.

Stdlib only, driven entirely through injected seams: no test creates a real
virtualenv or hits the network, mirroring ``tui_bootstrap.py`` itself staying
importable without ``textual`` installed. Do not import ``dashboard`` here —
that pulls in ``textual`` at module scope.
"""

import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
sys.path.insert(0, SCRIPTS)

import tui_bootstrap as tb  # noqa: E402


class VenvDirTest(unittest.TestCase):
    def test_honors_xdg_cache_home(self):
        environ = {"XDG_CACHE_HOME": "/xdg/cache", "HOME": "/home/mikk"}
        self.assertEqual(tb.venv_dir(environ),
                         os.path.join("/xdg/cache", "shipd", "tui-venv"))

    def test_falls_back_to_home_cache(self):
        environ = {"HOME": "/home/mikk"}
        self.assertEqual(
            tb.venv_dir(environ),
            os.path.join("/home/mikk", ".cache", "shipd", "tui-venv"))


class FindRequirementsTest(unittest.TestCase):
    def test_walks_up_to_repo_root(self):
        root = tempfile.mkdtemp(prefix="tui-bootstrap-test-")
        try:
            req = os.path.join(root, "requirements.txt")
            with open(req, "w", encoding="utf-8") as fh:
                fh.write("textual>=8.2.8,<9\n")
            scripts_dir = os.path.join(
                root, "plugins", "am", "skills", "build", "scripts")
            os.makedirs(scripts_dir)
            self.assertEqual(tb.find_requirements(scripts_dir), req)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_returns_none_when_absent(self):
        root = tempfile.mkdtemp(prefix="tui-bootstrap-test-")
        try:
            scripts_dir = os.path.join(root, "scripts")
            os.makedirs(scripts_dir)
            self.assertIsNone(tb.find_requirements(scripts_dir))
        finally:
            shutil.rmtree(root, ignore_errors=True)


class FakeRun:
    """Records invocations and returns a canned (returncode) result."""

    def __init__(self, returncodes=None):
        self.calls = []
        self._returncodes = list(returncodes or [])

    def __call__(self, cmd):
        self.calls.append(cmd)
        code = self._returncodes.pop(0) if self._returncodes else 0
        return _Result(code)


class _Result:
    def __init__(self, returncode):
        self.returncode = returncode


class EnsureTextualTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="tui-bootstrap-test-")
        self.req = os.path.join(self.root, "requirements.txt")
        with open(self.req, "w", encoding="utf-8") as fh:
            fh.write("textual>=8.2.8,<9\n")
        self.scripts_dir = os.path.join(
            self.root, "plugins", "am", "skills", "build", "scripts")
        os.makedirs(self.scripts_dir)
        self.script = os.path.join(self.scripts_dir, "dashboard.py")
        self.environ = {"HOME": os.path.join(self.root, "home")}

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _ensure(self, argv, **overrides):
        kwargs = dict(
            has_textual=lambda: False,
            venv_has_textual=lambda _vpy: False,
            run=FakeRun(),
            execv=lambda *_a: self.fail("execv should not be reached"),
            out=lambda *_a: None,
            environ=self.environ,
        )
        kwargs.update(overrides)
        return tb.ensure_textual(argv, self.script, **kwargs)

    def test_noop_when_textual_importable(self):
        run = FakeRun()
        execs = []
        tb.ensure_textual(
            ["dashboard.py", "tui"], self.script,
            has_textual=lambda: True,
            venv_has_textual=lambda _vpy: self.fail("should not probe venv"),
            run=run,
            execv=lambda *a: execs.append(a),
            out=lambda *_a: None,
            environ=self.environ,
        )
        self.assertEqual(run.calls, [])
        self.assertEqual(execs, [])

    def test_existing_venv_is_reused_without_install(self):
        run = FakeRun()
        execs = []
        tb.ensure_textual(
            ["dashboard.py", "tui", "--interval", "1"], self.script,
            has_textual=lambda: False,
            venv_has_textual=lambda _vpy: True,
            run=run,
            execv=lambda *a: execs.append(a),
            out=lambda *_a: None,
            environ=self.environ,
        )
        self.assertEqual(run.calls, [])
        self.assertEqual(len(execs), 1)
        vpy, argv = execs[0]
        self.assertEqual(vpy, tb.venv_python(tb.venv_dir(self.environ)))
        self.assertEqual(argv, [vpy, self.script, "tui", "--interval", "1"])

    def test_fresh_venv_creates_installs_and_re_execs(self):
        run = FakeRun()
        execs = []
        messages = []
        tb.ensure_textual(
            ["dashboard.py", "board"], self.script,
            has_textual=lambda: False,
            venv_has_textual=lambda _vpy: False,
            run=run,
            execv=lambda *a: execs.append(a),
            out=lambda msg: messages.append(msg),
            environ=self.environ,
        )
        vdir = tb.venv_dir(self.environ)
        vpy = tb.venv_python(vdir)
        self.assertEqual(len(run.calls), 2)
        venv_cmd, install_cmd = run.calls
        self.assertIn(vdir, venv_cmd)
        self.assertEqual(install_cmd[0], vpy)
        self.assertIn("-r", install_cmd)
        self.assertIn(self.req, install_cmd)
        self.assertEqual(len(execs), 1)
        self.assertEqual(execs[0][0], vpy)
        self.assertEqual(execs[0][1], [vpy, self.script, "board"])
        self.assertTrue(any("Setting up the delivery board" in m
                            for m in messages))

    def test_failing_venv_creation_prints_hint_and_exits(self):
        run = FakeRun(returncodes=[1])
        messages = []
        with self.assertRaises(SystemExit) as ctx:
            self._ensure(["dashboard.py", "tui"], run=run,
                         out=lambda msg: messages.append(msg))
        self.assertEqual(ctx.exception.code, 1)
        self.assertEqual(len(run.calls), 1)
        self.assertTrue(any("pip install" in m for m in messages))

    def test_failing_install_prints_hint_and_exits(self):
        run = FakeRun(returncodes=[0, 1])
        messages = []
        with self.assertRaises(SystemExit) as ctx:
            self._ensure(["dashboard.py", "tui"], run=run,
                         out=lambda msg: messages.append(msg))
        self.assertEqual(ctx.exception.code, 1)
        self.assertEqual(len(run.calls), 2)
        self.assertTrue(any("pip install" in m for m in messages))

    def test_missing_requirements_prints_hint_and_exits(self):
        os.remove(self.req)
        run = FakeRun()
        messages = []
        with self.assertRaises(SystemExit) as ctx:
            self._ensure(["dashboard.py", "tui"], run=run,
                         out=lambda msg: messages.append(msg))
        self.assertEqual(ctx.exception.code, 1)
        self.assertEqual(run.calls, [])
        self.assertTrue(any("pip install" in m for m in messages))


if __name__ == "__main__":
    unittest.main()
