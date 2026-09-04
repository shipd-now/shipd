#!/usr/bin/env python3
"""Tests for worktree.py: the engine's worktree front door.

The script is driven as a black box via subprocess against a throwaway temp
git repository (git init + one commit) used as cwd — never against the real
repo — mirroring ``test_worktree.py``'s fixture style. ``$HOME`` is isolated
so the layered config search can never reach the developer's own
``~/.shipd-config.json``.

Covers the create path that wraps ``worktree.sh``'s git mechanics and then
runs the configured ``post-worktree-scripts`` (worktree-hooks
engine-worktree-create, post-worktree-execution), and the machine-local trust
ledger those scripts are gated on (worktree-hooks hook-trust-ledger,
hook-consent-gate). ``$HOME`` isolation is what keeps the ledger tests off the
developer's own ``~/.shipd-trust.json``."""

import hashlib
import json
import os
import pty
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
SCRIPT = os.path.join(SCRIPTS, "worktree.py")
SHELL_SCRIPT = os.path.join(SCRIPTS, "worktree.sh")


class WorktreeEngineTestBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="worktree-engine-test-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        # A private HOME so the layered config search can never reach the
        # developer's own ~/.shipd-config.json.
        self.home = os.path.join(self.tmp, "home")
        os.makedirs(self.home)
        self.root = os.path.join(self.tmp, "repo")
        os.makedirs(self.root)
        # A minimal git repo: init + identity + one commit so a branch exists.
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Test")
        self.write(os.path.join(self.root, "README.md"), "seed\n")
        self.git("add", "README.md")
        self.git("commit", "-q", "-m", "seed")

    # --- fixture helpers -------------------------------------------------

    def git(self, *args, cwd=None):
        return subprocess.run(
            ["git", *args], cwd=cwd or self.root,
            capture_output=True, text=True, check=True)

    def write(self, path, text):
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    def read(self, path):
        with open(path, encoding="utf-8") as fh:
            return fh.read()

    def write_config(self, data, where=None):
        """Write a ``.shipd-config.json`` at ``where`` (default the repo root)."""
        path = os.path.join(where or self.root, ".shipd-config.json")
        return self.write(path, json.dumps(data, indent=2) + "\n")

    def set_hooks(self, items, where=None, trust=True):
        """Declare ``items`` in ``where``'s config and, unless ``trust`` is
        false, record the machine-local trust entry the consent gate looks
        for — the fixture equivalent of a user who has already consented."""
        self.write_config({"dir": ".shipd", "post-worktree-scripts": items},
                          where=where)
        if trust:
            self.trust_hooks(items, where=where)

    # --- trust ledger helpers (hook-trust-ledger) ------------------------

    def trust_path(self):
        """The ledger the engine reads, inside the isolated ``$HOME``."""
        return os.path.join(self.home, ".shipd-trust.json")

    def fingerprint(self, items):
        return hashlib.sha256(
            json.dumps(items, separators=(",", ":")).encode()).hexdigest()

    def read_ledger(self):
        if not os.path.exists(self.trust_path()):
            return {}
        return json.loads(self.read(self.trust_path()))

    def trust_hooks(self, items, where=None):
        """Record consent for exactly ``items`` the way the engine does: keyed
        by the list's fingerprint, with the declaring config path stored only
        informationally, so consent follows the commands rather than the file
        that happened to declare them (hook-trust-ledger)."""
        ledger = self.read_ledger()
        ledger[self.fingerprint(items)] = os.path.realpath(
            os.path.join(where or self.root, ".shipd-config.json"))
        self.write(self.trust_path(), json.dumps(ledger, indent=2) + "\n")

    def assertTrusted(self, items):
        self.assertIn(self.fingerprint(items), self.read_ledger())

    def assertNotTrusted(self, items):
        self.assertNotIn(self.fingerprint(items), self.read_ledger())

    def commit_all(self, message="config"):
        """Commit the working tree, so a config written here is *tracked* and
        therefore checked out again inside every worktree created from it."""
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)

    def run_engine(self, *args, cwd=None, env=None):
        run_env = dict(os.environ)
        run_env["HOME"] = self.home
        if env:
            run_env.update(env)
        return subprocess.run(
            [sys.executable, SCRIPT, *args],
            cwd=cwd or self.root, capture_output=True, text=True,
            env=run_env)

    def run_engine_tty(self, *args, answer="y\n", cwd=None):
        """Drive the engine with stdin attached to a pseudo-terminal, feeding
        ``answer`` to whatever it prompts for — the only way to exercise the
        interactive half of the consent gate (hook-consent-gate)."""
        run_env = dict(os.environ)
        run_env["HOME"] = self.home
        master, slave = pty.openpty()
        try:
            proc = subprocess.Popen(
                [sys.executable, SCRIPT, *args],
                cwd=cwd or self.root, stdin=slave,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, env=run_env)
            os.close(slave)
            slave = None
            os.write(master, answer.encode())
            out, errtext = proc.communicate(timeout=120)
        finally:
            if slave is not None:
                os.close(slave)
            os.close(master)
        return subprocess.CompletedProcess(args, proc.returncode, out, errtext)

    def run_shell(self, *args, cwd=None):
        run_env = dict(os.environ)
        run_env["HOME"] = self.home
        return subprocess.run(
            ["bash", SHELL_SCRIPT, *args],
            cwd=cwd or self.root, capture_output=True, text=True,
            env=run_env)

    def worktree_path(self, name):
        return os.path.join(self.root, ".worktrees", name)

    def combined(self, r):
        return (r.stdout or "") + (r.stderr or "")


