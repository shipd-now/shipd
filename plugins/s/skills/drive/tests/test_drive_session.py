#!/usr/bin/env python3
"""Unit tests for `drive.py`'s session-daemon client side (drive-session):
the driving verbs as thin socket clients, `console` relaying whatever the
daemon returns (the daemon's own job is buffering events across navigation
— covered separately in `browser_worker.py`, which these tests never
import), `session start` replacing a running session for a different
target, and `session status` reporting a stale socket.

None of this touches Playwright. Two fake-server strategies stand in for
the real `browser_worker.py session` daemon:

- For the plain driving-verb tests, a small in-process Python `socket`
  server (`_FakeSessionServer`) is bound directly to a Unix socket under a
  throwaway `$HOME`, and this test writes the session state file
  `drive.py` is expected to read by hand — no `session start` involved, so
  these tests exercise only "does a driving verb send the right request and
  print the right reply."
- For `session start`/`status`, which spawn a background worker through
  `uv run`, the restricted test `PATH`'s `uv` is itself a tiny real NDJSON
  socket server (mirroring `test_drive_targets.py`'s spy-script approach):
  it binds the requested socket, writes a `running-<target>.pid` marker so
  the test can observe it being alive, and tears both down on a `close`
  request or `SIGTERM` — whichever mechanism `drive.py` uses to stop the
  previous session, this spy reacts to it.

Session state contract this suite pins (`drive-session`, no prior task
having fixed it yet): a session state file at
``~/.shipd/drive/session.json`` holding ``{"target", "pid", "socket"}``,
and a **fixed** socket path ``~/.shipd/drive/session.sock`` (drive-skill's
plan.md: "a Unix socket at ``~/.shipd/drive/session.sock``") — one session
at a time, never one per target.
"""

import json
import os
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
SCRIPT = os.path.join(SCRIPTS, "drive.py")

SESSION_SUBDIR = os.path.join(".shipd", "drive")
SESSION_STATE_NAME = "session.json"
SESSION_SOCKET_NAME = "session.sock"


def _read_request(conn):
    data = b""
    while not data.endswith(b"\n"):
        chunk = conn.recv(65536)
        if not chunk:
            break
        data += chunk
    return json.loads(data.decode("utf-8")) if data else {}


def _write_reply(conn, reply):
    conn.sendall((json.dumps(reply) + "\n").encode("utf-8"))


class _FakeSessionServer:
    """A minimal in-process stand-in for `browser_worker.py session`'s
    socket protocol: one NDJSON request in, one JSON reply out, per
    connection. `console_events` seeds what a `console` request replies
    with, standing in for events the real daemon would have buffered
    before this test's driving verb ever ran."""

    def __init__(self, socket_path, console_events=None,
                 reply_overrides=None):
        self.socket_path = socket_path
        self.console_events = console_events or []
        self.reply_overrides = reply_overrides or {}
        self.received = []
        self._srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        if os.path.exists(socket_path):
            os.remove(socket_path)
        self._srv.bind(socket_path)
        self._srv.listen(5)
        self._srv.settimeout(0.2)
        self._stop = False
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def _serve(self):
        while not self._stop:
            try:
                conn, _ = self._srv.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            with conn:
                request = _read_request(conn)
                self.received.append(request)
                op = request.get("op")
                if op in self.reply_overrides:
                    _write_reply(conn, self.reply_overrides[op])
                elif op == "console":
                    _write_reply(conn, {"ok": True,
                                        "events": self.console_events})
                else:
                    _write_reply(conn, {"ok": True, "echo": request})

    def close(self):
        self._stop = True
        self._thread.join(timeout=2)
        self._srv.close()
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)


