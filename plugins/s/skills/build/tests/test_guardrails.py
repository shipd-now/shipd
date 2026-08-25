#!/usr/bin/env python3
"""Tests for the PreToolUse guardrail hook (guardrail-hook capability).

``guardrails.py`` is driven as the hook harness drives it: as a subprocess with
a PreToolUse payload on stdin, its stdout parsed as the hook's decision JSON.
``HOME`` is isolated and every payload's ``cwd`` points at a throwaway temp
directory, so no test picks up this checkout's — or the real user's —
``.shipd-config.json`` layers.
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
SCRIPT = os.path.join(SCRIPTS, "guardrails.py")
PLUGIN_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
HOOKS_JSON = os.path.join(PLUGIN_ROOT, "hooks", "hooks.json")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)


def builtin(name):
    """Return the built-in rule dict named ``name``, imported lazily so a
    missing module fails the test that needs it rather than the whole file."""
    import guardrails
    for rule in guardrails.DEFAULT_RULES:
        if rule["name"] == name:
            return rule
    raise AssertionError("no built-in rule named %r" % (name,))


class GuardrailCase(unittest.TestCase):
    """Base case: an isolated HOME and an empty config-free start directory."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.home = os.path.join(self.tmp, "home")
        self.root = os.path.join(self.tmp, "repo")
        os.makedirs(self.home)
        os.makedirs(self.root)

    def write_config(self, payload, root=None):
        path = os.path.join(root or self.root, ".shipd-config.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)
        return path

    def hook(self, payload, env_extra=None, raw=None):
        """Run the hook over ``payload`` (or ``raw`` stdin text) and return the
        completed process."""
        env = dict(os.environ)
        env["HOME"] = self.home
        env.pop("SHIPD_GUARDRAILS", None)
        env.update(env_extra or {})
        stdin = raw if raw is not None else json.dumps(payload)
        return subprocess.run(
            ["python3", SCRIPT], input=stdin, capture_output=True, text=True,
            cwd=self.root, env=env)

    def edit(self, old, new, file_path="app.py", cwd=None):
        return {
            "hook_event_name": "PreToolUse",
            "cwd": cwd if cwd is not None else self.root,
            "tool_name": "Edit",
            "tool_input": {
                "file_path": os.path.join(self.root, file_path),
                "old_string": old,
                "new_string": new,
            },
        }

    def write(self, content, file_path="app.py", cwd=None):
        return {
            "hook_event_name": "PreToolUse",
            "cwd": cwd if cwd is not None else self.root,
            "tool_name": "Write",
            "tool_input": {
                "file_path": os.path.join(self.root, file_path),
                "content": content,
            },
        }

    def assertAllowed(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "")

    def assertDenied(self, result):
        """Assert the hook denied, and return the decision reason."""
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.strip(), "expected a deny on stdout")
        payload = json.loads(result.stdout)
        out = payload["hookSpecificOutput"]
        self.assertEqual(out["hookEventName"], "PreToolUse")
        self.assertEqual(out["permissionDecision"], "deny")
        return out["permissionDecisionReason"]


class AddedLineExtraction(GuardrailCase):
    """guardrail-added-line-matching."""

    def test_line_in_both_strings_is_not_added(self):
        line = "# fixed: legacy comment"
        r = self.hook(self.edit(
            "def f():\n    pass\n" + line + "\n",
            "def f():\n    return 1\n" + line + "\n"))
        self.assertAllowed(r)

    def test_edit_flags_a_genuinely_new_line(self):
        r = self.hook(self.edit(
            "def f():\n    pass\n",
            "def f():\n    # fixed: legacy comment\n    pass\n"))
        self.assertIn("changelog-comment", self.assertDenied(r))

    def test_write_scans_the_whole_content(self):
        r = self.hook(self.write("x = 1\n# Updated: bumped the timeout\n"))
        self.assertIn("changelog-comment", self.assertDenied(r))

    def test_other_tools_pass_through(self):
        payload = self.edit("", "# fixed: nope\n")
        payload["tool_name"] = "NotebookEdit"
        self.assertAllowed(self.hook(payload))

    def test_missing_tool_name_passes_through(self):
        payload = self.edit("", "# fixed: nope\n")
        del payload["tool_name"]
        self.assertAllowed(self.hook(payload))


class DenyOutput(GuardrailCase):
    """guardrail-deny-output."""

    def test_reason_names_rule_message_and_line(self):
        line = "// Fixed: off-by-one in pager"
        reason = self.assertDenied(self.hook(self.edit("", line + "\n")))
        self.assertIn("changelog-comment", reason)
        self.assertIn(builtin("changelog-comment")["message"], reason)
        self.assertIn(line, reason)

    def test_clean_edit_passes_silently(self):
        r = self.hook(self.edit(
            "def f():\n    pass\n",
            "def f():\n    # guard against a zero page size\n    return 1\n"))
        self.assertAllowed(r)

    def test_file_glob_restricts_a_rule(self):
        self.write_config({"guardrails": {"rules": [{
            "name": "no-todo",
            "pattern": r"TODO",
            "message": "Do not leave TODOs.",
            "files": ["*.py"],
        }]}})
        self.assertAllowed(self.hook(self.edit(
            "", "TODO: later\n", file_path="notes.md")))
        reason = self.assertDenied(self.hook(self.edit(
            "", "TODO: later\n", file_path="notes.py")))
        self.assertIn("no-todo", reason)

    def test_every_violated_rule_is_reported(self):
        r = self.hook(self.write(
            "# Fixed: the pager\n# now we build the index\n"))
        reason = self.assertDenied(r)
        self.assertIn("changelog-comment", reason)
        self.assertIn("narrating-comment", reason)


