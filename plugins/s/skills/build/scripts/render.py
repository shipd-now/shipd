#!/usr/bin/env python3
"""render.py — display markdown with its mermaid diagrams drawn as text.

The single code path three surfaces share: the ``shipd render`` verb's own
display modes, the delivery board's markdown panes (``dashboard.py``), and the
``/s:explain`` skill's diagrams. All of them call
:func:`substitute_mermaid_fences`, so a diagram reads identically wherever it
is shown.

Module scope imports the standard library and the vendored
``beautiful_mermaid`` only — no ``textual``, no ``rich`` — so ``import render``
works in the stdlib-only engine and its stdlib-only test suite. The display
modes that do need those packages import them inside their own functions,
after the board's ``tui_bootstrap`` has had a chance to provision them.
"""

from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import beautiful_mermaid  # noqa: E402
import cli_common as cc  # noqa: E402
import tui_bootstrap  # noqa: E402

# An opening fence: optional indent, three or more backticks, the ``mermaid``
# info string, nothing else. The indent and the backtick run are captured
# because the closing fence and the substituted block are measured against
# them.
_OPEN_RE = re.compile(r"^(?P<indent>[ \t]*)(?P<ticks>`{3,})[ \t]*mermaid[ \t]*$")

# The info string the rendered diagram is fenced under: a preformatted block
# every markdown renderer in the engine (textual's ``Markdown``, rich's, and a
# plain terminal) shows monospaced and unstyled, which is what keeps the
# box-drawing aligned.
_RENDERED_INFO = "text"


def _closes(line, ticks, indent):
    """Whether ``line`` closes a fence opened with ``ticks`` backticks at
    ``indent``: a run of at least that many backticks, alone on the line, at
    the opening indent or less."""
    stripped = line.rstrip("\n\r")
    body = stripped.lstrip(" \t")
    lead = stripped[:len(stripped) - len(body)]
    if len(lead) > len(indent):
        return False
    return len(body) >= len(ticks) and set(body) == {"`"}


def _dedent(lines, indent):
    """``lines`` with up to ``indent``'s width of leading whitespace removed —
    the fence's own indentation, which is markdown structure rather than
    mermaid source."""
    out = []
    for line in lines:
        stripped = line
        for ch in indent:
            if stripped.startswith(ch):
                stripped = stripped[1:]
            else:
                break
        out.append(stripped)
    return out


def _fenced(diagram, indent):
    """The rendered ``diagram`` as an indented ```` ```text ```` block, as a
    list of newline-terminated lines."""
    out = ["%s%s%s\n" % (indent, "```", _RENDERED_INFO)]
    for line in diagram.rstrip("\n").split("\n"):
        out.append("%s%s\n" % (indent, line) if line else "\n")
    out.append("%s```\n" % indent)
    return out


def substitute_mermaid_fences(text, use_ascii=False):
    """Return ``text`` with every ```` ```mermaid ```` fenced block replaced by
    a ```` ```text ```` block holding the diagram rendered as characters.

    Everything else is byte-identical, and so is any fence the renderer cannot
    draw: an unsupported diagram type, a syntax error, or any other exception
    leaves that fence exactly as it was, so a document never loses content to a
    rendering failure. Fences are recognized at any indentation; the diagram is
    re-indented to match.

    ``use_ascii`` selects the vendored renderer's 7-bit charset (``+``, ``-``,
    ``|``) instead of Unicode box drawing.
    """
    lines = text.splitlines(keepends=True)
    out = []
    i = 0
    while i < len(lines):
        opened = _OPEN_RE.match(lines[i].rstrip("\n\r"))
        if opened is None:
            out.append(lines[i])
            i += 1
            continue
        indent, ticks = opened.group("indent"), opened.group("ticks")
        close = None
        for j in range(i + 1, len(lines)):
            if _closes(lines[j], ticks, indent):
                close = j
                break
        if close is None:
            # An unterminated fence is not a fence: pass the rest through.
            out.extend(lines[i:])
            break
        body = "".join(_dedent(lines[i + 1:close], indent))
        try:
            diagram = beautiful_mermaid.render_mermaid_ascii(
                body, use_ascii=use_ascii)
        except Exception:
            out.extend(lines[i:close + 1])
        else:
            out.extend(_fenced(diagram, indent))
        i = close + 1
    return "".join(out)


# ---------------------------------------------------------------------------
# Reading the document
# ---------------------------------------------------------------------------

# The file argument that means standard input, so a caller can pipe a document
# in — the form ``/s:explain`` uses to render one fenced block.
STDIN = "-"


class ReadError(Exception):
    """The document could not be read. Carries the finished ``Error:``
    reason."""


def read_document(path):
    """The markdown at ``path``, or standard input when ``path`` is ``-``.

    Raises :class:`ReadError` rather than exiting, so every caller keeps
    owning its own exit code — the engine's CLI convention.
    """
    if path == STDIN:
        try:
            return sys.stdin.read()
        except OSError as exc:
            raise ReadError("cannot read standard input: %s" % exc)
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except (OSError, UnicodeDecodeError) as exc:
        raise ReadError("cannot read %s: %s" % (path, exc))


# ---------------------------------------------------------------------------
# output — the non-interactive mode
# ---------------------------------------------------------------------------

