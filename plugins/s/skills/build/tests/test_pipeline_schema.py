#!/usr/bin/env python3
"""Unit tests for pipeline_schema: the stdlib-only entry validator behind
declared-pipeline validation (shipd-config pipeline-stage-options,
pipeline-entry-validation).

    python3 -m unittest discover -s plugins/s/skills/build/tests -v
"""

import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import pipeline_schema as ps  # noqa: E402


class ValidateEntriesFormsTest(unittest.TestCase):
    """Every entry form of the closed grammar parses and round-trips."""

    def test_bare_stage_entries_parse(self):
        raw = [{"stage": "research"}, {"stage": "epic"}, {"stage": "plan"},
               {"stage": "gate"}, {"stage": "build"}, {"stage": "review"}]
        self.assertEqual(ps.validate_entries(raw), raw)

    def test_skip_form_parses(self):
        self.assertEqual(
            ps.validate_entries([{"stage": "gate", "skip": True}]),
            [{"stage": "gate", "skip": True}])

    def test_tools_form_parses(self):
        entry = {"stage": "plan",
                 "tools": [{"name": "mcp:sourcebot", "fallback": "builtin"}]}
        self.assertEqual(ps.validate_entries([entry]), [entry])

    def test_replace_form_parses_with_command(self):
        entry = {"stage": "review",
                 "replace": {"command": "my-ci review", "fallback": "skip"}}
        self.assertEqual(ps.validate_entries([entry]), [entry])

    def test_replace_form_parses_with_tool_only(self):
        entry = {"stage": "review",
                 "replace": {"tool": "mcp:reviewer", "fallback": "builtin"}}
        self.assertEqual(ps.validate_entries([entry]), [entry])

    def test_custom_form_parses(self):
        entry = {"custom": "deploy-preview", "command": "deploy.sh"}
        self.assertEqual(ps.validate_entries([entry]), [entry])

    def test_empty_list_yields_empty_list(self):
        self.assertEqual(ps.validate_entries([]), [])


class ExcludeUnsetTest(unittest.TestCase):
    """Schema defaults are declared, never injected into resolved entries."""

    def test_bare_build_entry_round_trips_exactly(self):
        self.assertEqual(
            ps.validate_entries([{"stage": "build"}]), [{"stage": "build"}])

    def test_declared_options_are_carried_verbatim(self):
        entry = {"stage": "build", "validator": False, "telemetry": False,
                 "parallelism": 2, "subagent_model": "tier-two-below"}
        self.assertEqual(ps.validate_entries([entry]), [entry])

    def test_undeclared_autopilot_keys_are_not_injected(self):
        entry = {"stage": "plan", "autopilot": {"attempts": 5}}
        self.assertEqual(ps.validate_entries([entry]), [entry])

    def test_declared_false_skip_free_options_survive(self):
        # `validator: false` must not be dropped as "falsy"; exclude_unset keys
        # on what was declared, not on truthiness.
        out = ps.validate_entries([{"stage": "build", "validator": False}])
        self.assertEqual(out, [{"stage": "build", "validator": False}])


class TierTest(unittest.TestCase):
    """`model` / `subagent_model`: an open non-empty string, with the symbolic
    tiers exported as a documented constant."""

    def test_symbolic_tiers_constant(self):
        self.assertEqual(
            ps.SYMBOLIC_TIERS, ("session", "tier-below", "tier-two-below"))

    def test_each_symbolic_tier_is_accepted(self):
        for tier in ps.SYMBOLIC_TIERS:
            with self.subTest(tier=tier):
                self.assertEqual(
                    ps.validate_entries([{"stage": "plan", "model": tier}]),
                    [{"stage": "plan", "model": tier}])

    def test_concrete_model_id_is_accepted(self):
        entry = {"stage": "plan", "model": "claude-opus-4-5-20251101"}
        self.assertEqual(ps.validate_entries([entry]), [entry])

    def test_empty_tier_is_rejected(self):
        with self.assertRaises(ValueError) as cm:
            ps.validate_entries([{"stage": "plan", "model": ""}])
        self.assertIn("entry 0 (", str(cm.exception))
        self.assertIn("model", str(cm.exception))

    def test_non_string_tier_is_rejected(self):
        with self.assertRaises(ValueError) as cm:
            ps.validate_entries([{"stage": "build", "subagent_model": 3}])
        self.assertIn("subagent_model", str(cm.exception))


