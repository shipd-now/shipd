# named-pipelines
Status: complete
Theme: spec-engine

## Introduction

Delivering a change through shipd always runs the full ceremony: spec
authoring on the strongest model, a fan-out of implementation sub-agents,
an adversarial validator session, a semantic review with a per-finding
disposition loop, and token telemetry — regardless of how much rigor the
work actually warrants. The `autonomous-pipeline` config key can already
skip or replace whole stages, but it governs only the autopilot, its
grammar is hand-validated, and the biggest token levers — model tiers, the
validator, the disposition loop — live as prose inside skill instructions
where no configuration can reach them.

This epic makes the pipeline the single delivery contract for both
drivers. The `autonomous-pipeline` key gains a second form — a string
naming a built-in preset (`default`, `eco`, `basic`) — alongside the
existing custom entry list. Entries become typed, stage-specific pydantic
models: per-stage options for the expensive parts (sub-agent model tier,
validator on/off, review disposition depth, telemetry) plus an
`autopilot`-namespaced block for driver-only knobs (retry attempts,
timeouts). User-authored pipelines are validated fail-closed before use —
a malformed declaration never half-runs. Both the interactive
`/s:build`/`/s:plan` flow and the autopilot resolve the same pipeline and
honor the same options, each ignoring what only the other can act on.
Success: `{"autonomous-pipeline": "eco"}` is a one-line opt-in that
measurably cuts token spend on both interactive and autopilot deliveries,
while a hand-authored pipeline with a typo fails resolution with an error
naming the offending entry and field.

### Non-goals

- No preset+override merging: the key holds a preset name **or** a full
  entry list, never both, and layers keep merging
  nearest-wins-wholesale. "Eco but with the validator on" means expanding
  the preset (`pipeline-show`) and committing the tweaked list.
- No skipping the semantic-review requirement: shipped presets always run
  the review stage — cheapening means a lower model tier and a shallower
  disposition scope, never an unposted gate. The schema still permits an
  explicit `skip` on review for custom pipelines (repos without the
  required check), per the existing explicit-skip doctrine.
- No engine-wide pydantic: the stdlib-only rule stands for every path
  except declared-pipeline validation. The default pipeline (no key, or
  `"default"`) resolves without pydantic installed; every other engine
  verb keeps working without it.
- No new registry stages: the six-stage canonical order
  (`research, epic, plan, gate, build, review`) is unchanged; new
  expressiveness comes from per-stage options, not new stages.
- No autopilot concurrency or scheduling changes: members still run
  sequentially, risk-ascending, one worktree/branch/PR each.

## Decisions

- **Pydantic is the second scoped constitution exception.** The
  constitution's stdlib-only rule gains a `textual`-style named exception:
  pydantic, pinned in the repo-root `requirements.txt`, imported lazily
  and only inside pipeline validation. Resolution of the built-in default
  stays stdlib-only; resolving a *declared* pipeline without pydantic
  installed is a hard error with an install hint (fail-closed — a
  user-authored schema is never half-validated). Rejected: engine-wide
  dependency (breaks clone-and-run for every verb) and a stdlib fallback
  validator (silently weaker validation exactly when the user authored
  something to validate). `/s:doctor` gains the preflight check and a
  consent-gated install remedy.
- **Entries are a pydantic discriminated union with `extra="forbid"`.**
  One model per stage plus the custom-step form, discriminated on
  `stage`/`custom`. Unknown keys, wrong types, and misplaced options fail
  resolution naming the entry index and field. The union replaces the
  hand-rolled `_validate_pipeline_entry`; the existing error-message
  quality (offending entry by index and content) is a requirement on the
  new validator, not a casualty. The canonical-order check and the
  existing `tools`/`replace`/`skip` forms carry over unchanged.
