#!/usr/bin/env python3
"""cli_common.py — the shared human-facing output convention for the shipd
CLIs (stdlib only, no network, no third-party imports).

This module is the single authority on how the engine scripts under
``plugins/s/skills/build/scripts/`` and the ``shipd`` binary render a fatal
error or a fail-soft warning:

  * a fatal error is one ``Error: <reason>`` line on stderr, and the caller
    exits nonzero (usage errors exit ``2``);
  * a warning is one ``WARNING: <message>`` line on stderr.

Color is a presentation detail layered on top of that, never a change to it:
the ``Error:`` prefix is red and the ``WARNING:`` prefix yellow **only** when
the target stream is a terminal and ``NO_COLOR`` is unset or empty (the
no-color.org convention). Piped and redirected output is therefore
byte-identical to the plain text above, which is what keeps every scenario
that pins exact stderr text unaffected.

Neither helper exits — callers keep owning their exit codes.
"""

import os
import sys

RED = "\x1b[31m"
YELLOW = "\x1b[33m"
RESET = "\x1b[0m"


def color_enabled(stream):
    """Return True when ``stream`` is a terminal and ``NO_COLOR`` is unset or
    empty. Any non-empty ``NO_COLOR`` value disables color, per
    https://no-color.org. Streams without a usable ``isatty`` (a StringIO in a
    test, a closed handle) count as not a terminal."""
    if os.environ.get("NO_COLOR"):
        return False
    try:
        return bool(stream.isatty())
    except (AttributeError, ValueError):
        return False


def _line(stream, prefix, color, text):
    """Write ``<prefix> <text>`` to ``stream``, coloring only the prefix when
    the stream qualifies."""
    if color_enabled(stream):
        prefix = color + prefix + RESET
    stream.write("%s %s\n" % (prefix, text))


def err(reason, *, stream=None):
    """Write a single ``Error: <reason>`` line to ``stream`` (stderr by
    default). Does not exit — the caller owns the exit code."""
    _line(stream if stream is not None else sys.stderr, "Error:", RED, reason)


def warn(message, *, stream=None):
    """Write a single ``WARNING: <message>`` line to ``stream`` (stderr by
    default). Does not exit."""
    _line(
        stream if stream is not None else sys.stderr,
        "WARNING:", YELLOW, message)
