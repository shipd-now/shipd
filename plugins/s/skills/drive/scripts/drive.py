#!/usr/bin/env python3
"""drive.py — the stdlib-only control CLI for `/s:drive` (drive-doctor,
drive-targets-config, drive-auth-cache, drive-session, drive-verdict,
drive-recording, drive-postprocess, drive-brand-frames).

This script holds every decision the skill makes — config resolution, auth
recipes, cache TTL, the doctor table, the verdict rules, the ffmpeg graphs —
so the CI suite under `plugins/s/skills/drive/tests/` exercises it with no
Playwright installed at all, exactly as
`plugins/s/skills/video-ingest/tests/_stubs.py` stubs `ffmpeg` and `uv` on
PATH for `video_ingest.py`. All browser I/O lives in the Playwright workers
this script shells out to through `uv run` — `browser_worker.py` and
`record_worker.py` — which are the only files in this tree allowed to import
`playwright`; nothing in this module ever does.

A fatal error is reported as one ``Error: <reason>`` line on stderr with a
non-zero exit; an unknown or missing verb prints usage on stderr and exits 2
(cli-conventions' `error-output-convention` shape, followed here by
convention though `drive.py` is not one of that requirement's named CLIs).
"""

import argparse
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import postprocess as pp  # noqa: E402 - stdlib-only sibling, same split as drive.py


class DriveError(Exception):
    """A user-facing error: printed as ``Error: ...`` to stderr, exit 1."""


# --- private-directory helper ---------------------------------------------


def _ensure_private_dir(path):
    """Create `path` (and any missing parents) and guarantee it ends up
    owner-only (`0700`) — the session socket, and every credential-bearing
    file under `~/.shipd/drive/`, must never sit inside a world-readable or
    world-traversable directory (the auth cache holds live session cookies;
    the session socket is an unauthenticated, arbitrary-JS-eval remote into
    a logged-in browser).

    `os.makedirs(..., mode=..., exist_ok=True)` only applies `mode` to a
    directory it actually creates — an already-existing directory (e.g. one
    left behind, world-readable, by a version of this script that predates
    this fix) keeps whatever mode it already had. So this always `chmod`s
    `path` to `0o700` after `makedirs`, regardless of whether this call
    created it or found it already there."""
    os.makedirs(path, mode=0o700, exist_ok=True)
    os.chmod(path, 0o700)


# --- shared tool-presence helpers ---------------------------------------


def have(tool):
    return shutil.which(tool) is not None


def playwright_browsers_dir():
    """The directory Playwright itself resolves its downloaded browsers
    into: the `PLAYWRIGHT_BROWSERS_PATH` environment variable when set (a
    real Playwright override, not a drive-only invention), falling back to
    its per-OS default cache location otherwise."""
    override = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if override:
        return override
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Caches/ms-playwright")
    if sys.platform.startswith("win"):
        base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        return os.path.join(base, "ms-playwright")
    return os.path.expanduser("~/.cache/ms-playwright")


def browser_installed():
    """Whether a Playwright chromium build is present, checked purely by
    filesystem presence under `playwright_browsers_dir()` — no `playwright`
    import required, so this stays true even with nothing installed."""
    d = playwright_browsers_dir()
    if not os.path.isdir(d):
        return False
    return any(name.startswith("chromium")
               for name in os.listdir(d))


# --- default (production) subprocess seam --------------------------------


