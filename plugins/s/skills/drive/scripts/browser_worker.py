#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "playwright",
# ]
# ///
"""browser_worker.py — the Playwright-backed worker behind `drive.py`
(shipd-drive), invoked as ``uv run browser_worker.py <subcommand> ...``.

`drive.py` is stdlib-only and never imports Playwright directly; every piece
of real browser I/O crosses a process boundary into this script, mirroring
how `video_ingest.py` reaches `asr_whisper.py` (video-backend-adapters). This
file, and `record_worker.py` beside it, are the only two scripts in the
`drive` skill allowed to import `playwright` — carried through the PEP 723
inline dependency header above and resolved by `uv run`, never installed
into the shared environment.

Subcommands:
  login             (drive-targets-config, drive-auth-cache) log in to a
                     target's site using the username/password handed in
                     through the environment (never argv), and write the
                     resulting storage state to the requested path. With
                     `--manual`, open a *visible* window and let the human
                     at the keyboard log in instead — no credential is read
                     from anywhere — waiting for `--done` (the `wait` verb's
                     signal grammar) or, without one, until the URL has left
                     the login page while the host still matches it. On
                     failure, write a debug screenshot beside it and exit
                     non-zero, leaving the requested output path untouched.
  session           (drive-session, drive-handoff) launch one browser and
                     one page loaded with the target's cached storage state
                     — headless unless `--headed` — attach
                     `console`/`response` listeners once, and serve
                     newline-delimited JSON requests on a Unix socket —
                     one JSON reply per request — for the life of the
                     session. Its `handoff`/`resume` ops hand the live page
                     to the human at the keyboard and take it back,
                     relaunching a headless browser visible in place
                     (drive-handoff) without losing the accumulated
                     evidence.
  probe             (drive-skill-flow) a read-only DOM sampler: navigate,
                     optionally perform one non-destructive reveal click,
                     then dump the scoped accessibility tree, a
                     `data-testid`/`data-anchor` inventory, truncated scoped
                     HTML, and a screenshot. Never submits, saves, or
                     creates anything.
  cards             (drive-brand-frames) render the shipd-branded title card
                     and the fast-forward speed badge used by
                     `postprocess.py`.
  install-browser   download the Playwright browser binary `doctor --fix`
                     is missing, after the caller has already stated the
                     network access this performs.

Every subcommand prints its result as one line of JSON to stdout on success.
A subcommand-level failure is reported as ``Error: <reason>`` on stderr with
a non-zero exit; the `session` subcommand additionally reports a per-request
handler failure as a JSON error object on the socket, without exiting.
"""

import argparse
import html
import json
import os
import socket
import sys
import time
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
# `postprocess.py` is stdlib-only (no playwright import at module scope), so
# importing it here carries nothing into this file's PEP 723 dependency
# surface — done only to share its badge geometry constants (`BADGE_WIDTH`,
# `BADGE_HEIGHT`) as the one source of truth `cards` renders to and
# `postprocess.py`'s `assemble` composites against.
import postprocess as pp  # noqa: E402

# Env vars drive.py's `login` verb (drive-targets-config, drive-auth-cache)
# places the resolved username/password into before invoking this worker —
# never on this process's argv, matching drive-targets-config's "secrets
# never reach a command line" scenario.
LOGIN_USERNAME_ENV = "DRIVE_LOGIN_USERNAME"
LOGIN_PASSWORD_ENV = "DRIVE_LOGIN_PASSWORD"


def _ensure_private_dir(path):
    """Create `path` (and any missing parents) and guarantee it ends up
    owner-only (`0700`) — duplicated from `drive.py`'s helper of the same
    name rather than imported, the same split as `LOGIN_USERNAME_ENV` above:
    this worker never imports `drive.py`. The session socket this worker
    binds lives in this directory, and it is an unauthenticated,
    arbitrary-JS-eval remote into a logged-in browser — it must never sit
    inside a world-traversable directory.

    `os.makedirs(..., mode=..., exist_ok=True)` only applies `mode` to a
    directory it actually creates — an already-existing directory (e.g. one
    left behind, world-readable, by a version of this script that predates
    this fix) keeps whatever mode it already had. So this always `chmod`s
    `path` to `0o700` after `makedirs`, regardless of whether this call
    created it or found it already there."""
    os.makedirs(path, mode=0o700, exist_ok=True)
    os.chmod(path, 0o700)


# Candidate selectors for the generic login form, tried in order. Real apps
# vary; this best-effort list covers the common identifier/password/submit
# shapes without needing per-app configuration.
_IDENTIFIER_SELECTORS = [
    "input[type=email]",
    "input[autocomplete=username]",
    "input[autocomplete=email]",
    "input[name=email]",
    "input[name=username]",
    "input#email",
    "input#username",
]
_CONTINUE_SELECTORS = [
    "button:has-text(\"Next\")",
    "button:has-text(\"Continue\")",
]
_PASSWORD_SELECTORS = [
    "input[type=password]",
    "input[autocomplete=current-password]",
    "input[name=password]",
    "input#password",
]
_SUBMIT_SELECTORS = [
    "button[type=submit]",
    "input[type=submit]",
    "button:has-text(\"Sign in\")",
    "button:has-text(\"Log in\")",
    "button:has-text(\"Continue\")",
]


