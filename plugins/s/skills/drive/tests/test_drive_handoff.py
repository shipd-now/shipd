#!/usr/bin/env python3
"""Unit tests for `browser_worker.py`'s handoff-window bookkeeping
(drive-handoff): the `handoff` and `resume` handlers' pure window algebra,
exercised directly against a fake session context.

These are the one part of the session daemon that *is* unit-testable without
a browser. `browser_worker.py` imports only the standard library and its
stdlib-only `postprocess` sibling at module scope — `playwright` is imported
inside the functions that actually drive a browser — so importing it here
needs nothing installed, and `_handle_handoff`/`_handle_resume` touch the
page only through two calls a stub can stand in for (`wait_for_timeout` and,
with a signal, the wait). Everything that needs a real browser — the
relaunch itself, whether the window is visible, whether evidence survives —
is covered by the manual smoke in the change's `tasks.md`, since CI has no
Playwright.

A fake `playwright` module is still installed in `sys.modules` before the
import, the same defensive stub `test_drive_helper_docs.py` puts in front of
`record_worker.py`: the module does not need it today, and this keeps the
suite passing with nothing installed even if a future edit moves that import
to module scope.

Covered: a second `handoff` while one is open refuses, opens no second
window, and relaunches nothing (drive-handoff's "a second handoff while one
is open fails"); `resume` closes the open window; `resume` with none open
refuses; and a `handoff`/`resume`/`handoff` cycle opens a second window
normally, so the guard rejects only the overlapping case.

The same fake-page approach reaches two more browser-free seams in the same
module, so they live here rather than in a third file that would duplicate
the stub: `_wait_for_manual_login`'s default completion rule (which URL it
compares against — the bug where a configured url lacking the trailing slash
Chromium adds ends the wait on first paint) and `_teardown`'s tolerance of a
browser the human already closed.
"""

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

if "playwright" not in sys.modules:
    _fake = types.ModuleType("playwright")
    _fake_sync = types.ModuleType("playwright.sync_api")
    _fake_sync.sync_playwright = None
    _fake_sync.TimeoutError = Exception
    sys.modules["playwright"] = _fake
    sys.modules["playwright.sync_api"] = _fake_sync

import browser_worker as bw  # noqa: E402


class _StubPage:
    """The only page surface these two handlers touch: `wait_for_timeout`
    (the `resume` drain and the idle pump) and `url`. Records its calls so a
    test can assert the drain really happened."""

    def __init__(self, url="https://app.example/dashboard"):
        self.url = url
        self.waits = []

    def wait_for_timeout(self, ms):
        self.waits.append(ms)


def _ctx(headed=True, handoffs=None):
    """A fake session context of the shape `cmd_session` builds. `headed`
    True by default so nothing here can reach `_relaunch_headed`, which
    needs a real browser — a test that accidentally triggered a relaunch
    would fail loudly on the missing `pw`/`browser` keys rather than
    silently pass."""
    return {
        "target": "app",
        "base_url": "https://app.example",
        "console_events": [],
        "network_events": [],
        "handoffs": [] if handoffs is None else handoffs,
        "headed": headed,
        "closed": False,
        "page": _StubPage(),
    }


