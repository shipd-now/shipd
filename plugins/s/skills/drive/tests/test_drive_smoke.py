#!/usr/bin/env python3
"""Live end-to-end smoke test for `drive.py`'s `probe` verb against a real,
installed Playwright browser (drive-skill-flow).

Every other suite under this directory stubs `uv`/the browser worker
entirely (`_stubs.py`'s spy binaries), which is exactly why none of them
caught Playwright 1.62 removing the `Page.accessibility` namespace
(`'Page' object has no attribute 'accessibility'`) — a stub can only be
wrong in the way it was written to be wrong. This case is the one test
shape that can catch a real Playwright API drift: it drives the actual
`browser_worker.py probe` subcommand through a real `uv run` against a real
Chromium build, so a removed/renamed API surfaces as an actual failure here.

Serves a small static page from a background `http.server` thread, runs the
real `probe` verb (`drive.py probe <url>`), and asserts the four artifact
files it reports all exist, are non-empty, and that the accessibility file's
ARIA output is non-empty and mentions the page's own content.

Guarded with `unittest.skipUnless` on `uv` being on PATH and a Playwright
browser binary being present (`drive.have("uv")` / `drive.browser_installed()`
— the same presence checks `doctor` itself uses), so CI, which installs
neither, skips this case cleanly, while a developer machine with both
actually runs it.

To avoid writing into a developer's real `~/.shipd/drive/`, the subprocess
runs under a scratch `HOME`; `PLAYWRIGHT_BROWSERS_PATH` and `UV_CACHE_DIR`
are pointed at the *real* browser cache and uv cache so this never
re-downloads a browser build or the `playwright` wheel on every run."""

import functools
import http.server
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
SCRIPT = os.path.join(SCRIPTS, "drive.py")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import drive  # noqa: E402

_SKIP_REASON = "needs `uv` on PATH and a Playwright browser binary installed"


def _live_prereqs_present():
    return drive.have("uv") and drive.browser_installed()


def _real_uv_cache_dir():
    """The developer's actual uv cache directory, resolved with this
    process's real environment (never the test's scratch `HOME`) so the
    probe subprocess reuses an already-resolved `playwright` environment
    instead of re-downloading the wheel under a fresh `HOME` every run."""
    try:
        r = subprocess.run(["uv", "cache", "dir"],
                           capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    return r.stdout.strip() or None


_PAGE_HTML = """<!doctype html>
<html>
<head><title>Drive Smoke Test</title></head>
<body>
  <h1>Hello Drive</h1>
  <button data-testid="reveal-btn">Reveal</button>
  <div id="content">Some content here.</div>
</body>
</html>
"""


@unittest.skipUnless(_live_prereqs_present(), _SKIP_REASON)
class ProbeSmokeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="drive-smoke-")
        site_dir = os.path.join(self.tmp, "site")
        os.makedirs(site_dir, exist_ok=True)
        with open(os.path.join(site_dir, "index.html"), "w",
                 encoding="utf-8") as fh:
            fh.write(_PAGE_HTML)

        handler = functools.partial(
            http.server.SimpleHTTPRequestHandler, directory=site_dir)
        self.httpd = http.server.ThreadingHTTPServer(
            ("127.0.0.1", 0), handler)
        self.port = self.httpd.server_address[1]
        self.server_thread = threading.Thread(
            target=self.httpd.serve_forever, daemon=True)
        self.server_thread.start()

        self.home = os.path.join(self.tmp, "home")
        os.makedirs(self.home, exist_ok=True)

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.server_thread.join(timeout=5)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_probe_writes_four_artifacts_with_nonempty_aria_output(self):
        url = "http://127.0.0.1:%d/index.html" % self.port

        env = dict(os.environ)
        env["HOME"] = self.home
        # Never touch the real `~/.shipd/drive/`, but still find the real
        # browser build and reuse the real uv/playwright resolution cache
        # — both live outside the scratch `HOME` this probe run is
        # otherwise confined to.
        env["PLAYWRIGHT_BROWSERS_PATH"] = drive.playwright_browsers_dir()
        cache_dir = _real_uv_cache_dir()
        if cache_dir:
            env["UV_CACHE_DIR"] = cache_dir

        r = subprocess.run(
            [sys.executable, SCRIPT, "probe", url],
            capture_output=True, text=True, env=env, timeout=180)
        self.assertEqual(r.returncode, 0, r.stderr)

        paths = {}
        for line in r.stdout.splitlines():
            key, sep, value = line.partition(":")
            if sep:
                paths[key.strip()] = value.strip()

        for key in ("accessibility", "testids", "html", "screenshot"):
            self.assertIn(key, paths, r.stdout)
            self.assertTrue(os.path.isfile(paths[key]), paths.get(key))
            self.assertGreater(os.path.getsize(paths[key]), 0, key)

        with open(paths["accessibility"], encoding="utf-8") as fh:
            aria = fh.read()
        self.assertTrue(aria.strip())
        self.assertIn("Hello Drive", aria)


if __name__ == "__main__":
    unittest.main()
