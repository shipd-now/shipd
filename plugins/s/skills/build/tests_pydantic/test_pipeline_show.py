#!/usr/bin/env python3
"""Unit tests for `spec_status.py pipeline-show` on a declared pipeline
(spec-status pipeline-show-verb, shipd-config pipeline-entry-validation).

Rendering a *declared* pipeline resolves it, which validates through the
pydantic ``pipeline_schema`` models — so these cases require pydantic and live
here rather than in the stdlib-only ``tests/`` suite. The no-key `[default]`
rendering stays in ``tests/test_spec_status.py``, which must keep passing with
pydantic absent. The CLI is driven with ``sys.executable`` so the subprocess
inherits this suite's interpreter (and therefore its pydantic).

    python3 -m unittest discover -s plugins/s/skills/build/tests_pydantic -v
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.normpath(
    os.path.join(HERE, "..", "scripts", "spec_status.py"))


class PipelineShowDeclaredTest(unittest.TestCase):
    """`pipeline-show` prints one line per resolved entry (form + bindings with
    fallbacks) plus the provenance of the key; invalid pipelines print every
    validation error and exit non-zero. The verb requires neither a workspace
    nor a selected change. ``$HOME`` is isolated so the real home config never
    leaks in, and flow capture is redirected to a throwaway directory."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="pipeline-show-root-")
        self.home = tempfile.mkdtemp(prefix="pipeline-show-home-")
        self.flow_dir = tempfile.mkdtemp(prefix="pipeline-show-flow-")

    def tearDown(self):
        for d in (self.flow_dir, self.home, self.root):
            shutil.rmtree(d, ignore_errors=True)

    def cli(self, *args):
        env = dict(os.environ)
        env["HOME"] = self.home
        env["AM_FLOW_LOG_DIR"] = self.flow_dir
        return subprocess.run(
            [sys.executable, SCRIPT, "--root", self.root, *args],
            capture_output=True, text=True, env=env)

    def _write_config(self, d, payload):
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, ".shipd-config.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(payload, fh)

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


if __name__ == "__main__":
    unittest.main()