class CreatePathTest(WorktreeEngineTestBase):
    """The create path wraps worktree.sh and runs the configured scripts
    (worktree-hooks engine-worktree-create)."""

    def test_fresh_create_runs_configured_scripts_in_order(self):
        # engine-worktree-create: Fresh create runs the configured scripts.
        self.set_hooks(["echo one >> ran.txt", "echo two >> ran.txt"])
        r = self.run_engine("my-change")
        self.assertEqual(r.returncode, 0, self.combined(r))
        wt = self.worktree_path("my-change")
        self.assertTrue(os.path.isdir(wt), self.combined(r))
        # Both ran, in declaration order, with the new worktree as cwd.
        self.assertEqual(self.read(os.path.join(wt, "ran.txt")),
                         "one\ntwo\n")
        out = self.combined(r)
        self.assertIn("post-worktree: running echo one >> ran.txt", out)
        self.assertIn("post-worktree: running echo two >> ran.txt", out)

    def test_scripts_see_the_shipd_environment(self):
        # post-worktree-execution: Scripts see the shipd environment.
        self.set_hooks(
            ['printf "%s|%s|%s\\n" "$SHIPD_CHANGE" "$SHIPD_WORKTREE" '
             '"$SHIPD_ROOT" > env.txt'])
        r = self.run_engine("my-change")
        self.assertEqual(r.returncode, 0, self.combined(r))
        wt = self.worktree_path("my-change")
        change, worktree, root = self.read(
            os.path.join(wt, "env.txt")).strip().split("|")
        self.assertEqual(change, "my-change")
        self.assertTrue(worktree.endswith(os.path.join(
            ".worktrees", "my-change")), worktree)
        self.assertTrue(os.path.isabs(worktree), worktree)
        self.assertEqual(os.path.realpath(worktree), os.path.realpath(wt))
        self.assertEqual(os.path.realpath(root), os.path.realpath(self.root))

    def test_reused_worktree_skips_the_scripts(self):
        # engine-worktree-create: Reused worktree skips the scripts.
        self.set_hooks(["echo one >> ran.txt"])
        first = self.run_engine("my-change")
        self.assertEqual(first.returncode, 0, self.combined(first))
        wt = self.worktree_path("my-change")
        self.assertEqual(self.read(os.path.join(wt, "ran.txt")), "one\n")
        second = self.run_engine("my-change")
        self.assertEqual(second.returncode, 0, self.combined(second))
        out = self.combined(second)
        self.assertIn("Reusing existing worktree", out)
        self.assertNotIn("post-worktree: running", out)
        # The file is unchanged: the script did not run a second time.
        self.assertEqual(self.read(os.path.join(wt, "ran.txt")), "one\n")

    def test_attached_worktree_runs_the_scripts(self):
        """A branch that exists without a worktree is an attach, not a reuse:
        the checkout is new, so the setup scripts run."""
        self.git("branch", "change/my-change")
        self.set_hooks(["echo one >> ran.txt"])
        r = self.run_engine("my-change")
        self.assertEqual(r.returncode, 0, self.combined(r))
        self.assertIn("Attached worktree", self.combined(r))
        self.assertEqual(
            self.read(os.path.join(self.worktree_path("my-change"),
                                   "ran.txt")),
            "one\n")

    def test_failing_script_stops_the_chain_with_exit_three(self):
        # post-worktree-execution: Failing script stops the chain.
        self.set_hooks(["echo a >> ran.txt", "exit 1", "echo c >> ran.txt"])
        r = self.run_engine("my-change")
        self.assertEqual(r.returncode, 3, self.combined(r))
        wt = self.worktree_path("my-change")
        # The worktree is left in place.
        self.assertTrue(os.path.isdir(wt))
        # The third item never ran.
        self.assertEqual(self.read(os.path.join(wt, "ran.txt")), "a\n")
        out = self.combined(r)
        self.assertIn("exit 1", out)
        self.assertNotIn("post-worktree: running echo c >> ran.txt", out)

    def test_invalid_config_fails_before_creation(self):
        # post-worktree-execution: Invalid config fails before creation.
        self.write_config({"dir": ".shipd", "post-worktree-scripts": 42})
        r = self.run_engine("my-change")
        self.assertNotEqual(r.returncode, 0)
        self.assertNotEqual(r.returncode, 3)
        self.assertIn("post-worktree-scripts", self.combined(r))
        self.assertFalse(os.path.exists(self.worktree_path("my-change")))

    def test_non_string_item_is_rejected_before_creation(self):
        self.write_config(
            {"dir": ".shipd", "post-worktree-scripts": ["echo ok", ""]})
        r = self.run_engine("my-change")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("post-worktree-scripts", self.combined(r))
        self.assertFalse(os.path.exists(self.worktree_path("my-change")))

    def test_no_key_configured_creates_with_no_scripts(self):
        self.write_config({"dir": ".shipd"})
        r = self.run_engine("my-change")
        self.assertEqual(r.returncode, 0, self.combined(r))
        self.assertTrue(os.path.isdir(self.worktree_path("my-change")))
        self.assertNotIn("post-worktree: running", self.combined(r))

    def test_no_config_file_at_all_creates_with_no_scripts(self):
        r = self.run_engine("my-change")
        self.assertEqual(r.returncode, 0, self.combined(r))
        self.assertTrue(os.path.isdir(self.worktree_path("my-change")))
        self.assertNotIn("post-worktree: running", self.combined(r))

    def test_fresh_flag_passes_through_to_the_helper(self):
        self.set_hooks(["echo one >> ran.txt"])
        first = self.run_engine("my-change")
        self.assertEqual(first.returncode, 0, self.combined(first))
        # --fresh refuses to reuse the existing worktree, exactly as
        # worktree.sh does.
        second = self.run_engine("my-change", "--fresh")
        self.assertEqual(second.returncode, 1, self.combined(second))
        self.assertIn("--fresh refuses to reuse", self.combined(second))

    def test_no_arguments_prints_usage_non_zero(self):
        r = self.run_engine()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("usage:", self.combined(r))
        self.assertIn("worktree.py", self.combined(r))


