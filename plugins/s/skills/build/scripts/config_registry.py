#!/usr/bin/env python3
"""The ``.shipd-config.json`` key registry and the one validating writer
(shipd-config config-key-registry, config-layer-writer).

Every top-level key the engine recognizes has one :class:`KeySpec` row in
:data:`REGISTRY` — a validator, a one-line hint, a default layer, and an optional
owning verb. :func:`write_layer` is the single function through which an engine
write of a config file goes: it validates the change and the merged result, and
writes atomically or not at all. :func:`set_key`, :func:`unset_key`,
:func:`layer_path`, and :func:`check` serve the ``config-set``, ``config-unset``,
and ``config-check`` verbs of ``spec_status.py``.

Stdlib-only. Imports :mod:`spec_common`; ``spec_common.init_workspace`` imports
this module lazily."""

import collections
import difflib
import json
import os
import re
import stat
import subprocess
import tempfile

import spec_common as sc

# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------

Finding = collections.namedtuple(
    "Finding", ("level", "path", "key", "message", "hint"))
Finding.__doc__ = (
    "One problem with a config value: ``level`` is ``error`` or ``warning``, "
    "``path`` the file it lives in (or ``None``), ``key`` the top-level key "
    "(or ``None``), ``message`` the text, ``hint`` a one-line remedy or "
    "``None``.")


class ConfigWriteError(sc.ConfigError):
    """A refused write: carries one error :class:`Finding` per problem in
    ``.findings``."""

    def __init__(self, findings):
        self.findings = list(findings)
        super().__init__("; ".join(f.message for f in self.findings))


def refusal_lines(exc):
    """The stderr lines for a refused write: ``error: <message>`` per finding,
    each followed by ``hint: <hint>`` where it has one."""
    lines = []
    for finding in exc.findings:
        lines.append("error: %s" % finding.message)
        if finding.hint:
            lines.append("hint: %s" % finding.hint)
    return lines


# ---------------------------------------------------------------------------
# Statusline layout (moved from bin/shipd)
# ---------------------------------------------------------------------------

STATUSLINE_SEGMENTS = ("spec", "directory", "context")


def validate_layout(lines):
    """Return ``lines`` normalised, or raise ``ValueError`` naming the
    problem: each line a non-empty list of known, non-repeating segments."""
    if not isinstance(lines, list) or not lines:
        raise ValueError("a layout needs at least one line")
    seen = set()
    out = []
    for line in lines:
        if not isinstance(line, list) or not line:
            raise ValueError("a layout line needs at least one segment")
        for seg in line:
            if seg not in STATUSLINE_SEGMENTS:
                raise ValueError("unknown segment %r (known: %s)"
                                 % (seg, ", ".join(STATUSLINE_SEGMENTS)))
            if seg in seen:
                raise ValueError("segment %r appears more than once" % seg)
            seen.add(seg)
        out.append(list(line))
    return out


def statusline_from_config(entry, path):
    """The validated layout lines of a declared ``statusline`` ``entry`` found
    in ``path``; raises :class:`spec_common.ConfigError` naming the file and
    the reason otherwise."""
    try:
        if not isinstance(entry, dict):
            raise ValueError("it is not an object")
        return validate_layout(entry.get("lines"))
    except ValueError as exc:
        raise sc.ConfigError(
            "malformed `statusline` key in %s: %s" % (path, exc))


# ---------------------------------------------------------------------------
# Validators: each takes ``(value, path)`` and raises ConfigError when bad
# ---------------------------------------------------------------------------

def _bad(key, path, expected, value):
    raise sc.ConfigError(
        "config `%s` must be %s (from %s), got %r"
        % (key, expected, path, value))


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _string_list(value):
    return isinstance(value, list) and all(
        isinstance(item, str) and item.strip() for item in value)


def _via_core(core, key):
    def validate(value, path):
        core({key: value}, {key: path})
    return validate


def _via_config(accessor, key):
    def validate(value, path):
        accessor({key: value})
    return validate


def _path_value(key, nullable):
    def validate(value, path):
        if nullable and value is None:
            return
        sc.absolute_path_value(key, value)
    return validate


def _boolean(key):
    def validate(value, path):
        if not isinstance(value, bool):
            _bad(key, path, "true or false", value)
    return validate


def _non_empty_string(key):
    def validate(value, path):
        if not isinstance(value, str) or not value.strip():
            _bad(key, path, "a non-empty string", value)
    return validate


def _string_list_of(key, noun):
    def validate(value, path):
        if not _string_list(value):
            _bad(key, path, "a list of non-empty %s" % noun, value)
    return validate


