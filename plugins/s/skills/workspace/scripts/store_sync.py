#!/usr/bin/env python3
"""store_sync.py — the session-boundary hook that keeps a workspace or
external store's git checkout in sync with its upstream (shipd-wiki
store-sync-hook).

Registered on both ``SessionStart`` and ``SessionEnd``. On ``SessionStart`` it
integrates the store's upstream (:func:`integrate`: fetch, then nothing, a
fast-forward merge, or — when the store has diverged — a rebase of the local
commits onto the upstream with the working tree autostashed, aborted on a
conflict), then pushes any local commits; on ``SessionEnd`` it only pushes. Any other event — or a payload
naming none — exits 0 having run no git at all. It never touches the *working*
repository — only a resolved workspace or external store, and only while the
resolved ``store_sync`` key (shipd-config store-sync-keys) is true.

Run as ``store_sync.py --delayed <store> --delay <n>`` it is instead the
delayed push the engine starts, detached, after every store auto-commit
(shipd-wiki store-push-debounce): it reads no stdin, records a unique token
in ``<tempdir>/shipd-store-push-<digest>.token``, sleeps ``<n>`` seconds, and
exits having run no git when a later helper has replaced the token — so a
burst of writes ends in one push. Otherwise it integrates the upstream and
pushes. The engine already applied the ``store_sync`` gate before starting it.

This script lives outside ``plugins/s/skills/build/scripts/`` (the engine's
stdlib-only, no-network zone per ``.shipd/constitution.md``), mirroring the
``voice_digest.py`` precedent: it imports the engine's ``spec_common`` lazily
for config and store resolution, but is itself the one surface allowed to
reach the network.

**Fail-soft, always.** Every failure path — the key resolves false, no store
resolves, the store is the repo-local fallback, the store is not inside a git
work tree, it carries no ``origin`` remote, the upstream is missing, the
rebase conflicts (and is aborted), a push is rejected, a git call times out,
or configuration resolution itself fails — prints at most one warning line to
stderr and the script still exits 0. Session start/end must never break
because of this script.

Every git call carries a 20-second timeout and runs with
``GIT_TERMINAL_PROMPT=0``, so a missing credential fails fast.
"""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD_SCRIPTS = os.path.normpath(
    os.path.join(HERE, "..", "..", "build", "scripts"))

GIT_TIMEOUT = 20


class _SkipSync(Exception):
    """Raised internally to signal a silent, no-warning no-op — one of the
    ordinary not-applicable cases the requirement enumerates (disabled,
    unresolvable store, fallback store, non-git, no origin)."""


def _git_env():
    """A copy of the environment with ``GIT_TERMINAL_PROMPT=0``, so a missing
    credential fails fast instead of waiting on a prompt nobody will see."""
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def _one_line(text):
    """Collapse git's (possibly multi-line, hint-laden) output to one line,
    so a failure still prints at most one warning line."""
    lines = [line.strip() for line in (text or "").splitlines()
             if line.strip() and not line.lstrip().startswith("hint:")]
    return "; ".join(lines)


def _run(args, timeout=GIT_TIMEOUT):
    """Run a git command, raising ``RuntimeError`` naming it on any failure —
    a nonzero exit, a timeout, or an ``OSError`` starting the process."""
    try:
        result = subprocess.run(
            args, capture_output=True, text=True, timeout=timeout,
            env=_git_env())
    except subprocess.TimeoutExpired:
        raise RuntimeError("%s timed out" % " ".join(args))
    except OSError as exc:
        raise RuntimeError("%s: %s" % (" ".join(args), exc))
    if result.returncode != 0:
        detail = _one_line(result.stderr or result.stdout) or "failed"
        raise RuntimeError("%s: %s" % (" ".join(args), detail))
    return result


def _is_ancestor(store, ancestor, descendant):
    """Return whether ``ancestor`` is an ancestor of ``descendant``, from
    ``git merge-base --is-ancestor`` (exit 0 yes, exit 1 no). Any other
    outcome raises ``RuntimeError``."""
    args = ["git", "-C", store, "merge-base", "--is-ancestor",
            ancestor, descendant]
    try:
        result = subprocess.run(
            args, capture_output=True, text=True, timeout=GIT_TIMEOUT,
            env=_git_env())
    except subprocess.TimeoutExpired:
        raise RuntimeError("%s timed out" % " ".join(args))
    except OSError as exc:
        raise RuntimeError("%s: %s" % (" ".join(args), exc))
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    raise RuntimeError("%s: %s" % (
        " ".join(args), _one_line(result.stderr) or "failed"))