class PassthroughVerbTest(WorktreeEngineTestBase):
    """`remove` and `prune-branches` re-execute worktree.sh verbatim
    (worktree-hooks engine-worktree-create)."""

    def test_remove_passes_through_to_the_guarded_helper(self):
        # engine-worktree-create: Remove passes through to the guarded helper.
        r = self.run_engine("my-change")
        self.assertEqual(r.returncode, 0, self.combined(r))
        wt = self.worktree_path("my-change")
        self.write(os.path.join(wt, "dirty.txt"), "uncommitted\n")

        engine = self.run_engine("remove", "my-change")
        self.assertEqual(engine.returncode, 2, self.combined(engine))
        self.assertIn("refusing to remove", self.combined(engine))
        self.assertIn("dirty worktree", self.combined(engine))
        self.assertTrue(os.path.isdir(wt))

        # Identical to invoking worktree.sh directly.
        direct = self.run_shell("remove", "my-change")
        self.assertEqual(direct.returncode, engine.returncode)
        self.assertEqual(direct.stderr, engine.stderr)

    def test_remove_succeeds_on_a_clean_worktree(self):
        r = self.run_engine("my-change")
        self.assertEqual(r.returncode, 0, self.combined(r))
        removed = self.run_engine("remove", "my-change")
        self.assertEqual(removed.returncode, 0, self.combined(removed))
        self.assertIn("Removed worktree", self.combined(removed))
        self.assertFalse(os.path.exists(self.worktree_path("my-change")))

    def test_remove_never_runs_the_post_worktree_scripts(self):
        self.set_hooks(["echo one >> ran.txt"])
        self.assertEqual(self.run_engine("my-change").returncode, 0)
        # --force: the hook's own `ran.txt` leaves the worktree dirty, which
        # the guarded teardown refuses on — the point here is only that the
        # teardown path never runs a post-worktree script.
        removed = self.run_engine("remove", "my-change", "--force")
        self.assertEqual(removed.returncode, 0, self.combined(removed))
        self.assertNotIn("post-worktree: running", self.combined(removed))

    def test_prune_branches_passes_through(self):
        # A merged change/* branch with no worktree: the helper prunes it.
        self.git("branch", "change/gone")
        engine = self.run_engine("prune-branches")
        self.assertEqual(engine.returncode, 0, self.combined(engine))
        self.assertIn("pruned: change/gone", engine.stdout)
        self.assertIn("prune-branches:", engine.stdout)

    def test_prune_branches_rejects_unknown_arguments_like_the_helper(self):
        engine = self.run_engine("prune-branches", "--nope")
        direct = self.run_shell("prune-branches", "--nope")
        self.assertEqual(engine.returncode, direct.returncode)
        self.assertNotEqual(engine.returncode, 0)
        self.assertEqual(engine.stderr, direct.stderr)


