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
"""

import os
import sys
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


if __name__ == "__main__":
    unittest.main()
