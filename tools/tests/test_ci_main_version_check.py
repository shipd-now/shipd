"""Tests for the main-branch plugin version check step in ci.yml.

The step's run block is read out of ``.github/workflows/ci.yml`` and executed
with ``bash -e`` (the shell GitHub Actions uses for ``run:``) inside a
throwaway git repo, so the test exercises the shipped text, not a copy.
"""

import json
import re
import shutil
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CI_YML = REPO_ROOT / ".github" / "workflows" / "ci.yml"
GUARD_REL = "plugins/s/skills/build/scripts/version_guard.py"
MANIFEST_REL = "plugins/s/.claude-plugin/plugin.json"
STEP_NAME = "Check the plugin version on main"


def _steps(text):
    """Split ci.yml text into (name, body) pairs, one per `- name:` step."""
    parts = re.split(r"^      - name: ", text, flags=re.M)[1:]
    return [(part.splitlines()[0].strip(), part) for part in parts]


def _run_block(body):
    """Return the dedented script under the step's `run: |` line."""
    lines = body.splitlines()
    start = next(i for i, l in enumerate(lines) if l.strip() == "run: |")
    return textwrap.dedent("\n".join(lines[start + 1:])).strip() + "\n"


def _git(repo, *args):
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )


class MainCheckStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = CI_YML.read_text(encoding="utf-8")
        cls.by_name = dict(_steps(cls.text))

    def test_workflow_triggers_on_push_to_main(self):
        on_block = self.text.split("\njobs:", 1)[0]
        self.assertRegex(on_block, r"(?m)^  push:\n    branches: \[main\]$")

    def test_step_runs_on_push_against_the_parent(self):
        self.assertIn(STEP_NAME, self.by_name)
        body = self.by_name[STEP_NAME]
        self.assertIn("if: github.event_name == 'push'", body)
        self.assertIn("version_guard.py", body)
        self.assertIn("--base HEAD^1 --head HEAD", body)

    def test_step_ignores_the_ci_scope(self):
        self.assertNotIn("scope", self.by_name[STEP_NAME])

    def test_step_follows_the_pull_request_guard(self):
        names = [n for n, _ in _steps(self.text)]
        self.assertEqual(
            names.index(STEP_NAME), names.index("Guard the plugin version") + 1
        )


class MainCheckBehaviourTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        steps = dict(_steps(CI_YML.read_text(encoding="utf-8")))
        cls.script = _run_block(steps[STEP_NAME])

    def make_repo(self, version="0.6.319"):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        repo = Path(tmp.name)
        _git(repo, "init", "-q", "-b", "main")
        _git(repo, "config", "user.email", "t@example.com")
        _git(repo, "config", "user.name", "t")
        guard = repo / GUARD_REL
        guard.parent.mkdir(parents=True)
        shutil.copy(REPO_ROOT / GUARD_REL, guard)
        self.write_version(repo, version)
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "parent")
        return repo

    def write_version(self, repo, version):
        manifest = repo / MANIFEST_REL
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(json.dumps({"name": "s", "version": version}) + "\n")

    def commit(self, repo, files, version=None):
        for rel, text in files.items():
            p = repo / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text)
        if version is not None:
            self.write_version(repo, version)
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "pushed")

    def run_step(self, repo):
        return subprocess.run(
            ["bash", "-e", "-c", self.script],
            cwd=repo,
            capture_output=True,
            text=True,
        )

    def test_duplicate_version_fails_loudly(self):
        repo = self.make_repo()
        self.commit(repo, {"plugins/s/skills/build/scripts/x.py": "x = 1\n"})
        r = self.run_step(repo)
        out = r.stdout + r.stderr
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("base version '0.6.319', head version '0.6.319'", out)
        self.assertIn("::error", r.stdout)
        self.assertIn("follow-up", out)

    def test_advanced_version_passes(self):
        repo = self.make_repo()
        self.commit(
            repo,
            {"plugins/s/skills/build/scripts/x.py": "x = 1\n"},
            version="0.6.320",
        )
        r = self.run_step(repo)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("::error", r.stdout)

    def test_content_only_change_passes(self):
        repo = self.make_repo()
        self.commit(repo, {".shipd/epics/x/epic.md": "# x\n"})
        r = self.run_step(repo)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
