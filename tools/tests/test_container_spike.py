"""Tests for tools/container/ — the Apple `container` spike.

Two surfaces, two idioms:

* the host launcher (`tools/container/spike.py`) is exercised through
  `subprocess` with a **stub `container`** first on `PATH` that logs its argv,
  so no test ever reaches the real tool or builds a real image;
* the in-VM entry script (`tools/container/entry.py`) is imported as a module
  and driven through its injectable seams (the turn runner, the `gh` callable),
  so no test spawns a live Claude Code session.

Standard library only.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent
CONTAINER_DIR = TOOLS_DIR / "container"
SPIKE_PY = CONTAINER_DIR / "spike.py"
ENTRY_PY = CONTAINER_DIR / "entry.py"
ENGINE_SCRIPTS = TOOLS_DIR.parent / "plugins" / "s" / "skills" / "build" / "scripts"
DOCKERFILE = CONTAINER_DIR / "Dockerfile"

# The workspace-relative path the launcher must derive for the repo, matching
# this repo's own registration in the workspace config.
REPO_PATH = "shipd/shipd"

FEEDBACK = "Teach the onboarding skill how overlapping workspaces are configured"


def expected_tag():
    """The tag the launcher must derive: `shipd-runner:` + sha256(Dockerfile)[:12]."""
    digest = hashlib.sha256(DOCKERFILE.read_bytes()).hexdigest()
    return "shipd-runner:" + digest[:12]


# The stub `container`: logs every invocation's argv, answers the two read-only
# probes, and — for `run` — copies a canned result into whatever directory the
# argv binds at /out.
STUB = """#!/bin/sh
{
  echo '--- invocation'
  for a in "$@"; do echo "arg $a"; done
} >> '__LOG__'
if [ "$1" = system ] && [ "$2" = status ]; then exit 0; fi
if [ "$1" = image ] && [ "$2" = list ]; then '__CAT__' '__IMAGES__'; exit 0; fi
if [ "$1" = run ]; then
  out=''
  for a in "$@"; do
    case "$a" in
      *target=/out) out=${a#*source=}; out=${out%%,*} ;;
    esac
  done
  if [ -f '__RESULT__' ] && [ -n "$out" ]; then
    '__CP__' '__RESULT__' "$out/result.json"
  fi
  exit 0
fi
exit 0
"""


def _branch_of(path):
    """The branch `path`'s checkout is on — the `--ref` the launcher passes."""
    return subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True, check=True).stdout.strip()


def _git(cwd, *args, env=None):
    subprocess.run(["git", "-C", str(cwd), *args], check=True,
                   capture_output=True, text=True, env=env)