def _fill_first(page, selectors, value, timeout=5000):
    """Fill the first selector in `selectors` whose element becomes visible
    within `timeout` ms; raise if none do."""
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            locator.wait_for(state="visible", timeout=timeout)
            locator.fill(value)
            return selector
        except Exception:  # noqa: BLE001 - try the next candidate
            continue
    raise RuntimeError(
        "no matching field for any of: %s" % ", ".join(selectors))


def _click_first(page, selectors, optional=False, timeout=5000):
    """Click the first selector in `selectors` whose element becomes visible
    within `timeout` ms. Returns None with no click when `optional` and none
    match; otherwise raises."""
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            locator.wait_for(state="visible", timeout=timeout)
            locator.click()
            return selector
        except Exception:  # noqa: BLE001 - try the next candidate
            continue
    if optional:
        return None
    raise RuntimeError(
        "no matching control for any of: %s" % ", ".join(selectors))


def _write_storage_state_privately(context, out_path):
    """Write `context`'s storage state to `out_path` and immediately lock
    it down to `0600` — the file holds live session cookies, so it must
    never be left world-readable under the process's umask. Takes a plain
    `context` (anything with a Playwright-shaped `storage_state(path=...)`
    method) rather than a full page/browser, so a test can exercise this
    exact chmod behavior with a stand-in object, with no real Playwright
    context or browser involved."""
    context.storage_state(path=out_path)
    os.chmod(out_path, 0o600)


# --- the shared completion-signal wait -----------------------------------

# Signal names `_wait_for_signal` treats as Playwright load states rather
# than as a selector.
_LOAD_STATE_SIGNALS = ("load", "domcontentloaded", "networkidle")


def _wait_for_signal(page, signal, timeout_seconds=None):
    """Block until `signal` appears on `page`, never for a fixed sleep
    (drive-skill-flow). One grammar, shared by every caller that waits:

    - one of the Playwright load-state names
      (`load`/`domcontentloaded`/`networkidle`),
    - `url:<pattern>` — a URL wait on the pattern after the prefix,
    - anything else — a selector, waited for visible.

    `timeout_seconds` of `None` leaves Playwright's own default in force.
    Raises on expiry, which is how both callers — the session's `wait`
    handler (reported as `{"ok": false}`) and the manual login's own wait
    (reported as an `Error:` line beside a debug screenshot) — learn the
    signal never arrived."""
    if not signal:
        raise ValueError("a completion signal is required")
    kwargs = {"timeout": timeout_seconds * 1000} if timeout_seconds else {}
    if signal in _LOAD_STATE_SIGNALS:
        page.wait_for_load_state(signal, **kwargs)
    elif signal.startswith("url:"):
        page.wait_for_url(signal[len("url:"):], **kwargs)
    else:
        page.locator(signal).first.wait_for(state="visible", **kwargs)
    return signal


# --- the login subcommand (drive-auth-cache) ----------------------------

# The JavaScript the default manual-login completion rule evaluates: the URL
# must have left the login page *and* still be on the target's host, so an
# SSO bounce through an identity provider's own domain never ends the wait
# early (the human is mid-flow there, not logged in).
_MANUAL_DONE_JS = "([u, h]) => location.href !== u && location.host === h"

DEFAULT_MANUAL_TIMEOUT_SECONDS = 300.0


def _manual_wait_description(url, done):
    """What the stderr notice names as the thing the manual login waits
    for — the caller's own `done` signal, or the default rule spelled out,
    so the human can see what will end the wait."""
    if done:
        return "the completion signal %s" % done
    host = urllib.parse.urlsplit(url).netloc
    return ("the page to leave %s while the host is still %s" % (url, host))


def _wait_for_manual_login(page, url, done, timeout_seconds):
    """Block until the human's login is done: `done` through the shared
    `_wait_for_signal` grammar when the recipe declares one, otherwise the
    default `_MANUAL_DONE_JS` rule. Raises on expiry, which `cmd_login`
    turns into the same debug-screenshot failure any other login failure
    reports."""
    if done:
        _wait_for_signal(page, done, timeout_seconds)
        return
    host = urllib.parse.urlsplit(url).netloc
    page.wait_for_function(
        _MANUAL_DONE_JS, arg=[url, host],
        timeout=timeout_seconds * 1000)


