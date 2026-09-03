#!/usr/bin/env python3
"""spec_lint.py — structural validator for the shipd spec format (stdlib
only, no network, no third-party imports).

This is the linter that fills the gating role ``openspec validate --strict``
fills today: it checks that master specs and change deltas are structurally
sound before the merge engine runs, and exits non-zero on any error so it can
gate a build.

Checks (see the shipd-spec-lint capability for the behavioral contract):

  Requirement structural validation
    every requirement block (master and delta) has an `id`, at least one
    SHALL/MUST statement, and at least one `#### Scenario:` block.
  Unique identifiers
    `id` slugs are unique within each capability master and within each delta.
  Delta header and scenario validity
    deltas use only the four known operation headers, and every scenario uses
    exactly four hashtags.
  Base-hash presence
    every MODIFIED/REMOVED entry carries a `base:` line.
  Removal metadata
    every REMOVED entry carries both `Reason` and `Migration`.
  Rename metadata
    every RENAMED entry carries `FROM:` and a kebab-case `TO:`.
  Context economy (warning only)
    `plan.md` and each delta spec should stay under a ~2,000-token budget
    (estimated as one token per four characters); oversized files print a
    `WARNING: ...` to stderr without affecting the exit code.

CLI:  spec_lint.py [<change>] [--epic <slug>] [--initiative <slug>] [--root DIR]
      With a change name, lints that change's deltas. With --epic, lints one
      epic under .shipd/epics/<slug>/. With --initiative, lints one brief under the
      discoverable workspace's initiatives/<slug>/ (non-zero when no workspace
      is found). Without any, lints the whole master library under .shipd/verified/
      plus every epic under .shipd/epics/.

      With --json, the findings are emitted as one JSON object on stdout —
      `ok`, `errors`, `warnings` — carrying the same strings the text mode
      prints, with the same exit code, instead of the text report.
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cli_common as cc  # noqa: E402
import spec_common as sc  # noqa: E402

SHALL_MUST_RE = re.compile(r"\b(SHALL|MUST)\b")

# The six valid values for a change plan's `Status:` header line. ``rejected``
# is the context-sufficiency gate's parking state; a rejected plan may carry a
# gate-owned ``## Context insufficient`` section (tolerated in any status —
# check_plan_header enforces only that the required sections are present, never
# forbidding this optional one before ``## Idea``).
VALID_STATUSES = ("draft", "ready", "active", "complete", "verified",
                  "rejected")
STATUS_LINE_RE = re.compile(r"^Status:\s*(.*)$")

# The level-2 sections every plan.md must carry, in order.
REQUIRED_PLAN_SECTIONS = ("## Idea", "## Implementation")

# The level-3 subsections every plan.md's ``## Idea`` must carry. Presence-only,
# never order or length: the authoring order (one-sentence summary, then
# Motivation, Details, Non-goals) and the length limits stay guidance in the
# format docs — the linter enforces only that all three headings are present.
REQUIRED_IDEA_SUBSECTIONS = ("### Motivation", "### Details", "### Non-goals")

# The level-2 sections every epic.md must carry, in reader order, with
# ``## Introduction`` mandated as the opening section (shipd-spec-format
# epic-artifact-layout). Sourced from spec_common so the format has one
# authority.
REQUIRED_EPIC_SECTIONS = sc.EPIC_SECTIONS

# Context-economy budget (design D5): ~2,000 tokens per artifact, estimated
# stdlib-only as one token per four characters. Oversized artifacts warn,
# never error.
TOKEN_BUDGET = 2000
CHARS_PER_TOKEN = 4

# Traceability tags (shipd-spec-lint traceability-tag-enforcement): every checkbox
# task in a change's tasks.md carries exactly one `[req: <id>[, <id>...]]` tag
# (or a lone `[req: *]` wildcard for whole-change tasks). Ids resolve against
# the requirement ids the change's own delta specs declare. The tag sits after
# the optional `[P<n>]` group tag, which it never overlaps, so task
# coordination is untouched.
#
# The grammar is **anchored**: a checkbox line's content begins — after
# optional leading blanks — with the `- [<state>]` marker, and the marker alone
# is the whole of it, so even a degenerate text-free marker line is a task. A
# marker-shaped substring further along a line is prose, so a backticked
# literal quoted in a wrapped task description is neither counted as a task nor
# required to carry a tag. This is the same grammar `claim_task.sh` counts
# ordinals with and `spec_status.py` counts boxes with, so the three surfaces
# never disagree about which lines are tasks.
CHECKBOX_RE = re.compile(r"^[ \t]*- \[[ ~x]\]")
REQ_TAG_RE = re.compile(r"\[req:([^\]]*)\]")

# An epic's context sections (`## Research`, `## Video`; shipd-spec-format
# epic-research-section, epic-video-section): a markdown list entry links a
# context file — `- [title](path)`. This captures the link target of any
# inline markdown link on a list-item line; trailing annotation prose after
# the link is ignored.
EPIC_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")

# Plan `## Questions and answers` section (shipd-spec-format
# plan-document-sections, shipd-spec-lint qa-section-validation): one oracle
# consultation per `### Q<n>: <one-line question summary>` entry, numbered
# sequentially from Q1, each carrying the fields below. `**Verdict:**`,
# `**Cited:**`, and `**Queued:**` stay authoring guidance — only the three
# fields `/s:teach` reads mechanically are enforced.
QA_SECTION = "## Questions and answers"
QA_ENTRY_RE = re.compile(r"^###\s+Q(\d+):\s*\S")
QA_REQUIRED_FIELDS = ("**Question:**", "**Answered by:**", "**Answer:**")


class LintError:
    """A single structural error, tied to a file ``location`` for reporting."""

    def __init__(self, message, location=""):
        self.message = message
        self.location = location

    def __str__(self):
        if self.location:
            return "%s: %s" % (self.location, self.message)
        return self.message


class LintWarning(LintError):
    """A non-fatal advisory, reported as ``WARNING: ...`` on stderr. Warnings
    never affect the exit code."""


# ---------------------------------------------------------------------------
# Per-requirement structural checks
# ---------------------------------------------------------------------------


def check_requirement_structural(req, errors, location):
    """Structural checks that apply to every requirement block, in both master
    specs and deltas: an `id`, a SHALL/MUST statement, and at least one
    scenario."""
    label = req.id or ("<requirement '%s'>" % req.title or "<unnamed>")
    if not req.id:
        errors.append(LintError(
            "requirement '%s' has no `id:` line" % (req.title or "<untitled>"),
            location))
    if not SHALL_MUST_RE.search(req.content):
        errors.append(LintError(
            "requirement '%s' has no SHALL/MUST normative statement" % label,
            location))
    if not req.scenarios:
        errors.append(LintError(
            "requirement '%s' has no `#### Scenario:` block" % label,
            location))


def check_scenario_levels(req, errors, location):
    """Every scenario must use exactly four hashtags (`#### Scenario:`). A
    mis-leveled scenario is reported so it is not silently ignored."""
    for sc_block in req.scenarios:
        if sc_block.level != 4:
            errors.append(LintError(
                "requirement '%s' scenario '%s' uses %d hashtags, expected 4"
                % (req.id or req.title, sc_block.title, sc_block.level),
                location))


def check_unique_ids(reqs, errors, location):
    """Report ids that appear more than once among ``reqs``."""
    seen = set()
    for r in reqs:
        if r.id is None:
            continue
        if r.id in seen:
            errors.append(LintError("duplicate id '%s'" % r.id, location))
        seen.add(r.id)


# ---------------------------------------------------------------------------
# File-level linting
# ---------------------------------------------------------------------------


def lint_master_spec(text, location, errors):
    """Lint a master capability spec file."""
    spec = sc.parse_spec(text)
    for req in spec.requirements:
        check_requirement_structural(req, errors, location)
        check_scenario_levels(req, errors, location)
    check_unique_ids(spec.requirements, errors, location)


def lint_delta_spec(text, location, errors):
    """Lint a change delta spec file (structural checks; delta-specific checks
    are layered on in later tasks).

    ADDED and MODIFIED entries carry full requirement content (they become
    master content) and get the full structural check. REMOVED entries only
    reference an existing requirement by id to delete it, so they are checked
    for an `id` only (their `base`/`Reason`/`Migration` metadata is validated
    by the delta-specific checks)."""
    delta = sc.parse_delta(text)

    # Only the four known operation headers are allowed.
    for header in delta.unknown_ops:
        errors.append(LintError(
            "unknown operation header '%s' (expected one of: %s)"
            % (header, ", ".join("## %s Requirements" % op
                                 for op in sc.KNOWN_OPS)), location))

    for req in delta.added + delta.modified:
        check_requirement_structural(req, errors, location)
        check_scenario_levels(req, errors, location)

    # MODIFIED/REMOVED entries must record the base hash they were written
    # against, so the merge concurrency check can run.
    for req in delta.modified + delta.removed:
        if req.base is None:
            errors.append(LintError(
                "entry '%s' under MODIFIED/REMOVED has no `base:` line"
                % (req.id or req.title), location))

    for req in delta.removed:
        if not req.id:
            errors.append(LintError(
                "REMOVED entry '%s' has no `id:` line"
                % (req.title or "<untitled>"), location))
        if req.reason is None:
            errors.append(LintError(
                "REMOVED entry '%s' has no `Reason:` note"
                % (req.id or req.title), location))
        if req.migration is None:
            errors.append(LintError(
                "REMOVED entry '%s' has no `Migration:` note"
                % (req.id or req.title), location))

    # RENAMED entries need both a FROM id and a valid kebab-case TO id.
    for ren in delta.renamed:
        if not ren.from_id:
            errors.append(LintError(
                "RENAMED entry is missing a `FROM:` id", location))
        if not ren.to_id:
            errors.append(LintError(
                "RENAMED entry (FROM: %s) is missing a `TO:` id"
                % (ren.from_id or "?"), location))
        elif not sc.KEBAB_RE.match(ren.to_id):
            errors.append(LintError(
                "RENAMED `TO:` id '%s' is not a valid kebab-case slug"
                % ren.to_id, location))

    keyed = delta.added + delta.modified + delta.removed
    check_unique_ids(keyed, errors, location)


# ---------------------------------------------------------------------------
# Change plan header
# ---------------------------------------------------------------------------


def check_plan_header(root, change, errors):
    """Validate a change's ``plan.md`` header and required sections (see the
    shipd-spec-lint ``proposal-header-validation`` requirement). Reports an error
    when the file is missing, when line 1 is not a ``# <change-slug>`` title
    matching the change directory name, when no ``Status:`` line appears among
    the first five non-blank lines, when the status value is not one of the
    six valid statuses, when the document lacks a level-2 ``## Idea`` or
    ``## Implementation`` section, or when the document lacks any of the
    level-3 ``### Motivation``, ``### Details``, or ``### Non-goals``
    subsections."""
    path = os.path.join(sc.specs_dir(root), "planned", change, "plan.md")
    if not os.path.isfile(path):
        errors.append(LintError(
            "change '%s' has no plan.md (%s not found)" % (change, path),
            path))
        return

    text = _read(path)
    lines = text.splitlines()

    first_line = lines[0].rstrip() if lines else ""
    expected_title = "# %s" % change
    if first_line != expected_title:
        errors.append(LintError(
            "plan.md line 1 is '%s', expected title '%s'"
            % (first_line, expected_title), path))

    non_blank = [ln for ln in lines if ln.strip()][:5]
    status_value = None
    for ln in non_blank:
        m = STATUS_LINE_RE.match(ln.strip())
        if m:
            status_value = m.group(1).strip()
            break

    if status_value is None:
        errors.append(LintError(
            "plan.md has no `Status:` line in its first five non-blank "
            "lines", path))
    elif status_value not in VALID_STATUSES:
        errors.append(LintError(
            "plan.md status value '%s' is not one of: %s"
            % (status_value, ", ".join(VALID_STATUSES)), path))

    stripped = [ln.rstrip() for ln in lines]
    for section in REQUIRED_PLAN_SECTIONS:
        if section not in stripped:
            errors.append(LintError(
                "plan.md has no level-2 `%s` section" % section, path))
    for subsection in REQUIRED_IDEA_SUBSECTIONS:
        if subsection not in stripped:
            errors.append(LintError(
                "plan.md has no level-3 `%s` subsection" % subsection, path))


# ---------------------------------------------------------------------------
# Change plan header metadata
# ---------------------------------------------------------------------------


def check_plan_metadata(root, change, errors):
    """Validate a change's ``plan.md`` optional header metadata block (see the
    shipd-spec-lint ``plan-metadata-validation`` requirement). The block is the
    contiguous ``<Key>: <value>`` run immediately after the ``Status:`` line.
    Reports an error on an unrecognized key, on a value that is not a kebab-case
    slug, on a ``Profile:`` value other than ``full``/``lite``, and on a plan
    carrying both ``Epic:`` and ``Initiative:`` lines (the initiative attaches
    through the epic). A plan with no metadata block is a no-op. A missing plan
    is left to :func:`check_plan_header` to report. A malformed layered
    configuration is reported once, naming ``.shipd-config.json``."""
    # Resolve the layered configuration once: it both locates the content
    # directory (for the plan path) and supplies the theme vocabulary. A
    # malformed or invalid config is a single error naming the file.
    try:
        config, _prov = sc.resolve_config(root)
        content_dir = sc.specs_dirname(config)
    except sc.ConfigError as exc:
        errors.append(LintError(str(exc), sc.CONFIG_FILENAME))
        return
    path = os.path.join(root, content_dir, "planned", change, "plan.md")
    if not os.path.isfile(path):
        return
    pairs = sc.parse_plan_metadata(_read(path))
    keys = [k for k, _ in pairs]

    # Theme vocabulary: validate a declared `Theme:` against a non-empty
    # `valid_themes` in the resolved configuration; an absent config or empty
    # vocabulary accepts any kebab theme.
    valid_themes = None
    if "Theme" in keys:
        themes = config.get("valid_themes")
        if isinstance(themes, list) and themes:
            valid_themes = themes

    for key, value in pairs:
        if key not in sc.METADATA_KEYS:
            errors.append(LintError(
                "plan.md metadata has unrecognized key '%s' (recognized keys: "
                "%s)" % (key, ", ".join(sc.METADATA_KEYS)), path))
            continue
        if not sc.KEBAB_RE.match(value):
            errors.append(LintError(
                "plan.md metadata `%s: %s` value is not a kebab-case slug"
                % (key, value), path))
            continue
        if key == "Profile" and value not in sc.PROFILES:
            errors.append(LintError(
                "plan.md `Profile: %s` is not one of: %s"
                % (value, ", ".join(sc.PROFILES)), path))
        if key == "Theme" and valid_themes is not None \
                and value not in valid_themes:
            errors.append(LintError(
                "plan.md `Theme: %s` is not in the .shipd-config.json "
                "valid_themes vocabulary (%s)"
                % (value, ", ".join(valid_themes)), path))
    if "Epic" in keys and "Initiative" in keys:
        errors.append(LintError(
            "plan.md carries both `Epic:` and `Initiative:`; a grouped change "
            "derives its initiative through its epic, so attach the initiative "
            "to the epic instead", path))


# ---------------------------------------------------------------------------
# Change plan questions-and-answers ledger (shipd-spec-lint
# qa-section-validation)
# ---------------------------------------------------------------------------


def check_plan_qa_section(root, change, errors):
    """Validate a change's optional ``## Questions and answers`` plan section
    (shipd-spec-lint ``qa-section-validation``, shipd-spec-format
    ``plan-document-sections``).

    When the section is absent, no finding is produced. When it is present it
    SHALL hold at least one ``### Q<n>: <one-line question summary>`` entry,
    the entry numbers SHALL run sequentially from ``Q1``, and every entry
    SHALL carry a ``**Question:**``, an ``**Answered by:**``, and an
    ``**Answer:**`` field. Each error names the offending entry. A missing
    plan is left to :func:`check_plan_header` to report."""
    path = os.path.join(sc.specs_dir(root), "planned", change, "plan.md")
    if not os.path.isfile(path):
        return
    section = _section_lines(_read(path), QA_SECTION)
    if section is None:
        return

    # Split the section into entries at its level-3 headings; a heading that is
    # not a well-formed `### Q<n>:` header is an error naming the raw heading.
    entries = []          # (label, header_line, body_lines)
    for line in section:
        if line.startswith("### "):
            m = QA_ENTRY_RE.match(line.rstrip())
            label = "Q%s" % m.group(1) if m else None
            entries.append((label, line.rstrip(), []))
        elif entries:
            entries[-1][2].append(line)

    if not entries:
        errors.append(LintError(
            "plan.md `%s` section has no entries (at least one "
            "`### Q<n>: <summary>` entry required)" % QA_SECTION, path))
        return

    expected = 1
    for label, header, body in entries:
        if label is None:
            errors.append(LintError(
                "plan.md `%s` entry header '%s' does not match "
                "`### Q<n>: <summary>`" % (QA_SECTION, header), path))
            continue
        number = int(label[1:])
        if number != expected:
            errors.append(LintError(
                "plan.md `%s` entry '%s' is out of sequence (expected `### Q%d:`"
                "; entries are numbered sequentially from Q1)"
                % (QA_SECTION, label, expected), path))
        expected = number + 1
        text = "\n".join(body)
        for field in QA_REQUIRED_FIELDS:
            if field not in text:
                errors.append(LintError(
                    "plan.md `%s` entry '%s' has no `%s` field"
                    % (QA_SECTION, label, field), path))


# ---------------------------------------------------------------------------
# Epic reference resolution on a change plan (shipd-spec-lint
# epic-reference-resolution)
# ---------------------------------------------------------------------------


def check_epic_reference(root, change, errors, warnings=None):
    """Resolve a change plan's ``Epic:`` reference. An ``Epic: <slug>`` line
    that does not resolve to an existing ``.shipd/epics/<slug>/epic.md`` is an
    error. A resolved epic whose ``## Changes`` stub table does not list the
    change's own slug produces a :class:`LintWarning` (membership drift is
    visible but never fatal). A plan with no ``Epic:`` line — or no plan at all
    (left to :func:`check_plan_header`) — is a no-op. Warnings are only appended
    when a ``warnings`` list is passed."""
    path = os.path.join(sc.specs_dir(root), "planned", change, "plan.md")
    if not os.path.isfile(path):
        return
    epic_slug = None
    for key, value in sc.parse_plan_metadata(_read(path)):
        if key == "Epic":
            epic_slug = value
            break
    if not epic_slug:
        return
    epic_path = os.path.join(sc.specs_dir(root), "epics", epic_slug, "epic.md")
    if not os.path.isfile(epic_path):
        errors.append(LintError(
            "plan.md `Epic: %s` does not resolve to an existing epic "
            "(%s not found)" % (epic_slug, epic_path), path))
        return
    if warnings is None:
        return
    _header, rows = sc.parse_epic_changes(_read(epic_path))
    member_slugs = {slug for slug, _desc, _ratings in rows}
    if change not in member_slugs:
        warnings.append(LintWarning(
            "change '%s' carries `Epic: %s` but is not listed in that epic's "
            "`## Changes` stub table" % (change, epic_slug), path))


# ---------------------------------------------------------------------------
# Epic validation (shipd-spec-lint epic-structural-validation)
# ---------------------------------------------------------------------------


def _check_epic_metadata(root, path, text, errors):
    """Validate an epic's optional header metadata block, reusing the plan
    header grammar (:func:`spec_common.parse_plan_metadata`) against the epic
    key set (``Theme``, ``Initiative``). ``Profile:`` and ``Epic:`` are not
    recognized on an epic, so they surface as unrecognized-key errors. ``Theme:``
    is validated against a non-empty ``valid_themes`` in the resolved layered
    configuration."""
    pairs = sc.parse_plan_metadata(text)
    keys = [k for k, _ in pairs]

    valid_themes = None
    if "Theme" in keys:
        try:
            config, _prov = sc.resolve_config(root)
        except sc.ConfigError as exc:
            errors.append(LintError(str(exc), path))
        else:
            themes = config.get("valid_themes")
            if isinstance(themes, list) and themes:
                valid_themes = themes

    for key, value in pairs:
        if key not in sc.EPIC_METADATA_KEYS:
            errors.append(LintError(
                "epic.md metadata has unrecognized key '%s' (recognized keys: "
                "%s)" % (key, ", ".join(sc.EPIC_METADATA_KEYS)), path))
            continue
        if not sc.KEBAB_RE.match(value):
            errors.append(LintError(
                "epic.md metadata `%s: %s` value is not a kebab-case slug"
                % (key, value), path))
            continue
        if key == "Theme" and valid_themes is not None \
                and value not in valid_themes:
            errors.append(LintError(
                "epic.md `Theme: %s` is not in the .shipd-config.json "
                "valid_themes vocabulary (%s)"
                % (value, ", ".join(valid_themes)), path))


def _check_epic_changes(text, path, errors):
    """Validate an epic's ``## Changes`` stub table: the exact six-column
    header, at least one data row, kebab-case Change slugs unique within the
    table, and every rating cell one of ``low``/``medium``/``high``."""
    header, rows = sc.parse_epic_changes(text)
    if header is None:
        errors.append(LintError(
            "epic.md `## Changes` section has no stub table", path))
        return
    if header != list(sc.EPIC_CHANGES_COLUMNS):
        errors.append(LintError(
            "epic.md stub table header is %s, expected %s"
            % (header, list(sc.EPIC_CHANGES_COLUMNS)), path))
    if not rows:
        errors.append(LintError(
            "epic.md stub table has no data rows (at least one required)",
            path))
    seen = set()
    for slug, _desc, ratings in rows:
        if not sc.KEBAB_RE.match(slug):
            errors.append(LintError(
                "epic.md stub table Change '%s' is not a kebab-case slug"
                % slug, path))
        elif slug in seen:
            errors.append(LintError(
                "epic.md stub table has a duplicate Change slug '%s'" % slug,
                path))
        seen.add(slug)
        if len(ratings) != 4:
            errors.append(LintError(
                "epic.md stub table row '%s' has %d rating cells, expected 4 "
                "(Code, Integration, Unknowns, Risk)"
                % (slug or "<blank>", len(ratings)), path))
        for rating in ratings:
            if rating not in sc.EPIC_RATINGS:
                errors.append(LintError(
                    "epic.md stub table rating '%s' is not one of: %s"
                    % (rating, ", ".join(sc.EPIC_RATINGS)), path))


def _is_within(path, parent):
    """True when ``path`` is ``parent`` itself or lives beneath it. Both are
    absolute, normalized paths."""
    parent = parent.rstrip(os.sep)
    return path == parent or path.startswith(parent + os.sep)


def _check_epic_link_section(root, path, text, errors, header, folder, noun):
    """Validate one of an epic's optional context-link sections — ``header``
    (e.g. ``"## Research"``), whose entries must resolve to files under the
    content directory's ``folder`` (e.g. ``"research"``), reported with the
    given ``noun`` (e.g. ``"research file"``).

    When the section is present it SHALL hold at least one markdown list entry
    whose link resolves — first relative to the epic's own directory, then
    relative to the repository root — to an existing file under the content
    directory's ``folder`` folder. A section carrying no link entries is an
    error; each link that resolves to no existing file, or to a file outside
    that folder, is an error naming the link. When the section is absent, no
    finding is produced and the folder is never walked."""
    section = _section_lines(text, header)
    if section is None:
        return
    links = []
    for line in section:
        if line.lstrip().startswith(("- ", "* ", "+ ")):
            links.extend(EPIC_LINK_RE.findall(line))
    if not links:
        errors.append(LintError(
            "epic.md `%s` section has no link entries (at least one "
            "`- [title](path)` linking a %s required)" % (header, noun),
            path))
        return
    try:
        folder_root = os.path.abspath(
            os.path.join(sc.specs_dir(root), folder))
    except sc.ConfigError as exc:
        errors.append(LintError(str(exc), sc.CONFIG_FILENAME))
        return
    epic_dir = os.path.dirname(path)
    for target in links:
        resolved = False
        for base in (epic_dir, root):
            candidate = os.path.abspath(os.path.join(base, target))
            if os.path.isfile(candidate) and _is_within(candidate,
                                                        folder_root):
                resolved = True
                break
        if not resolved:
            errors.append(LintError(
                "epic.md `%s` link '%s' does not resolve to an existing "
                "file under the content directory's %s/ folder"
                % (header, target, folder), path))


def _section_lines(text, header):
    """Return the lines of the level-2 ``header`` section (between the header
    and the next ``## `` heading), or ``None`` when the section is absent."""
    lines = text.splitlines()
    idx = next((i for i, ln in enumerate(lines)
                if ln.rstrip() == header), None)
    if idx is None:
        return None
    out = []
    for ln in lines[idx + 1:]:
        if ln.startswith("## "):
            break
        out.append(ln)
    return out


def lint_epic(root, slug, errors, warnings=None):
    """Validate the epic at ``.shipd/epics/<slug>/epic.md`` (shipd-spec-lint
    epic-structural-validation): a ``# <slug>`` title matching the directory, a
    ``Status:`` line whose value is one of the four epic statuses, a recognized
    header metadata block, the three required level-2 sections, and a
    well-formed ``## Changes`` stub table. Appends :class:`LintError` for each
    violation; ``warnings`` is accepted for signature parity with
    :func:`lint_change` (epics emit no warnings today)."""
    path = os.path.join(sc.specs_dir(root), "epics", slug, "epic.md")
    if not os.path.isfile(path):
        errors.append(LintError(
            "epic '%s' has no epic.md (%s not found)" % (slug, path), path))
        return

    text = _read(path)
    lines = text.splitlines()

    first_line = lines[0].rstrip() if lines else ""
    expected_title = "# %s" % slug
    if first_line != expected_title:
        errors.append(LintError(
            "epic.md line 1 is '%s', expected title '%s'"
            % (first_line, expected_title), path))

    non_blank = [ln for ln in lines if ln.strip()][:5]
    status_value = None
    for ln in non_blank:
        m = STATUS_LINE_RE.match(ln.strip())
        if m:
            status_value = m.group(1).strip()
            break
    if status_value is None:
        errors.append(LintError(
            "epic.md has no `Status:` line in its first five non-blank lines",
            path))
    elif status_value not in sc.EPIC_STATUSES:
        errors.append(LintError(
            "epic.md status value '%s' is not one of: %s"
            % (status_value, ", ".join(sc.EPIC_STATUSES)), path))

    _check_epic_metadata(root, path, text, errors)
    check_initiative_reference(root, sc.parse_plan_metadata(text), errors)

    stripped = [ln.rstrip() for ln in lines]
    for section in REQUIRED_EPIC_SECTIONS:
        if section not in stripped:
            errors.append(LintError(
                "epic.md has no level-2 `%s` section" % section, path))
    # ``## Introduction`` must be the first level-2 section: the why-first
    # narrative precedes any technical content (shipd-spec-format
    # epic-artifact-layout). The Introduction carries a ``### Non-goals``
    # subsection bounding the epic's scope.
    first_section = next(
        (ln for ln in stripped if ln.startswith("## ")), None)
    if first_section is not None and first_section != "## Introduction":
        errors.append(LintError(
            "epic.md's first level-2 section is `%s`, expected "
            "`## Introduction` as the opening section" % first_section, path))
    if "### Non-goals" not in stripped:
        errors.append(LintError(
            "epic.md `## Introduction` has no `### Non-goals` subsection",
            path))
    if "## Changes" in stripped:
        _check_epic_changes(text, path, errors)
    _check_epic_link_section(
        root, path, text, errors, "## Research", "research", "research file")
    _check_epic_link_section(
        root, path, text, errors, "## Video", "video", "video intent brief")


# ---------------------------------------------------------------------------
# Initiative briefs (shipd-workspace initiative-brief-format,
# initiative-reference-resolution; shipd-spec-lint initiative-lint-mode)
# ---------------------------------------------------------------------------


def check_initiative_reference(root, metadata, errors):
    """Resolve an ``Initiative:`` reference carried in ``metadata`` (the ordered
    ``(key, value)`` pairs parsed from a change plan or an epic header). When a
    workspace root is discoverable from ``root``, an ``Initiative: <slug>`` line
    SHALL resolve to an existing brief in the nearest workspace-chain member
    holding one (:func:`spec_common.resolve_initiative_brief`,
    shipd-workspace workspace-chain-facilities) — a missing brief in every
    chain member is an error naming both the nearest workspace root and the
    expected path there (so the stray-marker cause is visible). When no
    workspace is discoverable (a bare CI checkout), the check is skipped
    silently, so repo lint never depends on files outside the repository. A
    metadata block with no ``Initiative:`` line is a no-op."""
    slug = None
    for key, value in metadata:
        if key == "Initiative":
            slug = value
            break
    if not slug:
        return
    ws_root = sc.find_workspace_root(root)
    if ws_root is None:
        return
    brief_path = sc.resolve_initiative_brief(root, slug)
    if brief_path is None:
        expected = sc.initiative_brief_path(ws_root, slug)
        errors.append(LintError(
            "`Initiative: %s` does not resolve to a brief (%s not found; "
            "workspace root %s)" % (slug, expected, ws_root), expected))


def _check_brief_project(ws_root, project_value, path, errors):
    """Validate a brief's ``Project:`` value against the workspace registry
    (shipd-workspace initiative-brief-format). Called only when the brief carries a
    ``Project:`` line — a brief without one never loads the registry. Surfaces
    the registry's own :func:`spec_common.validate_workspace` findings first (a
    broken registry must not silently pass a brief), then requires the value to
    name a declared project slug; with no projects declared, any ``Project:``
    line is an error."""
    reg_loc = sc.CONFIG_FILENAME
    try:
        registry = sc.load_workspace(ws_root)
    except sc.ConfigError as exc:
        errors.append(LintError(str(exc)))
        return
    for msg in sc.validate_workspace(registry):
        errors.append(LintError(msg, reg_loc))
    projects = registry.get("projects")
    declared = sorted(projects) if isinstance(projects, dict) else []
    if not declared:
        errors.append(LintError(
            "brief `Project: %s` but no projects declared in the workspace "
            "registry (%s)" % (project_value, reg_loc), path))
    elif project_value not in declared:
        errors.append(LintError(
            "brief `Project: %s` names no declared project (declared slugs: %s)"
            % (project_value, ", ".join(declared)), path))


def lint_initiative(ws_root, slug, errors):
    """Validate the initiative brief at ``<ws_root>/<content-dir>/initiatives/<slug>/brief.md``
    (shipd-workspace initiative-brief-format): a ``# <slug>`` title matching the
    directory, a ``Status:`` line whose value is one of the three initiative
    statuses, a header metadata block whose only recognized key is ``Project:``
    (a kebab value naming a declared project slug), and a ``## Requirements``
    section carrying at least one checkbox requirement. Appends a
    :class:`LintError` for each violation."""
    path = sc.initiative_brief_path(ws_root, slug)
    if not os.path.isfile(path):
        errors.append(LintError(
            "initiative '%s' has no brief (%s not found)" % (slug, path), path))
        return

    text = _read(path)
    lines = text.splitlines()

    first_line = lines[0].rstrip() if lines else ""
    expected_title = "# %s" % slug
    if first_line != expected_title:
        errors.append(LintError(
            "brief.md line 1 is '%s', expected title '%s'"
            % (first_line, expected_title), path))

    non_blank = [ln for ln in lines if ln.strip()][:5]
    status_value = None
    for ln in non_blank:
        m = STATUS_LINE_RE.match(ln.strip())
        if m:
            status_value = m.group(1).strip()
            break
    if status_value is None:
        errors.append(LintError(
            "brief.md has no `Status:` line in its first five non-blank lines",
            path))
    elif status_value not in sc.INITIATIVE_STATUSES:
        errors.append(LintError(
            "brief.md status value '%s' is not one of: %s"
            % (status_value, ", ".join(sc.INITIATIVE_STATUSES)), path))

    project_value = None
    for key, value in sc.parse_plan_metadata(text):
        if key not in sc.BRIEF_METADATA_KEYS:
            errors.append(LintError(
                "brief.md metadata has unrecognized key '%s' (recognized keys: "
                "%s)" % (key, ", ".join(sc.BRIEF_METADATA_KEYS)), path))
            continue
        if not sc.KEBAB_RE.match(value):
            errors.append(LintError(
                "brief.md metadata `%s: %s` value is not a kebab-case slug"
                % (key, value), path))
            continue
        if key == "Project":
            project_value = value
    if project_value is not None:
        _check_brief_project(ws_root, project_value, path, errors)

    stripped = [ln.rstrip() for ln in lines]
    req_idx = next(
        (i for i, ln in enumerate(stripped) if ln == "## Requirements"), None)
    if req_idx is None:
        errors.append(LintError(
            "brief.md has no level-2 `## Requirements` section", path))
        return
    section = []
    for ln in stripped[req_idx + 1:]:
        if ln.startswith("## "):
            break
        section.append(ln)
    if not any(CHECKBOX_RE.search(ln) for ln in section):
        errors.append(LintError(
            "brief.md `## Requirements` section has no checkbox requirements "
            "(at least one `- [ ]` required)", path))


# ---------------------------------------------------------------------------
# Research report validation (shipd-spec-lint research-report-validation,
# shipd-spec-format research-report-format)
# ---------------------------------------------------------------------------

# A numbered source entry under `## Sources`: `N. …` (leading whitespace
# tolerated). The captured group is the source number.
SOURCE_ENTRY_RE = re.compile(r"^\s*(\d+)\.\s")

# An inline citation marker `[n]` NOT immediately followed by `(` — a `[n](...)`
# is a markdown link, not a marker. The captured group is the marker number.
CITATION_MARKER_RE = re.compile(r"\[(\d+)\](?!\()")

# A fenced code-block delimiter line (``` or ~~~, any info string).
CODE_FENCE_RE = re.compile(r"^\s*(```|~~~)")


def _citation_markers_outside_code(text):
    """Return the citation-marker numbers (as strings, in first-seen order) in
    ``text`` that sit outside fenced code blocks and are not immediately
    followed by ``(`` (a markdown link). Fenced blocks are delimited by ``` or
    ~~~ lines, so code samples with index expressions never register as
    markers."""
    markers = []
    in_fence = False
    for line in text.splitlines():
        if CODE_FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        markers.extend(CITATION_MARKER_RE.findall(line))
    return markers


def lint_research(root, slug, errors):
    """Validate the research report at ``<content-dir>/research/<slug>/
    report.md`` (shipd-spec-lint research-report-validation, shipd-spec-format
    research-report-format): a non-empty ``# <title>`` on line 1 is always
    required. The citation skeleton — a ``## Sources`` section holding at least
    one numbered entry (``N. …``), at least one inline ``[n]`` citation marker,
    and every marker (outside fenced code blocks, ignoring ``[n](`` markdown
    links) resolving to a listed source number — is enforced only when the
    report carries a citation signal: a ``## Sources`` section, or at least one
    such marker. A titled report carrying neither signal produces no findings,
    so a supplied document installs without declaring a provenance it does not
    have. Every finding names the report file. These checks run only when the
    emit engine installs a report; :func:`lint_library` never calls them, so the
    library lint never walks the content directory's ``research/`` folder."""
    path = os.path.join(sc.specs_dir(root), "research", slug, "report.md")
    if not os.path.isfile(path):
        errors.append(LintError(
            "research report '%s' not found (%s)" % (slug, path), path))
        return

    text = _read(path)
    lines = text.splitlines()

    first_line = lines[0].rstrip() if lines else ""
    if not first_line.startswith("# ") or not first_line[2:].strip():
        errors.append(LintError(
            "report.md line 1 is '%s', expected a non-empty `# <title>`"
            % first_line, path))

    section = _section_lines(text, "## Sources")
    markers = _citation_markers_outside_code(text)
    if section is None and not markers:
        # No citation signal: a supplied document, validated on its title only.
        return

    source_numbers = set()
    if section is None:
        errors.append(LintError(
            "report.md has no `## Sources` section", path))
    else:
        for line in section:
            m = SOURCE_ENTRY_RE.match(line)
            if m:
                source_numbers.add(m.group(1))
        if not source_numbers:
            errors.append(LintError(
                "report.md `## Sources` section has no numbered entries "
                "(at least one `N. …` required)", path))

    if not markers:
        errors.append(LintError(
            "report.md has no inline `[n]` citation markers (at least one "
            "required)", path))
    else:
        for num in dict.fromkeys(markers):
            if num not in source_numbers:
                errors.append(LintError(
                    "report.md citation marker [%s] does not resolve to a "
                    "listed source" % num, path))


# ---------------------------------------------------------------------------
# Video intent brief validation (shipd-spec-lint video-brief-validation,
# shipd-spec-format video-brief-format)
# ---------------------------------------------------------------------------

# A `Key: value` header metadata line (the brief's own small header parse —
# distinct from parse_plan_metadata, whose vocabulary is anchored on a
# `Status:` line the brief does not carry).
VIDEO_HEADER_LINE_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.+)$")

