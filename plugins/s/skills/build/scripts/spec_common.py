#!/usr/bin/env python3
"""spec_common.py — shared parser, content hashing, and serialization for the
shipd spec engine (stdlib only, no network, no third-party imports).

This module is the single place that understands the on-disk spec format
documented in ``.shipd/README.md``. Both ``spec_merge.py`` and ``spec_lint.py``
build on it so the format has exactly one authority.

Format recap (see .shipd/README.md for the full contract):

  Master library file  ``.shipd/verified/<capability>/spec.md``
    Zero or more requirement blocks, each::

        ### Requirement: <title>
        id: <kebab-slug>

        <EARS body using SHALL/MUST>

        #### Scenario: <name>
        - **WHEN** ...
        - **THEN** ...

  Delta file  ``.shipd/planned/<change>/specs/<capability>/spec.md``
    Level-2 operation headers partition requirement blocks::

        ## ADDED Requirements
        ## MODIFIED Requirements     (entries carry `base:`)
        ## REMOVED Requirements      (entries carry `base:`, `Reason:`, `Migration:`)
        ## RENAMED Requirements      (`- FROM: <id>` / `  TO: <id>` bullet pairs)

Parsing is deliberately line-oriented: master and delta files are split into
blocks at ``### Requirement:`` headers (delta files partitioned by their ``##``
operation header first), per design decision D4. No markdown library is used.
"""

import hashlib
import json
import os
import re
import subprocess
import sys

# Length of the truncated hex content hash (design D3).
HASH_LENGTH = 12

# ---------------------------------------------------------------------------
# Format constants
# ---------------------------------------------------------------------------

REQUIREMENT_HEADER_RE = re.compile(r"^###\s+Requirement:\s*(.*?)\s*$")
# Any level of "Scenario:" header, so the linter can flag mis-leveled ones.
SCENARIO_HEADER_RE = re.compile(r"^(#{1,6})\s+Scenario:\s*(.*?)\s*$")
# Metadata lines that may appear immediately under a requirement header.
METADATA_RE = re.compile(r"^(id|base|Reason|Migration):\s*(.*?)\s*$")
OP_HEADER_RE = re.compile(r"^##\s+([A-Za-z]+)\s+Requirements\s*$")

KNOWN_OPS = ("ADDED", "MODIFIED", "REMOVED", "RENAMED")

# RENAMED bullet entries: "- FROM: old-id" then "  TO: new-id".
RENAME_FROM_RE = re.compile(r"^\s*-\s*FROM:\s*(.*?)\s*$")
RENAME_TO_RE = re.compile(r"^\s*TO:\s*(.*?)\s*$")

KEBAB_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# Plan header metadata (shipd-spec-format plan-header-metadata-lines): the optional
# block is the contiguous run of ``<Key>: <value>`` lines immediately after the
# ``Status:`` line, recognizing exactly these five keys; ``Profile`` accepts
# exactly these two values (absent meaning ``full``). ``Fixes`` is repeatable —
# each line names a shipped change this plan remediates (the post-merge fix
# linkage the delivery-metrics change-failure signal derives from).
METADATA_KEYS = ("Profile", "Epic", "Initiative", "Theme", "Fixes")
PROFILES = ("full", "lite")

# Epic header metadata (shipd-spec-format epic-header-metadata): an epic reuses the
# plan header grammar (title / ``Status:`` / metadata block) but recognizes a
# smaller key set and its own status vocabulary. ``Profile:`` and ``Epic:`` are
# deliberately *not* recognized on an epic (a profile is change-level; epics do
# not nest), so they lint as unrecognized keys.
EPIC_STATUSES = ("draft", "ready", "active", "complete")
EPIC_METADATA_KEYS = ("Theme", "Initiative")

# Epic document sections (shipd-spec-format epic-artifact-layout): the four
# required level-2 sections, in reader order, with ``## Introduction`` mandated
# as the opening (why-first) section ahead of any technical content.
EPIC_SECTIONS = ("## Introduction", "## Decisions", "## Design", "## Changes")

# Epic ``## Changes`` stub table (shipd-spec-format epic-artifact-layout): the six
# columns in order, the closed rating vocabulary, and the row-splitting helpers.
EPIC_RATINGS = ("low", "medium", "high")
EPIC_CHANGES_COLUMNS = ("Change", "Description", "Code", "Integration",
                        "Unknowns", "Risk")
SECTION_HEADER_RE = re.compile(r"^##\s+(.*?)\s*$")
TABLE_SEPARATOR_CELL_RE = re.compile(r"^:?-+:?$")

PLAN_STATUS_LINE_RE = re.compile(r"^Status:\s*(.*?)\s*$")
# A single ``<Key>: <value>`` metadata line: the key is one bareword (no
# spaces), the value the trimmed remainder. Unrecognized keys still match so the
# linter can report them; validation of key and value happens in the linter.
METADATA_LINE_RE = re.compile(r"^([A-Za-z][A-Za-z0-9]*):\s*(.*?)\s*$")


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


class Scenario:
    """A single ``#### Scenario:`` block. ``level`` is the number of leading
    hashtags so the linter can detect mis-leveled scenarios (must be 4)."""

    def __init__(self, level, title, text):
        self.level = level
        self.title = title
        self.text = text  # full block text including its own header line

    def __repr__(self):
        return "Scenario(level=%d, title=%r)" % (self.level, self.title)


class Requirement:
    """A single requirement block.

    Attributes
    ----------
    title : str            the human-readable header text
    id : str | None        the `id:` slug (merge key), or None if absent
    base : str | None      the `base:` content hash on delta edits, or None
    reason : str | None    the `Reason:` note on REMOVED entries, or None
    migration : str | None the `Migration:` note on REMOVED entries, or None
    body : str             normative text between metadata and first scenario
    scenarios : list[Scenario]
    content : str          body + scenarios (everything after the metadata
                           block) — the region that is content-hashed
    raw : str              the exact original block text, as parsed
    """

    def __init__(self, title="", id=None, base=None, reason=None,
                 migration=None, body="", scenarios=None, content="", raw=""):
        self.title = title
        self.id = id
        self.base = base
        self.reason = reason
        self.migration = migration
        self.body = body
        self.scenarios = scenarios if scenarios is not None else []
        self.content = content
        self.raw = raw

    def __repr__(self):
        return "Requirement(id=%r, title=%r)" % (self.id, self.title)


class Rename:
    """A ``## RENAMED Requirements`` entry mapping one id to another."""

    def __init__(self, from_id=None, to_id=None, raw=""):
        self.from_id = from_id
        self.to_id = to_id
        self.raw = raw

    def __repr__(self):
        return "Rename(from=%r, to=%r)" % (self.from_id, self.to_id)


class SpecFile:
    """A parsed master spec file: an optional preamble (e.g. a ``# auth``
    title) followed by requirement blocks in file order."""

    def __init__(self, preamble="", requirements=None):
        self.preamble = preamble
        self.requirements = requirements if requirements is not None else []


class DeltaFile:
    """A parsed delta spec file, grouped by operation."""

    def __init__(self):
        self.added = []       # list[Requirement]
        self.modified = []    # list[Requirement]
        self.removed = []     # list[Requirement]
        self.renamed = []     # list[Rename]
        self.unknown_ops = []  # list[str] raw header text of unrecognized ops


# ---------------------------------------------------------------------------
# Block parsing
# ---------------------------------------------------------------------------


def _split_requirement_blocks(lines):
    """Split a list of lines into (preamble, blocks) where each block is a list
    of lines beginning with a ``### Requirement:`` header. ``preamble`` holds
    any lines before the first requirement header."""
    preamble = []
    blocks = []
    current = None
    for line in lines:
        if REQUIREMENT_HEADER_RE.match(line):
            if current is not None:
                blocks.append(current)
            current = [line]
        elif current is None:
            preamble.append(line)
        else:
            current.append(line)
    if current is not None:
        blocks.append(current)
    return preamble, blocks


def parse_requirement_block(text):
    """Parse the text of a single requirement block into a Requirement.

    The block must start with a ``### Requirement:`` header. Metadata lines
    (``id:``, ``base:``, ``Reason:``, ``Migration:``) are read from the
    contiguous run starting at the first non-blank line under the header; the
    remainder is the content (body + scenarios)."""
    raw = text
    lines = text.splitlines()
    title = ""
    if lines:
        m = REQUIREMENT_HEADER_RE.match(lines[0])
        if m:
            title = m.group(1)

    req = Requirement(title=title, raw=raw)

    # Locate the contiguous metadata run beginning at the first non-blank line.
    i = 1
    n = len(lines)
    while i < n and lines[i].strip() == "":
        i += 1
    while i < n:
        m = METADATA_RE.match(lines[i])
        if not m:
            break
        key, val = m.group(1).lower(), m.group(2)
        if key == "id":
            req.id = val or None
        elif key == "base":
            req.base = val or None
        elif key == "reason":
            req.reason = val or None
        elif key == "migration":
            req.migration = val or None
        i += 1

    content_lines = lines[i:]
    req.content = "\n".join(content_lines).strip("\n")
    req.body, req.scenarios = _split_body_and_scenarios(content_lines)
    return req


def _split_body_and_scenarios(content_lines):
    """Split content lines into the leading body text and a list of Scenario
    blocks (any hashtag level, so the linter can flag mis-leveled ones)."""
    body_lines = []
    scenarios = []
    current = None  # (level, title, [lines])
    for line in content_lines:
        m = SCENARIO_HEADER_RE.match(line)
        if m:
            if current is not None:
                scenarios.append(_finish_scenario(current))
            current = (len(m.group(1)), m.group(2), [line])
        elif current is not None:
            current[2].append(line)
        else:
            body_lines.append(line)
    if current is not None:
        scenarios.append(_finish_scenario(current))
    body = "\n".join(body_lines).strip("\n")
    return body, scenarios