def _object(key):
    def validate(value, path):
        if not isinstance(value, dict):
            _bad(key, path, "a JSON object", value)
    return validate


def _validate_retention(value, path):
    if value is None:
        return
    if not _is_int(value) or value < 0:
        _bad("completed_retention_days", path,
             "a non-negative integer or null", value)


def _validate_idle(value, path):
    if not _is_int(value) or value < 0:
        _bad("worktree_idle_minutes", path, "a non-negative integer", value)


def _validate_stale(value, path):
    if not _is_int(value) or value < 1:
        _bad("worktree_stale_days", path, "a positive integer", value)


def _validate_guardrails(value, path):
    if value is False:
        return
    if not isinstance(value, dict):
        _bad("guardrails", path, "false or an object", value)
    if "disable" in value and not _string_list(value["disable"]):
        _bad("guardrails.disable", path, "a list of non-empty strings",
             value["disable"])


def _validate_lint(value, path):
    if not isinstance(value, dict):
        _bad("lint", path, "an object", value)
    if "run_scripts" in value and not isinstance(value["run_scripts"], bool):
        _bad("lint.run_scripts", path, "true or false", value["run_scripts"])
    if "disable" in value and not _string_list(value["disable"]):
        _bad("lint.disable", path, "a list of non-empty strings",
             value["disable"])


def _validate_hooks(value, path):
    key = "post-worktree-scripts"
    if not isinstance(value, list):
        _bad(key, path, "a JSON list of shell command lines", value)
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise sc.ConfigError(
                "config `%s` items must be non-empty strings (from %s), "
                "got %r" % (key, path, item))


def _validate_statusline(value, path):
    statusline_from_config(value, path)


def _validate_workspace(value, path):
    if not isinstance(value, dict):
        _bad("workspace", path, "a JSON object", value)
    errors = sc.validate_workspace(value)
    if errors:
        raise sc.ConfigError(
            "config `workspace` is invalid (from %s): %s"
            % (path, "; ".join(errors)))


# ---------------------------------------------------------------------------
# The registry (artefacts/registry.md of the config-control change)
# ---------------------------------------------------------------------------

KeySpec = collections.namedtuple(
    "KeySpec", ("key", "validate", "hint", "layer", "owner"))
KeySpec.__doc__ = (
    "One registry row: the key, its ``validate(value, path)`` callable, the "
    "one-line ``hint``, the default ``layer`` (``repo``, ``workspace`` or "
    "``user``), and the ``owner`` verb that alone writes it (or ``None``).")


def _row(key, validate, hint, layer, owner=None):
    return KeySpec(key, validate, hint, layer, owner)


REGISTRY = {spec.key: spec for spec in (
    _row("autonomous-pipeline",
         _via_core(sc.pipeline_from_config, "autonomous-pipeline"),
         "a preset name (basic, default, eco) or a list of stage entries",
         "repo"),
    _row("build", _object("build"),
         'an object of /s:build settings, e.g. {"parallelism": 3}', "repo"),
    _row("clone_sources", _via_config(sc.resolve_clone_sources,
                                      "clone_sources"),
         "a list of directory paths", "workspace"),
    _row("completed_retention_days", _validate_retention,
         "a non-negative number of days; 0 or null disables retention",
         "repo"),
    _row("dir", _via_config(sc.specs_dirname, "dir"),
         "a relative path such as .shipd", "repo"),
    _row("guardrails", _validate_guardrails,
         'false, or an object such as {"disable": ["<rule>"]}', "repo"),
    _row("lint", _validate_lint,
         "an object with run_scripts (true or false) and disable (a list of "
         "linter names)", "repo"),
    _row("memory_dir", _path_value("memory_dir", False),
         "an absolute path such as ~/.shipd-memory", "user"),
    _row("merge", _via_core(sc.merge_from_config, "merge"),
         "an object with approvals, dismiss_stale, last_push_approval, "
         "required_checks, strict, thread_resolution", "repo"),
    _row("model", _via_config(sc.resolve_model_base, "model"),
         "a non-empty model id", "user"),
    _row("models", _via_config(sc.resolve_models, "models"),
         "an object mapping effort levels to model ids", "user"),
    _row("post-worktree-scripts", _validate_hooks,
         "a list of shell command lines", "repo",
         "shipd worktree hooks add"),
    _row("pr", _via_core(sc.pr_from_config, "pr"),
         "an object with title (containing {summary}) and ticket_pattern "
         "(a regular expression)", "repo"),
    _row("pr-mode", _via_core(sc.pr_mode_from_config, "pr-mode"),
         "accepted values: auto, draft", "repo"),
    _row("room", _via_core(sc.room_from_config, "room"),
         "an object with agent (a non-empty string) and max_rounds (an "
         "integer of at least 1)", "user"),
    _row("statusline", _validate_statusline,
         'an object such as {"lines": [["spec", "context"]]}; segments: '
         'spec, directory, context', "user", "shipd statusline layout"),
    _row("store_autocommit", _boolean("store_autocommit"), "true or false",
         "repo"),
    _row("store_root", _non_empty_string("store_root"),
         "a path to the external store root", "repo"),
    _row("store_sync", _boolean("store_sync"), "true or false", "repo"),
    _row("valid_themes", _string_list_of("valid_themes", "strings"),
         "a list of theme slugs", "repo"),
    _row("voice", _boolean("voice"), "true or false", "user"),
    _row("wiki_base", _path_value("wiki_base", True),
         "an absolute path to the base wiki store", "user"),
    _row("workspace", _validate_workspace,
         "an object declaring the workspace registry", "workspace",
         "shipd workspace init"),
    _row("workspaces_root", _path_value("workspaces_root", True),
         "an absolute path such as ~/projects", "user"),
    _row("worktree_idle_minutes", _validate_idle,
         "a non-negative number of minutes; 0 disables the guard", "repo"),
    _row("worktree_stale_days", _validate_stale,
         "a positive number of days", "repo"),
    _row("worktree_sweep", _boolean("worktree_sweep"), "true or false",
         "repo"),
)}