def cmd_login(args):
    """Log the target's storage state in, per drive-auth-cache.

    Reads the username/password `drive.py` placed into the environment
    (never this process's argv), drives the generic login form — identifier
    field, an optional "Next"/"Continue" step, password field, submit —
    waits until the page leaves the authentication screen, re-navigates to
    the requested host if the flow redirected elsewhere, and writes the
    storage state to ``args.out``.

    With ``--manual`` it does none of that form driving. No credential is
    read at all — the human at the keyboard is the credential, which is the
    whole point of the mode: MFA, SSO, a passkey, or an OAuth consent screen
    is something only a person can get through. The browser launches
    *visible*, navigates to the url, prints a stderr notice naming the
    window and what it is waiting for, and then waits for ``--done`` (the
    shared `_wait_for_signal` grammar) or, without one, the default
    `_MANUAL_DONE_JS` rule, for up to ``--timeout`` seconds.

    On any failure — a form that would not fill, a manual login whose signal
    never arrived — writes a debug screenshot beside the requested output
    (leaving that output itself untouched) and reports ``Error: <reason>``
    on stderr with a non-zero exit.
    """
    manual = bool(getattr(args, "manual", False))
    username = os.environ.get(LOGIN_USERNAME_ENV)
    password = os.environ.get(LOGIN_PASSWORD_ENV)
    if not manual and (not username or not password):
        print("Error: login requires %s and %s in the environment"
              % (LOGIN_USERNAME_ENV, LOGIN_PASSWORD_ENV), file=sys.stderr)
        return 1

    from playwright.sync_api import sync_playwright
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

    debug_shot = args.debug_screenshot or (args.out + ".debug.png")
    done = getattr(args, "done", None)
    timeout_seconds = (getattr(args, "timeout", None)
                       or DEFAULT_MANUAL_TIMEOUT_SECONDS)

    with sync_playwright() as pw:
        # Visible for a manual login and headless for every other one —
        # `headless=True` is `launch()`'s own default, so the automated path
        # launches exactly as it always did.
        browser = pw.chromium.launch(headless=not manual)
        page = browser.new_page()
        try:
            page.goto(args.url, wait_until="domcontentloaded")

            if manual:
                # The notice goes to stderr, never stdout: stdout carries
                # this worker's one line of result JSON and nothing else.
                print("drive: waiting for %s (up to %g s) in the open "
                      "Chromium window"
                      % (_manual_wait_description(args.url, done),
                         timeout_seconds),
                      file=sys.stderr)
                _wait_for_manual_login(
                    page, args.url, done, timeout_seconds)
            else:
                _fill_first(page, _IDENTIFIER_SELECTORS, username)
                # Some flows insert a "Next"/"Continue" step between the
                # identifier and password fields (e.g. Google-style two-step
                # login); skip it when the password field is already present.
                _click_first(page, _CONTINUE_SELECTORS, optional=True)
                _fill_first(page, _PASSWORD_SELECTORS, password)
                _click_first(page, _SUBMIT_SELECTORS)

                try:
                    page.wait_for_function(
                        "url => location.href !== url", arg=args.url,
                        timeout=30000)
                except PlaywrightTimeoutError:
                    raise RuntimeError(
                        "the page never left the authentication screen (%s)"
                        % args.url)

                target_host = urllib.parse.urlsplit(args.url).netloc
                current_host = urllib.parse.urlsplit(page.url).netloc
                if current_host and current_host != target_host:
                    page.goto(args.url, wait_until="domcontentloaded")

            _write_storage_state_privately(page.context, args.out)
        except Exception as exc:  # noqa: BLE001 - report any failure
            try:
                page.screenshot(path=debug_shot)
            except Exception:  # noqa: BLE001 - screenshot is best-effort
                pass
            print("Error: login failed: %s (screenshot: %s)"
                  % (exc, debug_shot), file=sys.stderr)
            return 1
        finally:
            browser.close()

    print(json.dumps({"ok": True, "storageState": args.out}))
    return 0


# Request ops the session socket accepts, named identically to the
# `drive.py` driving verbs that forward them (drive-session): each is
# dispatched to `_HANDLERS[op]` with the request's other fields as keyword
# arguments plus the session context (`ctx["page"]`, the accumulated
# `console_events`/`network_events` buffers, and `ctx["closed"]`). Every
# handler returns a plain dict of reply fields (no `ok` key — `_serve_one`
# adds `ok: true` on a normal return, or turns a raised exception into
# `{"ok": false, "error": ...}` without killing the daemon, per
# drive-session's "a handler failure is a JSON error" contract).


def _handle_open(ctx, url=None, **_params):
    if not url:
        raise ValueError("open requires 'url'")
    page = ctx["page"]
    page.goto(url, wait_until="domcontentloaded")
    return {"url": page.url}


def _handle_snapshot(ctx, selector=None, **_params):
    # Playwright removed the `Page.accessibility` namespace (gone as of
    # 1.62); `Locator.aria_snapshot()` is the supported replacement. It
    # returns a YAML-ish string rather than the old snapshot dict, so the
    # reply's "snapshot" key now carries a string — the key name itself is
    # unchanged, which is the daemon's actual output contract.
    page = ctx["page"]
    if selector:
        locator = page.locator(selector).first
        if locator.count() == 0:
            raise ValueError("no element matches selector: %r" % selector)
    else:
        locator = page.locator("html")
    tree = locator.aria_snapshot()
    return {"snapshot": tree}


def _handle_click(ctx, selector=None, **_params):
    if not selector:
        raise ValueError("click requires 'selector'")
    ctx["page"].locator(selector).first.click()
    return {}


def _handle_type(ctx, selector=None, text=None, **_params):
    if not selector or text is None:
        raise ValueError("type requires 'selector' and 'text'")
    ctx["page"].locator(selector).first.fill(text)
    return {}