def _finish_scenario(current):
    level, title, lines = current
    return Scenario(level=level, title=title, text="\n".join(lines).strip("\n"))


def parse_spec(text):
    """Parse a master spec file into a SpecFile."""
    lines = text.splitlines()
    preamble_lines, blocks = _split_requirement_blocks(lines)
    spec = SpecFile(preamble="\n".join(preamble_lines).strip("\n"))
    for block in blocks:
        spec.requirements.append(parse_requirement_block("\n".join(block)))
    return spec


def parse_delta(text):
    """Parse a delta spec file into a DeltaFile, partitioning by ``##``
    operation header first, then splitting requirement blocks (or RENAMED
    bullet pairs) within each operation section."""
    delta = DeltaFile()
    lines = text.splitlines()

    # Partition into (op, section_lines) segments.
    sections = []  # list[(op_or_None, header_text, [lines])]
    current_op = None
    current_header = None
    current_lines = []

    def flush():
        if current_op is not None or current_lines:
            sections.append((current_op, current_header, current_lines))

    for line in lines:
        m = OP_HEADER_RE.match(line)
        if m:
            flush()
            op = m.group(1).upper()
            current_op = op if op in KNOWN_OPS else "__UNKNOWN__"
            current_header = line.strip()
            current_lines = []
        else:
            current_lines.append(line)
    flush()

    for op, header, seg_lines in sections:
        if op is None:
            # Preamble before any operation header — ignored for merge.
            continue
        if op == "__UNKNOWN__":
            delta.unknown_ops.append(header)
            continue
        if op == "RENAMED":
            delta.renamed.extend(_parse_renames(seg_lines))
            continue
        _, blocks = _split_requirement_blocks(seg_lines)
        reqs = [parse_requirement_block("\n".join(b)) for b in blocks]
        if op == "ADDED":
            delta.added.extend(reqs)
        elif op == "MODIFIED":
            delta.modified.extend(reqs)
        elif op == "REMOVED":
            delta.removed.extend(reqs)
    return delta


# ---------------------------------------------------------------------------
# Plan header metadata (shipd-spec-format plan-header-metadata-lines)
# ---------------------------------------------------------------------------


class ConfigError(Exception):
    """Raised when a ``.shipd-config.json`` file (or a workspace declaration inside
    it) exists but is not parseable JSON, is not a JSON object, or violates a
    resolution rule. The message names the offending file so the caller can
    surface it directly."""


# ---------------------------------------------------------------------------
# Layered configuration (shipd-config config-file-discovery, layered-key-merge,
# content-dir-key)
# ---------------------------------------------------------------------------

# The fixed configuration filename. It is a constant, never renamed by the
# ``dir`` key — otherwise upward discovery could not bootstrap. The ``dir`` key
# renames the *content* directory (default ``.shipd``), never this file.
CONFIG_FILENAME = ".shipd-config.json"

# Built-in defaults beneath all config files. Only ``dir`` carries a defined
# default; every other key is absent unless a layer declares it.
DEFAULT_DIR = ".shipd"


def _load_config_file(path):
    """Parse one ``.shipd-config.json`` file. Raises :class:`ConfigError` naming
    ``path`` when it is not parseable JSON or its top level is not a JSON
    object."""
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as exc:
        raise ConfigError("%s is not valid JSON: %s" % (path, exc))
    if not isinstance(data, dict):
        raise ConfigError("%s must contain a JSON object" % path)
    return data


def load_layered_config(start):
    """Collect the ``.shipd-config.json`` layers governing ``start``, nearest-first
    (shipd-config config-file-discovery).

    Walk from ``os.path.abspath(start)`` parent-by-parent to the filesystem
    root, collecting each directory's ``.shipd-config.json`` when present; then
    append ``~/.shipd-config.json`` as the outermost layer when the home directory
    was not already in the walked chain. Returns a list of ``(path, dict)``
    pairs ordered nearest (most specific) first. A directory with no config file
    is skipped silently; a malformed file raises :class:`ConfigError` naming
    it."""
    layers = []
    seen = set()
    cur = os.path.abspath(start)
    while True:
        seen.add(cur)
        path = os.path.join(cur, CONFIG_FILENAME)
        if os.path.isfile(path):
            layers.append((path, _load_config_file(path)))
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    home = os.path.abspath(os.path.expanduser("~"))
    if home not in seen:
        home_path = os.path.join(home, CONFIG_FILENAME)
        if os.path.isfile(home_path):
            layers.append((home_path, _load_config_file(home_path)))
    return layers


def resolve_config(start):
    """Resolve the effective layered configuration for ``start`` (shipd-config
    layered-key-merge).

    Returns ``(config, provenance)``. ``config`` is the shallow per-key merge of
    every layer over the built-in defaults: the nearest layer declaring a
    top-level key wins it wholesale, values are never deep-merged across layers,
    and unknown keys are preserved. ``provenance`` maps each effective key to the
    path of the file that supplied it, or the string ``"default"`` for a
    defaulted key."""
    layers = load_layered_config(start)
    config = {"dir": DEFAULT_DIR}
    provenance = {"dir": "default"}
    # Nearest-first: the first layer to declare a key wins it wholesale.
    for path, data in layers:
        for key, value in data.items():
            if key not in provenance or provenance[key] == "default":
                config[key] = value
                provenance[key] = path
    return config, provenance


def specs_dirname(config):
    """Return the content-directory name from a resolved config's ``dir`` key
    (shipd-config content-dir-key), defaulting to ``.shipd``. The value SHALL be a
    single, non-empty path component; a value that is empty, non-string, ``.``,
    ``..``, or contains a path separator raises :class:`ConfigError` naming the
    offending value."""
    name = config.get("dir", DEFAULT_DIR)
    if not isinstance(name, str) or not name:
        raise ConfigError(
            "config `dir` must be a non-empty string, got %r" % (name,))
    if name in (".", "..") or "/" in name or "\\" in name or os.sep in name:
        raise ConfigError(
            "config `dir` must be a single path component, got %r" % (name,))
    return name


# ---------------------------------------------------------------------------
# External store root (shipd-config store-root-key, store-repo-folder-name)
# ---------------------------------------------------------------------------

# The config key relocating the content directory into an external store.
STORE_ROOT_KEY = "store_root"

# Memo of the per-repo store folder name, keyed by ``os.path.realpath(root)``.
# Deriving the name costs a ``git rev-parse`` subprocess and ``specs_dir`` is
# on every verb's hot path, so the probe runs once per root per process.
_STORE_FOLDER_CACHE = {}


def repo_store_folder(root):
    """Return the per-repo folder name for ``root`` inside an external store
    (shipd-config store-repo-folder-name).

    The name is the basename of the *main checkout's* directory, so every
    linked worktree resolves the same store folder as the main checkout: probe
    ``git rev-parse --path-format=absolute --git-common-dir`` from ``root``
    and take the basename of the printed path's parent directory. Any git
    failure (git absent, not a repository) falls back to the basename of
    ``root`` itself. Local git only — never the network. Memoized per
    ``os.path.realpath(root)``."""
    key = os.path.realpath(root)
    if key in _STORE_FOLDER_CACHE:
        return _STORE_FOLDER_CACHE[key]
    name = ""
    try:
        result = subprocess.run(
            ["git", "-C", root, "rev-parse", "--path-format=absolute",
             "--git-common-dir"],
            capture_output=True, text=True)
    except OSError:
        result = None
    if result is not None and result.returncode == 0:
        common = result.stdout.strip()
        if common:
            name = os.path.basename(os.path.dirname(os.path.abspath(common)))
    if not name:
        name = os.path.basename(os.path.abspath(root))
    _STORE_FOLDER_CACHE[key] = name
    return name


def _resolve_store_root(config, provenance, root):
    """Resolve the ``store_root`` value out of an already-resolved config, or
    ``None`` when no layer declares the key. Shared by :func:`store_root_dir`
    and :func:`specs_dir` so the layered config is resolved only once."""
    if STORE_ROOT_KEY not in config:
        return None
    value = config[STORE_ROOT_KEY]
    if not isinstance(value, str) or not value:
        raise ConfigError(
            "config `store_root` must be a non-empty string, got %r"
            % (value,))
    expanded = os.path.expanduser(value)
    if os.path.isabs(expanded):
        return os.path.normpath(expanded)
    # A relative value resolves against the directory of the config file that
    # declared it — a deliberate departure from the absolute-only `wiki_base` /
    # `memory_dir` convention, so a committed workspace config stays portable
    # across machines.
    declared = provenance.get(STORE_ROOT_KEY)
    if isinstance(declared, str) and declared != "default":
        base = os.path.dirname(declared)
    else:
        base = os.path.abspath(root)
    return os.path.normpath(os.path.join(base, expanded))


def store_root_dir(root):
    """Return the absolute external store root governing ``root``, or ``None``
    when no layer declares ``store_root`` (shipd-config store-root-key).

    ``~`` expands, and a value still relative after expansion resolves against
    the directory of the config file that declared it (taken from
    :func:`resolve_config`'s provenance map). A declared value that is not a
    non-empty string raises :class:`ConfigError` naming ``store_root``. The key
    merges nearest-wins-wholesale like every other top-level key, so a
    workspace root's declaration governs every member repo beneath it with no
    per-repo configuration."""
    config, provenance = resolve_config(root)
    return _resolve_store_root(config, provenance, root)