def default_run(args, input=None, env=None):
    """Real subprocess runner: ``args`` is a full argv. Returns
    ``(rc, stdout, stderr)``. Mirrors `video_ingest.py`'s `default_run` seam
    so a test can substitute a fake with the same signature — used by
    `doctor --fix`'s browser install (drive-doctor) and the `login` verb's
    worker invocation (drive-auth-cache), never by presence checking
    itself, which reads `PATH`/`PLAYWRIGHT_BROWSERS_PATH` directly and so is
    already deterministic under a stubbed environment. ``env`` of ``None``
    (the default) inherits this process's own environment unchanged, exactly
    as a bare `subprocess.run` call would; passing a dict replaces it
    entirely, so a caller that wants to extend rather than replace passes
    ``dict(os.environ, **extra)`` itself (`worker_env_with_secrets` does
    exactly that)."""
    proc = subprocess.run(
        list(args), input=input, text=True, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc.returncode, proc.stdout or "", proc.stderr or ""


# --- doctor (dependency preflight) ---------------------------------------

# (name, always_required, check, remedy). `uv` and the Playwright browser
# binary are required for every verb (drive-doctor); `ffmpeg`/`ffprobe` are
# required for `record`/`post` only. Each `check` reports presence purely
# via `PATH` (`have`) or `PLAYWRIGHT_BROWSERS_PATH` (`browser_installed`),
# so the test suite controls presence entirely through the subprocess
# environment it launches `drive.py` with — no other injection needed for
# the report itself.
DOCTOR_TOOLS = [
    ("uv", True, lambda: have("uv"),
     "install uv (`brew install uv`), or see "
     "https://docs.astral.sh/uv/getting-started/installation/"),
    ("playwright browser", True, browser_installed,
     "install the Playwright browser binary — run `drive.py doctor --fix`"),
    ("ffmpeg", False, lambda: have("ffmpeg"),
     "install ffmpeg (`brew install ffmpeg`) — required for recording and "
     "post-processing only"),
    ("ffprobe", False, lambda: have("ffprobe"),
     "install ffmpeg, which provides ffprobe — required for recording and "
     "post-processing only"),
]


def doctor_report():
    """Evaluate `DOCTOR_TOOLS` and return `(rows, ok)`: `rows` is
    `(name, present, always_required, remedy)` in table order, and `ok` is
    False only when an always-required tool is missing (drive-doctor:
    "Exit non-zero only when an always-required tool is missing")."""
    rows = []
    ok = True
    for name, always_required, check, remedy in DOCTOR_TOOLS:
        present = bool(check())
        if always_required and not present:
            ok = False
        rows.append((name, present, always_required, remedy))
    return rows, ok


def print_doctor_report(rows):
    for name, present, always_required, remedy in rows:
        scope = "required" if always_required else "recording only"
        if present:
            print("  + %s (%s)" % (name, scope))
            continue
        print("  x %s — MISSING (%s): %s" % (name, scope, remedy))


def cmd_doctor(args, run=default_run):
    """`doctor` (drive-doctor): report every prerequisite's state and exit
    non-zero only when an always-required tool (`uv`, the Playwright
    browser) is missing. `--fix` additionally installs the missing browser
    binary through the Playwright worker and re-reports.

    `run` is the injectable subprocess seam (`default_run`'s signature) the
    `--fix` path uses to invoke `uv run browser_worker.py install-browser`,
    so a test can substitute a fake without touching the host toolchain —
    presence *reporting* itself never needs this seam, since it reads
    `PATH`/`PLAYWRIGHT_BROWSERS_PATH` directly.
    """
    rows, ok = doctor_report()

    if not args.fix:
        print_doctor_report(rows)
        if not ok:
            print("drive: required tool(s) missing. Re-run with --fix to "
                  "install what can be automated.", file=sys.stderr)
        return 0 if ok else 1

    # --fix installs only the Playwright browser binary — the one
    # always-required tool this CLI can automate; `uv` itself has no
    # automated remedy (drive-doctor names a manual install for it).
    already_present = browser_installed()
    if already_present:
        print("drive: doctor --fix performs no network access — the "
              "Playwright browser binary is already installed.")
    else:
        print("drive: doctor --fix will download the Playwright chromium "
              "browser binary over the network, via "
              "`uv run browser_worker.py install-browser`.")
        worker = os.path.join(HERE, "browser_worker.py")
        try:
            rc, out, err = run(["uv", "run", worker, "install-browser"])
        except OSError as exc:
            rc, out, err = 1, "", str(exc)
        if rc != 0:
            print_doctor_report(rows)
            print("drive: failed to install the Playwright browser binary: "
                  "%s" % (err.strip() or out.strip() or "unknown error"),
                  file=sys.stderr)
            return 1

    rows, ok = doctor_report()
    print_doctor_report(rows)
    if not ok:
        print("drive: required tool(s) still missing after --fix.",
              file=sys.stderr)
    return 0 if ok else 1


# --- target and credential resolution (drive-targets-config) -------------

USER_TARGETS_PATH = os.path.expanduser(
    os.path.join("~", ".shipd", "drive", "targets.json"))


def _build_scripts_dir():
    """Absolute path to the build skill's scripts/ — the established
    cross-skill engine import point (`video_ingest.py`'s
    `_build_scripts_dir`, itself following `semdiff.py`'s convention)."""
    return os.path.normpath(
        os.path.join(HERE, "..", "..", "build", "scripts"))


def content_dir(start="."):
    """The absolute content directory governing `start` (default: cwd) —
    `.shipd` unless the layered `.shipd-config.json` `dir` key (or an
    external `store_root`) says otherwise. Reached through the engine's own
    `spec_common.specs_dir`, the same cross-skill import point
    `video_ingest.py`'s `video_config` uses; falls back to `<start>/.shipd`
    when the engine cannot be imported at all, so target resolution never
    hard-fails on that detail."""
    try:
        build = _build_scripts_dir()
        if build not in sys.path:
            sys.path.insert(0, build)
        import spec_common as sc  # noqa: WPS433 - local import by design
        return sc.specs_dir(os.path.abspath(start))
    except Exception:  # noqa: BLE001 - resolution is best-effort
        return os.path.join(os.path.abspath(start), ".shipd")


def user_targets_path():
    return USER_TARGETS_PATH


def repo_targets_path(start="."):
    return os.path.join(content_dir(start), "drive", "targets.json")


def _read_targets_file(path):
    """The raw parsed contents of a targets.json file at `path`, or `None`
    when it does not exist. Invalid JSON is a fatal `DriveError` naming the
    file — a malformed config is never silently dropped from the merge."""
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError) as exc:
        raise DriveError("could not read %s: %s" % (path, exc))


def resolve_targets(start="."):
    """The merged targets configuration (drive-targets-config):
    `~/.shipd/drive/targets.json` as the base, overridden entry-by-entry —
    by target name — with `<content-dir>/drive/targets.json` when the
    repository ships one. Returns `(targets, meta)`: `targets` maps each
    target's name to its declared dict (`url`, `auth`, ...); `meta` carries
    the merged `default` and `authCacheTtlHours` top-level keys, with the
    repo-level file's value winning whenever it declares one."""
    user = _read_targets_file(user_targets_path()) or {}
    repo = _read_targets_file(repo_targets_path(start)) or {}

    targets = dict(user.get("targets") or {})
    for name, entry in (repo.get("targets") or {}).items():
        targets[name] = entry

    meta = {}
    for key in ("default", "authCacheTtlHours"):
        if key in repo:
            meta[key] = repo[key]
        elif key in user:
            meta[key] = user[key]
    return targets, meta


def get_target(name, targets):
    """The declared config dict for target `name` out of an already-resolved
    `targets` mapping, or a `DriveError` naming it when absent from both
    files (drive-targets-config: "an unknown target fails loudly")."""
    if name not in targets:
        raise DriveError("unknown target: %s" % name)
    return targets[name]


# --- auth recipes (drive-targets-config) ----------------------------------

