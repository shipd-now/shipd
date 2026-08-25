#!/usr/bin/env python3
"""Tests for the guardrail hook (guardrail-hook capability).

``guardrails.py`` is driven as the hook harness drives it: as a subprocess with
a hook payload on stdin, its stdout parsed as the hook's decision JSON.
``HOME`` is isolated and every payload's ``cwd`` points at a throwaway temp
directory, so no test picks up this checkout's — or the real user's —
``.shipd-config.json`` layers, rule files, or cooldown state.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
SCRIPT = os.path.join(SCRIPTS, "guardrails.py")
PLUGIN_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
HOOKS_JSON = os.path.join(PLUGIN_ROOT, "hooks", "hooks.json")
PLUGIN_RULES = os.path.join(PLUGIN_ROOT, "hooks", "rules")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

# Dumps the registry the hook would resolve for a start directory. Run as a
# subprocess so the isolated ``HOME`` governs the user rules source too.
REGISTRY_PROBE = (
    "import json, sys\n"
    "sys.path.insert(0, sys.argv[1])\n"
    "import guardrails\n"
    "json.dump(guardrails.resolve_rules(sys.argv[2]), sys.stdout)\n"
)


def builtin(name):
    """Return the built-in rule named ``name``, loaded from the plugin's own
    rule files (imported lazily so a missing module fails the test that needs
    it rather than the whole file)."""
    import guardrails
    for rule in guardrails.load_rules_dir(PLUGIN_RULES):
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

    def repo_rules(self, root=None, dirname=".shipd"):
        """The repo rulebook directory for ``root`` under content dir
        ``dirname``."""
        return os.path.join(root or self.root, dirname, "rules")

    def user_rules(self):
        """The user rulebook directory under the isolated ``HOME``."""
        return os.path.join(self.home, ".shipd", "rules")

    def write_rule(self, directory, name, text):
        """Write the rule file ``<name>.md`` into ``directory``, dedenting the
        literal so tests can write rule markdown inline."""
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, name + ".md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(textwrap.dedent(text).lstrip())
        return path

    def registry(self, cwd=None):
        """Return the rule registry the hook resolves for ``cwd`` — a list of
        rule dicts, or ``None`` when the hook is off there."""
        env = dict(os.environ)
        env["HOME"] = self.home
        result = subprocess.run(
            ["python3", "-c", REGISTRY_PROBE, SCRIPTS,
             cwd if cwd is not None else self.root],
            capture_output=True, text=True, cwd=self.root, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def named(self, registry, name):
        """Return the one rule named ``name`` in ``registry``."""
        matches = [rule for rule in registry if rule["name"] == name]
        self.assertEqual(
            len(matches), 1,
            "expected exactly one %r among %r"
            % (name, [rule["name"] for rule in registry]))
        return matches[0]

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

    def post(self, payload, session_id="sess-1"):
        """Return ``payload`` as the PostToolUse payload the harness sends once
        the tool has run — with ``session_id`` unless it is ``None``."""
        payload = dict(payload)
        payload["hook_event_name"] = "PostToolUse"
        if session_id is None:
            payload.pop("session_id", None)
        else:
            payload["session_id"] = session_id
        return payload

    def state_dir(self):
        """The cooldown-state directory under the isolated ``HOME``."""
        return os.path.join(self.home, ".shipd", "guardrails")

    def state_path(self, session_id="sess-1"):
        return os.path.join(self.state_dir(), session_id + ".json")

    def assertSilent(self, result):
        """Assert the hook exited 0 printing nothing."""
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "")

    def assertAllowed(self, result):
        self.assertSilent(result)

    def assertReminded(self, result):
        """Assert the hook injected a non-blocking reminder, and return its
        text."""
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.strip(), "expected a reminder on stdout")
        out = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(out["hookEventName"], "PostToolUse")
        self.assertNotIn("permissionDecision", out)
        return out["additionalContext"]

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
        self.write_rule(self.repo_rules(), "no-todo", r"""
            ---
            pattern: TODO
            files: *.py
            ---
            Do not leave TODOs.
            """)
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

    def test_the_built_ins_are_ordinary_rule_files(self):
        self.assertEqual(
            sorted(os.listdir(PLUGIN_RULES)),
            ["changelog-comment.md", "filler-placeholder.md",
             "narrating-comment.md"])

    def test_exactly_three_built_ins(self):
        import guardrails
        rules = guardrails.load_rules_dir(PLUGIN_RULES)
        self.assertEqual(
            sorted(rule["name"] for rule in rules),
            ["changelog-comment", "filler-placeholder", "narrating-comment"])
        for rule in rules:
            self.assertEqual(rule["mode"], "deny")
            self.assertTrue(rule["message"].strip())


class RulebookFormat(GuardrailCase):
    """guardrail-rulebook-format."""

    def test_a_valid_rule_file_loads(self):
        self.write_rule(self.repo_rules(), "no-console-log", r"""
            ---
            pattern: console\.log\(
            ---
            Use the logger, not console.log.
            """)
        rule = self.named(self.registry(), "no-console-log")
        self.assertEqual(rule["pattern"], r"console\.log\(")
        self.assertEqual(rule["message"], "Use the logger, not console.log.")
        self.assertEqual(rule["mode"], "deny")

    def test_a_multi_line_message_body_is_the_message(self):
        self.write_rule(self.repo_rules(), "no-console-log", r"""
            ---
            pattern: console\.log\(
            ---
            Use the logger, not console.log.

            The logger carries the request id.
            """)
        rule = self.named(self.registry(), "no-console-log")
        self.assertIn("Use the logger, not console.log.", rule["message"])
        self.assertIn("The logger carries the request id.", rule["message"])

    def test_a_remind_rule_parses_mode_and_cooldown(self):
        self.write_rule(self.repo_rules(), "prefer-pathlib", r"""
            ---
            pattern: os\.path\.join\(
            mode: remind
            cooldown: 300
            ---
            This repo prefers pathlib over os.path.
            """)
        rule = self.named(self.registry(), "prefer-pathlib")
        self.assertEqual(rule["mode"], "remind")
        self.assertEqual(rule["cooldown"], 300)

    def test_files_parses_as_a_comma_separated_glob_list(self):
        self.write_rule(self.repo_rules(), "no-console-log", r"""
            ---
            pattern: console\.log\(
            files: *.js, *.ts
            ---
            Use the logger, not console.log.
            """)
        rule = self.named(self.registry(), "no-console-log")
        self.assertEqual(rule["files"], ["*.js", "*.ts"])

    def test_an_unknown_frontmatter_key_is_ignored(self):
        self.write_rule(self.repo_rules(), "no-console-log", r"""
            ---
            pattern: console\.log\(
            severity: high
            ---
            Use the logger, not console.log.
            """)
        self.named(self.registry(), "no-console-log")

    def test_a_file_without_a_pattern_is_skipped(self):
        self.write_rule(self.repo_rules(), "patternless", """
            ---
            mode: deny
            ---
            Nothing to match on.
            """)
        self.write_rule(self.repo_rules(), "no-console-log", r"""
            ---
            pattern: console\.log\(
            ---
            Use the logger, not console.log.
            """)
        names = [rule["name"] for rule in self.registry()]
        self.assertNotIn("patternless", names)
        self.assertIn("no-console-log", names)

    def test_a_file_with_an_empty_body_is_skipped(self):
        self.write_rule(self.repo_rules(), "silent", r"""
            ---
            pattern: console\.log\(
            ---

            """)
        self.assertNotIn(
            "silent", [rule["name"] for rule in self.registry()])

    def test_an_unrecognized_mode_is_skipped(self):
        self.write_rule(self.repo_rules(), "interrupter", r"""
            ---
            pattern: console\.log\(
            mode: interrupt
            ---
            Stop the stream.
            """)
        self.assertNotIn(
            "interrupter", [rule["name"] for rule in self.registry()])


class RulebookDiscovery(GuardrailCase):
    """guardrail-rulebook-discovery."""

    CONSOLE_LOG = r"""
        ---
        pattern: console\.log\(
        ---
        Use the logger, not console.log.
        """

    def test_a_repo_rule_extends_the_registry(self):
        self.write_rule(self.repo_rules(), "no-console-log", self.CONSOLE_LOG)
        reason = self.assertDenied(self.hook(self.edit(
            "", "console.log(user)\n", file_path="app.js")))
        self.assertIn("no-console-log", reason)
        self.assertIn("Use the logger, not console.log.", reason)

    def test_a_repo_rule_overrides_a_built_in_by_name(self):
        self.write_rule(self.repo_rules(), "changelog-comment", """
            ---
            pattern: BANNED-TOKEN
            ---
            The repo's own changelog rule.
            """)
        rule = self.named(self.registry(), "changelog-comment")
        self.assertEqual(rule["pattern"], "BANNED-TOKEN")
        # The built-in's pattern is gone with it.
        self.assertAllowed(self.hook(self.edit("", "# Fixed: the pager\n")))
        reason = self.assertDenied(self.hook(self.edit(
            "", "x = BANNED-TOKEN\n")))
        self.assertIn("The repo's own changelog rule.", reason)

    def test_a_user_rule_applies_in_every_repo(self):
        self.write_rule(self.user_rules(), "no-console-log", self.CONSOLE_LOG)
        self.assertFalse(os.path.isdir(self.repo_rules()))
        reason = self.assertDenied(self.hook(self.edit(
            "", "console.log(user)\n", file_path="app.js")))
        self.assertIn("no-console-log", reason)

    def test_a_repo_rule_overrides_a_user_rule(self):
        self.write_rule(self.user_rules(), "no-console-log", self.CONSOLE_LOG)
        self.write_rule(self.repo_rules(), "no-console-log", """
            ---
            pattern: BANNED-TOKEN
            ---
            The repo's own console rule.
            """)
        rule = self.named(self.registry(), "no-console-log")
        self.assertEqual(rule["pattern"], "BANNED-TOKEN")

    def test_a_nearer_ancestor_wins(self):
        nested = os.path.join(self.root, "member")
        os.makedirs(nested)
        self.write_rule(self.repo_rules(), "no-console-log", self.CONSOLE_LOG)
        self.write_rule(self.repo_rules(root=nested), "no-console-log", """
            ---
            pattern: BANNED-TOKEN
            ---
            The member's own console rule.
            """)
        rule = self.named(self.registry(cwd=nested), "no-console-log")
        self.assertEqual(rule["pattern"], "BANNED-TOKEN")

    def test_the_content_dir_key_renames_the_rules_directory(self):
        self.write_config({"dir": "specs"})
        self.write_rule(self.repo_rules(dirname="specs"), "no-console-log",
                        self.CONSOLE_LOG)
        self.named(self.registry(), "no-console-log")

    def test_disable_drops_a_built_in_file_rule(self):
        self.write_config({"guardrails": {"disable": ["narrating-comment"]}})
        names = [rule["name"] for rule in self.registry()]
        self.assertNotIn("narrating-comment", names)
        self.assertIn("changelog-comment", names)

    def test_false_disables_every_source(self):
        self.write_rule(self.repo_rules(), "no-console-log", self.CONSOLE_LOG)
        self.write_rule(self.user_rules(), "no-todo", """
            ---
            pattern: TODO
            ---
            Do not leave TODOs.
            """)
        self.write_config({"guardrails": False})
        self.assertIsNone(self.registry())
        self.assertAllowed(self.hook(self.edit(
            "", "console.log(user)\n", file_path="app.js")))


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

    def test_a_legacy_rules_member_is_ignored(self):
        # The rulebook superseded config-declared rules; the member no longer
        # contributes, and carrying it is not an error.
        self.write_config({"guardrails": {"rules": [{
            "name": "no-console-log",
            "pattern": r"console\.log\(",
            "message": "Use the logger, not console.log.",
        }]}})
        names = [rule["name"] for rule in self.registry()]
        self.assertNotIn("no-console-log", names)
        self.assertIn("changelog-comment", names)
        self.assertAllowed(self.hook(self.edit(
            "", "console.log(user)\n", file_path="app.js")))

    def test_an_unrecognized_member_is_ignored(self):
        self.write_config({"guardrails": {"loudness": 11}})
        reason = self.assertDenied(self.hook(self.edit(
            "", "# Fixed: the pager\n")))
        self.assertIn("changelog-comment", reason)

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


class RemindOutput(GuardrailCase):
    """guardrail-remind-output."""

    REMIND_CONSOLE = r"""
        ---
        pattern: console\.log\(
        mode: remind
        ---
        Use the logger, not console.log.
        """

    def setUp(self):
        super().setUp()
        self.write_rule(self.repo_rules(), "no-console-log",
                        self.REMIND_CONSOLE)

    def logging_edit(self):
        return self.edit("", "console.log(user)\n", file_path="app.js")

    def test_a_remind_rule_injects_context_without_blocking(self):
        context = self.assertReminded(self.hook(self.post(
            self.logging_edit())))
        self.assertIn("no-console-log", context)
        self.assertIn("Use the logger, not console.log.", context)

    def test_the_same_rule_is_silent_for_the_rest_of_the_session(self):
        self.assertReminded(self.hook(self.post(self.logging_edit())))
        self.assertSilent(self.hook(self.post(self.logging_edit())))

    def test_a_different_session_fires_again(self):
        self.assertReminded(self.hook(self.post(self.logging_edit())))
        self.assertReminded(self.hook(self.post(
            self.logging_edit(), session_id="sess-2")))

    def test_a_deny_rule_is_not_evaluated_on_posttooluse(self):
        self.assertSilent(self.hook(self.post(self.edit(
            "", "// Fixed: off-by-one\n"))))

    def test_a_remind_rule_is_not_denied_on_pretooluse(self):
        self.assertAllowed(self.hook(self.logging_edit()))

    def test_a_cooldown_rule_refires_once_elapsed(self):
        self.write_rule(self.repo_rules(), "no-console-log", r"""
            ---
            pattern: console\.log\(
            mode: remind
            cooldown: 60
            ---
            Use the logger, not console.log.
            """)
        self.assertReminded(self.hook(self.post(self.logging_edit())))
        self.assertSilent(self.hook(self.post(self.logging_edit())))
        # Back-date the recorded fire rather than waiting out the cooldown.
        with open(self.state_path(), encoding="utf-8") as fh:
            state = json.load(fh)
        self.assertIn("no-console-log", state)
        state["no-console-log"] = time.time() - 120
        with open(self.state_path(), "w", encoding="utf-8") as fh:
            json.dump(state, fh)
        self.assertReminded(self.hook(self.post(self.logging_edit())))

    def test_a_payload_without_a_session_id_fires_without_recording(self):
        self.assertReminded(self.hook(self.post(
            self.logging_edit(), session_id=None)))
        self.assertFalse(os.path.isdir(self.state_dir()))
        # With nothing recorded, the next call fires again.
        self.assertReminded(self.hook(self.post(
            self.logging_edit(), session_id=None)))

    def test_an_unwritable_state_directory_still_reminds(self):
        os.makedirs(self.state_dir())
        os.chmod(self.state_dir(), 0o000)
        self.addCleanup(os.chmod, self.state_dir(), 0o755)
        self.assertReminded(self.hook(self.post(self.logging_edit())))

    def test_a_disabled_remind_rule_stays_silent(self):
        self.write_config({"guardrails": {"disable": ["no-console-log"]}})
        self.assertSilent(self.hook(self.post(self.logging_edit())))


class StatePruning(GuardrailCase):
    """guardrail-state-prune: the sweep that runs on the state write path."""

    REMIND_CONSOLE = r"""
        ---
        pattern: console\.log\(
        mode: remind
        ---
        Use the logger, not console.log.
        """

    STALE_AGE = 8 * 24 * 3600

    def setUp(self):
        super().setUp()
        self.write_rule(self.repo_rules(), "no-console-log",
                        self.REMIND_CONSOLE)

    def logging_edit(self):
        return self.edit("", "console.log(user)\n", file_path="app.js")

    def sibling(self, name, age=0):
        """Write a state-directory entry named ``name`` whose modification
        time sits ``age`` seconds in the past, and return its path."""
        os.makedirs(self.state_dir(), exist_ok=True)
        path = os.path.join(self.state_dir(), name)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"no-console-log": 1}, fh)
        stamp = time.time() - age
        os.utime(path, (stamp, stamp))
        return path

    def test_a_stale_session_file_is_pruned_on_write(self):
        stale = self.sibling("sess-old.json", age=self.STALE_AGE)
        self.assertReminded(self.hook(self.post(self.logging_edit())))
        self.assertFalse(os.path.exists(stale))
        self.assertTrue(os.path.exists(self.state_path()))

    def test_a_fresh_session_file_survives_the_sweep(self):
        fresh = self.sibling("sess-recent.json", age=60)
        self.assertReminded(self.hook(self.post(self.logging_edit())))
        self.assertTrue(os.path.exists(fresh))

    def test_a_non_json_entry_is_never_touched(self):
        other = self.sibling("sess-old.log", age=self.STALE_AGE)
        self.assertReminded(self.hook(self.post(self.logging_edit())))
        self.assertTrue(os.path.exists(other))

    def test_no_fire_means_no_sweep(self):
        stale = self.sibling("sess-old.json", age=self.STALE_AGE)
        result = self.hook(self.post(self.edit("", "total = count + 1\n")))
        self.assertSilent(result)
        self.assertTrue(os.path.exists(stale))

    def test_a_failing_sweep_does_not_disturb_the_write(self):
        import guardrails
        stale = self.sibling("sess-old.json", age=self.STALE_AGE)
        path = self.state_path()
        with mock.patch.object(guardrails.os, "remove",
                               side_effect=OSError("nope")):
            guardrails.save_state(path, {"no-console-log": time.time()})
        self.assertTrue(os.path.exists(stale))
        with open(path, encoding="utf-8") as fh:
            self.assertIn("no-console-log", json.load(fh))


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

    def test_uncompilable_rule_file_is_skipped(self):
        self.write_rule(self.repo_rules(), "broken", """
            ---
            pattern: ([unclosed
            ---
            never applies
            """)
        reason = self.assertDenied(self.hook(self.edit(
            "", "# Fixed: the pager\n")))
        self.assertIn("changelog-comment", reason)
        self.assertNotIn("broken", reason)

    def test_a_malformed_rule_file_is_skipped(self):
        self.write_rule(self.repo_rules(), "unparseable",
                        "no frontmatter here, just prose\n")
        reason = self.assertDenied(self.hook(self.edit(
            "", "# Fixed: the pager\n")))
        self.assertIn("changelog-comment", reason)
        self.assertNotIn("unparseable", reason)

    def test_an_unreadable_rules_directory_is_skipped(self):
        os.makedirs(self.repo_rules())
        os.chmod(self.repo_rules(), 0o000)
        self.addCleanup(os.chmod, self.repo_rules(), 0o755)
        reason = self.assertDenied(self.hook(self.edit(
            "", "# Fixed: the pager\n")))
        self.assertIn("changelog-comment", reason)


class HookRegistration(unittest.TestCase):
    """guardrail-hook-registration: the plugin's own hooks.json."""

    COMMAND = ('python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/'
               'guardrails.py"')

    def test_hooks_json_declares_both_events(self):
        with open(HOOKS_JSON, encoding="utf-8") as fh:
            hooks = json.load(fh)["hooks"]
        self.assertEqual(sorted(hooks), ["PostToolUse", "PreToolUse"])
        for event in ("PreToolUse", "PostToolUse"):
            self.assertEqual(len(hooks[event]), 1, event)
            entry = hooks[event][0]
            self.assertEqual(entry["matcher"], "Edit|Write", event)
            self.assertEqual(len(entry["hooks"]), 1, event)
            command = entry["hooks"][0]
            self.assertEqual(command["type"], "command", event)
            self.assertEqual(command["command"], self.COMMAND, event)


if __name__ == "__main__":
    unittest.main()
