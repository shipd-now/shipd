#!/usr/bin/env python3
"""spike.py — the host launcher for the Apple `container` spike.

Loads the shipd workspace and this repo into a Linux VM run by Apple's
`container` CLI, and drives one piece of user feedback through headless
`/s:plan` and `/s:build` sessions to a draft pull request.

The launcher never writes into the checkouts it carries: the workspace root,
the repo, and the repo's main checkout are mounted **read-only**, and the in-VM
entry script (`tools/container/entry.py`) clones them. Only the run directory
is writable, and it is where the VM leaves `result.json` and the turn
transcripts.

Usage:

    tools/container/spike.py [--dry-run] "<the user feedback>"

Exit codes: 0 the run produced a PR (or a dry run printed its plan), 1 the run
produced no PR, 2 a preflight check failed (each reported as
`Error: <what> — <remedy>`).

Standard library only.
"""

import argparse
import datetime
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# The repo this launcher ships in: `tools/container/` is two levels down.
REPO_ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, "..", ".."))
DOCKERFILE = os.path.join(SCRIPT_DIR, "Dockerfile")

# The build's argv is relative to the repo root, which is also the build's cwd,
# so the printed command reads exactly as a human would type it.
DOCKERFILE_REL = os.path.join("tools", "container", "Dockerfile")
CONTEXT_REL = os.path.join("tools", "container")

CONFIG_FILENAME = ".shipd-config.json"

# In-VM paths. The mounts are read-only; /out is the run directory.
WORKSPACE_MOUNT = "/mnt/workspace"
REPO_MOUNT = "/mnt/repo"
# The repo's *main* checkout, mounted alongside the repo: a linked worktree's
# `.git` is a file naming a host path, so it is useless as a clone source
# inside the VM. The clone is taken from this mount and checked out at the
# worktree's own ref.
MAIN_MOUNT = "/mnt/main"
OUT_MOUNT = "/out"
ENTRY_IN_VM = REPO_MOUNT + "/tools/container/entry.py"

RELEASES_URL = "https://github.com/apple/container/releases"

# The token variables passed through by name — never by value, so no secret
# reaches the argv or this process's output.
TOKEN_VARS = ("GH_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_API_KEY")


def _escapes(relative):
    """True when a relative path leaves the directory it was computed against."""
    return relative == os.pardir or relative.startswith(os.pardir + os.sep)


class PreflightError(Exception):
    """A failed preflight check: reported as `Error: <what> — <remedy>`, exit 2."""

    def __init__(self, what, remedy):
        super().__init__("%s — %s" % (what, remedy))


# ---------------------------------------------------------------------------
# Image tag
# ---------------------------------------------------------------------------

def image_tag(dockerfile=DOCKERFILE):
    """The image tag: `shipd-runner:` plus the first 12 hex characters of the
    SHA-256 of the Dockerfile, so any edit to the image re-tags and rebuilds."""
    with open(dockerfile, "rb") as handle:
        digest = hashlib.sha256(handle.read()).hexdigest()
    return "shipd-runner:" + digest[:12]


# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------

