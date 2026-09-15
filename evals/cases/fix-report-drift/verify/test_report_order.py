"""Held-out oracle for the `fix-report-drift` eval case.

Kept outside `fixture/` so a session cannot read or weaken it: the runner
copies this file into `<scratch>/tests/` only after the session ends (see
`evals/run.py`'s `grade_behavior`). It asserts the row order documented by
`.shipd/verified/report-output/spec.md`'s `report-row-order` requirement —
team ascending, then name ascending — which the fixture's seeded
`src/report.py` violates by iterating `ROWS` in declaration order instead.
"""

import contextlib
import io
import os
import sys
import unittest

# Reach `src/report.py` the same way `fixture/tests/test_report.py` does:
# insert the sibling `src/` directory (one level above `tests/`) onto
# `sys.path`. Once the runner copies this file to `<scratch>/tests/`,
# `src/` sits next to it at `<scratch>/src/`, resolving correctly.
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURE_DIR = os.path.dirname(TESTS_DIR)
SRC_DIR = os.path.join(FIXTURE_DIR, "src")
sys.path.insert(0, SRC_DIR)

import report  # noqa: E402


class ReportRowOrderTests(unittest.TestCase):

    def test_rows_print_sorted_by_team_then_name(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            report.main()
        lines = buf.getvalue().splitlines()
        names_in_order = [line.split()[0] for line in lines[1:]]
        # design < engineering < sales: carol (design), alice (engineering),
        # bob (sales).
        self.assertEqual(names_in_order, ["carol", "alice", "bob"])


if __name__ == "__main__":
    unittest.main()
