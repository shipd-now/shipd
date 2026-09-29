#!/usr/bin/env python3
"""entry.py — the runtime-neutral spike entry point, run inside the VM.

The host launcher (`tools/container/spike.py`) mounts the workspace root at
`/mnt/workspace`, the repo at `/mnt/repo`, and the repo's main checkout at
`/mnt/main`, all read-only, and the run directory at `/out`. This script owns
everything after that: it clones the workspace and the repo (from
`--clone-from`, checked out at `--ref`) into a writable tree, injects
`pr-mode: draft` into the cloned workspace layer, then drives a headless
`/s:plan` session and a headless `/s:build` session over one piece of user
feedback and writes `/out/result.json`.

Nothing here is Apple-`container`-specific: the mounts, the output directory,
and the clone root are all arguments, so the same script becomes an ax Task
command by changing only how it is invoked.

Standard library only. The engine modules it drives with — `session_driver`,
`spec_common`, `spec_status`, `spec_lint`, `autopilot` — are imported from the
**clone**, never from the host, so the VM runs the code it is about to build on.
"""

import argparse
import json
import os
import subprocess
import sys

DEFAULT_ROOT = "/workspace"
CONFIG_FILENAME = ".shipd-config.json"

# The engine's scripts directory, relative to the repo clone's root.
ENGINE_REL = os.path.join("plugins", "s", "skills", "build", "scripts")

# Mirrors the epic autopilot's budgets (autopilot.py): four resumed turns
# per drive, half an hour of wall clock per turn.
MAX_RESUMES = 4
TIMEOUT = 1800

# The two stage prompts. Each is sent with `autopilot.GOAHEAD_REPLY` appended,
# so turn 1 already carries the standing instruction every resumed turn repeats.
PLAN_PROMPT = (
    "Run /s:plan %s. Investigate, spec it, and promote it to Status: ready.")

BUILD_PROMPT = (
    "Run /s:build for the change %s: implement every task, then merge and "
    "archive it and open its draft PR (draft mode — do not enable "
    "auto-merge).")


class EntryError(Exception):
    """A run-blocking condition inside the VM."""


# ---------------------------------------------------------------------------
# Shell seams
# ---------------------------------------------------------------------------

def _run(cmd, cwd=None):
    """Run `cmd`; return `(returncode, stdout, stderr)`."""
    try:
        proc = subprocess.run(cmd, cwd=cwd, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as exc:
        return 127, "", str(exc)
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def _git(args, cwd=None):
    rc, out, err = _run(["git", *args], cwd=cwd)
    if rc != 0:
        raise EntryError("git %s failed (exit %d): %s"
                         % (" ".join(args), rc, (err or out).strip()))
    return out


def default_gh(args, cwd=None):
    """The production `gh` seam: run `gh <args>` and return
    `(returncode, stdout, stderr)`. Injectable so tests never shell out."""
    return _run(["gh", *args], cwd=cwd)


# ---------------------------------------------------------------------------
# Clone layout
# ---------------------------------------------------------------------------

def clone_layout(workspace, repo, repo_path, root=DEFAULT_ROOT, gh_fn=None,
                 clone_from=None, ref=None):
    """Build the writable working tree from the read-only mounts.

    Clones the workspace mount to `<root>/ws` and the repo to
    `<root>/ws/<repo_path>`, points each clone's `origin` at the URL its mount
    carries (the mount path itself is useless to anyone downstream), injects
    `pr-mode: draft` into the cloned workspace's `.shipd-config.json` — the
    layer that governs every repo beneath it — and runs `gh auth setup-git` so
    the clones can push.

    The repo clone is taken from `clone_from` (default `repo`): a linked
    worktree's `.git` is a file whose `gitdir:` names a host path, so the
    worktree mount itself is not clonable inside the VM — the main checkout is.
    When `ref` is given the clone is checked out at it, either a branch its
    `origin` carries or a sha, so the run still builds on the worktree's branch.

    Returns `(workspace_clone, repo_clone)`.
    """
    gh_fn = gh_fn or default_gh
    root = os.path.abspath(root)
    ws_dir = os.path.join(root, "ws")
    clone = os.path.join(ws_dir, repo_path)
    source = clone_from or repo

    os.makedirs(root, exist_ok=True)
    _git(["clone", "--quiet", workspace, ws_dir])
    _git(["remote", "set-url", "origin", _origin_of(workspace)], cwd=ws_dir)

    _git(["clone", "--quiet", source, clone])
    if ref:
        _git(["checkout", "--quiet", ref], cwd=clone)
    _git(["remote", "set-url", "origin", _origin_of(source)], cwd=clone)

    inject_draft_mode(ws_dir)

    rc, _out, err = gh_fn(["auth", "setup-git"], ws_dir)
    if rc != 0:
        raise EntryError("gh auth setup-git failed (exit %d): %s"
                         % (rc, err.strip()))
    return ws_dir, clone


def _origin_of(mount):
    return _git(["-C", mount, "remote", "get-url", "origin"]).strip()


def inject_draft_mode(ws_dir):
    """Set `pr-mode: draft` in the cloned workspace's config, preserving every
    other key. Draft mode rides the workspace layer, so every repo beneath it
    stops at an open draft PR rather than auto-merging."""
    path = os.path.join(ws_dir, CONFIG_FILENAME)
    data = {}
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as handle:
            try:
                loaded = json.load(handle)
            except ValueError as exc:
                raise EntryError("%s is not valid JSON: %s" % (path, exc))
        if isinstance(loaded, dict):
            data = loaded
    data["pr-mode"] = "draft"
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")
    return path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        description="Plan and build one piece of user feedback inside a "
                    "sandboxed runtime, ending on a draft PR.")
    parser.add_argument("--workspace", required=True,
                        help="the read-only workspace mount")
    parser.add_argument("--repo", required=True,
                        help="the read-only repo mount")
    parser.add_argument("--repo-path", required=True,
                        help="the repo's path relative to the workspace root")
    parser.add_argument("--clone-from", default=None,
                        help="the mount the repo clone is taken from "
                             "(default: --repo)")
    parser.add_argument("--ref", default=None,
                        help="the branch or sha the repo clone checks out "
                             "(default: whatever the clone's HEAD names)")
    parser.add_argument("--out", required=True,
                        help="the writable run directory (result.json, "
                             "turn transcripts)")
    parser.add_argument("--feedback", required=True,
                        help="the user feedback to plan and build")
    parser.add_argument("--root", default=DEFAULT_ROOT,
                        help="where the clones land (default: %s)"
                             % DEFAULT_ROOT)
    return parser

