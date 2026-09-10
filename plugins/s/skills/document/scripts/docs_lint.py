#!/usr/bin/env python3
"""docs_lint.py — check markdown against the mechanical half of the shipd
documentation standard.

The standard itself lives in ``references/standard.md``; this script checks
only the rules a machine can check honestly, and says nothing about the rules
that need judgement (noun clusters, one word one meaning, whether a diagram
earns its place). Stdlib only.

Errors (exit 1):
  * a missing or unknown first-line ``<!-- doc-type: ... -->`` marker
  * a file over its doc type's line cap (concept 100, how-to 150,
    reference 250)
  * a sentence over its word cap — 20 words inside a numbered-list item,
    where the standard puts procedural steps, 25 words everywhere else
  * a paragraph over six sentences
  * a second mermaid fence, where the standard allows one diagram per doc

Warning only, never affecting the exit code (exit 0):
  * a passive-voice match, because detecting passive voice without a
    part-of-speech tagger is noisy and a false error would be worse than a
    missed one

Prose is analysed outside fenced code blocks; headings, table rows,
link-reference definitions, and HTML comments carry no prose and are skipped.
Sentence boundaries are periods, exclamation marks, and question marks
followed by whitespace — except after a known abbreviation, or where the
period sits inside an inline-code span, which the analyser masks to a single
word before it splits anything.

Usage:
  docs_lint.py <file.md> [<file.md> ...]

Exit codes: 0 no errors, 1 any error, 2 usage or unreadable file.
"""

from __future__ import annotations

import re
import sys

USAGE = "usage: docs_lint.py <file.md> [<file.md> ...]"

LINE_CAPS = {"concept": 100, "how-to": 150, "reference": 250}

DESCRIPTIVE_CAP = 25
PROCEDURAL_CAP = 20
PARAGRAPH_CAP = 6

MARKER_RE = re.compile(r"^<!--\s*doc-type:\s*([A-Za-z0-9-]+)\s*-->\s*$")
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s")
SETEXT_RE = re.compile(r"^\s{0,3}(=+|-{2,})\s*$")
TABLE_RE = re.compile(r"^\s*\|")
LINKREF_RE = re.compile(r"^\s*\[[^\]]+\]:\s")
COMMENT_RE = re.compile(r"^\s*<!--")
NUMBERED_RE = re.compile(r"^\s*\d+[.)]\s+")
BULLET_RE = re.compile(r"^\s*[-*+]\s+")
FENCE_RE = re.compile(r"^\s*(```+|~~~+)(.*)$")
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")

# Periods that end one of these tokens never end a sentence.
ABBREVIATIONS = {"e.g.", "i.e.", "etc.", "vs."}

BE_FORMS = {"is", "are", "was", "were", "be", "been", "being", "am"}

# Participles the "-ed" test misses, kept short on purpose: every entry here
# is a word the heuristic will flag after a form of "be".
IRREGULAR_PARTICIPLES = {
    "written", "built", "made", "run", "given", "taken", "seen", "done",
    "known", "shown", "held", "kept", "sent", "set", "put", "found", "told",
    "left", "drawn", "thrown", "brought", "caught", "taught", "read", "lost",
    "met", "paid", "said", "sold", "won", "chosen", "driven", "hidden",
}


class Finding:
    """One reported line: ``path:line: error|warning: message``."""

    def __init__(self, path, line, level, message):
        self.path = path
        self.line = line
        self.level = level
        self.message = message

    def __str__(self):
        return "%s:%d: %s: %s" % (self.path, self.line, self.level,
                                  self.message)


class Unit:
    """A contiguous run of prose lines: one paragraph, or one list item."""

    def __init__(self, kind, numbered=False):
        self.kind = kind          # "para" or "item"
        self.numbered = numbered
        self.segments = []        # (line number, text)

    def add(self, line, text):
        self.segments.append((line, text))

    @property
    def word_cap(self):
        return PROCEDURAL_CAP if self.numbered else DESCRIPTIVE_CAP

    @property
    def cap_name(self):
        return "procedural" if self.numbered else "descriptive"


def mask_inline_code(text):
    """Blank out inline-code spans, preserving length.

    The mask keeps every character offset valid, so a finding still maps back
    to its line, and it holds no whitespace or sentence punctuation, so a
    span counts as one word and never ends a sentence.
    """
    return INLINE_CODE_RE.sub(lambda m: "C" * len(m.group(0)), text)


def _token_before(text, end):
    """The whitespace-delimited token ending at offset ``end`` (exclusive)."""
    start = end
    while start > 0 and not text[start - 1].isspace():
        start -= 1
    return text[start:end]


def split_sentences(text):
    """Split masked prose into ``(start, end)`` offset spans."""
    spans = []
    start, i, size = 0, 0, len(text)
    while i < size:
        if text[i] in ".!?":
            end = i + 1
            while end < size and text[end] in ".!?)\"'”’]":
                end += 1
            rest = text[end:]
            if not rest or rest[0].isspace():
                if _is_boundary(text, i):
                    spans.append((start, end))
                    start = end + (len(rest) - len(rest.lstrip()))
                    i = start
                    continue
        i += 1
    if text[start:].strip():
        spans.append((start, size))
    return spans


def _is_boundary(text, punct):
    """False only where the period belongs to a known abbreviation.

    The standard authorises two guards, this one and the inline-code mask the
    caller applies before it splits. The case of the next word is not a third
    guard: shipd's own name is lowercase, so a case test merges every sentence
    that opens with it — hiding the paragraph cap and inventing over-cap
    sentences out of two conforming ones.
    """
    return _token_before(text, punct + 1).lower() not in ABBREVIATIONS