# A bracketed timestamp opening a `## Sources` entry: `[HH:MM:SS]`, with
# optional fractional seconds, followed by what was said.
VIDEO_TIMESTAMP_RE = re.compile(r"^\[\d{2}:\d{2}:\d{2}(?:\.\d+)?\]\s+\S")


def _video_header_metadata(text):
    """Return the ordered ``(key, value)`` pairs of a video brief's header
    metadata block: the contiguous ``Key: value`` lines immediately following
    the title line, ended by the first blank line or heading."""
    lines = text.splitlines()
    pairs = []
    for line in lines[1:]:
        if line.strip() == "" or line.lstrip().startswith("#"):
            break
        m = VIDEO_HEADER_LINE_RE.match(line)
        if not m:
            break
        pairs.append((m.group(1), m.group(2)))
    return pairs


def lint_video(root, slug, errors):
    """Validate the video intent brief at ``<content-dir>/video/<slug>/
    brief.md`` (shipd-spec-lint video-brief-validation, shipd-spec-format
    video-brief-format): a non-empty ``# <title>`` on line 1, a required
    ``Video:`` header line in the header metadata block immediately following
    the title (``Bundle:`` is optional and unvalidated; ``Project:`` is
    optional but validated against the workspace registry when present), an
    ``## Intents`` section with at least one level-3 intent heading each
    carrying at least one inline ``[n]`` citation marker, and a
    ``## Sources`` section with at least one numbered entry (``N. …``) whose
    text opens with a bracketed timestamp (``[HH:MM:SS]``, fractional seconds
    permitted) followed by what was said; every citation marker outside
    fenced code blocks must resolve to a listed source number. Every finding
    names the brief file. These checks run only when the emit engine installs
    a brief; :func:`lint_library` never calls them, so the library lint never
    walks the content directory's ``video/`` folder."""
    path = os.path.join(sc.specs_dir(root), "video", slug, "brief.md")
    if not os.path.isfile(path):
        errors.append(LintError(
            "video brief '%s' not found (%s)" % (slug, path), path))
        return

    text = _read(path)
    lines = text.splitlines()

    first_line = lines[0].rstrip() if lines else ""
    if not first_line.startswith("# ") or not first_line[2:].strip():
        errors.append(LintError(
            "brief.md line 1 is '%s', expected a non-empty `# <title>`"
            % first_line, path))

    metadata = _video_header_metadata(text)
    if not any(key == "Video" for key, _ in metadata):
        errors.append(LintError(
            "brief.md has no `Video:` header line", path))

    project_value = next(
        (value for key, value in metadata if key == "Project"), None)
    if project_value is not None:
        ws_root = sc.find_workspace_root(root)
        if ws_root is not None:
            _check_brief_project(ws_root, project_value, path, errors)

    intents = _section_lines(text, "## Intents")
    if intents is None:
        errors.append(LintError(
            "brief.md has no level-2 `## Intents` section", path))
    else:
        headings = [i for i, ln in enumerate(intents)
                    if ln.startswith("### ")]
        if not headings:
            errors.append(LintError(
                "brief.md `## Intents` section has no level-3 intent "
                "headings (at least one `### <intent>` required)", path))
        for pos, idx in enumerate(headings):
            end = headings[pos + 1] if pos + 1 < len(headings) else len(intents)
            body = "\n".join(intents[idx:end])
            if not _citation_markers_outside_code(body):
                errors.append(LintError(
                    "brief.md intent '%s' carries no inline `[n]` citation "
                    "marker" % intents[idx][4:].strip(), path))

    section = _section_lines(text, "## Sources")
    source_numbers = set()
    if section is None:
        errors.append(LintError(
            "brief.md has no `## Sources` section", path))
    else:
        for line in section:
            m = SOURCE_ENTRY_RE.match(line)
            if not m:
                continue
            source_numbers.add(m.group(1))
            entry_text = line[m.end():].strip()
            if not VIDEO_TIMESTAMP_RE.match(entry_text):
                errors.append(LintError(
                    "brief.md source entry '%s' has no bracketed timestamp "
                    "(`[HH:MM:SS]`) opening it" % entry_text, path))
        if not source_numbers:
            errors.append(LintError(
                "brief.md `## Sources` section has no numbered entries "
                "(at least one `N. …` required)", path))

    markers = _citation_markers_outside_code(text)
    for num in dict.fromkeys(markers):
        if num not in source_numbers:
            errors.append(LintError(
                "brief.md citation marker [%s] does not resolve to a "
                "listed source" % num, path))