# ---------------------------------------------------------------------------
# The engine, imported from the clone
# ---------------------------------------------------------------------------

_ENGINE_CACHE = {}


class _Engine(object):
    """The engine modules the drive needs, loaded from one clone."""

    def __init__(self, session_driver, spec_common, spec_status, spec_lint,
                 autopilot):
        self.session_driver = session_driver
        self.spec_common = spec_common
        self.spec_status = spec_status
        self.spec_lint = spec_lint
        self.autopilot = autopilot


def load_engine(clone):
    """Import the spec engine from `<clone>/plugins/s/skills/build/scripts`.

    The VM drives the code it is about to build on, never a host copy. The
    result is cached per clone, so the per-turn grades cost one import."""
    clone = os.path.abspath(clone)
    cached = _ENGINE_CACHE.get(clone)
    if cached is not None:
        return cached
    scripts = os.path.join(clone, ENGINE_REL)
    if not os.path.isdir(scripts):
        raise EntryError("the clone carries no engine scripts at %s" % scripts)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    import session_driver
    import spec_common
    import spec_status
    import spec_lint
    import autopilot
    engine = _Engine(session_driver, spec_common, spec_status, spec_lint,
                     autopilot)
    _ENGINE_CACHE[clone] = engine
    return engine


# ---------------------------------------------------------------------------
# Grades
# ---------------------------------------------------------------------------

def plan_grade(clone):
    """The plan stage's grade: the name of the change whose worktree under
    `<clone>/.worktrees/` holds it at `Status: ready`, lint clean — or `None`
    while no worktree does.

    Mirrors `autopilot._plan_grade`, but discovers the change rather than being
    told it: the planning session chooses the change's name, so the grade is
    also how the entry script learns what was planned."""
    engine = load_engine(clone)
    worktrees = os.path.join(clone, ".worktrees")
    if not os.path.isdir(worktrees):
        return None
    for name in sorted(os.listdir(worktrees)):
        worktree = os.path.join(worktrees, name)
        if not os.path.isdir(worktree):
            continue
        try:
            if engine.spec_status.read_status(worktree, name) != "ready":
                continue
            if engine.spec_lint.lint_change(worktree, name):
                continue
        except Exception:
            continue
        return name
    return None


def build_grade(worktree, name, gh_fn=None):
    """The build stage's grade: the change's PR URL once it is archived under
    `completed/*-<name>` **and** `gh pr view change/<name>` names a URL — or
    `None`. Mirrors `autopilot._build_grade`, returning the URL it proves
    rather than a boolean, since that URL is the run's result."""
    gh_fn = gh_fn or default_gh
    engine = load_engine_for_worktree(worktree)
    completed = os.path.join(engine.spec_common.specs_dir(worktree), "completed")
    archived = os.path.isdir(completed) and any(
        entry.endswith("-" + name) for entry in os.listdir(completed))
    if not archived:
        return None
    rc, out, _err = gh_fn(
        ["pr", "view", "change/" + name, "--json", "url", "-q", ".url"],
        worktree)
    if rc != 0:
        return None
    return out.strip() or None


def load_engine_for_worktree(worktree):
    """Load the engine from the clone a worktree belongs to
    (`<clone>/.worktrees/<name>`)."""
    return load_engine(os.path.dirname(os.path.dirname(
        os.path.abspath(worktree))))


# ---------------------------------------------------------------------------
# Turn runner
# ---------------------------------------------------------------------------