def _handle_press(ctx, key=None, **_params):
    if not key:
        raise ValueError("press requires 'key'")
    ctx["page"].keyboard.press(key)
    return {}


def _handle_wait(ctx, signal=None, timeout=None, **_params):
    """Wait for a named completion signal, never a fixed sleep
    (drive-skill-flow), through the shared `_wait_for_signal` grammar.
    Raises (and so reports as `{"ok": false}`) when the signal never appears
    within `timeout`, which is how the caller learns to fail the verdict
    rather than report `PASS` (drive-verdict)."""
    if not signal:
        raise ValueError("wait requires 'signal'")
    _wait_for_signal(ctx["page"], signal, timeout)
    return {"signal": signal}


def _handle_eval(ctx, expression=None, **_params):
    if expression is None:
        raise ValueError("eval requires 'expression'")
    return {"result": ctx["page"].evaluate(expression)}


def _handle_shot(ctx, out=None, **_params):
    if not out:
        raise ValueError("shot requires 'out'")
    ctx["page"].screenshot(path=out)
    return {"path": out}


def _handle_console(ctx, **_params):
    # The handoff windows ride along so the verdict can tell the human's own
    # console noise apart from the app's (drive-verdict): an event whose
    # time falls inside a window is reported, never failed on.
    return {"events": list(ctx["console_events"]),
            "handoffs": list(ctx["handoffs"])}


def _handle_network(ctx, **_params):
    return {"events": list(ctx["network_events"]),
            "handoffs": list(ctx["handoffs"])}


def _handle_close(ctx, **_params):
    ctx["closed"] = True
    return {}


# --- the human handoff (drive-handoff) -----------------------------------

DEFAULT_HANDOFF_TIMEOUT_SECONDS = 300.0


def _open_handoff_window(ctx):
    """Stamp and append a new, open handoff window. The windows are a list
    of their own (`ctx["handoffs"]`) rather than marker events inside the
    console/network buffers, so every existing reader of those buffers is
    left alone — nothing has to learn to filter a synthetic event out."""
    window = {"start": time.time(), "end": None}
    ctx["handoffs"].append(window)
    return window


def _open_handoff_windows(ctx):
    """The handoff windows still open — those whose `end` is `None`. At most
    one can ever be open, which `_handle_handoff`'s own guard is what
    enforces; this returns a list so both callers read the same way."""
    return [w for w in ctx["handoffs"] if w.get("end") is None]


def _relaunch_headed(ctx):
    """Reopen this session's browser *visible*, in place, carrying over
    everything that matters (drive-handoff): the context's storage state
    (saved as a dict, never a temporary file), the page's current URL, and —
    because the event buffers are plain lists living in `ctx`, not in the
    browser — every console and network event recorded so far.

    Done inside this process rather than by restarting the daemon: a restart
    would lose the buffers, the baseline, and the socket. The cost is the
    page's own unsaved state — text typed into a form, an SPA's in-memory
    store — which does not survive a new page, and which the skill states
    plainly before it offers a handoff.

    Returns the URL it navigated back to, or `None` when there was nothing
    to navigate back to (a session still sitting on `about:blank`)."""
    storage_state = ctx["context"].storage_state()
    url = ctx["page"].url

    ctx["context"].close()
    ctx["browser"].close()

    browser = ctx["pw"].chromium.launch(headless=False)
    context = browser.new_context(storage_state=storage_state)
    page = context.new_page()
    ctx["browser"] = browser
    ctx["context"] = context
    ctx["page"] = page
    # The same listeners, re-attached to the new page, appending into the
    # same two lists — which is what makes the pre-handoff evidence and the
    # post-handoff evidence one continuous record.
    _attach_listeners(ctx, page)
    ctx["headed"] = True

    if url and url != "about:blank":
        page.goto(url, wait_until="domcontentloaded")
        return url
    return None


def _handle_handoff(ctx, signal=None, timeout=None, **_params):
    """Hand the live session to the human at the keyboard (drive-handoff).

    Refuses outright when a window is already open: it opens no second
    window, relaunches nothing, and raises (so the reply is
    `{"ok": false}`). Two stacked windows would be worse than a confusing
    reply — only the innermost would ever be closed, and the outer one,
    left open forever, would excuse every event for the rest of the run
    from the verdict. The check comes first, before any relaunch, so a
    refused handoff leaves the session exactly as it was.

    Otherwise relaunches the browser visible when it is headless (replying
    with a truthy `relaunched`; an already-visible browser relaunches
    nothing and replies falsey), then opens a handoff window stamped with
    now. With a `signal`, blocks on it through the shared
    `_wait_for_signal` grammar — closing the window and replying on
    success, closing the window and raising (so the reply is
    `{"ok": false}`) on timeout. Without one, replies at once with `open`
    true and leaves the window for `resume` to close."""
    if _open_handoff_windows(ctx):
        raise RuntimeError(
            "a handoff window is already open — `resume` closes it")

    relaunched = False
    if not ctx["headed"]:
        _relaunch_headed(ctx)
        relaunched = True

    window = _open_handoff_window(ctx)

    if not signal:
        return {"relaunched": relaunched, "open": True}

    try:
        _wait_for_signal(ctx["page"], signal,
                         timeout or DEFAULT_HANDOFF_TIMEOUT_SECONDS)
    finally:
        # The window closes either way: a handoff that timed out is still
        # over, and leaving it open would excuse every later event from the
        # verdict.
        window["end"] = time.time()
    return {"relaunched": relaunched, "signal": signal}


