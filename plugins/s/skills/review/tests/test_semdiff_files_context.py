#!/usr/bin/env python3
"""Unit tests for `semdiff files` (cohort grouping) and `semdiff context`
(best-effort reference lookup). Fixtures are temp git repos; no network."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.normpath(os.path.join(HERE, "..", "scripts", "semdiff.py"))


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


if __name__ == "__main__":
    unittest.main()
