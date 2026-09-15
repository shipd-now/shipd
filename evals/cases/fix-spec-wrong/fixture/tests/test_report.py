"""Shipped suite for the `fix-spec-wrong` eval fixture.

Asserts the header line and the six-character column padding of
`report.main()`'s output for the rows whose names fit within that width —
behavior the fixture already satisfies, so this suite is green before any
session runs. It asserts nothing about `ROWS[2]` ("christopher"), whose name
is longer than the documented width and whose row therefore misaligns; that
misalignment is the symptom `prompt.md` describes, and the case's correct
outcome is a hand-off, not a code change, so this suite must stay green
whether or not a session touches it.
"""

import contextlib
import io
import os
import sys
import unittest

# Reach the fixture's `src/report.py` the same way
# `evals/cases/fix-report-drift/fixture/tests/test_report.py` does: insert
# the sibling `src/` directory (one level above `tests/`) onto `sys.path`.
# This resolves correctly both in place under `fixture/` and after the
# grader copies this file to `<scratch>/tests/`, since `src/` sits next to
# `tests/` in both locations.
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURE_DIR = os.path.dirname(TESTS_DIR)
SRC_DIR = os.path.join(FIXTURE_DIR, "src")
sys.path.insert(0, SRC_DIR)

import report  # noqa: E402


def _run_report():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        report.main()
    return buf.getvalue().splitlines()


class ReportOutputTests(unittest.TestCase):

    def test_header_line(self):
        lines = _run_report()
        self.assertEqual(lines[0], "name    age  team")

    def test_rows_are_padded_columns_for_names_that_fit(self):
        lines = _run_report()
        self.assertGreater(len(lines), 1)
        # Only the rows whose name fits within the documented six-character
        # width — ROWS[:2] ("alice", "bob") — are asserted here. ROWS[2]
        # ("christopher") is longer than six characters and is deliberately
        # left unasserted; see the module docstring.
        for line in lines[1:3]:
            # "%-6s  %3d  %s" — name left-padded to width 6, two spaces, age
            # right-justified to width 3, two spaces, team.
            self.assertEqual(len(line[:6]), 6)
            self.assertEqual(line[6:8], "  ")
            self.assertTrue(line[8:11].strip().isdigit())
            self.assertEqual(line[11:13], "  ")


if __name__ == "__main__":
    unittest.main()
