# effort-level-tiers
Status: verified
Theme: spec-engine
Planned-at: a5657d24de10f051510521fb2d296ade8d1eaea2
Gated-hash: 225eedb123f3

## Idea

Make the pipeline's model tiers effort levels — `high` for planning, `medium`
for implementation, `low` for mechanical work — resolved by a built-in
stage→level default and expressed by each harness runner's own knob, so no
ladder configuration is needed.

### Motivation

The symbolic tiers still require a user to declare a `models` ladder before
`tier-below` means anything, and a positional ladder says nothing about *what
kind of work* a stage does. A user who never wants to name models cannot get
sensible defaults, and a stage's intent — planning versus mechanical tool work
— is invisible in the pipeline.

### Details

- `pipeline_schema.py` / `spec_common.py`: the symbolic tiers become
  `session`, `high`, `medium`, `low`; a built-in stage→level map gives planning
  stages `high`, implementation `medium`, and the rest `low`.
- `session_driver.py`: each runner expresses a level with its harness's own
  knob — Claude Code `--effort <level>`, OpenCode `--model <base>#<level>`.
- `autopilot.py`: resolve a stage's level and hand it to the runner instead of
  resolving a model id itself.
- The config `models` key becomes an optional per-level override map, and a new
  optional `model` key names the base a variant harness appends its level to.
- Every description (the autopilot and build skills, the harness autopilot body
  and reference, `docs/customise.md`, the config example) names the levels.
- `plugins/s/.claude-plugin/plugin.json`: the version bump this change owes.

Affected capabilities: `epic-autopilot` (modified), `shipd-config` (modified).
Impact: no new dependency; a repository declaring nothing gets sensible levels
per stage.

### Non-goals

- No second harness runner; the level expression is per-runner data.
- No change to the in-session drive's Agent-tool tier policy.
- No new config key beyond `models` (reshaped) and `model` (the base).
- No automatic discovery of a harness's configured model: an absent base means
  the harness runs its own default.

## Implementation

- **The tier vocabulary is an effort level, not a position.** `SYMBOLIC_TIERS`
  becomes `("session", "high", "medium", "low")`; `session` inherits the
  driver's model, the other three are effort levels, and any other non-empty
  string is still a concrete model id. `EFFORT_LEVELS` names the three.
- **A stage has a built-in level.** `STAGE_EFFORT` maps the planning stages
  (`plan`, `enrich`, `replan`, `epic`) to `high`, the implementation and
  judgement stages (`build`, `review`) to `medium`, and every other stage
  (`gate`, `research`, an unknown stage) to `low`. A pipeline entry's `model`
  option overrides its stage's level; an entry declaring none uses the default,
  so the common pipeline needs no `model` options at all.
- **The harness expresses the level, not the engine.** The session driver's
  runners gain the level: Claude Code renders `--effort <level>` (its
  `low`/`medium`/`high` vocabulary); OpenCode renders `--model
  <base>#<level>`, using the optional `model` base, and passes no `--model`
  flag when no base is declared — OpenCode then runs its own default, so a
  level never fails a run. A concrete model id renders as `--model <id>` on
  both. Rejected: reading the harness's own configured model — it couples the
  engine to each harness's config format for no correctness gain.
- **The `models` override is a per-level map.** `{"high": "<id>", ...}` pins a
  level to a concrete model id, overriding the harness's expression for that
  level only; an absent key leaves the level to the harness. The key's
  recognized shape changes from a strongest-first list to this map, and a
  malformed value raises a `ConfigError` naming `models`.
- **The autopilot resolves a level, not a model.** `drive_member` resolves each
  stage's level through `STAGE_EFFORT` and the entry's `model`, threads the
  level and the resolved `models`/`model` config to the runner, prints the
  stage→level map in the dry run, and records the levels and the config in the
  report. `_tier_anchor` and `--session-model` keep naming the driver's own
  model, which `session` inherits.
- **The version bump rides here.** `plugin.json` moves `0.6.326` → `0.6.327`.

Risk: a repository that declared the old list-shaped `models` would now fail
its validation loudly rather than silently mis-resolving; the key shipped only
in the previous change, so the blast radius is one release.

## Readiness attestation

### Problem and motivation

The tiers need a declared ladder before they mean anything, and a positional
ladder cannot express that planning deserves more effort than a mechanical tool
call — so a user who does not want to name models gets nothing useful.

Evidence:

- `spec_common.resolve_model_tier` resolves only against a ladder, and the
  prior change's `models` key is the sole source of one.
- The user asked for built-in `high`/`medium`/`low` by stage with no required
  configuration.

### Scope and non-goals

The tier vocabulary, the built-in stage levels, the runners' expression of a
level, the config keys, and every description; the in-session policy and a
second runner stay out.

Evidence:

- In scope: `pipeline_schema.py`, `spec_common.py`, `session_driver.py`,
  `autopilot.py`, the autopilot and build skills, the harness autopilot body
  and reference, `docs/customise.md`, the config example, and the version bump.
- Out of scope: the Agent-tool tier policy the build skill documents.

### Affected capabilities and files

Two capabilities modified; four engine modules, five prose surfaces, and the
version bump.

Evidence:

- Capability `epic-autopilot`: `stage-model-resolution` (base 3ea368e1c224)
  modified.
- Capability `shipd-config`: `model-ladder-key` (base 0721881bc55e) modified;
  `pipeline-entry-validation` (base 41176d17e688) modified for the new tier
  vocabulary.
- Edited: `pipeline_schema.py`, `spec_common.py`, `session_driver.py`,
  `autopilot.py`, the autopilot and build skills, the harness autopilot body
  and reference, `docs/customise.md`, the config example,
  `plugins/s/.claude-plugin/plugin.json`.
- Runnable premise: `claude --help` lists `--effort <level>` with `low`,
  `medium`, `high`; `opencode run --model
  'fireworks-ai/accounts/fireworks/models/deepseek-v4p1-flash#high' "…"` ran and
  replied, while `--model '#high'` was refused as an invalid model reference.

### No open task-shaping decision

Every task-shaping decision is settled by the user and by the live CLI probes.

Evidence:

- The level vocabulary, the OpenCode base, and the `models` map shape: settled
  by the user, Q1 through Q3.
- The stage→level defaults: settled by the user's ask (planning high,
  implementation medium, mechanical low).
- The two harnesses' effort knobs: observed live.
