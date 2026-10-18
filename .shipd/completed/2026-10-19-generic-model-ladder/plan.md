# generic-model-ladder
Status: verified
Theme: spec-engine
Planned-at: e689d4b77f95e58a599a96c8169059aee46dd2ef
Gated-hash: 9e705f4b393d

## Idea

Make the symbolic model tier's ladder generic: a `models` config key declares
the ladder, `spec_common` resolves against it, and every consumer and
description uses the declared ladder rather than the hard-coded Claude aliases.

### Motivation

The symbolic tiers `tier-below` and `tier-two-below` resolve against a ladder
hard-coded to `fable`, `opus`, `sonnet`, `haiku`, so on any non-Claude harness
the tiers step onto model names that harness cannot run — the exact gap left
open when the autopilot became harness-agnostic. A user who drives OpenCode
with a Fireworks model has no way to say what "one tier down" means.

### Details

- `spec_common.py`: a `models` recognized config key, a `resolve_model_ladder`
  resolver (the declared list, else `DEFAULT_MODEL_LADDER`), and
  `resolve_model_tier(tier, session_model=None, ladder=None)` resolving against
  the passed ladder.
- `autopilot.py`: resolve the ladder once per run from config, thread it to
  every `resolve_model_tier` call and to `_tier_anchor`, print it in the dry
  run, and record it in the report.
- The descriptions that name the Claude aliases: the autopilot and build
  skills, the harness autopilot body and reference, and `docs/customise.md`'s
  config table.
- `plugins/s/.claude-plugin/plugin.json`: the version bump this change owes.

Affected capabilities: `epic-autopilot` (modified), `shipd-config` (modified).
Impact: no new dependency; a repo declaring no `models` key resolves exactly as
it does today.

### Non-goals

- No per-harness ladders in the registry: the ladder is a property of the
  models a user runs, not of the harness.
- No change to the symbolic tier vocabulary (`session`, `tier-below`,
  `tier-two-below`).
- No new model ids or aliases; the fallback tuple stays.
- No change to the in-session drive or to any stage's resolved value beyond the
  ladder it resolves against.

## Implementation

- **The ladder is configuration; the tuple is only its fallback.**
  `spec_common.DEFAULT_MODEL_LADDER` holds today's `fable`/`opus`/`sonnet`/
  `haiku` tuple as the default, and `resolve_model_ladder(config)` returns the
  `models` list when the configuration declares one, else that default.
  `models` joins `RECOGNIZED_CONFIG_KEYS`. Rejected: a per-harness ladder in
  the registry — OpenCode and friends are provider-agnostic, so the ladder
  belongs to the models the user runs, not to the harness binary.
- **Resolution takes the ladder as a parameter.** `resolve_model_tier(tier,
  session_model=None, ladder=None)` resolves `session` to the anchor and
  `tier-below`/`tier-two-below` to the ladder entry one or two positions below
  the anchor, clamped at the bottom; `ladder=None` uses the default, so every
  existing caller is unchanged. A non-empty string that is not a symbolic tier
  is still returned verbatim.
- **An off-ladder anchor falls back to itself.** When the anchor is not on the
  ladder — including an empty ladder — `tier-below` and `tier-two-below`
  resolve to the anchor, so a run proceeds on one model rather than stepping
  onto a name the harness cannot run. This replaces today's "step from the
  ladder top when the anchor is unknown", which assumed the ladder was the only
  vocabulary. Rejected: refusing the run — an unresolvable tier is a weaker
  result, not a broken one.
- **The autopilot resolves the ladder once and threads it.** `run`,
  `drive_member`, `drive_single_member`, and `run_member` resolve the ladder
  from the run's root and pass it to every `resolve_model_tier` call and to
  `_tier_anchor`, whose "ladder top" becomes the resolved ladder's first entry.
  The dry run prints the ladder beside the anchor, and the report records both.
- **Every description says "the declared ladder".** The autopilot skill's
  `--session-model` note, the build skill's `subagent_model` table, the harness
  autopilot body and reference, and `customise.md`'s config table name the
  `models` key and the fallback rather than `fable`.
- **The version bump rides here.** `plugin.json` moves `0.6.325` → `0.6.326`.

Risk: a repo that declared `models` for another purpose would gain ladder
semantics; the key is new, so no existing configuration carries it.

## Readiness attestation

### Problem and motivation

On a non-Claude harness the symbolic tiers resolve onto Claude aliases the
harness cannot run, and there is no way to declare what "one tier down" means.

Evidence:

- `spec_common.MODEL_LADDER` is the fixed tuple `fable`/`opus`/`sonnet`/
  `haiku`.
- The prior change `autopilot-harness-runner` left the model ladder explicitly
  out of scope as Claude-shaped.

### Scope and non-goals

The ladder's declaration, resolution, and every description; per-harness
ladders, the tier vocabulary, and the in-session drive stay out.

Evidence:

- In scope: `spec_common.py`, `autopilot.py`, the autopilot and build skills,
  the harness autopilot body and reference, `docs/customise.md`, and the
  version bump.
- Out of scope: `pipeline_schema.SYMBOLIC_TIERS` is already harness-neutral.

### Affected capabilities and files

Two capabilities modified; six prose and engine files plus the version bump.

Evidence:

- Capability `epic-autopilot`: `stage-model-resolution` (base ac93ef8e6aeb)
  modified.
- Capability `shipd-config`: the `models` key added to its recognized set.
- Edited: `spec_common.py`, `autopilot.py`, the autopilot and build skills, the
  harness autopilot body and reference, `docs/customise.md`,
  `plugins/s/.claude-plugin/plugin.json`.
- Runnable premise: `python3 -c "import spec_common; print(spec_common.MODEL_LADDER)"`
  → the fixed tuple; `resolve_model_tier("tier-below", None)` → `opus`.

### No open task-shaping decision

Every task-shaping decision is settled by the user and the existing resolver.

Evidence:

- The `models` key and the anchor fallback: settled by the user, Q1 and Q2.
- The resolver's shape and the consumers: settled by investigation of
  `spec_common.resolve_model_tier` and `autopilot.py`.