class ContainerSpikeTestCase(unittest.TestCase):
    """Fixture: a stub `container`, a temp workspace/repo layout, a temp HOME."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        # realpath: macOS routes the temp root through /private, and the launcher
        # reports resolved mount sources.
        self.tmp = Path(os.path.realpath(tmp.name))

        self.home = self.tmp / "home"
        self.home.mkdir()
        self.stub_dir = self.tmp / "stub-bin"
        self.stub_dir.mkdir()
        self.clean_bin = self.tmp / "clean-bin"
        self.clean_bin.mkdir()
        for name in ("git", "sh"):
            found = shutil.which(name)
            if found:
                os.symlink(found, self.clean_bin / name)

        self.log = self.tmp / "container.log"
        self.images = self.tmp / "image-list.txt"
        self.images.write_text("")
        self.result = self.tmp / "canned-result.json"

        self.gitconfig = self.tmp / "gitconfig"
        self.gitconfig.write_text(
            "[user]\n\tname = Spike Tester\n\temail = spike@example.com\n")
        self.git_env = dict(os.environ)
        self.git_env["GIT_CONFIG_GLOBAL"] = str(self.gitconfig)
        self.git_env["GIT_CONFIG_NOSYSTEM"] = "1"

        self.write_stub()

    # -- fixture builders ---------------------------------------------------

    def write_stub(self):
        path = self.stub_dir / "container"
        path.write_text(
            STUB.replace("__LOG__", str(self.log))
                .replace("__IMAGES__", str(self.images))
                .replace("__RESULT__", str(self.result))
                .replace("__CAT__", shutil.which("cat") or "/bin/cat")
                .replace("__CP__", shutil.which("cp") or "/bin/cp"))
        path.chmod(0o755)

    def set_image_list(self, text):
        self.images.write_text(text)

    def set_result(self, payload):
        self.result.write_text(json.dumps(payload))

    def make_layout(self):
        """Build `<tmp>/ws` (a workspace git repo tracking `.shipd-config.json`)
        with a repo git checkout at `<tmp>/ws/shipd/shipd`, each carrying an
        `origin` remote. Returns `(workspace, repo)` as strings."""
        ws = self.tmp / "ws"
        ws.mkdir()
        _git(ws, "init", "-q", env=self.git_env)
        _git(ws, "remote", "add", "origin",
             "https://example.com/workspace.git", env=self.git_env)
        (ws / ".shipd-config.json").write_text(json.dumps({
            "workspace": {
                "focus": "shipd",
                "projects": {"shipd": {"repos": [
                    {"path": REPO_PATH,
                     "url": "https://example.com/repo.git",
                     "branch": "main"},
                ]}},
            },
        }, indent=2) + "\n")
        _git(ws, "add", ".shipd-config.json", env=self.git_env)
        _git(ws, "commit", "-q", "-m", "workspace", env=self.git_env)

        repo = ws / REPO_PATH
        repo.mkdir(parents=True)
        _git(repo, "init", "-q", env=self.git_env)
        _git(repo, "remote", "add", "origin",
             "https://example.com/repo.git", env=self.git_env)
        (repo / "README.md").write_text("repo\n")
        _git(repo, "add", "README.md", env=self.git_env)
        _git(repo, "commit", "-q", "-m", "repo", env=self.git_env)
        return str(ws), str(repo)

    # -- invocation ---------------------------------------------------------

    def spike_env(self, clean_path=False, **overrides):
        path = str(self.clean_bin)
        if not clean_path:
            path = str(self.stub_dir) + os.pathsep + path
        env = {
            "PATH": path,
            "HOME": str(self.home),
            "GIT_CONFIG_GLOBAL": str(self.gitconfig),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GH_TOKEN": "gh-token-value",
            "CLAUDE_CODE_OAUTH_TOKEN": "claude-token-value",
            "LANG": "C.UTF-8",
        }
        env.update(overrides)
        return {k: v for k, v in env.items() if v is not None}

    def run_spike(self, *args, env=None):
        return subprocess.run(
            [sys.executable, str(SPIKE_PY), *args],
            capture_output=True, text=True, env=env or self.spike_env())

    # -- log reading --------------------------------------------------------

    def invocations(self):
        """Every logged stub invocation, as a list of argv lists."""
        if not self.log.exists():
            return []
        blocks = self.log.read_text().split("--- invocation\n")
        out = []
        for block in blocks:
            args = [line[len("arg "):] for line in block.splitlines()
                    if line.startswith("arg ")]
            if args:
                out.append(args)
        return out

    def verbs(self):
        return [argv[0] for argv in self.invocations() if argv]

    def one_invocation(self, verb):
        matches = [a for a in self.invocations() if a and a[0] == verb]
        self.assertEqual(len(matches), 1,
                         "expected exactly one %r invocation, saw %r"
                         % (verb, self.invocations()))
        return matches[0]


class LauncherPreflightTests(ContainerSpikeTestCase):
    def test_missing_container_tool_names_the_installer(self):
        ws, repo = self.make_layout()
        result = self.run_spike(
            "--workspace", ws, "--repo", repo, "--dry-run", FEEDBACK,
            env=self.spike_env(clean_path=True))
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        message = result.stdout + result.stderr
        self.assertIn("Error:", message)
        self.assertIn("https://github.com/apple/container/releases", message)
        self.assertIn("container system start", message)

    def test_missing_claude_token_names_setup_token(self):
        ws, repo = self.make_layout()
        env = self.spike_env(CLAUDE_CODE_OAUTH_TOKEN=None)
        env.pop("ANTHROPIC_API_KEY", None)
        result = self.run_spike(
            "--workspace", ws, "--repo", repo, "--dry-run", FEEDBACK, env=env)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        message = result.stdout + result.stderr
        self.assertIn("Error:", message)
        self.assertIn("claude setup-token", message)
        self.assertNotIn("build", self.verbs())
        self.assertNotIn("run", self.verbs())

    def test_dry_run_prints_the_plan_and_invokes_nothing(self):
        ws, repo = self.make_layout()
        result = self.run_spike(
            "--workspace", ws, "--repo", repo, "--dry-run", FEEDBACK)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(expected_tag(), result.stdout)
        self.assertIn("container run", result.stdout)
        self.assertIn("--repo-path %s" % REPO_PATH, result.stdout)
        self.assertNotIn("build", self.verbs())
        self.assertNotIn("run", self.verbs())

    def test_worktree_repo_resolves_to_the_member_path(self):
        """A launcher run from a change worktree must nest the clone at the
        checkout's registered member path, not at the worktree's own path —
        while still mounting (and therefore cloning) the worktree itself.

        The clone itself is taken from the main checkout mounted at
        `/mnt/main`, since a linked worktree's `.git` file names a host path
        the VM cannot resolve, and lands on the worktree's own branch."""
        ws, repo = self.make_layout()
        worktree = str(Path(repo) / ".worktrees" / "x")
        _git(repo, "worktree", "add", "-q", worktree, "-b", "change/x",
             env=self.git_env)

        result = self.run_spike(
            "--workspace", ws, "--repo", worktree, "--dry-run", FEEDBACK)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("--repo-path %s " % REPO_PATH, result.stdout)
        self.assertIn(
            "type=bind,source=%s,target=/mnt/repo,readonly" % worktree,
            result.stdout)
        self.assertIn(
            "type=bind,source=%s,target=/mnt/main,readonly" % repo,
            result.stdout)
        self.assertIn("--clone-from /mnt/main", result.stdout)
        self.assertIn("--ref change/x", result.stdout)


