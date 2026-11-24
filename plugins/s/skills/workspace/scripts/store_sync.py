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


def _stash_tip(store):
    """The commit ``refs/stash`` names, or ``None`` when the stash is empty."""
    try:
        return _run(["git", "-C", store, "rev-parse", "--quiet", "--verify",
                     "refs/stash"]).stdout.strip() or None
    except RuntimeError:
        return None


def _unmerged_paths(store):
    """The index's unmerged entries, as ``git ls-files --unmerged`` prints
    them; empty when the index carries no conflict."""
    return _run(
        ["git", "-C", store, "ls-files", "--unmerged"]).stdout.strip()


def _restore_after_autostash_conflict(store, before, stash_before):
    """Put the branch and working tree back as they were before a rebase
    whose autostash would not re-apply: reset to ``before`` — the conflicted
    tree holds nothing the stash entry does not — then, where the rebase left
    a new stash entry, apply it with its index state onto the commit it was
    made from and drop it. Raises ``RuntimeError`` when a step fails, leaving
    the work in the stash entry."""
    _run(["git", "-C", store, "reset", "--hard", before])
    if _stash_tip(store) not in (None, stash_before):
        _run(["git", "-C", store, "stash", "pop", "--index"])


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
    the caller pushes nothing. So does a rebase that succeeds but whose
    autostashed work no longer applies: git reports that one as success, so
    it is detected by its unmerged paths and undone
    (:func:`_restore_after_autostash_conflict`)."""
    _run(["git", "-C", store, "fetch", _upstream_remote(store)])
    if _is_ancestor(store, "@{u}", "HEAD"):
        return
    spec_common = _engine()
    with spec_common.store_commit_lock(store):
        if _is_ancestor(store, "HEAD", "@{u}"):
            _run(["git", "-C", store, "merge", "--ff-only", "@{u}"])
            return
        before = _run(["git", "-C", store, "rev-parse", "HEAD"]).stdout.strip()
        stash_before = _stash_tip(store)
        try:
            _run(["git", "-C", store, "rebase", "--autostash", "@{u}"])
        except RuntimeError as exc:
            try:
                _run(["git", "-C", store, "rebase", "--abort"])
            except RuntimeError:
                pass
            raise RuntimeError("rebase onto upstream failed, aborted: %s"
                               % exc)
        if _unmerged_paths(store):
            # The rebase itself succeeded, but git could not re-apply the
            # autostashed work on top of it: it exits 0 all the same, leaving
            # conflict markers in the tree and the work in a stash entry.
            # Undo the rebase and put the work back where it was.
            _restore_after_autostash_conflict(store, before, stash_before)
            raise RuntimeError(
                "rebase onto upstream conflicts with uncommitted work, "
                "undone")


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
    named by a 16-hex digest of the store's absolute path. The engine passes
    the store's repository root, so every write into one repository shares
    the token. Its body is ``"<id> <deadline>"``: a unique id and the epoch
    time after which the push may run (:func:`_token_deadline`)."""
    digest = hashlib.sha256(
        os.path.abspath(store).encode("utf-8")).hexdigest()[:16]
    return os.path.join(
        tempfile.gettempdir(), "shipd-store-push-%s.token" % digest)


# The waiter lock beside the token file: its holder refreshes it at least
# every _LOCK_REFRESH seconds, and a lock left unrefreshed for _LOCK_STALE
# seconds counts as abandoned and is taken over.
_LOCK_REFRESH = 10
_LOCK_STALE = 60


def _lock_path(store):
    """The waiter lock file for ``store``: the token path with ``.token``
    replaced by ``.lock``."""
    path = _token_path(store)
    return path[:-len(".token")] + ".lock"


def _token_deadline(body):
    """The push deadline in a token body: the float after the last space, or
    None when ``body`` is missing or malformed."""
    if not body or " " not in body:
        return None
    try:
        return float(body.rsplit(" ", 1)[1])
    except ValueError:
        return None


def _create_lock(path, ident):
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(ident)


def _claim_lock(path, ident):
    """Claim the waiter lock at ``path`` for ``ident`` by exclusive create.
    A lock whose mtime is older than ``_LOCK_STALE`` seconds (or that
    vanished meanwhile) is removed and the create tried once more. Return
    whether this helper now holds the lock; a fresh lock returns False."""
    try:
        _create_lock(path, ident)
        return True
    except FileExistsError:
        pass
    try:
        stale = time.time() - os.stat(path).st_mtime > _LOCK_STALE
    except FileNotFoundError:
        stale = True
    if not stale:
        return False
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass
    try:
        _create_lock(path, ident)
        return True
    except FileExistsError:
        return False


def _holds_lock(path, ident):
    """Whether the lock file at ``path`` carries ``ident``."""
    return _read_token(path) == ident


def _release_lock(path, ident):
    """Remove the lock file at ``path`` only while ``ident`` holds it."""
    if _holds_lock(path, ident):
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass


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
    """The delayed push (shipd-wiki store-push-debounce). Record a unique
    token with a push deadline ``delay`` seconds from now, then claim the
    waiter lock beside the token file; a helper that finds a live lock exits
    having run no git, so at most one helper waits per repository. The lock
    holder waits until the token's deadline passes, re-reading the token so a
    later write extends the wait and refreshing the lock while it waits. It
    then releases the lock; when the token changed after its last read, it
    claims the lock again and keeps waiting, or exits when another helper now
    holds it. Otherwise, when ``store`` sits inside a git work tree with an
    ``origin`` remote, it integrates the upstream (:func:`integrate`) and
    pushes. Any failure leaves the store's commits in place for the next
    attempt. Always returns 0."""
    ident = "%d-%d" % (os.getpid(), time.time_ns())
    path = _token_path(store)
    lock = _lock_path(store)
    try:
        _write_token(path, "%s %r" % (ident, time.time() + delay))
    except OSError:
        return 0
    if not _claim_lock(lock, ident):
        return 0
    try:
        while True:
            while True:
                seen = _read_token(path)
                deadline = _token_deadline(seen)
                remaining = (deadline - time.time()
                             if deadline is not None else 0)
                if remaining <= 0:
                    break
                time.sleep(min(remaining, _LOCK_REFRESH))
                if not _holds_lock(lock, ident):
                    return 0
                try:
                    os.utime(lock)
                except OSError:
                    return 0
            _release_lock(lock, ident)
            if _read_token(path) == seen:
                break
            if not _claim_lock(lock, ident):
                return 0
    finally:
        _release_lock(lock, ident)
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