def specs_dir(root):
    """Return the absolute content directory for ``root`` (shipd-config
    content-dir-key, store-root-key).

    Where the layered configuration declares ``store_root``, the external store
    governs: the content directory is
    ``<resolved store root>/<repo folder name>``, that per-repo folder directly
    holding ``verified/``, ``planned/``, ``completed/`` and ``research/``, and
    the ``dir`` key does not apply. Otherwise it is ``root`` joined with the
    ``dir`` name resolved from ``root``'s layered configuration."""
    config, provenance = resolve_config(root)
    store = _resolve_store_root(config, provenance, root)
    if store is not None:
        return os.path.join(store, repo_store_folder(root))
    return os.path.join(root, specs_dirname(config))


# ---------------------------------------------------------------------------
# Artifact schema version (schema-versioning schema-version-declaration,
# schema-compat-gate, schema-marker-stamping)
# ---------------------------------------------------------------------------

# The artifact grammar's own semver, independent of the plugin version: it
# moves when the on-disk format documented in ``.shipd/README.md`` moves, not
# when the plugin ships. Major = a grammar break, minor = additive surface,
# patch = a clarification.
SCHEMA_VERSION = "1.0.0"

# The marker's filename inside the resolved content directory. It sits beside
# the artifacts it versions, so an external ``store_root`` store carries its
# own marker and it travels with whatever git repo tracks those artifacts.
SCHEMA_MARKER_NAME = "schema"

# The version an unmarked repo reads as, so every repo predating the marker
# stays valid unmigrated.
SCHEMA_BASELINE = "1.0.0"

SCHEMA_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")

# Roots already warned about a newer-minor marker in this process, so the
# "one stderr warning" contract holds even if a verb checks twice.
_SCHEMA_WARNED = set()


def schema_marker_path(root):
    """Return the absolute path of ``root``'s ``schema`` marker — the resolved
    content directory joined with :data:`SCHEMA_MARKER_NAME`."""
    return os.path.join(specs_dir(root), SCHEMA_MARKER_NAME)


def parse_schema_version(value):
    """Return ``value`` as a ``(major, minor, patch)`` tuple of ints, or ``None``
    when it is not three dot-separated integers. Stdlib-only comparison — a
    tuple of ints orders exactly as semver does for this shape, so no packaging
    dependency is taken (constitution: stdlib-only engine)."""
    if not isinstance(value, str) or not SCHEMA_VERSION_RE.match(value):
        return None
    return tuple(int(part) for part in value.split("."))


def read_schema_marker(root):
    """Return the artifact grammar version ``root``'s artifacts were written
    under (schema-versioning schema-version-declaration).

    Reads the one-line ``schema`` marker in the resolved content directory. An
    absent marker reads as :data:`SCHEMA_BASELINE`, so an unmigrated repo stays
    valid. Content that is not three dot-separated integers raises
    :class:`ConfigError` naming the marker file."""
    path = schema_marker_path(root)
    try:
        with open(path, encoding="utf-8") as fh:
            raw = fh.read()
    except FileNotFoundError:
        return SCHEMA_BASELINE
    except OSError as exc:
        raise ConfigError("%s is not readable: %s" % (path, exc))
    value = raw.strip()
    if parse_schema_version(value) is None:
        raise ConfigError(
            "%s must hold a three-part schema version (N.N.N), got %r"
            % (path, value))
    return value


def stamp_schema_marker(root):
    """Stamp ``root``'s ``schema`` marker with :data:`SCHEMA_VERSION`
    (schema-versioning schema-marker-stamping).

    Writes only while the marker is absent or carries a same-major, strictly
    older version; a marker of a different major is never rewritten (a major
    bump ships with its own migration story), and neither is one already at or
    ahead of the engine's version. Returns the marker path when it was written,
    otherwise ``None``. A malformed existing marker raises through
    :func:`read_schema_marker`.

    Writing only — committing is the caller's, so a stamp made alongside an
    artifact write rides that write's existing :func:`store_autocommit` call
    (its returned path joins the same pathspec) rather than adding a second
    commit to an external store."""
    path = schema_marker_path(root)
    engine = parse_schema_version(SCHEMA_VERSION)
    if os.path.exists(path):
        current = parse_schema_version(read_schema_marker(root))
        if current[0] != engine[0] or current >= engine:
            return None
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(SCHEMA_VERSION + "\n")
    return path


def schema_remedy(repo_version, engine_version=None):
    """The one remedy sentence every schema surface repeats — the gate's error,
    and the doctor's ``fail`` detail."""
    engine_version = engine_version or SCHEMA_VERSION
    return (
        "repo artifacts declare schema %s but this engine speaks %s; "
        "upgrade the older side (the plugin, or the repo's artifacts) so both "
        "share a major version" % (repo_version, engine_version))


def check_schema_compat(root):
    """Refuse or warn before an artifact verb touches ``root``'s artifacts
    (schema-versioning schema-compat-gate).

    A major difference between the repo's marker and :data:`SCHEMA_VERSION`
    raises :class:`ConfigError` naming both versions and the remedy, so the
    caller exits before reading or writing anything. A same-major marker whose
    minor is ahead of the engine's prints one stderr warning and proceeds.
    Everything else is silent. Callers that must report rather than die (the
    doctor) read the marker directly instead."""
    repo_version = read_schema_marker(root)
    repo = parse_schema_version(repo_version)
    engine = parse_schema_version(SCHEMA_VERSION)
    if repo[0] != engine[0]:
        raise ConfigError(schema_remedy(repo_version))
    if repo[1] > engine[1]:
        key = os.path.realpath(root)
        if key not in _SCHEMA_WARNED:
            _SCHEMA_WARNED.add(key)
            sys.stderr.write(
                "warning: repo artifacts declare schema %s, ahead of this "
                "engine's %s; proceeding — some newer surface may be "
                "ignored\n" % (repo_version, SCHEMA_VERSION))


# ---------------------------------------------------------------------------
# Autonomous pipeline (shipd-config autonomous-pipeline-key,
# pipeline-stage-registry, pipeline-entry-validation)
# ---------------------------------------------------------------------------

# The pipeline stage registry: the ordered, canonical relative order of the
# built-in delivery stages. Single source of truth imported by the resolver,
# the pipeline-show verb, and (later) the autopilot. Stage semantics beyond
# name and order do not live here.
PIPELINE_STAGES = ("research", "epic", "plan", "gate", "build", "review")

# The permitted fallback values for a `tools` binding or a `replace` entry.
PIPELINE_FALLBACKS = ("builtin", "skip")

# The built-in preset names a string `autonomous-pipeline` value may take
# (shipd-config pipeline-presets). Stdlib-side names only: the entry table
# itself is data in `pipeline_schema.PRESETS`, keyed by exactly these names, so
# an unknown name is rejected here without importing that module.
PIPELINE_PRESETS = ("default", "eco", "basic")

# The config key naming the autonomous pipeline.
PIPELINE_KEY = "autonomous-pipeline"

# The model ladder, strongest first: the aliases a symbolic tier steps over
# (epic-autopilot stage-model-resolution). Single source of truth for every
# consumer of a pipeline entry's `model` / `subagent_model` option.
MODEL_LADDER = ("fable", "opus", "sonnet", "haiku")

# The symbolic tiers and how far below the anchor each sits. Mirrors
# `pipeline_schema.SYMBOLIC_TIERS` on the stdlib side, so resolution never
# imports the schema module.
_TIER_STEPS = {"session": 0, "tier-below": 1, "tier-two-below": 2}


def resolve_model_tier(tier, session_model=None):
    """Resolve a pipeline entry's ``model``/``subagent_model`` ``tier`` to the
    concrete value a consumer passes as ``--model`` (epic-autopilot
    stage-model-resolution). Pure — no config, no environment, no imports.

    ``session`` resolves to ``session_model`` itself, so a ``None`` anchor
    means "pass no ``--model``" and inherit whatever the CLI defaults to.
    ``tier-below`` and ``tier-two-below`` resolve to the :data:`MODEL_LADDER`
    alias one or two positions below the anchor, clamped at the ladder bottom;
    the anchor is ``session_model`` when it names a ladder alias, else the
    ladder top — an unknown anchor cannot be positioned on the ladder, so
    stepping starts from the strongest rung (fail expensive, never weak). Any
    other non-empty string is a concrete model id and is returned verbatim."""
    if tier not in _TIER_STEPS:
        return tier
    if tier == "session":
        return session_model
    if session_model in MODEL_LADDER:
        index = MODEL_LADDER.index(session_model)
    else:
        index = 0
    return MODEL_LADDER[min(index + _TIER_STEPS[tier], len(MODEL_LADDER) - 1)]