def _handle_resume(ctx, **_params):
    """Take the session back from the human and close the open handoff
    window (drive-handoff). The `wait_for_timeout` first is the drain: sync
    Playwright dispatches listeners only inside a Playwright call, so the
    events a human's last clicks raised are still queued, and draining them
    here is what stamps them inside the window they belong to rather than
    after it. Raises (a falsey `ok`) when no window is open."""
    ctx["page"].wait_for_timeout(50)

    open_windows = _open_handoff_windows(ctx)
    if not open_windows:
        raise RuntimeError(
            "no handoff window is open — `handoff` opens one")
    window = open_windows[-1]
    window["end"] = time.time()
    return {"closed": dict(window)}


def _build_handlers():
    """The op -> handler table `_serve_one` dispatches through."""
    return {
        "open": _handle_open,
        "snapshot": _handle_snapshot,
        "click": _handle_click,
        "type": _handle_type,
        "press": _handle_press,
        "wait": _handle_wait,
        "eval": _handle_eval,
        "shot": _handle_shot,
        "handoff": _handle_handoff,
        "resume": _handle_resume,
        "console": _handle_console,
        "network": _handle_network,
        "close": _handle_close,
    }


def _serve_one(conn, handlers, ctx):
    """Read one newline-delimited JSON request off `conn`, dispatch it
    through `handlers`, and write back exactly one JSON reply — a handler
    failure becomes `{"ok": false, "error": ...}` rather than propagating,
    so one bad request never brings down the session (drive-session)."""
    buf = b""
    while not buf.endswith(b"\n"):
        chunk = conn.recv(65536)
        if not chunk:
            if not buf:
                return
            break
        buf += chunk
    try:
        request = json.loads(buf.decode("utf-8"))
        op = request.get("op")
        handler = handlers.get(op)
        if handler is None:
            reply = {"ok": False, "error": "unknown op: %r" % (op,)}
        else:
            params = {k: v for k, v in request.items() if k != "op"}
            reply = handler(ctx, **params)
            if "ok" not in reply:
                reply = dict(reply, ok=True)
    except Exception as exc:  # noqa: BLE001 - report, never crash the daemon
        reply = {"ok": False, "error": str(exc)}
    conn.sendall((json.dumps(reply) + "\n").encode("utf-8"))


def _bind_private_socket(server, socket_path):
    """Bind `server` (an `AF_UNIX`/`SOCK_STREAM` socket) to `socket_path` as
    owner-only, `0600`. This socket accepts unauthenticated `eval`/navigate/
    click/type requests against an already-logged-in browser, so it must
    never be connectable by another local user.

    A restrictive umask for the duration of `bind()` is the strong
    guarantee — the socket file never exists, even momentarily, with
    group/other bits set — with a belt-and-braces `chmod` right after as a
    second, redundant layer (a `chmod` alone would leave a brief window
    between `bind` and `chmod` during which the socket is connectable by
    anyone). Split out from `cmd_session` so this exact sequence is
    directly testable with a plain `socket.socket`, with no real session
    (and so no Playwright) involved."""
    old_umask = os.umask(0o077)
    try:
        server.bind(socket_path)
    finally:
        os.umask(old_umask)
    os.chmod(socket_path, 0o600)


def _attach_listeners(ctx, page):
    """Attach the `console` and `response` listeners that fill this
    session's two event buffers to `page`.

    Lifted out of `cmd_session` so `_relaunch_headed` can re-attach exactly
    the same pair to the new page it opens: the buffers are the lists in
    `ctx`, not anything the browser holds, so a relaunched session keeps
    appending to the same continuous record (drive-handoff). Called once at
    startup, before any request is served — which is what lets
    `console`/`network` report events emitted before the verb that reads
    them ran (drive-session)."""
    console_events = ctx["console_events"]
    network_events = ctx["network_events"]

    def _on_console(msg):
        console_events.append({
            "type": msg.type,
            "text": msg.text,
            "time": time.time(),
        })

    def _on_response(response):
        try:
            method = response.request.method
        except Exception:  # noqa: BLE001 - best-effort field
            method = None
        network_events.append({
            "url": response.url,
            "status": response.status,
            "method": method,
            "time": time.time(),
        })

    page.on("console", _on_console)
    page.on("response", _on_response)