class SecondHandoffWhileOneIsOpenTest(unittest.TestCase):
    def test_a_second_handoff_refuses_and_opens_no_second_window(self):
        ctx = _ctx()
        first = bw._handle_handoff(ctx)
        self.assertTrue(first["open"])
        self.assertEqual(len(ctx["handoffs"]), 1)

        with self.assertRaises(RuntimeError) as caught:
            bw._handle_handoff(ctx)

        # The refusal says which verb clears the window, so the caller's
        # next move is obvious from the reply alone.
        self.assertIn("already open", str(caught.exception))
        self.assertIn("resume", str(caught.exception))
        # Exactly one window, still open — never a second, and never a
        # first one quietly closed by the attempt.
        self.assertEqual(len(ctx["handoffs"]), 1)
        self.assertIsNone(ctx["handoffs"][0]["end"])

    def test_a_refused_handoff_relaunches_nothing(self):
        # A headless context with a window already open. `_relaunch_headed`
        # would need `ctx["pw"]`/`ctx["browser"]`, which this context does
        # not carry: if the guard ran after the relaunch instead of before
        # it, this would raise KeyError rather than the refusal, and the
        # session would have been rebuilt on the way to being told no.
        ctx = _ctx(headed=False,
                   handoffs=[{"start": 1000.0, "end": None}])

        with self.assertRaises(RuntimeError) as caught:
            bw._handle_handoff(ctx)

        self.assertIn("already open", str(caught.exception))
        self.assertFalse(ctx["headed"], "the browser was relaunched anyway")
        self.assertEqual(len(ctx["handoffs"]), 1)

    def test_the_console_reply_still_carries_exactly_one_window(self):
        ctx = _ctx()
        bw._handle_handoff(ctx)
        with self.assertRaises(RuntimeError):
            bw._handle_handoff(ctx)

        self.assertEqual(len(bw._handle_console(ctx)["handoffs"]), 1)
        self.assertEqual(len(bw._handle_network(ctx)["handoffs"]), 1)


class ResumeClosesTheWindowTest(unittest.TestCase):
    def test_resume_drains_then_closes_the_open_window(self):
        ctx = _ctx()
        bw._handle_handoff(ctx)

        reply = bw._handle_resume(ctx)

        # The drain is what stamps a human's last queued events inside the
        # window they belong to rather than after it.
        self.assertEqual(ctx["page"].waits, [50])
        self.assertIsNotNone(ctx["handoffs"][0]["end"])
        self.assertIsNotNone(reply["closed"]["end"])

    def test_resume_with_no_open_window_refuses(self):
        ctx = _ctx()

        with self.assertRaises(RuntimeError) as caught:
            bw._handle_resume(ctx)

        self.assertIn("no handoff window is open", str(caught.exception))

    def test_a_handoff_after_a_resume_opens_a_second_window(self):
        # The guard rejects overlap, never a later handoff: two sequential
        # takeovers are two windows.
        ctx = _ctx()
        bw._handle_handoff(ctx)
        bw._handle_resume(ctx)
        second = bw._handle_handoff(ctx)

        self.assertTrue(second["open"])
        self.assertEqual(len(ctx["handoffs"]), 2)
        self.assertIsNotNone(ctx["handoffs"][0]["end"])
        self.assertIsNone(ctx["handoffs"][1]["end"])


class HandoffOnAVisibleBrowserTest(unittest.TestCase):
    def test_an_already_visible_browser_relaunches_nothing(self):
        # drive-handoff: "while the browser is already visible it SHALL
        # relaunch nothing and reply with a falsey `relaunched` field".
        reply = bw._handle_handoff(_ctx(headed=True))

        self.assertFalse(reply["relaunched"])


class _RecordingPage:
    """A page that records the `wait_for_function` call
    `_wait_for_manual_login` makes, and reports whatever `url` the test
    gives it — which is the whole point: `page.url` is the browser's
    normalized URL, and the default completion rule has to compare against
    *that*, not the configured string."""

    def __init__(self, url):
        self.url = url
        self.calls = []

    def wait_for_function(self, expression, arg=None, timeout=None):
        self.calls.append({"expression": expression, "arg": arg,
                           "timeout": timeout})


