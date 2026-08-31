#!/usr/bin/env python3
"""Tests for ``install_tui.py`` — the interactive ``shipd install`` finish.

Three layers, mirroring how the module is built. The *pure* tests drive the
selection reducer and the key decoder as data, with no terminal anywhere. The
*surface* tests exercise the record at ``~/.shipd/harnesses.json`` and the
per-harness generation hand-off inside an isolated ``HOME``, so every write a
test provokes lands in a directory it owns. The *pty* tests run the real raw
mode loop end to end against a pseudo-terminal — keys in, files and a report
out — because the terminal handling is exactly the part a reducer test cannot
vouch for.

Nothing here touches the real home directory, the network, or the shipped
harness tree (rendering only reads it).
"""

import io
import json
import os
import pty
import shutil
import sys
import tempfile
import termios
import threading
import tty as tty_mod
import unittest
import unittest.mock

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import harness_bodies as hb  # noqa: E402
import harness_generate as hg  # noqa: E402
import harness_registry as hr  # noqa: E402
import install_tui as it  # noqa: E402
import wordmark  # noqa: E402

# The keys the raw loop reads, as a terminal actually delivers them.
UP = b"\x1b[A"
DOWN = b"\x1b[B"
TOGGLE = b" "
CONFIRM = b"\r"
ABORT = b"q"
INTERRUPT = b"\x03"
ESCAPE = b"\x1b"

# The registry position of the harness the spec's interactive scenario names.
CODEX_INDEX = hr.ids().index("codex")


def home_tree(base):
    """Every file under ``base``, relative — the assertion that a path was or
    was not written, without caring where the temp home happens to live."""
    found = []
    for current, _dirs, names in os.walk(base):
        for name in names:
            found.append(os.path.relpath(os.path.join(current, name), base))
    return sorted(found)


class FakeTty(io.StringIO):
    """A writable stand-in for the ``/dev/tty`` handle that claims to be a
    terminal and reads its lines from a queue — enough for the line-prompt
    fallback, which never touches ``termios`` or a file descriptor."""

    def __init__(self, lines=()):
        io.StringIO.__init__(self)
        self.lines = list(lines)

    def isatty(self):
        return True

    def readline(self, *_args):
        if not self.lines:
            return ""          # EOF: the caller must treat it as an abort
        return self.lines.pop(0)


# ---------------------------------------------------------------------------
# The pure pieces: the key decoder and the selection reducer
# ---------------------------------------------------------------------------


class DecodeKeysTest(unittest.TestCase):
    """A terminal delivers a burst of keystrokes as one read, so decoding has
    to yield every key in a chunk, not just the first."""

    def test_a_chunk_decodes_to_every_key_it_carries(self):
        self.assertEqual(
            it.decode_keys(TOGGLE + DOWN + TOGGLE + CONFIRM),
            [it.TOGGLE, it.DOWN, it.TOGGLE, it.CONFIRM])

    def test_arrow_sequences_decode_to_moves(self):
        self.assertEqual(it.decode_keys(UP + DOWN), [it.UP, it.DOWN])

    def test_every_abort_key_decodes_to_abort(self):
        self.assertEqual(it.decode_keys(ABORT), [it.ABORT])
        self.assertEqual(it.decode_keys(INTERRUPT), [it.ABORT])
        self.assertEqual(it.decode_keys(ESCAPE), [it.ABORT])

    def test_escape_sequences_keep_their_meaning(self):
        self.assertEqual(it.decode_keys(b"\x1b[A"), [it.UP])
        self.assertEqual(it.decode_keys(b"\x1b[B"), [it.DOWN])
        self.assertEqual(it.decode_keys(b"\x1b[C"), [])

    def test_a_selects_all(self):
        self.assertEqual(it.decode_keys(b"a"), [it.ALL])

    def test_newline_confirms_too(self):
        self.assertEqual(it.decode_keys(b"\n"), [it.CONFIRM])

    def test_unknown_keys_are_ignored(self):
        self.assertEqual(it.decode_keys(b"zx\x1b[C"), [])
        self.assertEqual(it.decode_keys(b"z" + TOGGLE), [it.TOGGLE])


