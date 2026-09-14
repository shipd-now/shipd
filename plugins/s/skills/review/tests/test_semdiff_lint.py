#!/usr/bin/env python3
"""Unit tests for `semdiff lint` (the static-analysis subcommand).

Fixtures are temp git repositories. None of ruff/eslint/flake8/pylint needs to
be installed: each test that needs a "resolvable binary" writes a small
stand-in executable script into the scratch repo (or a bin dir prepended to
PATH) that emits the shape `semdiff.py` is expected to parse for that tool —
mirroring each real tool's machine-readable output closely enough to exercise
the parsing contract, without requiring the real tool.
"""

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.normpath(os.path.join(HERE, "..", "scripts", "semdiff.py"))


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args],
                          capture_output=True, text=True, check=True)


def init_repo(tmp):
    repo = os.path.join(tmp, "repo")
    os.makedirs(repo)
    subprocess.run(["git", "-c", "init.defaultBranch=main", "init", "-q", repo],
                   check=True, capture_output=True)
    git(repo, "config", "user.email", "t@example.com")
    git(repo, "config", "user.name", "Test")
    git(repo, "config", "commit.gpgsign", "false")
    return repo


def write(repo, rel, text):
    path = os.path.join(repo, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(text)
    return path


def commit_all(repo, message="init"):
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", message)
    git(repo, "branch", "-M", "main")


def make_stub(path, body):
    """Write an executable `/bin/sh` stub at `path` running `body`."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write("#!/bin/sh\n" + body)
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return path


def run_semdiff(repo, *args, tmp, stub_dirs=()):
    """Run `semdiff <args>` with cwd=repo and HOME pinned to `tmp` (so no
    real `~/.shipd-config.json` on the host leaks into the resolved config).
    `stub_dirs` are prepended to PATH, ahead of whatever is really installed,
    so a fake linter always wins resolution over a real one of the same
    name."""
    env = dict(os.environ)
    if stub_dirs:
        env["PATH"] = os.pathsep.join(list(stub_dirs) + [env.get("PATH", "")])
    env["HOME"] = tmp
    r = subprocess.run([sys.executable, SCRIPT, *args],
                       cwd=repo, capture_output=True, text=True, env=env)
    parsed = json.loads(r.stdout) if r.stdout.strip() else None
    return r.returncode, parsed, r.stderr


def entry_for(out, name):
    for e in out["linters"]:
        if e["name"] == name:
            return e
    raise AssertionError(f"no {name!r} entry in {out['linters']!r}")


class RanStateTest(unittest.TestCase):
    """A detected linter with a resolvable binary runs over changed paths
    only, and its findings carry the five required fields."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="semdiff-lint-ran-")
        self.repo = init_repo(self.tmp)
        write(self.repo, "ruff.toml", "line-length = 100\n")
        write(self.repo, "unchanged.py", "x = 1\n")
        commit_all(self.repo)
        write(self.repo, "a.py", "import os\n")
        write(self.repo, "b.py", "import sys\n")
        write(self.repo, "notes.md", "not python\n")
        self.bindir = os.path.join(self.tmp, "bin")
        os.makedirs(self.bindir)
        make_stub(os.path.join(self.bindir, "ruff"), textwrap.dedent("""\
            cat <<'EOF'
            [
              {"filename": "a.py", "location": {"row": 1, "column": 1},
               "code": "F401", "message": "'os' imported but unused"}
            ]
            EOF
            """))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_ran_state_scoped_argv_and_findings(self):
        rc, out, err = run_semdiff(self.repo, "lint", "main", tmp=self.tmp,
                                   stub_dirs=[self.bindir])
        self.assertEqual(rc, 0, err)
        self.assertEqual(out["base"], "main")
        self.assertIsNone(out["head"])
        self.assertEqual(out["mode"], "working-tree")

        entry = entry_for(out, "ruff")
        self.assertEqual(entry["state"], "ran")
        argv = entry["argv"]
        self.assertEqual(argv[0], os.path.join(self.bindir, "ruff"))
        tail = set(argv[-2:])
        self.assertEqual(tail, {"a.py", "b.py"})
        self.assertNotIn("unchanged.py", argv)
        self.assertNotIn("notes.md", argv)

        findings = entry["findings"]
        self.assertEqual(len(findings), 1)
        f = findings[0]
        self.assertEqual(f["path"], "a.py")
        self.assertEqual(f["line"], 1)
        self.assertEqual(f["rule"], "F401")
        self.assertIn("unused", f["message"])
        self.assertIn("severity", f)

        self.assertEqual(out["summary"]["findings"], 1)
        self.assertEqual(out["summary"]["ran"], 1)


class UnavailableStateTest(unittest.TestCase):
    """A marker with no resolvable binary is reported, never dropped."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="semdiff-lint-unavail-")
        self.repo = init_repo(self.tmp)
        write(self.repo, ".flake8", "[flake8]\nmax-line-length = 100\n")
        commit_all(self.repo)
        write(self.repo, "a.py", "x=1\n")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    @unittest.skipIf(
        shutil.which("flake8") is not None,
        "flake8 is installed on this machine; this scenario assumes none "
        "of the four linters resolve, per the build environment note")
    def test_marker_without_binary_reports_unavailable(self):
        rc, out, err = run_semdiff(self.repo, "lint", "main", tmp=self.tmp)
        self.assertEqual(rc, 0, err)
        entry = entry_for(out, "flake8")
        self.assertEqual(entry["state"], "unavailable")
        self.assertEqual(entry.get("argv"), [])


class SkippedStateTest(unittest.TestCase):
    """A detected linter owning no changed path is skipped and never run."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="semdiff-lint-skip-")
        self.repo = init_repo(self.tmp)
        write(self.repo, "eslint.config.js", "module.exports = [];\n")
        commit_all(self.repo)
        write(self.repo, "a.py", "x = 1\n")  # only a Python change
        self.bindir = os.path.join(self.tmp, "bin")
        os.makedirs(self.bindir)
        self.marker = os.path.join(self.tmp, "eslint-ran")
        make_stub(os.path.join(self.bindir, "eslint"),
                  f"touch {self.marker}\necho '[]'\n")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_skipped_when_no_owned_changed_path(self):
        rc, out, err = run_semdiff(self.repo, "lint", "main", tmp=self.tmp,
                                   stub_dirs=[self.bindir])
        self.assertEqual(rc, 0, err)
        entry = entry_for(out, "eslint")
        self.assertEqual(entry["state"], "skipped")
        self.assertEqual(entry.get("argv"), [])
        self.assertFalse(
            os.path.exists(self.marker),
            "eslint stub must not run when it owns no changed path")


class NpmScriptTest(unittest.TestCase):
    """A `package.json` lint script is not-run by default, and runs only
    with the `lint.run_scripts` opt-in."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="semdiff-lint-npm-")
        self.repo = init_repo(self.tmp)
        write(self.repo, "package.json",
              json.dumps({"name": "x", "scripts": {"lint": "eslint ."}}))
        commit_all(self.repo)
        write(self.repo, "app.js", "var x = 1;\n")
        self.bindir = os.path.join(self.tmp, "bin")
        os.makedirs(self.bindir)
        self.marker = os.path.join(self.tmp, "npm-ran")
        make_stub(os.path.join(self.bindir, "npm"),
                  f"touch {self.marker}\nexit 0\n")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_not_run_without_opt_in(self):
        rc, out, err = run_semdiff(self.repo, "lint", "main", tmp=self.tmp,
                                   stub_dirs=[self.bindir])
        self.assertEqual(rc, 0, err)
        entry = entry_for(out, "npm-lint-script")
        self.assertEqual(entry["state"], "not-run")
        self.assertFalse(os.path.exists(self.marker))

    def test_runs_with_opt_in(self):
        write(self.repo, ".shipd-config.json",
              json.dumps({"lint": {"run_scripts": True}}))
        rc, out, err = run_semdiff(self.repo, "lint", "main", tmp=self.tmp,
                                   stub_dirs=[self.bindir])
        self.assertEqual(rc, 0, err)
        entry = entry_for(out, "npm-lint-script")
        self.assertEqual(entry["state"], "ran")
        self.assertTrue(os.path.exists(self.marker),
                        "npm run lint should execute once opted in")


class FailedStateTest(unittest.TestCase):
    """A timeout or unparseable output degrades to `failed`, exit 0."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="semdiff-lint-fail-")
        self.repo = init_repo(self.tmp)
        write(self.repo, ".flake8", "[flake8]\n")
        commit_all(self.repo)
        write(self.repo, "a.py", "x=1\n")
        self.bindir = os.path.join(self.tmp, "bin")
        os.makedirs(self.bindir)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_unparseable_output_sets_failed(self):
        make_stub(os.path.join(self.bindir, "flake8"),
                  "echo 'not json at all'\n"
                  "echo 'flake8: internal crash trace' 1>&2\n"
                  "exit 1\n")
        rc, out, err = run_semdiff(self.repo, "lint", "main", tmp=self.tmp,
                                   stub_dirs=[self.bindir])
        self.assertEqual(rc, 0, err)
        entry = entry_for(out, "flake8")
        self.assertEqual(entry["state"], "failed")
        self.assertTrue(entry["argv"])
        self.assertIn("stderr", entry)
        self.assertIn("crash trace", entry["stderr"])

    def test_timeout_sets_failed(self):
        make_stub(os.path.join(self.bindir, "flake8"),
                  "sleep 3\necho '[]'\n")
        rc, out, err = run_semdiff(self.repo, "lint", "main", "--timeout", "1",
                                   tmp=self.tmp, stub_dirs=[self.bindir])
        self.assertEqual(rc, 0, err)
        entry = entry_for(out, "flake8")
        self.assertEqual(entry["state"], "failed")
        self.assertIn("stderr", entry)
        self.assertIn("timeout", entry["stderr"].lower())


class NodeModulesPrecedenceTest(unittest.TestCase):
    """The repository's own `node_modules/.bin` install wins over PATH."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="semdiff-lint-nm-")
        self.repo = init_repo(self.tmp)
        write(self.repo, "eslint.config.js", "module.exports = [];\n")
        commit_all(self.repo)
        write(self.repo, "app.js", "var x = 1;\n")
        nm_bin = os.path.join(self.repo, "node_modules", ".bin")
        os.makedirs(nm_bin)
        make_stub(os.path.join(nm_bin, "eslint"), "echo '[]'\n")
        self.path_bin = os.path.join(self.tmp, "pathbin")
        os.makedirs(self.path_bin)
        make_stub(os.path.join(self.path_bin, "eslint"), "echo '[]'\n")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_node_modules_bin_wins(self):
        rc, out, err = run_semdiff(self.repo, "lint", "main", tmp=self.tmp,
                                   stub_dirs=[self.path_bin])
        self.assertEqual(rc, 0, err)
        entry = entry_for(out, "eslint")
        self.assertEqual(entry["state"], "ran")
        # realpath on both sides: semdiff resolves the repo root via `git
        # rev-parse --show-toplevel`, which canonicalizes symlinks (e.g.
        # macOS's /var -> /private/var), while `self.repo` is the raw
        # tempfile.mkdtemp() path.
        self.assertEqual(
            os.path.realpath(entry["argv"][0]),
            os.path.realpath(os.path.join(
                self.repo, "node_modules", ".bin", "eslint")))


class DisableTest(unittest.TestCase):
    """`lint.disable` suppresses a fully detected linter."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="semdiff-lint-disable-")
        self.repo = init_repo(self.tmp)
        write(self.repo, "ruff.toml", "line-length = 100\n")
        commit_all(self.repo)
        write(self.repo, "a.py", "import os\n")
        write(self.repo, ".shipd-config.json",
              json.dumps({"lint": {"disable": ["ruff"]}}))
        self.bindir = os.path.join(self.tmp, "bin")
        os.makedirs(self.bindir)
        self.marker = os.path.join(self.tmp, "ruff-ran")
        make_stub(os.path.join(self.bindir, "ruff"),
                  f"touch {self.marker}\necho '[]'\n")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_disabled_linter_does_not_run(self):
        rc, out, err = run_semdiff(self.repo, "lint", "main", tmp=self.tmp,
                                   stub_dirs=[self.bindir])
        self.assertEqual(rc, 0, err)
        entry = entry_for(out, "ruff")
        self.assertEqual(entry["state"], "skipped")
        self.assertEqual(entry.get("argv"), [])
        self.assertFalse(os.path.exists(self.marker),
                         "a disabled linter must not execute")


if __name__ == "__main__":
    unittest.main()
