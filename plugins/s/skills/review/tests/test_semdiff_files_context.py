#!/usr/bin/env python3
"""Unit tests for `semdiff files` (cohort grouping) and `semdiff context`
(best-effort reference lookup). Fixtures are temp git repos; no network."""

import argparse
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
    failure, in both `context` and `related` — never come back silently as
    "no matches"/"no importers", which would be indistinguishable from the
    search having actually run and found nothing. White-box: imports
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

    def test_related_dies_rather_than_reporting_zero_importers(self):
        args = argparse.Namespace(base="main", head=None, linear=False,
                                  mode="balanced")
        with mock.patch.object(semdiff, "_find_importers",
                               side_effect=semdiff.GrepFailure("boom")):
            with self.assertRaises(SystemExit) as ctx:
                semdiff.cmd_related(args)
        self.assertNotEqual(ctx.exception.code, 0)


class RelatedTest(unittest.TestCase):
    """`semdiff related`: importers, importees, caps, and the modes.

    Its own fixture, not `FilesCohortTest`'s shared one — that fixture's file
    count is asserted by `test_cohort_grouping`, so growing it for these
    cases would make that count a lie.

    Base commit: `lib/parser.py` (defines `parse_spec`), `lib/util.py`, and
    ten pre-existing stub modules (`other1/mod1.py` .. `other10/mod10.py`)
    that each `import lib.parser` — real, committed importers, so both the
    ripgrep and the `git grep` fallback can find them. The working tree then
    adds two *changed* files on top of that base: `lib/caller.py` (new,
    importing `lib.parser` by name, `from . import util` which resolves to
    nothing concrete, and `somepkg.outside`, a package outside the repo) and
    an appended `lib/parser.py` (now also `import lib.util`). That gives
    `lib/parser.py` 11 real importers (the ten stubs plus `caller.py`) and
    one real importee (`lib/util.py`) — 12 related files combined, enough on
    its own to exceed the balanced per-file cap of 8 (importers and
    importees share one per-file budget, ranked together by proximity) — so
    a single entry exercises both directions and the cap at once.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="semdiff-related-")
        self.repo = os.path.join(self.tmp, "repo")
        os.makedirs(self.repo)
        subprocess.run(["git", "-c", "init.defaultBranch=main", "init", "-q",
                        self.repo], check=True, capture_output=True)
        git(self.repo, "config", "user.email", "t@example.com")
        git(self.repo, "config", "user.name", "Test")
        git(self.repo, "config", "commit.gpgsign", "false")

        self._write("lib/parser.py",
                    "def parse_spec(text):\n    return text\n")
        self._write("lib/util.py", "def helper():\n    return 1\n")
        for i in range(1, 11):
            self._write(f"other{i}/mod{i}.py", "import lib.parser\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "init")
        git(self.repo, "branch", "-M", "main")

        # Working-tree-only changes: lib/parser.py gains an importee, and
        # lib/caller.py is a new file naming one real importee (lib.parser)
        # and two names that resolve to nothing in the repo.
        self._write(
            "lib/parser.py",
            "def parse_spec(text):\n    return text\n\n\n"
            "import lib.util\n\n\n"
            "def extra():\n    return lib.util.helper()\n")
        self._write(
            "lib/caller.py",
            "from lib.parser import parse_spec\n"
            "from . import util\n"
            "import somepkg.outside\n\n\n"
            "def run():\n    return parse_spec('x')\n")
        # Staged but uncommitted: `related main` still reviews them as
        # working-tree changes against `main`, and staging (rather than
        # leaving `lib/caller.py` untracked) keeps the fixture deterministic
        # across the `git grep` fallback, which — like `context`'s — only
        # searches tracked paths.
        git(self.repo, "add", "-A")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, rel, text):
        path = os.path.join(self.repo, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(text)

    def test_importers_and_importees_both_appear(self):
        rc, out, err = run_semdiff(self.repo, "related", "main")
        self.assertEqual(rc, 0, err)
        self.assertEqual(out["mode"], "balanced")
        self.assertIn("best-effort", out["note"])
        files = out["files"]
        self.assertIn("lib/parser.py", files)
        self.assertIn("lib/caller.py", files)
        parser_entry = files["lib/parser.py"]
        self.assertIn("lib/util.py", parser_entry["importees"])
        self.assertTrue(parser_entry["importers"])
        caller_entry = files["lib/caller.py"]
        self.assertEqual(caller_entry["importees"], ["lib/parser.py"])

    def test_prose_mention_does_not_outrank_a_real_importer(self):
        """A doc file naming the module in prose, in the *same* directory as
        the changed file (so it would rank first by proximity if it were a
        candidate at all), must never appear as an importer, and must never
        displace a genuine importer sitting farther away in a different
        directory — because the matching importer search excludes it from
        the candidate set before ranking runs, not merely by losing a
        proximity tiebreak.
        """
        self._write(
            "lib/README.md",
            "See lib/parser.py and lib.parser for the parse_spec API.\n")
        git(self.repo, "add", "-A")
        rc, out, err = run_semdiff(self.repo, "related", "main")
        self.assertEqual(rc, 0, err)
        entry = out["files"]["lib/parser.py"]
        self.assertNotIn("lib/README.md", entry["importers"])
        self.assertNotIn("lib/README.md", entry["importees"])
        # Unchanged from the no-decoy case (test_per_file_cap_reports_its_
        # dropped_count): the prose file consumed no cap slot at all.
        self.assertEqual(len(entry["importers"]) + len(entry["importees"]), 8)
        self.assertEqual(entry["truncated"], 4)
        self.assertIn("other1/mod1.py", entry["importers"])

    def test_changed_file_never_in_its_own_importer_list(self):
        rc, out, err = run_semdiff(self.repo, "related", "main")
        self.assertEqual(rc, 0, err)
        self.assertNotIn("lib/parser.py", out["files"]["lib/parser.py"]
                         ["importers"])

    def test_unresolvable_import_is_dropped_not_guessed(self):
        rc, out, err = run_semdiff(self.repo, "related", "main")
        self.assertEqual(rc, 0, err)
        importees = out["files"]["lib/caller.py"]["importees"]
        self.assertEqual(importees, ["lib/parser.py"])
        for bogus in ("somepkg/outside.py", "lib/util.py", "lib"):
            self.assertNotIn(bogus, importees)

    def test_import_cannot_escape_the_repository_root(self):
        """A relative import with enough `../` segments can normalize to a
        path outside the repo root. `related` must never name it as an
        importee even when a real file happens to sit there on disk — the
        repository boundary is the limit, not merely the filesystem's. (A
        regression guard: before the fix, `_exists_with_extension` accepted
        any `os.path.isfile` hit regardless of where the join landed, so a
        deeply-relative import in the diff could make `related` name — and
        the review then read — a file outside the repository.)"""
        outside = os.path.join(self.tmp, "escaped.py")
        with open(outside, "w") as fh:
            fh.write("SECRET = 1\n")
        self._write("lib/escape.js",
                    "const x = require('../../escaped');\n")
        git(self.repo, "add", "-A")
        rc, out, err = run_semdiff(self.repo, "related", "main")
        self.assertEqual(rc, 0, err)
        entry = out["files"]["lib/escape.js"]
        self.assertEqual(entry["importees"], [])

    def test_per_file_cap_reports_its_dropped_count(self):
        rc, out, err = run_semdiff(self.repo, "related", "main")
        self.assertEqual(rc, 0, err)
        entry = out["files"]["lib/parser.py"]
        # 11 importers + 1 importee = 12 found, sharing the balanced
        # per-file cap of 8, so 4 are dropped and reported, never silently.
        self.assertEqual(len(entry["importers"]) + len(entry["importees"]), 8)
        self.assertEqual(entry["truncated"], 4)

    def test_max_mode_raises_both_caps_and_names_the_mode(self):
        rc, out, err = run_semdiff(self.repo, "related", "main",
                                   "--mode", "max")
        self.assertEqual(rc, 0, err)
        self.assertEqual(out["mode"], "max")
        self.assertEqual(out["caps"], {"per_file": 20, "per_review": 120})
        entry = out["files"]["lib/parser.py"]
        self.assertEqual(len(entry["importers"]) + len(entry["importees"]), 12)
        self.assertEqual(entry["truncated"], 0)

    def test_git_grep_fallback_finds_the_same_importers(self):
        rc, out, err = run_semdiff(self.repo, "related", "main",
                                   mask_rg=True, home=self.tmp)
        self.assertEqual(rc, 0, err)
        entry = out["files"]["lib/parser.py"]
        self.assertEqual(len(entry["importers"]) + len(entry["importees"]), 8)
        self.assertEqual(entry["truncated"], 4)

    def test_neither_search_tool_present_fails_like_context(self):
        bindir = os.path.join(self.tmp, "pyonly")
        os.makedirs(bindir, exist_ok=True)
        os.symlink(sys.executable, os.path.join(bindir, "python3"))
        env = dict(os.environ)
        env["PATH"] = bindir
        env["HOME"] = self.tmp
        r = subprocess.run(
            [sys.executable, SCRIPT, "related", "main"],
            cwd=self.repo, capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 127, r.stderr)
        self.assertIn("rg", r.stderr)
        self.assertIn("git", r.stderr)


class ImporteeEngineImportFallbackTest(unittest.TestCase):
    """Importee resolution for the cross-skill `sys.path`-injection pattern
    this repo's own scripts use (see `semdiff.py`'s own `_import_engine`): a
    bare `import foo` whose target lives in a directory reached only by
    mutating `sys.path` at runtime, not one resolvable relative to the
    importing file's own directory or the repo root.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="semdiff-engineimport-")
        self.repo = os.path.join(self.tmp, "repo")
        os.makedirs(self.repo)
        subprocess.run(["git", "-c", "init.defaultBranch=main", "init", "-q",
                        self.repo], check=True, capture_output=True)
        git(self.repo, "config", "user.email", "t@example.com")
        git(self.repo, "config", "user.name", "Test")
        git(self.repo, "config", "commit.gpgsign", "false")
        self._write("other/scripts/engine_helper.py",
                    "def helper():\n    return 1\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "init")
        git(self.repo, "branch", "-M", "main")
        self._write(
            "tools/runner.py",
            "import sys, os\n"
            "sys.path.insert(0, os.path.join('other', 'scripts'))\n"
            "import engine_helper\n\n\n"
            "def run():\n    return engine_helper.helper()\n")
        git(self.repo, "add", "-A")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, rel, text):
        path = os.path.join(self.repo, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(text)

    def test_bare_import_resolves_via_unique_repo_wide_fallback(self):
        rc, out, err = run_semdiff(self.repo, "related", "main")
        self.assertEqual(rc, 0, err)
        entry = out["files"]["tools/runner.py"]
        self.assertEqual(
            entry["importees"], ["other/scripts/engine_helper.py"])

    def test_ambiguous_bare_name_is_dropped_not_guessed(self):
        # A second file sharing the basename makes the fallback ambiguous;
        # the importee must be dropped, not guessed at, same as a name that
        # resolves to nothing at all.
        self._write("another/engine_helper.py",
                    "def helper():\n    return 2\n")
        git(self.repo, "add", "-A")
        rc, out, err = run_semdiff(self.repo, "related", "main")
        self.assertEqual(rc, 0, err)
        entry = out["files"]["tools/runner.py"]
        self.assertEqual(entry["importees"], [])


class CrossLanguageImporterTest(unittest.TestCase):
    """`semdiff related` outside Python: a JS/TS-style relative `require()`
    and a C-style relative `#include`, each against a file in the same repo
    that only *mentions* the module's name in a comment.

    Regression coverage for a real bug this change's own verification
    caught: `./foo`-shaped tokens (common to JS/TS/Go/C) were being routed
    into the Python dots-as-package-levels branch because both start with
    `.`, and `os.path.join` silently discards everything before a component
    that starts with `/` — so `./util` resolved to nothing at all, every
    time, regardless of language.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="semdiff-crosslang-")
        self.repo = os.path.join(self.tmp, "repo")
        os.makedirs(self.repo)
        subprocess.run(["git", "-c", "init.defaultBranch=main", "init", "-q",
                        self.repo], check=True, capture_output=True)
        git(self.repo, "config", "user.email", "t@example.com")
        git(self.repo, "config", "user.name", "Test")
        git(self.repo, "config", "commit.gpgsign", "false")
        self._write("src/util.js", "function helper() { return 1; }\n"
                                    "module.exports = { helper };\n")
        self._write("src/helper.h", "int helper(void);\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "init")
        git(self.repo, "branch", "-M", "main")
        self._write("src/consumer.js",
                    "const { helper } = require('./util');\n"
                    "console.log(helper());\n")
        self._write("src/mention.js",
                    "// This file just talks about util.js in a comment.\n"
                    "function other() { return 2; }\n")
        self._write("src/main.c",
                    '#include "./helper.h"\n'
                    "int main(void) { return helper(); }\n")
        self._write("src/mentions.c",
                    "/* helper.h is discussed here but never included. */\n"
                    "int other(void) { return 2; }\n")
        git(self.repo, "add", "-A")
        self._write("src/util.js", "function helper() { return 1; }\n"
                                    "module.exports = { helper };\n// touch\n")
        self._write("src/helper.h", "int helper(void);\n// touch\n")
        git(self.repo, "add", "-A")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, rel, text):
        path = os.path.join(self.repo, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(text)

    def test_js_relative_require_is_found_and_the_mention_is_not(self):
        rc, out, err = run_semdiff(self.repo, "related", "main")
        self.assertEqual(rc, 0, err)
        entry = out["files"]["src/util.js"]
        self.assertEqual(entry["importers"], ["src/consumer.js"])
        self.assertNotIn("src/mention.js", entry["importers"])

    def test_c_relative_include_is_found_and_the_mention_is_not(self):
        rc, out, err = run_semdiff(self.repo, "related", "main")
        self.assertEqual(rc, 0, err)
        entry = out["files"]["src/helper.h"]
        self.assertEqual(entry["importers"], ["src/main.c"])
        self.assertNotIn("src/mentions.c", entry["importers"])


class FairShareInvariantTest(unittest.TestCase):
    """`semdiff related`'s fair-share allocation: no changed file holds a
    second related file while another candidate-bearing file holds none.

    Fixture: 21 changed files (`lib/s01.py` .. `lib/s21.py`), each importing
    two distinct, otherwise-unshared modules (`lib/sNN_a.py`, `lib/sNN_b.py`),
    so every file carries exactly 2 real candidates and the 42 modules never
    overlap between files. 21 files times 2 is 42 — more than the balanced
    per-review cap of 40 can satisfy twice over, so the budget cannot give
    every file a second pick, but 21 is comfortably under 40 so every file
    can get its *first*. That is exactly the scenario the invariant governs:
    some files are denied a second pick, none is denied a first.

    Under the old single running-budget allocation, processing these 21
    files in order would instead give the first 20 their full 2 each (40,
    exhausting the cap) and leave the 21st with zero — the still exact
    defect this change fixes.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="semdiff-fairshare-")
        self.repo = os.path.join(self.tmp, "repo")
        os.makedirs(self.repo)
        subprocess.run(["git", "-c", "init.defaultBranch=main", "init", "-q",
                        self.repo], check=True, capture_output=True)
        git(self.repo, "config", "user.email", "t@example.com")
        git(self.repo, "config", "user.name", "Test")
        git(self.repo, "config", "commit.gpgsign", "false")

        self.names = [f"s{i:02d}" for i in range(1, 22)]
        for name in self.names:
            self._write(f"lib/{name}_a.py", "VALUE = 1\n")
            self._write(f"lib/{name}_b.py", "VALUE = 2\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "init")
        git(self.repo, "branch", "-M", "main")

        for name in self.names:
            self._write(f"lib/{name}.py",
                        f"import {name}_a, {name}_b\n")
        git(self.repo, "add", "-A")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, rel, text):
        path = os.path.join(self.repo, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(text)

    def test_no_file_holds_second_while_another_has_none(self):
        rc, out, err = run_semdiff(self.repo, "related", "main")
        self.assertEqual(rc, 0, err)
        files = out["files"]
        self.assertEqual(len(files), 21)
        counts = {
            path: len(e["importers"]) + len(e["importees"])
            for path, e in files.items()
        }
        # Every one of the 21 candidate-bearing files holds at least one
        # related file — the budget was spent on second picks, never on
        # leaving a file at zero while candidates existed for it.
        self.assertTrue(all(c >= 1 for c in counts.values()), counts)
        self.assertEqual(out["summary"]["files_starved"], 0)
        self.assertEqual(out["summary"]["files_without_candidates"], 0)
        # The 42-candidate demand exceeds the 40 cap, so the cap is indeed
        # exhausted — this isn't a vacuous pass where nobody was denied
        # anything at all.
        self.assertEqual(out["summary"]["related_files"], 40)
        self.assertTrue(any(c == 1 for c in counts.values()), counts)

    def test_allocation_is_deterministic_across_runs(self):
        rc1, out1, err1 = run_semdiff(self.repo, "related", "main")
        rc2, out2, err2 = run_semdiff(self.repo, "related", "main")
        self.assertEqual(rc1, 0, err1)
        self.assertEqual(rc2, 0, err2)
        self.assertEqual(out1["files"], out2["files"])
        self.assertEqual(out1["summary"], out2["summary"])


class FairShareOrderingTest(unittest.TestCase):
    """Scarce-first ordering within a pass: a file with few candidates is
    served before a hub with many, so when the budget is finally contested
    it is the hub's later picks that are sacrificed, never a scarce file's
    first or second.

    Fixture: the same 21 two-candidate files as `FairShareInvariantTest`,
    plus one hub file, `lib/hub.py`, importing 8 distinct modules of its
    own (hitting the balanced per-file cap exactly). Combined demand is
    21*2 + 8 = 50 against the 40 cap, so the budget runs out mid-allocation
    — the condition under which visiting order actually matters.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="semdiff-fairshare-order-")
        self.repo = os.path.join(self.tmp, "repo")
        os.makedirs(self.repo)
        subprocess.run(["git", "-c", "init.defaultBranch=main", "init", "-q",
                        self.repo], check=True, capture_output=True)
        git(self.repo, "config", "user.email", "t@example.com")
        git(self.repo, "config", "user.name", "Test")
        git(self.repo, "config", "commit.gpgsign", "false")

        self.names = [f"s{i:02d}" for i in range(1, 22)]
        for name in self.names:
            self._write(f"lib/{name}_a.py", "VALUE = 1\n")
            self._write(f"lib/{name}_b.py", "VALUE = 2\n")
        for j in range(8):
            self._write(f"lib/hubmod{j}.py", "VALUE = 3\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "init")
        git(self.repo, "branch", "-M", "main")

        for name in self.names:
            self._write(f"lib/{name}.py",
                        f"import {name}_a, {name}_b\n")
        hub_imports = ", ".join(f"hubmod{j}" for j in range(8))
        self._write("lib/hub.py", f"import {hub_imports}\n")
        git(self.repo, "add", "-A")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, rel, text):
        path = os.path.join(self.repo, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(text)

    def test_scarce_file_outranks_hub_within_a_pass(self):
        rc, out, err = run_semdiff(self.repo, "related", "main")
        self.assertEqual(rc, 0, err)
        files = out["files"]
        hub = files["lib/hub.py"]
        hub_count = len(hub["importers"]) + len(hub["importees"])
        scarce_counts = {
            path: len(e["importers"]) + len(e["importees"])
            for path, e in files.items() if path != "lib/hub.py"
        }
        # No file — scarce or hub — is left at zero.
        self.assertTrue(hub_count >= 1, files)
        self.assertTrue(all(c >= 1 for c in scarce_counts.values()),
                        scarce_counts)
        # The hub has 8 real candidates but is the one whose picks are
        # sacrificed once the budget is contested: it ends with fewer than
        # its 8, while at least one scarce file (visited first every pass)
        # reaches its full 2.
        self.assertLess(hub_count, 8)
        self.assertTrue(any(c == 2 for c in scarce_counts.values()),
                        scarce_counts)
        # The hub's own truncation is at least as large as the worst-off
        # scarce file's — the hub, not a scarce file, absorbs the shortfall.
        self.assertGreaterEqual(hub["truncated"],
                                max(2 - c for c in scarce_counts.values()))


class StarvationCountsTest(unittest.TestCase):
    """The two zero reasons stay separate: `files_without_candidates` (the
    search found nothing to relate) and `files_starved` (candidates existed
    and the budget denied them all).

    Fixture: 41 changed files (`lib/f00.py` .. `lib/f40.py`), each importing
    exactly one distinct, unshared module — 41 candidate-bearing files is
    one more than the balanced per-review cap of 40 can give even a single
    pick each, so exactly one of them (the last visited, `lib/f40.py`) ends
    with real candidates and zero kept. A 42nd changed file, `docs/notes.md`,
    is not a source file at all, so it never had a candidate to deny.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="semdiff-starvation-")
        self.repo = os.path.join(self.tmp, "repo")
        os.makedirs(self.repo)
        subprocess.run(["git", "-c", "init.defaultBranch=main", "init", "-q",
                        self.repo], check=True, capture_output=True)
        git(self.repo, "config", "user.email", "t@example.com")
        git(self.repo, "config", "user.name", "Test")
        git(self.repo, "config", "commit.gpgsign", "false")

        self.names = [f"f{i:02d}" for i in range(41)]
        for name in self.names:
            self._write(f"lib/{name}_mod.py", "VALUE = 1\n")
        self._write("docs/notes.md", "Pre-existing notes.\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "init")
        git(self.repo, "branch", "-M", "main")

        for name in self.names:
            self._write(f"lib/{name}.py", f"import {name}_mod\n")
        self._write("docs/notes.md", "Pre-existing notes, now edited.\n")
        git(self.repo, "add", "-A")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, rel, text):
        path = os.path.join(self.repo, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(text)

    def test_starved_file_is_distinguished_from_one_with_nothing_to_relate(
            self):
        rc, out, err = run_semdiff(self.repo, "related", "main")
        self.assertEqual(rc, 0, err)
        summary = out["summary"]
        self.assertEqual(summary["changed_files"], 42)
        self.assertEqual(summary["files_without_candidates"], 1)
        self.assertEqual(summary["files_starved"], 1)

        notes = out["files"]["docs/notes.md"]
        self.assertEqual(len(notes["importers"]) + len(notes["importees"]), 0)
        self.assertEqual(notes["truncated"], 0)

        starved_path = self.names[-1]  # "f40" — visited last, denied last
        starved = out["files"][f"lib/{starved_path}.py"]
        self.assertEqual(
            len(starved["importers"]) + len(starved["importees"]), 0)
        self.assertEqual(starved["truncated"], 1)


class SharedRelatedFileTest(unittest.TestCase):
    """A related file shared by several changed files is charged against
    the per-review cap once, and still listed under every changed file
    that relates to it.

    Fixture: three changed files (`lib/a.py`, `lib/b.py`, `lib/c.py`) that
    each import nothing but the same pre-existing module, `lib/shared.py`.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="semdiff-shared-")
        self.repo = os.path.join(self.tmp, "repo")
        os.makedirs(self.repo)
        subprocess.run(["git", "-c", "init.defaultBranch=main", "init", "-q",
                        self.repo], check=True, capture_output=True)
        git(self.repo, "config", "user.email", "t@example.com")
        git(self.repo, "config", "user.name", "Test")
        git(self.repo, "config", "commit.gpgsign", "false")

        self._write("lib/shared.py", "VALUE = 1\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "init")
        git(self.repo, "branch", "-M", "main")

        for letter in ("a", "b", "c"):
            self._write(f"lib/{letter}.py", "import shared\n")
        git(self.repo, "add", "-A")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, rel, text):
        path = os.path.join(self.repo, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(text)

    def test_shared_related_file_is_charged_once(self):
        rc, out, err = run_semdiff(self.repo, "related", "main")
        self.assertEqual(rc, 0, err)
        for letter in ("a", "b", "c"):
            self.assertEqual(
                out["files"][f"lib/{letter}.py"]["importees"],
                ["lib/shared.py"])
        summary = out["summary"]
        self.assertEqual(summary["related_files"], 1)
        self.assertEqual(summary["related_edges"], 3)
        self.assertGreater(summary["related_edges"], summary["related_files"])
        self.assertEqual(summary["files_starved"], 0)
        self.assertEqual(summary["files_without_candidates"], 0)


class PerFileCapBoundsFreeCandidatesTest(unittest.TestCase):
    """The per-file cap is a hard limit on what a file's entry *lists*,
    never only on what it *pays for* — it still applies to a file whose
    every candidate is free because another changed file already selected
    it.

    Fixture: ten pre-existing modules `lib/s0.py` .. `lib/s9.py`. Ten
    "selector" changed files, `lib/sel0.py` .. `lib/sel9.py`, each import
    exactly one of them (`seli.py` imports `si`), so each selector has a
    single candidate and is visited — and pays for its one module — before
    the eleventh changed file. That eleventh file, `lib/big.py`, imports
    all ten modules: by the time it is visited (it has 10 candidates, every
    selector has 1, so it sorts last), every one of its candidates is
    already `selected` and therefore free. The balanced per-file cap is 8,
    so `big.py` must still stop at 8 even though picking all 10 would cost
    the per-review budget nothing further.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="semdiff-capfree-")
        self.repo = os.path.join(self.tmp, "repo")
        os.makedirs(self.repo)
        subprocess.run(["git", "-c", "init.defaultBranch=main", "init", "-q",
                        self.repo], check=True, capture_output=True)
        git(self.repo, "config", "user.email", "t@example.com")
        git(self.repo, "config", "user.name", "Test")
        git(self.repo, "config", "commit.gpgsign", "false")

        for i in range(10):
            self._write(f"lib/s{i}.py", "VALUE = 1\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "init")
        git(self.repo, "branch", "-M", "main")

        for i in range(10):
            self._write(f"lib/sel{i}.py", f"import s{i}\n")
        big_imports = ", ".join(f"s{i}" for i in range(10))
        self._write("lib/big.py", f"import {big_imports}\n")
        git(self.repo, "add", "-A")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, rel, text):
        path = os.path.join(self.repo, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(text)

    def test_per_file_cap_holds_even_when_every_candidate_is_free(self):
        rc, out, err = run_semdiff(self.repo, "related", "main")
        self.assertEqual(rc, 0, err)

        # Every selector got its one, paid, candidate.
        for i in range(10):
            self.assertEqual(
                out["files"][f"lib/sel{i}.py"]["importees"], [f"lib/s{i}.py"])

        big = out["files"]["lib/big.py"]
        big_count = len(big["importers"]) + len(big["importees"])
        # All 10 of big.py's candidates were already selected by the
        # selectors, so none of them cost the per-review budget anything —
        # yet the per-file cap (8) still bounds what big.py's entry lists.
        self.assertEqual(big_count, 8)
        self.assertEqual(big["truncated"], 2)

        summary = out["summary"]
        # The ten selectors' picks are the only ones charged against the
        # cap; big.py's entirely-free picks add nothing further.
        self.assertEqual(summary["related_files"], 10)
        self.assertEqual(summary["files_starved"], 0)
        self.assertEqual(summary["files_without_candidates"], 0)


if __name__ == "__main__":
    unittest.main()
