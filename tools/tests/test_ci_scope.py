"""Tests for tools/ci_scope.py, the CI fast-path path classifier."""

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CI_SCOPE_PY = Path(__file__).resolve().parent.parent / "ci_scope.py"


def _git(repo, *args):
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def _load():
    import importlib.util

    spec = importlib.util.spec_from_file_location("ci_scope", CI_SCOPE_PY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_cli(*args, cwd=None):
    return subprocess.run(
        [sys.executable, "-B", str(CI_SCOPE_PY), *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


class ClassifyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def test_epic_and_research_paths_are_fast(self):
        self.assertTrue(
            self.mod.classify(
                [".shipd/epics/x/epic.md", ".shipd/research/y/report.md"]
            )
        )

    def test_docs_path_is_fast(self):
        self.assertTrue(self.mod.classify([".shipd/docs/z/doc.md"]))

    def test_mixed_is_full(self):
        self.assertFalse(
            self.mod.classify(
                [
                    ".shipd/epics/x/epic.md",
                    "plugins/s/skills/build/scripts/spec_lint.py",
                ]
            )
        )

    def test_verified_is_full(self):
        self.assertFalse(self.mod.classify([".shipd/verified/x/spec.md"]))

    def test_top_level_docs_is_full(self):
        self.assertFalse(self.mod.classify(["docs/customise.md"]))

    def test_planned_and_completed_are_full(self):
        self.assertFalse(self.mod.classify([".shipd/planned/x/plan.md"]))
        self.assertFalse(self.mod.classify([".shipd/completed/x/plan.md"]))

    def test_empty_list_is_full(self):
        self.assertFalse(self.mod.classify([]))

    def test_dotdot_segment_is_full(self):
        self.assertFalse(self.mod.classify([".shipd/epics/../../x.py"]))

    def test_backslash_is_full(self):
        self.assertFalse(self.mod.classify([".shipd/epics\\x\\epic.md"]))

    def test_script_itself_is_full(self):
        self.assertFalse(self.mod.classify(["tools/ci_scope.py"]))


class CliTests(unittest.TestCase):
    def make_repo(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        repo = Path(tmp.name)
        _git(repo, "init", "-q", "-b", "main")
        _git(repo, "config", "user.email", "t@example.com")
        _git(repo, "config", "user.name", "t")
        (repo / "README.md").write_text("hi\n")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "base")
        _git(repo, "checkout", "-q", "-b", "feature")
        return repo

    def commit(self, repo, files):
        for rel, text in files.items():
            p = repo / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text)
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "change")

    def test_epic_only_prints_fast_true_and_writes_output(self):
        repo = self.make_repo()
        self.commit(repo, {".shipd/epics/x/epic.md": "# x\n"})
        out = repo / "gh_output"
        r = run_cli(
            "--event", "pull_request", "--base", "main", "--head", "HEAD",
            "--github-output", str(out), cwd=repo,
        )
        self.assertEqual(r.returncode, 0)
        self.assertIn("fast=true", r.stdout)
        self.assertEqual(out.read_text().splitlines(), ["fast=true"])

    def test_mixed_prints_fast_false(self):
        repo = self.make_repo()
        self.commit(
            repo,
            {".shipd/epics/x/epic.md": "# x\n", "src/a.py": "x = 1\n"},
        )
        r = run_cli(
            "--event", "pull_request", "--base", "main", "--head", "HEAD",
            cwd=repo,
        )
        self.assertEqual(r.returncode, 0)
        self.assertIn("fast=false", r.stdout)

    def test_rename_out_of_allowlist_is_full(self):
        repo = self.make_repo()
        self.commit(repo, {".shipd/epics/x/epic.md": "# x\n"})
        _git(repo, "checkout", "-q", "-b", "second")
        (repo / "moved.md").write_text("# x\n")
        _git(repo, "mv", "-f", ".shipd/epics/x/epic.md", "moved.md")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "mv")
        r = run_cli(
            "--event", "pull_request", "--base", "main", "--head", "HEAD",
            cwd=repo,
        )
        self.assertIn("fast=false", r.stdout)

    def test_push_event_is_full(self):
        repo = self.make_repo()
        self.commit(repo, {".shipd/epics/x/epic.md": "# x\n"})
        r = run_cli(
            "--event", "push", "--base", "main", "--head", "HEAD", cwd=repo
        )
        self.assertEqual(r.returncode, 0)
        self.assertIn("fast=false", r.stdout)

    def test_bad_base_ref_is_full_and_exits_zero(self):
        repo = self.make_repo()
        self.commit(repo, {".shipd/epics/x/epic.md": "# x\n"})
        out = repo / "gh_output"
        r = run_cli(
            "--event", "pull_request", "--base", "no-such-ref",
            "--head", "HEAD", "--github-output", str(out), cwd=repo,
        )
        self.assertEqual(r.returncode, 0)
        self.assertIn("fast=false", r.stdout)
        self.assertEqual(out.read_text().splitlines(), ["fast=false"])

CI_YML = Path(__file__).resolve().parent.parent.parent / ".github" / "workflows" / "ci.yml"
GUARD = "if: steps.scope.outputs.fast != 'true'"


def _steps(text):
    """Split ci.yml text into (name, body) pairs, one per `- name:` step."""
    parts = re.split(r"^      - name: ", text, flags=re.M)[1:]
    return [(part.splitlines()[0].strip(), part) for part in parts]


class CiWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = CI_YML.read_text(encoding="utf-8")
        cls.steps = _steps(cls.text)

    def test_job_is_named_ci(self):
        self.assertRegex(self.text, r"(?m)^  ci:\n    name: ci$")

    def test_scope_step_exists(self):
        self.assertTrue(any("id: scope" in body for _, body in self.steps))

    def test_expensive_steps_are_guarded(self):
        expensive = [
            (n, b)
            for n, b in self.steps
            if any(k in b for k in ("unittest discover", "pip install", "difft"))
        ]
        self.assertGreaterEqual(len(expensive), 10)
        for name, body in expensive:
            self.assertIn(GUARD, body, f"step {name!r} is not guarded")

    def test_lint_and_guard_steps_are_unguarded(self):
        by_name = dict(self.steps)
        for name in (
            "Lint master spec library",
            "Lint in-flight changes",
            "Lint docs",
            "Shell syntax checks",
            "Guard the plugin version",
        ):
            self.assertIn(name, by_name)
            self.assertNotIn("scope", by_name[name], f"step {name!r} is guarded")


if __name__ == "__main__":
    unittest.main()