class SelectionReducerTest(unittest.TestCase):
    """The reducer is the whole of the multi-select's behaviour; the loop
    around it only draws and reads."""

    def selection(self, chosen=()):
        return it.Selection(hr.ids(), chosen)

    def press(self, selection, *keys):
        for key in keys:
            it.apply_key(selection, key)
        return selection

    def test_a_fresh_selection_starts_at_the_top_with_the_record(self):
        selection = self.selection(("codex",))
        self.assertEqual(selection.cursor, 0)
        self.assertEqual(selection.chosen, {"codex"})
        self.assertIsNone(selection.done)

    def test_down_moves_the_cursor_and_stops_at_the_end(self):
        selection = self.selection()
        self.press(selection, *([it.DOWN] * (len(hr.ids()) + 3)))
        self.assertEqual(selection.cursor, len(hr.ids()) - 1)

    def test_up_stops_at_the_top(self):
        selection = self.selection()
        self.press(selection, it.DOWN, it.DOWN, it.UP, it.UP, it.UP)
        self.assertEqual(selection.cursor, 0)

    def test_space_toggles_the_harness_under_the_cursor(self):
        selection = self.selection()
        self.press(selection, it.DOWN, it.TOGGLE)
        self.assertEqual(selection.chosen, {hr.ids()[1]})
        self.press(selection, it.TOGGLE)
        self.assertEqual(selection.chosen, set())

    def test_a_selects_every_harness(self):
        selection = self.selection()
        self.press(selection, it.ALL)
        self.assertEqual(selection.chosen, set(hr.ids()))

    def test_confirm_yields_the_selection_in_registry_order(self):
        selection = self.selection()
        self.press(selection, *([it.DOWN] * CODEX_INDEX))
        self.press(selection, it.TOGGLE)
        self.press(selection, it.UP, it.TOGGLE, it.CONFIRM)
        self.assertEqual(selection.done, it.CONFIRMED)
        expected = tuple(i for i in hr.ids()
                         if i in ("codex", hr.ids()[CODEX_INDEX - 1]))
        self.assertEqual(selection.result(), expected)

    def test_abort_yields_nothing(self):
        selection = self.selection()
        self.press(selection, it.TOGGLE, it.ABORT)
        self.assertEqual(selection.done, it.ABORTED)
        self.assertIsNone(selection.result())

    def test_keys_after_a_verdict_are_ignored(self):
        selection = self.selection()
        self.press(selection, it.CONFIRM, it.TOGGLE, it.ABORT)
        self.assertEqual(selection.done, it.CONFIRMED)
        self.assertEqual(selection.result(), ())

    def test_an_unknown_recorded_id_never_reaches_the_selection(self):
        selection = it.Selection(hr.ids(), ("codex", "no-such-harness"))
        self.assertEqual(selection.chosen, {"codex"})


# ---------------------------------------------------------------------------
# The selection record
# ---------------------------------------------------------------------------


class HomeTestCase(unittest.TestCase):
    """An isolated ``HOME`` for everything that reads or writes the user's own
    directories — the record, and the generated user-global command files."""

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="shipd-install-tui-home-")
        patcher = unittest.mock.patch.dict(os.environ, {"HOME": self.home})
        patcher.start()
        os.environ.pop("NO_COLOR", None)
        self.addCleanup(patcher.stop)

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)

    def record(self):
        with open(it.record_path(), encoding="utf-8") as handle:
            return json.load(handle)

    def write_record(self, payload):
        os.makedirs(os.path.dirname(it.record_path()), exist_ok=True)
        with open(it.record_path(), "w", encoding="utf-8") as handle:
            json.dump(payload, handle)

    def codex_files(self):
        return [hg.user_path(hr.get("codex"), command)
                for command in hb.commands()]


class RecordTest(HomeTestCase):
    def test_the_record_lives_under_the_shipd_data_home(self):
        self.assertEqual(
            it.record_path(),
            os.path.join(self.home, ".shipd", "harnesses.json"))

    def test_a_confirmed_selection_round_trips(self):
        it.save_record(("codex", "cursor"))
        payload = self.record()
        self.assertEqual(payload["version"], it.RECORD_VERSION)
        self.assertEqual(payload["harnesses"], ["cursor", "codex"])
        self.assertEqual(it.load_record(), ("cursor", "codex"))

    def test_an_absent_record_loads_as_nothing_selected(self):
        self.assertEqual(it.load_record(), ())

    def test_unknown_ids_are_dropped_on_load(self):
        self.write_record({"version": 1,
                           "harnesses": ["codex", "no-such-harness"]})
        self.assertEqual(it.load_record(), ("codex",))

    def test_a_malformed_record_loads_as_nothing_selected(self):
        os.makedirs(os.path.dirname(it.record_path()), exist_ok=True)
        with open(it.record_path(), "w", encoding="utf-8") as handle:
            handle.write("{not json")
        self.assertEqual(it.load_record(), ())

    def test_the_write_is_atomic_and_leaves_no_temp_file(self):
        it.save_record(("codex",))
        it.save_record(("cursor",))
        directory = os.path.dirname(it.record_path())
        self.assertEqual(os.listdir(directory), ["harnesses.json"])
        self.assertEqual(self.record()["harnesses"], ["cursor"])