class ManualLoginDefaultRuleTest(unittest.TestCase):
    """The default manual-login completion rule compares `location.href`
    against the URL the browser landed on. Comparing against the raw
    configured url instead is a silent, high-cost regression: Chromium
    normalizes `https://h` to `https://h/`, so the inequality holds from the
    first paint, the wait returns before anyone has logged in, and an
    unauthenticated storage state is cached for the whole TTL. These tests
    assert the argument is what `page.url` reports."""

    def test_the_rule_compares_against_the_landed_url(self):
        page = _RecordingPage("http://h/")

        bw._wait_for_manual_login(page, "http://h/", None, 20)

        self.assertEqual(len(page.calls), 1)
        call = page.calls[0]
        self.assertEqual(call["arg"], ["http://h/", "h"])
        self.assertEqual(call["expression"], bw._MANUAL_DONE_JS)
        self.assertEqual(call["timeout"], 20 * 1000)

    def test_the_landed_url_wins_over_a_slashless_configured_url(self):
        # The regression case. The configured target url is `http://h` and
        # the browser lands on `http://h/`; `cmd_login` is what passes
        # `page.url` through, so the rule must see the trailing slash. An
        # implementation that forwarded the configured string would put
        # "http://h" here and `location.href !== u` would be true at once.
        page = _RecordingPage("http://h/")

        bw._wait_for_manual_login(page, page.url, None, 20)

        self.assertEqual(page.calls[0]["arg"], ["http://h/", "h"])
        self.assertNotEqual(page.calls[0]["arg"][0], "http://h")

    def test_the_notice_names_the_same_url_the_rule_compares(self):
        # The stderr notice and the wait must describe one URL, or the
        # person is told to wait for something other than what is checked.
        description = bw._manual_wait_description("http://h/", None)

        self.assertIn("http://h/", description)
        self.assertIn("h", description)

    def test_a_done_signal_bypasses_the_default_rule(self):
        page = _RecordingPage("http://h/")
        waited = []

        original = bw._wait_for_signal
        bw._wait_for_signal = lambda p, sig, t=None: waited.append((sig, t))
        try:
            bw._wait_for_manual_login(page, page.url, "url:**/home", 20)
        finally:
            bw._wait_for_signal = original

        self.assertEqual(waited, [("url:**/home", 20)])
        self.assertEqual(page.calls, [],
                         "the default rule ran despite an explicit signal")


class _FakeLoginPage:
    """A page for the `cmd_login` seam: `goto` records the requested url and
    then reports a *normalized* `url` the way Chromium would, so a test can
    tell which of the two `cmd_login` forwards to the completion rule."""

    def __init__(self, landed_url):
        self._landed_url = landed_url
        self.url = "about:blank"
        self.goto_urls = []
        self.waits = []
        self.context = self

    def goto(self, url, wait_until=None):
        self.goto_urls.append(url)
        self.url = self._landed_url

    def wait_for_function(self, expression, arg=None, timeout=None):
        self.waits.append({"expression": expression, "arg": arg,
                           "timeout": timeout})

    def screenshot(self, path=None):
        pass

    # `page.context` is this same object: `_write_storage_state_privately`
    # only needs a `storage_state(path=...)` that writes the file.
    def storage_state(self, path=None):
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"cookies": []}, fh)


class _FakeBrowser:
    def __init__(self, page):
        self._page = page
        self.launched_headless = None
        self.closed = False

    def new_page(self):
        return self._page

    def close(self):
        self.closed = True


class _FakePlaywright:
    def __init__(self, browser):
        self.chromium = self
        self._browser = browser

    def launch(self, headless=True):
        self._browser.launched_headless = headless
        return self._browser

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False