def is_comment_key(key):
    """Whether ``key`` is a ``//`` comment, never validated."""
    return isinstance(key, str) and key.startswith("//")


def unknown_key_hint(key):
    """The hint for a key outside the registry: the close registry key, else
    a pointer to the report."""
    close = difflib.get_close_matches(key, list(REGISTRY), n=1, cutoff=0.6)
    if close:
        return "did you mean %s?" % close[0]
    return "run shipd config to see the keys in effect"


def validate_value(key, value, path):
    """Validate one declared ``key`` = ``value`` found in ``path``; returns a
    list of error :class:`Finding`\\ s (empty when valid). A key outside the
    registry yields one finding with the did-you-mean hint."""
    spec = REGISTRY.get(key)
    if spec is None:
        return [Finding("error", path, key, "unknown key %s" % key,
                        unknown_key_hint(key))]
    try:
        spec.validate(value, path)
    except sc.ConfigError as exc:
        return [Finding("error", path, key, str(exc), spec.hint)]
    return []


# ---------------------------------------------------------------------------
# The writer
# ---------------------------------------------------------------------------

def _same(a, b):
    """JSON-level equality (so ``1`` and ``true`` differ)."""
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def _unchanged_hint(key):
    return ("fix it with shipd config set %s <value> or shipd config unset %s"
            % (key, key))


def write_layer(path, data, anchor=None):
    """Write ``data`` as the config file at ``path`` if, and only if, it keeps
    the merged configuration valid (shipd-config config-layer-writer).

    Validates each key whose value differs from the file's current content on
    its own, then every registered key of the merged configuration resolved
    from ``anchor`` (default: ``path``'s directory) with ``data`` in place of
    the file. Any failure raises :class:`ConfigWriteError` and writes nothing.
    Otherwise writes atomically (temp file in the same directory renamed over
    the target) as 2-space JSON with a trailing newline, keeping an existing
    file's mode, and returns the warning findings for unchanged keys outside
    the registry."""
    path = os.path.abspath(path)
    anchor = os.path.abspath(anchor) if anchor else os.path.dirname(path)
    current = sc._load_config_file(path) if os.path.isfile(path) else {}
    changed = {key for key in data
               if key not in current or not _same(current[key], data[key])}
    errors = []
    seen = set()

    def add(finding):
        marker = (finding.key, finding.message)
        if marker not in seen:
            seen.add(marker)
            errors.append(finding)

    for key, value in data.items():
        if is_comment_key(key) or key not in changed:
            continue
        for finding in validate_value(key, value, path):
            add(finding)
    config, prov = sc.resolve_config(anchor, override=(path, data))
    for key, value in config.items():
        source = prov.get(key)
        if is_comment_key(key) or key not in REGISTRY \
                or source in (None, "default"):
            continue
        if source == path and key in changed:
            continue
        for finding in validate_value(key, value, source):
            add(finding._replace(hint=_unchanged_hint(key)))
    # The file's own other registered keys count too: a file outside the
    # discovered layers (an explicit --config path) is not in the merged view.
    for key, value in data.items():
        if is_comment_key(key) or key not in REGISTRY or key in changed:
            continue
        for finding in validate_value(key, value, path):
            add(finding._replace(hint=_unchanged_hint(key)))
    if errors:
        raise ConfigWriteError(errors)
    warnings = [
        Finding("warning", path, key, "unknown key %s" % key,
                unknown_key_hint(key))
        for key in data
        if not is_comment_key(key) and key not in REGISTRY]
    _atomic_write(path, data)
    return warnings


