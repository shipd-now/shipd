#!/usr/bin/env python3
"""pipeline_schema.py — stdlib-only table-driven validator for
`autonomous-pipeline` entries (shipd-config pipeline-entry-validation,
pipeline-presets).

The engine is stdlib-only Python 3 with one scoped third-party exception —
`textual`, used by `dashboard.py`'s `tui` verb — and this module carries none
of it: `spec_common.resolve_pipeline` imports it **lazily**, and only when a
config layer actually declares the ``autonomous-pipeline`` key, so the
no-key default pipeline — and every other engine script — never pays for the
import.

The grammar it enforces is the closed one documented in the shipd-config spec:
an entry is either a stage entry (``{"stage": <registry name>}``, optionally
with ``skip``, ``tools``, ``replace``, and the typed per-stage options) or a
custom step (``{"custom": <kebab slug>, "command": ...}``). Each entry form is
declared as a **key table** — key name to whether it is required and how its
value is checked — and one generic walker checks a raw entry's keys against
its form's table: an unknown key is always an error, and every value is
checked without coercion (``bool`` is tested before ``int``, since in Python
``True`` is an ``int``, so ``{"skip": 1}`` and ``{"parallelism": true}`` both
fail). Defaults are declared in this module's docstrings and the shipped
presets, but never injected into a resolved entry: :func:`validate_entries`
copies each valid entry as written, so it carries exactly the keys its author
declared.

Every rejection is rendered ``entry <i> (<compact-sorted-json>): <path>:
<message>``, one line per offending field, across every offending entry (not
only the first).
"""

import copy
import json

from spec_common import KEBAB_RE, PIPELINE_FALLBACKS, PIPELINE_STAGES

# The symbolic model tiers a `model` / `subagent_model` option may name,
# resolved relative to the driving session by the pipeline's consumers. Any
# other non-empty string is a concrete model id — the set of ids is open, so a
# new model never needs a schema release.
SYMBOLIC_TIERS = ("session", "tier-below", "tier-two-below")

# The closed set a `review` entry's `disposition` option may take.
_DISPOSITIONS = ("all", "high-only", "none")

# The stage keys every stage entry shares, plus each stage's own typed
# options — the "shared key table" this module's docstring describes. Keyed
# by exactly the six registry stages in `spec_common.PIPELINE_STAGES`.
_SHARED_STAGE_KEYS = frozenset({"skip", "tools", "replace", "model",
                                "autopilot"})
_BUILD_EXTRA_KEYS = frozenset({"subagent_model", "validator", "telemetry",
                               "parallelism"})
_REVIEW_EXTRA_KEYS = frozenset({"disposition"})

_STAGE_FORM_KEYS = {name: _SHARED_STAGE_KEYS for name in PIPELINE_STAGES}
_STAGE_FORM_KEYS["build"] = _SHARED_STAGE_KEYS | _BUILD_EXTRA_KEYS
_STAGE_FORM_KEYS["review"] = _SHARED_STAGE_KEYS | _REVIEW_EXTRA_KEYS

# A custom step's own key table.
_CUSTOM_KEYS = frozenset({"custom", "command", "autopilot"})


class AutopilotOpts:
    """The `autopilot`-namespaced driver knobs any entry may carry, and their
    schema-declared defaults — documentation only: a resolved entry never
    carries a key its author did not write (see :func:`validate_entries`)."""

    def __init__(self, attempts=3, timeout=None, max_resumes=None):
        self.attempts = attempts
        self.timeout = timeout
        self.max_resumes = max_resumes


# ---------------------------------------------------------------------------
# Leaf-value checks — no coercion; `bool` is checked before `int` since
# `True`/`False` are `int` instances in Python.
# ---------------------------------------------------------------------------


def _is_bool(value):
    return isinstance(value, bool)


def _is_nonempty_str(value):
    return isinstance(value, str) and len(value) > 0


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _is_int_ge(value, minimum):
    return _is_int(value) and value >= minimum


def _is_int_gt(value, minimum):
    return _is_int(value) and value > minimum


# ---------------------------------------------------------------------------
# Nested sub-objects: `tools` items, `replace`, `autopilot`.
# ---------------------------------------------------------------------------


def _validate_tools(value, path, errors):
    if not isinstance(value, list) or len(value) < 1:
        errors.append((path, "`tools` must be a non-empty list"))
        return
    for index, item in enumerate(value):
        item_path = "%s.%d" % (path, index)
        if not isinstance(item, dict):
            errors.append((item_path, "a `tools` entry must be an object"))
            continue
        for key in sorted(set(item) - {"name", "fallback"}):
            errors.append(("%s.%s" % (item_path, key),
                           "unknown key `%s`" % key))
        if "name" not in item:
            errors.append((item_path, "`name` is required"))
        elif not _is_nonempty_str(item["name"]):
            errors.append(("%s.name" % item_path,
                           "`name` must be a non-empty string"))
        if "fallback" not in item:
            errors.append((item_path, "`fallback` is required"))
        elif item["fallback"] not in PIPELINE_FALLBACKS:
            errors.append(("%s.fallback" % item_path,
                           "`fallback` must be one of %s, got %r"
                           % (", ".join(PIPELINE_FALLBACKS),
                              item["fallback"])))