# The environment variable names `browser_worker.py`'s `login` subcommand
# reads a resolved username/password from — never this process's argv, and
# never printed. Must match `browser_worker.py`'s
# `LOGIN_USERNAME_ENV`/`LOGIN_PASSWORD_ENV` exactly; duplicated here rather
# than imported, since `drive.py` never imports the Playwright-only worker
# module (the CLI split: `drive.py` is stdlib-only end to end).
LOGIN_USERNAME_ENV = "DRIVE_LOGIN_USERNAME"
LOGIN_PASSWORD_ENV = "DRIVE_LOGIN_PASSWORD"


def resolve_secret_command(argv, run=default_run):
    """The `command` auth recipe's one leg: run `argv` through `run` (the
    injectable subprocess seam) and return its stdout as the secret, with
    exactly one trailing newline stripped (drive-targets-config: "two argv
    arrays whose stdout is the secret, trailing newline stripped"). Raises
    `DriveError` naming the failed command on a non-zero exit — the secret
    value itself never appears in the error message, only the argv that
    failed to produce one, plus that command's own `stderr`. `stdout` is
    never included, even as a fallback when `stderr` is empty, since a
    credential helper that prints the secret and exits non-zero would put
    it exactly there; an empty `stderr` is reported as such rather than
    falling back to it."""
    rc, out, err = run(argv)
    if rc != 0:
        stderr_detail = err.strip()
        detail = stderr_detail if stderr_detail else \
            "the command produced no stderr output"
        raise DriveError(
            "auth command failed (%s): %s"
            % (" ".join(str(a) for a in argv), detail))
    if out.endswith("\n"):
        out = out[:-1]
    return out


def resolve_auth(entry, run=default_run):
    """Resolve a target's declared `auth` recipe into `(username,
    password)` (drive-targets-config):

    - `none` (the default when `auth` is absent) — `(None, None)`.
    - `env` — `auth["username"]`/`auth["password"]` name the two
      environment variables to read; missing either variable is a
      `DriveError`.
    - `command` — `auth["username"]`/`auth["password"]` are each a full
      argv array whose stdout (via `resolve_secret_command`) is the secret.

    Never writes a resolved secret anywhere but this function's return
    value — the caller (`worker_env_with_secrets`) is what keeps it out of
    a worker's argv and confined to its environment."""
    auth = entry.get("auth") or {"kind": "none"}
    kind = auth.get("kind", "none")

    if kind == "none":
        return None, None

    if kind == "env":
        username_var = auth.get("username")
        password_var = auth.get("password")
        if not username_var or not password_var:
            raise DriveError(
                "'env' auth recipe requires 'username' and 'password' "
                "environment variable names")
        username = os.environ.get(username_var)
        password = os.environ.get(password_var)
        if username is None or password is None:
            raise DriveError(
                "'env' auth requires %s and %s in the environment"
                % (username_var, password_var))
        return username, password

    if kind == "command":
        username_argv = auth.get("username")
        password_argv = auth.get("password")
        if not username_argv or not password_argv:
            raise DriveError(
                "'command' auth recipe requires 'username' and 'password' "
                "argv arrays")
        username = resolve_secret_command(username_argv, run=run)
        password = resolve_secret_command(password_argv, run=run)
        return username, password

    raise DriveError("unknown auth kind: %r" % (kind,))


def worker_env_with_secrets(username, password, base_env=None):
    """The environment a login worker subprocess should run with: a copy of
    `base_env` (default: this process's own `os.environ`) with the resolved
    `username`/`password` placed under the fixed variable names
    `browser_worker.py` reads them from — never in the worker's argv, and
    never printed anywhere (drive-targets-config: "pass resolved secrets to
    a worker through its environment only"). `username`/`password` of
    `None` (the `none` auth kind) leave the corresponding variable unset
    rather than set to an empty string."""
    env = dict(os.environ if base_env is None else base_env)
    if username is not None:
        env[LOGIN_USERNAME_ENV] = username
    if password is not None:
        env[LOGIN_PASSWORD_ENV] = password
    return env


def cmd_targets(args):
    """`targets` (drive-targets-config): print each resolved target's name,
    url, and auth kind — never a secret, and never a resolved credential
    value (only the kind, e.g. `env`, is printed; the `env`/`command`
    recipe's own variable names or argv are also withheld, since those can
    themselves hint at where a secret lives)."""
    targets, _meta = resolve_targets()
    for name in sorted(targets):
        entry = targets[name] or {}
        url = entry.get("url", "")
        auth = entry.get("auth") or {"kind": "none"}
        kind = auth.get("kind", "none")
        print("%s: %s (auth: %s)" % (name, url, kind))
    return 0


AUTH_CACHE_TTL_HOURS_KEY = "authCacheTtlHours"
DEFAULT_AUTH_CACHE_TTL_HOURS = 8


def auth_cache_dir():
    """`~/.shipd/drive/auth/` — the directory `login` writes/reuses cached
    storage state under (drive-auth-cache), sibling to the user-level
    targets file."""
    return os.path.join(os.path.dirname(USER_TARGETS_PATH), "auth")


def auth_cache_path(name):
    """`~/.shipd/drive/auth/<name>.json` — the cached storage-state path
    for target `name`."""
    return os.path.join(auth_cache_dir(), "%s.json" % name)


def _auth_cache_is_fresh(path, ttl_hours):
    """Whether the auth cache at `path` exists and its mtime is within
    `ttl_hours` of now (drive-auth-cache: "While that file exists and its
    modification time is within the resolved authCacheTtlHours ... the CLI
    SHALL reuse it")."""
    if not os.path.isfile(path):
        return False
    age_seconds = time.time() - os.path.getmtime(path)
    return age_seconds <= ttl_hours * 3600