def _engine():
    """Import the engine's ``spec_common`` lazily, raising ``RuntimeError``
    when it cannot be imported."""
    if BUILD_SCRIPTS not in sys.path:
        sys.path.insert(0, BUILD_SCRIPTS)
    try:
        import spec_common
    except ImportError as exc:
        raise RuntimeError("engine unavailable: %s" % exc)
    return spec_common


def _has_origin_remote(store):
    try:
        result = subprocess.run(
            ["git", "-C", store, "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=GIT_TIMEOUT,
            env=_git_env())
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
    spec_common = _engine()
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


def integrate(store):
    """Bring the store's upstream into its current branch (shipd-wiki
    store-sync-hook).

    Fetch the remote the branch's upstream actually tracks — not a hardcoded
    ``origin``, or a branch tracking another remote would integrate a ref the
    fetch never refreshed. Then: change nothing when the upstream is already
    an ancestor of ``HEAD``; ``merge --ff-only`` when ``HEAD`` is an ancestor
    of the upstream (no local commits of its own); otherwise rebase the local
    commits onto the upstream with ``--autostash``, so uncommitted work
    survives. The merge or rebase runs under the engine's store commit lock,
    so it never races an engine auto-commit. A failed rebase is aborted —
    restoring the branch and working tree — and raises ``RuntimeError``, so
    the caller pushes nothing."""
    _run(["git", "-C", store, "fetch", _upstream_remote(store)])
    if _is_ancestor(store, "@{u}", "HEAD"):
        return
    spec_common = _engine()
    with spec_common.store_commit_lock(store):
        if _is_ancestor(store, "HEAD", "@{u}"):
            _run(["git", "-C", store, "merge", "--ff-only", "@{u}"])
            return
        try:
            _run(["git", "-C", store, "rebase", "--autostash", "@{u}"])
        except RuntimeError as exc:
            try:
                _run(["git", "-C", store, "rebase", "--abort"])
            except RuntimeError:
                pass
            raise RuntimeError("rebase onto upstream failed, aborted: %s"
                               % exc)


def sync_session_start(store):
    """Integrate the store's upstream (:func:`integrate`), then push any
    local commits."""
    integrate(store)
    _run(["git", "-C", store, "push"])


def sync_session_end(store):
    """Push any local commits."""
    _run(["git", "-C", store, "push"])


def _token_path(store):
    """The debounce token file for ``store``: in the system temp directory,
    named by the same 16-hex digest of the store's absolute path that the
    engine's store commit lock uses."""
    digest = hashlib.sha256(
        os.path.abspath(store).encode("utf-8")).hexdigest()[:16]
    return os.path.join(
        tempfile.gettempdir(), "shipd-store-push-%s.token" % digest)


def _write_token(path, token):
    """Write ``token`` to ``path`` atomically, through a temp file in the
    same directory and ``os.replace``."""
    fd, tmp = tempfile.mkstemp(
        dir=os.path.dirname(path), prefix=".shipd-store-push-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(token)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _read_token(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read().strip()
    except OSError:
        return None


def _parse_delayed(argv):
    """Return ``(store, delay)`` when ``argv`` carries
    ``--delayed <store> --delay <n>``, else None. A malformed delay falls
    back to the 60-second default; a negative one to 0."""
    if "--delayed" not in argv:
        return None
    try:
        store = argv[argv.index("--delayed") + 1]
    except IndexError:
        return None
    delay = 60
    if "--delay" in argv:
        try:
            delay = max(0, int(argv[argv.index("--delay") + 1]))
        except (IndexError, ValueError):
            delay = 60
    return store, delay


def run_delayed(store, delay):
    """The delayed push (shipd-wiki store-push-debounce): record a unique
    token, wait ``delay`` seconds, and exit having run no git when a later
    helper for the same store has since replaced the token — so a burst of
    writes ends in one push after the last write. Otherwise, when ``store``
    sits inside a git work tree with an ``origin`` remote, integrate the
    upstream (:func:`integrate`) and push. Any failure leaves the store's
    commits in place for the next attempt. Always returns 0."""
    token = "%d-%d" % (os.getpid(), time.time_ns())
    path = _token_path(store)
    try:
        _write_token(path, token)
    except OSError:
        return 0
    if delay:
        time.sleep(delay)
    if _read_token(path) != token:
        return 0
    try:
        spec_common = _engine()
        if not spec_common.inside_git_work_tree(store):
            return 0
        if not _has_origin_remote(store):
            return 0
        integrate(store)
        _run(["git", "-C", store, "push"])
    except Exception as exc:
        sys.stderr.write("warning: store push skipped: %s\n" % exc)
    return 0


def _read_payload():
    try:
        payload = json.loads(sys.stdin.read())
    except (ValueError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def main():
    delayed = _parse_delayed(sys.argv[1:])
    if delayed is not None:
        return run_delayed(*delayed)
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