def count_words(sentence):
    return len(sentence.split())


def passive_match(sentence):
    """The passive phrase a form of "be" plus a participle makes, or None."""
    # Trailing punctuation is stripped too, so a sentence-final participle
    # ("The spec is written.") still reads as one.
    tokens = [t.strip("`*_()[]{}\"',;:.!?").lower() for t in sentence.split()]
    for index, token in enumerate(tokens):
        if token not in BE_FORMS:
            continue
        for offset in range(1, 3):
            if index + offset >= len(tokens):
                break
            nxt = tokens[index + offset]
            if not nxt:
                continue
            if nxt.endswith("ed") or nxt in IRREGULAR_PARTICIPLES:
                return "%s %s" % (token, nxt)
    return None


def collect_units(lines):
    """Split a document's lines into prose units and mermaid fence lines.

    Returns ``(units, mermaid_lines)``. A list item is its own unit and never
    joins a paragraph: the six-sentence paragraph cap governs prose blocks,
    not the length of a list.
    """
    units = []
    mermaid_lines = []
    current = None
    fence = None

    def flush():
        nonlocal current
        if current is not None and current.segments:
            units.append(current)
        current = None

    for number, raw in enumerate(lines, start=1):
        stripped = raw.strip()

        if fence is not None:
            if stripped.startswith(fence):
                fence = None
            continue

        match = FENCE_RE.match(raw)
        if match:
            flush()
            fence = match.group(1)[:3]
            if match.group(2).strip().lower().startswith("mermaid"):
                mermaid_lines.append(number)
            continue

        if not stripped:
            flush()
            continue

        if (HEADING_RE.match(raw) or TABLE_RE.match(raw)
                or LINKREF_RE.match(raw) or COMMENT_RE.match(raw)
                or SETEXT_RE.match(raw)):
            flush()
            continue

        item = NUMBERED_RE.match(raw) or BULLET_RE.match(raw)
        if item:
            flush()
            current = Unit("item", numbered=bool(NUMBERED_RE.match(raw)))
            current.add(number, raw[item.end():].strip())
            continue

        if current is None:
            current = Unit("para")
        current.add(number, stripped)

    flush()
    return units, mermaid_lines


def _joined(unit):
    """The unit's text on one line, with an offset-to-line-number index."""
    parts = []
    index = []
    position = 0
    for number, text in unit.segments:
        if parts:
            parts.append(" ")
            position += 1
        index.append((position, number))
        parts.append(text)
        position += len(text)
    return "".join(parts), index


def _line_of(index, offset):
    line = index[0][1]
    for start, number in index:
        if start <= offset:
            line = number
        else:
            break
    return line


def check_text(path, lines):
    """Every prose finding in one document, in line order."""
    findings = []
    units, mermaid_lines = collect_units(lines)

    for unit in units:
        text, index = _joined(unit)
        masked = mask_inline_code(text)
        spans = split_sentences(masked)

        if unit.kind == "para" and len(spans) > PARAGRAPH_CAP:
            findings.append(Finding(
                path, unit.segments[0][0], "error",
                "paragraph has %d sentences; the cap is %d sentences"
                % (len(spans), PARAGRAPH_CAP)))

        for start, end in spans:
            sentence = masked[start:end]
            line = _line_of(index, start)
            count = count_words(sentence)
            if count > unit.word_cap:
                findings.append(Finding(
                    path, line, "error",
                    "sentence has %d words; the %s cap is %d words"
                    % (count, unit.cap_name, unit.word_cap)))
            phrase = passive_match(sentence)
            if phrase:
                findings.append(Finding(
                    path, line, "warning",
                    "possible passive voice (\"%s\"); prefer active voice"
                    % phrase))

    for line in mermaid_lines[1:]:
        findings.append(Finding(
            path, line, "error",
            "a second mermaid diagram; the standard allows one per doc"))

    return findings


def check_marker(path, lines):
    """The doc-type marker finding and the resolved type, or ``(finding, None)``."""
    first = lines[0] if lines else ""
    match = MARKER_RE.match(first.strip())
    if not match:
        return Finding(path, 1, "error",
                       "missing first-line doc-type marker; add "
                       "<!-- doc-type: concept|how-to|reference -->"), None
    value = match.group(1).lower()
    if value not in LINE_CAPS:
        return Finding(path, 1, "error",
                       "unknown doc-type '%s'; use concept, how-to, or "
                       "reference" % match.group(1)), None
    return None, value


def check_file(path):
    """Every finding in one file, in line order.

    Raises ``OSError`` when the file cannot be read; the caller turns that
    into exit 2.
    """
    with open(path, "r", encoding="utf-8") as handle:
        lines = handle.read().splitlines()

    findings = []
    marker_finding, doc_type = check_marker(path, lines)
    if marker_finding:
        findings.append(marker_finding)
    elif len(lines) > LINE_CAPS[doc_type]:
        findings.append(Finding(
            path, 1, "error",
            "%s doc has %d lines; the cap is %d lines"
            % (doc_type, len(lines), LINE_CAPS[doc_type])))

    findings.extend(check_text(path, lines))
    findings.sort(key=lambda f: f.line)
    return findings


def main(argv):
    if not argv:
        sys.stderr.write(USAGE + "\n")
        return 2
    if argv[0] in ("-h", "--help"):
        print(USAGE)
        return 0

    errors = 0
    for path in argv:
        try:
            findings = check_file(path)
        except OSError as exc:
            print("%s:1: error: cannot read file (%s)"
                  % (path, exc.strerror or exc))
            return 2
        for finding in findings:
            print(finding)
            if finding.level == "error":
                errors += 1
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
