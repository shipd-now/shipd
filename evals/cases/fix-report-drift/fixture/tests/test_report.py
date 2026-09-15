"""Shipped suite for the `fix-report-drift` eval fixture.

Asserts the header line and the fixed-width column padding of
`report.main()`'s output — behavior the fixture already satisfies, so this
suite is green before any session runs. It does NOT assert row order: that is
the held-out oracle at `evals/cases/fix-report-drift/verify/`, kept outside
this fixture so a session cannot read or weaken it.
"""

import contextlib
import io
import os
import sys
import unittest

# Reach the fixture's `src/report.py` the same way
# `evals/tests/test_runner.py` reaches `run.py`: insert the sibling `src/`
# directory (one level above `tests/`) onto `sys.path`. This resolves
# correctly both in place under `fixture/` and after the grader copies this
# file to `<scratch>/tests/`, since `src/` sits next to `tests/` in both
# locations.
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

    def test_rows_are_padded_columns(self):
        lines = _run_report()
        self.assertGreater(len(lines), 1)
        for line in lines[1:]:
            # "%-6s  %3d  %s" — name left-padded to width 6, two spaces, age
            # right-justified to width 3, two spaces, team.
            self.assertEqual(len(line[:6]), 6)
            self.assertEqual(line[6:8], "  ")
            self.assertTrue(line[8:11].strip().isdigit())
            self.assertEqual(line[11:13], "  ")


if __name__ == "__main__":
    unittest.main()
