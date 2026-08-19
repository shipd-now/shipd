#!/usr/bin/env python3
"""Unit tests for wordmark: the block-character "shipd now" banner, its
static render (plain or truecolor gradient), the finite two-phase animation,
and the script-level preview CLI.

The banner art is the contract's source of truth: it must stay byte-identical
to the fenced block at the top of the repository ``README.md``, so the tests
read that fence and compare against it rather than restating the art."""

import io
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
REPO_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", "..", ".."))
README = os.path.join(REPO_ROOT, "README.md")
WORDMARK = os.path.join(SCRIPTS, "wordmark.py")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import cli_common as cc  # noqa: E402,F401  (import parity with the module)
import wordmark  # noqa: E402

ESC = "\x1b"
RESET = "\x1b[0m"
LEFT = "\x1b[38;2;136;136;160m"
RIGHT = "\x1b[38;2;198;255;78m"
WHITE = "\x1b[38;2;255;255;255m"
HIDE = "\x1b[?25l"
SHOW = "\x1b[?25h"


def readme_banner():
    """Return the lines inside the README's opening fenced block."""
    with open(README, encoding="utf-8") as handle:
        lines = handle.read().split("\n")
    start = lines.index("```")
    end = lines.index("```", start + 1)
    return tuple(lines[start + 1:end])


class TtyStream(io.StringIO):
    """An in-memory stream that claims to be a terminal, so ``color_enabled``
    takes the colored path without needing a real pty."""

    def isatty(self):
        return True


class SpySleep(object):
    """A stand-in for ``time.sleep`` that records the delays asked for."""

    def __init__(self):
        self.calls = []

    def __call__(self, delay):
        self.calls.append(delay)


class ArtFidelityTest(unittest.TestCase):
    def test_art_equals_the_readme_fence(self):
        self.assertEqual(tuple(wordmark.ART), readme_banner())

    def test_art_is_not_empty(self):
        self.assertTrue(wordmark.ART)


class PlainRenderTest(unittest.TestCase):
    def test_piped_render_is_byte_identical_to_the_readme_banner(self):
        stream = io.StringIO()
        wordmark.render(stream)
        expected = "".join(line + "\n" for line in readme_banner())
        self.assertEqual(stream.getvalue(), expected)

    def test_piped_render_carries_no_escape_sequences(self):
        stream = io.StringIO()
        wordmark.render(stream)
        self.assertNotIn(ESC, stream.getvalue())

    def test_no_color_on_a_terminal_is_plain(self):
        stream = TtyStream()
        old = os.environ.get("NO_COLOR")
        os.environ["NO_COLOR"] = "1"
        try:
            wordmark.render(stream)
        finally:
            if old is None:
                os.environ.pop("NO_COLOR", None)
            else:
                os.environ["NO_COLOR"] = old
        out = stream.getvalue()
        self.assertNotIn(ESC, out)
        self.assertEqual(out, "".join(line + "\n" for line in readme_banner()))


class ColoredRenderTest(unittest.TestCase):
    def setUp(self):
        self._old = os.environ.pop("NO_COLOR", None)
        stream = TtyStream()
        wordmark.render(stream)
        self.out = stream.getvalue()

    def tearDown(self):
        if self._old is not None:
            os.environ["NO_COLOR"] = self._old

    def test_leftmost_glyph_column_uses_the_start_of_the_gradient(self):
        self.assertIn(LEFT + wordmark.ART[0][0], self.out)

    def test_rightmost_glyph_column_uses_the_end_of_the_gradient(self):
        width = max(len(line) for line in wordmark.ART)
        rightmost = [line[width - 1] for line in wordmark.ART
                     if len(line) >= width and line[width - 1] != " "]
        self.assertTrue(rightmost, "no glyph in the rightmost column")
        self.assertIn(RIGHT + rightmost[0], self.out)

    def test_every_line_resets_attributes_at_its_end(self):
        lines = self.out.split("\n")
        self.assertEqual(lines[-1], "")
        body = lines[:-1]
        self.assertEqual(len(body), len(wordmark.ART))
        for line in body:
            self.assertTrue(line.endswith(RESET), repr(line))

    def test_stripping_escapes_recovers_the_plain_art(self):
        import re
        plain = re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", self.out)
        self.assertEqual(plain, "".join(l + "\n" for l in readme_banner()))


class AnimateDisabledTest(unittest.TestCase):
    def test_non_tty_writes_one_plain_render_and_never_sleeps(self):
        stream = io.StringIO()
        spy = SpySleep()
        wordmark.animate(stream, sleep=spy)
        self.assertEqual(stream.getvalue(),
                         "".join(line + "\n" for line in readme_banner()))
        self.assertEqual(spy.calls, [])
        self.assertNotIn(ESC, stream.getvalue())


class AnimateEnabledTest(unittest.TestCase):
    def setUp(self):
        self._old = os.environ.pop("NO_COLOR", None)
        self.spy = SpySleep()
        stream = TtyStream()
        wordmark.animate(stream, sleep=self.spy)
        self.out = stream.getvalue()
        static = TtyStream()
        wordmark.render(static)
        self.static = static.getvalue()

    def tearDown(self):
        if self._old is not None:
            os.environ["NO_COLOR"] = self._old

    def test_animation_is_finite_and_bounded(self):
        self.assertGreater(len(self.spy.calls), 0)
        self.assertLess(len(self.spy.calls), 200)

    def test_cursor_is_hidden_then_restored(self):
        self.assertIn(HIDE, self.out)
        self.assertTrue(self.out.endswith(SHOW))
        self.assertLess(self.out.index(HIDE), self.out.index(SHOW))

    def test_first_phase_renders_white_glyphs(self):
        self.assertIn(WHITE, self.out)

    def test_frames_are_redrawn_in_place(self):
        self.assertIn("\x1b[%dA" % len(wordmark.ART), self.out)

    def test_settles_on_the_static_colored_render(self):
        self.assertTrue(self.out.endswith(self.static + SHOW),
                        "final frame is not the static colored render")

    def test_color_phase_delays_are_strictly_faster_than_reveal_delays(self):
        delays = self.spy.calls
        distinct = sorted(set(delays))
        self.assertEqual(len(distinct), 2, "expected one delay per phase")
        color_delay, reveal_delay = distinct[0], distinct[1]
        self.assertLess(color_delay, reveal_delay)
        first_color = delays.index(color_delay)
        self.assertNotIn(reveal_delay, delays[first_color:],
                         "a reveal-phase delay occurs after the color phase began")


class PreviewCliTest(unittest.TestCase):
    def run_preview(self, *args):
        env = dict(os.environ)
        env.pop("NO_COLOR", None)
        return subprocess.run(
            [sys.executable, WORDMARK] + list(args),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=env, universal_newlines=True)

    def test_bare_run_prints_the_plain_banner(self):
        proc = self.run_preview()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout,
                         "".join(line + "\n" for line in readme_banner()))

    def test_animate_flag_degrades_to_one_plain_banner_when_piped(self):
        proc = self.run_preview("--animate")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout,
                         "".join(line + "\n" for line in readme_banner()))

    def test_no_wordmark_verb_is_added_to_the_shipd_binary(self):
        """The preview stays script-level: the binary's curated verb set is
        untouched, so ``shipd wordmark`` remains a usage error."""
        proc = subprocess.run(
            [os.path.join(REPO_ROOT, "plugins", "s", "bin", "shipd"), "wordmark"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True)
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, "")
        self.assertIn("usage: shipd", proc.stderr)


if __name__ == "__main__":
    unittest.main()
