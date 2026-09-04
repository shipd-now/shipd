#!/usr/bin/env python3
"""Tests for render.py's interactive ``screen`` mode — the textual viewer.

Requires `textual` (``pip install -r requirements.txt``), which is why this
sits beside ``test_dashboard.py`` rather than in the stdlib-only
``plugins/s/skills/build/tests/``: ``render.py`` itself imports without
textual, but building its viewer app does not. The substitution function and
the ``output`` verb are covered by ``tests/test_render.py``, which must keep
passing with no display packages installed at all.

The app is driven headless via ``App.run_test``/``Pilot``, the style the board's
own app tests use.
"""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
sys.path.insert(0, SCRIPTS)

import render  # noqa: E402

from textual.containers import VerticalScroll  # noqa: E402
from textual.widgets import Markdown  # noqa: E402

# The same supported flowchart the stdlib suite renders — spaced arrows, which
# the vendored renderer needs to read an edge as an edge.
DOCUMENT = ("# Overview\n\nBefore.\n\n"
            "```mermaid\ngraph LR\n  A[Plan] --> B[Build]\n```\n\nAfter.\n")

BOX_DRAWING = "─│┌┐└┘"


class ViewerAppTest(unittest.IsolatedAsyncioTestCase):
    async def test_markdown_widget_holds_the_substituted_document(self):
        app = render.viewer_app(DOCUMENT)
        async with app.run_test():
            markdown = app.query_one(Markdown)
            self.assertEqual(markdown.source,
                             render.substitute_mermaid_fences(DOCUMENT))
            self.assertIn("```text", markdown.source)
            self.assertNotIn("```mermaid", markdown.source)
            self.assertTrue(
                any(ch in markdown.source for ch in BOX_DRAWING),
                markdown.source)
            # The prose either side of the diagram is untouched.
            self.assertIn("Before.", markdown.source)
            self.assertIn("After.", markdown.source)

    async def test_the_document_is_scrollable(self):
        app = render.viewer_app(DOCUMENT)
        async with app.run_test():
            scroll = app.query_one(VerticalScroll)
            self.assertTrue(list(scroll.query(Markdown)))

    async def test_ascii_charset_reaches_the_widget(self):
        app = render.viewer_app(DOCUMENT, use_ascii=True)
        async with app.run_test():
            source = app.query_one(Markdown).source
            self.assertIn("```text", source)
            self.assertTrue(all(ord(ch) < 128 for ch in source),
                            sorted({ch for ch in source if ord(ch) > 127}))

    async def test_unrenderable_fence_reaches_the_widget_unchanged(self):
        document = '# Chart\n\n```mermaid\npie title Pets\n    "Dogs" : 386\n```\n'
        app = render.viewer_app(document)
        async with app.run_test():
            self.assertEqual(app.query_one(Markdown).source, document)

    async def test_q_quits_the_app(self):
        app = render.viewer_app(DOCUMENT)
        async with app.run_test() as pilot:
            await pilot.press("q")
            await pilot.pause()
            self.assertFalse(app.is_running)
        self.assertEqual(app.return_code, 0)

    async def test_escape_quits_the_app(self):
        app = render.viewer_app(DOCUMENT)
        async with app.run_test() as pilot:
            await pilot.press("escape")
            await pilot.pause()
            self.assertFalse(app.is_running)
        self.assertEqual(app.return_code, 0)


if __name__ == "__main__":
    unittest.main()