class LauncherImageTests(ContainerSpikeTestCase):
    def test_present_tag_skips_the_build(self):
        ws, repo = self.make_layout()
        self.set_image_list(expected_tag() + "\n")
        self.set_result({"pr_url": "https://example.com/pr/1"})
        result = self.run_spike(
            "--workspace", ws, "--repo", repo,
            "--run-dir", str(self.tmp / "run"), FEEDBACK)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("build", self.verbs())

    def test_absent_tag_builds_once_before_the_run(self):
        ws, repo = self.make_layout()
        self.set_image_list("")
        self.set_result({"pr_url": "https://example.com/pr/1"})
        result = self.run_spike(
            "--workspace", ws, "--repo", repo,
            "--run-dir", str(self.tmp / "run"), FEEDBACK)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        build = self.one_invocation("build")
        self.assertEqual(
            build,
            ["build", "-t", expected_tag(), "-f",
             "tools/container/Dockerfile", "tools/container"])
        verbs = self.verbs()
        self.assertLess(verbs.index("build"), verbs.index("run"))

    def test_dockerfile_edit_changes_the_tag(self):
        spike = _import_spike()
        original = self.tmp / "Dockerfile"
        original.write_bytes(DOCKERFILE.read_bytes())
        edited = self.tmp / "Dockerfile.edited"
        edited.write_bytes(DOCKERFILE.read_bytes() + b"\n")
        self.assertEqual(spike.image_tag(original), expected_tag())
        self.assertNotEqual(spike.image_tag(edited), spike.image_tag(original))


