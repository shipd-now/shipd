# plan-depth-gate
Status: verified

## Idea

`am:plan` converges fast by design: it suppresses questions (one batched call at
most), never shows its thinking, and emits silently. On simple changes that is a
virtue; on complex ones the user's first sight of the plan's reasoning is the
finished spec — trade-offs are resolved invisibly, assumptions are never
challenged, and no diagram or option comparison ever reaches the user. A
comparison against OpenSpec's explore mode and Matt Pocock's grill-me skill
identified the missing behaviors; the decision is to build them into `am:plan`
itself rather than add a separate explore skill.

This change adds an adaptive depth gate and a bounded grill loop:

- A **depth gate** after investigation classifies each change fast/depth by
  counting concrete signals; explicit user words override the count.
- The **fast path** is today's behavior verbatim; the question contract is
  rewritten to be explicitly scoped to it.
- The **depth path** loads a new `references/dialogue.md` and runs a bounded
  grill loop: one decision per AskUserQuestion, recommended answer first,
  facts read rather than asked, terminating when no open decision would change
  the task list.
- **Visualization on demand**: a new `references/visualization.md` is loaded
  only when a diagram or options table would carry a decision.
- A **shared-understanding summary** with a confirm closes the depth path
  before silent emission.

### Non-goals

- No separate explore skill — everything lands inside `am:plan`.
- No open-ended discussion mode: the grill loop has a defined start (the gate)
  and end (no task-shaping decision remains); "thinking time" without a
  destination is explicitly rejected.
- No changes to the readiness checklist, emission format, lint gate, or any
  engine script under `plugins/s/skills/build/scripts/`.
- No changes to `am:epic` or `am:build` in this change.

Affected capabilities: `shipd-plan` (modified). Impact:
`plugins/s/skills/plan/SKILL.md`, new
`plugins/s/skills/plan/references/dialogue.md` and
`plugins/s/skills/plan/references/visualization.md`,
`plugins/s/.claude-plugin/plugin.json` (version bump). Skill-markdown only —
no engine tests required.

## Implementation

- **Gate = explicit signal checklist, not judgment.** Five observable signals,
  counted after investigation: (1) more than one viable approach survived and
  the choice changes the task list; (2) the request states an outcome/problem
  rather than a mechanism; (3) a new capability is added rather than an
  existing one modified; (4) blast radius spans multiple capabilities; (5) the
  user's wording signals uncertainty. 0–1 signals → fast path; ≥2 → depth.
  Explicit user words ("grill me" → depth, "just plan it" → fast) always
  override the count. The verdict is announced in one sentence so the gate is
  visible and debuggable. Rejected: "use judgment" phrasing — with the skill's
  existing convergence gradient it would collapse to never firing.
- **Mode-scoped rules via progressive disclosure.** The grill-loop protocol
  lives only in `references/dialogue.md`, loaded when the gate selects depth;
  the batching contract in `SKILL.md` is reworded as fast-path-only. This keeps
  contradictory rules (batch-once vs one-at-a-time) from ever being loaded
  together. Rejected: all rules inline in `SKILL.md` — global contradictions
  make skill behavior flaky and cost tokens on every fast-path run.
- **Grill loop protocol** (in `dialogue.md`): derive an agenda of open
  task-shaping decisions from readiness item 4; resolve them one at a time,
  each via a single-question AskUserQuestion with the recommended option
  listed first; apply a fact/decision test to every candidate (discoverable →
  read it, never ask); fold each answer back into the agenda. Soft cap of ~6
  decisions — exceeding it is a decomposition signal and the loop suggests
  `/s:epic` instead of continuing. Rejected: uncapped looping — turns into an
  interrogation and hides an epic-sized change.
- **Visualization on demand** (in `visualization.md`): ASCII idioms
  (current-vs-proposed maps, flow sketches, options tables) and use of the
  AskUserQuestion `preview` field for per-option diagrams. Loaded at most once
  per session, the first time a visual would carry a decision; decorative
  visuals are prohibited.
- **Depth path ends with a shared-understanding summary**: problem, chosen
  approach, decisions with one-line rationale, known risks — confirmed via a
  final AskUserQuestion whose recommended option is "emit". This implements
  grill-me's "don't act until confirmed" with a hard end. The fast path gets
  no such step. The readiness gate remains the formal terminator for both
  paths, unchanged.
- **Version bump** `0.2.3` → `0.2.4` in `plugins/s/.claude-plugin/plugin.json`
  per the cache-snapshot rule.

Risk: gate miscalibration at the trivial/complex boundary. Guarded three ways:
conservative default (fast path), verbal overrides in both directions, and the
announced verdict making a wrong classification immediately visible and
correctable.
