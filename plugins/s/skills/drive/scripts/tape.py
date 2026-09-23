#!/usr/bin/env python3
"""Pure reader for `vhs` tape annotations (drive-tape-timeline).

A terminal recording's timeline carries `holds` (protected windows) and
`leadingCut` (the application-boot end) only — never `spans` — leaving
every dead-air stretch to the post-processor's spinner backstop
(drive-postprocess) instead of deriving spans from the tape's own `Sleep`
directives, whose durations describe intended pauses rather than the
recording's real timing (a recorded command can easily take longer than its
author guessed).

Annotations ride in tape comments, so a tape stays a valid `vhs` file that
`vhs` itself can run unchanged: a `#hold` comment opens a protected window
at that point in the tape and a `#endhold` comment closes it (an unclosed
`#hold` extends to the end of the recording); a `#ready` comment marks the
boot end that becomes `leadingCut`.

This module is stdlib-only and never shells out — it has no access to the
recording's real duration or to `vhs`'s own keystroke/typing timing, so the
running clock it tracks while walking the tape advances only on the tape's
own `Sleep <duration>` directives, in the order they appear. That is
necessarily an approximation of the recording's real timing (exactly like
the `Sleep` durations themselves), but it is the only timing information a
pure, no-subprocess reader has available; a `#hold`/`#endhold` pair meant to
protect a real stretch of the recording is expected to bracket the `Sleep`
that holds it visible."""

import re

# A hold left open at the end of the tape extends to "the end of the
# recording" (drive-tape-timeline), but this module never sees the real
# recorded duration. A sentinel far past any real recording stands in for
# it: `compute_ff_spans` only ever uses a hold to subtract it from spans
# that already fall inside the timeline it is given, so an oversized end is
# harmless downstream.
OPEN_HOLD_END = 1_000_000.0

# vhs `Sleep <duration>` accepts a bare number of seconds or a Go-style
# duration suffix (`ms`, `s`, `m`) — see `plugins/s/skills/drive/references
# /recording.md`'s tape section for the worked example this mirrors.
_SLEEP_RE = re.compile(
    r'^Sleep\s+([0-9]*\.?[0-9]+)\s*(ms|s|m)?\s*$', re.IGNORECASE)


def _sleep_seconds(match):
    value = float(match.group(1))
    unit = (match.group(2) or "s").lower()
    if unit == "ms":
        return value / 1000.0
    if unit == "m":
        return value * 60.0
    return value


def read_annotations(tape_text):
    """Read `#hold`/`#endhold`/`#ready` comments out of `tape_text` and
    return the `holds`/`leadingCut` timeline they describe:
    ``{"holds": [{"start": ..., "end": ...}, ...], "leadingCut": <offset or
    None>}``. No `spans` key is ever present — spans are never derived from
    a tape (drive-tape-timeline).

    A tape carrying no annotations still yields a valid timeline: empty
    `holds` and a `None` `leadingCut`, so the spinner backstop alone
    carries it. Only the first `#ready` is honored, matching `leadingCut`
    being a single offset rather than a list."""
    holds = []
    leading_cut = None
    open_hold_start = None
    clock = 0.0

    for raw_line in tape_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("#"):
            comment = line[1:].strip().lower()
            if comment == "hold":
                if open_hold_start is None:
                    open_hold_start = clock
            elif comment == "endhold":
                if open_hold_start is not None:
                    holds.append({"start": open_hold_start, "end": clock})
                    open_hold_start = None
            elif comment == "ready":
                if leading_cut is None:
                    leading_cut = clock
            continue

        match = _SLEEP_RE.match(line)
        if match:
            clock += _sleep_seconds(match)

    if open_hold_start is not None:
        holds.append({"start": open_hold_start, "end": OPEN_HOLD_END})

    return {"holds": holds, "leadingCut": leading_cut}