class HooksVerbTest(WorktreeEngineTestBase):
    """The `hooks` verb family manages the declaration without hand-editing
    (worktree-hooks worktree-hooks-verbs)."""

    def config_path(self, where=None):
        return os.path.join(where or self.root, ".shipd-config.json")

    def config_data(self, where=None):
        return json.loads(self.read(self.config_path(where)))

    def hooks(self, *args, cwd=None, env=None):
        return self.run_engine("hooks", *args, cwd=cwd, env=env)

    # --- add ------------------------------------------------------------

    def test_add_creates_the_key_and_list_reports_it(self):
        # worktree-hooks-verbs: Add creates the key and list reports it.
        self.write_config({"dir": ".shipd", "pr-mode": "draft"})
        added = self.hooks("add", "cp .env.example .env")
        self.assertEqual(added.returncode, 0, self.combined(added))
        data = self.config_data()
        self.assertEqual(data["post-worktree-scripts"],
                         ["cp .env.example .env"])
        # Unrelated keys are untouched.
        self.assertEqual(data["dir"], ".shipd")
        self.assertEqual(data["pr-mode"], "draft")

        listed = self.hooks("list")
        self.assertEqual(listed.returncode, 0, self.combined(listed))
        self.assertIn("0", listed.stdout)
        self.assertIn("cp .env.example .env", listed.stdout)
        self.assertIn(self.config_path(), listed.stdout)

    def test_add_creates_the_config_file_when_absent(self):
        self.assertFalse(os.path.exists(self.config_path()))
        added = self.hooks("add", "npm install")
        self.assertEqual(added.returncode, 0, self.combined(added))
        self.assertEqual(self.config_data()["post-worktree-scripts"],
                         ["npm install"])

    def test_add_writes_two_space_indented_json_with_trailing_newline(self):
        self.write_config({"dir": ".shipd"})
        self.assertEqual(self.hooks("add", "npm install").returncode, 0)
        text = self.read(self.config_path())
        self.assertTrue(text.endswith("\n"), repr(text[-20:]))
        self.assertFalse(text.endswith("\n\n"), repr(text[-20:]))
        self.assertEqual(
            text,
            json.dumps(self.config_data(), indent=2) + "\n")
        self.assertIn('\n  "post-worktree-scripts"', text)

    def test_add_appends_in_order(self):
        self.assertEqual(self.hooks("add", "first").returncode, 0)
        self.assertEqual(self.hooks("add", "second").returncode, 0)
        self.assertEqual(self.config_data()["post-worktree-scripts"],
                         ["first", "second"])

    def test_exact_duplicate_is_refused(self):
        # worktree-hooks-verbs: Exact duplicate is refused.
        self.set_hooks(["cp .env.example .env"])
        again = self.hooks("add", "cp .env.example .env")
        self.assertNotEqual(again.returncode, 0)
        self.assertIn("cp .env.example .env", self.combined(again))
        self.assertEqual(self.config_data()["post-worktree-scripts"],
                         ["cp .env.example .env"])

    def test_add_warns_when_it_shadows_an_outer_layer(self):
        # An outer layer declares the list; the root file does not. Appending
        # here creates a root-level list that wins the key wholesale.
        self.write_config({"post-worktree-scripts": ["outer setup"]},
                          where=self.tmp)
        self.write_config({"dir": ".shipd"})
        added = self.hooks("add", "npm install")
        self.assertEqual(added.returncode, 0, self.combined(added))
        self.assertIn("WARNING:", added.stderr)
        self.assertIn(self.config_path(self.tmp), added.stderr)
        self.assertEqual(self.config_data()["post-worktree-scripts"],
                         ["npm install"])

    def test_add_does_not_warn_without_an_outer_declaration(self):
        self.write_config({"dir": ".shipd"})
        added = self.hooks("add", "npm install")
        self.assertEqual(added.returncode, 0, self.combined(added))
        self.assertNotIn("WARNING:", added.stderr)

    def test_add_rejects_an_empty_item(self):
        r = self.hooks("add", "   ")
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse(os.path.exists(self.config_path()))

    # --- list -----------------------------------------------------------

    def test_list_reports_index_item_and_declaring_path(self):
        self.set_hooks(["cp .env.example .env", ".shipd/hooks/seed.sh"])
        listed = self.hooks("list")
        self.assertEqual(listed.returncode, 0, self.combined(listed))
        lines = [ln for ln in listed.stdout.splitlines() if ln.strip()]
        self.assertEqual(len(lines), 2, listed.stdout)
        self.assertIn("0", lines[0])
        self.assertIn("cp .env.example .env", lines[0])
        self.assertIn(self.config_path(), lines[0])
        self.assertIn("1", lines[1])
        self.assertIn(".shipd/hooks/seed.sh", lines[1])

    def test_list_json_is_machine_readable(self):
        self.set_hooks(["cp .env.example .env", ".shipd/hooks/seed.sh"])
        listed = self.hooks("list", "--json")
        self.assertEqual(listed.returncode, 0, self.combined(listed))
        payload = json.loads(listed.stdout)
        # realpath both sides: on macOS the temp dir is reached through the
        # /private symlink, which `os.getcwd()` resolves and `abspath` does not.
        expected = os.path.realpath(self.config_path())
        self.assertEqual(os.path.realpath(payload["source"]), expected)
        self.assertEqual(
            [(it["index"], it["item"]) for it in payload["items"]],
            [(0, "cp .env.example .env"), (1, ".shipd/hooks/seed.sh")])
        self.assertEqual(os.path.realpath(payload["items"][0]["source"]),
                         expected)

    def test_list_with_no_declaration_is_empty_and_zero(self):
        listed = self.hooks("list")
        self.assertEqual(listed.returncode, 0, self.combined(listed))
        self.assertIn("no post-worktree-scripts", listed.stdout)
        payload = json.loads(self.hooks("list", "--json").stdout)
        self.assertEqual(payload["items"], [])
        self.assertIsNone(payload["source"])

    def test_list_reports_an_invalid_declaration_as_an_error(self):
        self.write_config({"post-worktree-scripts": 42})
        listed = self.hooks("list")
        self.assertNotEqual(listed.returncode, 0)
        self.assertIn("post-worktree-scripts", self.combined(listed))

    # --- remove ---------------------------------------------------------

    def test_remove_by_index_deletes_one_entry(self):
        # worktree-hooks-verbs: Remove by index deletes one entry.
        self.set_hooks(["first", "second"])
        removed = self.hooks("remove", "0")
        self.assertEqual(removed.returncode, 0, self.combined(removed))
        self.assertEqual(self.config_data()["post-worktree-scripts"],
                         ["second"])

    def test_remove_by_item_deletes_one_entry(self):
        self.set_hooks(["first", "second", "first"])
        removed = self.hooks("remove", "first")
        self.assertEqual(removed.returncode, 0, self.combined(removed))
        self.assertEqual(self.config_data()["post-worktree-scripts"],
                         ["second", "first"])

    def test_remove_preserves_unrelated_keys(self):
        self.write_config({"dir": ".shipd", "pr-mode": "draft",
                           "post-worktree-scripts": ["only"]})
        removed = self.hooks("remove", "only")
        self.assertEqual(removed.returncode, 0, self.combined(removed))
        data = self.config_data()
        self.assertEqual(data["post-worktree-scripts"], [])
        self.assertEqual(data["dir"], ".shipd")
        self.assertEqual(data["pr-mode"], "draft")

    def test_remove_of_an_unregistered_item_errors(self):
        self.set_hooks(["first"])
        r = self.hooks("remove", "nope")
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(self.config_data()["post-worktree-scripts"],
                         ["first"])

    def test_remove_of_an_out_of_range_index_errors(self):
        self.set_hooks(["first"])
        r = self.hooks("remove", "7")
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(self.config_data()["post-worktree-scripts"],
                         ["first"])

    def test_remove_without_a_root_declaration_errors(self):
        self.write_config({"dir": ".shipd"})
        r = self.hooks("remove", "0")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("post-worktree-scripts", self.combined(r))

    # --- run ------------------------------------------------------------

    def test_run_executes_the_effective_list_in_place(self):
        # worktree-hooks-verbs: Hooks run executes in place.
        self.set_hooks(["echo one >> ran.txt", "echo two >> ran.txt"])
        wt = os.path.join(self.root, ".worktrees", "my-change")
        r = self.run_engine("my-change")
        self.assertEqual(r.returncode, 0, self.combined(r))
        rerun = self.hooks("run", cwd=wt)
        self.assertEqual(rerun.returncode, 0, self.combined(rerun))
        # Once from the create path, once from `hooks run`.
        self.assertEqual(self.read(os.path.join(wt, "ran.txt")),
                         "one\ntwo\none\ntwo\n")
        self.assertIn("post-worktree: running echo one >> ran.txt",
                      rerun.stdout)

    def test_run_stops_on_the_first_failure_with_exit_three(self):
        self.set_hooks(["echo a >> ran.txt", "exit 1", "echo c >> ran.txt"])
        r = self.hooks("run")
        self.assertEqual(r.returncode, 3, self.combined(r))
        self.assertEqual(self.read(os.path.join(self.root, "ran.txt")), "a\n")
        self.assertNotIn("post-worktree: running echo c >> ran.txt",
                         self.combined(r))

    def test_run_exports_the_shipd_environment(self):
        self.set_hooks(['printf "%s|%s" "$SHIPD_CHANGE" "$SHIPD_WORKTREE" '
                        '> env.txt'])
        wt = os.path.join(self.root, ".worktrees", "my-change")
        self.assertEqual(self.run_engine("my-change").returncode, 0)
        rerun = self.hooks("run", cwd=wt)
        self.assertEqual(rerun.returncode, 0, self.combined(rerun))
        change, worktree = self.read(
            os.path.join(wt, "env.txt")).split("|")
        self.assertEqual(change, "my-change")
        self.assertEqual(os.path.realpath(worktree), os.path.realpath(wt))

    def test_run_with_no_declaration_is_a_no_op(self):
        r = self.hooks("run")
        self.assertEqual(r.returncode, 0, self.combined(r))
        self.assertNotIn("post-worktree: running", self.combined(r))

    # --- dispatch -------------------------------------------------------

    def test_hooks_without_a_verb_prints_usage(self):
        r = self.hooks()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("usage:", self.combined(r))

    def test_unknown_hooks_verb_prints_usage(self):
        r = self.hooks("frobnicate")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("usage:", self.combined(r))

    def test_hooks_root_flag_targets_another_repo(self):
        self.write_config({"dir": ".shipd"})
        elsewhere = os.path.join(self.tmp, "elsewhere")
        os.makedirs(elsewhere)
        added = self.hooks("add", "npm install", "--root", self.root,
                           cwd=elsewhere)
        self.assertEqual(added.returncode, 0, self.combined(added))
        self.assertEqual(self.config_data()["post-worktree-scripts"],
                         ["npm install"])