def resolve_pipeline(root):
    """Resolve the effective autonomous pipeline for ``root`` (shipd-config
    autonomous-pipeline-key, pipeline-stage-registry, pipeline-entry-validation).

    Reads the ``autonomous-pipeline`` key from ``root``'s layered configuration
    (nearest-wins-wholesale, via :func:`resolve_config`). When no layer declares
    the key, returns the built-in default: every :data:`PIPELINE_STAGES` stage in
    canonical order as a plain built-in, with provenance ``"default"`` —
    resolved without importing any third-party package. When a layer declares
    it, validates every entry against the stdlib-only, table-driven schema in
    :mod:`pipeline_schema` (imported lazily here, so the default path never
    imports it) and against the canonical relative order of built-in
    stages, then returns the ordered effective entries — plain dicts carrying
    exactly the keys each entry declared — together with the provenance (the
    supplying config file path). A declared list is wholesale: stages absent
    from it simply do not run, which is legal (including for gates). Raises
    :class:`ConfigError` listing every validation error, each naming the
    offending entry by index and content.

    A string value names a built-in preset (shipd-config pipeline-presets).
    The name is checked against :data:`PIPELINE_PRESETS` first, so an unknown
    one fails naming the known presets with no import at all; ``"default"``
    short-circuits to the absent key's pipeline, likewise stdlib-only. Every
    other known name expands through :func:`pipeline_schema.expand_preset`,
    which validates the table's entries exactly like a user-authored list.
    The provenance of a preset-resolved pipeline is
    ``preset:<name> (<config-path>)``."""
    config, prov = resolve_config(root)
    raw = config.get(PIPELINE_KEY)
    if raw is None:
        return [{"stage": name} for name in PIPELINE_STAGES], "default"
    source = prov.get(PIPELINE_KEY, "default")
    provenance = source
    if isinstance(raw, str):
        if raw not in PIPELINE_PRESETS:
            raise ConfigError(
                "unknown pipeline preset '%s' (from %s); known presets: %s"
                % (raw, source, ", ".join(sorted(PIPELINE_PRESETS))))
        provenance = "preset:%s (%s)" % (raw, source)
        if raw == "default":
            return [{"stage": name} for name in PIPELINE_STAGES], provenance
    elif not isinstance(raw, list):
        raise ConfigError(
            "`%s` must be a JSON list or a preset name string (from %s)"
            % (PIPELINE_KEY, source))

    # Imported lazily so the no-key default pipeline never pays for it; the
    # module is stdlib-only, so a *declared* pipeline never depends on a
    # third-party package either.
    import pipeline_schema

    try:
        if isinstance(raw, str):
            entries = pipeline_schema.expand_preset(raw)
        else:
            entries = pipeline_schema.validate_entries(raw)
    except ValueError as exc:
        raise ConfigError(str(exc))

    # Canonical relative order for the built-in stages; custom entries may sit
    # anywhere and are skipped here.
    errors = []
    last_pos = -1
    last_stage = None
    for entry in entries:
        stage = entry.get("stage")
        if stage not in PIPELINE_STAGES:
            continue
        pos = PIPELINE_STAGES.index(stage)
        if pos <= last_pos:
            errors.append(
                "stage %r appears out of canonical order (after %r); the "
                "built-in order is %s"
                % (stage, last_stage, ", ".join(PIPELINE_STAGES)))
        last_pos = pos
        last_stage = stage

    if errors:
        raise ConfigError("\n".join(errors))
    return entries, provenance


# ---------------------------------------------------------------------------
# PR mode (shipd-config pr-mode-key)
# ---------------------------------------------------------------------------

# The config key naming how change-shipping flows open their PRs.
PR_MODE_KEY = "pr-mode"

# The accepted `pr-mode` values: `auto` is today's auto-merging behavior and
# the effective mode when no layer declares the key; `draft` opens draft PRs
# and never arms auto-merge.
PR_MODES = ("auto", "draft")


def resolve_pr_mode(root):
    """Resolve the effective PR mode for ``root`` (shipd-config pr-mode-key).

    Reads the ``pr-mode`` key from ``root``'s layered configuration
    (nearest-wins-wholesale, via :func:`resolve_config`), so a workspace root
    declaring it governs every member repo beneath it. Returns ``"auto"`` when
    no layer declares the key, otherwise the declared value. A *declared* value
    that is not one of :data:`PR_MODES` raises :class:`ConfigError` naming the
    key, the offending value, the accepted values, and the config file that
    supplied it, so a consuming flow can stop and surface it directly —
    declaredness is key presence, never the value, so an explicit JSON ``null``
    is a bad value rather than an absent key. Stdlib-only: the mode is
    standalone config, never a pipeline entry, so resolving it never imports
    any third-party package."""
    config, prov = resolve_config(root)
    if PR_MODE_KEY not in config:
        return PR_MODES[0]
    raw = config[PR_MODE_KEY]
    if raw not in PR_MODES:
        raise ConfigError(
            "`%s` must be one of %s (from %s), got %r"
            % (PR_MODE_KEY, " or ".join(PR_MODES),
               prov.get(PR_MODE_KEY, "default"), raw))
    return raw


# ---------------------------------------------------------------------------
# Workspace discovery (shipd-workspace workspace-root-discovery,
# workspace-registry-loading)
# ---------------------------------------------------------------------------

def workspace_chain(start):
    """Locate every enclosing workspace root by upward search from ``start``
    on the ``.shipd-config.json`` ``workspace``-key convention (shipd-workspace
    workspace-root-discovery).

    Walk from ``os.path.abspath(start)`` parent-by-parent to the filesystem
    root, collecting every directory whose own ``.shipd-config.json`` declares
    a ``workspace`` key — ``start`` itself included — ordered nearest first.
    Returns an empty list when no ancestor declares one. Makes no git
    assumptions and consults no ``.shipd/`` marker. A malformed config file in
    the chain raises :class:`ConfigError` naming it."""
    chain = []
    cur = os.path.abspath(start)
    while True:
        path = os.path.join(cur, CONFIG_FILENAME)
        if os.path.isfile(path):
            data = _load_config_file(path)
            if "workspace" in data:
                chain.append(cur)
        parent = os.path.dirname(cur)
        if parent == cur:
            return chain
        cur = parent


def find_workspace_root(start):
    """Locate the workspace root: the workspace chain's nearest member
    (shipd-workspace workspace-root-discovery), or ``None`` when the chain is
    empty. See :func:`workspace_chain`."""
    chain = workspace_chain(start)
    return chain[0] if chain else None


def resolve_wiki_stores(start):
    """Return every existing wiki store directory across the workspace chain
    resolved from ``start``, nearest first (shipd-workspace
    workspace-chain-facilities).

    A chain member holding no store directory on disk is skipped silently.
    Returns an empty list when the chain is empty or no member holds a
    store."""
    return [d for d in (wiki_dir(root) for root in workspace_chain(start))
            if os.path.isdir(d)]


def resolve_initiative_brief(start, slug):
    """Return the on-disk path of an initiative brief named ``slug`` at the
    nearest workspace-chain member holding it, resolved from ``start``
    (shipd-workspace workspace-chain-facilities).

    Returns ``None`` when no chain member holds the brief, including when the
    chain is empty."""
    for root in workspace_chain(start):
        path = initiative_brief_path(root, slug)
        if os.path.isfile(path):
            return path
    return None


def registry_root(start):
    """Return the workspace-chain member whose project registry is effective,
    resolved from ``start`` (shipd-workspace workspace-chain-facilities).

    The nearest chain member whose ``workspace`` object declares a ``projects``
    key wins outright; when no member declares one, the chain's nearest member
    (``find_workspace_root``'s result) is the fallback. Returns ``None`` when
    the chain is empty. A registry is never merged across chain members —
    whichever root this returns, its own registry (via
    :func:`load_workspace`) is the whole answer."""
    chain = workspace_chain(start)
    if not chain:
        return None
    for root in chain:
        if "projects" in load_workspace(root):
            return root
    return chain[0]


# The marked member-repos block seeded into a git-initialized workspace's
# ``.gitignore`` (shipd-workspace workspace-initialization). The workspace-sync
# member owns the block's contents; init only seeds an empty marked block, and
# the markers make the block idempotent to re-seed and safe for the sync member
# to rewrite in place.
GITIGNORE_MEMBERS_BEGIN = "# >>> shipd-workspace members"
GITIGNORE_MEMBERS_END = "# <<< shipd-workspace members"


