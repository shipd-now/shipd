#!/usr/bin/env python3
"""install_tui.py — the interactive ``shipd install`` finish (stdlib only, no
network, no third-party imports).

The curl installer ends by asking the one onboarding question the rest of the
engine cannot infer: *which coding harnesses do you work in?* This module is
that question — an animated wordmark, a multi-select over
:mod:`harness_registry`, a selection persisted at ``~/.shipd/harnesses.json``,
and the user-global generation for every selected harness that declares a
``user_dir``.

Three layers, deliberately separated so all but the last is testable without a
terminal:

  * :class:`Selection` plus :func:`apply_key` and :func:`decode_keys` — the
    whole behaviour of the multi-select as a pure reducer over key names;
  * :func:`load_record` / :func:`save_record` and
    :func:`install_selection` — the file surfaces, which touch only paths the
    registry and this module's own constant name;
  * :func:`multiselect` and :func:`run` — the raw-mode loop on ``/dev/tty``,
    its numbered line-prompt fallback for a terminal that will not go raw, and
    the headless degradation that prints a note and writes nothing.

Every terminal exit path — confirm, abort, interrupt, exception — restores the
saved terminal attributes and the cursor in a ``finally``.
"""

import argparse
import io
import json
import os
import sys
import tempfile
import termios
import tty as tty_mod

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cli_common as cc  # noqa: E402
import harness_generate as hg  # noqa: E402
import harness_registry as hr  # noqa: E402
import wordmark  # noqa: E402

# The selection record: the shipd data home (alongside ``builds/`` and
# ``designs/``), and the schema version its readers check.
RECORD_DIR = "~/.shipd"
RECORD_NAME = "harnesses.json"
RECORD_VERSION = 1

# The key names the reducer understands. A raw byte sequence becomes one of
# these (or nothing, for a key this flow has no meaning for) in
# :func:`decode_keys`, so the reducer never sees an escape sequence.
UP = "up"
DOWN = "down"
TOGGLE = "toggle"
ALL = "all"
CONFIRM = "confirm"
ABORT = "abort"

# The two verdicts a finished selection carries.
CONFIRMED = "confirmed"
ABORTED = "aborted"

# Single bytes to key names. ``\x03`` is the interrupt: raw mode delivers it
# as a byte rather than a signal, and the flow treats it exactly as ``q``.
_KEYS = {
    b" ": TOGGLE,
    b"a": ALL,
    b"A": ALL,
    b"\r": CONFIRM,
    b"\n": CONFIRM,
    b"q": ABORT,
    b"Q": ABORT,
    b"\x03": ABORT,
}

# The final byte of a ``\x1b[`` sequence, for the two arrows that move.
_ARROWS = {b"A": UP, b"B": DOWN}

ESC = b"\x1b"

# Presentation. The accent is the wordmark's own end-of-gradient color, so the
# picker reads as the same surface the banner just drew.
ACCENT = wordmark.fg(wordmark.END_RGB)
DIM = "\x1b[2m"
REVERSE = "\x1b[7m"
RESET = wordmark.RESET
CLEAR_LINE = "\x1b[2K"

PROMPT = "Which coding harnesses do you work in?"
HINT = "↑/↓ move · space toggle · a all · enter confirm · q quit"
LINE_HINT = ("toggle by number, `a` for all, empty line to confirm, "
             "`q` to quit")
REPO_ONLY = "repo only"

# What a selected harness with no user-global surface is told instead of being
# generated: its commands are a per-repository act.
REPO_ONLY_HINT = "repo-level only — run `shipd harness add %s` in a repo"

# The headless degradation. Printed with the plain wordmark when no usable
# controlling terminal is available; nothing is written on that path.
NON_INTERACTIVE_NOTE = (
    "\n"
    "No terminal to ask on, so no harnesses were picked.\n"
    "Run `shipd install` from a terminal to choose the coding harnesses you\n"
    "work in — or `shipd harness add <id>` to install one repository's\n"
    "commands right now.\n")


# ---------------------------------------------------------------------------
# The pure selection reducer
# ---------------------------------------------------------------------------


def decode_keys(data):
    """Every key name ``data`` carries, in order.

    A terminal delivers a burst of keystrokes as one read — and a pasted or
    scripted sequence arrives whole — so this decodes a chunk rather than a
    keystroke. Unrecognized bytes and escape sequences are dropped: an
    unmapped key is a no-op, never an abort.
    """
    keys = []
    index = 0
    while index < len(data):
        byte = data[index:index + 1]
        if byte == ESC and data[index + 1:index + 2] == b"[":
            key = _ARROWS.get(data[index + 2:index + 3])
            if key is not None:
                keys.append(key)
            index += 3
            continue
        key = _KEYS.get(byte)
        if key is not None:
            keys.append(key)
        index += 1
    return keys


