#!/usr/bin/env python3
"""harness_bodies — the feature-scaled command-body render engine.

One distilled body template per ``/s:`` command lives under the plugin's
``harness/bodies/`` tree; this module composes the text a harness actually
receives by scaling that single source to the features the target harness
declares. Nothing here writes files: ``render`` returns a string and the
generation step decides where it lands.

The template dialect is deliberately tiny — whole-line HTML-comment markers,
which stay invisible in a markdown preview and need no templating
dependency:

    <!-- description: <one line> -->   the command's one-line description,
                                       required as the template's opening
                                       marker; stripped from the render
    <!-- include:preamble -->          spliced with ``bodies/_preamble.md``
    <!-- if:<feature> -->              kept only when <feature> is declared
    <!-- else -->                      kept only when it is not
    <!-- end -->                       closes the gate
    {refs}                             the harness's reference directory

Gates do not nest, and every gate name must be a member of
``harness_registry.FEATURES`` — a typo is a loud refusal at render time
rather than a segment that silently never renders. Every comment line must
parse as one of the markers above, so the "a rendered body carries no
markers" property is structural: a stray comment cannot leak into output
because it is refused before it gets there.

Stdlib-only Python 3, per the engine's constitution.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness_registry  # noqa: E402

# ``plugins/s/harness/`` — plugin data beside ``skills/``, resolved relative
# to this file so a checkout and a plugin cache snapshot both work.
_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BASE_DIR = os.path.normpath(
    os.path.join(_SCRIPTS_DIR, "..", "..", "..", "harness"))

# The shared partial ``include:preamble`` splices in, and the only include.
PREAMBLE = "_preamble"

_MARKER_RE = re.compile(r"^\s*<!--\s*(?P<body>.*?)\s*-->\s*$")
_IF_RE = re.compile(r"^if:(?P<feature>[a-z0-9-]+)$")
_INCLUDE_RE = re.compile(r"^include:(?P<partial>[a-z0-9_-]+)$")
_DESCRIPTION_RE = re.compile(r"^description:\s*(?P<text>.*)$")

REFS_PLACEHOLDER = "{refs}"


def _base(base_dir):
    return DEFAULT_BASE_DIR if base_dir is None else base_dir


def _bodies_dir(base_dir):
    return os.path.join(_base(base_dir), "bodies")


def _read(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def _template_path(command, base_dir):
    path = os.path.join(_bodies_dir(base_dir), "%s.md" % command)
    if not os.path.isfile(path):
        raise ValueError("no body template for command %r (%s)"
                         % (command, path))
    return path


def _fail(template, lineno, message):
    """Every refusal names the template and the line, so a bad template is
    fixed where it is written rather than where it is rendered."""
    raise ValueError("%s.md:%d: %s" % (template, lineno, message))


def _include_of(text):
    """The partial ``text`` includes, or ``None`` when it is not an include
    marker."""
    marker = _MARKER_RE.match(text)
    if marker is None:
        return None
    include = _INCLUDE_RE.match(marker.group("body"))
    return None if include is None else include.group("partial")


def _numbered(template, text):
    """``text``'s lines as ``(template, lineno, line)`` triples."""
    return [(template, lineno, line)
            for lineno, line in enumerate(text.splitlines(True), start=1)]


def _expand(command, base_dir):
    """The template's lines with ``include:preamble`` spliced in.

    Each line carries the *template it came from*, so a refusal inside the
    preamble names the preamble rather than whichever body included it.
    """
    expanded = []
    for template, lineno, text in _numbered(
            command, _read(_template_path(command, base_dir))):
        partial = _include_of(text)
        if partial is None:
            expanded.append((template, lineno, text))
            continue
        if partial != "preamble":
            _fail(template, lineno, "unknown include %r" % partial)
        path = os.path.join(_bodies_dir(base_dir), "%s.md" % PREAMBLE)
        if not os.path.isfile(path):
            _fail(template, lineno, "no %s.md partial to include" % PREAMBLE)
        for line in _numbered(PREAMBLE, _read(path)):
            if _include_of(line[2]) is not None:
                _fail(PREAMBLE, line[1], "partials may not include partials")
            expanded.append(line)
    return expanded


def render(command, features, refs_dir=None, base_dir=None):
    """``command``'s body, scaled to the ``features`` a harness declares.

    Includes are resolved, each gated segment is kept only when its feature
    is declared (its ``else`` segment otherwise), every marker line is
    stripped, and ``{refs}`` becomes ``refs_dir``. Raises ``ValueError``,
    naming the template, for an unknown gate name, a malformed gate, a
    stray comment, or a surviving ``{refs}`` with no ``refs_dir`` to put
    there.
    """
    declared = set(features or ())
    kept = []
    gate = None          # the open gate's feature name, or None
    gate_declared = False
    in_else = False
    keeping = True
    gate_line = 0
    gate_template = command

    for template, lineno, text in _expand(command, base_dir):
        marker = _MARKER_RE.match(text)
        if marker is None:
            if "<!--" in text:
                _fail(template, lineno,
                      "comment markers must stand alone on their own line")
            if keeping:
                kept.append(text)
            continue

        body = marker.group("body")
        opening = _IF_RE.match(body)
        if opening is not None:
            if gate is not None:
                _fail(template, lineno,
                      "gates do not nest (%r is still open)" % gate)
            feature = opening.group("feature")
            if feature not in harness_registry.FEATURES:
                _fail(template, lineno, "unknown gate %r — not a member of "
                                        "harness_registry.FEATURES" % feature)
            gate, gate_declared, in_else = feature, feature in declared, False
            gate_line, gate_template = lineno, template
            keeping = gate_declared
        elif body == "else":
            if gate is None:
                _fail(template, lineno, "else outside a gate")
            if in_else:
                _fail(template, lineno, "a gate takes one else")
            in_else, keeping = True, not gate_declared
        elif body == "end":
            if gate is None:
                _fail(template, lineno, "end outside a gate")
            gate, in_else, keeping = None, False, True
        elif _DESCRIPTION_RE.match(body) is not None:
            continue
        else:
            _fail(template, lineno, "unknown marker %r" % body)

    if gate is not None:
        _fail(gate_template, gate_line, "gate %r is never closed" % gate)

    out = "".join(kept)
    if REFS_PLACEHOLDER in out:
        if refs_dir is None:
            raise ValueError(
                "%s.md: a kept segment carries %s but no refs_dir was given"
                % (command, REFS_PLACEHOLDER))
        out = out.replace(REFS_PLACEHOLDER, refs_dir)
    return out


def commands(base_dir=None):
    """Every body template's id, sorted; ``_``-prefixed partials excluded."""
    bodies = _bodies_dir(base_dir)
    return tuple(sorted(
        name[:-len(".md")] for name in os.listdir(bodies)
        if name.endswith(".md") and not name.startswith("_")))


def reference(command, base_dir=None):
    """``command``'s fallback reference text, or ``None`` when it has none."""
    path = os.path.join(_base(base_dir), "references", "%s.md" % command)
    return _read(path) if os.path.isfile(path) else None


def description(command, base_dir=None):
    """The one-line description ``command``'s template declares, or ``None``
    when the template declares none."""
    for text in _read(_template_path(command, base_dir)).splitlines():
        marker = _MARKER_RE.match(text)
        if marker is None:
            continue
        declared = _DESCRIPTION_RE.match(marker.group("body"))
        if declared is not None:
            return declared.group("text").strip()
    return None