# ---------------------------------------------------------------------------
# The generation hand-off
# ---------------------------------------------------------------------------


class InstallSelectionTest(HomeTestCase):
    def test_a_user_surface_harness_is_generated_and_reported(self):
        out = io.StringIO()
        self.assertIsNone(it.install_selection(("codex",), out))
        for path in self.codex_files():
            self.assertTrue(os.path.exists(path), path)
        self.assertIn("codex", out.getvalue())
        self.assertIn("installed", out.getvalue())

    def test_a_repo_only_harness_is_pointed_at_the_harness_verb(self):
        out = io.StringIO()
        self.assertIsNone(it.install_selection(("github-copilot",), out))
        self.assertIn("github-copilot", out.getvalue())
        self.assertIn("shipd harness add", out.getvalue())
        self.assertEqual(home_tree(self.home), [],
                         "a repo-only harness must write nothing in $HOME")

    def test_a_mixed_selection_generates_only_the_user_surfaces(self):
        out = io.StringIO()
        self.assertIsNone(
            it.install_selection(("codex", "github-copilot"), out))
        written = home_tree(self.home)
        self.assertTrue(written)
        for path in written:
            self.assertNotIn(".github", path)
        self.assertIn("shipd harness add", out.getvalue())


# ---------------------------------------------------------------------------
# Degradation: no usable terminal, and no raw mode
# ---------------------------------------------------------------------------


class NoTerminalTest(HomeTestCase):
    def assertPlainBanner(self, text):
        for line in wordmark.ART:
            self.assertIn(line, text)
        self.assertNotIn("\x1b[", text)

    def test_an_unopenable_tty_prints_the_banner_and_the_note(self):
        out = io.StringIO()
        with unittest.mock.patch.object(it, "open_tty", lambda: None):
            code = it.run(out=out)
        self.assertEqual(code, 0)
        self.assertPlainBanner(out.getvalue())
        self.assertIn("shipd install", out.getvalue())
        self.assertEqual(home_tree(self.home), [],
                         "the non-interactive path must write nothing")

    def test_a_tty_without_color_is_not_interactive_either(self):
        # NO_COLOR set, or a handle that is not a terminal: `color_enabled`
        # is the single gate, exactly as the plan fixes it.
        out = io.StringIO()
        opened = FakeTty()
        with unittest.mock.patch.object(it, "open_tty", lambda: opened), \
                unittest.mock.patch.dict(os.environ, {"NO_COLOR": "1"}):
            code = it.run(out=out)
        self.assertEqual(code, 0)
        self.assertPlainBanner(out.getvalue())
        self.assertEqual(home_tree(self.home), [])


class LinePromptTest(HomeTestCase):
    """The fallback for a terminal that will not go into raw mode: the same
    reducer, driven by whole lines."""

    def test_a_number_toggles_and_an_empty_line_confirms(self):
        handle = FakeTty(["%d\n" % (CODEX_INDEX + 1), "\n"])
        selection = it.line_prompt(handle, it.Selection(hr.ids()))
        self.assertEqual(selection.done, it.CONFIRMED)
        self.assertEqual(selection.result(), ("codex",))

    def test_q_aborts(self):
        handle = FakeTty(["q\n"])
        selection = it.line_prompt(handle, it.Selection(hr.ids()))
        self.assertEqual(selection.done, it.ABORTED)

    def test_eof_aborts(self):
        selection = it.line_prompt(FakeTty(), it.Selection(hr.ids()))
        self.assertEqual(selection.done, it.ABORTED)

    def test_an_out_of_range_number_is_refused_not_applied(self):
        handle = FakeTty(["99\n", "\n"])
        selection = it.line_prompt(handle, it.Selection(hr.ids()))
        self.assertEqual(selection.done, it.CONFIRMED)
        self.assertEqual(selection.result(), ())

    def test_multiselect_falls_back_when_raw_mode_is_unavailable(self):
        handle = FakeTty(["\n"])
        handle.fileno = lambda: -1
        with unittest.mock.patch.object(
                it.termios, "tcgetattr",
                unittest.mock.Mock(side_effect=termios.error("nope"))):
            selection = it.multiselect(handle, it.Selection(hr.ids()))
        self.assertEqual(selection.done, it.CONFIRMED)
        self.assertIn("number", handle.getvalue())


