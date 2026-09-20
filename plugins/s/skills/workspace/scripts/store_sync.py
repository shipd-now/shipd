#!/usr/bin/env python3
"""store_sync.py — the session-boundary hook that keeps a workspace or
external store's git checkout in sync with its upstream (shipd-wiki
store-sync-hook).

Registered on both ``SessionStart`` and ``SessionEnd``. On ``SessionStart`` it
fetches the store's upstream, fast-forward merges it, then pushes any local
commits; on ``SessionEnd`` it only pushes. Any other event — or a payload
naming none — exits 0 having run no git at all. It never touches the *working*
repository — only a resolved workspace or external store, and only while the
resolved ``store_sync`` key (shipd-config store-sync-keys) is true.

This script lives outside ``plugins/s/skills/build/scripts/`` (the engine's
stdlib-only, no-network zone per ``.shipd/constitution.md``), mirroring the
``voice_digest.py`` precedent: it imports the engine's ``spec_common`` lazily
for config and store resolution, but is itself the one surface allowed to
reach the network.

**Fail-soft, always.** Every failure path — the key resolves false, no store
resolves, the store is the repo-local fallback, the store is not inside a git
work tree, it carries no ``origin`` remote, the upstream is missing, the merge
is not a fast-forward, a push is rejected, a git call times out, or
configuration resolution itself fails — prints at most one warning line to
stderr and the script still exits 0. Session start/end must never break
because of this script.
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD_SCRIPTS = os.path.normpath(
    os.path.join(HERE, "..", "..", "build", "scripts"))

GIT_TIMEOUT = 20


class _SkipSync(Exception):
    """Raised internally to signal a silent, no-warning no-op — one of the
    ordinary not-applicable cases the requirement enumerates (disabled,
    unresolvable store, fallback store, non-git, no origin)."""


def _run(args, timeout=GIT_TIMEOUT):
    """Run a git command, raising ``RuntimeError`` naming it on any failure —
    a nonzero exit, a timeout, or an ``OSError`` starting the process."""
    try:
        result = subprocess.run(
            args, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise RuntimeError("%s timed out" % " ".join(args))
    except OSError as exc:
        raise RuntimeError("%s: %s" % (" ".join(args), exc))
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip() or "failed"
        raise RuntimeError("%s: %s" % (" ".join(args), detail))
    return result


def _has_origin_remote(store):
    try:
        result = subprocess.run(
            ["git", "-C", store, "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=GIT_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0 and bool(result.stdout.strip())


def resolve_store(start):
    """Return the store directory the hook should sync.

    Raises ``RuntimeError`` naming the problem on a genuine resolution
    failure (an unimportable engine, a malformed configuration layer) so the
    caller can warn once. Raises :class:`_SkipSync` for every ordinary
    not-applicable case the requirement enumerates, so the caller can exit 0
    printing nothing for those.
    """
    if BUILD_SCRIPTS not in sys.path:
        sys.path.insert(0, BUILD_SCRIPTS)
    try:
        import spec_common
    except ImportError as exc:
        raise RuntimeError("engine unavailable: %s" % exc)
    try:
        config, _provenance = spec_common.resolve_config(start)
    except spec_common.ConfigError as exc:
        raise RuntimeError("config: %s" % exc)
    if not spec_common.store_sync_enabled(config):
        raise _SkipSync()
    try:
        resolved = spec_common.resolve_wiki_root(start)
    except spec_common.ConfigError as exc:
        raise RuntimeError("config: %s" % exc)
    if resolved is None:
        raise _SkipSync()
    anchor, is_fallback = resolved
    if is_fallback:
        # The repo-local fallback store: never synced, so the hook can never
        # push a working repository's own branch (shipd-wiki store-sync-hook).
        raise _SkipSync()
    store = spec_common.wiki_dir(anchor)
    if not spec_common.inside_git_work_tree(store):
        raise _SkipSync()
    if not _has_origin_remote(store):
        raise _SkipSync()
    return store


def _upstream_remote(store):
    """The remote the current branch's upstream tracks, from
    ``git rev-parse --abbrev-ref @{u}`` (e.g. ``origin/main`` -> ``origin``).

    Raises ``RuntimeError`` when the branch has no upstream, so the caller
    warns once rather than fetching a remote the merge will not read."""
    ref = _run(
        ["git", "-C", store, "rev-parse", "--abbrev-ref", "@{u}"]
    ).stdout.strip()
    remote, _, _branch = ref.partition("/")
    if not remote or not _branch:
        raise RuntimeError("upstream %r names no remote" % ref)
    return remote


def sync_session_start(store):
    """Fetch the store's upstream, fast-forward merge it, then push any local
    commits.

    The fetch targets the remote the branch's upstream actually tracks, not a
    hardcoded ``origin`` — otherwise a branch tracking another remote would
    fast-forward onto a ref the fetch never refreshed."""
    _run(["git", "-C", store, "fetch", _upstream_remote(store)])
    _run(["git", "-C", store, "merge", "--ff-only", "@{u}"])
    _run(["git", "-C", store, "push"])


def sync_session_end(store):
    """Push any local commits."""
    _run(["git", "-C", store, "push"])


def _read_payload():
    try:
        payload = json.loads(sys.stdin.read())
    except (ValueError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def main():
    payload = _read_payload()
    event = payload.get("hook_event_name")
    start = payload.get("cwd")
    if not isinstance(start, str) or not start:
        start = os.getcwd()
    try:
        store = resolve_store(start)
    except _SkipSync:
        return 0
    except Exception as exc:
        sys.stderr.write("warning: store sync skipped: %s\n" % exc)
        return 0
    if event not in ("SessionStart", "SessionEnd"):
        # An unrecognized or absent event never reaches the network: the hook
        # is registered for exactly two, and a malformed payload must not be
        # read as a push request.
        return 0
    try:
        if event == "SessionStart":
            sync_session_start(store)
        else:
            sync_session_end(store)
    except Exception as exc:
        sys.stderr.write("warning: store sync skipped: %s\n" % exc)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # fail soft: never break session start/end
        sys.exit(0)
