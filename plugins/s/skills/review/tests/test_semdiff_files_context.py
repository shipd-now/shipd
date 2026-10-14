#!/usr/bin/env python3
"""Unit tests for `semdiff files` (cohort grouping) and `semdiff context`
(best-effort reference lookup), plus the module-reachability guard that keeps
a deletion from `semdiff.py` leaving its orphans behind. Fixtures are temp
git repos; no network."""

import argparse
import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.normpath(os.path.join(HERE, "..", "scripts", "semdiff.py"))
SCRIPTS = os.path.dirname(SCRIPT)
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import semdiff  # noqa: E402 — the GrepFailure tests call module internals directly


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args],
                          capture_output=True, text=True, check=True)


def _git_only_bindir(base):
    """A bin dir holding only a git symlink, so rg/ast-grep are unfindable —
    forcing the git grep fallback deterministically."""
    bindir = os.path.join(base, "gitonly")
    os.makedirs(bindir, exist_ok=True)
    link = os.path.join(bindir, "git")
    if not os.path.exists(link):
        os.symlink(shutil.which("git"), link)
    return bindir


def run_semdiff(repo, *args, mask_rg=False, home=None):
    env = dict(os.environ)
    if mask_rg:
        env["PATH"] = _git_only_bindir(home or repo)
        env["HOME"] = home or repo
    r = subprocess.run([sys.executable, SCRIPT, *args],
                       cwd=repo, capture_output=True, text=True, env=env)
    parsed = json.loads(r.stdout) if r.stdout.strip() else None
    return r.returncode, parsed, r.stderr


class FilesCohortTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="semdiff-files-")
        self.repo = os.path.join(self.tmp, "repo")
        os.makedirs(self.repo)
        subprocess.run(["git", "-c", "init.defaultBranch=main", "init", "-q",
                        self.repo], check=True, capture_output=True)
        git(self.repo, "config", "user.email", "t@example.com")
        git(self.repo, "config", "user.name", "Test")
        git(self.repo, "config", "commit.gpgsign", "false")
        self._write("README.md", "seed\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "init")
        git(self.repo, "branch", "-M", "main")
        # Untracked working-tree changes spanning every cohort.
        for rel in (
            "plugins/s/skills/review/SKILL.md",
            ".shipd/planned/x/plan.md",
            "api/routes/users.py",
            "tests/test_x.py",
            "web/components/App.tsx",
            "randomtop/file.py",
        ):
            self._write(rel, "content\n")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, rel, text):
        path = os.path.join(self.repo, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(text)

    def test_cohort_grouping(self):
        rc, out, err = run_semdiff(self.repo, "files", "main")
        self.assertEqual(rc, 0, err)
        cohorts = out["cohorts"]

        def cohort_of(path):
            for name, paths in cohorts.items():
                if path in paths:
                    return name
            return None

        self.assertEqual(
            cohort_of("plugins/s/skills/review/SKILL.md"), "skills")
        self.assertEqual(cohort_of(".shipd/planned/x/plan.md"), "specs")
        self.assertEqual(cohort_of("api/routes/users.py"), "api")
        self.assertEqual(cohort_of("tests/test_x.py"), "tests")
        self.assertEqual(cohort_of("web/components/App.tsx"), "frontend")
        self.assertEqual(cohort_of("randomtop/file.py"), "randomtop")
        self.assertEqual(out["summary"]["files"], 6)

    def test_manifests_land_in_contracts(self):
        """A packaging or dependency manifest is a contract, wherever it sits.

        It declares what the package ships, exports and depends on, so it is
        reviewed in the contracts cohort — foundational, before api and
        frontend — rather than inheriting the cohort of its directory. A
        benchmark run missed three manifest defects (a new file absent from
        `package.json`'s `files`, dependencies present only in the lockfile)
        partly because manifests scattered across unrelated cohorts.
        """
        for rel in ("package.json", "server/package.json", "go.mod",
                    "rust/Cargo.toml", "tests/fixtures/package.json"):
            self._write(rel, "{}\n")
        rc, out, err = run_semdiff(self.repo, "files", "main")
        self.assertEqual(rc, 0, err)
        contracts = out["cohorts"].get("contracts", [])
        for rel in ("package.json", "server/package.json", "go.mod",
                    "rust/Cargo.toml"):
            self.assertIn(rel, contracts)
        # The contracts rule is matched first, so a manifest under tests/
        # lands in contracts too. Pinned deliberately: a fixture manifest
        # reviewed as a contract is reviewed early, never skipped.
        self.assertIn("tests/fixtures/package.json", contracts)

    def test_manifests_whose_name_varies_are_matched_too(self):
        """A manifest named after its project or package still groups right.

        An exact-basename set cannot hold these: a C# project file is named
        after its project, a gemspec after its gem, and the
        `requirements*.txt` family splits by environment. The benchmark's
        test set carries C# and Swift projects, so the suffix and prefix
        shapes are load-bearing, not hypothetical.
        """
        varying = ("Acme.Api.csproj", "src/Lib.fsproj", "Old.vbproj",
                   "my_gem.gemspec", "Thing.nuspec",
                   "requirements-dev.txt")
        fixed = ("Directory.Packages.props", "packages.lock.json",
                 "Package.swift", "Package.resolved", "mix.exs",
                 "pubspec.yaml", "uv.lock", "go.work", "Podfile",
                 "build.sbt")
        for rel in varying + fixed:
            self._write(rel, "x\n")
        rc, out, err = run_semdiff(self.repo, "files", "main")
        self.assertEqual(rc, 0, err)
        contracts = out["cohorts"].get("contracts", [])
        for rel in varying + fixed:
            self.assertIn(rel, contracts, "%s is a manifest" % rel)

    def test_non_manifests_keep_their_cohorts(self):
        """The manifest match must not pull ordinary files into contracts.

        `_is_manifest` grew a suffix list and a `requirements*` prefix rule;
        both are the kind of broad match that can over-capture, so the
        negative case is pinned alongside the positive one.
        """
        rc, out, err = run_semdiff(self.repo, "files", "main")
        self.assertEqual(rc, 0, err)
        contracts = out["cohorts"].get("contracts", [])
        for rel in ("api/routes/users.py", "web/components/App.tsx",
                    "tests/test_x.py", "randomtop/file.py"):
            self.assertNotIn(rel, contracts)


class ContextTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="semdiff-ctx-")
        self.repo = os.path.join(self.tmp, "repo")
        os.makedirs(self.repo)
        subprocess.run(["git", "-c", "init.defaultBranch=main", "init", "-q",
                        self.repo], check=True, capture_output=True)
        git(self.repo, "config", "user.email", "t@example.com")
        git(self.repo, "config", "user.name", "Test")
        git(self.repo, "config", "commit.gpgsign", "false")
        path = os.path.join(self.repo, "lib", "parser.py")
        os.makedirs(os.path.dirname(path))
        with open(path, "w") as fh:
            fh.write("def parse_spec(text):\n    return text\n\n\n"
                     "def caller():\n    return parse_spec('x')\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "init")
        git(self.repo, "branch", "-M", "main")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_git_grep_fallback_without_rg(self):
        rc, out, err = run_semdiff(self.repo, "context", "parse_spec",
                                   mask_rg=True, home=self.tmp)
        self.assertEqual(rc, 0, err)
        self.assertEqual(out["symbol"], "parse_spec")
        self.assertIn("best-effort", out["note"])
        self.assertGreaterEqual(len(out["matches"]), 2)
        for m in out["matches"]:
            self.assertIn("file", m)
            self.assertIn("line", m)
            self.assertIn("text", m)
        self.assertTrue(any(m["file"].endswith("parser.py")
                            for m in out["matches"]))


class GrepFailureTest(unittest.TestCase):
    """A genuine `rg`/`git grep` tool failure (a non-zero exit outside the
    {0, 1} match/no-match pair both tools document) must surface as a hard
    failure, in `context` — never come back silently as "no matches", which
    would be indistinguishable from the search having actually run and
    found nothing. White-box: imports
    `semdiff` directly so the failure can be injected below the subprocess
    boundary, deterministically and without depending on either tool's
    real-world exit codes for a crafted error."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="semdiff-grepfail-")
        self.repo = os.path.join(self.tmp, "repo")
        os.makedirs(self.repo)
        subprocess.run(["git", "-c", "init.defaultBranch=main", "init", "-q",
                        self.repo], check=True, capture_output=True)
        git(self.repo, "config", "user.email", "t@example.com")
        git(self.repo, "config", "user.name", "Test")
        git(self.repo, "config", "commit.gpgsign", "false")
        self._write("lib/mod.py", "def f():\n    return 1\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "init")
        git(self.repo, "branch", "-M", "main")
        self._write("lib/caller.py", "import lib.mod\n")
        git(self.repo, "add", "-A")
        self._cwd = os.getcwd()
        os.chdir(self.repo)

    def tearDown(self):
        os.chdir(self._cwd)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, rel, text):
        path = os.path.join(self.repo, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(text)

    def test_grep_matches_raises_on_a_real_tool_failure(self):
        """A returncode outside {0, 1} must raise `GrepFailure`, not come
        back as an empty, no-matches-indistinguishable list."""
        fake = subprocess.CompletedProcess(
            args=["git", "grep"], returncode=2, stdout="",
            stderr="fatal: boom")
        with mock.patch.object(semdiff, "run", return_value=fake):
            with self.assertRaises(semdiff.GrepFailure):
                semdiff._grep_matches("mod", word=True, fixed=True)

    def test_grep_matches_treats_no_match_as_a_real_empty_result(self):
        """Returncode 1 (git grep's documented "no match") must still come
        back as an ordinary empty list, not raise — only a failure outside
        the documented {0, 1} pair is a `GrepFailure`."""
        fake = subprocess.CompletedProcess(
            args=["git", "grep"], returncode=1, stdout="", stderr="")
        with mock.patch.object(semdiff, "run", return_value=fake):
            self.assertEqual(
                semdiff._grep_matches("mod", word=True, fixed=True), [])

    def test_context_dies_rather_than_reporting_an_empty_result(self):
        args = argparse.Namespace(symbol="mod", path=None, lang=None)
        with mock.patch.object(semdiff, "_grep_matches",
                               side_effect=semdiff.GrepFailure("boom")):
            with self.assertRaises(SystemExit) as ctx:
                semdiff.cmd_context(args)
        self.assertNotEqual(ctx.exception.code, 0)


# Nothing may be deliberately defined in `semdiff.py` and read only from
# outside it: the module is a standalone CLI, never imported for its symbols
# except by these white-box tests. Any entry added here must say which
# out-of-module reader justifies it.
REACHABILITY_ALLOWLIST = frozenset()


class ModuleReachabilityTest(unittest.TestCase):
    """Every module-level definition in `semdiff.py` must be read somewhere
    in `semdiff.py`.

    A subcommand removal deletes a function and leaves whatever only that
    function read. Behavioural tests cannot catch it: a definition nobody
    reads changes no output, so the suite stays green while dead machinery
    accumulates — which is how `semdiff-drop-related` left three orphaned
    import-matching regexes behind after deleting their one reader.

    The scan is whole-file and name-based on purpose, the same shape the
    deletion itself has to reason in. A load inside a module-level lambda,
    a comprehension, a dict literal or a decorator counts, because those are
    exactly the call sites a `def`-body scan misses: `_is_manifest`'s only
    reader is a lambda in `COHORT_RULES`, and a body-only scan would report
    it unused and invite its deletion.
    """

    def test_no_module_level_definition_is_unread(self):
        with open(semdiff.__file__, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())

        defined = set()
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                 ast.ClassDef)):
                defined.add(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        defined.add(target.id)
            elif isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name):
                    defined.add(node.target.id)

        loaded = {node.id for node in ast.walk(tree)
                  if isinstance(node, ast.Name)
                  and isinstance(node.ctx, ast.Load)}

        orphans = sorted(defined - loaded - REACHABILITY_ALLOWLIST)
        self.assertEqual(
            orphans, [],
            "module-level definitions in semdiff.py that nothing in "
            "semdiff.py reads: %s — delete them, or add each to "
            "REACHABILITY_ALLOWLIST naming its out-of-module reader"
            % ", ".join(orphans))