class LauncherRunTests(ContainerSpikeTestCase):
    def test_run_argv_carries_the_mounts_and_passthrough(self):
        ws, repo = self.make_layout()
        run_dir = self.tmp / "run"
        self.set_image_list(expected_tag() + "\n")
        self.set_result({"pr_url": "https://example.com/pr/7"})
        env = self.spike_env()
        env.pop("ANTHROPIC_API_KEY", None)
        result = self.run_spike(
            "--workspace", ws, "--repo", repo, "--run-dir", str(run_dir),
            FEEDBACK, env=env)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        argv = self.one_invocation("run")
        joined = " ".join(argv)
        self.assertIn(
            "type=bind,source=%s,target=/mnt/workspace,readonly" % ws, argv)
        self.assertIn(
            "type=bind,source=%s,target=/mnt/repo,readonly" % repo, argv)
        self.assertIn(
            "type=bind,source=%s,target=/mnt/main,readonly" % repo, argv)
        self.assertIn(
            "type=bind,source=%s,target=/out" % run_dir, argv)
        self.assertEqual(argv.count("--mount"), 4)
        self.assertIn("GH_TOKEN", argv)
        self.assertIn("CLAUDE_CODE_OAUTH_TOKEN", argv)
        self.assertNotIn("ANTHROPIC_API_KEY", argv)
        self.assertIn("--repo-path", argv)
        self.assertEqual(argv[argv.index("--repo-path") + 1], REPO_PATH)
        self.assertIn("--clone-from", argv)
        self.assertEqual(argv[argv.index("--clone-from") + 1], "/mnt/main")
        self.assertIn("--ref", argv)
        self.assertEqual(argv[argv.index("--ref") + 1],
                         _branch_of(repo))
        self.assertIn("-w", argv)
        self.assertIn(expected_tag(), argv)
        self.assertIn("python3", argv)
        self.assertIn("/mnt/repo/tools/container/entry.py", argv)
        self.assertIn("GIT_AUTHOR_NAME=Spike Tester", argv)
        self.assertIn("GIT_COMMITTER_EMAIL=spike@example.com", argv)
        self.assertIn(FEEDBACK, argv)
        self.assertIn("--rm", joined)

    def test_result_with_a_pr_url_exits_zero(self):
        ws, repo = self.make_layout()
        self.set_image_list(expected_tag() + "\n")
        self.set_result({"pr_url": "https://github.com/o/r/pull/42",
                         "change": "x"})
        result = self.run_spike(
            "--workspace", ws, "--repo", repo,
            "--run-dir", str(self.tmp / "run"), FEEDBACK)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.strip().splitlines()[-1],
                         "https://github.com/o/r/pull/42")

    def test_result_without_a_pr_url_exits_one(self):
        ws, repo = self.make_layout()
        self.set_image_list(expected_tag() + "\n")
        self.set_result({"pr_url": "", "failure": "plan stage exhausted"})
        result = self.run_spike(
            "--workspace", ws, "--repo", repo,
            "--run-dir", str(self.tmp / "run"), FEEDBACK)
        self.assertEqual(result.returncode, 1)
        self.assertIn("plan stage exhausted", result.stdout + result.stderr)


def _import_entry():
    """Import `tools/container/entry.py` as a module."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("entry", ENTRY_PY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# A change fixture that reads `ready` and lints clean, written against the
# grammar `.shipd/README.md` defines.
PLAN_MD = """# %(name)s
Status: ready

## Idea

Add a thing so the tool reports it.

### Motivation

Nobody can see the thing today, so the report is unreadable.

### Details

- The report line gains the thing.

Affected capabilities: `thing` (new).

### Non-goals

- No change to any other report.

## Implementation

- **Print the thing** in the report line. Rejected: a separate command.
"""

TASKS_MD = """## 1. Thing

- [ ] 1.1 [req: thing-printed] Print the thing in the report line.
"""

DELTA_MD = """## ADDED Requirements

### Requirement: The thing is printed
id: thing-printed

The report SHALL print the thing on its own line.

#### Scenario: The thing appears
- **WHEN** the report runs
- **THEN** the thing appears on its own line
"""


class EntryTestCase(unittest.TestCase):
    """Fixture for the in-VM entry script, driven through its seams."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(os.path.realpath(tmp.name))
        self.entry = _import_entry()

        self.gitconfig = self.tmp / "gitconfig"
        self.gitconfig.write_text(
            "[user]\n\tname = Spike Tester\n\temail = spike@example.com\n")
        self.git_env = dict(os.environ)
        self.git_env["GIT_CONFIG_GLOBAL"] = str(self.gitconfig)
        self.git_env["GIT_CONFIG_NOSYSTEM"] = "1"

        self.gh_calls = []

    def gh_fn(self, result=(0, "", "")):
        def fn(args, cwd=None):
            self.gh_calls.append((list(args), cwd))
            return result
        return fn

    # -- fixtures -----------------------------------------------------------

    def make_mounts(self):
        """Two source repos standing in for the read-only mounts."""
        ws = self.tmp / "mnt-workspace"
        ws.mkdir()
        _git(ws, "init", "-q", env=self.git_env)
        _git(ws, "remote", "add", "origin",
             "https://example.com/workspace.git", env=self.git_env)
        (ws / ".shipd-config.json").write_text(
            json.dumps({"workspace": {"focus": "shipd"},
                        "themes": ["reliability"]}, indent=2) + "\n")
        _git(ws, "add", "-A", env=self.git_env)
        _git(ws, "commit", "-q", "-m", "workspace", env=self.git_env)

        repo = self.tmp / "mnt-repo"
        repo.mkdir()
        _git(repo, "init", "-q", env=self.git_env)
        _git(repo, "remote", "add", "origin",
             "https://example.com/repo.git", env=self.git_env)
        (repo / "README.md").write_text("repo\n")
        _git(repo, "add", "-A", env=self.git_env)
        _git(repo, "commit", "-q", "-m", "repo", env=self.git_env)
        return str(ws), str(repo)

    def make_clone(self):
        """A stand-in for the in-VM repo clone, carrying the engine scripts at
        the path the entry script imports them from."""
        clone = self.tmp / "clone"
        build = clone / "plugins" / "s" / "skills" / "build"
        build.mkdir(parents=True)
        os.symlink(str(ENGINE_SCRIPTS), str(build / "scripts"))
        return clone

    def make_change(self, root, name):
        """Write a ready, lint-clean change under `<root>/.shipd/planned/<name>`."""
        planned = Path(root) / ".shipd" / "planned" / name
        (planned / "specs" / "thing").mkdir(parents=True, exist_ok=True)
        (planned / "plan.md").write_text(PLAN_MD % {"name": name})
        (planned / "tasks.md").write_text(TASKS_MD)
        (planned / "specs" / "thing" / "spec.md").write_text(DELTA_MD)

    def archive_change(self, root, name):
        (Path(root) / ".shipd" / "completed" / ("20260101-" + name)).mkdir(
            parents=True, exist_ok=True)