def make_runner(out, stage, claude_bin="claude", extra_args=None,
                timeout=TIMEOUT):
    """Build a `session_driver.drive` runner that also retains each turn.

    Same contract as `session_driver.run_turn` — `(ok, failure, session_id)` —
    but the turn's stdout is written to `<out>/<stage>-turn<N>.json` first, so
    a finished run leaves behind the transcripts a human needs to reopen the
    conversation with `claude --resume <id>`."""

    def runner(prompt, cwd, resume_id, turn_index, timeout=timeout, **_kwargs):
        cmd = [claude_bin, "-p", prompt, "--output-format", "json"]
        if extra_args:
            cmd += list(extra_args)
        if resume_id is not None:
            cmd += ["--resume", resume_id]
        try:
            proc = subprocess.run(
                cmd, cwd=cwd, timeout=timeout, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.TimeoutExpired:
            return False, "%s turn timed out after %d s" % (stage, timeout), None
        except OSError as exc:
            return False, "%s turn could not start: %s" % (stage, exc), None

        stdout = proc.stdout or ""
        path = os.path.join(out, "%s-turn%d.json" % (stage, turn_index))
        try:
            os.makedirs(out, exist_ok=True)
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(stdout)
        except OSError:
            pass

        if proc.returncode != 0:
            tail = (proc.stderr or stdout).strip().splitlines()
            detail = tail[-1][:200] if tail else "no CLI diagnostics"
            return (False,
                    "%s session exited %d: %s" % (stage, proc.returncode, detail),
                    None)
        return True, None, _session_id(stdout)

    return runner


def _session_id(text):
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        return None
    if isinstance(data, dict):
        sid = data.get("session_id")
        if isinstance(sid, str) and sid:
            return sid
    return None


# ---------------------------------------------------------------------------
# The two drives
# ---------------------------------------------------------------------------

def drive_stages(clone, out, feedback, runner_factory=None, gh_fn=None,
                 claude_bin="claude", max_resumes=MAX_RESUMES,
                 timeout=TIMEOUT):
    """Drive `/s:plan` in the clone, then `/s:build` in the worktree the plan
    produced, and write `<out>/result.json`.

    Both drives go through `session_driver.drive` with `autopilot`'s own canned
    reply and grades — one driving idiom, shared with the epic autopilot.
    `runner_factory(out, stage) -> runner` is the injectable seam tests use to
    drive the loop without a live session.

    Returns the result payload (also written to `<out>/result.json`)."""
    engine = load_engine(clone)
    sd = engine.session_driver
    reply = engine.autopilot.GOAHEAD_REPLY
    gh_fn = gh_fn or default_gh

    extra_args = ["--plugin-dir", os.path.join(clone, "plugins", "s"),
                  "--permission-mode", "bypassPermissions"]
    if runner_factory is None:
        def runner_factory(out_dir, stage):
            return make_runner(out_dir, stage, claude_bin=claude_bin,
                               extra_args=extra_args, timeout=timeout)

    result = {"change": "", "pr_url": "", "plan_session_id": "",
              "build_session_id": "", "failure": ""}

    plan_prompt = (PLAN_PROMPT % feedback) + " " + reply
    ok, session_id, failure = sd.drive(
        plan_prompt, clone, lambda: plan_grade(clone) is not None, reply,
        max_resumes=max_resumes, timeout=timeout,
        runner=runner_factory(out, "plan"))
    result["plan_session_id"] = session_id or ""

    name = plan_grade(clone)
    if not ok or not name:
        result["failure"] = "plan stage: " + (
            failure or "no change reached Status: ready")
        return _write_result(out, result)
    result["change"] = name

    worktree = os.path.join(clone, ".worktrees", name)
    build_prompt = (BUILD_PROMPT % name) + " " + reply
    ok, session_id, failure = sd.drive(
        build_prompt, worktree,
        lambda: build_grade(worktree, name, gh_fn) is not None, reply,
        max_resumes=max_resumes, timeout=timeout,
        runner=runner_factory(out, "build"))
    result["build_session_id"] = session_id or ""

    pr_url = build_grade(worktree, name, gh_fn)
    if not ok or not pr_url:
        result["failure"] = "build stage: " + (
            failure or "the change opened no draft PR")
        return _write_result(out, result)

    result["pr_url"] = pr_url
    return _write_result(out, result)


def _write_result(out, result):
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "result.json"), "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    return result


def main(argv=None, runner_factory=None, gh_fn=None):
    args = build_parser().parse_args(argv)
    gh_fn = gh_fn or default_gh
    try:
        _ws_dir, clone = clone_layout(
            args.workspace, args.repo, args.repo_path, root=args.root,
            gh_fn=gh_fn, clone_from=args.clone_from, ref=args.ref)
        result = drive_stages(clone, args.out, args.feedback,
                              runner_factory=runner_factory, gh_fn=gh_fn)
    except EntryError as exc:
        sys.stderr.write("Error: %s\n" % exc)
        _write_result(args.out, {"change": "", "pr_url": "",
                                 "plan_session_id": "", "build_session_id": "",
                                 "failure": str(exc)})
        return 1
    if result.get("pr_url"):
        print(result["pr_url"])
        return 0
    sys.stderr.write("Error: %s\n" % result.get("failure", "the run failed"))
    return 1


if __name__ == "__main__":
    sys.exit(main())