def cmd_session(args):
    """Own one browser and one page for the life of the session and serve
    the driving verbs over a Unix socket, per drive-session.

    Launches one browser — headless unless `--headed` — and one page loaded
    with the target's cached storage state (when `--storage-state` names an
    existing file), attaches `console` and `response` listeners exactly
    once, before any request is served, so every event for the life of the
    session lands in an in-memory buffer that survives navigation, per
    drive-session's "console events survive a navigation" scenario. Then
    serves newline-delimited JSON requests on the `--socket` Unix socket,
    one JSON reply per request, until a `close` request arrives or the
    process is signalled to stop.

    The `Playwright` handle, the browser, the window mode, and the handoff
    windows all live in `ctx` because the `handoff` op replaces the first
    two in place (`_relaunch_headed`) rather than restarting this process
    (drive-handoff) — so the teardown below closes whatever context and
    browser `ctx` holds *now*, never the pair this function happened to
    open.
    """
    from playwright.sync_api import sync_playwright

    socket_path = args.socket
    socket_dir = os.path.dirname(socket_path)
    if socket_dir:
        _ensure_private_dir(socket_dir)
    # Reclaim a stale socket file left behind by a prior run — `session
    # start` (drive.py, task 4.2) already checked liveness before spawning
    # us, so any file still here is dead.
    if os.path.exists(socket_path):
        os.remove(socket_path)

    ctx = {
        "target": args.target,
        "base_url": args.url,
        "console_events": [],
        "network_events": [],
        "handoffs": [],
        "headed": bool(args.headed),
        "closed": False,
    }

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not args.headed)
        context_kwargs = {}
        if args.storage_state and os.path.exists(args.storage_state):
            context_kwargs["storage_state"] = args.storage_state
        context = browser.new_context(**context_kwargs)
        page = context.new_page()
        ctx["pw"] = pw
        ctx["browser"] = browser
        ctx["page"] = page
        ctx["context"] = context

        _attach_listeners(ctx, page)

        handlers = _build_handlers()

        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            _bind_private_socket(server, socket_path)
            server.listen(5)
            server.settimeout(1.0)
            while not ctx["closed"]:
                try:
                    conn, _addr = server.accept()
                except socket.timeout:
                    # The idle event pump. Sync Playwright dispatches its
                    # listeners only from inside a Playwright call, so an
                    # event raised while this loop sits in `accept()` —
                    # every console message and response a human's clicks
                    # produce during a handoff — waits for the next verb and
                    # is then stamped with *that* verb's time. A 1 ms wait
                    # each time around is one such call, so those events
                    # land within a second of when they really happened,
                    # inside the handoff window they belong to. Guarded
                    # because a page mid-relaunch or mid-navigation may
                    # refuse it, and an idle pump must never be what stops
                    # the daemon.
                    try:
                        ctx["page"].wait_for_timeout(1)
                    except Exception:  # noqa: BLE001 - best-effort pump
                        pass
                    continue
                try:
                    _serve_one(conn, handlers, ctx)
                finally:
                    conn.close()
        finally:
            server.close()
            if os.path.exists(socket_path):
                os.remove(socket_path)
            # `ctx`, not the locals above: a `handoff` may have replaced
            # both with the visible pair it relaunched.
            ctx["context"].close()
            ctx["browser"].close()

    return 0


# Truncation floor for the scoped HTML dump — large enough to be useful for
# selector authoring, small enough to never dump a multi-megabyte page body.
_PROBE_HTML_TRUNCATE_CHARS = 20000


def cmd_probe(args):
    """Read-only DOM sampler backing the skill's probe-before-selecting
    rule (drive-skill-flow): navigate, optionally perform one
    non-destructive reveal click, then dump the accessibility tree, a
    `data-testid`/`data-anchor` inventory, truncated HTML, and a screenshot
    into `--out`. Performs no submitting, saving, or creating — the one
    permitted click is the caller-named `--reveal` target, never a form
    control this verb infers on its own.
    """
    from playwright.sync_api import sync_playwright

    out_dir = args.out
    accessibility_path = os.path.join(out_dir, "accessibility.json")
    testids_path = os.path.join(out_dir, "testids.json")
    html_path = os.path.join(out_dir, "page.html")
    screenshot_path = os.path.join(out_dir, "screenshot.png")

    try:
        os.makedirs(out_dir, exist_ok=True)

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            context_kwargs = {}
            if args.storage_state and os.path.exists(args.storage_state):
                context_kwargs["storage_state"] = args.storage_state
            context = browser.new_context(**context_kwargs)
            page = context.new_page()
            try:
                page.goto(args.url, wait_until="domcontentloaded")

                if args.reveal:
                    # The one permitted click: a caller-named,
                    # non-destructive reveal (e.g. opening a menu or
                    # accordion) so its contents are sampled too.
                    page.locator(args.reveal).first.click()

                # `Page.accessibility` is gone as of Playwright 1.62;
                # `Locator.aria_snapshot()` on the document root is the
                # supported replacement. It returns a YAML-ish string
                # rather than a dict, written verbatim so the file stays
                # human-readable — the reported path key ("accessibility")
                # and the four artifact paths are unchanged.
                tree = page.locator("html").aria_snapshot()
                with open(accessibility_path, "w", encoding="utf-8") as fh:
                    fh.write(tree)

                testids = page.evaluate(
                    "() => Array.from(document.querySelectorAll("
                    "'[data-testid],[data-anchor]')).map(el => ({"
                    "tag: el.tagName.toLowerCase(),"
                    "testid: el.getAttribute('data-testid'),"
                    "anchor: el.getAttribute('data-anchor'),"
                    "text: (el.textContent || '').trim().slice(0, 80)"
                    "}))")
                with open(testids_path, "w", encoding="utf-8") as fh:
                    json.dump(testids, fh, indent=2)

                html = page.content()
                if len(html) > _PROBE_HTML_TRUNCATE_CHARS:
                    html = (html[:_PROBE_HTML_TRUNCATE_CHARS]
                           + "\n<!-- truncated -->\n")
                with open(html_path, "w", encoding="utf-8") as fh:
                    fh.write(html)

                page.screenshot(path=screenshot_path)
            finally:
                context.close()
                browser.close()
    except Exception as exc:  # noqa: BLE001 - report any failure
        print("Error: probe failed: %s" % exc, file=sys.stderr)
        return 1

    print(json.dumps({
        "ok": True,
        "accessibility": accessibility_path,
        "testids": testids_path,
        "html": html_path,
        "screenshot": screenshot_path,
    }))
    return 0