# ---------------------------------------------------------------------------
# Wiki store validation (shipd-spec-lint wiki-lint-mode, shipd-wiki wiki-page-grammar,
# wiki-index-and-log, wiki-question-queue)
# ---------------------------------------------------------------------------

# The four top-level files every wiki store must carry.
WIKI_LAYOUT_FILES = ("schema.md", "index.md", "log.md", "queue.md")


def _lint_wiki_pages(pages_dir, errors):
    """Return ``(page_slugs, page_texts)`` for the ``wiki/`` pages directory,
    appending an error for every reserved or non-kebab page slug. ``page_slugs``
    is the set of valid page slugs; ``page_texts`` maps each slug to its file
    text (for later wikilink resolution)."""
    page_slugs = set()
    page_texts = {}
    if not os.path.isdir(pages_dir):
        return page_slugs, page_texts
    for fname in sorted(os.listdir(pages_dir)):
        if not fname.endswith(".md"):
            continue
        path = os.path.join(pages_dir, fname)
        if not os.path.isfile(path):
            continue
        slug = fname[:-3]
        if slug in sc.WIKI_RESERVED_SLUGS:
            errors.append(LintError(
                "wiki page '%s' uses a reserved slug (reserved: %s)"
                % (slug, ", ".join(sc.WIKI_RESERVED_SLUGS)), path))
            continue
        if not sc.KEBAB_RE.match(slug):
            errors.append(LintError(
                "wiki page slug '%s' is not a kebab-case slug" % slug, path))
            continue
        page_slugs.add(slug)
        page_texts[slug] = _read(path)
    return page_slugs, page_texts