class _Args:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class ManualLoginSeamTest(unittest.TestCase):
    """The `cmd_login` seam — the actual site of the normalization bug. The
    helper tests above pin what `_wait_for_manual_login` does with the url it
    is handed; this pins which url `cmd_login` hands it, which is the half
    that was wrong. Playwright is faked through the same `sys.modules` stub
    this file already installs, so no browser is involved."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="drive-manual-seam-")
        self.page = _FakeLoginPage("https://app.example/")
        self.browser = _FakeBrowser(self.page)
        self.fake_pw = _FakePlaywright(self.browser)
        self._sync_api = sys.modules["playwright.sync_api"]
        self._original = getattr(self._sync_api, "sync_playwright", None)
        self._sync_api.sync_playwright = lambda: self.fake_pw

    def tearDown(self):
        self._sync_api.sync_playwright = self._original
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _args(self, **over):
        base = dict(url="https://app.example",
                    out=os.path.join(self.tmp, "app.json"),
                    debug_screenshot=None, manual=True, done=None,
                    timeout=20.0)
        base.update(over)
        return _Args(**base)

    def _run(self, args):
        """Run `cmd_login` with its streams captured — it prints the result
        JSON to stdout and the waiting notice to stderr, neither of which
        belongs in the test runner's output. Returns
        `(rc, stdout, stderr)`."""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), \
                contextlib.redirect_stderr(err):
            rc = bw.cmd_login(args)
        return rc, out.getvalue(), err.getvalue()

    def test_cmd_login_waits_on_the_landed_url_not_the_configured_one(self):
        # The configured url has no trailing slash; the browser lands on one.
        args = self._args()

        rc, _out, err = self._run(args)

        self.assertEqual(rc, 0)
        self.assertEqual(self.page.goto_urls, ["https://app.example"])
        self.assertEqual(len(self.page.waits), 1)
        # The rule must compare against what the browser reports. Forwarding
        # the configured "https://app.example" here would make
        # `location.href !== u` true on first paint, completing the manual
        # login before anyone logged in.
        self.assertEqual(self.page.waits[0]["arg"],
                         ["https://app.example/", "app.example"])
        self.assertNotEqual(self.page.waits[0]["arg"][0],
                            "https://app.example")
        # The notice names that same landed url, so the person is never told
        # to wait for something other than what is checked.
        self.assertIn("https://app.example/", err)

    def test_a_manual_login_launches_visible_and_writes_the_cache(self):
        args = self._args()

        rc, out, _err = self._run(args)

        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(out)["storageState"], args.out)
        self.assertIs(self.browser.launched_headless, False,
                      "a manual login launched headless")
        self.assertTrue(os.path.isfile(args.out))
        self.assertTrue(self.browser.closed)

    def test_a_manual_login_reads_no_credential_from_the_environment(self):
        # The environment carries both login variables; the manual path must
        # ignore them rather than treat them as a reason to drive the form.
        os.environ["DRIVE_LOGIN_USERNAME"] = "should-not-be-used"
        os.environ["DRIVE_LOGIN_PASSWORD"] = "should-not-be-used"
        try:
            rc, _out, _err = self._run(self._args())
        finally:
            del os.environ["DRIVE_LOGIN_USERNAME"]
            del os.environ["DRIVE_LOGIN_PASSWORD"]

        self.assertEqual(rc, 0)
        # One wait on the completion rule, and no form driving at all.
        self.assertEqual(len(self.page.waits), 1)


class _ClosingStub:
    """A context/browser stand-in whose `close()` either records or raises."""

    def __init__(self, raises=False):
        self.raises = raises
        self.closed = False

    def close(self):
        self.closed = True
        if self.raises:
            raise RuntimeError("Target page, context or browser has been "
                               "closed")


class TeardownToleratesAClosedBrowserTest(unittest.TestCase):
    """A handoff puts a visible window on the desktop, so a human can close
    it by hand. `_teardown` must not turn that into a traceback out of
    `cmd_session`'s `finally` during an ordinary `session stop`."""

    def test_a_raising_context_close_is_swallowed_and_the_browser_still_closes(
            self):
        context = _ClosingStub(raises=True)
        browser = _ClosingStub()
        ctx = {"context": context, "browser": browser}

        bw._teardown(ctx)  # must not raise

        self.assertTrue(context.closed)
        # The browser is the real OS process — skipping it would leak
        # Chromium past the end of the session.
        self.assertTrue(browser.closed,
                        "a failing context close skipped the browser close")

    def test_a_raising_browser_close_is_swallowed(self):
        ctx = {"context": _ClosingStub(), "browser": _ClosingStub(raises=True)}

        bw._teardown(ctx)  # must not raise

        self.assertTrue(ctx["browser"].closed)

    def test_both_closes_raising_is_still_survivable(self):
        ctx = {"context": _ClosingStub(raises=True),
               "browser": _ClosingStub(raises=True)}

        bw._teardown(ctx)  # must not raise

        self.assertTrue(ctx["context"].closed)
        self.assertTrue(ctx["browser"].closed)

    def test_a_context_that_was_never_opened_is_skipped(self):
        # A session that failed before `new_context` leaves these unset;
        # teardown is still expected to run without raising.
        bw._teardown({})
        bw._teardown({"context": None, "browser": None})


if __name__ == "__main__":
    unittest.main()