def _atomic_write(path, data):
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    try:
        mode = stat.S_IMODE(os.stat(path).st_mode)
    except OSError:
        umask = os.umask(0)
        os.umask(umask)
        mode = 0o666 & ~umask
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".shipd-config-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
            fh.write("\n")
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    except OSError:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


# ---------------------------------------------------------------------------
# Layer resolution and the set / unset helpers
# ---------------------------------------------------------------------------

LAYERS = ("repo", "workspace", "user")


def _repo_root(root):
    result = subprocess.run(
        ["git", "-C", root, "rev-parse", "--show-toplevel"],
        capture_output=True, text=True)
    top = result.stdout.strip()
    if result.returncode == 0 and top:
        return top
    return os.path.abspath(root)


def layer_path(root, key, layer=None):
    """The config file ``key`` is written to from ``root``: ``layer``'s file
    when given, else the file of the layer whose declaration of the key wins,
    else the key's default layer. ``repo`` is the git top level of ``root``
    (``root`` itself outside git), ``workspace`` the nearest discoverable
    workspace root, ``user`` ``~/.shipd-config.json``."""
    root = os.path.realpath(root)
    if layer is None:
        _config, prov = sc.resolve_config(root)
        source = prov.get(key)
        if source and source != "default":
            return source
        spec = REGISTRY.get(key)
        layer = spec.layer if spec else "repo"
    if layer == "workspace":
        ws_root = sc.find_workspace_root(root)
        if ws_root is None:
            raise sc.ConfigError(
                "no workspace is discoverable from %s; point --root at one"
                % root)
        return os.path.join(ws_root, sc.CONFIG_FILENAME)
    if layer == "user":
        return os.path.join(os.path.expanduser("~"), sc.CONFIG_FILENAME)
    return os.path.join(_repo_root(root), sc.CONFIG_FILENAME)


def _refuse_owner(key):
    spec = REGISTRY.get(key)
    if spec is not None and spec.owner:
        raise ConfigWriteError([Finding(
            "error", None, key, "config `%s` is written by another verb" % key,
            "use %s" % spec.owner)])


def set_key(root, key, value, layer=None):
    """Set ``key`` to ``value`` in its layer's file through
    :func:`write_layer`. Returns ``(path, warnings)``."""
    _refuse_owner(key)
    root = os.path.realpath(root)
    path = layer_path(root, key, layer)
    current = sc._load_config_file(path) if os.path.isfile(path) else {}
    data = dict(current)
    data[key] = value
    return path, write_layer(path, data, root)


def unset_key(root, key, layer=None):
    """Remove ``key`` from its layer's file through :func:`write_layer`.
    Returns ``(path, removed, warnings)``; ``removed`` is false, and nothing
    is written, when the file does not declare the key."""
    _refuse_owner(key)
    root = os.path.realpath(root)
    path = layer_path(root, key, layer)
    current = sc._load_config_file(path) if os.path.isfile(path) else {}
    if key not in current:
        return path, False, []
    data = {k: v for k, v in current.items() if k != key}
    return path, True, write_layer(path, data, root)


# ---------------------------------------------------------------------------
# The layered check
# ---------------------------------------------------------------------------

def check(root):
    """Validate every declared key of every layer ``root`` resolves, nearest
    first (spec-status config-check-verb). Returns ``(errors, warnings)``
    finding lists: an invalid value of a registered key is an error, a key
    outside the registry a warning with the did-you-mean hint, and a layer
    file that cannot be loaded one error naming it. ``//`` keys are
    skipped."""
    errors = []
    warnings = []
    try:
        layers = sc.load_layered_config(root)
    except sc.ConfigError as exc:
        return [Finding("error", None, None, str(exc), None)], []
    for path, data in layers:
        for key, value in data.items():
            if is_comment_key(key):
                continue
            if key not in REGISTRY:
                warnings.append(Finding(
                    "warning", path, key, "unknown key %s" % key,
                    unknown_key_hint(key)))
                continue
            errors.extend(validate_value(key, value, path))
    return errors, warnings