# The one note the styled path prints before degrading, so a caller sees why
# the output is unstyled without the degradation costing them their document.
_UNSTYLED = ("could not set up the styled renderer — printing the markdown "
             "plain; pass --plain to skip this")


def _rich_renderer():
    """``(Console, Markdown)`` from ``rich``, or ``None`` where rich is not
    importable. Imported here rather than at module scope so ``render.py``
    stays a stdlib-only import for the board and the test suite."""
    try:
        from rich.console import Console
        from rich.markdown import Markdown
    except ImportError:
        return None
    return Console, Markdown


def _styled(text):
    """Print ``text`` through rich's markdown renderer, provisioning rich if it
    is missing. ``True`` when it was printed styled, ``False`` when the caller
    should degrade to the plain rendering.

    rich ships as a dependency of the pinned ``textual``, so the board's own
    self-provisioning path supplies it. That path re-execs on success and
    raises ``SystemExit`` when it cannot provision at all; neither may take the
    document down with it, so the failure is caught and reported as a
    degradation.
    """
    renderer = _rich_renderer()
    if renderer is None:
        try:
            tui_bootstrap.ensure_textual(sys.argv, __file__)
        except SystemExit:
            return False
        renderer = _rich_renderer()
        if renderer is None:
            return False
    console_cls, markdown_cls = renderer
    console_cls().print(markdown_cls(text))
    return True


def cmd_output(opts):
    """Print the substituted markdown: rich-styled by default, verbatim under
    ``--plain``."""
    try:
        text = read_document(opts.file)
    except ReadError as exc:
        cc.err(str(exc))
        return 1
    text = substitute_mermaid_fences(text, use_ascii=opts.ascii)
    if not opts.plain and _styled(text):
        return 0
    if not opts.plain:
        cc.warn(_UNSTYLED)
    sys.stdout.write(text)
    return 0


# ---------------------------------------------------------------------------
# screen — the interactive mode
# ---------------------------------------------------------------------------


def viewer_app(text, use_ascii=False):
    """A textual app showing ``text``'s substituted markdown, scrollable and
    quitting on ``q`` or escape.

    A factory rather than a module-scope class: ``textual`` is imported inside
    it, so ``import render`` stays stdlib-only for the board and the tests. The
    widget is the same ``Markdown`` the board's own panes use, which is what
    makes a diagram read identically in both.
    """
    from textual.app import App
    from textual.containers import VerticalScroll
    from textual.widgets import Markdown

    document = substitute_mermaid_fences(text, use_ascii=use_ascii)

    class RenderApp(App):
        BINDINGS = [("q", "quit", "Quit"),
                    ("escape", "quit", "Quit")]

        def compose(self):
            yield VerticalScroll(Markdown(document))

    return RenderApp()


def cmd_screen(opts):
    """Open the document in the full-screen viewer."""
    try:
        text = read_document(opts.file)
    except ReadError as exc:
        cc.err(str(exc))
        return 1
    viewer_app(text, use_ascii=opts.ascii).run()
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser():
    parser = argparse.ArgumentParser(
        prog="render.py",
        description="Display markdown with its mermaid diagrams drawn as "
                    "text.")
    sub = parser.add_subparsers(dest="verb", required=True)

    output = sub.add_parser(
        "output", help="print the document to stdout",
        description="Print the markdown to stdout with every mermaid fence "
                    "replaced by its rendered diagram. Styled through rich by "
                    "default.")
    output.add_argument(
        "file", nargs="?", default=STDIN,
        help="markdown file to render, or - for standard input (default: -)")
    output.add_argument(
        "--plain", action="store_true",
        help="print the substituted markdown verbatim, without styling")
    output.add_argument(
        "--ascii", action="store_true",
        help="draw diagrams with 7-bit characters instead of box drawing")
    output.set_defaults(run=cmd_output)

    screen = sub.add_parser(
        "screen", help="open the document in a full-screen viewer",
        description="Open the markdown in a scrollable full-screen viewer "
                    "with every mermaid fence replaced by its rendered "
                    "diagram. Quit with q or escape.")
    screen.add_argument(
        "file", nargs="?", default=STDIN,
        help="markdown file to render, or - for standard input (default: -)")
    screen.add_argument(
        "--ascii", action="store_true",
        help="draw diagrams with 7-bit characters instead of box drawing")
    screen.set_defaults(run=cmd_screen)
    return parser


def main(argv=None):
    opts = build_parser().parse_args(argv)
    return opts.run(opts)


# The verb whose delegate needs `textual`, so the bootstrap below runs for it
# and for nothing else.
SCREEN_VERB = "screen"


if __name__ == "__main__":
    # Self-provision `textual` before the viewer imports it, exactly as
    # `dashboard.py`'s script entry does — so `shipd render` just works with no
    # manual `pip install`. Only the screen mode is provisioned here: `output
    # --plain` must stay stdlib-only, and the styled `output` provisions on its
    # own, after it has read the document, so an unreadable file is an error
    # rather than a display-stack setup.
    if sys.argv[1:2] == [SCREEN_VERB]:
        tui_bootstrap.ensure_textual(sys.argv, __file__)
    sys.exit(main())