class StageOptionsTest(unittest.TestCase):
    """Per-stage typed options: build extras and review disposition."""

    def test_model_option_rides_every_stage(self):
        for stage in ("research", "epic", "plan", "gate", "build", "review"):
            with self.subTest(stage=stage):
                entry = {"stage": stage, "model": "tier-below"}
                self.assertEqual(ps.validate_entries([entry]), [entry])

    def test_build_options_are_accepted(self):
        entry = {"stage": "build", "validator": True, "telemetry": True,
                 "parallelism": 4, "subagent_model": "session"}
        self.assertEqual(ps.validate_entries([entry]), [entry])

    def test_parallelism_below_one_is_rejected(self):
        with self.assertRaises(ValueError) as cm:
            ps.validate_entries([{"stage": "build", "parallelism": 0}])
        self.assertIn("parallelism", str(cm.exception))

    def test_build_options_on_another_stage_are_rejected(self):
        with self.assertRaises(ValueError) as cm:
            ps.validate_entries([{"stage": "plan", "validator": False}])
        self.assertIn("validator", str(cm.exception))

    def test_each_disposition_value_is_accepted(self):
        for value in ("all", "high-only", "none"):
            with self.subTest(disposition=value):
                entry = {"stage": "review", "disposition": value}
                self.assertEqual(ps.validate_entries([entry]), [entry])

    def test_disposition_outside_the_closed_set_is_rejected(self):
        with self.assertRaises(ValueError) as cm:
            ps.validate_entries(
                [{"stage": "review", "disposition": "medium-up"}])
        msg = str(cm.exception)
        self.assertIn("entry 0 (", msg)
        self.assertIn("disposition", msg)
        self.assertIn("medium-up", msg)

    def test_disposition_on_another_stage_is_rejected(self):
        with self.assertRaises(ValueError) as cm:
            ps.validate_entries([{"stage": "build", "disposition": "none"}])
        self.assertIn("disposition", str(cm.exception))


class AutopilotOptsTest(unittest.TestCase):
    """The `autopilot`-namespaced driver knobs and their bounds."""

    def test_defaults_are_schema_declared(self):
        opts = ps.AutopilotOpts()
        self.assertEqual(opts.attempts, 3)
        self.assertIsNone(opts.timeout)
        self.assertIsNone(opts.max_resumes)

    def test_full_options_are_accepted(self):
        entry = {"stage": "build",
                 "autopilot": {"attempts": 2, "timeout": 900,
                               "max_resumes": 0}}
        self.assertEqual(ps.validate_entries([entry]), [entry])

    def test_custom_entry_may_carry_autopilot(self):
        entry = {"custom": "deploy-preview", "command": "deploy.sh",
                 "autopilot": {"attempts": 1}}
        self.assertEqual(ps.validate_entries([entry]), [entry])

    def test_attempts_below_one_is_rejected(self):
        with self.assertRaises(ValueError) as cm:
            ps.validate_entries([{"stage": "build",
                                  "autopilot": {"attempts": 0}}])
        msg = str(cm.exception)
        self.assertIn("entry 0 (", msg)
        self.assertIn("attempts", msg)

    def test_timeout_must_be_positive(self):
        with self.assertRaises(ValueError) as cm:
            ps.validate_entries([{"stage": "build",
                                  "autopilot": {"timeout": 0}}])
        self.assertIn("timeout", str(cm.exception))

    def test_max_resumes_must_not_be_negative(self):
        with self.assertRaises(ValueError) as cm:
            ps.validate_entries([{"stage": "build",
                                  "autopilot": {"max_resumes": -1}}])
        self.assertIn("max_resumes", str(cm.exception))

    def test_unknown_autopilot_key_is_rejected(self):
        with self.assertRaises(ValueError) as cm:
            ps.validate_entries([{"stage": "build",
                                  "autopilot": {"attempts": 2, "nope": 1}}])
        self.assertIn("nope", str(cm.exception))


class UnknownKeyTest(unittest.TestCase):
    """`extra="forbid"` on every form."""

    def test_unknown_key_on_a_stage_entry(self):
        with self.assertRaises(ValueError) as cm:
            ps.validate_entries([{"stage": "plan", "retries": 2}])
        msg = str(cm.exception)
        self.assertIn("entry 0 (", msg)
        self.assertIn("retries", msg)

    def test_unknown_key_on_a_tools_item(self):
        with self.assertRaises(ValueError) as cm:
            ps.validate_entries([{"stage": "plan", "tools": [
                {"name": "mcp:sourcebot", "fallback": "builtin",
                 "weight": 1}]}])
        self.assertIn("weight", str(cm.exception))

    def test_unknown_key_on_a_replace_object(self):
        with self.assertRaises(ValueError) as cm:
            ps.validate_entries([{"stage": "review", "replace": {
                "command": "x", "fallback": "skip", "when": "always"}}])
        self.assertIn("when", str(cm.exception))

    def test_unknown_key_on_a_custom_entry(self):
        with self.assertRaises(ValueError) as cm:
            ps.validate_entries([{"custom": "deploy-preview",
                                  "command": "x", "shell": True}])
        self.assertIn("shell", str(cm.exception))