class Selection:
    """The multi-select's whole state: the harness ids on offer, the ones
    chosen, where the cursor sits, and the verdict once the user reaches one.

    Ids the registry does not declare are dropped at construction, which is
    what makes a stale selection record safe to preload.
    """

    def __init__(self, ids, chosen=()):
        self.ids = tuple(ids)
        known = set(self.ids)
        self.chosen = set(harness_id for harness_id in chosen
                          if harness_id in known)
        self.cursor = 0
        self.done = None

    @property
    def current(self):
        """The harness id under the cursor."""
        return self.ids[self.cursor]

    def move(self, delta):
        """Move the cursor by ``delta``, clamped at both ends — the list does
        not wrap, so holding an arrow never spins past the edge."""
        self.cursor = max(0, min(len(self.ids) - 1, self.cursor + delta))

    def toggle_at(self, index):
        """Toggle the harness at ``index``; out-of-range indexes do nothing."""
        if not 0 <= index < len(self.ids):
            return False
        harness_id = self.ids[index]
        if harness_id in self.chosen:
            self.chosen.discard(harness_id)
        else:
            self.chosen.add(harness_id)
        return True

    def select_all(self):
        """Choose every harness on offer."""
        self.chosen = set(self.ids)

    def result(self):
        """The confirmed ids in registry order, or ``None`` until the
        selection is confirmed — an aborted or unfinished one has no
        result, which is what keeps an abort from writing anything."""
        if self.done != CONFIRMED:
            return None
        return tuple(harness_id for harness_id in self.ids
                     if harness_id in self.chosen)


def apply_key(selection, key):
    """Apply one key name to ``selection`` and return it. Keys arriving after
    a verdict are ignored, so a trailing keystroke in the same chunk as the
    confirm cannot change what was confirmed."""
    if selection.done is not None:
        return selection
    if key == UP:
        selection.move(-1)
    elif key == DOWN:
        selection.move(1)
    elif key == TOGGLE:
        selection.toggle_at(selection.cursor)
    elif key == ALL:
        selection.select_all()
    elif key == CONFIRM:
        selection.done = CONFIRMED
    elif key == ABORT:
        selection.done = ABORTED
    return selection


# ---------------------------------------------------------------------------
# The selection record
# ---------------------------------------------------------------------------


def record_path():
    """``~/.shipd/harnesses.json``, with ``~`` expanded now rather than at
    import time — the tests, and a vendored install, both move ``HOME``."""
    return os.path.join(os.path.expanduser(RECORD_DIR), RECORD_NAME)


def load_record(path=None):
    """The recorded harness ids the registry still declares, in registry
    order. An absent, unreadable, or malformed record reads as an empty
    selection: this file is a convenience, never a prerequisite."""
    try:
        with open(path or record_path(), encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, ValueError):
        return ()
    if not isinstance(payload, dict):
        return ()
    recorded = payload.get("harnesses")
    if not isinstance(recorded, list):
        return ()
    chosen = set(entry for entry in recorded if isinstance(entry, str))
    return tuple(harness_id for harness_id in hr.ids() if harness_id in chosen)


def save_record(ids, path=None):
    """Write the confirmed selection atomically — temp file in the same
    directory, then a rename — so an interrupted write can never leave a
    half-parsed record behind. Ids are normalized to registry order."""
    target = path or record_path()
    chosen = set(ids)
    payload = {
        "version": RECORD_VERSION,
        "harnesses": [harness_id for harness_id in hr.ids()
                      if harness_id in chosen],
    }
    directory = os.path.dirname(os.path.abspath(target))
    os.makedirs(directory, exist_ok=True)
    handle, temp = tempfile.mkstemp(dir=directory, prefix=".shipd-harnesses-")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
            fh.write("\n")
        os.chmod(temp, 0o644)
        os.replace(temp, target)
    except OSError:
        if os.path.exists(temp):
            os.unlink(temp)
        raise


# ---------------------------------------------------------------------------
# The generation hand-off
# ---------------------------------------------------------------------------