class DefaultRules(GuardrailCase):
    """guardrail-default-rules."""

    def test_changelog_comment_denied_by_default(self):
        reason = self.assertDenied(self.hook(self.edit(
            "", "// Fixed: off-by-one in pager\n")))
        self.assertIn("changelog-comment", reason)

    def test_narrating_comment_denied_by_default(self):
        reason = self.assertDenied(self.hook(self.edit(
            "", "# now we build the index\n")))
        self.assertIn("narrating-comment", reason)

    def test_placeholder_comment_denied_by_default(self):
        reason = self.assertDenied(self.hook(self.write(
            "def f():\n    pass\n// ... rest of the file\n")))
        self.assertIn("filler-placeholder", reason)

    def test_exactly_three_built_ins(self):
        import guardrails
        self.assertEqual(
            [r["name"] for r in guardrails.DEFAULT_RULES],
            ["changelog-comment", "narrating-comment", "filler-placeholder"])
        for rule in guardrails.DEFAULT_RULES:
            self.assertTrue(rule["message"].strip())


class ConfigKey(GuardrailCase):
    """shipd-config guardrails-key: the resolved registry."""

    def test_false_disables_the_hook_wholly(self):
        self.write_config({"guardrails": False})
        self.assertAllowed(self.hook(self.edit("", "# Fixed: the pager\n")))

    def test_disable_drops_one_built_in(self):
        self.write_config({"guardrails": {"disable": ["narrating-comment"]}})
        self.assertAllowed(self.hook(self.edit(
            "", "# now we build the index\n")))
        reason = self.assertDenied(self.hook(self.edit(
            "", "# Fixed: the pager\n")))
        self.assertIn("changelog-comment", reason)

    def test_a_config_rule_extends_the_registry(self):
        self.write_config({"guardrails": {"rules": [{
            "name": "no-console-log",
            "pattern": r"console\.log\(",
            "message": "Use the logger, not console.log.",
        }]}})
        reason = self.assertDenied(self.hook(self.edit(
            "", "console.log(user)\n", file_path="app.js")))
        self.assertIn("no-console-log", reason)
        self.assertIn("Use the logger, not console.log.", reason)

    def test_a_same_named_config_rule_replaces_the_built_in(self):
        self.write_config({"guardrails": {"rules": [{
            "name": "changelog-comment",
            "pattern": r"BANNED-TOKEN",
            "message": "The repo's own changelog rule.",
        }]}})
        # The built-in's pattern is gone with it.
        self.assertAllowed(self.hook(self.edit("", "# Fixed: the pager\n")))
        reason = self.assertDenied(self.hook(self.edit(
            "", "x = BANNED-TOKEN\n")))
        self.assertIn("changelog-comment", reason)
        self.assertIn("The repo's own changelog rule.", reason)

    def test_a_malformed_value_is_treated_as_undeclared(self):
        self.write_config({"guardrails": "loud"})
        reason = self.assertDenied(self.hook(self.edit(
            "", "# Fixed: the pager\n")))
        self.assertIn("changelog-comment", reason)

    def test_nearest_layer_wins_the_key_wholesale(self):
        nested = os.path.join(self.root, "member")
        os.makedirs(nested)
        self.write_config({"guardrails": False})
        self.write_config({"guardrails": {"disable": ["narrating-comment"]}},
                          root=nested)
        payload = self.edit("", "# Fixed: the pager\n", cwd=nested)
        self.assertIn("changelog-comment", self.assertDenied(self.hook(payload)))

    def test_config_resolves_from_the_payload_cwd(self):
        self.write_config({"guardrails": False})
        elsewhere = os.path.join(self.tmp, "elsewhere")
        os.makedirs(elsewhere)
        payload = self.edit("", "# Fixed: the pager\n", cwd=elsewhere)
        self.assertIn("changelog-comment", self.assertDenied(self.hook(payload)))


class FailOpen(GuardrailCase):
    """guardrail-fail-open."""

    def test_garbage_stdin_passes_through(self):
        self.assertAllowed(self.hook(None, raw="not json at all"))

    def test_empty_stdin_passes_through(self):
        self.assertAllowed(self.hook(None, raw=""))

    def test_env_bypass_disables_everything(self):
        r = self.hook(self.edit("", "# Fixed: the pager\n"),
                      env_extra={"SHIPD_GUARDRAILS": "off"})
        self.assertAllowed(r)

    def test_uncompilable_config_rule_is_skipped(self):
        self.write_config({"guardrails": {"rules": [{
            "name": "broken",
            "pattern": "([unclosed",
            "message": "never applies",
        }]}})
        reason = self.assertDenied(self.hook(self.edit(
            "", "# Fixed: the pager\n")))
        self.assertIn("changelog-comment", reason)
        self.assertNotIn("broken", reason)


class HookRegistration(unittest.TestCase):
    """guardrail-hook-registration: the plugin's own hooks.json."""

    def test_hooks_json_declares_only_the_pretooluse_hook(self):
        with open(HOOKS_JSON, encoding="utf-8") as fh:
            hooks = json.load(fh)["hooks"]
        self.assertEqual(list(hooks), ["PreToolUse"])
        self.assertEqual(len(hooks["PreToolUse"]), 1)
        entry = hooks["PreToolUse"][0]
        self.assertEqual(entry["matcher"], "Edit|Write")
        self.assertEqual(len(entry["hooks"]), 1)
        command = entry["hooks"][0]
        self.assertEqual(command["type"], "command")
        self.assertEqual(
            command["command"],
            'python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/'
            'guardrails.py"')


if __name__ == "__main__":
    unittest.main()