class ExclusivityTest(unittest.TestCase):
    """skip / tools / replace exclusivity, including the tightened skip rule."""

    def test_skip_with_an_option_is_rejected(self):
        with self.assertRaises(ValueError) as cm:
            ps.validate_entries([{"stage": "review", "skip": True,
                                  "model": "tier-below"}])
        msg = str(cm.exception)
        self.assertIn("entry 0 (", msg)
        self.assertIn("skip", msg)

    def test_skip_with_replace_is_rejected(self):
        with self.assertRaises(ValueError) as cm:
            ps.validate_entries([{"stage": "gate", "skip": True,
                                  "replace": {"command": "x",
                                              "fallback": "skip"}}])
        self.assertIn("skip", str(cm.exception))

    def test_skip_with_tools_is_rejected(self):
        with self.assertRaises(ValueError) as cm:
            ps.validate_entries([{"stage": "gate", "skip": True, "tools": [
                {"name": "mcp:sourcebot", "fallback": "builtin"}]}])
        self.assertIn("skip", str(cm.exception))

    def test_skip_false_is_rejected(self):
        with self.assertRaises(ValueError) as cm:
            ps.validate_entries([{"stage": "gate", "skip": False}])
        self.assertIn("skip", str(cm.exception))

    def test_tools_and_replace_together_are_rejected(self):
        with self.assertRaises(ValueError) as cm:
            ps.validate_entries([{"stage": "plan",
                                  "tools": [{"name": "t",
                                             "fallback": "skip"}],
                                  "replace": {"command": "x",
                                              "fallback": "skip"}}])
        msg = str(cm.exception)
        self.assertIn("tools", msg)
        self.assertIn("replace", msg)

    def test_options_combine_freely_with_tools(self):
        entry = {"stage": "plan", "model": "tier-below",
                 "tools": [{"name": "mcp:sourcebot", "fallback": "builtin"}],
                 "autopilot": {"attempts": 2}}
        self.assertEqual(ps.validate_entries([entry]), [entry])

    def test_options_combine_freely_with_replace(self):
        entry = {"stage": "build", "validator": False,
                 "replace": {"command": "my-build", "fallback": "skip"}}
        self.assertEqual(ps.validate_entries([entry]), [entry])


class StrictTypeTest(unittest.TestCase):
    """Strict mode: a wrongly typed option value is rejected, never coerced.
    JSON already distinguishes `true` from `1` and from `"true"`, so a config
    that writes the wrong one is a mistake worth naming — and the hand-rolled
    validator this schema replaces rejected `skip: 1` too."""

    def _assert_rejected(self, entry, field):
        with self.assertRaises(ValueError) as cm:
            ps.validate_entries([entry])
        msg = str(cm.exception)
        self.assertIn("entry 0 (", msg)
        self.assertIn(field, msg)
        return msg

    def test_skip_as_integer_one_is_rejected(self):
        self._assert_rejected({"stage": "gate", "skip": 1}, "skip")

    def test_skip_as_string_is_rejected(self):
        self._assert_rejected({"stage": "gate", "skip": "true"}, "skip")

    def test_boolean_option_as_string_is_rejected(self):
        self._assert_rejected(
            {"stage": "build", "validator": "false"}, "validator")

    def test_integer_option_as_string_is_rejected(self):
        self._assert_rejected(
            {"stage": "build", "parallelism": "2"}, "parallelism")

    def test_autopilot_integer_as_string_is_rejected(self):
        self._assert_rejected(
            {"stage": "build", "autopilot": {"attempts": "3"}}, "attempts")

    def test_integer_option_as_float_is_rejected(self):
        self._assert_rejected(
            {"stage": "build", "parallelism": 2.0}, "parallelism")

    def test_correctly_typed_values_still_parse(self):
        # The tightening must not touch well-typed config, including nested
        # objects, which stay plain dicts.
        entry = {"stage": "build", "skip": True}
        self.assertEqual(ps.validate_entries([entry]), [entry])
        entry = {"stage": "build", "validator": False, "parallelism": 2,
                 "autopilot": {"attempts": 3},
                 "tools": [{"name": "mcp:sourcebot", "fallback": "builtin"}]}
        self.assertEqual(ps.validate_entries([entry]), [entry])