def install_selection(ids, out):
    """Generate the user-global command files for every selected harness that
    has a user surface, and report each selected harness on ``out``.

    Returns ``None`` on success, or a single reason string when the
    generation refuses — a file in the way that this install does not own is
    the only such case, and then nothing at all was written.
    """
    entries = [hr.get(harness_id) for harness_id in ids]
    entries = [entry for entry in entries if entry is not None]
    generated = [entry for entry in entries
                 if hg.has_surface(entry, hg.USER_MODE)]
    if generated:
        try:
            _lines, reason = hg.add(generated, hg.USER_MODE)
        except (OSError, ValueError) as exc:
            return "cannot install the harness commands: %s" % exc
        if reason is not None:
            return reason
    width = max((len(entry["id"]) for entry in entries), default=0)
    for entry in entries:
        if entry in generated:
            paths = hg.command_paths(entry, hg.USER_MODE)
            where = hg.display(os.path.dirname(paths[0]), hg.USER_MODE)
            detail = "%d command%s in %s" % (
                len(paths), "" if len(paths) == 1 else "s", where)
            out.write("  installed  %-*s  %s\n" % (width, entry["id"], detail))
        else:
            out.write("  skipped    %-*s  %s\n"
                      % (width, entry["id"], REPO_ONLY_HINT % entry["id"]))
    return None


# ---------------------------------------------------------------------------
# The interactive surfaces
# ---------------------------------------------------------------------------


def wrap_tty(fd, closefd=True):
    """A text handle that reads *and* writes terminal descriptor ``fd``.

    Built by hand rather than with :func:`open`: a terminal is not seekable,
    and the buffered reader-writer :func:`open` would build for ``"r+"``
    refuses an unseekable stream outright.
    """
    return io.TextIOWrapper(io.FileIO(fd, "r+", closefd=closefd),
                            errors="replace", line_buffering=True)


def open_tty():
    """A read-write handle on the controlling terminal, or ``None`` when
    there is none — the single fact that decides whether this flow can ask
    anything at all. Input is bound to the terminal, never to this process's
    stdin, which a ``curl … | sh`` pipeline owns."""
    try:
        fd = os.open("/dev/tty", os.O_RDWR | os.O_NOCTTY)
    except OSError:
        return None
    return wrap_tty(fd)


def _label(entry):
    """One registry entry's display name, with the repo-only harnesses marked
    — a user picking one deserves to know before confirming that it has no
    home-directory surface."""
    if hg.has_surface(entry, hg.USER_MODE):
        return entry["name"]
    return "%s (%s)" % (entry["name"], REPO_ONLY)


def _frame(selection):
    """The picker's lines for the current state, cursor row highlighted.
    Constant height, so the next frame overdraws this one exactly."""
    entries = [hr.get(harness_id) for harness_id in selection.ids]
    width = max(len(harness_id) for harness_id in selection.ids)
    rows = [" [%s] %-*s  %s"
            % ("x" if entry["id"] in selection.chosen else " ",
               width, entry["id"], _label(entry))
            for entry in entries]
    # A uniform row width keeps the cursor's highlight a full bar rather than
    # a ragged one that ends with the harness's name.
    span = max(len(row) for row in rows) + 1
    lines = ["%s%s%s" % (ACCENT, PROMPT, RESET), ""]
    for index, row in enumerate(rows):
        row = "%-*s" % (span, row)
        if index == selection.cursor:
            row = "%s%s%s" % (REVERSE, row, RESET)
        lines.append(row)
    lines.append("")
    lines.append("%s%s%s" % (DIM, HINT, RESET))
    return lines


def _draw(handle, lines, redraw):
    """Write one frame, rewinding over the previous one when there is one.
    Raw mode leaves the carriage where it was, so every line ends ``\\r\\n``
    and starts by clearing what it overdraws."""
    if redraw:
        handle.write("\x1b[%dA" % len(lines))
    handle.write("".join(CLEAR_LINE + line + "\r\n" for line in lines))
    handle.flush()


def _read_keys(fd):
    """The key names of the next burst of input on ``fd``; an empty list on
    end of input, which the caller treats as an abort."""
    try:
        data = os.read(fd, 64)
    except (OSError, KeyboardInterrupt):
        return None
    if not data:
        return None
    return decode_keys(data)


def raw_multiselect(handle, fd, saved, selection):
    """The raw-mode picker on ``handle``, whose descriptor ``fd`` is already
    known to carry ``saved`` terminal attributes. Restores those attributes
    and the cursor on every exit path, including an exception."""
    pending = []
    redraw = False
    handle.write(wordmark.HIDE_CURSOR)
    try:
        # TCSADRAIN, never TCSAFLUSH: flushing would discard input the user
        # (or a driving test) has already typed ahead.
        tty_mod.setraw(fd, termios.TCSADRAIN)
    except termios.error:
        handle.write(wordmark.SHOW_CURSOR)
        return line_prompt(handle, selection)
    try:
        while selection.done is None:
            _draw(handle, _frame(selection), redraw)
            redraw = True
            if not pending:
                keys = _read_keys(fd)
                if keys is None:
                    selection.done = ABORTED
                    break
                pending = keys
                continue
            apply_key(selection, pending.pop(0))
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, saved)
        handle.write(wordmark.SHOW_CURSOR)
        handle.flush()
    return selection


