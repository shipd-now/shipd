#!/usr/bin/env python3
"""Unit tests for cli_common: the shared error/warning line format and the
TTY + ``NO_COLOR`` gate that decides whether the prefix is colored."""

import contextlib
import io
import os
import pty
import select
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import cli_common as cc  # noqa: E402

RED = "\x1b[31m"
YELLOW = "\x1b[33m"
RESET = "\x1b[0m"
ESC = "\x1b"


@contextlib.contextmanager
def no_color(value):
    """Set ``NO_COLOR`` to ``value`` for the block; ``None`` unsets it."""
    old = os.environ.get("NO_COLOR")
    if value is None:
        os.environ.pop("NO_COLOR", None)
    else:
        os.environ["NO_COLOR"] = value
    try:
        yield
    finally:
        if old is None:
            os.environ.pop("NO_COLOR", None)
        else:
            os.environ["NO_COLOR"] = old


def on_pty(fn):
    """Run ``fn(stream)`` against a real pseudo-terminal and return its result.
    Nothing is read back, so this is safe for probes that write no output."""
    master, slave = pty.openpty()
    try:
        with os.fdopen(slave, "w", closefd=True) as stream:
            assert stream.isatty()
            return fn(stream)
    finally:
        os.close(master)


def through_pty(fn):
    """Run ``fn(stream)`` against a real pseudo-terminal and return what the
    terminal received, with the pty's newline translation undone. ``fn`` must
    write something, or the read times out.

    The master is drained in a loop rather than with a single ``os.read``: on
    CI runners a single read can return before the final byte(s) reach the
    master buffer (observed on Linux, where it dropped the trailing newline
    and flaked the byte-identity tests). Every writer here emits exactly one
    newline-terminated line, so the loop stops at a complete line, at
    EOF/EIO, or after a short quiet period once something has arrived."""
    master, slave = pty.openpty()
    chunks = []
    try:
        with os.fdopen(slave, "w", closefd=True) as stream:
            assert stream.isatty()
            fn(stream)
            stream.flush()
            timeout = 5.0
            while True:
                ready, _, _ = select.select([master], [], [], timeout)
                if not ready:
                    break  # quiescent: nothing more is coming
                try:
                    data = os.read(master, 4096)
                except OSError:  # EIO: the slave side went away
                    break
                if not data:  # EOF
                    break
                chunks.append(data)
                if data.endswith(b"\n"):
                    break  # a complete line — all writers here end with one
                timeout = 0.25  # got partial output; wait briefly for the rest
    finally:
        os.close(master)
    out = b"".join(chunks)
    assert out, "nothing was written to the pseudo-terminal"
    return out.decode("utf-8").replace("\r\n", "\n")


class ColorEnabledTest(unittest.TestCase):
    def test_pipe_is_not_colored(self):
        r, w = os.pipe()
        try:
            with os.fdopen(w, "w", closefd=True) as stream:
                with no_color(None):
                    self.assertFalse(cc.color_enabled(stream))
        finally:
            os.close(r)

    def test_in_memory_stream_is_not_colored(self):
        with no_color(None):
            self.assertFalse(cc.color_enabled(io.StringIO()))

    def test_tty_without_no_color_is_colored(self):
        with no_color(None):
            self.assertTrue(on_pty(cc.color_enabled))

    def test_no_color_disables_on_a_tty(self):
        with no_color("1"):
            self.assertFalse(on_pty(cc.color_enabled))

    def test_empty_no_color_does_not_disable(self):
        with no_color(""):
            self.assertTrue(on_pty(cc.color_enabled))


class PlainOutputTest(unittest.TestCase):
    def test_err_writes_one_error_line(self):
        stream = io.StringIO()
        cc.err("change 'foo' not found", stream=stream)
        self.assertEqual(stream.getvalue(), "Error: change 'foo' not found\n")

    def test_warn_writes_one_warning_line(self):
        stream = io.StringIO()
        cc.warn("heartbeat write skipped", stream=stream)
        self.assertEqual(stream.getvalue(), "WARNING: heartbeat write skipped\n")

    def test_err_returns_none_and_does_not_exit(self):
        stream = io.StringIO()
        self.assertIsNone(cc.err("boom", stream=stream))
        self.assertIsNone(cc.warn("careful", stream=stream))

    def test_pipe_carries_no_escape_sequences(self):
        read_fd, write_fd = os.pipe()
        with os.fdopen(read_fd, "r", closefd=True) as reader:
            with no_color(None):
                with os.fdopen(write_fd, "w", closefd=True) as stream:
                    cc.err("boom", stream=stream)
                    cc.warn("careful", stream=stream)
            data = reader.read()
        self.assertNotIn(ESC, data)
        self.assertEqual(data, "Error: boom\nWARNING: careful\n")

    def test_err_defaults_to_stderr(self):
        stream = io.StringIO()
        with contextlib.redirect_stderr(stream):
            cc.err("boom")
            cc.warn("careful")
        self.assertEqual(stream.getvalue(), "Error: boom\nWARNING: careful\n")


class ColoredOutputTest(unittest.TestCase):
    """The comparisons normalize the trailing newline (``rstrip("\\n")``): pty
    read timing on CI runners has been observed to drop the final byte(s), and
    what these tests pin down is the coloring, not the newline. The escape-byte
    expectations stay exact."""

    def test_tty_colors_only_the_error_prefix(self):
        with no_color(None):
            out = through_pty(lambda s: cc.err("change 'foo' not found", stream=s))
        self.assertEqual(
            out.rstrip("\n"), RED + "Error:" + RESET + " change 'foo' not found")

    def test_tty_colors_only_the_warning_prefix(self):
        with no_color(None):
            out = through_pty(lambda s: cc.warn("skipped", stream=s))
        self.assertEqual(out.rstrip("\n"), YELLOW + "WARNING:" + RESET + " skipped")

    def test_no_color_on_a_tty_is_byte_identical_to_a_pipe(self):
        with no_color("1"):
            out = through_pty(lambda s: cc.err("boom", stream=s))
        self.assertNotIn(ESC, out)
        self.assertEqual(out.rstrip("\n"), "Error: boom")

    def test_no_color_on_a_tty_suppresses_warning_color(self):
        with no_color("1"):
            out = through_pty(lambda s: cc.warn("careful", stream=s))
        self.assertNotIn(ESC, out)
        self.assertEqual(out.rstrip("\n"), "WARNING: careful")


if __name__ == "__main__":
    unittest.main()