class EntryCloneLayoutTests(EntryTestCase):
    def test_nested_clones_with_rewritten_origins(self):
        ws, repo = self.make_mounts()
        root = self.tmp / "root"
        gh = self.gh_fn()
        ws_dir, clone = self.entry.clone_layout(
            ws, repo, REPO_PATH, root=str(root), gh_fn=gh)

        self.assertEqual(Path(ws_dir), root / "ws")
        self.assertEqual(Path(clone), root / "ws" / REPO_PATH)
        self.assertTrue((root / "ws" / ".git").exists())
        self.assertTrue((root / "ws" / REPO_PATH / ".git").exists())

        def origin(path):
            return subprocess.run(
                ["git", "-C", str(path), "remote", "get-url", "origin"],
                capture_output=True, text=True, check=True).stdout.strip()

        self.assertEqual(origin(root / "ws"), "https://example.com/workspace.git")
        self.assertEqual(origin(root / "ws" / REPO_PATH),
                         "https://example.com/repo.git")
        self.assertIn(["auth", "setup-git"], [c[0] for c in self.gh_calls])

    def test_worktree_branch_is_cloned_from_the_main_checkout(self):
        """A worktree mount is not clonable inside the VM, so the clone comes
        from the main checkout and is checked out at the worktree's branch."""
        ws, repo = self.make_mounts()
        _git(repo, "branch", "change/x", env=self.git_env)
        worktree = Path(repo) / ".worktrees" / "x"
        _git(repo, "worktree", "add", "-q", str(worktree), "change/x",
             env=self.git_env)

        root = self.tmp / "root"
        _ws_dir, clone = self.entry.clone_layout(
            ws, str(worktree), REPO_PATH, root=str(root), gh_fn=self.gh_fn(),
            clone_from=repo, ref="change/x")

        def git_out(*args):
            return subprocess.run(["git", "-C", str(clone), *args],
                                  capture_output=True, text=True,
                                  check=True).stdout.strip()

        self.assertEqual(git_out("rev-parse", "--abbrev-ref", "HEAD"),
                         "change/x")
        self.assertEqual(git_out("remote", "get-url", "origin"),
                         "https://example.com/repo.git")

    def test_draft_mode_injected_preserving_other_keys(self):
        ws, repo = self.make_mounts()
        root = self.tmp / "root"
        self.entry.clone_layout(ws, repo, REPO_PATH, root=str(root),
                                gh_fn=self.gh_fn())
        config = json.loads((root / "ws" / ".shipd-config.json").read_text())
        self.assertEqual(config["pr-mode"], "draft")
        self.assertEqual(config["themes"], ["reliability"])
        self.assertEqual(config["workspace"], {"focus": "shipd"})