def _validate_replace(value, path, errors):
    if not isinstance(value, dict):
        errors.append((path, "`replace` must be an object"))
        return
    for key in sorted(set(value) - {"command", "tool", "fallback"}):
        errors.append(("%s.%s" % (path, key), "unknown key `%s`" % key))
    if "command" in value and not _is_nonempty_str(value["command"]):
        errors.append(("%s.command" % path,
                       "`command` must be a non-empty string"))
    if "tool" in value and not _is_nonempty_str(value["tool"]):
        errors.append(("%s.tool" % path,
                       "`tool` must be a non-empty string"))
    if "command" not in value and "tool" not in value:
        errors.append((path, "`replace` must name a `command` or a `tool`"))
    if "fallback" not in value:
        errors.append((path, "`fallback` is required"))
    elif value["fallback"] not in PIPELINE_FALLBACKS:
        errors.append(("%s.fallback" % path,
                       "`fallback` must be one of %s, got %r"
                       % (", ".join(PIPELINE_FALLBACKS), value["fallback"])))


def _validate_autopilot(value, path, errors):
    if not isinstance(value, dict):
        errors.append((path, "`autopilot` must be an object"))
        return
    for key in sorted(set(value) - {"attempts", "timeout", "max_resumes"}):
        errors.append(("%s.%s" % (path, key), "unknown key `%s`" % key))
    if "attempts" in value and not _is_int_ge(value["attempts"], 1):
        errors.append(("%s.attempts" % path,
                       "`attempts` must be an integer >= 1"))
    if "timeout" in value and not _is_int_gt(value["timeout"], 0):
        errors.append(("%s.timeout" % path,
                       "`timeout` must be an integer > 0"))
    if "max_resumes" in value and not _is_int_ge(value["max_resumes"], 0):
        errors.append(("%s.max_resumes" % path,
                       "`max_resumes` must be an integer >= 0"))


# ---------------------------------------------------------------------------
# Entry forms: a stage entry, or a custom step.
# ---------------------------------------------------------------------------


def _validate_stage_entry(entry, stage, errors):
    allowed = _STAGE_FORM_KEYS[stage]
    declared = set(entry) - {"stage"}
    for key in sorted(declared - allowed):
        errors.append((key, "unknown key `%s`" % key))

    if "skip" in entry:
        if entry["skip"] is not True:
            errors.append(("skip", "`skip` must be `true` when present"))
        others = sorted((declared & allowed) - {"skip"})
        if others:
            errors.append((
                "skip",
                "`skip: true` excludes every other field; a skipped stage "
                "carries no options, so drop %s"
                % ", ".join("`%s`" % key for key in others)))

    if "tools" in entry and "replace" in entry:
        errors.append(("<entry>",
                       "`tools` and `replace` are mutually exclusive"))

    if "tools" in entry:
        _validate_tools(entry["tools"], "tools", errors)
    if "replace" in entry:
        _validate_replace(entry["replace"], "replace", errors)
    if "model" in entry and not _is_nonempty_str(entry["model"]):
        errors.append(("model", "`model` must be a non-empty string"))
    if "autopilot" in entry:
        _validate_autopilot(entry["autopilot"], "autopilot", errors)

    if stage == "build":
        if "subagent_model" in entry and not _is_nonempty_str(
                entry["subagent_model"]):
            errors.append(("subagent_model",
                           "`subagent_model` must be a non-empty string"))
        if "validator" in entry and not _is_bool(entry["validator"]):
            errors.append(("validator", "`validator` must be a boolean"))
        if "telemetry" in entry and not _is_bool(entry["telemetry"]):
            errors.append(("telemetry", "`telemetry` must be a boolean"))
        if "parallelism" in entry and not _is_int_ge(entry["parallelism"], 1):
            errors.append(("parallelism",
                           "`parallelism` must be an integer >= 1"))

    if stage == "review" and "disposition" in entry:
        if entry["disposition"] not in _DISPOSITIONS:
            errors.append(("disposition",
                           "`disposition` must be one of %s, got %r"
                           % (", ".join(_DISPOSITIONS),
                              entry["disposition"])))