_UV_SESSION_SPY = """#!{python}
import json
import os
import signal
import socket
import sys

argv = sys.argv[1:]


def _arg(flag):
    return argv[argv.index(flag) + 1] if flag in argv else None


target = _arg("--target")
sock_path = _arg("--socket")
marker_dir = os.environ["DRIVE_TEST_MARKER_DIR"]
marker_path = os.path.join(marker_dir, "running-%s.pid" % target)

with open(marker_path, "w", encoding="utf-8") as fh:
    fh.write(str(os.getpid()))


def _cleanup(*_a):
    try:
        os.remove(marker_path)
    except OSError:
        pass
    try:
        os.remove(sock_path)
    except OSError:
        pass
    sys.exit(0)


signal.signal(signal.SIGTERM, _cleanup)

if os.path.exists(sock_path):
    os.remove(sock_path)
srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
srv.bind(sock_path)
srv.listen(5)
srv.settimeout(0.5)

while True:
    try:
        conn, _ = srv.accept()
    except socket.timeout:
        continue
    except OSError:
        break
    data = b""
    while not data.endswith(b"\\n"):
        chunk = conn.recv(65536)
        if not chunk:
            break
        data += chunk
    try:
        req = json.loads(data.decode("utf-8")) if data else {{}}
    except Exception:
        req = {{}}
    op = req.get("op")
    if op == "close":
        conn.sendall((json.dumps({{"ok": True}}) + "\\n").encode("utf-8"))
        conn.close()
        _cleanup()
    reply = {{"ok": True, "op": op, "target": target}}
    conn.sendall((json.dumps(reply) + "\\n").encode("utf-8"))
    conn.close()
"""


class DriveSessionTestBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="drive-session-")
        self.home = os.path.join(self.tmp, "home")
        os.makedirs(os.path.join(self.home, SESSION_SUBDIR), exist_ok=True)
        self._servers = []

    def tearDown(self):
        for server in self._servers:
            server.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def state_path(self):
        return os.path.join(self.home, SESSION_SUBDIR, SESSION_STATE_NAME)

    def socket_path(self):
        return os.path.join(self.home, SESSION_SUBDIR, SESSION_SOCKET_NAME)

    def write_state(self, target, pid, sock_path=None):
        with open(self.state_path(), "w", encoding="utf-8") as fh:
            json.dump({"target": target, "pid": pid,
                      "socket": sock_path or self.socket_path()}, fh)

    def start_fake_server(self, console_events=None, reply_overrides=None):
        server = _FakeSessionServer(self.socket_path(),
                                    console_events=console_events,
                                    reply_overrides=reply_overrides)
        self._servers.append(server)
        return server

    def run_cli(self, *args, path_dir=None, extra_env=None):
        env = {"PATH": path_dir or "/usr/bin:/bin", "HOME": self.home}
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            [sys.executable, SCRIPT, *args],
            capture_output=True, text=True, env=env)


class DrivingVerbSendsOneRequestTest(DriveSessionTestBase):
    def test_a_driving_verb_sends_one_request_and_prints_the_reply(self):
        server = self.start_fake_server()
        self.write_state("app", os.getpid())

        r = self.run_cli("open", "https://app.example/dashboard")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(len(server.received), 1)
        self.assertEqual(server.received[0].get("op"), "open")
        self.assertEqual(server.received[0].get("url"),
                         "https://app.example/dashboard")
        # The reply the fake daemon sent back is what gets printed.
        self.assertIn("echo", r.stdout)


class ConsoleReturnsPriorEventsTest(DriveSessionTestBase):
    def test_console_returns_events_recorded_before_the_verb_ran(self):
        seeded = [{"type": "error", "text": "boom", "time": 1.0}]
        self.start_fake_server(console_events=seeded)
        self.write_state("app", os.getpid())

        r = self.run_cli("console")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("boom", r.stdout)