def _lint_wikilinks(location, text, page_slugs, errors):
    """Append an error for every ``[[slug]]`` wikilink in ``text`` (outside
    fenced code blocks) that does not resolve to a slug in ``page_slugs``."""
    for target in dict.fromkeys(sc.extract_wikilinks(text)):
        if target not in page_slugs:
            errors.append(LintError(
                "wikilink [[%s]] does not resolve to an existing page"
                % target, location))


def lint_wiki(ws_root, errors, wiki=None):
    """Validate a wiki store against the shipd-wiki grammar (shipd-spec-lint
    wiki-lint-mode): layout-file presence, reserved/kebab page slugs, wikilink
    resolution (in pages and ``index.md``, outside fenced code blocks),
    bidirectional index coverage, the ``log.md`` dated-header format, and
    ``queue.md`` block fields. Appends a :class:`LintError` for each violation;
    never raises for a missing store (an absent store surfaces as
    missing-layout-file findings).

    By default the store is the workspace store at
    ``<ws_root>/<content-dir>/wiki/``. Pass ``wiki`` to lint an explicit store
    directory instead — e.g. the personal memory store at ``<memory_dir>/wiki``,
    which resolves by fixed path and has no workspace root; ``ws_root`` is then
    unused."""
    if wiki is None:
        wiki = sc.wiki_dir(ws_root)

    for name in WIKI_LAYOUT_FILES:
        path = os.path.join(wiki, name)
        if not os.path.isfile(path):
            errors.append(LintError(
                "wiki store is missing %s" % name, path))

    pages_dir = os.path.join(wiki, "wiki")
    page_slugs, page_texts = _lint_wiki_pages(pages_dir, errors)

    for slug in sorted(page_texts):
        _lint_wikilinks(
            os.path.join(pages_dir, slug + ".md"), page_texts[slug],
            page_slugs, errors)

    index_path = os.path.join(wiki, "index.md")
    if os.path.isfile(index_path):
        index_text = _read(index_path)
        _lint_wikilinks(index_path, index_text, page_slugs, errors)
        entry_slugs = set()
        for entry_slug, _summary in sc.parse_index_entries(index_text):
            entry_slugs.add(entry_slug)
        for slug in sorted(page_slugs - entry_slugs):
            errors.append(LintError(
                "wiki page '%s' has no index.md catalog entry" % slug,
                index_path))
        for slug in sorted(entry_slugs - page_slugs):
            errors.append(LintError(
                "index.md catalogs '%s' but no wiki/%s.md page exists"
                % (slug, slug), index_path))

    log_path = os.path.join(wiki, "log.md")
    if os.path.isfile(log_path):
        for line in _read(log_path).splitlines():
            if line.startswith("## ") and not sc.WIKI_LOG_HEADER_RE.match(line):
                errors.append(LintError(
                    "log.md header '%s' does not match the "
                    "`## [YYYY-MM-DD] <op> | <subject>` shape" % line.strip(),
                    log_path))

    queue_path = os.path.join(wiki, "queue.md")
    if os.path.isfile(queue_path):
        seen = set()
        for qid, fields in sc.parse_queue_blocks(_read(queue_path)):
            if qid in seen:
                errors.append(LintError(
                    "queue.md has a duplicate block '%s'" % qid, queue_path))
            seen.add(qid)
            for field in sc.WIKI_QUEUE_FIELDS:
                if field not in fields:
                    errors.append(LintError(
                        "queue.md block '%s' is missing the `- %s:` field"
                        % (qid, field), queue_path))
                elif fields[field].strip() == "":
                    errors.append(LintError(
                        "queue.md block '%s' has an empty `- %s:` field"
                        % (qid, field), queue_path))


