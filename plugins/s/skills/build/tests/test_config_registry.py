#!/usr/bin/env python3
"""Unit tests for config_registry: the key registry, the one validating
``.shipd-config.json`` writer, layer resolution, and the layered check
(shipd-config config-key-registry, config-layer-writer, config-writer-migration;
spec-status config-write-verbs, config-check-verb)."""

import ast
import glob
import json
import os
import stat
import sys
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
for _path in (SCRIPTS, HERE):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import config_registry as cr  # noqa: E402
import spec_common as sc  # noqa: E402
from test_spec_common import home_set_to  # noqa: E402

# artefacts/registry.md of the config-control change, key by key:
# (default layer, hint, owner).
ROWS = {
    "autonomous-pipeline": (
        "repo", "a preset name (basic, default, eco) or a list of stage "
        "entries", None),
    "build": ("repo", "an object of /s:build settings, e.g. "
              '{"parallelism": 3}', None),
    "clone_sources": ("workspace", "a list of directory paths", None),
    "completed_retention_days": (
        "repo", "a non-negative number of days; 0 or null disables "
        "retention", None),
    "dir": ("repo", "a relative path such as .shipd", None),
    "guardrails": ("repo", "false, or an object such as "
                   '{"disable": ["<rule>"]}', None),
    "lint": ("repo", "an object with run_scripts (true or false) and "
             "disable (a list of linter names)", None),
    "memory_dir": ("user", "an absolute path such as ~/.shipd-memory", None),
    "merge": ("repo", "an object with approvals, dismiss_stale, "
              "last_push_approval, required_checks, strict, "
              "thread_resolution", None),
    "model": ("user", "a non-empty model id", None),
    "models": ("user", "an object mapping effort levels to model ids", None),
    "post-worktree-scripts": ("repo", "a list of shell command lines",
                              "shipd worktree hooks add"),
    "pr": ("repo", "an object with title (containing {summary}) and "
           "ticket_pattern (a regular expression)", None),
    "pr-mode": ("repo", "accepted values: auto, draft", None),
    "room": ("user", "an object with agent (a non-empty string) and "
             "max_rounds (an integer of at least 1)", None),
    "statusline": ("user", 'an object such as {"lines": [["spec", '
                   '"context"]]}; segments: spec, directory, context',
                   "shipd statusline layout"),
    "store_autocommit": ("repo", "true or false", None),
    "store_root": ("repo", "a path to the external store root", None),
    "store_sync": ("repo", "true or false", None),
    "valid_themes": ("repo", "a list of theme slugs", None),
    "voice": ("user", "true or false", None),
    "wiki_base": ("user", "an absolute path to the base wiki store", None),
    "workspace": ("workspace", "an object declaring the workspace registry",
                  "shipd workspace init"),
    "workspaces_root": ("user", "an absolute path such as ~/projects", None),
    "worktree_idle_minutes": ("repo", "a non-negative number of minutes; 0 "
                              "disables the guard", None),
    "worktree_stale_days": ("repo", "a positive number of days", None),
    "worktree_sweep": ("repo", "true or false", None),
}