def _validate_custom_entry(entry, errors):
    for key in sorted(set(entry) - _CUSTOM_KEYS):
        errors.append((key, "unknown key `%s`" % key))

    custom = entry.get("custom")
    if not isinstance(custom, str) or not KEBAB_RE.match(custom):
        errors.append(("custom",
                       "`custom` must be a kebab-case slug, got %r"
                       % (custom,)))

    if "command" not in entry:
        errors.append(("command", "`command` is required"))
    elif not _is_nonempty_str(entry["command"]):
        errors.append(("command", "`command` must be a non-empty string"))

    if "autopilot" in entry:
        _validate_autopilot(entry["autopilot"], "autopilot", errors)


def _validate_entry(entry):
    """Validate one raw entry, returning a list of ``(path, message)``
    violations — empty when the entry is valid."""
    if not isinstance(entry, dict):
        return [("<entry>",
                 "must be an object declaring `stage` or `custom`")]
    if "custom" in entry:
        errors = []
        _validate_custom_entry(entry, errors)
        return errors
    stage = entry.get("stage")
    if not isinstance(stage, str):
        return [("<entry>",
                 "must be an object declaring `stage` or `custom`")]
    if stage not in PIPELINE_STAGES:
        return [("stage", "unknown stage `%s`; known stages: %s"
                 % (stage, ", ".join(PIPELINE_STAGES)))]
    errors = []
    _validate_stage_entry(entry, stage, errors)
    return errors


def _render(index, entry, field_errors):
    """Render one entry's violations as ``entry <i> (<compact-sorted-json>):
    <path>: <message>`` lines, one per offending field."""
    try:
        label = json.dumps(entry, sort_keys=True)
    except (TypeError, ValueError):
        label = repr(entry)
    return ["entry %d (%s): %s: %s" % (index, label, path, message)
            for path, message in field_errors]


def validate_entries(raw):
    """Validate ``raw`` (the declared ``autonomous-pipeline`` list) entry by
    entry, returning the effective entries as plain dicts carrying exactly the
    keys each entry declared.

    Every offending entry is reported, not just the first: raises
    :class:`ValueError` whose message joins one line per validation error. The
    cross-entry canonical-order check is not done here — it lives in
    :func:`spec_common.resolve_pipeline`, which owns entry ordering. No value
    is coerced, so a valid entry is returned as a deep copy of exactly what
    was declared."""
    errors = []
    entries = []
    for index, entry in enumerate(raw):
        field_errors = _validate_entry(entry)
        if field_errors:
            errors.extend(_render(index, entry, field_errors))
        else:
            entries.append(copy.deepcopy(entry))
    if errors:
        raise ValueError("\n".join(errors))
    return entries


# ---------------------------------------------------------------------------
# The shipped preset table (shipd-config pipeline-presets)
# ---------------------------------------------------------------------------

# The built-in presets a string `autonomous-pipeline` value may name, as data
# beside the schema that types them. Keyed by exactly the names in
# ``spec_common.PIPELINE_PRESETS`` — the stdlib-side mirror the resolver checks
# an unknown name against without importing this module (the same
# mirror discipline as PIPELINE_FALLBACKS above), asserted by
# ``tests/test_resolve_pipeline.py``.
#
# `default` is bare: schema defaults apply, they are never injected. The
# cheapened presets skip a stage *explicitly* rather than by omission, so a
# skipped stage stays visible in `pipeline-show`, and both keep plan on
# `session` and keep an unskipped review — cheapening review through `model`
# and `disposition` instead.
PRESETS = {
    "default": [{"stage": name} for name in PIPELINE_STAGES],
    "eco": [
        {"stage": "research", "skip": True},
        {"stage": "epic", "skip": True},
        {"stage": "plan", "model": "session"},
        {"stage": "gate", "autopilot": {"attempts": 1}},
        {"stage": "build", "validator": False,
         "subagent_model": "tier-two-below", "telemetry": False},
        {"stage": "review", "model": "tier-below",
         "disposition": "high-only"},
    ],
    "basic": [
        {"stage": "research", "skip": True},
        {"stage": "epic", "skip": True},
        {"stage": "plan", "model": "session"},
        {"stage": "gate", "skip": True},
        {"stage": "build", "validator": False,
         "subagent_model": "tier-below"},
        {"stage": "review", "model": "tier-below",
         "disposition": "high-only"},
    ],
}


def expand_preset(name):
    """Return the named preset's entries, validated exactly like a
    user-authored list (shipd-config pipeline-presets).

    Running the table through :func:`validate_entries` is the point: a preset
    is not a privileged shape, so a preset entry that stops matching the schema
    fails the same way a hand-written one would — the drift guard the ported
    test suite relies on. ``name`` is already known to be a preset name; an
    unknown one is the resolver's error to raise, stdlib-side, without this
    import."""
    return validate_entries(PRESETS[name])