def cmd_login(args, run=default_run):
    """`login` (drive-auth-cache): resolve the target and reuse its cached
    storage state under `auth_cache_path` while that file's mtime is inside
    the resolved `authCacheTtlHours` (default `DEFAULT_AUTH_CACHE_TTL_HOURS`
    hours) — performing no login at all in that case. Otherwise resolve the
    target's auth recipe (drive-targets-config) and invoke the login worker
    through `uv run`, with the resolved secrets passed through its
    environment only (`worker_env_with_secrets`), overwriting the cache on
    success.

    On a worker failure, the requested cache path is left exactly as it
    was — the worker itself never touches `--out` until it has fully
    succeeded (`browser_worker.py cmd_login`'s own contract) — and this
    reports the worker's failure detail (which names its debug-screenshot
    path) with a non-zero exit, never touching the previous cache file.

    `run` is the injectable subprocess seam (`default_run`'s signature),
    supplied by tests to avoid a real `uv`/Playwright invocation.
    """
    targets, meta = resolve_targets()
    name = args.target or meta.get("default")
    if not name:
        raise DriveError(
            "no target given and no default target is configured")
    entry = get_target(name, targets)

    ttl_hours = meta.get(AUTH_CACHE_TTL_HOURS_KEY, DEFAULT_AUTH_CACHE_TTL_HOURS)
    cache_path = auth_cache_path(name)

    if _auth_cache_is_fresh(cache_path, ttl_hours):
        print("drive: reusing cached login for %r (%s)" % (name, cache_path))
        return 0

    # A target whose auth recipe is `none` has no login to perform
    # (drive-auth-cache): `resolve_auth` would hand back `(None, None)` and
    # the worker would then fail demanding DRIVE_LOGIN_USERNAME and
    # DRIVE_LOGIN_PASSWORD, so short-circuit before any credential is
    # resolved. No cache file is written either — an empty storage state
    # would fake a cache whose mtime drives TTL logic that means nothing for
    # a target that never logs in.
    auth = entry.get("auth") or {"kind": "none"}
    if auth.get("kind", "none") == "none":
        print("drive: target %r declares no login (auth kind 'none') — "
              "nothing to do" % name)
        return 0

    url = entry.get("url")
    if not url:
        raise DriveError("target %r declares no url" % name)

    username, password = resolve_auth(entry, run=run)
    worker_env = worker_env_with_secrets(username, password)

    _ensure_private_dir(os.path.dirname(cache_path))
    worker = os.path.join(HERE, "browser_worker.py")
    worker_argv = ["uv", "run", worker, "login",
                  "--url", url, "--out", cache_path]

    try:
        rc, out, err = run(worker_argv, env=worker_env)
    except OSError as exc:
        raise DriveError("could not start the login worker: %s" % exc)

    if rc != 0:
        detail = (err or out).strip() or "the login worker exited %d" % rc
        raise DriveError("login failed for target %r: %s" % (name, detail))

    print("drive: logged in %r (%s)" % (name, cache_path))
    return 0


# --- the session daemon (drive-session) -----------------------------------

# One session at a time, never one per target (drive-skill's plan.md: "a
# Unix socket at ``~/.shipd/drive/session.sock``") — `SESSION_DIR` is the
# same `~/.shipd/drive/` directory `USER_TARGETS_PATH`/`auth_cache_dir` live
# under.
SESSION_DIR = os.path.dirname(USER_TARGETS_PATH)
SESSION_STATE_PATH = os.path.join(SESSION_DIR, "session.json")
SESSION_SOCKET_PATH = os.path.join(SESSION_DIR, "session.sock")


