# build-provider-neutral-models
Status: verified

## Idea

Make the build skill's sub-agent model choice provider-neutral: the
orchestrator picks the "model down" itself from the models it has, and the
skill names no vendor's models.

### Motivation

An orchestrator running `/s:build` on a harness or model lineup other than
Fable/Opus/Sonnet/Haiku gets instructions that name models it does not have,
so it cannot follow the policy as written. The user wants the agent to judge
both the model down and a decent sub-agent model from what is actually
available, without the skill dictating any provider's model names.

### Details

- Rewrite the build skill's model policy so the orchestrator stays on the
  session's model and spawns sub-agents on the **model down**: the model it
  judges one clear capability step below its own, picked from the Agent
  tool's options in that session.
- Replace the `tier-below` / `tier-two-below` table row's named ladder with
  the same judgement, in both the build and autopilot skills.
- Swap "most-powerful" / "second-most-powerful" wording for "session's
  model" / "model down" in the Phase 3 heading and body, the verification
  fix-up step, and the operating rule.
- Bump the plugin version.

Affected capabilities: `build-spec-lifecycle` (one requirement modified, one
added). Impact: `plugins/s/skills/build/SKILL.md`,
`plugins/s/skills/autopilot/SKILL.md`, `plugins/s/.claude-plugin/plugin.json`.
No engine code changes.

### Non-goals

- No change to the engine's `MODEL_LADDER` in
  `plugins/s/skills/build/scripts/spec_common.py` or to `resolve_model_tier`:
  the detached autopilot driver passes `claude --model <alias>` and needs
  concrete ids.
- No change to autopilot's description of the detached driver's tier anchor
  (`autopilot/SKILL.md`, the `--session-model` anchor paragraph), which
  documents that engine behavior.
- No new pipeline option values; `session`, `tier-below`, `tier-two-below`,
  and verbatim ids keep their meaning.

## Implementation

- **Model policy text (build `SKILL.md`, the "Model policy" block).** Replace
  it with these bullets, provider-neutral:
  - Planning/design/validation/Q&A runs on the session's model — the user
    chose it; do not downgrade yourself.
  - Implementation sub-agents spawn on the **model down**: the model you
    judge one clear capability step below your own and a decent fit for the
    tasks.
  - You pick the model down at spawn time from the `model` options the Agent
    tool offers in this session. The skill names no provider's models.
  - When no option sits below your own model, omit the parameter so
    sub-agents inherit the session's model. Never spawn sub-agents on a model
    stronger than your own.
  - Drop two steps only when the user asks to optimize for cost on simple
    tasks.
  Rationale: the agent knows what its harness offers; a hardcoded ladder goes
  stale and is wrong off one provider. Rejected: keeping names as "e.g."
  examples — the user asked for none.
- **Table row (build and autopilot `SKILL.md`).** The `tier-below` /
  `tier-two-below` cell reads: "the model you judge one / two capability
  steps below this session's own model among the Agent tool's options; when
  fewer options sit below, the lowest one below; when none does, omit the
  parameter". Identical text in both files, because both describe the same
  in-session spawn.
- **Wording swaps (build `SKILL.md`).** Frontmatter `description`: "on the
  session's model ... on a model one step down". Intro paragraph: "running on
  the model down (one step below yours)". Phase 3 heading becomes
  `## Phase 3 — Spawn execution sub-agents (model down)`; its body says
  "`model` set to the **model down** per the model policy above". Verification
  step 4 says "(model down)". Operating rule: "The session's model plans; the
  model down executes. Never invert this."
- **Spec.** MODIFY `interactive-pipeline-resolution` to drop the named ladder,
  and ADD `provider-neutral-model-down` for the default policy and the
  no-provider-names rule, scoped to the build skill body and the autopilot
  in-session table.
- **Version.** Bump `plugins/s/.claude-plugin/plugin.json` `version` by one
  patch from whatever `main` carries at build time.

Risk: an orchestrator could pick a model above its own. The "never stronger
than your own" sentence guards it. Risk: losing a deterministic mapping. The
detached driver keeps its engine ladder, so unattended runs stay
deterministic.

## Readiness attestation

### Problem and motivation

The build skill names one provider's models when choosing sub-agent models,
so orchestrators elsewhere cannot follow it, and the user wants the agent to
choose.

Evidence:

- `plugins/s/skills/build/SKILL.md:28-35` names Opus, Fable, `sonnet`, `opus`,
  `haiku` in the policy.
- `plugins/s/skills/build/SKILL.md:48` resolves tiers on the ladder
  `fable` → `opus` → `sonnet` → `haiku`.
- The request: "only says model down rather than naming Anthropic models".

### Scope and non-goals

Skill prose and the spec change; the engine ladder and the detached driver's
anchor stay.

Evidence:

- In scope: `plugins/s/skills/build/SKILL.md:5-6,18-35,48,333-336,513,960`;
  `plugins/s/skills/autopilot/SKILL.md:332`.
- Out of scope: `plugins/s/skills/build/scripts/spec_common.py:970`
  (`MODEL_LADDER`), `plugins/s/skills/autopilot/SKILL.md:520`.

### Affected capabilities and files

One capability and three files are affected.

Evidence:

- Capability `build-spec-lifecycle`: requirement
  `interactive-pipeline-resolution` (base 839eecfd0dba, from
  `spec_status.py base-hash`), plus new `provider-neutral-model-down`.
- Capability `epic-autopilot` carries no model names (grep for
  `fable|sonnet|haiku` in its master found none), so it needs no delta.
- Files: `plugins/s/skills/build/SKILL.md`,
  `plugins/s/skills/autopilot/SKILL.md`,
  `plugins/s/.claude-plugin/plugin.json` (now 0.6.257).

### No open task-shaping decision

Every decision is settled by investigation; none went to the oracle or the
user.

Evidence:

- "Decent model" read as the orchestrator's own judgement of a capable model
  one step down, with session inheritance when none is lower: settled by
  investigation of the request wording.
- Autopilot's in-session table row included, because it repeats the build
  row verbatim: settled by investigation.
- Engine `MODEL_LADDER` excluded, because `claude --model` needs real ids:
  settled by investigation of `spec_common.py:970` and its tests.