# ---------------------------------------------------------------------------
# Context economy (warnings)
# ---------------------------------------------------------------------------


def check_context_economy(root, change, warnings):
    """Append a :class:`LintWarning` for the change's ``plan.md`` and each
    delta spec whose estimated token count (``len(text) / 4``) exceeds the
    ~2,000-token context-economy budget (see the shipd-spec-lint
    ``context-economy-warning`` requirement). Warnings never affect the exit
    code."""
    change_dir = os.path.join(sc.specs_dir(root), "planned", change)
    targets = [os.path.join(change_dir, "plan.md")]
    deltas_dir = os.path.join(change_dir, "specs")
    if os.path.isdir(deltas_dir):
        for capability in sorted(os.listdir(deltas_dir)):
            path = os.path.join(deltas_dir, capability, "spec.md")
            if os.path.isfile(path):
                targets.append(path)
    for path in targets:
        if not os.path.isfile(path):
            continue
        text = _read(path)
        if len(text) / CHARS_PER_TOKEN > TOKEN_BUDGET:
            warnings.append(LintWarning(
                "~%d tokens exceeds the ~%d-token context-economy budget; "
                "consider decomposing the change into smaller documents"
                % (len(text) // CHARS_PER_TOKEN, TOKEN_BUDGET), path))


# ---------------------------------------------------------------------------
# Task traceability tags
# ---------------------------------------------------------------------------


def _collect_change_req_ids(root, change):
    """Return the set of requirement ids the change's own delta specs declare —
    across every capability and every operation (ADDED/MODIFIED/REMOVED ids plus
    both endpoints of every RENAMED pair). These are the ids a `[req: ...]` tag
    may resolve against."""
    ids = set()
    deltas_dir = os.path.join(sc.specs_dir(root), "planned", change, "specs")
    if not os.path.isdir(deltas_dir):
        return ids
    for capability in sorted(os.listdir(deltas_dir)):
        path = os.path.join(deltas_dir, capability, "spec.md")
        if not os.path.isfile(path):
            continue
        delta = sc.parse_delta(_read(path))
        for req in delta.added + delta.modified + delta.removed:
            if req.id:
                ids.add(req.id)
        for ren in delta.renamed:
            if ren.from_id:
                ids.add(ren.from_id)
            if ren.to_id:
                ids.add(ren.to_id)
    return ids


def check_task_traceability(root, change, errors):
    """Enforce the `[req: ...]` traceability tag on every checkbox task in a
    change's ``tasks.md`` (shipd-spec-lint ``traceability-tag-enforcement``). Each
    checkbox task must carry exactly one well-formed tag whose ids all resolve
    against the change's own delta requirement ids, or a lone ``[req: *]``
    wildcard for whole-change tasks. Every violating task produces its own error
    naming its ordinal position — the 1-based count of checkbox lines, matching
    the coordinator's stable task IDs. A change with no ``tasks.md`` has no
    tasks to enforce, so the check is a no-op there."""
    path = os.path.join(sc.specs_dir(root), "planned", change, "tasks.md")
    if not os.path.isfile(path):
        return
    valid_ids = _collect_change_req_ids(root, change)
    ordinal = 0
    for line in _read(path).splitlines():
        if not CHECKBOX_RE.search(line):
            continue
        ordinal += 1
        tags = REQ_TAG_RE.findall(line)
        if not tags:
            errors.append(LintError(
                "tasks.md task %d has no `[req: ...]` traceability tag"
                % ordinal, path))
            continue
        if len(tags) > 1:
            errors.append(LintError(
                "tasks.md task %d carries %d `[req: ...]` tags; exactly one is "
                "required" % (ordinal, len(tags)), path))
            continue
        parts = [p.strip() for p in tags[0].split(",")]
        if any(p == "" for p in parts):
            errors.append(LintError(
                "tasks.md task %d has a malformed `[req: ...]` tag" % ordinal,
                path))
            continue
        if "*" in parts:
            if len(parts) != 1:
                errors.append(LintError(
                    "tasks.md task %d combines the wildcard `*` with "
                    "requirement ids in its `[req: ...]` tag" % ordinal, path))
            continue
        for rid in parts:
            if rid not in valid_ids:
                errors.append(LintError(
                    "tasks.md task %d references requirement id '%s', which no "
                    "delta spec in the change declares" % (ordinal, rid), path))


# ---------------------------------------------------------------------------
# Artefact reference enforcement
# ---------------------------------------------------------------------------


def check_artefact_references(root, change, errors):
    """Enforce that every file under a change's ``artefacts/`` directory is
    referenced by at least one of `plan.md`, `tasks.md`, or a delta spec, by
    its change-relative POSIX path (shipd-spec-lint
    ``artefact-reference-enforcement``). Returns immediately when the change
    has no ``artefacts/`` directory, so a change without one lints exactly as
    it does without this check."""
    change_dir = os.path.join(sc.specs_dir(root), "planned", change)
    artefacts_dir = os.path.join(change_dir, "artefacts")
    if not os.path.isdir(artefacts_dir):
        return
    haystack_parts = []
    for name in ("plan.md", "tasks.md"):
        path = os.path.join(change_dir, name)
        if os.path.isfile(path):
            haystack_parts.append(_read(path))
    deltas_dir = os.path.join(change_dir, "specs")
    if os.path.isdir(deltas_dir):
        for capability in sorted(os.listdir(deltas_dir)):
            path = os.path.join(deltas_dir, capability, "spec.md")
            if os.path.isfile(path):
                haystack_parts.append(_read(path))
    haystack = "\n".join(haystack_parts)
    for dirpath, dirnames, filenames in os.walk(artefacts_dir):
        dirnames.sort()
        for filename in sorted(filenames):
            full = os.path.join(dirpath, filename)
            rel_posix = os.path.relpath(full, change_dir).replace(
                os.sep, "/")
            if rel_posix not in haystack:
                errors.append(LintError(
                    "artefact '%s' is referenced by none of plan.md, "
                    "tasks.md, or a delta spec" % rel_posix, full))


# ---------------------------------------------------------------------------
# Target discovery and gating
# ---------------------------------------------------------------------------


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def lint_library(root):
    """Lint every master capability spec under ``.shipd/verified/`` and every epic
    under ``.shipd/epics/``. Returns the list of :class:`LintError`. A repository
    with no ``.shipd/epics/`` directory lints exactly as before this feature."""
    errors = []
    specs_dir = os.path.join(sc.specs_dir(root), "verified")
    if os.path.isdir(specs_dir):
        for capability in sorted(os.listdir(specs_dir)):
            path = os.path.join(specs_dir, capability, "spec.md")
            if os.path.isfile(path):
                lint_master_spec(_read(path), path, errors)
    epics_dir = os.path.join(sc.specs_dir(root), "epics")
    if os.path.isdir(epics_dir):
        for slug in sorted(os.listdir(epics_dir)):
            if os.path.isfile(os.path.join(epics_dir, slug, "epic.md")):
                lint_epic(root, slug, errors)
    return errors


def lint_change(root, change, warnings=None):
    """Lint every capability delta of ``change`` under
    ``.shipd/planned/<change>/specs/``. Returns the list of
    :class:`LintError`. When a ``warnings`` list is passed, non-fatal
    :class:`LintWarning` advisories (context economy) are appended to it;
    they never affect the returned errors."""
    errors = []
    check_plan_header(root, change, errors)
    check_plan_metadata(root, change, errors)
    check_plan_qa_section(root, change, errors)
    check_epic_reference(root, change, errors, warnings)
    plan_path = os.path.join(sc.specs_dir(root), "planned", change, "plan.md")
    if os.path.isfile(plan_path):
        check_initiative_reference(
            root, sc.parse_plan_metadata(_read(plan_path)), errors)
    check_task_traceability(root, change, errors)
    check_artefact_references(root, change, errors)
    if warnings is not None:
        check_context_economy(root, change, warnings)
    deltas_dir = os.path.join(sc.specs_dir(root), "planned", change, "specs")
    if not os.path.isdir(deltas_dir):
        errors.append(LintError(
            "change '%s' has no delta specs (%s not found)"
            % (change, deltas_dir)))
        return errors
    for capability in sorted(os.listdir(deltas_dir)):
        path = os.path.join(deltas_dir, capability, "spec.md")
        if os.path.isfile(path):
            lint_delta_spec(_read(path), path, errors)
    return errors


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Structurally validate .shipd/verified specs and change "
                    "deltas; exits non-zero on any error so it can gate a "
                    "build.")
    parser.add_argument("change", nargs="?", default=None,
                        help="change to lint; omit to lint the master library")
    parser.add_argument("--epic", default=None,
                        help="lint a single epic under .shipd/epics/<slug>/")
    parser.add_argument("--initiative", default=None,
                        help="lint a single initiative brief in the "
                             "discoverable workspace")
    parser.add_argument("--workspace", action="store_true",
                        help="lint the discoverable workspace's registry "
                             "(.shipd-config.json workspace registry)")
    parser.add_argument("--wiki", action="store_true",
                        help="lint the discoverable workspace's wiki store "
                             "(<content-dir>/wiki)")
    parser.add_argument("--root", default=os.getcwd(),
                        help="repo root containing the .shipd/ content directory (default: cwd)")
    parser.add_argument("--json", action="store_true", dest="json",
                        help="emit one JSON object on stdout — ok, errors, "
                             "warnings — instead of the text report")
    args = parser.parse_args(argv)

    warnings = []
    # A malformed layered config is a fatal error, not a lint finding:
    # report it as the convention's one `Error:` line and exit 1.
    try:
        if args.wiki:
            errors = []
            ws_root = sc.find_workspace_root(args.root)
            if ws_root is None:
                errors.append(LintError(
                    "no workspace found from %s; `--wiki` requires a "
                    "discoverable workspace root" % os.path.abspath(args.root)))
            else:
                lint_wiki(ws_root, errors)
            target = "wiki"
        elif args.workspace:
            errors = []
            ws_root = sc.find_workspace_root(args.root)
            if ws_root is None:
                errors.append(LintError(
                    "no workspace found from %s; `--workspace` requires a "
                    "discoverable workspace root" % os.path.abspath(args.root)))
            else:
                try:
                    registry = sc.load_workspace(ws_root)
                except sc.ConfigError as exc:
                    errors.append(LintError(str(exc)))
                else:
                    for msg in sc.validate_workspace(registry):
                        errors.append(LintError(msg, sc.CONFIG_FILENAME))
            target = "workspace"
        elif args.initiative:
            errors = []
            ws_root = sc.find_workspace_root(args.root)
            if ws_root is None:
                errors.append(LintError(
                    "no workspace found from %s; `--initiative` requires a "
                    "discoverable workspace root"
                    % os.path.abspath(args.root)))
            else:
                lint_initiative(ws_root, args.initiative, errors)
            target = "initiative '%s'" % args.initiative
        elif args.epic:
            errors = []
            lint_epic(args.root, args.epic, errors, warnings)
            target = "epic '%s'" % args.epic
        elif args.change:
            errors = lint_change(args.root, args.change, warnings)
            target = "change '%s'" % args.change
        else:
            errors = lint_library(args.root)
            target = "master library"
    except sc.ConfigError as exc:
        cc.err(str(exc))
        return 1

    # The machine rendering of the very same findings, carrying the strings the
    # text report prints below (shipd-spec-lint lint-json). The exit code is
    # computed from the same errors either way, so the two modes gate
    # identically; the fatal `Error:` path above is untouched by the flag.
    if args.json:
        print(json.dumps({
            "ok": not errors,
            "errors": [str(err) for err in errors],
            "warnings": [str(warning) for warning in warnings],
        }))
        return 1 if errors else 0

    for warning in warnings:
        print("WARNING: %s" % warning, file=sys.stderr)
    if errors:
        for err in errors:
            print("ERROR: %s" % err, file=sys.stderr)
        print("%d error(s) in %s." % (len(errors), target), file=sys.stderr)
        return 1
    print("OK: %s is valid." % target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