# ---------------------------------------------------------------------------
# The real loop, on a pseudo-terminal
# ---------------------------------------------------------------------------


class PtyTest(HomeTestCase):
    """The end-to-end smoke test: real ``/dev/tty``-shaped handle, real raw
    mode, real keystrokes, real generated files."""

    def drive(self, keys):
        """Run the flow against a pty preloaded with ``keys``. Returns
        ``(exit code, everything the flow wrote, attributes before, after)``.

        The slave is put in raw mode *before* the keys are written so they
        reach the flow byte for byte, and a reader thread drains the master
        throughout so the wordmark animation can never fill the buffer and
        deadlock the run.
        """
        master, slave = pty.openpty()
        tty_mod.setraw(slave, termios.TCSANOW)
        before = termios.tcgetattr(slave)
        os.write(master, keys)
        chunks = []

        def drain():
            while True:
                try:
                    data = os.read(master, 4096)
                except OSError:
                    return
                if not data:
                    return
                chunks.append(data)

        reader = threading.Thread(target=drain)
        reader.daemon = True
        reader.start()
        handle = it.wrap_tty(slave)
        try:
            code = it.run(tty=handle)
            after = termios.tcgetattr(handle.fileno())
        finally:
            handle.close()
            reader.join(timeout=10)
            os.close(master)
        return code, b"".join(chunks).decode("utf-8", "replace"), before, after

    def test_toggling_codex_generates_the_user_global_commands(self):
        code, output, _before, _after = self.drive(
            DOWN * CODEX_INDEX + TOGGLE + CONFIRM)
        self.assertEqual(code, 0)
        self.assertEqual(self.record()["harnesses"], ["codex"])
        self.assertEqual(self.record()["version"], it.RECORD_VERSION)
        for path in self.codex_files():
            self.assertTrue(os.path.exists(path), path)
        self.assertIn("codex", output)

    def test_the_documented_key_sequence_toggles_two_harnesses(self):
        # space, down, space, enter — the first two registry entries.
        code, _output, _before, _after = self.drive(
            TOGGLE + DOWN + TOGGLE + CONFIRM)
        self.assertEqual(code, 0)
        self.assertEqual(self.record()["harnesses"], list(hr.ids()[:2]))
        for harness_id in hr.ids()[:2]:
            first = hg.user_path(hr.get(harness_id), hb.commands()[0])
            self.assertTrue(os.path.exists(first), first)

    def test_a_confirmed_run_restores_the_terminal_and_the_cursor(self):
        _code, output, before, after = self.drive(TOGGLE + CONFIRM)
        self.assertEqual(before, after)
        self.assertIn(wordmark.SHOW_CURSOR, output)

    def test_an_abort_writes_nothing_and_restores_the_terminal(self):
        code, output, before, after = self.drive(
            TOGGLE + DOWN + TOGGLE + ABORT)
        self.assertEqual(code, 0)
        self.assertEqual(before, after)
        self.assertIn(wordmark.SHOW_CURSOR, output)
        self.assertEqual(home_tree(self.home), [],
                         "an aborted flow must write nothing")

    def test_a_bare_escape_aborts_like_q(self):
        code, output, before, after = self.drive(
            TOGGLE + DOWN + TOGGLE + ESCAPE)
        self.assertEqual(code, 0)
        self.assertEqual(before, after)
        self.assertIn(wordmark.SHOW_CURSOR, output)
        self.assertEqual(home_tree(self.home), [],
                         "an aborted flow must write nothing")
        self.assertIn("esc", output)

    def test_an_interrupt_aborts_like_q(self):
        code, _output, before, after = self.drive(TOGGLE + INTERRUPT)
        self.assertEqual(code, 0)
        self.assertEqual(before, after)
        self.assertEqual(home_tree(self.home), [])

    def test_a_recorded_harness_starts_selected_and_survives_a_bare_confirm(
            self):
        self.write_record({"version": 1,
                           "harnesses": ["codex", "no-such-harness"]})
        code, _output, _before, _after = self.drive(CONFIRM)
        self.assertEqual(code, 0)
        # The unknown id is dropped, the recorded one is rewritten.
        self.assertEqual(self.record()["harnesses"], ["codex"])
        for path in self.codex_files():
            self.assertTrue(os.path.exists(path), path)


if __name__ == "__main__":
    unittest.main()