def line_prompt(handle, selection):
    """The fallback for a terminal that will not go into raw mode: the same
    reducer, driven a whole line at a time on the same handle."""
    handle.write("%s\n" % PROMPT)
    _list(handle, selection)
    while selection.done is None:
        handle.write("%s: " % LINE_HINT)
        handle.flush()
        line = handle.readline()
        if not line:
            selection.done = ABORTED
            break
        text = line.strip().lower()
        if text == "":
            selection.done = CONFIRMED
        elif text in ("q", "quit"):
            selection.done = ABORTED
        elif text == "a":
            selection.select_all()
            _list(handle, selection)
        elif text.isdigit() and selection.toggle_at(int(text) - 1):
            _list(handle, selection)
        else:
            handle.write("no harness numbered %s\n" % line.strip())
    handle.flush()
    return selection


def _list(handle, selection):
    """The numbered harness list the line prompt redraws after every change."""
    width = max(len(harness_id) for harness_id in selection.ids)
    for index, harness_id in enumerate(selection.ids):
        entry = hr.get(harness_id)
        handle.write("  %2d) [%s] %-*s  %s\n"
                     % (index + 1, "x" if harness_id in selection.chosen
                        else " ", width, harness_id, _label(entry)))
    handle.flush()


def multiselect(handle, selection):
    """Run the picker on ``handle``, in raw mode where the terminal allows it
    and as a numbered line prompt where it does not.

    Only the *entry* into raw mode is guarded: a handle with no usable
    descriptor, or a terminal that refuses ``tcgetattr``, falls back to the
    line prompt — anything failing inside the loop propagates, having already
    restored the terminal.
    """
    try:
        fd = handle.fileno()
        saved = termios.tcgetattr(fd)
    except (termios.error, AttributeError, ValueError, OSError):
        return line_prompt(handle, selection)
    return raw_multiselect(handle, fd, saved, selection)


# ---------------------------------------------------------------------------
# The verb
# ---------------------------------------------------------------------------


def _non_interactive(out):
    """The headless degradation: the plain wordmark, one note, nothing
    written."""
    out.write("".join("%s\n" % line for line in wordmark.plain_lines()))
    out.write(NON_INTERACTIVE_NOTE)
    flush = getattr(out, "flush", None)
    if flush is not None:
        flush()


def run(tty=None, out=None):
    """The ``shipd install`` flow. Returns the verb's exit code.

    ``tty`` is the controlling-terminal handle, opened here when the caller
    passes none; ``out`` receives the headless output only. Every path that
    cannot ask — no ``/dev/tty``, or color disabled for it — prints the plain
    banner and the note, writes nothing, and exits 0.
    """
    out = sys.stdout if out is None else out
    opened = None
    if tty is None:
        tty = opened = open_tty()
    try:
        if tty is None or not cc.color_enabled(tty):
            _non_interactive(out)
            return 0
        wordmark.animate(tty)
        tty.write("\n")
        selection = multiselect(tty, Selection(hr.ids(), load_record()))
        if selection.done != CONFIRMED:
            tty.write("\nAborted — nothing was written.\n")
            tty.flush()
            return 0
        chosen = selection.result()
        save_record(chosen)
        if not chosen:
            tty.write("\nNo harnesses selected. Re-run `shipd install` any "
                      "time to pick some.\n")
            tty.flush()
            return 0
        tty.write("\n")
        reason = install_selection(chosen, tty)
        tty.flush()
        if reason is not None:
            cc.err(reason, stream=tty)
            return 1
        return 0
    finally:
        if opened is not None:
            opened.close()


def main(argv=None):
    """The ``shipd install`` entry point. The verb takes no arguments: the
    one question it asks is the interactive one."""
    parser = argparse.ArgumentParser(
        prog="shipd install",
        description="Pick the coding harnesses you work in and install their "
                    "shipd commands into your home directory. Run it from a "
                    "terminal; `shipd harness add <id>` covers one repo.")
    parser.parse_args(argv)
    return run()


if __name__ == "__main__":
    sys.exit(main())