- **Driver-only knobs live under an `autopilot` namespace.** Retries
  (`attempts`, default 3 — today's three-strike behavior), `timeout`, and
  `max_resumes` sit in an `autopilot` sub-object on each stage entry,
  because retrying is a property of the unattended driver: interactively
  the human is the retry loop. The interactive flow ignores the block
  entirely; no context-dependent defaults. `attempts` governs the outer
  fresh-session retry loop only — `max_resumes` (continuing one session)
  stays a separate knob, never conflated.
- **Model selection is symbolic, resolved at spawn time.** Per-stage
  `model` (and `subagent_model` on build) take the symbolic tiers
  `session`, `tier-below`, `tier-two-below` — codifying the ladder policy
  that is currently `/s:build` SKILL.md prose — with concrete model ids
  also accepted. Symbolic values stay correct as model generations ship;
  the spawn-time resolution logic becomes code with one authority instead
  of per-skill prose.
- **Named presets: a string is a preset, a list is custom.** The
  `autonomous-pipeline` key's value union gains the string form; the
  preset table ships as data beside the schema (one source of truth), and
  `default`, `eco`, and `basic` are the v1 names, with `"default"` an
  explicit spelling of the no-key built-in. Unknown names fail listing
  the known presets. Provenance reports `preset:<name>` plus the
  supplying config path. `spec_status.py pipeline-show` renders the
  effective pipeline and can expand any named preset on demand — the
  supported path to fork a preset into a custom list.
- **Presets never cheapen `plan`.** A weak spec multiplies downstream
  cost (sub-agent questions, refuted scenarios, review findings), so
  every shipped preset keeps plan on `session`; savings come from stages
  whose output is mechanically verifiable — implementation, validation,
  review.
- **Review always runs in shipped presets; disposition depth is the
  lever.** The `semantic-review` commit status is a required check, so a
  preset that skipped review would deadlock auto-merge. Review's options
  are `model` and `disposition` (`all` | `high-only` | `none`):
  `high-only` implements high-severity findings and auto-replies on the
  rest so threads still resolve; `none` posts the review and auto-replies
  on everything (the gate stays honest, the loop costs nothing). Shipped
  presets use `all` (default) and `high-only` (eco/basic).
- **One resolved pipeline, two drivers, documented applicability.** The
  autopilot maps entries to graded headless sessions (now passing the
  resolved model tier); the interactive skills map them to phases within
  the session, honoring `validator`, `telemetry`, `subagent_model`, and
  `disposition`, and ignoring `autopilot` blocks and `replace` commands
  (which stay autopilot semantics). Each schema field documents which
  driver honors it; a field neither driver can honor does not exist.

## Design

Three layers. The **stage registry** (unchanged) is the skeleton:
`research, epic, plan, gate, build, review`, canonical order enforced,
`research`/`epic` remaining pre-approval stages the autopilot ignores.
The **named-preset layer** resolves the config key's string form through
the preset table into an entry list. The **typed-options layer** is the
pydantic union validating every entry — preset-expanded or user-authored
— before any driver consumes it.

The v1 preset table (the contract each preset change implements):

```
             default                eco                       basic
research/epic  as-is                skip                      skip
plan           session              session                   session
gate           attempts 3           attempts 1                skip
build          validator on,        validator off,            validator off,
               subagents tier-below subagents tier-two-below, subagents tier-below
                                    telemetry off
review         session, all        tier-below, high-only      tier-below, high-only
```

Pieces and seams: the dependency groundwork (constitution amendment,
requirements pin, doctor remedy) is its own change (member 1). The
pydantic schema — stage models, autopilot namespace, symbolic tiers,
fail-closed lazy import — replaces the hand-rolled validator inside
`resolve_pipeline` (member 2). The preset table and the string-form
resolution extend the resolver and `pipeline-show` (member 3). The review
skill and `review_gate.py` learn disposition scope and model tier so both
drivers can invoke a cheapened review (member 4). The autopilot driver
honors per-stage `autopilot.attempts`, passes resolved model tiers to its
headless sessions, and conveys stage options in its stage prompts
(member 5). The interactive `/s:build`/`/s:plan` flow resolves the same
pipeline and honors the option fields in its phases (member 6).

Dependencies: member 2 depends on 1; member 3 depends on 2; members 4–6
depend on 2 and 3 (member 4 is also independently useful); members 4, 5,
and 6 are mutually independent. The epic is fully assembled when 5 and 6
land.

## Changes

| Change | Description | Code | Integration | Unknowns | Risk |
| --- | --- | --- | --- | --- | --- |
| pydantic-dependency | Constitution amendment naming pydantic as the second scoped exception, requirements.txt pin, CI wiring, /s:doctor check with consent-gated install remedy | low | medium | low | low |
| pipeline-schema | Pydantic discriminated-union entry models with per-stage typed options, autopilot namespace, symbolic tiers; lazy fail-closed validation replacing the hand-rolled grammar in resolve_pipeline | high | medium | medium | medium |
| pipeline-presets | String-or-list key union, preset table as data (default/eco/basic), preset:<name> provenance, pipeline-show preset expansion | medium | low | low | low |
| review-stage-options | /s:review and review_gate honor a disposition scope (all/high-only/none with auto-replies keeping threads resolvable) and a model tier | medium | medium | low | low |
| autopilot-stage-options | Autopilot reads autopilot.attempts per stage in place of the fixed three-strike, passes resolved model tiers to headless sessions, conveys stage options in stage prompts | medium | high | medium | medium |
| interactive-pipeline | /s:build and /s:plan resolve the shared pipeline and honor validator, telemetry, subagent_model, and disposition in their phases, ignoring autopilot-only fields | medium | high | medium | medium |

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 459 | 157.6k |
| Edit | 141 | 103.6k |
| Write | 19 | 50.3k |
| (no tool) | 0 | 46.3k |
| Read | 114 | 23.3k |
| Agent | 19 | 11.5k |
| SendMessage | 5 | 4.2k |
| ToolSearch | 6 | 1.7k |
| **Total** | 763 | 398.6k |