# Title card geometry — matches `postprocess.py`'s default assembly frame
# size (`title_card_clip_argv`/`concat_argv`'s `width=1280, height=720`), so
# rendering at this size needs no upscale before `ffmpeg` composites it.
_TITLE_CARD_WIDTH = 1280
_TITLE_CARD_HEIGHT = 720

# drive-brand-frames: the title card's dark ground and the shipd wordmark
# gradient, run left-to-right across the title text exactly as
# `wordmark.py`'s terminal banner runs it left-to-right across its art
# (`wordmark.py:50`, `START_RGB`/`END_RGB`).
_TITLE_CARD_BG = "#0f172a"
_WORDMARK_GRADIENT_START = "#8888a0"
_WORDMARK_GRADIENT_END = "#c6ff4e"
_COFFEE_GLYPH = "☕"  # drive-brand-frames: the hero glyph, U+2615

# The badge's own flat palette — no border, no glow (drive-brand-frames), a
# solid pill on the same dark ground as the title card with the wordmark's
# lime accent for its text, so the two branded assets read as one family.
_BADGE_BG = "#0f172a"
_BADGE_FG = "#c6ff4e"
_BADGE_CHEVRON = "›"  # a single chevron, ›

_DEFAULT_TITLE = "shipd"
_DEFAULT_SPEED = "10x"


def _title_card_html(title):
    return """<!doctype html>
<html><head><meta charset="utf-8"><style>
  html, body {{
    margin: 0; padding: 0;
    width: {w}px; height: {h}px;
    background: {bg};
  }}
  .card {{
    width: 100%; height: 100%;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
  }}
  .glyph {{ font-size: 96px; line-height: 1; margin-bottom: 28px; }}
  .title {{
    font-size: 64px; font-weight: 700; letter-spacing: 2px;
    background-image: linear-gradient(90deg, {start} 0%, {end} 100%);
    -webkit-background-clip: text; background-clip: text;
    color: transparent; -webkit-text-fill-color: transparent;
  }}
</style></head>
<body>
  <div class="card">
    <div class="glyph">{glyph}</div>
    <div class="title">{title}</div>
  </div>
</body></html>""".format(
        w=_TITLE_CARD_WIDTH, h=_TITLE_CARD_HEIGHT, bg=_TITLE_CARD_BG,
        start=_WORDMARK_GRADIENT_START, end=_WORDMARK_GRADIENT_END,
        glyph=_COFFEE_GLYPH, title=html.escape(title))


def _badge_html(speed, width, height):
    return """<!doctype html>
<html><head><meta charset="utf-8"><style>
  html, body {{
    margin: 0; padding: 0;
    width: {w}px; height: {h}px;
    background: transparent;
  }}
  .pill {{
    width: 100%; height: 100%;
    border-radius: {radius}px;
    background: {bg};
    border: none; box-shadow: none;
    display: flex; align-items: center; justify-content: center;
    gap: 6px;
    font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
    font-weight: 700; font-size: {font}px;
    color: {fg};
  }}
</style></head>
<body>
  <div class="pill">
    <span>{speed}</span><span>{chevron}</span>
  </div>
</body></html>""".format(
        w=width, h=height, radius=height // 2, bg=_BADGE_BG,
        font=int(height * 0.45), fg=_BADGE_FG,
        speed=html.escape(speed), chevron=_BADGE_CHEVRON)