class _Env(unittest.TestCase):
    """A temp ``HOME`` and a temp repo directory."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        base = os.path.realpath(self._tmp.name)
        self.home = os.path.join(base, "home")
        self.repo = os.path.join(base, "repo")
        os.makedirs(self.home)
        os.makedirs(self.repo)
        cm = home_set_to(self.home)
        cm.__enter__()
        self.addCleanup(cm.__exit__, None, None, None)
        self.repo_cfg = os.path.join(self.repo, sc.CONFIG_FILENAME)
        self.user_cfg = os.path.join(self.home, sc.CONFIG_FILENAME)

    def put(self, path, data):
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
            fh.write("\n")

    def raw(self, path):
        with open(path, "rb") as fh:
            return fh.read()

    def load(self, path):
        return json.loads(self.raw(path).decode("utf-8"))


class RegistryTest(unittest.TestCase):
    def test_keys_equal_recognized_keys(self):
        self.assertEqual(set(cr.REGISTRY), set(sc.RECOGNIZED_CONFIG_KEYS))
        self.assertIn("statusline", sc.RECOGNIZED_CONFIG_KEYS)

    def test_table_rows(self):
        self.assertEqual(set(ROWS), set(cr.REGISTRY))
        for key, (layer, hint, owner) in ROWS.items():
            spec = cr.REGISTRY[key]
            self.assertEqual(spec.key, key)
            self.assertEqual(spec.layer, layer, key)
            self.assertEqual(spec.hint, hint, key)
            self.assertEqual(spec.owner, owner, key)

    def test_pr_mode_validator_matches_accessor(self):
        with tempfile.TemporaryDirectory() as tmp, \
                tempfile.TemporaryDirectory() as home:
            root = os.path.realpath(tmp)
            path = os.path.join(root, sc.CONFIG_FILENAME)
            with open(path, "w", encoding="utf-8") as fh:
                json.dump({"pr-mode": "bogus"}, fh)
            with home_set_to(os.path.realpath(home)):
                with self.assertRaises(sc.ConfigError) as ctx:
                    sc.resolve_pr_mode(root)
            findings = cr.validate_value("pr-mode", "bogus", path)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].message, str(ctx.exception))
        self.assertEqual(findings[0].key, "pr-mode")
        self.assertEqual(findings[0].level, "error")
        self.assertEqual(findings[0].hint, "accepted values: auto, draft")

    def test_valid_value_has_no_findings(self):
        self.assertEqual(cr.validate_value("pr-mode", "draft", "/x"), [])
        self.assertEqual(cr.validate_value("voice", False, "/x"), [])

    def test_boolean_is_not_an_integer(self):
        for key in ("worktree_idle_minutes", "worktree_stale_days",
                    "completed_retention_days"):
            self.assertTrue(cr.validate_value(key, True, "/x"), key)
        self.assertEqual(
            cr.validate_value("completed_retention_days", None, "/x"), [])
        self.assertTrue(cr.validate_value("worktree_stale_days", 0, "/x"))
        self.assertEqual(cr.validate_value("worktree_idle_minutes", 0, "/x"),
                         [])

    def test_statusline_rejects_repeated_segment(self):
        findings = cr.validate_value(
            "statusline", {"lines": [["spec", "spec"]]}, "/p")
        self.assertEqual(len(findings), 1)
        self.assertIn("segment 'spec' appears more than once",
                      findings[0].message)
        self.assertIn("/p", findings[0].message)

    def test_statusline_accepts_a_layout(self):
        self.assertEqual(cr.validate_value(
            "statusline", {"lines": [["spec", "context"], ["directory"]]},
            "/p"), [])
        self.assertTrue(cr.validate_value("statusline", [], "/p"))

    def test_statusline_from_config_messages(self):
        with self.assertRaises(sc.ConfigError) as ctx:
            cr.statusline_from_config([], "/p")
        self.assertEqual(
            str(ctx.exception),
            "malformed `statusline` key in /p: it is not an object")
        self.assertEqual(
            cr.statusline_from_config({"lines": [["spec"]]}, "/p"),
            [["spec"]])

    def test_structural_validators(self):
        bad = {
            "build": [], "guardrails": True, "lint": {"run_scripts": "x"},
            "post-worktree-scripts": ["", "x"], "store_root": "",
            "valid_themes": "x", "store_sync": "yes", "voice": 1,
            "workspace": [], "dir": "/abs", "model": "", "pr": 3,
            "wiki_base": "rel", "memory_dir": "rel",
            "workspaces_root": "rel", "clone_sources": "x",
        }
        for key, value in bad.items():
            self.assertTrue(cr.validate_value(key, value, "/x"), key)
        good = {
            "build": {"parallelism": 3}, "guardrails": False,
            "lint": {"disable": ["a"]},
            "post-worktree-scripts": ["make"], "store_root": "/s",
            "valid_themes": ["a"], "store_sync": True, "voice": False,
            "workspace": {}, "dir": ".shipd", "model": "m",
            "wiki_base": "/w", "workspaces_root": "/r",
            "clone_sources": ["/a"],
        }
        for key, value in good.items():
            if key in cr.REGISTRY:
                self.assertEqual(cr.validate_value(key, value, "/x"), [], key)
        self.assertEqual(cr.validate_value(
            "guardrails", {"disable": ["r"]}, "/x"), [])
        self.assertTrue(cr.validate_value(
            "guardrails", {"disable": [""]}, "/x"))

    def test_unknown_key_finding_has_did_you_mean(self):
        findings = cr.validate_value("vioce", False, "/x")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].hint, "did you mean voice?")


class WriteLayerTest(_Env):
    def test_invalid_change_writes_nothing(self):
        self.put(self.repo_cfg, {"voice": True})
        before = self.raw(self.repo_cfg)
        with self.assertRaises(cr.ConfigWriteError) as ctx:
            cr.write_layer(self.repo_cfg,
                           {"voice": True, "pr-mode": "bogus"}, self.repo)
        self.assertIsInstance(ctx.exception, sc.ConfigError)
        self.assertEqual([f.key for f in ctx.exception.findings],
                         ["pr-mode"])
        self.assertIn("pr-mode", ctx.exception.findings[0].message)
        self.assertEqual(self.raw(self.repo_cfg), before)

    def test_unrelated_invalid_key_blocks_the_write(self):
        self.put(self.user_cfg, {"pr-mode": "bogus"})
        before = self.raw(self.user_cfg)
        with self.assertRaises(cr.ConfigWriteError) as ctx:
            cr.write_layer(self.repo_cfg, {"voice": False}, self.repo)
        finding = ctx.exception.findings[0]
        self.assertEqual(finding.level, "error")
        self.assertEqual(finding.key, "pr-mode")
        self.assertEqual(
            finding.hint, "fix it with shipd config set pr-mode <value> or "
            "shipd config unset pr-mode")
        self.assertFalse(os.path.exists(self.repo_cfg))
        self.assertEqual(self.raw(self.user_cfg), before)

    def test_fixing_the_invalid_key_succeeds(self):
        self.put(self.user_cfg, {"pr-mode": "bogus"})
        warnings = cr.write_layer(self.user_cfg, {}, self.home)
        self.assertEqual(warnings, [])
        self.assertEqual(self.load(self.user_cfg), {})

    def test_unrelated_unknown_key_only_warns(self):
        self.put(self.repo_cfg, {"vioce": False})
        warnings = cr.write_layer(
            self.repo_cfg, {"vioce": False, "voice": True}, self.repo)
        self.assertEqual(self.load(self.repo_cfg),
                         {"vioce": False, "voice": True})
        self.assertEqual([w.key for w in warnings], ["vioce"])
        self.assertEqual(warnings[0].level, "warning")

    def test_changed_unknown_key_fails(self):
        with self.assertRaises(cr.ConfigWriteError) as ctx:
            cr.write_layer(self.repo_cfg, {"pr_mode": "draft"}, self.repo)
        self.assertEqual(ctx.exception.findings[0].hint,
                         "did you mean pr-mode?")
        with self.assertRaises(cr.ConfigWriteError) as ctx:
            cr.write_layer(self.repo_cfg, {"zzzzzz": 1}, self.repo)
        self.assertEqual(ctx.exception.findings[0].hint,
                         "run shipd config to see the keys in effect")

    def test_outer_write_cannot_hide_a_bad_value(self):
        self.put(self.repo_cfg, {"pr-mode": "auto"})
        before = self.raw(self.repo_cfg)
        with self.assertRaises(cr.ConfigWriteError) as ctx:
            cr.write_layer(self.user_cfg, {"pr-mode": "bogus"}, self.repo)
        self.assertEqual({f.key for f in ctx.exception.findings},
                         {"pr-mode"})
        self.assertFalse(os.path.exists(self.user_cfg))
        self.assertEqual(self.raw(self.repo_cfg), before)

    def test_outer_valid_write_shadowed_by_bad_inner_still_refused(self):
        self.put(self.repo_cfg, {"pr-mode": "bogus"})
        with self.assertRaises(cr.ConfigWriteError):
            cr.write_layer(self.user_cfg, {"voice": True}, self.repo)

    def test_comment_keys_are_skipped(self):
        cr.write_layer(self.repo_cfg, {"// note": 1, "voice": True},
                       self.repo)
        self.assertEqual(self.load(self.repo_cfg),
                         {"// note": 1, "voice": True})

    def test_format_mode_and_unchanged_keys(self):
        self.put(self.repo_cfg, {"model": "m", "voice": True})
        os.chmod(self.repo_cfg, 0o640)
        cr.write_layer(self.repo_cfg, {"model": "m", "voice": False},
                       self.repo)
        raw = self.raw(self.repo_cfg).decode("utf-8")
        self.assertTrue(raw.endswith("}\n"))
        self.assertEqual(raw, json.dumps(
            {"model": "m", "voice": False}, indent=2) + "\n")
        self.assertEqual(stat.S_IMODE(os.stat(self.repo_cfg).st_mode), 0o640)
        self.assertEqual(os.listdir(self.repo), [sc.CONFIG_FILENAME])

    def test_new_file_gets_an_ordinary_mode(self):
        cr.write_layer(self.repo_cfg, {"voice": True}, self.repo)
        mode = stat.S_IMODE(os.stat(self.repo_cfg).st_mode)
        self.assertTrue(mode & stat.S_IRGRP or mode & stat.S_IRUSR)
        self.assertTrue(mode & stat.S_IWUSR)

    def test_anchor_defaults_to_the_files_directory(self):
        self.put(self.repo_cfg, {})
        cr.write_layer(self.repo_cfg, {"voice": True})
        self.assertEqual(self.load(self.repo_cfg), {"voice": True})


class LayerPathTest(_Env):
    def setUp(self):
        super().setUp()
        subprocess.run(["git", "init", "-q", self.repo], check=True)
        self.sub = os.path.join(self.repo, "sub")
        os.makedirs(self.sub)

    def test_default_layers(self):
        self.assertEqual(cr.layer_path(self.sub, "pr-mode"), self.repo_cfg)
        self.assertEqual(cr.layer_path(self.sub, "voice"), self.user_cfg)

    def test_explicit_layer(self):
        self.assertEqual(
            cr.layer_path(self.sub, "pr-mode", "user"), self.user_cfg)
        self.assertEqual(
            cr.layer_path(self.sub, "voice", "repo"), self.repo_cfg)

    def test_winning_layer_beats_the_default(self):
        self.put(self.repo_cfg, {"voice": True})
        self.assertEqual(cr.layer_path(self.sub, "voice"), self.repo_cfg)

    def test_workspace_layer_needs_a_workspace(self):
        with self.assertRaises(sc.ConfigError) as ctx:
            cr.layer_path(self.sub, "clone_sources")
        self.assertIn("--root", str(ctx.exception))
        self.put(self.repo_cfg, {"workspace": {}})
        self.assertEqual(
            cr.layer_path(self.sub, "clone_sources"), self.repo_cfg)

    def test_repo_falls_back_outside_git(self):
        plain = os.path.join(os.path.dirname(self.repo), "plain")
        os.makedirs(plain)
        self.assertEqual(cr.layer_path(plain, "pr-mode"),
                         os.path.join(plain, sc.CONFIG_FILENAME))


class SetUnsetKeyTest(_Env):
    def test_set_writes_the_default_layer(self):
        path, warnings = cr.set_key(self.repo, "voice", False)
        self.assertEqual(path, self.user_cfg)
        self.assertEqual(warnings, [])
        self.assertEqual(self.load(self.user_cfg), {"voice": False})
        self.assertFalse(os.path.exists(self.repo_cfg))

    def test_set_refuses_a_bad_value(self):
        with self.assertRaises(cr.ConfigWriteError) as ctx:
            cr.set_key(self.repo, "pr-mode", "bogus", "repo")
        self.assertEqual(ctx.exception.findings[0].hint,
                         "accepted values: auto, draft")
        self.assertFalse(os.path.exists(self.repo_cfg))

    def test_owner_keys_are_refused(self):
        for key, owner in (("post-worktree-scripts",
                            "shipd worktree hooks add"),
                           ("statusline", "shipd statusline layout")):
            for call in (lambda k: cr.set_key(self.repo, k, ["x"]),
                         lambda k: cr.unset_key(self.repo, k)):
                with self.assertRaises(cr.ConfigWriteError) as ctx:
                    call(key)
                self.assertEqual(ctx.exception.findings[0].hint,
                                 "use " + owner)

    def test_unset_removes_only_that_key(self):
        self.put(self.repo_cfg, {"pr-mode": "draft", "voice": True})
        path, removed, _w = cr.unset_key(self.repo, "pr-mode", "repo")
        self.assertTrue(removed)
        self.assertEqual(self.load(path), {"voice": True})

    def test_unset_of_an_undeclared_key_writes_nothing(self):
        path, removed, warnings = cr.unset_key(self.repo, "voice", "repo")
        self.assertFalse(removed)
        self.assertEqual(warnings, [])
        self.assertFalse(os.path.exists(path))

    def test_unset_can_remove_an_unknown_key(self):
        self.put(self.repo_cfg, {"vioce": False, "voice": True})
        _p, removed, _w = cr.unset_key(self.repo, "vioce", "repo")
        self.assertTrue(removed)
        self.assertEqual(self.load(self.repo_cfg), {"voice": True})


class CheckTest(_Env):
    def test_clean_config(self):
        self.put(self.repo_cfg, {"// note": 1, "pr-mode": "draft"})
        self.assertEqual(cr.check(self.repo), ([], []))

    def test_errors_and_warnings_across_layers(self):
        self.put(self.repo_cfg, {"pr-mode": "always", "vioce": False})
        self.put(self.user_cfg, {"voice": "yes"})
        errors, warnings = cr.check(self.repo)
        self.assertEqual([(e.key, e.path) for e in errors],
                         [("pr-mode", self.repo_cfg),
                          ("voice", self.user_cfg)])
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0].key, "vioce")
        self.assertEqual(warnings[0].hint, "did you mean voice?")
        self.assertEqual(warnings[0].message, "unknown key vioce")

    def test_shadowed_bad_value_is_still_reported(self):
        self.put(self.repo_cfg, {"pr-mode": "draft"})
        self.put(self.user_cfg, {"pr-mode": "bogus"})
        errors, _w = cr.check(self.repo)
        self.assertEqual([e.path for e in errors], [self.user_cfg])

    def test_malformed_file_is_one_error_naming_it(self):
        with open(self.repo_cfg, "w", encoding="utf-8") as fh:
            fh.write("{nope")
        errors, warnings = cr.check(self.repo)
        self.assertEqual(warnings, [])
        self.assertEqual(len(errors), 1)
        self.assertIn(self.repo_cfg, errors[0].message)


CONFIG_NAMES = ("CONFIG_FILENAME", "cfg_path", "_config_path")
BIN_SHIPD = os.path.normpath(os.path.join(HERE, "..", "..", "..", "bin",
                                          "shipd"))


def _write_open_calls(func):
    """The ``open(..., <write mode>)`` calls inside the function node."""
    found = []
    for node in ast.walk(func):
        if not (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "open"):
            continue
        modes = [a for a in node.args[1:2]] + [
            kw.value for kw in node.keywords if kw.arg == "mode"]
        for mode in modes:
            if isinstance(mode, ast.Constant) and isinstance(mode.value, str) \
                    and "w" in mode.value:
                found.append(node)
    return found


def _mentions_config_path(func):
    for node in ast.walk(func):
        if isinstance(node, ast.Name) and node.id in CONFIG_NAMES:
            return True
        if isinstance(node, ast.Attribute) and node.attr in CONFIG_NAMES:
            return True
    return False


class NoStrayWriterTest(unittest.TestCase):
    """config-writer-migration: No stray writer remains."""

    def test_only_the_registry_opens_a_config_path_for_writing(self):
        offenders = []
        for path in sorted(glob.glob(os.path.join(SCRIPTS, "*.py"))):
            with open(path, encoding="utf-8") as fh:
                tree = ast.parse(fh.read(), path)
            for func in ast.walk(tree):
                if not isinstance(func, (ast.FunctionDef,
                                         ast.AsyncFunctionDef)):
                    continue
                if _mentions_config_path(func) and _write_open_calls(func):
                    if os.path.basename(path) != "config_registry.py":
                        offenders.append("%s:%s" % (
                            os.path.basename(path), func.name))
        self.assertEqual(offenders, [])

    def test_atomic_write_is_the_registrys_only_writer(self):
        with open(os.path.join(SCRIPTS, "config_registry.py"),
                  encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        writers = [f.name for f in ast.walk(tree)
                   if isinstance(f, ast.FunctionDef)
                   and (_write_open_calls(f) or any(
                       isinstance(n, ast.Attribute) and n.attr == "fdopen"
                       for n in ast.walk(f)))]
        self.assertEqual(writers, ["_atomic_write"])

    def test_statusline_save_no_longer_writes_settings_directly(self):
        with open(BIN_SHIPD, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        save = [f for f in ast.walk(tree)
                if isinstance(f, ast.FunctionDef)
                and f.name == "_save_statusline_layout"]
        self.assertEqual(len(save), 1)
        called = {n.func.id for n in ast.walk(save[0])
                  if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        self.assertNotIn("_write_settings", called)
        self.assertIn("write_layer", ast.dump(save[0]))


if __name__ == "__main__":
    unittest.main()