def _run(cmd, cwd=None):
    """Run `cmd`; return `(returncode, stdout, stderr)`. A missing executable
    surfaces as a non-zero code rather than an exception."""
    try:
        proc = subprocess.run(cmd, cwd=cwd, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as exc:
        return 127, "", str(exc)
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def _git_toplevel(path):
    rc, out, _err = _run(["git", "-C", path, "rev-parse", "--show-toplevel"])
    if rc != 0:
        return None
    return os.path.realpath(out.strip()) if out.strip() else None


def main_checkout(repo):
    """The repo's **main checkout**: the parent of `git rev-parse
    --git-common-dir`.

    For an ordinary checkout this is the repo itself. For a linked worktree
    (`.worktrees/<change>`) it is the checkout the worktree belongs to — which
    is the path the workspace registers, and therefore the path the clone must
    be nested at inside the VM. The worktree itself is still what gets mounted
    and cloned, so the VM builds on that branch."""
    rc, out, _err = _run(["git", "-C", repo, "rev-parse", "--git-common-dir"])
    common = out.strip()
    if rc != 0 or not common:
        return os.path.realpath(repo)
    if not os.path.isabs(common):
        common = os.path.join(repo, common)
    return os.path.realpath(os.path.dirname(os.path.abspath(common)))


def _git_config(path, key):
    rc, out, _err = _run(["git", "-C", path, "config", key])
    return out.strip() if rc == 0 else ""


def default_workspace(repo_root):
    """The nearest ancestor **above** `repo_root` whose `.shipd-config.json`
    declares a `workspace` — the workspace root the repo is a member of."""
    current = os.path.dirname(os.path.realpath(repo_root))
    while True:
        config = os.path.join(current, CONFIG_FILENAME)
        if os.path.isfile(config):
            try:
                with open(config, "r", encoding="utf-8") as handle:
                    data = json.load(handle)
            except (OSError, ValueError):
                data = None
            if isinstance(data, dict) and "workspace" in data:
                return current
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent


def preflight(workspace, repo, env):
    """Run every check, in order, and return the preflight facts the run needs:
    `(workspace, repo, repo_path, token_vars, git_identity, ref)`.

    `ref` is the repo's current branch name, or its `HEAD` sha when the
    checkout is detached — what the in-VM clone must check out, since the clone
    is taken from the main checkout rather than from the repo itself.

    Raises :class:`PreflightError` on the first failure, before anything is
    built or run."""
    if shutil.which("container") is None:
        raise PreflightError(
            "Apple's `container` CLI is not on PATH",
            "install the signed package from %s, then run `container system "
            "start`" % RELEASES_URL)

    rc, _out, err = _run(["container", "system", "status"])
    if rc != 0:
        raise PreflightError(
            "the `container` service is not running (%s)"
            % (err.strip().splitlines()[-1] if err.strip() else "exit %d" % rc),
            "run `container system start`")

    if not env.get("GH_TOKEN"):
        raise PreflightError(
            "GH_TOKEN is not set, so the VM cannot reach GitHub",
            "export a token with `export GH_TOKEN=$(gh auth token)`")

    tokens = [name for name in TOKEN_VARS if env.get(name)]
    if not ({"CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_API_KEY"} & set(tokens)):
        raise PreflightError(
            "neither CLAUDE_CODE_OAUTH_TOKEN nor ANTHROPIC_API_KEY is set, so "
            "the VM cannot authenticate Claude Code",
            "run `claude setup-token` and export the result as "
            "CLAUDE_CODE_OAUTH_TOKEN")

    repo = os.path.realpath(repo)

    name = _git_config(repo, "user.name")
    email = _git_config(repo, "user.email")
    if not name or not email:
        raise PreflightError(
            "git has no commit identity (user.name / user.email)",
            "set one with `git config --global user.name <name>` and "
            "`git config --global user.email <email>`")

    if workspace is None:
        raise PreflightError(
            "no workspace root was found above the repo",
            "pass `--workspace <path>` naming the directory that holds %s"
            % CONFIG_FILENAME)
    workspace = os.path.realpath(workspace)

    if not os.path.isfile(os.path.join(workspace, CONFIG_FILENAME)):
        raise PreflightError(
            "the workspace root %s holds no %s" % (workspace, CONFIG_FILENAME),
            "pass `--workspace <path>` naming the workspace root")
    if _git_toplevel(workspace) != workspace:
        raise PreflightError(
            "the workspace root %s is not a git repository root" % workspace,
            "the entry script clones the workspace, so it must be a checkout")

    if _git_toplevel(repo) != repo:
        raise PreflightError(
            "the repo %s is not a git repository root" % repo,
            "pass `--repo <path>` naming the checkout's top level")
    rc, origin, _err = _run(["git", "-C", repo, "remote", "get-url", "origin"])
    if rc != 0 or not origin.strip():
        raise PreflightError(
            "the repo %s has no `origin` remote" % repo,
            "add one with `git remote add origin <url>`")

    if _escapes(os.path.relpath(repo, workspace)):
        raise PreflightError(
            "the repo %s is not beneath the workspace root %s"
            % (repo, workspace),
            "pass `--workspace <path>` naming the root the repo sits under")

    # The clone nests at the *main* checkout's registered member path, so a
    # launcher run from a change worktree still lands at `shipd/shipd` rather
    # than `shipd/shipd/.worktrees/<change>`.
    main = main_checkout(repo)
    repo_path = os.path.relpath(main, workspace)
    if _escapes(repo_path):
        raise PreflightError(
            "the repo's main checkout %s is not beneath the workspace root %s"
            % (main, workspace),
            "pass `--workspace <path>` naming the root that checkout sits under")

    # The ref the clone must land on: the repo's branch, or — when the checkout
    # is detached — the sha its HEAD names.
    _rc, ref, _err = _run(["git", "-C", repo, "rev-parse", "--abbrev-ref",
                           "HEAD"])
    ref = ref.strip()
    if ref == "HEAD" or not ref:
        _rc, ref, _err = _run(["git", "-C", repo, "rev-parse", "HEAD"])
        ref = ref.strip()

    return workspace, repo, repo_path, tokens, (name, email), ref


# ---------------------------------------------------------------------------
# Image and run
# ---------------------------------------------------------------------------

def image_present(tag):
    """True when `container image list --quiet` already lists `tag`."""
    rc, out, _err = _run(["container", "image", "list", "--quiet"])
    if rc != 0:
        return False
    return tag in [line.strip() for line in out.splitlines() if line.strip()]


def build_image(tag):
    rc, out, err = _run(
        ["container", "build", "-t", tag, "-f", DOCKERFILE_REL, CONTEXT_REL],
        cwd=REPO_ROOT)
    if rc != 0:
        raise PreflightError(
            "the image build failed (exit %d): %s"
            % (rc, (err or out).strip().splitlines()[-1] if (err or out).strip()
               else "no output"),
            "run the build by hand to see its output: container build -t %s "
            "-f %s %s" % (tag, DOCKERFILE_REL, CONTEXT_REL))


def run_argv(tag, stamp, workspace, repo, repo_path, run_dir, tokens,
             identity, feedback, cpus, memory, ref=None):
    """The full `container run` argv the launcher invokes.

    Both the repo and its main checkout are mounted: the repo carries the entry
    script and, for a plain checkout, is the main checkout itself, while the
    clone is always taken from `/mnt/main` and checked out at `ref` — a linked
    worktree's `.git` file names a host path no VM can resolve."""
    name, email = identity
    main = main_checkout(repo)
    argv = [
        "container", "run", "--rm",
        "--name", "shipd-spike-%s" % stamp,
        "--cpus", str(cpus),
        "--memory", memory,
        "--mount", "type=bind,source=%s,target=%s,readonly"
                   % (workspace, WORKSPACE_MOUNT),
        "--mount", "type=bind,source=%s,target=%s,readonly" % (repo, REPO_MOUNT),
        "--mount", "type=bind,source=%s,target=%s,readonly" % (main, MAIN_MOUNT),
        "--mount", "type=bind,source=%s,target=%s" % (run_dir, OUT_MOUNT),
    ]
    for var in tokens:
        argv += ["-e", var]
    argv += [
        "-e", "GIT_AUTHOR_NAME=%s" % name,
        "-e", "GIT_AUTHOR_EMAIL=%s" % email,
        "-e", "GIT_COMMITTER_NAME=%s" % name,
        "-e", "GIT_COMMITTER_EMAIL=%s" % email,
        "-w", "/workspace",
        tag,
        "python3", ENTRY_IN_VM,
        "--workspace", WORKSPACE_MOUNT,
        "--repo", REPO_MOUNT,
        "--repo-path", repo_path,
        "--clone-from", MAIN_MOUNT,
    ]
    if ref:
        argv += ["--ref", ref]
    argv += [
        "--out", OUT_MOUNT,
        "--feedback", feedback,
    ]
    return argv


def read_result(run_dir):
    """The run's `result.json` as a dict, or `None` when it is absent or
    unreadable — an absent result is a failed run, not a crash."""
    path = os.path.join(run_dir, "result.json")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        description="Drive one piece of user feedback to a draft PR inside an "
                    "Apple `container` VM.")
    parser.add_argument("feedback", help="the user feedback to plan and build")
    parser.add_argument("--dry-run", action="store_true",
                        help="preflight and print the plan; build and run "
                             "nothing")
    parser.add_argument("--workspace", default=None,
                        help="the workspace root (default: the nearest "
                             "ancestor declaring a workspace)")
    parser.add_argument("--repo", default=REPO_ROOT,
                        help="the repo checkout to load (default: this one)")
    parser.add_argument("--run-dir", default=None,
                        help="where the run's artifacts land (default: "
                             "~/.shipd/container/runs/<stamp>)")
    parser.add_argument("--cpus", default=4, type=int,
                        help="CPUs given to the VM (default: 4)")
    parser.add_argument("--memory", default="8G",
                        help="memory given to the VM (default: 8G)")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    env = os.environ

    workspace = args.workspace or default_workspace(args.repo)
    try:
        workspace, repo, repo_path, tokens, identity, ref = preflight(
            workspace, args.repo, env)
    except PreflightError as exc:
        sys.stderr.write("Error: %s\n" % exc)
        return 2

    tag = image_tag()
    needs_build = not image_present(tag)

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ")
    run_dir = args.run_dir or os.path.join(
        os.path.expanduser("~"), ".shipd", "container", "runs", stamp)
    run_dir = os.path.abspath(run_dir)

    if args.dry_run:
        argv_preview = run_argv(
            tag, stamp, workspace, repo, repo_path, run_dir, tokens, identity,
            args.feedback, args.cpus, args.memory, ref)
        print("tag: %s" % tag)
        print("build-needed: %s" % ("yes" if needs_build else "no"))
        print("run-dir: %s" % run_dir)
        print("run: %s" % shlex.join(argv_preview))
        return 0

    os.makedirs(run_dir, exist_ok=True)

    if needs_build:
        print("Building %s ..." % tag)
        try:
            build_image(tag)
        except PreflightError as exc:
            sys.stderr.write("Error: %s\n" % exc)
            return 2

    print("Running %s in %s ..." % (tag, run_dir))
    cmd = run_argv(tag, stamp, workspace, repo, repo_path, run_dir, tokens,
                   identity, args.feedback, args.cpus, args.memory, ref)
    rc = subprocess.call(cmd)

    result = read_result(run_dir)
    if result is None:
        sys.stderr.write(
            "Error: the run wrote no readable %s (container exited %d) — "
            "inspect the turn transcripts under %s\n"
            % (os.path.join(run_dir, "result.json"), rc, run_dir))
        return 1

    pr_url = (result.get("pr_url") or "").strip()
    if not pr_url:
        failure = (result.get("failure") or "the run reported no failure "
                                            "detail").strip()
        sys.stderr.write("Error: the run opened no PR — %s\n" % failure)
        return 1

    print(pr_url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