def _read_session_state():
    """The current session state dict (`{"target", "pid", "socket"}`), or
    `None` when no session has ever started or the state file is missing or
    unreadable — never a fatal error, since a missing/corrupt state file
    just means "nothing to report/stop"."""
    if not os.path.isfile(SESSION_STATE_PATH):
        return None
    try:
        with open(SESSION_STATE_PATH, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _write_session_state(target, pid, socket_path):
    _ensure_private_dir(SESSION_DIR)
    with open(SESSION_STATE_PATH, "w", encoding="utf-8") as fh:
        json.dump({"target": target, "pid": pid, "socket": socket_path}, fh)


def _remove_session_state():
    try:
        os.remove(SESSION_STATE_PATH)
    except OSError:
        pass


def _pid_alive(pid):
    """Whether a process with this pid currently exists, via the
    zero-signal `kill` probe. `False` for a falsy `pid` too, so a missing
    field in a state dict never raises."""
    if not pid:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _socket_alive(socket_path, timeout=0.5):
    """Whether something is actually listening on the Unix socket at
    `socket_path` — connecting is the only reliable test, since a stale
    socket *file* can be left behind by a worker that died without
    cleaning up after itself (drive-session's "session status reports a
    stale socket")."""
    if not socket_path or not os.path.exists(socket_path):
        return False
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect(socket_path)
        return True
    except OSError:
        return False
    finally:
        sock.close()


def _stop_running_session(state, timeout=3.0):
    """Best-effort stop of the session described by `state`: send a
    graceful `close` request over its socket first, falling back to
    `SIGTERM` against its pid when the socket is unreachable (a stuck or
    already-dead worker) — then wait up to `timeout` seconds for the pid to
    actually exit. Never raises; a session that is already dead is simply
    not there to stop."""
    sock_path = state.get("socket")
    closed_gracefully = False
    if sock_path and os.path.exists(sock_path):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        try:
            sock.connect(sock_path)
            sock.sendall((json.dumps({"op": "close"}) + "\n")
                        .encode("utf-8"))
            try:
                sock.recv(65536)
            except OSError:
                pass
            closed_gracefully = True
        except OSError:
            pass
        finally:
            sock.close()

    pid = state.get("pid")
    if pid and not closed_gracefully and _pid_alive(pid):
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass

    if pid:
        deadline = time.time() + timeout
        while time.time() < deadline and _pid_alive(pid):
            time.sleep(0.05)


def _resolve_session_target(args, targets, meta):
    name = args.target or meta.get("default")
    if not name:
        raise DriveError(
            "no target given and no default target is configured")
    return name


def _resolve_session_url(name, targets):
    """The URL passed to the session worker's `--url`: the target's
    declared url when one resolves, `about:blank` otherwise. `session
    start` never hard-fails on an unresolvable target the way `login`
    does (drive-targets-config's unknown-target error is that verb's own
    contract) — the worker starts with a blank page either way, and the
    `open` verb is how the caller actually navigates it."""
    entry = targets.get(name) or {}
    return entry.get("url") or "about:blank"


def _session_start(args):
    """`session start` (drive-session): stop and reclaim any running
    session first — whatever its target, so a stale socket never survives
    into the new session (drive-doctor's own tool-presence style: never
    trust a leftover file without checking it) — then spawn
    `browser_worker.py session` as a background process through `uv run`,
    record its target/pid/socket in the session state file, and print a
    one-line confirmation. `session start` for a different target replaces
    the running one (drive-session's "switching target replaces the
    session" scenario); this treats *any* running session the same way,
    since restarting for the same target is just as much a fresh worker.
    """
    targets, meta = resolve_targets()
    name = _resolve_session_target(args, targets, meta)

    existing = _read_session_state()
    if existing:
        _stop_running_session(existing)
        _remove_session_state()

    _ensure_private_dir(SESSION_DIR)
    if os.path.exists(SESSION_SOCKET_PATH):
        # A stale socket file from a session that did not clean up after
        # itself. The worker itself also reclaims this on its own start,
        # but removing it here means nothing else can observe a phantom
        # listener in the gap before the new worker binds.
        try:
            os.remove(SESSION_SOCKET_PATH)
        except OSError:
            pass

    url = _resolve_session_url(name, targets)
    storage_state = auth_cache_path(name)
    worker = os.path.join(HERE, "browser_worker.py")
    worker_argv = ["uv", "run", worker, "session",
                  "--target", name, "--url", url,
                  "--storage-state", storage_state,
                  "--socket", SESSION_SOCKET_PATH]

    try:
        proc = subprocess.Popen(
            worker_argv, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
    except OSError as exc:
        raise DriveError("could not start the session worker: %s" % exc)

    _write_session_state(name, proc.pid, SESSION_SOCKET_PATH)
    print("drive: session started for %r (pid=%s, socket=%s)"
         % (name, proc.pid, SESSION_SOCKET_PATH))
    return 0


def _session_status(args):
    """`session status` (drive-session): report whether the recorded
    session (if any) is actually alive — both its pid and its socket must
    check out, or the report calls it stale rather than pretending a dead
    session is still running."""
    state = _read_session_state()
    if not state:
        print("drive: no session is running")
        return 0

    if _pid_alive(state.get("pid")) and _socket_alive(state.get("socket")):
        print("drive: session running for %r (pid=%s, socket=%s)"
             % (state.get("target"), state.get("pid"), state.get("socket")))
        return 0

    print("drive: session state is stale (target=%r, pid=%s, socket=%s) — "
         "not responding; run `session start` to replace it"
         % (state.get("target"), state.get("pid"), state.get("socket")))
    return 0


def _session_stop(args):
    """`session stop` (drive-session): stop the running session, if any,
    and remove its state file."""
    state = _read_session_state()
    if not state:
        print("drive: no session is running")
        return 0
    _stop_running_session(state)
    _remove_session_state()
    print("drive: session stopped")
    return 0


_SESSION_ACTIONS = {
    "start": _session_start,
    "status": _session_status,
    "stop": _session_stop,
}


def cmd_session(args):
    return _SESSION_ACTIONS[args.action](args)


# --- driving verbs: thin socket clients (drive-session) -------------------


def _connect_session():
    """Connect to the running session's socket, or raise `DriveError` (one
    `Error:` line, non-zero exit) naming why not: no session recorded at
    all, or the recorded one refusing the connection — both are "a
    connection failure" from a driving verb's point of view."""
    state = _read_session_state()
    if not state or not state.get("socket"):
        raise DriveError(
            "no session is running — run `session start` first")
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(60.0)
    try:
        sock.connect(state["socket"])
    except OSError as exc:
        sock.close()
        raise DriveError(
            "could not connect to the running session: %s" % exc)
    return sock


def _session_request(op, **params):
    """Send one JSON request to the running session's socket and return its
    one JSON reply (drive-session: "each send one JSON request to that
    socket and print the JSON reply"). `None`-valued keyword params are
    dropped rather than sent, so an unset optional CLI flag never reaches
    the daemon as an explicit `null`. Any I/O failure along the way — the
    connection dropping mid-request, an empty or unparseable reply — is a
    `DriveError`, reported the same one-`Error:`-line way as a refused
    connection."""
    sock = _connect_session()
    try:
        request = {"op": op}
        request.update({k: v for k, v in params.items() if v is not None})
        sock.sendall((json.dumps(request) + "\n").encode("utf-8"))
        data = b""
        while not data.endswith(b"\n"):
            chunk = sock.recv(65536)
            if not chunk:
                break
            data += chunk
    except OSError as exc:
        raise DriveError("session request failed: %s" % exc)
    finally:
        sock.close()
    if not data:
        raise DriveError(
            "the session closed the connection with no reply")
    try:
        return json.loads(data.decode("utf-8"))
    except ValueError as exc:
        raise DriveError(
            "the session returned an unparseable reply: %s" % exc)


def _print_reply(reply):
    """Print a daemon reply verbatim and report it as an exit status
    (drive-session): the reply itself still reaches stdout unchanged, so a
    caller parsing the JSON sees exactly what the daemon said, while a
    caller reading only `$?` never mistakes a falsey `ok` — a timed-out
    `wait`, a click that found nothing — for a successful verb."""
    print(json.dumps(reply))
    ok = reply.get("ok") if isinstance(reply, dict) else False
    return 0 if ok else 1


def cmd_open(args):
    return _print_reply(_session_request("open", url=args.url))


def cmd_snapshot(args):
    return _print_reply(
        _session_request("snapshot", selector=args.selector))


def cmd_click(args):
    return _print_reply(_session_request("click", selector=args.selector))


def cmd_type(args):
    return _print_reply(
        _session_request("type", selector=args.selector, text=args.text))


def cmd_press(args):
    return _print_reply(_session_request("press", key=args.key))


def cmd_wait(args):
    return _print_reply(
        _session_request("wait", signal=args.signal, timeout=args.timeout))


def cmd_eval(args):
    return _print_reply(
        _session_request("eval", expression=args.expression))


def cmd_shot(args):
    return _print_reply(_session_request("shot", out=args.out))


def cmd_console(args):
    return _print_reply(_session_request("console"))


def cmd_network(args):
    return _print_reply(_session_request("network"))


def cmd_probe(args, run=default_run):
    """`probe` (drive-skill-flow): the read-only DOM/accessibility sampler
    that a driving run must use before authoring any precise selector,
    resolved and invoked the same way `record` resolves its target and
    invokes its worker: resolve the configured default target's url and its
    cached storage state (`login` is what populates the cache; a probe
    without one simply runs unauthenticated, matching the worker's own
    `--storage-state` being optional), invoke `browser_worker.py probe`
    through `uv run`, and print the artifact paths the worker reports.
    `args.url`, when given, overrides only the url navigated to — the
    resolved target's cached auth still applies, so a caller can probe a
    specific page inside the same app under test. `run` is the injectable
    subprocess seam (`default_run`'s signature), so a test can substitute a
    fake without a real `uv`/Playwright invocation.
    """
    targets, meta = resolve_targets()
    name = meta.get("default")
    entry = get_target(name, targets) if name else {}
    url = args.url or entry.get("url")
    if not url:
        raise DriveError(
            "no url given and no default target is configured")

    out_dir = os.path.join(
        SESSION_DIR, "probes", name or "adhoc", time.strftime("%Y%m%d-%H%M%S"))
    os.makedirs(out_dir, exist_ok=True)

    worker = os.path.join(HERE, "browser_worker.py")
    worker_argv = ["uv", "run", worker, "probe",
                  "--url", url, "--out", out_dir]
    if name:
        storage_state = auth_cache_path(name)
        if os.path.isfile(storage_state):
            worker_argv += ["--storage-state", storage_state]
    if args.reveal:
        worker_argv += ["--reveal", args.reveal]

    try:
        rc, out, err = run(worker_argv)
    except OSError as exc:
        raise DriveError("could not start the probe worker: %s" % exc)

    if rc != 0:
        detail = (err or out).strip() or "the probe worker exited %d" % rc
        # The worker already reports its own failure as one
        # `Error: probe failed: <detail>` line on stderr; re-wrapping that
        # verbatim would double the prefix (`Error: probe failed: Error:
        # probe failed: ...`). Strip a leading `Error: ` so `main()`'s own
        # `Error: %s` wrapping still yields a single `Error:` line carrying
        # the worker's detail once. A detail that never had that prefix
        # (e.g. a bare non-zero exit with no output) still gets the
        # `probe failed:` context added here.
        if detail.startswith("Error: "):
            detail = detail[len("Error: "):]
        else:
            detail = "probe failed: %s" % detail
        raise DriveError(detail)

    result = {}
    for line in reversed(out.strip().splitlines()):
        try:
            result = json.loads(line)
        except ValueError:
            continue
        break

    print("accessibility: %s" % result.get("accessibility"))
    print("testids: %s" % result.get("testids"))
    print("html: %s" % result.get("html"))
    print("screenshot: %s" % result.get("screenshot"))
    return 0


def cmd_record(args, run=default_run):
    """`record` (drive-recording): resolve the target and its cached
    storage state, invoke `record_worker.py <module>` through `uv run` to
    record the requested action module, and print the recording and
    timeline paths `record_worker.py` reports.

    `args.out` names the directory the raw recording (and its
    `.timeline.json`) are written under; when omitted, defaults to a
    timestamped directory under `~/.shipd/drive/recordings/<target>/` so
    repeated recordings for the same target never collide. The target's
    cached auth (`auth_cache_path`) is passed through only when it exists —
    `login` is what populates it; a recording without one simply runs
    unauthenticated, matching the worker's own `--storage-state` being
    optional. `run` is the injectable subprocess seam (`default_run`'s
    signature), so a test can substitute a fake without a real
    `uv`/Playwright invocation.
    """
    targets, meta = resolve_targets()
    name = args.target or meta.get("default")
    if not name:
        raise DriveError(
            "no target given and no default target is configured")
    entry = get_target(name, targets)
    url = entry.get("url")
    if not url:
        raise DriveError("target %r declares no url" % name)

    out_dir = args.out or os.path.join(
        SESSION_DIR, "recordings", name, time.strftime("%Y%m%d-%H%M%S"))
    os.makedirs(out_dir, exist_ok=True)

    worker = os.path.join(HERE, "record_worker.py")
    worker_argv = ["uv", "run", worker, args.module,
                  "--base-url", url, "--out-dir", out_dir]
    storage_state = auth_cache_path(name)
    if os.path.isfile(storage_state):
        worker_argv += ["--storage-state", storage_state]

    try:
        rc, out, err = run(worker_argv)
    except OSError as exc:
        raise DriveError("could not start the record worker: %s" % exc)

    if rc != 0:
        detail = (err or out).strip() or "the record worker exited %d" % rc
        raise DriveError(
            "recording failed for target %r: %s" % (name, detail))

    result = {}
    for line in reversed(out.strip().splitlines()):
        try:
            result = json.loads(line)
        except ValueError:
            continue
        break

    print("video: %s" % result.get("video"))
    print("timeline: %s" % result.get("timeline"))
    return 0


def _current_branch(run=default_run):
    """The working tree's current branch name, or `None` when it cannot be
    determined — a detached HEAD, no `git` on PATH, or not a repository at
    all. Best-effort only: `postprocess.resolve_title`'s pure precedence
    chain (drive-brand-frames) falls through to a supplied title or the
    fixed default either way, so a failure here is never fatal to `post`."""
    try:
        rc, out, _err = run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    except OSError:
        return None
    if rc != 0:
        return None
    branch = out.strip()
    return branch or None


def cmd_post(args, run=default_run):
    """`post` (drive-postprocess, drive-brand-frames): assemble the
    finished, branded, fast-forwarded video from a raw recording and its
    semantic timeline — cut the leading boot, fast-forward every eligible
    dead-air stretch (the timeline's own `spans` unioned with the spinner
    backstop's detected dead air), prepend the shipd title card, composite
    the fast-forward badge over sped-up segments only, and optionally write
    an inline-embeddable GIF alongside.
    """
    recording = args.recording
    if not os.path.isfile(recording):
        raise DriveError("recording not found: %s" % recording)

    timeline_path = args.timeline or (
        os.path.splitext(recording)[0] + ".timeline.json")
    if not os.path.isfile(timeline_path):
        raise DriveError("timeline not found: %s" % timeline_path)
    try:
        with open(timeline_path, "r", encoding="utf-8") as fh:
            timeline = json.load(fh)
    except (OSError, ValueError) as exc:
        raise DriveError(
            "could not read timeline %s: %s" % (timeline_path, exc))

    out_path = args.out or (
        os.path.splitext(recording)[0] + ".branded.mp4")

    branch = _current_branch(run=run)
    title = pp.resolve_title(branch=branch, supplied=args.title)

    workdir = tempfile.mkdtemp(prefix="drive-post-")
    worker = os.path.join(HERE, "browser_worker.py")
    try:
        try:
            backstop = pp.spinner_backstop_spans(recording, run)
        except RuntimeError as exc:
            raise DriveError("spinner backstop sampling failed: %s" % exc)

        title_card_path = os.path.join(workdir, "title-card.png")
        rc, out, err = run(["uv", "run", worker, "cards",
                           "--kind", "title", "--title", title,
                           "--out", title_card_path])
        if rc != 0:
            raise DriveError("failed rendering the title card: %s"
                             % (err or out).strip())

        badge_path = os.path.join(workdir, "badge.png")
        rc, out, err = run(["uv", "run", worker, "cards",
                           "--kind", "badge", "--speed", "10x",
                           "--corner", args.corner, "--out", badge_path])
        if rc != 0:
            raise DriveError("failed rendering the fast-forward badge: %s"
                             % (err or out).strip())

        try:
            result = pp.assemble(
                recording, timeline, out_path, run, workdir=workdir,
                backstop_spans=backstop, title_card_path=title_card_path,
                badge_path=badge_path, badge_corner=args.corner,
                gif=args.gif)
        except RuntimeError as exc:
            raise DriveError("assembling the output failed: %s" % exc)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    if args.gif:
        out_path, gif_path = result
        print("output: %s" % out_path)
        print("gif: %s" % gif_path)
    else:
        print("output: %s" % result)
    return 0


# --- verdict computation (drive-verdict) -----------------------------------


def _response_origin(url):
    """The `scheme://netloc` origin of a response's URL, for comparison
    against a target's own origin (drive-verdict: "any 4xx or 5xx response
    to the target's own origin"). Pure — no I/O."""
    parts = urllib.parse.urlsplit(url or "")
    return "%s://%s" % (parts.scheme, parts.netloc)


def _console_error_signature(event):
    """The identity a console *error* event is deduplicated by when
    comparing the baseline against the final set: its `type` (always
    `"error"` here) and `text` — never `time`, since the same error
    re-logged at a later timestamp is still "pre-existing noise"
    (drive-verdict's "pre-existing noise does not fail a run" scenario),
    not a new failure."""
    return (event.get("type"), event.get("text"))


def compute_verdict(baseline_console, final_console, network_events,
                    target_origin, signal_observed, signal_name):
    """The run's verdict (drive-verdict): `("PASS" | "FAIL", evidence)`,
    `evidence` a list of human-readable lines.

    - A missing completion signal is checked first and always fails the
      run, however clean everything else looks (drive-verdict: "the
      verdict SHALL be FAIL and SHALL state that the signal was never
      observed, never PASS").
    - `baseline_console` (the console state right after the first
      navigation) is never itself evidence; only a `final_console` *error*
      absent from that baseline fails the run — a repeat of a pre-existing
      error does not, and a warning never does regardless of when it
      appears.
    - Any `network_events` response carrying a 4xx/5xx `status` whose URL
      shares `target_origin` fails the run; a response to a different
      origin (a third-party asset, a CDN) is not evidence against this
      run.

    Pure — no I/O; every input is evidence already collected by the
    session daemon's `console`/`network` verbs."""
    evidence = []
    ok = True

    if not signal_observed:
        evidence.append(
            "completion signal %r was never observed" % (signal_name,))
        ok = False

    baseline_errors = {
        _console_error_signature(event) for event in baseline_console
        if event.get("type") == "error"
    }
    for event in final_console:
        if event.get("type") != "error":
            continue
        if _console_error_signature(event) in baseline_errors:
            continue
        evidence.append("new console error: %s" % event.get("text"))
        ok = False

    for event in network_events:
        status = event.get("status")
        if status is None or status < 400:
            continue
        url = event.get("url") or ""
        if _response_origin(url) != target_origin:
            continue
        evidence.append("%s %s -> %s response from the target's own origin"
                        % (event.get("method") or "?", url, status))
        ok = False

    return ("PASS" if ok else "FAIL"), evidence


# --- argument parsing -----------------------------------------------------


def build_parser():
    parser = argparse.ArgumentParser(
        prog="drive",
        description="Drive a real browser with Playwright to operate an "
                    "app, verify a change, and record a demo (stdlib "
                    "only; browser I/O lives in the worker scripts).")
    sub = parser.add_subparsers(dest="verb", required=True)

    p_doctor = sub.add_parser(
        "doctor", help="report prerequisite state; --fix installs what "
                       "it can")
    p_doctor.add_argument("--fix", action="store_true",
                          help="install the missing browser binary and "
                               "re-report (network access happens only "
                               "here)")
    p_doctor.set_defaults(func=cmd_doctor)

    p_targets = sub.add_parser(
        "targets", help="print each resolved target's name, url, and "
                        "auth kind")
    p_targets.set_defaults(func=cmd_targets)

    p_login = sub.add_parser(
        "login", help="obtain or reuse a cached login for a target")
    p_login.add_argument("target", nargs="?", default=None,
                         help="target name (default: the config default)")
    p_login.set_defaults(func=cmd_login)

    p_session = sub.add_parser(
        "session", help="start, check, or stop the browser session daemon")
    p_session.add_argument("action", choices=["start", "status", "stop"])
    p_session.add_argument("target", nargs="?", default=None,
                           help="target name (default: the config "
                                "default; only meaningful for `start`)")
    p_session.set_defaults(func=cmd_session)

    p_open = sub.add_parser("open", help="navigate the session's page")
    p_open.add_argument("url")
    p_open.set_defaults(func=cmd_open)

    p_snapshot = sub.add_parser(
        "snapshot", help="print an accessibility-tree snapshot of the "
                         "current page")
    p_snapshot.add_argument("--selector", default=None,
                            help="scope the snapshot to this selector")
    p_snapshot.set_defaults(func=cmd_snapshot)

    p_click = sub.add_parser("click", help="click an element")
    p_click.add_argument("selector")
    p_click.set_defaults(func=cmd_click)

    p_type = sub.add_parser("type", help="type text into an element")
    p_type.add_argument("selector")
    p_type.add_argument("text")
    p_type.set_defaults(func=cmd_type)

    p_press = sub.add_parser("press", help="press a key")
    p_press.add_argument("key")
    p_press.set_defaults(func=cmd_press)

    p_wait = sub.add_parser(
        "wait", help="wait for a named completion signal, never a fixed "
                     "sleep")
    p_wait.add_argument("signal")
    p_wait.add_argument("--timeout", type=float, default=None,
                        help="timeout in seconds")
    p_wait.set_defaults(func=cmd_wait)

    p_eval = sub.add_parser(
        "eval", help="evaluate a JavaScript expression on the page")
    p_eval.add_argument("expression")
    p_eval.set_defaults(func=cmd_eval)

    p_shot = sub.add_parser("shot", help="take a screenshot")
    p_shot.add_argument("--out", default=None, help="output path")
    p_shot.set_defaults(func=cmd_shot)

    p_console = sub.add_parser(
        "console", help="print console events accumulated since the "
                        "session started")
    p_console.set_defaults(func=cmd_console)

    p_network = sub.add_parser(
        "network", help="print response events accumulated since the "
                        "session started")
    p_network.set_defaults(func=cmd_network)

    p_probe = sub.add_parser(
        "probe", help="a read-only sampler: accessibility tree, "
                     "data-testid/data-anchor inventory, scoped HTML, "
                     "and a screenshot")
    p_probe.add_argument("url", nargs="?", default=None)
    p_probe.add_argument("--reveal", default=None,
                         help="one non-destructive reveal click before "
                              "sampling")
    p_probe.set_defaults(func=cmd_probe)

    p_record = sub.add_parser(
        "record", help="record a demo by running an action module")
    p_record.add_argument("module", help="path to the action module")
    p_record.add_argument("--target", default=None)
    p_record.add_argument("--out", default=None, help="output directory")
    p_record.set_defaults(func=cmd_record)

    p_post = sub.add_parser(
        "post", help="post-process a recording into a branded, "
                     "fast-forwarded video")
    p_post.add_argument("recording", help="path to the raw recording")
    p_post.add_argument("--timeline", default=None,
                        help="path to the timeline JSON (default: beside "
                             "the recording)")
    p_post.add_argument("--out", default=None, help="output path")
    p_post.add_argument("--title", default=None,
                        help="title card text (default: the change/<slug> "
                             "branch name)")
    p_post.add_argument("--gif", action="store_true",
                        help="additionally write an animated GIF")
    p_post.add_argument("--corner", default="bottom-right",
                        choices=["top-left", "top-right", "bottom-left",
                                "bottom-right"],
                        help="which corner the fast-forward badge sits in "
                             "(default: bottom-right); pick one that never "
                             "covers the region under demonstration")
    p_post.set_defaults(func=cmd_post)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except DriveError as exc:
        print("Error: %s" % exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
