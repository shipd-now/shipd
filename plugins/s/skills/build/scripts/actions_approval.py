#!/usr/bin/env python3
"""actions_approval.py — read, and with ``allow`` set, the repository setting
"Allow GitHub Actions to create and approve pull requests"
(actions-approval actions-approval-setting).

With the setting off, GitHub refuses a review decision submitted under
``github.token``, so the CI reviewer's approval degrades to a comment.

Stdlib-only. Every GitHub call goes through one injectable runner
``run(args, stdin=None, cwd=None)`` returning ``(returncode, stdout, stderr)``,
so tests drive the module with a recording fake and never reach the network.
Bare invocation is read-only; ``allow`` writes only when the setting reads
``disabled``, and carries the ``default_workflow_permissions`` it just read
back unchanged so the write cannot loosen it.

Exit codes: ``0`` ok, ``1`` an unreadable setting under ``allow``, a failed
write, or a write that did not take, ``2`` bad usage.
"""

import argparse
import json
import os
import subprocess
import sys

ENDPOINT = "repos/{nwo}/actions/permissions/workflow"

# Seconds a single ``gh`` call may take before it reports as a failure.
GH_TIMEOUT = 30


def gh_run(args, stdin=None, cwd=None):
    """``(returncode, stdout, stderr)`` for ``gh <args...>``, bounded by
    :data:`GH_TIMEOUT`; a timeout or a missing ``gh`` reports as an ordinary
    failure."""
    try:
        proc = subprocess.run(["gh"] + list(args), input=stdin, cwd=cwd,
                              capture_output=True, text=True,
                              timeout=GH_TIMEOUT)
    except subprocess.TimeoutExpired:
        return (1, "", "gh timed out after %ds" % GH_TIMEOUT)
    except OSError as exc:
        return (1, "", str(exc))
    return (proc.returncode, proc.stdout, proc.stderr)


def read_setting(nwo, run):
    """``(state, default_perms)``: state is ``enabled``, ``disabled`` or
    ``unknown`` (a failed call or an unparseable answer); ``default_perms`` is
    the ``default_workflow_permissions`` value read, or ``None``."""
    code, out, _err = run(["api", ENDPOINT.format(nwo=nwo)])
    if code != 0:
        return ("unknown", None)
    try:
        data = json.loads(out)
    except ValueError:
        return ("unknown", None)
    if not isinstance(data, dict):
        return ("unknown", None)
    can = data.get("can_approve_pull_request_reviews")
    perms = data.get("default_workflow_permissions")
    if can is True:
        return ("enabled", perms)
    if can is False:
        return ("disabled", perms)
    return ("unknown", perms)


def enable(nwo, run):
    """Turn the setting on and re-read it: ``(ok, message)``. Writes only from
    ``disabled``; the read default permissions ride back unchanged."""
    state, perms = read_setting(nwo, run)
    if state == "enabled":
        return (True, "already enabled; nothing written")
    if state != "disabled" or not perms:
        return (False, "the setting could not be read; nothing written")
    body = json.dumps({"default_workflow_permissions": perms,
                       "can_approve_pull_request_reviews": True})
    code, _out, err = run(["api", "-X", "PUT", ENDPOINT.format(nwo=nwo),
                           "--input", "-"], stdin=body)
    if code != 0:
        return (False, "the write failed: %s" % (err.strip() or "exit %d" % code))
    after, _perms = read_setting(nwo, run)
    if after != "enabled":
        return (False, "the write was accepted but the setting still reads "
                       "%s; an organization policy can override the "
                       "repository" % after)
    return (True, "enabled")


def _resolve_repo(repo, root, run):
    if repo:
        return repo
    code, out, err = run(["repo", "view", "--json", "nameWithOwner", "-q",
                          ".nameWithOwner"], cwd=root)
    nwo = out.strip()
    if code != 0 or not nwo:
        raise RuntimeError("cannot resolve the repository: %s"
                           % (err.strip() or "gh repo view failed"))
    return nwo


def main(argv, run=gh_run, out=print):
    """Run ``actions_approval.py [allow] [--repo OWNER/NAME] [--root DIR]`` and
    return the exit code."""
    parser = argparse.ArgumentParser(
        prog="actions_approval.py",
        description="Report, or with `allow` set, the repository setting that "
                    "lets GitHub Actions create and approve pull requests. "
                    "Bare, it changes nothing.")
    parser.add_argument("action", nargs="?", choices=["allow"],
                        help="allow: enable the setting (default: report only)")
    parser.add_argument("--repo", help="OWNER/NAME (default: the repository "
                                       "`gh repo view` resolves from --root)")
    parser.add_argument("--root", default=os.getcwd(),
                        help="repository root (default: cwd)")
    try:
        opts = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2
    root = os.path.abspath(opts.root)
    try:
        nwo = _resolve_repo(opts.repo, root, run)
    except RuntimeError as exc:
        sys.stderr.write("Error: %s\n" % exc)
        return 1
    if opts.action != "allow":
        state, _perms = read_setting(nwo, run)
        out("actions-approve: %s" % state)
        return 0
    ok, message = enable(nwo, run)
    state, _perms = read_setting(nwo, run) if not ok else ("enabled", None)
    out("actions-approve: %s" % ("enabled" if ok else state))
    out(message)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