class HookTrustTest(WorktreeEngineTestBase):
    """The machine-local trust ledger and the consent gate in front of every
    hook execution (worktree-hooks hook-trust-ledger, hook-consent-gate)."""

    def hooks(self, *args, cwd=None):
        return self.run_engine("hooks", *args, cwd=cwd)

    def config_data(self, where=None):
        return json.loads(self.read(
            os.path.join(where or self.root, ".shipd-config.json")))

    # --- the gate --------------------------------------------------------

    def test_untrusted_hooks_refuse_non_interactively(self):
        # hook-consent-gate: Untrusted hooks refuse non-interactively.
        # Hooks inherited from an enclosing (workspace-style) config, with no
        # ledger entry on this machine.
        outer = self.write_config(
            {"post-worktree-scripts": ["echo one >> ran.txt"]},
            where=self.tmp)
        r = self.run_engine("my-change")
        self.assertEqual(r.returncode, 3, self.combined(r))
        wt = self.worktree_path("my-change")
        # The worktree is created and left in place; the hook never ran.
        self.assertTrue(os.path.isdir(wt), self.combined(r))
        self.assertFalse(os.path.exists(os.path.join(wt, "ran.txt")))
        out = self.combined(r)
        self.assertNotIn("post-worktree: running", out)
        # The declaring config is named — the layered search reaches it through
        # the resolved cwd, so compare against its realpath.
        self.assertIn(os.path.realpath(outer), out)
        self.assertIn("echo one >> ran.txt", out)
        # The resume path is named in full: consent, then run the hooks from
        # the worktree that was just created — not from the parked root.
        self.assertIn("hooks trust", out)
        self.assertIn("hooks run", out)
        self.assertIn(wt, out)

    def test_untrusted_root_declared_hooks_refuse_too(self):
        # The uniform ledger covers a freshly cloned repo's own tracked hooks,
        # not only workspace-inherited ones.
        self.set_hooks(["echo one >> ran.txt"], trust=False)
        r = self.run_engine("my-change")
        self.assertEqual(r.returncode, 3, self.combined(r))
        self.assertFalse(os.path.exists(
            os.path.join(self.worktree_path("my-change"), "ran.txt")))
        self.assertIn("hooks trust", self.combined(r))

    def test_hooks_run_is_gated_too(self):
        self.set_hooks(["echo one >> ran.txt"], trust=False)
        r = self.hooks("run")
        self.assertEqual(r.returncode, 3, self.combined(r))
        self.assertFalse(os.path.exists(os.path.join(self.root, "ran.txt")))
        # No worktree was created here, so the resume path names the worktree
        # generically rather than pointing at a path.
        self.assertIn("hooks trust", self.combined(r))
        self.assertIn("from the worktree", self.combined(r))

    def test_trusted_hooks_run_exactly_as_before(self):
        self.set_hooks(["echo one >> ran.txt"])
        r = self.run_engine("my-change")
        self.assertEqual(r.returncode, 0, self.combined(r))
        self.assertEqual(
            self.read(os.path.join(self.worktree_path("my-change"),
                                   "ran.txt")), "one\n")

    def test_consent_records_and_runs(self):
        # hook-consent-gate: Consent records and runs.
        self.set_hooks(["echo one >> ran.txt"], trust=False)
        r = self.run_engine_tty("my-change", answer="y\n")
        self.assertEqual(r.returncode, 0, self.combined(r))
        self.assertEqual(
            self.read(os.path.join(self.worktree_path("my-change"),
                                   "ran.txt")), "one\n")
        self.assertTrusted(["echo one >> ran.txt"])

    def test_declined_consent_keeps_the_worktree(self):
        # hook-consent-gate: Declined consent keeps the worktree.
        self.set_hooks(["echo one >> ran.txt"], trust=False)
        r = self.run_engine_tty("my-change", answer="n\n")
        self.assertEqual(r.returncode, 3, self.combined(r))
        wt = self.worktree_path("my-change")
        self.assertTrue(os.path.isdir(wt))
        self.assertFalse(os.path.exists(os.path.join(wt, "ran.txt")))
        self.assertEqual(self.read_ledger(), {})
        # A declined prompt leaves the same resume path behind as a headless
        # refusal — the user can still consent and run the setup later.
        out = self.combined(r)
        self.assertIn("hooks trust", out)
        self.assertIn("hooks run", out)
        self.assertIn(wt, out)

    # --- the ledger ------------------------------------------------------

    def test_hooks_add_auto_trusts_the_resulting_list(self):
        # hook-trust-ledger: Registration through the verb auto-trusts.
        added = self.hooks("add", "echo one >> ran.txt")
        self.assertEqual(added.returncode, 0, self.combined(added))
        self.assertEqual(
            self.read_ledger(),
            {self.fingerprint(["echo one >> ran.txt"]):
             os.path.realpath(os.path.join(self.root, ".shipd-config.json"))})
        r = self.run_engine("my-change")
        self.assertEqual(r.returncode, 0, self.combined(r))
        self.assertEqual(
            self.read(os.path.join(self.worktree_path("my-change"),
                                   "ran.txt")), "one\n")

    def test_hooks_remove_re_trusts_the_remaining_list(self):
        self.assertEqual(self.hooks("add", "echo one >> ran.txt").returncode, 0)
        self.assertEqual(self.hooks("add", "echo two >> ran.txt").returncode, 0)
        removed = self.hooks("remove", "echo two >> ran.txt")
        self.assertEqual(removed.returncode, 0, self.combined(removed))
        self.assertTrusted(["echo one >> ran.txt"])
        r = self.run_engine("my-change")
        self.assertEqual(r.returncode, 0, self.combined(r))

    def test_out_of_band_list_edit_invalidates_trust(self):
        # hook-trust-ledger: Out-of-band list edit invalidates trust.
        self.assertEqual(self.hooks("add", "echo one >> ran.txt").returncode, 0)
        data = self.config_data()
        data["post-worktree-scripts"].append("echo two >> ran.txt")
        self.write_config(data)
        r = self.run_engine("my-change")
        self.assertEqual(r.returncode, 3, self.combined(r))
        self.assertFalse(os.path.exists(
            os.path.join(self.worktree_path("my-change"), "ran.txt")))
        self.assertIn("hooks trust", self.combined(r))

    def test_malformed_ledger_reads_as_empty(self):
        # hook-trust-ledger: Malformed ledger reads as empty.
        self.write(self.trust_path(), "{not json at all\n")
        self.set_hooks(["echo one >> ran.txt"], trust=False)
        r = self.run_engine("my-change")
        self.assertEqual(r.returncode, 3, self.combined(r))
        self.assertNotIn("Traceback", self.combined(r))
        self.assertIn("hooks trust", self.combined(r))

    def test_no_hooks_never_touches_the_ledger(self):
        r = self.run_engine("my-change")
        self.assertEqual(r.returncode, 0, self.combined(r))
        self.assertFalse(os.path.exists(self.trust_path()))

    def test_ledger_is_keyed_by_the_lists_fingerprint(self):
        # hook-trust-ledger: consent is to the exact command list, so the
        # ledger key is the list's fingerprint and the declaring config path
        # is recorded only informationally.
        self.assertEqual(self.hooks("add", "echo one >> ran.txt").returncode,
                         0)
        ledger = self.read_ledger()
        key = self.fingerprint(["echo one >> ran.txt"])
        self.assertEqual(list(ledger), [key])
        self.assertEqual(
            ledger[key],
            os.path.realpath(os.path.join(self.root, ".shipd-config.json")))

    def test_trust_carries_into_the_worktrees_copy_of_a_tracked_config(self):
        # hook-trust-ledger: Trust carries into the worktree's copy of a
        # tracked config. The worktree checks out its own copy of the tracked
        # declaration, so a path-keyed ledger would strand the consent granted
        # at the root.
        self.set_hooks(["echo one >> ran.txt"], trust=False)
        self.commit_all()
        parked = self.run_engine("my-change")
        self.assertEqual(parked.returncode, 3, self.combined(parked))
        wt = self.worktree_path("my-change")
        self.assertTrue(os.path.isfile(
            os.path.join(wt, ".shipd-config.json")), self.combined(parked))

        trusted = self.hooks("trust")
        self.assertEqual(trusted.returncode, 0, self.combined(trusted))

        rerun = self.hooks("run", cwd=wt)
        self.assertEqual(rerun.returncode, 0, self.combined(rerun))
        self.assertEqual(self.read(os.path.join(wt, "ran.txt")), "one\n")

    def test_adding_onto_an_untrusted_list_does_not_trust_it(self):
        # hook-trust-ledger: Adding onto an untrusted list does not trust it.
        # A registration the user typed must never blanket-trust commands they
        # have not yet been shown.
        self.set_hooks(["echo theirs >> ran.txt"], trust=False)
        self.commit_all()
        added = self.hooks("add", "echo mine >> ran.txt")
        self.assertEqual(added.returncode, 0, self.combined(added))
        self.assertEqual(self.read_ledger(), {})

        r = self.run_engine("my-change")
        self.assertEqual(r.returncode, 3, self.combined(r))
        out = self.combined(r)
        self.assertIn("echo theirs >> ran.txt", out)
        self.assertIn("echo mine >> ran.txt", out)
        self.assertFalse(os.path.exists(
            os.path.join(self.worktree_path("my-change"), "ran.txt")))


