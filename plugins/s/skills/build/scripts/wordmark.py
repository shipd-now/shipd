#!/usr/bin/env python3
"""wordmark.py — the block-character "shipd now" banner (stdlib only, no
network, no third-party imports).

The art below is byte-identical to the fenced block at the top of the
repository ``README.md`` (trailing spaces included). It is a constant rather
than a runtime read of that file because the module ships inside the plugin
cache snapshot, where no ``README.md`` exists; a test compares the two so the
copies can never drift silently.

``render(stream)`` writes the banner once: plain and escape-free when color is
disabled for the stream (per ``cli_common.color_enabled`` — a non-TTY stream,
or a non-empty ``NO_COLOR``), and otherwise decorated with a horizontal
truecolor gradient interpolated linearly per column from ``#8888a0`` on the
leftmost column to ``#c6ff4e`` on the rightmost.

``animate(stream)`` plays a finite two-phase intro — a white letter-by-letter
reveal, then a strictly faster left-to-right color wipe — redrawn in place and
settling on exactly what ``render`` writes. With color disabled it degrades to
a single plain render with no escapes and no delays.
"""

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cli_common as cc  # noqa: E402

# The banner art — copy of README.md's opening fenced block, trailing spaces
# preserved. Keep in sync with that fence (test_wordmark asserts equality).
ART = (
    "█▀▀▀ █    ▀         █    ▄▄   ▄▄  ▄   ▄",
    "▀▀▀█ █▀▀▄ █ █▀▀▄ ▄▀▀█   █  █ █  █ █ ▄ █",
    "▀▀▀▀ ▀  ▀ ▀ █▄▄▀ ▀▄▄▀ ▀ ▀  ▀  ▀▀   ▀▀▀ ",
    "            █ ",
)

WIDTH = max(len(line) for line in ART)

START_RGB = (136, 136, 160)   # #8888a0, leftmost column
END_RGB = (198, 255, 78)      # #c6ff4e, rightmost column
WHITE_RGB = (255, 255, 255)

RESET = "\x1b[0m"
HIDE_CURSOR = "\x1b[?25l"
SHOW_CURSOR = "\x1b[?25h"
CURSOR_UP = "\x1b[%dA" % len(ART)   # rewind over one frame, to redraw in place


def fg(rgb):
    """Return the truecolor foreground escape for an ``(r, g, b)`` triple."""
    return "\x1b[38;2;%d;%d;%dm" % tuple(rgb)


def column_rgb(x):
    """Return the gradient color of art column ``x``: a linear RGB
    interpolation from ``START_RGB`` at column 0 to ``END_RGB`` at the
    rightmost column."""
    if WIDTH <= 1:
        return END_RGB
    t = float(x) / (WIDTH - 1)
    return tuple(int(round(a + (b - a) * t)) for a, b in zip(START_RGB, END_RGB))


def frame_lines(color_for):
    """Return the art as decorated lines. ``color_for(x)`` gives column ``x``'s
    RGB triple, or ``None`` for a column that is not revealed yet — a hidden
    glyph becomes a blank, so every frame keeps the art's exact width and can
    be overdrawn in place. Each line ends with an attribute reset."""
    lines = []
    for line in ART:
        parts = []
        last = None
        for x, ch in enumerate(line):
            if ch == " ":
                parts.append(ch)
                last = None       # a gap breaks the run: recolor after it
                continue
            rgb = color_for(x)
            if rgb is None:
                parts.append(" ")
                last = None
                continue
            escape = fg(rgb)
            if escape != last:
                parts.append(escape)
                last = escape
            parts.append(ch)
        parts.append(RESET)
        lines.append("".join(parts))
    return lines


def plain_lines():
    """Return the art lines verbatim, with no escape sequences."""
    return list(ART)


def _write_lines(stream, lines):
    stream.write("".join(line + "\n" for line in lines))
    flush = getattr(stream, "flush", None)
    if flush is not None:
        flush()


def render(stream):
    """Write the banner to ``stream`` once — plain when color is disabled for
    it, gradient-colored otherwise."""
    if cc.color_enabled(stream):
        _write_lines(stream, frame_lines(column_rgb))
    else:
        _write_lines(stream, plain_lines())


def letter_groups():
    """Return the art's letters as ``(start, end)`` column ranges: maximal
    runs of columns carrying a glyph on at least one line, split at the blank
    columns between them. One reveal step per group is what makes the
    animation advance letter by letter rather than column by column."""
    filled = [any(x < len(line) and line[x] != " " for line in ART)
              for x in range(WIDTH)]
    groups = []
    start = None
    for x, on in enumerate(filled):
        if on and start is None:
            start = x
        elif not on and start is not None:
            groups.append((start, x))
            start = None
    if start is not None:
        groups.append((start, WIDTH))
    return groups


def _revealed(limit):
    """``color_for`` for the reveal phase: columns left of ``limit`` are white,
    the rest are still hidden."""
    return lambda x: WHITE_RGB if x < limit else None


def _wiped(limit):
    """``color_for`` for the color phase: columns left of ``limit`` carry their
    gradient color, the rest are still white."""
    return lambda x: column_rgb(x) if x < limit else WHITE_RGB


def animate(stream, *, reveal_delay=0.035, color_delay=0.012, sleep=time.sleep):
    """Play the finite two-phase intro on ``stream``, settling on the static
    render. ``sleep`` and both delays are injectable so tests can run the whole
    animation deterministically without waiting on the clock.

    With color disabled for ``stream`` this is exactly one plain ``render``:
    no escapes, no frames, no sleeps."""
    if not cc.color_enabled(stream):
        _write_lines(stream, plain_lines())
        return
    groups = letter_groups()
    frames = [(_revealed(end), reveal_delay) for _, end in groups]
    frames += [(_wiped(end), color_delay) for _, end in groups]
    stream.write(HIDE_CURSOR)
    try:
        for index, (color_for, delay) in enumerate(frames):
            if index:
                stream.write(CURSOR_UP)
            _write_lines(stream, frame_lines(color_for))
            if index < len(frames) - 1:
                sleep(delay)     # the settled last frame is not a transition
    finally:
        # Restore the cursor even if the animation is interrupted mid-frame.
        stream.write(SHOW_CURSOR)
        flush = getattr(stream, "flush", None)
        if flush is not None:
            flush()


def main(argv=None):
    """Developer preview of the banner. This is script-level only — the
    ``shipd`` binary's curated verb set is deliberately untouched."""
    parser = argparse.ArgumentParser(
        description="Preview the shipd wordmark banner.")
    parser.add_argument("--animate", action="store_true",
                        help="play the animated intro instead of the static "
                             "render (a piped stdout degrades to plain art)")
    args = parser.parse_args(argv)
    if args.animate:
        animate(sys.stdout)
    else:
        render(sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
