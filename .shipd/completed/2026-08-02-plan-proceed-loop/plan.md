# plan-proceed-loop
Status: verified

## Idea

Replace the plan skill's rigid numbered go-ahead with a natural, loopable "Shall
we proceed with the plan?" gate, and stop asking for a second "emit" confirmation
once the depth gate runs clean.

### Motivation

After the findings digest the skill asks a stiff numbered prompt ("1. proceed…
2. adjust scope"), and on the depth path it then asks a *second* time ("reply
'emit'…") — two ceremonial gates for one approval. Users want to keep planning
conversationally and give a single "yes" that carries through to emission.

### Details

- Replace the "without open questions" ending in `am:plan` Flow step 2: instead
  of a numbered proceed/adjust prompt, close the digest with the plain question
  **"Shall we proceed with the plan?"**
- Make that question a loop: an affirmative reply fires the depth gate; any other
  reply (more questions, new information, scope changes) is folded in as
  continued planning, the skill shows a one-line delta of what changed and
  re-asks once the plan is settled again — looping until the user affirms.
- An explicit go-ahead already in the reply (e.g. answering an OPEN QUESTIONS
  list) counts as the affirmative and skips a redundant re-ask.
- Make the depth path's shared-understanding "reply 'emit'" checkpoint
  conditional: the affirmative is the sole approval, so a clean gate (fast path,
  no interactive rounds) emits directly with no summary/emit step; only when the
  depth gate needs more info (the grill loop runs) does the closing summary +
  "emit" confirmation appear.

Affected capabilities: `shipd-plan` (modified — `investigation-findings-digest`,
`shared-understanding-summary`). Impact: `plugins/s/skills/plan/SKILL.md`,
`plugins/s/skills/plan/references/dialogue.md`, and the plugin version bump in
`plugins/s/.claude-plugin/plugin.json`.

### Non-goals

- The **OPEN QUESTIONS** ending is unchanged — it still ends the turn with no
  go-ahead prompt when task-shaping questions remain open.
- The depth-gate classification (the five signals, overrides, announcement) is
  unchanged — this only reshapes the prompt that precedes it and the emit
  checkpoint that follows.
- No change to enrichment mode, the ask-mikk rung, or question-rejection
  recovery.

## Implementation

- **Two coupled surfaces move together.** The go-ahead contract lives in both
  the verified spec (`shipd-plan`) and the operative `SKILL.md`; both are edited in
  this change so they never drift. The spec requirements are applied to
  `verified/` by the merge engine at build/archive time; the `SKILL.md` and
  `dialogue.md` prose are edited directly.
- **`investigation-findings-digest` (MODIFIED).** The only changed clause is the
  "no open questions" ending: it becomes a single plain-text question, "Shall we
  proceed with the plan?", with no numbered options and no AskUserQuestion, plus
  the loop semantics and the go-ahead-anywhere shortcut. Every other clause
  (grouped dot-points, diagram lean, OPEN QUESTIONS ending, no AskUserQuestion in
  the investigation turn, no planning decisions, no depth-gate verdict) is
  restated verbatim — a MODIFIED delta replaces the whole requirement by `id`.
- **`shared-understanding-summary` (MODIFIED).** Reframed around the single-
  approval model: on a clean gate the skill emits on the affirmative alone with
  no summary/emit checkpoint; only when the depth gate needs more info and the
  grill loop runs does the shared-understanding summary + "emit" confirmation
  close the path. This matches the existing fast/depth split — the fast path
  already emits silently — so no code behavior is being invented, only the
  contract is made explicit and tied to the new gate. Rejected: dropping the
  depth-path "emit" confirmation entirely — the grill loop produces decisions the
  initial affirmative never saw, so a final confirmation still earns its keep.
- **Plugin version bump.** The change touches `plugins/s/`, so
  `plugins/s/.claude-plugin/plugin.json` bumps `0.6.19 → 0.6.20` in the same
  PR; without it the cached snapshot keeps running the stale skill.
- **Eval before ship.** A `SKILL.md` edit warrants a local eval run
  (`python3 evals/run.py`) per repo policy; the existing generic proceed reply
  the runner uses already satisfies the new free-text question, so no eval-harness
  change is needed.

Risk: the loop could read as never-ending to a user who keeps talking. Guarded by
the affirmative being the sole exit and the one-line delta each round keeping the
user oriented on what changed.