def _inside_git_work_tree(target):
    """True when ``target`` is already inside a git work tree, probed with a
    local ``git rev-parse`` (no network). Any git failure (git absent, not a
    repository) reads as ``False``."""
    try:
        result = subprocess.run(
            ["git", "-C", target, "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True)
    except OSError:
        return False
    return result.returncode == 0 and result.stdout.strip() == "true"


def wiki_autocommit(store_dir, paths, subject):
    """Make a local git commit scoped to exactly ``paths`` after a successful
    wiki write, returning True only when a commit was made (shipd-wiki
    wiki-autocommit).

    A silent no-op returning False when ``store_dir`` is not inside a git work
    tree — that is the epic's non-git store case. Otherwise probe
    ``git status --porcelain -- <paths>``: empty output means the write changed
    no bytes, so skip the commit quietly (returns False). Otherwise ``git add``
    then ``git commit`` the paths, the pathspec scoping the commit to exactly
    the written files so unrelated staged index state is never swept in. Any git
    failure (missing identity, hook failure) prints one
    ``warning: wiki auto-commit skipped: …`` line to stderr and returns False —
    the write already succeeded, so its exit code stays zero. Local git only
    (``status``, ``add``, ``commit``) — never the network."""
    if not _inside_git_work_tree(store_dir):
        return False
    paths = list(paths)
    try:
        status = subprocess.run(
            ["git", "-C", store_dir, "status", "--porcelain", "--", *paths],
            capture_output=True, text=True)
        if status.returncode != 0:
            raise RuntimeError(status.stderr.strip() or "git status failed")
        if not status.stdout.strip():
            return False
        add = subprocess.run(
            ["git", "-C", store_dir, "add", "--", *paths],
            capture_output=True, text=True)
        if add.returncode != 0:
            raise RuntimeError(add.stderr.strip() or "git add failed")
        commit = subprocess.run(
            ["git", "-C", store_dir, "commit", "-m", subject, "--", *paths],
            capture_output=True, text=True)
        if commit.returncode != 0:
            raise RuntimeError(commit.stderr.strip() or "git commit failed")
    except (OSError, RuntimeError) as exc:
        sys.stderr.write("warning: wiki auto-commit skipped: %s\n" % exc)
        return False
    return True


def store_autocommit(root, paths, subject):
    """Auto-commit an engine write into an *externally* resolved content
    directory, returning True only when a commit was made (shipd-config
    store-autocommit).

    Returns False without touching git when ``root``'s content directory
    resolves in-repo — committing in-repo artifacts stays the skill/PR
    workflow's job, never the engine's. Otherwise delegates to
    :func:`wiki_autocommit` against the resolved store, inheriting its whole
    convention: a silent no-op when the store is not inside a git work tree, a
    commit scoped to exactly ``paths``, one warning line and an unchanged exit
    code when git fails, and local git only — never the network."""
    if store_root_dir(root) is None:
        return False
    return wiki_autocommit(specs_dir(root), paths, subject)


def _ensure_members_gitignore_block(target):
    """Ensure ``<target>/.gitignore`` carries the marked member-repos block,
    appending an empty marked block only when the markers are absent
    (idempotent). Creates the file when absent."""
    gi_path = os.path.join(target, ".gitignore")
    if os.path.isfile(gi_path):
        with open(gi_path, encoding="utf-8") as fh:
            body = fh.read()
        if GITIGNORE_MEMBERS_BEGIN in body:
            return
        prefix = body if body.endswith("\n") or body == "" else body + "\n"
        sep = "\n" if body and not body.endswith("\n\n") else ""
        new_body = "%s%s%s\n%s\n" % (
            prefix, sep, GITIGNORE_MEMBERS_BEGIN, GITIGNORE_MEMBERS_END)
    else:
        new_body = "%s\n%s\n" % (
            GITIGNORE_MEMBERS_BEGIN, GITIGNORE_MEMBERS_END)
    with open(gi_path, "w", encoding="utf-8") as fh:
        fh.write(new_body)


def init_workspace(path, git=False, nested=False):
    """Initialize a workspace at ``path`` (shipd-workspace
    workspace-initialization).

    Declares ``"workspace": {}`` in ``<path>/.shipd-config.json`` — creating the
    file when absent, otherwise preserving its other keys. Refuses when a
    workspace root is already discoverable from ``path`` (nearest-ancestor
    search, ``path`` itself included): raises :class:`ConfigError` naming that
    existing root and writes nothing, because a nested declaration silently
    re-roots every directory beneath it. Errors when ``path`` is not an existing
    directory rather than creating it.

    When ``nested`` is true, that refusal is skipped for an *enclosing*
    workspace — creation proceeds beneath it — but still applies when ``path``
    itself already declares ``workspace`` (a target is never re-declared).
    Returns a ``(created_root, enclosing_root)`` tuple in this mode,
    ``enclosing_root`` being the discoverable ancestor root nested beneath (or
    ``None`` when none was discoverable). When ``nested`` is false (the
    default), the return value is the created root alone, unchanged from
    before.

    When ``git`` is true, additionally run ``git init`` at the target when it is
    not already inside a git work tree, then ensure the target's ``.gitignore``
    carries the marked member-repos block (appending an empty marked block only
    when the markers are absent). Local git operations only — never the network.
    Stdlib only."""
    target = os.path.abspath(path)
    existing = find_workspace_root(target)
    self_declares = (
        existing is not None
        and os.path.realpath(existing) == os.path.realpath(target))
    if existing is not None and (not nested or self_declares):
        raise ConfigError(
            "a workspace is already discoverable at %s; refusing to nest a "
            "new one (deliberate nesting is a hand edit)" % existing)
    enclosing = existing if nested else None
    if not os.path.isdir(target):
        raise ConfigError(
            "target directory does not exist: %s" % target)
    cfg_path = os.path.join(target, CONFIG_FILENAME)
    data = _load_config_file(cfg_path) if os.path.isfile(cfg_path) else {}
    data["workspace"] = {}
    with open(cfg_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")
    if git:
        if not _inside_git_work_tree(target):
            subprocess.run(["git", "init", target],
                           capture_output=True, text=True)
        _ensure_members_gitignore_block(target)
    if nested:
        return target, enclosing
    return target


def load_workspace(ws_root):
    """Load a workspace's registry as the ``workspace`` object of
    ``<ws_root>/.shipd-config.json`` (shipd-workspace workspace-registry-loading).

    Returns that object as parsed, preserving unknown keys inside it for forward
    compatibility. Raises :class:`ConfigError` (naming the config file) when the
    file is missing, is not parseable JSON, its top level is not a JSON object,
    or its ``workspace`` value is missing or not a JSON object. Interprets
    nothing else — project semantics live in ``validate_workspace`` /
    ``project_of``."""
    path = os.path.join(ws_root, CONFIG_FILENAME)
    data = _load_config_file(path)
    registry = data.get("workspace")
    if not isinstance(registry, dict):
        raise ConfigError(
            "%s must declare a `workspace` object" % path)
    return registry


# ---------------------------------------------------------------------------
# Workspace content locations (shipd-workspace initiative-brief-format,
# project-context-convention)
# ---------------------------------------------------------------------------

# A brief's ``Status:`` vocabulary: an initiative is a goal — ``open`` while
# pursued, ``achieved`` when its requirement checkboxes are all ticked,
# ``dropped`` when abandoned. Deliberately *not* the five change statuses: a
# goal has no draft/ready pipeline.
INITIATIVE_STATUSES = ("open", "achieved", "dropped")

# The only metadata key recognized in a brief header. ``Project:`` is parsed and
# lints as a kebab slug now; registry-existence validation is the project-groups
# member's job (workspace-discovery's tolerant-registry seam).
BRIEF_METADATA_KEYS = ("Project",)


def initiatives_dir(ws_root):
    """Return the initiatives directory under the workspace's resolved content
    directory: ``<ws_root>/<content-dir>/initiatives``."""
    return os.path.join(specs_dir(ws_root), "initiatives")


def projects_dir(ws_root):
    """Return the projects directory under the workspace's resolved content
    directory: ``<ws_root>/<content-dir>/projects``."""
    return os.path.join(specs_dir(ws_root), "projects")


def initiative_brief_path(ws_root, slug):
    """Return the on-disk path of an initiative brief:
    ``<ws_root>/<content-dir>/initiatives/<slug>/brief.md`` (shipd-workspace
    initiative-brief-format), the content directory resolved from the workspace
    root's configuration (default ``.shipd``)."""
    return os.path.join(initiatives_dir(ws_root), slug, "brief.md")


def project_context_path(ws_root, slug):
    """Return the on-disk path of a project's optional steering context:
    ``<ws_root>/<content-dir>/projects/<slug>/context.md`` (shipd-workspace
    project-context-convention)."""
    return os.path.join(projects_dir(ws_root), slug, "context.md")


# ---------------------------------------------------------------------------
# Wiki store (shipd-wiki wiki-store-layout, wiki-page-grammar, wiki-index-and-log,
# wiki-question-queue)
# ---------------------------------------------------------------------------

# The reserved slugs that may never name a ``wiki/<slug>.md`` page: they name
# the store's top-level files/directories, so a page of the same name would
# shadow them.
WIKI_RESERVED_SLUGS = ("index", "log", "queue", "schema", "sources")

# The five ordered fields every ``## q-<slug>`` queue block carries.
WIKI_QUEUE_FIELDS = ("Asked", "Question", "Options", "Recommendation", "Answer")

# A ``[[slug]]`` wikilink; the captured group is the inner link text.
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")

# A fenced code-block delimiter line (``` or ~~~, any info string) — the same
# fence handling the research linter uses, so wikilinks in code samples never
# register as links.
WIKI_CODE_FENCE_RE = re.compile(r"^\s*(```|~~~)")

# An index catalog entry: ``- [[slug]] — <summary>`` (em-dash separator). The
# captured groups are the page slug and the trimmed summary.
WIKI_INDEX_ENTRY_RE = re.compile(
    r"^\s*-\s+\[\[([^\]]+)\]\]\s+—\s+(\S.*?)\s*$")

# A ``log.md`` level-2 entry header: ``## [YYYY-MM-DD] <op> | <subject>``.
WIKI_LOG_HEADER_RE = re.compile(
    r"^##\s+\[(\d{4}-\d{2}-\d{2})\]\s+(.+?)\s+\|\s+(.+?)\s*$")

# A ``queue.md`` block header ``## q-<slug>`` (kebab). The captured group is the
# full block id, e.g. ``q-stale-cache``.
WIKI_QUEUE_HEADER_RE = re.compile(
    r"^##\s+(q-[a-z0-9]+(?:-[a-z0-9]+)*)\s*$")

# A queue block field line: ``- <Field>: <value>``.
WIKI_QUEUE_FIELD_RE = re.compile(
    r"^\s*-\s+(Asked|Question|Options|Recommendation|Answer):\s*(.*?)\s*$")


def wiki_dir(ws_root):
    """Return the workspace wiki store directory under the resolved content
    directory: ``<ws_root>/<content-dir>/wiki`` (shipd-wiki wiki-store-layout)."""
    return os.path.join(specs_dir(ws_root), "wiki")


def wiki_base_dir(ws_root):
    """Return the durable base wiki store directory declared by the optional
    ``wiki_base`` config key resolved from ``ws_root`` (shipd-config
    wiki-base-key), or ``None`` when undeclared.

    The value MUST be a non-empty string; ``~`` is expanded and the expanded
    value MUST be absolute. A value that is not a non-empty string, or does not
    expand to an absolute path, raises :class:`ConfigError` naming ``wiki_base``
    so the consuming verb can exit non-zero. When the expanded value equals the
    store directory of any member of ``ws_root``'s workspace chain — the
    consuming workspace's own store included — the base is treated as
    undeclared (``None``), so a base that is also an enclosing workspace is
    searched once, not twice."""
    config, _prov = resolve_config(ws_root)
    raw = config.get("wiki_base")
    if raw is None:
        return None
    if not isinstance(raw, str) or not raw:
        raise ConfigError(
            "config `wiki_base` must be a non-empty string path, got %r" % (raw,))
    expanded = os.path.expanduser(raw)
    if not os.path.isabs(expanded):
        raise ConfigError(
            "config `wiki_base` must expand to an absolute path, got %r" % (raw,))
    resolved = os.path.realpath(expanded)
    for member in workspace_chain(ws_root):
        if os.path.realpath(wiki_dir(member)) == resolved:
            return None
    return expanded


# The personal memory store root when no layer declares ``memory_dir``.
DEFAULT_MEMORY_DIR = "~/.shipd-memory"


def memory_store_dir(root):
    """Return the personal memory store directory ``<memory_dir>/wiki`` resolved
    from the optional ``memory_dir`` config key (shipd-config memory-store-key).

    Unlike ``wiki_base`` (``None`` when undeclared), ``memory_dir`` defaults to
    ``~/.shipd-memory`` when no layer declares it, so this helper always yields a
    store directory — the personal store is resolved by fixed path, bypassing
    workspace discovery. The value MUST be a non-empty string; ``~`` is expanded
    and the expanded value MUST be absolute. A value that is not a non-empty
    string, or does not expand to an absolute path, raises :class:`ConfigError`
    naming ``memory_dir`` so the consuming verb can exit non-zero."""
    config, _prov = resolve_config(root)
    raw = config.get("memory_dir", DEFAULT_MEMORY_DIR)
    if not isinstance(raw, str) or not raw:
        raise ConfigError(
            "config `memory_dir` must be a non-empty string path, got %r"
            % (raw,))
    expanded = os.path.expanduser(raw)
    if not os.path.isabs(expanded):
        raise ConfigError(
            "config `memory_dir` must expand to an absolute path, got %r"
            % (raw,))
    return os.path.join(expanded, "wiki")


def extract_wikilinks(text):
    """Return the ``[[slug]]`` link targets in ``text`` that sit outside fenced
    code blocks, in first-seen document order (duplicates preserved). Fenced
    blocks are delimited by ``` or ~~~ lines, so code samples never register as
    links (shipd-wiki wiki-page-grammar)."""
    links = []
    in_fence = False
    for line in text.splitlines():
        if WIKI_CODE_FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        links.extend(WIKILINK_RE.findall(line))
    return links


def parse_index_entries(text):
    """Parse ``index.md`` catalog entries: lines matching ``- [[slug]] — <summary>``
    (em-dash separator). Returns a list of ``(slug, summary)`` tuples in document
    order; lines not matching the entry shape are ignored (shipd-wiki
    wiki-index-and-log)."""
    entries = []
    for line in text.splitlines():
        m = WIKI_INDEX_ENTRY_RE.match(line)
        if m:
            entries.append((m.group(1), m.group(2)))
    return entries


def parse_queue_blocks(text):
    """Parse ``queue.md`` into its ``## q-<slug>`` blocks (shipd-wiki
    wiki-question-queue). Returns a list of ``(qid, fields)`` tuples in document
    order, where ``qid`` is the full block id (e.g. ``q-stale-cache``) and
    ``fields`` maps each present field name (a member of
    :data:`WIKI_QUEUE_FIELDS`) to its trimmed value. A non-queue level-2 header
    closes the current block; field lines outside any block are ignored."""
    blocks = []
    current = None  # (qid, fields_dict)
    for line in text.splitlines():
        m = WIKI_QUEUE_HEADER_RE.match(line)
        if m:
            if current is not None:
                blocks.append(current)
            current = (m.group(1), {})
            continue
        if line.startswith("## "):
            # A different level-2 header ends the current block.
            if current is not None:
                blocks.append(current)
                current = None
            continue
        if current is not None:
            fm = WIKI_QUEUE_FIELD_RE.match(line)
            if fm:
                current[1][fm.group(1)] = fm.group(2)
    if current is not None:
        blocks.append(current)
    return blocks


# ---------------------------------------------------------------------------
# Project registry semantics (shipd-workspace project-registry-semantics,
# project-resolution)
# ---------------------------------------------------------------------------


def repo_entry_path(entry):
    """Return the workspace-root-relative path of a ``repos`` entry, or ``None``
    when the entry is malformed (shipd-workspace project-registry-semantics).

    An entry is either a non-empty path string (today's form) or an object
    carrying a required non-empty string ``path`` (plus optional ``url`` /
    ``branch``). This is the single reader of the entry path, used by
    :func:`validate_workspace`, :func:`project_of`, and the show verbs so the
    two shapes never drift."""
    if isinstance(entry, str):
        return entry or None
    if isinstance(entry, dict):
        path = entry.get("path")
        if isinstance(path, str) and path:
            return path
    return None


def validate_workspace(registry):
    """Validate a workspace registry's ``projects`` map and optional ``focus``,
    returning a list of error strings (empty when valid). Shape-only, never
    existence-checked — registries travel across machines (shipd-workspace
    project-registry-semantics, workspace-focus).

    ``projects`` (when present) must be a JSON object mapping kebab-case project
    slugs to objects whose ``repos`` is a list of entries, each entry either a
    non-empty workspace-root-relative path string or an object carrying a
    required non-empty string ``path`` and optional non-empty string ``url`` and
    ``branch``. A duplicate resolved repo path across two projects, regardless of
    entry shape, is an ambiguous-ownership error naming the path. When present,
    ``focus`` must be a kebab-case slug naming a declared project (a same-file
    consistency check, never disk-consulted). Returns strings (not raising) so
    ``spec_lint.py`` can wrap them as ``LintError``s and the status CLI can print
    them — one implementation, two consumers."""
    errors = []
    projects = registry.get("projects")
    project_slugs = []
    if projects is None:
        projects_map = None
    elif not isinstance(projects, dict):
        errors.append("workspace registry `projects` must be a JSON object")
        projects_map = None
    else:
        projects_map = projects
    seen = {}  # repo path -> slug that first declared it
    if projects_map is not None:
        for slug, entry in projects_map.items():
            project_slugs.append(slug)
            if not KEBAB_RE.match(slug):
                errors.append(
                    "project slug '%s' is not a kebab-case slug" % slug)
            if not isinstance(entry, dict):
                errors.append(
                    "project '%s' must map to a JSON object" % slug)
                continue
            repos = entry.get("repos")
            if not isinstance(repos, list):
                errors.append(
                    "project '%s' `repos` must be a list of entries" % slug)
                continue
            for repo in repos:
                path = repo_entry_path(repo)
                if path is None:
                    errors.append(
                        "project '%s' has a repo entry that is not a non-empty "
                        "path string or an object with a non-empty `path`"
                        % slug)
                    continue
                if isinstance(repo, dict):
                    url = repo.get("url")
                    if url is not None and (not isinstance(url, str) or not url):
                        errors.append(
                            "project '%s' repo '%s' `url` must be a non-empty "
                            "string when present" % (slug, path))
                    branch = repo.get("branch")
                    if branch is not None and (
                            not isinstance(branch, str) or not branch):
                        errors.append(
                            "project '%s' repo '%s' `branch` must be a "
                            "non-empty string when present" % (slug, path))
                if path in seen:
                    errors.append(
                        "repo path '%s' is claimed by both projects '%s' and "
                        "'%s' (ambiguous ownership)" % (path, seen[path], slug))
                else:
                    seen[path] = slug
    focus = registry.get("focus")
    if focus is not None:
        declared = ", ".join(sorted(project_slugs)) or "(none)"
        if not isinstance(focus, str) or not KEBAB_RE.match(focus):
            errors.append(
                "workspace `focus` must be a kebab-case project slug, got %r "
                "(declared projects: %s)" % (focus, declared))
        elif focus not in project_slugs:
            errors.append(
                "workspace `focus` names unknown project '%s' (declared "
                "projects: %s)" % (focus, declared))
    return errors


def _ws_relative_parts(ws_root, path):
    """Normalize ``path`` to workspace-root-relative POSIX-style path
    components. Absolute paths are made relative to ``ws_root``; relative paths
    are taken as-is (already workspace-root-relative)."""
    rel = os.path.relpath(path, ws_root) if os.path.isabs(path) else path
    norm = os.path.normpath(rel).replace(os.sep, "/")
    return [p for p in norm.split("/") if p not in ("", ".")]


def project_of(ws_root, path):
    """Resolve which project owns ``path`` (shipd-workspace project-resolution).

    Loads the registry from ``ws_root``, normalizes ``path`` relative to it, and
    returns the slug of the project whose repo entry equals or contains the path,
    the longest (most specific) matching entry winning across projects. Ties
    (an exact duplicate path, which ``validate_workspace`` flags) break on
    first-declaration order, so display code never crashes on an invalid
    registry. Returns ``None`` when nothing matches — the anonymous implicit
    default project — or when the registry is unloadable or declares no
    projects."""
    try:
        registry = load_workspace(ws_root)
    except ConfigError:
        return None
    projects = registry.get("projects")
    if not isinstance(projects, dict):
        return None
    target = _ws_relative_parts(ws_root, path)
    best_slug = None
    best_len = -1
    for slug, entry in projects.items():
        if not isinstance(entry, dict):
            continue
        repos = entry.get("repos")
        if not isinstance(repos, list):
            continue
        for repo in repos:
            path = repo_entry_path(repo)
            if path is None:
                continue
            parts = _ws_relative_parts(ws_root, path)
            if parts and target[:len(parts)] == parts and len(parts) > best_len:
                best_len = len(parts)
                best_slug = slug
    return best_slug


# ---------------------------------------------------------------------------
# Workspace universe discovery (shipd-workspace workspace-universe-discovery)
# ---------------------------------------------------------------------------


def workspace_project_roots(root):
    """The declared workspace project repos a board-shaped read surface
    additionally aggregates, as ``(project_slug, repo_root)`` pairs
    (shipd-workspace workspace-universe-discovery).

    This is the single shared seam — bare ``show``'s workspace report, the
    dashboard's board aggregation, ``epic-show``, and ``locate`` all obtain
    their universes here, never through a private reimplementation, so they
    can never disagree about which epics exist or where they live.

    Aggregation is for **workspace-level invocations only**: the pairs are
    non-empty exactly when a project registry is discoverable from ``root``
    (:func:`registry_root`) *and* ``root`` lies inside no declared project repo
    (:func:`project_of` yields the implicit default, ``None``). Run from inside
    a member repo — or with no registry at all — this returns ``[]`` and every
    consumer stays the single-universe, per-repo surface it has always been.

    Pairs come out in projects' slug order, each project's repos in declaration
    order, every path resolved against the registry root.

    Fail-soft throughout — display never crashes on an invalid registry: an
    unloadable registry, a non-object project or repo entry, an entry whose
    path is not a directory on this machine, an entry duplicating an earlier
    one's real path, and an entry resolving to the invocation root itself are
    all skipped silently, never raised."""
    try:
        reg_root = registry_root(root)
        if reg_root is None or project_of(reg_root, root) is not None:
            return []
        registry = load_workspace(reg_root)
    except ConfigError:
        return []
    projects = registry.get("projects")
    if not isinstance(projects, dict):
        return []
    pairs = []
    seen = {os.path.realpath(root)}
    for slug in sorted(projects):
        entry = projects[slug]
        if not isinstance(entry, dict):
            continue
        repos = entry.get("repos")
        if not isinstance(repos, list):
            continue
        for repo in repos:
            path = repo_entry_path(repo)
            if path is None:
                continue
            repo_root = os.path.join(reg_root, path)
            if not os.path.isdir(repo_root):
                continue
            real = os.path.realpath(repo_root)
            if real in seen:
                continue
            seen.add(real)
            pairs.append((slug, repo_root))
    return pairs


def aggregation_universes(root):
    """Every universe a board-shaped read surface aggregates over, as
    ``(project_slug, universe_root)`` pairs in seam order (shipd-workspace
    workspace-universe-discovery): the invocation root's own universe first
    (``project`` ``None``), then each declared project repo
    :func:`workspace_project_roots` yields, in project slug order.

    A non-workspace-level invocation yields exactly ``[(None, root)]``, so a
    consumer written against this seam renders identically to its
    single-universe self."""
    return [(None, root)] + workspace_project_roots(root)


# ---------------------------------------------------------------------------
# Workspace materialization planning (shipd-workspace sync-materialization-planning,
# shipd-config clone-sources-key)
# ---------------------------------------------------------------------------

# The fixed cheapest-first materialization ladder for an absent member (epic
# portable-workspaces): a local work-tree candidate is cheapest, then a bare
# reference clone, then a full clone, and finally unmaterializable.
SYNC_ACTIONS = ("none", "worktree", "reference-clone", "clone", "unmaterializable")

# The config key naming the local directories probed for candidate clones.
CLONE_SOURCES_KEY = "clone_sources"


def resolve_clone_sources(config):
    """Return the ``clone_sources`` directories from a resolved ``config``
    (shipd-config clone-sources-key).

    The value is an optional list of non-empty directory path strings with ``~``
    expansion. An undeclared key resolves to an empty list — the planner never
    falls back to implicit discovery. A value that is not a list of non-empty
    strings raises :class:`ConfigError` naming the key, so the consuming verb can
    exit non-zero."""
    raw = config.get(CLONE_SOURCES_KEY)
    if raw is None:
        return []
    if not isinstance(raw, list) or not all(
            isinstance(item, str) and item for item in raw):
        raise ConfigError(
            "config `%s` must be a list of non-empty directory path strings, "
            "got %r" % (CLONE_SOURCES_KEY, raw))
    return [os.path.expanduser(item) for item in raw]


def _git_probe(target, *args):
    """Run ``git -C <target> <args>`` locally and return stripped stdout on a
    zero exit, else ``None``. Never the network — the caller passes only
    read-only local probes (``rev-parse``, ``remote get-url``). A missing git
    binary or a non-repository target reads as ``None``."""
    try:
        result = subprocess.run(
            ["git", "-C", target, *args], capture_output=True, text=True)
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _git_origin_url(target):
    """Return ``target``'s ``origin`` remote URL via a local probe, or ``None``
    when unset or unreadable."""
    return _git_probe(target, "remote", "get-url", "origin")


def _classify_git_repo(path):
    """Classify ``path`` as a git repository root for candidate/destination
    probing (shipd-workspace sync-materialization-planning).

    Returns ``(kind, origin)`` — ``kind`` is ``"bare"`` or ``"worktree"`` and
    ``origin`` the origin URL (or ``None``) — when ``path`` is a git repository
    root, else ``None``. A cheap filesystem prefilter (a ``.git`` entry for a
    work tree, ``HEAD`` + ``objects`` for a bare repo) keeps a plain directory
    sitting inside a parent work tree from reading as a repository, and bounds
    the probe to at most two local git calls. Never the network."""
    if not os.path.isdir(path):
        return None
    looks_worktree = os.path.exists(os.path.join(path, ".git"))
    looks_bare = (os.path.isfile(os.path.join(path, "HEAD"))
                  and os.path.isdir(os.path.join(path, "objects")))
    if not (looks_worktree or looks_bare):
        return None
    is_bare = _git_probe(path, "rev-parse", "--is-bare-repository")  # call 1
    if is_bare is None:
        return None
    kind = "bare" if is_bare == "true" else "worktree"
    origin = _git_origin_url(path)  # call 2
    return kind, origin


def _find_clone_candidate(source_dirs, url):
    """Find the first local candidate clone for ``url`` among the immediate
    children of ``source_dirs`` (first match in list order; children scanned in
    sorted order for determinism). Returns ``(src_path, kind)`` or ``None``.
    Only probes when ``url`` is set — a candidate is matched by origin URL."""
    if not url:
        return None
    for source in source_dirs:
        if not os.path.isdir(source):
            continue
        for child in sorted(os.listdir(source)):
            cand = os.path.join(source, child)
            classified = _classify_git_repo(cand)
            if classified is None:
                continue
            _kind, origin = classified
            if origin == url:
                return cand, classified[0]
    return None


def _plan_member(ws_root, slug, path, url, branch, source_dirs):
    """Compute one member's materialization record (shipd-workspace
    sync-materialization-planning). Pure but for local git probes of the
    destination and the candidate source directories — never the network."""
    dest = os.path.join(ws_root, path)
    record = {"kind": "member", "member": slug, "path": path}
    if url:
        record["url"] = url
    if branch:
        record["branch"] = branch

    if os.path.exists(dest):
        classified = _classify_git_repo(dest)
        if classified is not None:
            _kind, origin = classified
            record["state"] = "present"
            record["action"] = "none"
            if url and origin != url:
                if origin:
                    record["drift"] = (
                        "origin %s differs from manifest url %s" % (origin, url))
                else:
                    record["drift"] = (
                        "no origin remote is set; manifest declares url %s" % url)
        else:
            record["state"] = "occupied"
            record["action"] = "none"
            record["drift"] = (
                "%s exists but is not a git work tree; left unmodified" % path)
        return record

    # Absent destination: descend the cheapest-first ladder.
    record["state"] = "absent"
    candidate = _find_clone_candidate(source_dirs, url)
    branch_opt = " --branch %s" % branch if branch else ""
    if candidate is not None:
        src, kind = candidate
        record["source"] = src
        if kind == "bare":
            record["action"] = "reference-clone"
            record["command"] = (
                "git clone --reference %s%s %s %s"
                % (src, branch_opt, url, dest))
        else:
            record["action"] = "worktree"
            start = " %s" % branch if branch else ""
            record["command"] = (
                "git -C %s worktree add %s -b job/%s%s"
                % (src, dest, os.path.basename(os.path.abspath(ws_root)), start))
    elif url:
        record["action"] = "clone"
        record["command"] = "git clone%s %s %s" % (branch_opt, url, dest)
    else:
        record["action"] = "unmaterializable"
        record["reason"] = (
            "member '%s' declares no url and no local candidate was found; "
            "cannot materialize" % path)
    return record


def read_members_gitignore_block(ws_root):
    """Return the non-empty stripped lines inside the marked member-repos block
    of ``<ws_root>/.gitignore``, or ``[]`` when the file or the markers are
    absent (shipd-workspace sync-materialization-planning)."""
    gi_path = os.path.join(ws_root, ".gitignore")
    if not os.path.isfile(gi_path):
        return []
    with open(gi_path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    try:
        begin = lines.index(GITIGNORE_MEMBERS_BEGIN)
        end = lines.index(GITIGNORE_MEMBERS_END)
    except ValueError:
        return []
    return [ln.strip() for ln in lines[begin + 1:end] if ln.strip()]


def write_members_gitignore_block(ws_root, member_paths):
    """Rewrite only the marked member-repos block of ``<ws_root>/.gitignore`` to
    list ``member_paths`` (sorted, de-duplicated), idempotently, leaving every
    byte outside the markers untouched (shipd-workspace sync-materialization-
    planning). Seeds an empty marked block first when absent, reusing the init
    verb's block writer, so the markers always exist to rewrite between."""
    _ensure_members_gitignore_block(ws_root)
    gi_path = os.path.join(ws_root, ".gitignore")
    with open(gi_path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    begin = lines.index(GITIGNORE_MEMBERS_BEGIN)
    end = lines.index(GITIGNORE_MEMBERS_END)
    want = sorted(set(member_paths))
    new_lines = lines[:begin + 1] + want + lines[end:]
    with open(gi_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(new_lines))


def _plan_gitignore(ws_root, member_paths):
    """Compare the marked member-repos gitignore block against the manifest's
    member paths, recording the missing and stale lines (shipd-workspace
    sync-materialization-planning)."""
    have = read_members_gitignore_block(ws_root)
    want = sorted(set(member_paths))
    have_set = set(have)
    want_set = set(want)
    missing = [p for p in want if p not in have_set]
    stale = [ln for ln in have if ln not in want_set]
    return {"kind": "gitignore", "missing": missing, "stale": stale}


def plan_workspace_sync(ws_root, config):
    """Compute the deterministic per-member materialization plan for a workspace
    (shipd-workspace sync-materialization-planning).

    A pure function of the manifest (the workspace registry loaded from
    ``ws_root``), the resolved ``config``, and local disk state, using only local
    git probes and never the network. Returns one ``member`` record per manifest
    repo entry (in registry order) followed by a single ``gitignore`` record.
    Each member record carries ``kind``/``member``/``path``/``state``/``action``
    plus ``source``/``url``/``branch``/``command``/``drift``/``reason`` as
    applicable; the ``gitignore`` record carries ``missing`` and ``stale`` line
    lists. Raises :class:`ConfigError` (naming the key) when ``clone_sources`` is
    malformed."""
    registry = load_workspace(ws_root)
    source_dirs = resolve_clone_sources(config)
    records = []
    member_paths = []
    projects = registry.get("projects")
    if isinstance(projects, dict):
        for slug, entry in projects.items():
            if not isinstance(entry, dict):
                continue
            repos = entry.get("repos")
            if not isinstance(repos, list):
                continue
            for repo in repos:
                path = repo_entry_path(repo)
                if path is None:
                    continue
                url = repo.get("url") if isinstance(repo, dict) else None
                branch = repo.get("branch") if isinstance(repo, dict) else None
                member_paths.append(path)
                records.append(_plan_member(
                    ws_root, slug, path, url, branch, source_dirs))
    records.append(_plan_gitignore(ws_root, member_paths))
    return records


def parse_plan_metadata(text):
    """Parse a ``plan.md``'s optional header metadata block.

    The block is the contiguous run of ``<Key>: <value>`` lines immediately
    following the ``Status:`` line, ended by the first blank line or heading.
    Returns the ordered list of ``(key, value)`` pairs exactly as they appear —
    including unrecognized keys, so callers (the linter) can report them. Returns
    an empty list when the plan has no ``Status:`` line or no metadata block
    follows it."""
    lines = text.splitlines()
    status_idx = None
    for i, line in enumerate(lines):
        if PLAN_STATUS_LINE_RE.match(line):
            status_idx = i
            break
    if status_idx is None:
        return []
    pairs = []
    for line in lines[status_idx + 1:]:
        if line.strip() == "" or line.lstrip().startswith("#"):
            break
        m = METADATA_LINE_RE.match(line)
        if not m:
            break
        pairs.append((m.group(1), m.group(2)))
    return pairs


# ---------------------------------------------------------------------------
# Epic ``## Changes`` stub table (shipd-spec-format epic-artifact-layout)
# ---------------------------------------------------------------------------


def _split_table_row(line):
    """Split a markdown table row into trimmed cell strings, dropping the
    leading/trailing pipe delimiters. ``| a | b |`` -> ``['a', 'b']``."""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [cell.strip() for cell in s.split("|")]


def _is_separator_row(cells):
    """True when every cell is a markdown table separator (``---``, ``:-:``)."""
    return bool(cells) and all(
        TABLE_SEPARATOR_CELL_RE.match(c) for c in cells)


def parse_epic_changes(text):
    """Parse an epic's ``## Changes`` stub table.

    Returns ``(header, rows)`` where ``header`` is the list of trimmed header
    cell strings (or ``None`` when the ``## Changes`` section is absent or holds
    no table), and ``rows`` is a list of ``(slug, description, ratings)`` tuples
    — one per data row — with ``ratings`` the tuple of trailing rating cells
    (Code, Integration, Unknowns, Risk) in column order. A markdown separator
    row (``| --- | --- | ...``) immediately under the header is skipped.

    Only structural splitting happens here: validating the header columns, the
    rating values, and the slug shape/uniqueness is the linter's job."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        m = SECTION_HEADER_RE.match(line)
        if m and m.group(1).strip() == "Changes":
            start = i + 1
            break
    if start is None:
        return None, []
    section = []
    for line in lines[start:]:
        if SECTION_HEADER_RE.match(line):
            break
        section.append(line)

    table_rows = [ln for ln in section if ln.strip().startswith("|")]
    if not table_rows:
        return None, []
    header = _split_table_row(table_rows[0])
    data = table_rows[1:]
    if data and _is_separator_row(_split_table_row(data[0])):
        data = data[1:]
    rows = []
    for ln in data:
        cells = _split_table_row(ln)
        slug = cells[0] if len(cells) > 0 else ""
        description = cells[1] if len(cells) > 1 else ""
        ratings = tuple(cells[2:])
        rows.append((slug, description, ratings))
    return header, rows


# ---------------------------------------------------------------------------
# Content hashing (design D3)
# ---------------------------------------------------------------------------


def normalize_content(text):
    """Normalize a requirement's content region for hashing: strip trailing
    whitespace from every line, collapse runs of blank lines to a single blank
    line, and strip leading/trailing blank lines. The ``id:`` and ``base:``
    metadata lines are already excluded because hashing operates on the content
    region (body + scenarios), never the metadata block."""
    lines = [ln.rstrip() for ln in text.splitlines()]
    out = []
    prev_blank = False
    for ln in lines:
        blank = ln == ""
        if blank and prev_blank:
            continue
        out.append(ln)
        prev_blank = blank
    # Strip leading/trailing blank lines.
    while out and out[0] == "":
        out.pop(0)
    while out and out[-1] == "":
        out.pop()
    return "\n".join(out)


def content_hash(requirement):
    """Return the truncated sha256 hex content hash of a requirement.

    ``requirement`` may be a :class:`Requirement` (its ``content`` region is
    hashed) or a raw content string. The hash is deterministic across machines:
    identical normalized content yields an identical hash, so cosmetic
    whitespace differences do not change it, and a rename (re-keyed ``id``) does
    not change it because ``id``/``base`` metadata is excluded (design D3)."""
    if isinstance(requirement, Requirement):
        text = requirement.content
    else:
        text = requirement
    normalized = normalize_content(text)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return digest[:HASH_LENGTH]


# ---------------------------------------------------------------------------
# Serialization / write-back (design D5)
# ---------------------------------------------------------------------------


def render_requirement(req):
    """Render a Requirement as a canonical master-library block:

        ### Requirement: <title>
        id: <slug>

        <content>

    Delta-only metadata (``base:``, ``Reason:``, ``Migration:``) is dropped,
    because the master library never carries it. ``content`` (body + scenarios)
    is emitted verbatim as parsed."""
    lines = ["### Requirement: %s" % req.title]
    if req.id is not None:
        lines.append("id: %s" % req.id)
    header = "\n".join(lines)
    content = req.content.strip("\n")
    if content:
        return header + "\n\n" + content
    return header


def render_spec(spec):
    """Render a SpecFile back to file text, preserving requirement order. The
    caller (the merge engine) is responsible for having ordered
    ``spec.requirements`` per design D5 (existing master order preserved, newly
    ADDED requirements appended in delta order)."""
    parts = []
    preamble = spec.preamble.strip("\n")
    if preamble:
        parts.append(preamble)
    for req in spec.requirements:
        parts.append(render_requirement(req))
    return "\n\n".join(parts) + "\n" if parts else ""


def write_spec(path, spec):
    """Write a SpecFile to ``path`` (creating parent directories if needed)."""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(render_spec(spec))


def _parse_renames(lines):
    """Parse RENAMED bullet pairs: ``- FROM: old`` followed by ``  TO: new``."""
    renames = []
    pending = None  # (from_id, [raw_lines])
    for line in lines:
        fm = RENAME_FROM_RE.match(line)
        if fm:
            if pending is not None:
                renames.append(Rename(from_id=pending[0], to_id=None,
                                      raw="\n".join(pending[1])))
            pending = (fm.group(1) or None, [line])
            continue
        tm = RENAME_TO_RE.match(line)
        if tm and pending is not None:
            pending[1].append(line)
            renames.append(Rename(from_id=pending[0], to_id=tm.group(1) or None,
                                  raw="\n".join(pending[1])))
            pending = None
            continue
        if pending is not None and line.strip():
            pending[1].append(line)
    if pending is not None:
        renames.append(Rename(from_id=pending[0], to_id=None,
                              raw="\n".join(pending[1])))
    return renames