class HooksTrustVerbTest(WorktreeEngineTestBase):
    """`hooks trust` records consent explicitly — the resume path a parked
    create names (worktree-hooks worktree-hooks-trust-verb)."""

    def hooks(self, *args, cwd=None):
        return self.run_engine("hooks", *args, cwd=cwd)

    def test_trust_verb_unblocks_a_parked_create(self):
        # worktree-hooks-trust-verb: Trust verb unblocks a parked create.
        self.set_hooks(["echo one >> ran.txt"], trust=False)
        parked = self.run_engine("my-change")
        self.assertEqual(parked.returncode, 3, self.combined(parked))
        wt = self.worktree_path("my-change")

        trusted = self.hooks("trust")
        self.assertEqual(trusted.returncode, 0, self.combined(trusted))
        self.assertIn("echo one >> ran.txt", trusted.stdout)
        self.assertIn(
            os.path.realpath(os.path.join(self.root, ".shipd-config.json")),
            trusted.stdout)
        self.assertTrusted(["echo one >> ran.txt"])

        rerun = self.hooks("run", cwd=wt)
        self.assertEqual(rerun.returncode, 0, self.combined(rerun))
        self.assertEqual(self.read(os.path.join(wt, "ran.txt")), "one\n")

    def test_trust_verb_lets_a_later_create_run_unprompted(self):
        self.set_hooks(["echo one >> ran.txt"], trust=False)
        self.assertEqual(self.hooks("trust").returncode, 0)
        r = self.run_engine("my-change")
        self.assertEqual(r.returncode, 0, self.combined(r))
        self.assertEqual(
            self.read(os.path.join(self.worktree_path("my-change"),
                                   "ran.txt")), "one\n")

    def test_nothing_to_trust_is_an_error(self):
        # worktree-hooks-trust-verb: Nothing to trust is an error.
        self.write_config({"dir": ".shipd"})
        r = self.hooks("trust")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("post-worktree-scripts", self.combined(r))
        self.assertFalse(os.path.exists(self.trust_path()))

    def test_trust_rejects_unknown_arguments(self):
        r = self.hooks("trust", "--nope")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("usage:", self.combined(r))


if __name__ == "__main__":
    unittest.main()