class EntryGradeTests(EntryTestCase):
    def test_plan_grade_returns_the_change_name(self):
        clone = self.make_clone()
        self.make_change(clone / ".worktrees" / "x", "x")
        self.assertEqual(self.entry.plan_grade(str(clone)), "x")

    def test_plan_grade_withholds_a_change_that_is_not_ready(self):
        clone = self.make_clone()
        worktree = clone / ".worktrees" / "x"
        self.make_change(worktree, "x")
        plan = worktree / ".shipd" / "planned" / "x" / "plan.md"
        plan.write_text(plan.read_text().replace("Status: ready",
                                                 "Status: draft"))
        self.assertIsNone(self.entry.plan_grade(str(clone)))

    def test_build_grade_returns_the_pr_url_once_archived(self):
        clone = self.make_clone()
        worktree = clone / ".worktrees" / "x"
        worktree.mkdir(parents=True)
        gh = self.gh_fn((0, "https://github.com/o/r/pull/9\n", ""))
        self.assertIsNone(self.entry.build_grade(str(worktree), "x", gh))
        self.archive_change(worktree, "x")
        self.assertEqual(self.entry.build_grade(str(worktree), "x", gh),
                         "https://github.com/o/r/pull/9")


class EntryDriveTests(EntryTestCase):
    def test_build_drive_follows_a_passed_plan_drive(self):
        clone = self.make_clone()
        out = self.tmp / "out"
        out.mkdir()
        worktree = clone / ".worktrees" / "x"
        calls = []

        def runner_factory(out_dir, stage):
            def runner(prompt, cwd, resume_id, turn_index, timeout=None,
                       **kwargs):
                calls.append((stage, cwd, turn_index))
                if stage == "plan":
                    self.make_change(worktree, "x")
                else:
                    self.archive_change(worktree, "x")
                return True, None, "sid-" + stage
            return runner

        def gh(args, cwd=None):
            self.gh_calls.append((list(args), cwd))
            if args[:2] == ["pr", "view"]:
                if (worktree / ".shipd" / "completed" / "20260101-x").is_dir():
                    return 0, "https://github.com/o/r/pull/12\n", ""
                return 1, "", "no pull requests found"
            return 0, "", ""

        result = self.entry.drive_stages(
            str(clone), str(out), "make the thing visible",
            runner_factory=runner_factory, gh_fn=gh)

        self.assertEqual(result["change"], "x")
        self.assertEqual(result["pr_url"], "https://github.com/o/r/pull/12")
        self.assertEqual(result["plan_session_id"], "sid-plan")
        self.assertEqual(result["build_session_id"], "sid-build")
        self.assertEqual(result["failure"], "")

        stages = [c[0] for c in calls]
        self.assertEqual(stages, ["plan", "build"])
        self.assertEqual(calls[0][1], str(clone))
        self.assertEqual(calls[1][1], str(worktree))

        written = json.loads((out / "result.json").read_text())
        self.assertEqual(written["pr_url"], "https://github.com/o/r/pull/12")

    def test_exhausted_plan_drive_records_the_failure(self):
        clone = self.make_clone()
        out = self.tmp / "out"
        out.mkdir()
        calls = []

        def runner_factory(out_dir, stage):
            def runner(prompt, cwd, resume_id, turn_index, timeout=None,
                       **kwargs):
                calls.append(stage)
                return True, None, "sid-" + stage
            return runner

        result = self.entry.drive_stages(
            str(clone), str(out), "make the thing visible",
            runner_factory=runner_factory, gh_fn=self.gh_fn(), max_resumes=1)

        self.assertNotIn("build", calls)
        self.assertEqual(result["pr_url"], "")
        self.assertIn("plan", result["failure"])
        written = json.loads((out / "result.json").read_text())
        self.assertEqual(written["pr_url"], "")
        self.assertIn("plan", written["failure"])

    def test_make_runner_writes_each_turn_transcript(self):
        out = self.tmp / "out"
        out.mkdir()
        fake = self.tmp / "fake-claude"
        fake.write_text(
            "#!/bin/sh\n"
            "echo '{\"session_id\": \"abc123\", \"result\": \"done\"}'\n")
        fake.chmod(0o755)
        runner = self.entry.make_runner(str(out), "plan", claude_bin=str(fake))
        ok, failure, session_id = runner("prompt", str(self.tmp), None, 1,
                                         timeout=60)
        self.assertTrue(ok, failure)
        self.assertEqual(session_id, "abc123")
        transcript = json.loads((out / "plan-turn1.json").read_text())
        self.assertEqual(transcript["session_id"], "abc123")


def _import_spike():
    """Import `tools/container/spike.py` as a module."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("spike", SPIKE_PY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    unittest.main()
