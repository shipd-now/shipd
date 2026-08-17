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
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
SCRIPT = os.path.join(SCRIPTS, "spec_status.py")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import pipeline_schema  # noqa: E402


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
        env["SHIPD_FLOW_LOG_DIR"] = self.flow_dir
        env.pop("AM_FLOW_LOG_DIR", None)
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

    def test_json_declared_list_carries_entries_and_config_path(self):
        # The machine contract on a declared list: `entries` are the validated
        # dicts carrying exactly the declared keys, `source` the supplying path.
        self._write_config(self.root, {"autonomous-pipeline": [
            {"stage": "plan"},
            {"stage": "gate", "skip": True},
            {"stage": "build"},
        ]})
        r = self.cli("pipeline-show", "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        payload = json.loads(r.stdout)
        self.assertEqual(
            payload["source"], os.path.join(self.root, ".shipd-config.json"))
        self.assertIn({"stage": "gate", "skip": True}, payload["entries"])

    def test_json_invalid_pipeline_errors_like_the_flagless_form(self):
        self._write_config(self.root, {"autonomous-pipeline": [
            {"stage": "deploy"},
        ]})
        flagless = self.cli("pipeline-show")
        r = self.cli("pipeline-show", "--json")
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(r.returncode, flagless.returncode)
        self.assertEqual(r.stderr, flagless.stderr)
        self.assertIn("deploy", r.stderr)      # the unknown stage
        self.assertEqual(r.stdout, "")         # no half-emitted JSON

    def test_runs_without_workspace_or_change(self):
        # A declared, valid pipeline resolves with no workspace declared and no
        # change selected.
        self._write_config(self.root, {"autonomous-pipeline": [
            {"stage": "plan"}, {"stage": "build"}]})
        r = self.cli("pipeline-show")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("plan", r.stdout)
        self.assertIn("build", r.stdout)


class PipelineShowPresetTest(unittest.TestCase):
    """`pipeline-show` on a preset-resolved pipeline: the preset provenance,
    the per-stage options suffix on each entry line, and `--expand` printing a
    preset as a fork-ready entry list (spec-status pipeline-show-verb,
    shipd-config pipeline-presets). Expanding a non-`default` preset validates
    through the schema, so these cases require pydantic. Fixture plumbing —
    isolated ``$HOME``, throwaway root, `sys.executable` CLI — is the
    declared-pipeline case's."""

    setUp = PipelineShowDeclaredTest.setUp
    tearDown = PipelineShowDeclaredTest.tearDown
    cli = PipelineShowDeclaredTest.cli
    _write_config = PipelineShowDeclaredTest._write_config

    def _lines(self, stdout):
        """Map each rendered entry line to its stage/custom name."""
        lines = {}
        for line in stdout.splitlines():
            stripped = line.strip()
            if not stripped or not stripped[0].isdigit():
                continue
            body = stripped.split(". ", 1)[1]
            lines[body.split()[0]] = body
        return lines

    def test_eco_prints_preset_provenance_and_options(self):
        self._write_config(self.root, {"autonomous-pipeline": "eco"})
        r = self.cli("pipeline-show")
        self.assertEqual(r.returncode, 0, r.stderr)
        source = r.stdout.splitlines()[0]
        self.assertIn("preset:eco", source)
        self.assertIn(os.path.join(self.root, ".shipd-config.json"), source)
        lines = self._lines(r.stdout)
        self.assertIn("skipped", lines["research"])
        self.assertIn("autopilot.attempts=1", lines["gate"])
        for pair in ("validator=false", "subagent_model=tier-two-below",
                     "telemetry=false"):
            self.assertIn(pair, lines["build"])
        for pair in ("model=tier-below", "disposition=high-only"):
            self.assertIn(pair, lines["review"])

    def test_json_eco_carries_preset_source_and_entry_options(self):
        # Machine consumers read the options off the entry dicts, never off the
        # rendered label lines.
        self._write_config(self.root, {"autonomous-pipeline": "eco"})
        r = self.cli("pipeline-show", "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        payload = json.loads(r.stdout)
        self.assertTrue(payload["source"].startswith("preset:eco"))
        self.assertIn(os.path.join(self.root, ".shipd-config.json"),
                      payload["source"])
        build = next(e for e in payload["entries"]
                     if e.get("stage") == "build")
        self.assertEqual(build["subagent_model"], "tier-two-below")
        self.assertIs(build["validator"], False)
        self.assertIs(build["telemetry"], False)

    def test_expand_eco_prints_the_forkable_entry_list(self):
        r = self.cli("pipeline-show", "--expand", "eco")
        self.assertEqual(r.returncode, 0, r.stderr)
        entries = json.loads(r.stdout)
        self.assertEqual(entries, pipeline_schema.PRESETS["eco"])
        # And the printed value is valid as a declared list.
        self.assertEqual(pipeline_schema.validate_entries(entries), entries)


if __name__ == "__main__":
    unittest.main()