class SessionStartReplacesDifferentTargetTest(DriveSessionTestBase):
    def spy_bindir(self):
        d = os.path.join(self.tmp, "bin")
        os.makedirs(d, exist_ok=True)
        uv_path = os.path.join(d, "uv")
        with open(uv_path, "w", encoding="utf-8") as fh:
            fh.write(_UV_SESSION_SPY.format(python=sys.executable))
        os.chmod(uv_path, os.stat(uv_path).st_mode
                 | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        return d

    def marker_path(self, target):
        return os.path.join(self.tmp, "running-%s.pid" % target)

    def wait_for(self, predicate, timeout=5.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if predicate():
                return True
            time.sleep(0.05)
        return predicate()

    def test_starting_a_different_target_stops_the_running_daemon_first(
            self):
        bindir = self.spy_bindir()
        env = {"DRIVE_TEST_MARKER_DIR": self.tmp}

        r1 = self.run_cli("session", "start", "old-target",
                          path_dir=bindir, extra_env=env)
        self.assertEqual(r1.returncode, 0, r1.stderr)
        self.assertTrue(
            self.wait_for(lambda: os.path.isfile(
                self.marker_path("old-target"))),
            "the first session's daemon never started")

        r2 = self.run_cli("session", "start", "new-target",
                          path_dir=bindir, extra_env=env)
        self.assertEqual(r2.returncode, 0, r2.stderr)
        self.assertTrue(
            self.wait_for(lambda: os.path.isfile(
                self.marker_path("new-target"))),
            "the second session's daemon never started")
        self.assertTrue(
            self.wait_for(lambda: not os.path.isfile(
                self.marker_path("old-target"))),
            "the first session's daemon was never stopped")

        with open(self.state_path(), encoding="utf-8") as fh:
            state = json.load(fh)
        self.assertEqual(state.get("target"), "new-target")


class FailedVerbExitsNonZeroTest(DriveSessionTestBase):
    """drive-session: "If a reply carries a falsey `ok` field, then the
    verb SHALL still print that reply to stdout unchanged and SHALL exit
    non-zero" — covering the `wait` timeout scenario the requirement names
    explicitly, plus one other driving verb so the fix is known to be the
    shared `_print_reply` return value, not a `wait`-only special case."""

    def test_wait_timeout_reply_is_printed_and_exits_non_zero(self):
        timeout_reply = {
            "ok": False,
            "error": "Locator.wait_for: Timeout 20000ms exceeded.",
        }
        self.start_fake_server(reply_overrides={"wait": timeout_reply})
        self.write_state("app", os.getpid())

        r = self.run_cli("wait", "#search", "--timeout", "20")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Timeout 20000ms exceeded", r.stdout)
        printed = json.loads(r.stdout)
        self.assertEqual(printed, timeout_reply)

    def test_a_failed_click_reply_is_printed_and_exits_non_zero(self):
        failed_reply = {"ok": False, "error": "no such element: #missing"}
        self.start_fake_server(reply_overrides={"click": failed_reply})
        self.write_state("app", os.getpid())

        r = self.run_cli("click", "#missing")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no such element: #missing", r.stdout)
        printed = json.loads(r.stdout)
        self.assertEqual(printed, failed_reply)

    def test_a_successful_reply_still_exits_zero(self):
        # Guards against an overcorrection that fails every reply outright.
        self.start_fake_server()
        self.write_state("app", os.getpid())

        r = self.run_cli("open", "https://app.example/dashboard")
        self.assertEqual(r.returncode, 0, r.stderr)


class SessionStatusReportsStaleSocketTest(DriveSessionTestBase):
    def test_session_status_reports_a_stale_socket(self):
        # A socket file left behind with nothing listening on it, and a pid
        # that is not (or no longer) running: `session status` must call
        # this out as stale rather than pretending the session is live.
        dead = subprocess.Popen([sys.executable, "-c", "pass"])
        dead.wait()
        dead_pid = dead.pid
        with open(self.socket_path(), "wb"):
            pass  # a plain file, not a bound socket — nothing is listening
        self.write_state("app", dead_pid)

        r = self.run_cli("session", "status")
        self.assertIn("stale", (r.stdout + r.stderr).lower())


if __name__ == "__main__":
    unittest.main()
