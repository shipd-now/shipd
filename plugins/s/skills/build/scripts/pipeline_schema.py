#!/usr/bin/env python3
"""pipeline_schema.py — pydantic models for `autonomous-pipeline` entries
(shipd-config pipeline-entry-validation, pipeline-stage-options).

This is the engine's one pydantic-dependent module besides ``dashboard.py``'s
``tui`` verb, and the constitution scopes that exception to exactly this path:
``spec_common.resolve_pipeline`` imports this module **lazily**, and only when a
config layer actually declares the ``autonomous-pipeline`` key. Nothing else
imports it, so the no-key default pipeline — and every other engine script —
resolves with pydantic absent.

The grammar it enforces is the closed one documented in the shipd-config spec:
an entry is either a stage entry (``{"stage": <registry name>}``, optionally
with ``skip``, ``tools``, ``replace``, and the typed per-stage options) or a
custom step (``{"custom": <kebab slug>, "command": ...}``). Every model sets
``extra="forbid"``, so an unknown key is an error rather than silently ignored
config, and ``strict=True``, so a wrongly typed value is rejected rather than
coerced: ``{"skip": 1}`` and ``{"parallelism": "2"}`` are errors, as they were
under the hand-rolled validator this replaces. (Nested objects are still
accepted as plain dicts; strictness applies to the scalar leaves that JSON
already distinguishes.) Defaults are declared on the models but never injected
into resolved entries: :func:`validate_entries` dumps with
``exclude_unset=True`` so an entry carries exactly the keys its author wrote.
"""

import json
from typing import Annotated, List, Literal, Optional, Union

from pydantic import (BaseModel, ConfigDict, Discriminator, Field,
                      StringConstraints, Tag, TypeAdapter, ValidationError,
                      model_validator)

from spec_common import KEBAB_RE

# The symbolic model tiers a `model` / `subagent_model` option may name,
# resolved relative to the driving session by the pipeline's consumers. Any
# other non-empty string is a concrete model id — the set of ids is open, so a
# new model never needs a schema release.
SYMBOLIC_TIERS = ("session", "tier-below", "tier-two-below")

# A stage/tool binding falls back to the built-in implementation or skips the
# stage; mirrors spec_common.PIPELINE_FALLBACKS.
Fallback = Literal["builtin", "skip"]

NonEmptyStr = Annotated[str, StringConstraints(min_length=1)]

# A model tier: a symbolic tier from SYMBOLIC_TIERS or a concrete model id.
Tier = NonEmptyStr


# ---------------------------------------------------------------------------
# Shared sub-objects
# ---------------------------------------------------------------------------


class AutopilotOpts(BaseModel):
    """The `autopilot`-namespaced driver knobs any entry may carry."""

    model_config = ConfigDict(extra="forbid", strict=True)

    attempts: Annotated[int, Field(ge=1)] = 3
    timeout: Optional[Annotated[int, Field(gt=0)]] = None
    max_resumes: Optional[Annotated[int, Field(ge=0)]] = None


class ToolBinding(BaseModel):
    """One entry of a stage's `tools` list."""

    model_config = ConfigDict(extra="forbid", strict=True)

    name: NonEmptyStr
    fallback: Fallback


class ReplaceSpec(BaseModel):
    """A stage's `replace` object: a substitute `command` or `tool`."""

    model_config = ConfigDict(extra="forbid", strict=True)

    command: Optional[NonEmptyStr] = None
    tool: Optional[NonEmptyStr] = None
    fallback: Fallback

    @model_validator(mode="after")
    def _names_a_target(self):
        if self.command is None and self.tool is None:
            raise ValueError("`replace` must name a `command` or a `tool`")
        return self


# ---------------------------------------------------------------------------
# Stage entries
# ---------------------------------------------------------------------------


