#!/usr/bin/env python3
"""Unit tests for `drive.py`'s verdict computation (drive-verdict): pure
function tests, no session daemon and no browser involved — the console and
network evidence is handed in directly, exactly the shape the session
daemon's `console`/`network` verbs already return (each console event a
`{"type", "text", "time"}` dict; each network event a `{"url", "status",
"method", "time"}` dict, per `browser_worker.py`'s `_on_console`/
`_on_response` listeners).

Covers: an error present in the baseline console set and again in the final
one does not fail the run (pre-existing noise); a warning never fails
regardless of when it appears; a 4xx/5xx response to the target's own origin
fails the run and the evidence names the request; and a completion signal
that was never observed yields `FAIL` stating so, even with otherwise clean
evidence.

`drive.py` is stdlib-only, so this suite runs with no Playwright/ffmpeg/uv
installed at all — it imports `drive` directly, the same way
`test_drive_postprocess.py` imports `postprocess` directly for its pure
span algebra."""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import drive  # noqa: E402


TARGET_ORIGIN = "https://app.example"


class PreExistingNoiseTest(unittest.TestCase):
    def test_error_in_baseline_and_again_afterward_does_not_fail(self):
        baseline = [{"type": "error", "text": "favicon.ico 404"}]
        final = [{"type": "error", "text": "favicon.ico 404"}]

        verdict, evidence = drive.compute_verdict(
            baseline_console=baseline, final_console=final,
            network_events=[], target_origin=TARGET_ORIGIN,
            signal_observed=True, signal_name="save-complete")

        self.assertEqual(verdict, "PASS", evidence)


class WarningNeverFailsTest(unittest.TestCase):
    def test_a_warning_never_fails_the_run(self):
        baseline = []
        final = [{"type": "warning", "text": "Deprecated API usage"}]

        verdict, evidence = drive.compute_verdict(
            baseline_console=baseline, final_console=final,
            network_events=[], target_origin=TARGET_ORIGIN,
            signal_observed=True, signal_name="save-complete")

        self.assertEqual(verdict, "PASS", evidence)


class ServerErrorFailsTest(unittest.TestCase):
    def test_500_response_to_target_origin_fails_and_names_the_request(self):
        network = [{"url": "https://app.example/api/save",
                   "status": 500, "method": "POST"}]

        verdict, evidence = drive.compute_verdict(
            baseline_console=[], final_console=[],
            network_events=network, target_origin=TARGET_ORIGIN,
            signal_observed=True, signal_name="save-complete")

        self.assertEqual(verdict, "FAIL")
        joined = "\n".join(evidence)
        self.assertIn("500", joined)
        self.assertIn("https://app.example/api/save", joined)

    def test_a_4xx_response_to_a_different_origin_does_not_fail(self):
        # Only the target's own origin counts (drive-verdict: "any 4xx or
        # 5xx response to the target's own origin"); a third-party asset
        # 404ing is not evidence against this run.
        network = [{"url": "https://cdn.example/font.woff2",
                   "status": 404, "method": "GET"}]

        verdict, evidence = drive.compute_verdict(
            baseline_console=[], final_console=[],
            network_events=network, target_origin=TARGET_ORIGIN,
            signal_observed=True, signal_name="save-complete")

        self.assertEqual(verdict, "PASS", evidence)


class MissingCompletionSignalTest(unittest.TestCase):
    def test_unobserved_signal_fails_even_with_otherwise_clean_evidence(self):
        verdict, evidence = drive.compute_verdict(
            baseline_console=[], final_console=[],
            network_events=[], target_origin=TARGET_ORIGIN,
            signal_observed=False, signal_name="save-complete")

        self.assertEqual(verdict, "FAIL")
        joined = " ".join(evidence).lower()
        self.assertIn("save-complete", joined)
        self.assertIn("never observed", joined)


if __name__ == "__main__":
    unittest.main()
