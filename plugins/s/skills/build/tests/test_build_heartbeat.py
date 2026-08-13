#!/usr/bin/env python3
"""Tests for heartbeat.py's interactive build-heartbeat CLI verbs.

Stdlib only and subprocess-driven: each test invokes ``heartbeat.py`` exactly
as the build skill does, so the env-derived session id, the invoking cwd as
``location``, the monotonic ``seq``, and the fail-soft exit-zero-on-write-
failure contract are all exercised end to end without importing ``textual``.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
HEARTBEAT_PY = os.path.join(SCRIPTS, "heartbeat.py")


def _plant_file(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


class BuildHeartbeatCliTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="build-heartbeat-test-")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _path(self, slug):
        return os.path.join(self.root, ".shipd", "autopilot",
                            "%s-build-heartbeat.json" % slug)

    def _read(self, slug):
        with open(self._path(slug), encoding="utf-8") as fh:
            return json.load(fh)

    def _run(self, args, cwd=None, session_id=None):
        """Invoke ``heartbeat.py`` with ``--root`` pinned to the test root. The
        parent's ``CLAUDE_CODE_SESSION_ID`` is always stripped first so a test
        controls the env datum outright; ``session_id`` re-supplies it."""
        env = dict(os.environ)
        env.pop("CLAUDE_CODE_SESSION_ID", None)
        if session_id is not None:
            env["CLAUDE_CODE_SESSION_ID"] = session_id
        return subprocess.run(
            [sys.executable, HEARTBEAT_PY] + args + ["--root", self.root],
            cwd=cwd or self.root, env=env,
            capture_output=True, text=True)

    def test_build_start_records_running_heartbeat(self):
        res = self._run(["build-start", "my-change"], session_id="sess-123")
        self.assertEqual(res.returncode, 0, res.stderr)
        hb = self._read("my-change")
        self.assertEqual(hb["state"], "running")
        self.assertEqual(hb["kind"], "build")
        self.assertEqual(hb["slug"], "my-change")
        self.assertEqual(hb["session_id"], "sess-123")
        self.assertEqual(os.path.realpath(hb["location"]),
                         os.path.realpath(self.root))
        self.assertGreater(hb["updated_at"], 0)

    def test_stage_transition_bumps_seq(self):
        self._run(["build-start", "my-change"], session_id="sess-123")
        start_seq = self._read("my-change")["seq"]
        res = self._run(["build-stage", "my-change", "--stage", "implement"],
                        session_id="sess-123")
        self.assertEqual(res.returncode, 0, res.stderr)
        hb = self._read("my-change")
        self.assertEqual(hb["stage"], "implement")
        self.assertGreater(hb["seq"], start_seq)
        self.assertEqual(hb["state"], "running")

    def test_finish_marks_finished_shipped(self):
        self._run(["build-start", "my-change"], session_id="sess-123")
        res = self._run(["build-finish", "my-change", "--outcome", "shipped"],
                        session_id="sess-123")
        self.assertEqual(res.returncode, 0, res.stderr)
        hb = self._read("my-change")
        self.assertEqual(hb["state"], "finished")
        self.assertEqual(hb["outcome"], "shipped")

    def test_build_start_stamps_started_at_once(self):
        res = self._run(["build-start", "my-change"], session_id="sess-123")
        self.assertEqual(res.returncode, 0, res.stderr)
        started_at = self._read("my-change").get("started_at")
        self.assertIsNotNone(started_at, "build-start should stamp started_at")
        self.assertGreater(started_at, 0)

        # A later build-stage leaves started_at unchanged.
        self._run(["build-stage", "my-change", "--stage", "implement"],
                  session_id="sess-123")
        self.assertEqual(self._read("my-change")["started_at"], started_at)

        # A repeated build-start leaves started_at unchanged.
        self._run(["build-start", "my-change"], session_id="sess-123")
        self.assertEqual(self._read("my-change")["started_at"], started_at)

    def test_missing_session_id_omits_the_field(self):
        res = self._run(["build-start", "my-change"], session_id=None)
        self.assertEqual(res.returncode, 0, res.stderr)
        hb = self._read("my-change")
        self.assertNotIn("session_id", hb)

    def test_unwritable_destination_exits_zero_with_warning(self):
        # Plant a plain file where the `autopilot/` directory must go so
        # `makedirs` raises and the atomic write fails.
        _plant_file(os.path.join(self.root, ".shipd", "autopilot"), "not a dir")
        res = self._run(["build-start", "my-change"], session_id="sess-123")
        self.assertEqual(res.returncode, 0)
        self.assertTrue(res.stderr.strip(), "expected a warning on stderr")


if __name__ == "__main__":
    unittest.main()