class StageStep(BaseModel):
    """Fields every stage entry shares. Subclasses pin `stage` to one registry
    name and add that stage's own options."""

    model_config = ConfigDict(extra="forbid", strict=True)

    skip: bool = False
    tools: Optional[Annotated[List[ToolBinding], Field(min_length=1)]] = None
    replace: Optional[ReplaceSpec] = None
    model: Optional[Tier] = None
    autopilot: Optional[AutopilotOpts] = None

    @model_validator(mode="after")
    def _exclusive_forms(self):
        declared = self.model_fields_set
        if "skip" in declared:
            if self.skip is not True:
                raise ValueError("`skip` must be true when present")
            others = sorted(declared - {"stage", "skip"})
            if others:
                raise ValueError(
                    "`skip: true` excludes every other field; a skipped stage "
                    "carries no options, so drop %s"
                    % ", ".join("`%s`" % key for key in others))
        if "tools" in declared and "replace" in declared:
            raise ValueError("`tools` and `replace` are mutually exclusive")
        return self


class ResearchStep(StageStep):
    stage: Literal["research"]


class EpicStep(StageStep):
    stage: Literal["epic"]


class PlanStep(StageStep):
    stage: Literal["plan"]


class GateStep(StageStep):
    stage: Literal["gate"]


class BuildStep(StageStep):
    stage: Literal["build"]

    subagent_model: Optional[Tier] = None
    validator: bool = True
    telemetry: bool = True
    parallelism: Optional[Annotated[int, Field(ge=1)]] = None


class ReviewStep(StageStep):
    stage: Literal["review"]

    disposition: Literal["all", "high-only", "none"] = "all"


class CustomStep(BaseModel):
    """A custom step inserted at its list position."""

    model_config = ConfigDict(extra="forbid", strict=True)

    custom: Annotated[str, StringConstraints(pattern=KEBAB_RE.pattern)]
    command: NonEmptyStr
    autopilot: Optional[AutopilotOpts] = None


# ---------------------------------------------------------------------------
# The discriminated entry union
# ---------------------------------------------------------------------------


def stage_or_custom(value):
    """Discriminate an entry: a stage entry is tagged by its `stage` name, a
    custom step by the literal tag ``custom``. Returning ``None`` (an entry
    that is neither) makes pydantic report that the entry matches no form."""
    if isinstance(value, dict):
        if "custom" in value:
            return "custom"
        stage = value.get("stage")
        return stage if isinstance(stage, str) else None
    if isinstance(value, CustomStep):
        return "custom"
    return getattr(value, "stage", None)


PipelineEntry = Annotated[
    Union[
        Annotated[ResearchStep, Tag("research")],
        Annotated[EpicStep, Tag("epic")],
        Annotated[PlanStep, Tag("plan")],
        Annotated[GateStep, Tag("gate")],
        Annotated[BuildStep, Tag("build")],
        Annotated[ReviewStep, Tag("review")],
        Annotated[CustomStep, Tag("custom")],
    ],
    Discriminator(stage_or_custom),
]

_ENTRY_ADAPTER = TypeAdapter(PipelineEntry)


def _render(index, entry, exc):
    """Render one entry's :class:`ValidationError` as human-readable lines,
    each naming the offending entry by index and content: ``entry <i>
    (<compact-sorted-json>): <field-path>: <message>``."""
    try:
        label = json.dumps(entry, sort_keys=True)
    except (TypeError, ValueError):
        label = repr(entry)
    lines = []
    for err in exc.errors():
        path = ".".join(str(part) for part in err.get("loc", ()))
        lines.append("entry %d (%s): %s: %s"
                     % (index, label, path or "<entry>", err.get("msg", "")))
    return lines


def validate_entries(raw):
    """Validate ``raw`` (the declared ``autonomous-pipeline`` list) entry by
    entry, returning the effective entries as plain dicts carrying exactly the
    keys each entry declared.

    Every offending entry is reported, not just the first: raises
    :class:`ValueError` whose message joins one line per validation error. The
    cross-entry canonical-order check is not done here — it lives in
    :func:`spec_common.resolve_pipeline`, which owns entry ordering."""
    errors = []
    entries = []
    for index, entry in enumerate(raw):
        try:
            model = _ENTRY_ADAPTER.validate_python(entry)
        except ValidationError as exc:
            errors.extend(_render(index, entry, exc))
            continue
        entries.append(model.model_dump(exclude_unset=True))
    if errors:
        raise ValueError("\n".join(errors))
    return entries