class GrammarErrorTest(unittest.TestCase):
    """The remaining closed-grammar rejections carried over from the
    hand-rolled validator."""

    def test_unknown_stage_names_the_registry(self):
        with self.assertRaises(ValueError) as cm:
            ps.validate_entries([{"stage": "deploy"}])
        msg = str(cm.exception)
        self.assertIn("entry 0 (", msg)
        self.assertIn("deploy", msg)
        self.assertIn("research", msg)

    def test_entry_matching_no_form_is_rejected(self):
        with self.assertRaises(ValueError) as cm:
            ps.validate_entries([{"foo": "bar"}])
        self.assertIn("entry 0 (", str(cm.exception))

    def test_non_object_entry_is_rejected(self):
        with self.assertRaises(ValueError) as cm:
            ps.validate_entries(["plan"])
        self.assertIn("entry 0 (", str(cm.exception))

    def test_stage_and_custom_together_are_rejected(self):
        with self.assertRaises(ValueError) as cm:
            ps.validate_entries(
                [{"stage": "plan", "custom": "x", "command": "y"}])
        self.assertIn("entry 0 (", str(cm.exception))

    def test_tools_missing_fallback_is_rejected(self):
        with self.assertRaises(ValueError) as cm:
            ps.validate_entries(
                [{"stage": "plan", "tools": [{"name": "mcp:sourcebot"}]}])
        self.assertIn("fallback", str(cm.exception))

    def test_tools_invalid_fallback_is_rejected(self):
        with self.assertRaises(ValueError) as cm:
            ps.validate_entries([{"stage": "plan", "tools": [
                {"name": "mcp:sourcebot", "fallback": "abort"}]}])
        self.assertIn("fallback", str(cm.exception))

    def test_tools_item_needs_a_non_empty_name(self):
        with self.assertRaises(ValueError) as cm:
            ps.validate_entries([{"stage": "plan", "tools": [
                {"name": "", "fallback": "builtin"}]}])
        self.assertIn("name", str(cm.exception))

    def test_empty_tools_list_is_rejected(self):
        with self.assertRaises(ValueError) as cm:
            ps.validate_entries([{"stage": "plan", "tools": []}])
        self.assertIn("tools", str(cm.exception))

    def test_replace_missing_fallback_is_rejected(self):
        with self.assertRaises(ValueError) as cm:
            ps.validate_entries(
                [{"stage": "review", "replace": {"command": "x"}}])
        self.assertIn("fallback", str(cm.exception))

    def test_replace_without_command_or_tool_is_rejected(self):
        with self.assertRaises(ValueError) as cm:
            ps.validate_entries(
                [{"stage": "review", "replace": {"fallback": "skip"}}])
        self.assertIn("entry 0 (", str(cm.exception))

    def test_custom_non_kebab_name_is_rejected(self):
        with self.assertRaises(ValueError) as cm:
            ps.validate_entries([{"custom": "Deploy_Preview", "command": "x"}])
        msg = str(cm.exception)
        self.assertIn("entry 0 (", msg)
        self.assertIn("Deploy_Preview", msg)

    def test_custom_missing_command_is_rejected(self):
        with self.assertRaises(ValueError) as cm:
            ps.validate_entries([{"custom": "deploy-preview"}])
        self.assertIn("command", str(cm.exception))

    def test_custom_empty_command_is_rejected(self):
        with self.assertRaises(ValueError) as cm:
            ps.validate_entries([{"custom": "deploy-preview", "command": ""}])
        self.assertIn("command", str(cm.exception))


class ErrorRenderingTest(unittest.TestCase):
    """Errors are rendered as ``entry <i> (<compact-sorted-json>): ...`` lines,
    one per validation error, collected across every offending entry."""

    def test_line_carries_index_and_sorted_entry_json(self):
        entry = {"stage": "plan", "retries": 2}
        with self.assertRaises(ValueError) as cm:
            ps.validate_entries([entry])
        prefix = "entry 0 (%s):" % json.dumps(entry, sort_keys=True)
        self.assertIn(prefix, str(cm.exception))

    def test_every_offending_entry_is_reported(self):
        with self.assertRaises(ValueError) as cm:
            ps.validate_entries([{"stage": "deploy"},
                                 {"stage": "plan"},
                                 {"custom": "Bad_Name", "command": "x"}])
        msg = str(cm.exception)
        self.assertIn("entry 0 (", msg)
        self.assertIn("entry 2 (", msg)
        self.assertNotIn("entry 1 (", msg)
        self.assertIn("deploy", msg)
        self.assertIn("Bad_Name", msg)

    def test_error_lines_name_the_offending_field(self):
        with self.assertRaises(ValueError) as cm:
            ps.validate_entries([{"stage": "build", "parallelism": 0,
                                  "telemetry": "maybe"}])
        msg = str(cm.exception)
        self.assertIn("parallelism", msg)
        self.assertIn("telemetry", msg)
        # One rendered line per validation error.
        self.assertEqual(len(msg.splitlines()), 2)


if __name__ == "__main__":
    unittest.main()