def cmd_cards(args):
    """Render the shipd-branded title card and fast-forward badge frames,
    per drive-brand-frames.

    Both are rendered by loading a small self-contained HTML/CSS document
    into a Playwright page sized to the exact target pixel geometry and
    screenshotting it — a browser's own text/gradient rendering, not a
    third-party imaging library (this file's PEP 723 header declares only
    `playwright`).

    `--kind title`: the U+2615 coffee mark as the hero glyph, above the
    title, on `#0f172a`, with the shipd wordmark gradient (`#8888a0` to
    `#c6ff4e`) run across the title text.

    `--kind badge`: a flat pill at `postprocess.py`'s `BADGE_WIDTH` x
    `BADGE_HEIGHT` (at most 180 x 44 pixels at the 1280x720 frame those
    constants are defined for), carrying the speed factor and a single
    chevron, with no border and no glow — rendered with a transparent
    background (`omit_background=True`) so `postprocess.py`'s overlay
    compositing shows only the pill itself.
    """
    from playwright.sync_api import sync_playwright

    out_path = args.out
    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    try:
        if args.kind == "title":
            width, height = _TITLE_CARD_WIDTH, _TITLE_CARD_HEIGHT
            content = _title_card_html(args.title or _DEFAULT_TITLE)
            omit_background = False
        else:
            width, height = pp.BADGE_WIDTH, pp.BADGE_HEIGHT
            content = _badge_html(args.speed or _DEFAULT_SPEED, width, height)
            omit_background = True

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(
                viewport={"width": width, "height": height})
            try:
                page.set_content(content)
                page.screenshot(path=out_path, omit_background=omit_background)
            finally:
                browser.close()
    except Exception as exc:  # noqa: BLE001 - report any failure
        print("Error: cards failed: %s" % exc, file=sys.stderr)
        return 1

    print(json.dumps({
        "ok": True, "kind": args.kind, "path": out_path,
        "width": width, "height": height,
    }))
    return 0


def cmd_install_browser(args):
    """Install the Playwright browser binary every other verb needs.

    Invoked by ``drive.py doctor --fix`` (drive-doctor) after it has already
    stated the network access this performs. Shells to Playwright's own
    installer CLI (``python -m playwright install <browser>``) rather than
    importing internal Playwright modules, since the installer is the one
    documented entry point for fetching browser binaries.
    """
    import subprocess

    browser = args.browser
    try:
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", browser],
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        print("browser_worker: install-browser failed: %s" % exc,
              file=sys.stderr)
        return 1
    except OSError as exc:
        print("browser_worker: install-browser failed: %s" % exc,
              file=sys.stderr)
        return 1
    print(json.dumps({"ok": True, "browser": browser}))
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="browser_worker",
        description="Playwright worker behind drive.py (shipd-drive)",
    )
    sub = parser.add_subparsers(dest="command")

    p_login = sub.add_parser(
        "login", help="log in and write the target's storage state")
    p_login.add_argument("--url", required=True,
                          help="the target's login URL")
    p_login.add_argument("--out", required=True,
                          help="path to write the storage state JSON to")
    p_login.add_argument("--debug-screenshot", default=None,
                          help="path to write a screenshot to on failure")
    p_login.add_argument("--manual", action="store_true",
                          help="open a visible window and let the human at "
                               "the keyboard log in; reads no credential")
    p_login.add_argument("--done", default=None,
                          help="completion signal ending a manual login "
                               "(the `wait` verb's grammar); without one, "
                               "the URL leaving the login page while the "
                               "host still matches ends it")
    p_login.add_argument("--timeout", type=float,
                          default=DEFAULT_MANUAL_TIMEOUT_SECONDS,
                          help="seconds to wait for a manual login's "
                               "completion signal (default: %(default)s)")
    p_login.set_defaults(func=cmd_login)

    p_session = sub.add_parser(
        "session", help="own one browser/page and serve the socket")
    p_session.add_argument("--target", required=True,
                            help="the target name this session drives")
    p_session.add_argument("--url", required=True,
                            help="the target's base URL")
    p_session.add_argument("--storage-state", default=None,
                            help="path to a cached storage state to load")
    p_session.add_argument("--socket", required=True,
                            help="Unix socket path to listen on")
    p_session.add_argument("--headed", action="store_true",
                            help="launch the browser visible instead of "
                                 "headless; a headless one can still be "
                                 "relaunched visible later by `handoff`")
    p_session.set_defaults(func=cmd_session)

    p_probe = sub.add_parser(
        "probe", help="read-only DOM/accessibility sampler")
    p_probe.add_argument("--url", required=True,
                          help="URL to navigate to before sampling")
    p_probe.add_argument("--storage-state", default=None,
                          help="path to a cached storage state to load")
    p_probe.add_argument("--reveal", default=None,
                          help="a single non-destructive selector to click "
                               "before sampling")
    p_probe.add_argument("--out", required=True,
                          help="directory to write the probe's evidence to")
    p_probe.set_defaults(func=cmd_probe)

    p_cards = sub.add_parser(
        "cards", help="render branded title-card / badge frames")
    p_cards.add_argument("--kind", required=True, choices=["title", "badge"],
                          help="which frame to render")
    p_cards.add_argument("--title", default=None,
                          help="title-card text (kind=title)")
    p_cards.add_argument("--speed", default=None,
                          help="speed factor label, e.g. 10x (kind=badge)")
    p_cards.add_argument("--corner", default="bottom-right",
                          help="badge corner placement (kind=badge)")
    p_cards.add_argument("--out", required=True,
                          help="path to write the rendered frame image to")
    p_cards.set_defaults(func=cmd_cards)

    p_install = sub.add_parser(
        "install-browser", help="download the Playwright browser binary")
    p_install.add_argument("--browser", default="chromium",
                            help="the Playwright browser to install "
                                 "(default: chromium)")
    p_install.set_defaults(func=cmd_install_browser)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_usage(sys.stderr)
        return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
