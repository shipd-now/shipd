#!/usr/bin/env python3
"""Guard the delivery board's modal close-control glyph width.

The historical spec-detail "overhang" was a terminal glyph-width desync, not a
Textual region overflow: an ambiguous-East-Asian-width close glyph — ``×``
U+00D7, ``east_asian_width`` ``A`` — renders two cells in ambiguous-as-wide
terminals, advancing the cursor one column past what Textual reserved and
pushing the accent title bar's right edge over the modal border. A region
measurement cannot see that (every widget region stays contained); only the
paint desyncs. The #158 chrome work standardized every close control on ``✕``
U+2715, whose ``east_asian_width`` is ``N`` (narrow, always one cell), which is
why the region-containment sweep measures contained everywhere.

This stdlib guard reads ``dashboard.py`` as source — no ``textual`` import, so it
runs in the dependency-free ``tests/`` suite — and asserts every board modal's
close-control label glyph is single-cell, so a regression to an ambiguous/wide
glyph fails CI (delivery-dashboard modal-chrome-containment).
"""

import os
import re
import unicodedata
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
DASHBOARD = os.path.normpath(
    os.path.join(HERE, "..", "scripts", "dashboard.py"))

# ``east_asian_width`` values that always occupy exactly one terminal cell.
# ``A`` (ambiguous) renders two cells in ambiguous-as-wide terminals and ``W``/
# ``F`` (wide) always do — all three are forbidden for a compact close control.
SAFE_WIDTHS = {"N", "Na", "H"}

# A close/clear control: an id-carrying ``Button`` whose id names a close or
# clear control (``close-detail``, ``epic-detail-close``, ``board-search-clear``,
# …), captured with its first-argument label literal. ``[^()]*?`` stays inside
# the single ``Button(...)`` call (a paren ends it), so a label never pairs with
# a sibling button's id.
_ID_BUTTON_RE = re.compile(
    r'Button\(\s*"([^"]*)"\s*,[^()]*?id="([\w-]+)"')
# The filter-chip remove control carries no id: a ``%``-format label tagged
# ``classes="filter-chip"``. Matched structurally (not by its glyph) so a
# regression that swaps the glyph is still inspected.
_CHIP_BUTTON_RE = re.compile(
    r'Button\(\s*"([^"]*)"\s*%\s*\([^)]*\)\s*,\s*classes="filter-chip"')

# Every close/clear control the scan must discover — a floor so the regexes can
# never silently match nothing and pass vacuously. New close controls are
# covered automatically by the id scan; this only guards the scan's own health.
_EXPECTED_IDS = frozenset({
    "close-detail",         # spec-detail modal (MemberDetailScreen)
    "epic-run-close",       # epic-run confirmation
    "epic-detail-close",    # epic-detail modal
    "graph-config-close",   # graph config dialog
    "close-metrics",        # metrics modal
    "picker-close",         # filter picker
    "board-search-clear",   # board search clear
})


class ModalCloseGlyphTest(unittest.TestCase):
    def setUp(self):
        with open(DASHBOARD, encoding="utf-8") as fh:
            self.src = fh.read()

    def _close_controls(self):
        """(control, label) for every close/clear control Button — the id
        controls plus the id-less filter-chip remove control."""
        controls = []
        for label, bid in _ID_BUTTON_RE.findall(self.src):
            if "close" in bid or "clear" in bid:
                controls.append((bid, label))
        for label in _CHIP_BUTTON_RE.findall(self.src):
            controls.append(("filter-chip", label))
        return controls

    def test_scan_discovers_every_known_close_control(self):
        found = {c for c, _ in self._close_controls()}
        self.assertFalse(
            _EXPECTED_IDS - found,
            "close-control scan missed %r" % (_EXPECTED_IDS - found,))
        self.assertIn(
            "filter-chip", found,
            "the filter-chip remove control was not discovered")

    def test_every_close_control_glyph_is_single_cell(self):
        controls = self._close_controls()
        self.assertTrue(controls, "no close controls discovered")
        for control, label in controls:
            for ch in label:
                width = unicodedata.east_asian_width(ch)
                self.assertIn(
                    width, SAFE_WIDTHS,
                    "close control %r label %r has glyph %r (U+%04X) of "
                    "east_asian_width %r — an ambiguous/wide glyph can render "
                    "two cells and overhang the modal border; use a narrow "
                    "glyph such as '✕' U+2715"
                    % (control, label, ch, ord(ch), width))

    def test_current_close_controls_use_narrow_cross(self):
        # The concrete state #158 standardized on: every close control uses
        # ✕ U+2715 (narrow) and none uses the confusable × U+00D7 (ambiguous).
        for control, label in self._close_controls():
            self.assertIn(
                "✕", label,
                "close control %r no longer uses '✕' U+2715: %r"
                % (control, label))
            self.assertNotIn(
                "×", label,
                "close control %r uses the ambiguous-width '×' U+00D7: %r"
                % (control, label))


if __name__ == "__main__":
    unittest.main()
