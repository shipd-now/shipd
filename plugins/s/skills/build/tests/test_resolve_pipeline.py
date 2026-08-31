#!/usr/bin/env python3
"""Unit tests for spec_common.resolve_pipeline's declared-pipeline path
(shipd-config autonomous-pipeline-key, pipeline-entry-validation).

Every case here declares the ``autonomous-pipeline`` key, which is exactly the
path that validates through the stdlib-only ``pipeline_schema`` module. The
no-key default resolution lives in ``tests/test_spec_common.py``.

    python3 -m unittest discover -s plugins/s/skills/build/tests -v
"""

import contextlib
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import spec_common as sc  # noqa: E402


@contextlib.contextmanager
def home_set_to(path):
    """Override ``$HOME`` (the ``expanduser`` seam) for the duration of the
    block, so config resolution never reads the real home directory."""
    old = os.environ.get("HOME")
    os.environ["HOME"] = path
    try:
        yield
    finally:
        if old is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = old


class ResolveDeclaredPipelineTest(unittest.TestCase):
    """resolve_pipeline on a declared key: the closed entry grammar, wholesale
    semantics, canonical-order check, typed options, and provenance return.
    ``$HOME`` is always overridden to an empty directory so the real home config
    never leaks into a test."""

    def _write_config(self, d, payload):
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, sc.CONFIG_FILENAME), "w",
                  encoding="utf-8") as fh:
            json.dump(payload, fh)
        return d

    def _resolve(self, tmp, home, pipeline):
        """Write ``{"autonomous-pipeline": pipeline}`` at ``tmp`` and resolve."""
        root = os.path.realpath(tmp)
        self._write_config(root, {"autonomous-pipeline": pipeline})
        with home_set_to(os.path.realpath(home)):
            return sc.resolve_pipeline(root)

    def _config_path(self, tmp):
        return os.path.join(os.path.realpath(tmp), sc.CONFIG_FILENAME)

    # --- wholesale resolution --------------------------------------------

    def test_declared_list_is_wholesale(self):
        # A declared list with only plan/gate/build resolves to exactly those;
        # the omission of research/epic/review is not an error.
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            entries, prov = self._resolve(
                tmp, home,
                [{"stage": "plan"}, {"stage": "gate"}, {"stage": "build"}])
            self.assertEqual(
                [e["stage"] for e in entries], ["plan", "gate", "build"])
            self.assertEqual(prov, self._config_path(tmp))

    def test_explicit_gate_skip_resolves(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            entries, _prov = self._resolve(
                tmp, home,
                [{"stage": "research"}, {"stage": "gate", "skip": True},
                 {"stage": "build"}])
            gate = [e for e in entries if e["stage"] == "gate"][0]
            self.assertTrue(gate.get("skip"))

    def test_tools_binding_resolves_with_layer_provenance(self):
        # A repo layer binds a tool to plan under a workspace layer; the repo's
        # config path is the provenance and the binding survives.
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            ws = os.path.realpath(tmp)
            repo = os.path.join(ws, "repo")
            self._write_config(ws, {"dir": ".shipd"})
            self._write_config(repo, {"autonomous-pipeline": [
                {"stage": "plan",
                 "tools": [{"name": "mcp:sourcebot", "fallback": "builtin"}]}]})
            with home_set_to(os.path.realpath(home)):
                entries, prov = sc.resolve_pipeline(repo)
            self.assertEqual(entries[0]["stage"], "plan")
            self.assertEqual(
                entries[0]["tools"][0]["fallback"], "builtin")
            self.assertEqual(prov, os.path.join(repo, sc.CONFIG_FILENAME))

    def test_replace_command_fallback_skip_resolves(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            entries, _prov = self._resolve(
                tmp, home,
                [{"stage": "review",
                  "replace": {"command": "my-ci review", "fallback": "skip"}}])
            self.assertEqual(entries[0]["replace"]["command"], "my-ci review")
            self.assertEqual(entries[0]["replace"]["fallback"], "skip")

    def test_custom_entry_between_builtins_resolves_at_position(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            entries, _prov = self._resolve(
                tmp, home,
                [{"stage": "build"},
                 {"custom": "deploy-preview", "command": "deploy.sh"},
                 {"stage": "review"}])
            self.assertEqual(entries[1]["custom"], "deploy-preview")
            self.assertEqual(entries[1]["command"], "deploy.sh")
            self.assertEqual(
                [e.get("stage") for e in entries],
                ["build", None, "review"])

    def test_nearest_layer_wins_the_key_wholesale(self):
        # The repo layer's whole pipeline replaces the workspace layer's; the
        # workspace entries do not merge in.
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            ws = os.path.realpath(tmp)
            repo = os.path.join(ws, "repo")
            self._write_config(ws, {"autonomous-pipeline": [
                {"stage": "research"}, {"stage": "plan"}, {"stage": "gate"},
                {"stage": "build"}, {"stage": "review"}]})
            self._write_config(repo, {"autonomous-pipeline": [
                {"stage": "plan"}, {"stage": "build"}]})
            with home_set_to(os.path.realpath(home)):
                entries, prov = sc.resolve_pipeline(repo)
            self.assertEqual(
                [e["stage"] for e in entries], ["plan", "build"])
            self.assertEqual(prov, os.path.join(repo, sc.CONFIG_FILENAME))

    # --- typed per-stage options ------------------------------------------

    def test_declared_option_resolves_carrying_only_declared_keys(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            entries, prov = self._resolve(
                tmp, home, [{"stage": "build", "validator": False}])
            self.assertEqual(entries, [{"stage": "build", "validator": False}])
            self.assertEqual(prov, self._config_path(tmp))

    # --- validation errors ------------------------------------------------

    def _assert_error(self, tmp, home, pipeline, *needles):
        with self.assertRaises(sc.ConfigError) as cm:
            self._resolve(tmp, home, pipeline)
        msg = str(cm.exception)
        for needle in needles:
            self.assertIn(needle, msg)
        return msg

    def test_unknown_stage_errors_naming_registry(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            # names the bad stage, a registry name, and the entry index.
            self._assert_error(
                tmp, home, [{"stage": "deploy"}],
                "deploy", "research", "0")

    def test_unknown_key_errors_naming_entry_and_key(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            self._assert_error(
                tmp, home, [{"stage": "plan", "retries": 2}],
                "retries", "entry 0")

    def test_builtins_out_of_order_errors_naming_stages(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            self._assert_error(
                tmp, home, [{"stage": "build"}, {"stage": "plan"}],
                "build", "plan")

    def test_tools_missing_fallback_errors(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            self._assert_error(
                tmp, home,
                [{"stage": "plan", "tools": [{"name": "mcp:sourcebot"}]}],
                "fallback", "0")

    def test_tools_invalid_fallback_errors(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            self._assert_error(
                tmp, home,
                [{"stage": "plan",
                  "tools": [{"name": "mcp:sourcebot", "fallback": "abort"}]}],
                "fallback")

    def test_replace_missing_fallback_errors(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            self._assert_error(
                tmp, home,
                [{"stage": "review", "replace": {"command": "x"}}],
                "fallback", "0")

    def test_replace_invalid_fallback_errors(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            self._assert_error(
                tmp, home,
                [{"stage": "review",
                  "replace": {"command": "x", "fallback": "nope"}}],
                "fallback")

    def test_replace_without_command_or_tool_errors(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            self._assert_error(
                tmp, home,
                [{"stage": "review", "replace": {"fallback": "skip"}}],
                "0")

    def test_custom_non_kebab_name_errors(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            self._assert_error(
                tmp, home,
                [{"custom": "Deploy_Preview", "command": "x"}],
                "Deploy_Preview", "0")

    def test_custom_missing_command_errors(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            self._assert_error(
                tmp, home,
                [{"custom": "deploy-preview"}],
                "command", "0")

    def test_skip_combined_with_replace_errors(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            self._assert_error(
                tmp, home,
                [{"stage": "gate", "skip": True,
                  "replace": {"command": "x", "fallback": "skip"}}],
                "0")

    def test_entry_matching_no_form_errors(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            self._assert_error(tmp, home, [{"foo": "bar"}], "0")

    def test_every_offending_entry_is_reported(self):
        # Two independently bad entries each produce an error line.
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            msg = self._assert_error(
                tmp, home,
                [{"stage": "deploy"},
                 {"custom": "Bad_Name", "command": "x"}],
                "deploy", "Bad_Name")
            self.assertIn("0", msg)
            self.assertIn("1", msg)

    def test_pipeline_not_a_list_errors(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            self._assert_error(tmp, home, {"stage": "plan"}, "list")


ECO_ENTRIES = [
    {"stage": "research", "skip": True},
    {"stage": "epic", "skip": True},
    {"stage": "plan", "model": "session"},
    {"stage": "gate", "autopilot": {"attempts": 1}},
    {"stage": "build", "validator": False,
     "subagent_model": "tier-two-below", "telemetry": False},
    {"stage": "review", "model": "tier-below", "disposition": "high-only"},
]

BASIC_ENTRIES = [
    {"stage": "research", "skip": True},
    {"stage": "epic", "skip": True},
    {"stage": "plan", "model": "session"},
    {"stage": "gate", "skip": True},
    {"stage": "build", "validator": False, "subagent_model": "tier-below"},
    {"stage": "review", "model": "tier-below", "disposition": "high-only"},
]


class ResolvePresetPipelineTest(unittest.TestCase):
    """The string form of the key: a preset name expands through the shipped
    table and the same stdlib-only validation as a user-authored list
    (shipd-config pipeline-presets). The ``default`` preset's own case also
    lives in the stdlib ``tests/test_spec_common.py`` suite.
    ``$HOME`` is always overridden to an empty directory so the real home config
    never leaks into a test."""

    _write_config = ResolveDeclaredPipelineTest._write_config
    _resolve = ResolveDeclaredPipelineTest._resolve
    _config_path = ResolveDeclaredPipelineTest._config_path

    def test_eco_resolves_to_the_eco_table(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            entries, prov = self._resolve(tmp, home, "eco")
            self.assertEqual(entries, ECO_ENTRIES)
            self.assertEqual(
                prov, "preset:eco (%s)" % self._config_path(tmp))

    def test_basic_resolves_to_the_basic_table(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            entries, prov = self._resolve(tmp, home, "basic")
            self.assertEqual(entries, BASIC_ENTRIES)
            self.assertEqual(
                prov, "preset:basic (%s)" % self._config_path(tmp))

    def test_table_keys_mirror_the_stdlib_names(self):
        import pipeline_schema
        self.assertEqual(
            sorted(pipeline_schema.PRESETS), sorted(sc.PIPELINE_PRESETS))

    def test_every_preset_validates_and_resolves(self):
        # The table cannot drift from the schema: every shipped preset's entry
        # list passes entry validation and resolves through resolve_pipeline.
        import pipeline_schema
        for name in sc.PIPELINE_PRESETS:
            with self.subTest(preset=name):
                validated = pipeline_schema.validate_entries(
                    pipeline_schema.PRESETS[name])
                self.assertEqual(validated, pipeline_schema.PRESETS[name])
                with tempfile.TemporaryDirectory() as tmp, \
                        tempfile.TemporaryDirectory() as home:
                    entries, _prov = self._resolve(tmp, home, name)
                    self.assertEqual(entries, validated)


if __name__ == "__main__":
    unittest.main()
