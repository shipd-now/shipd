# ask-rejection-recovery
Status: verified

## Idea

A confirmed Claude Code defect family (anthropics/claude-code#33511, #65392)
makes the harness deliver some AskUserQuestion interactions — "Chat about
this", Ctrl+O while a dialog is pending, and similar — to the model as a tool
rejection ("The user doesn't want to proceed with this tool use") even though
the user was trying to engage. Every interactive am skill currently reads such
a rejection as the user declining. This killed a live onboarding tour: the
user picked a checkpoint option, the harness delivered a rejection, and the
skill's "Stop means stop" guardrail ended the tour. All six interactive
skills — plan, build, epic, initiative, status, onboard — put decisions
through AskUserQuestion and are equally exposed.

This change hardens the skills at the prose level:

- Add a shared "question rejection recovery" rule to all six interactive
  SKILL.md files: a rejected or interrupted AskUserQuestion is a harness
  misfire, never a user decision.
- Give the onboard tour explicit resume semantics: an interruption resumes at
  the last checkpoint — the tour never restarts and never silently ends.
- Bump the plugin version so the cache snapshot picks up the fix.

### Non-goals

- No fix or workaround inside Claude Code itself — the upstream bug is out of
  this repo's reach.
- No replacement of AskUserQuestion with plain-text prompts: dialogs remain
  the primary interaction; plain text is the fallback after a misfire only.
- No engine/script changes and no changes to the onboarding chapter content
  under `docs/onboarding/`.

Affected capabilities: `shipd-interaction` (added), `shipd-onboard` (modified).
Impact: the six `plugins/s/skills/<skill>/SKILL.md` files and
`plugins/s/.claude-plugin/plugin.json`; no new dependencies.

## Implementation

- **Canonical recovery paragraph**, inserted verbatim into each interactive
  SKILL.md (only the heading level may adapt to the host file):

  > **Question rejection recovery.** A known Claude Code bug can deliver an
  > AskUserQuestion interaction as a tool rejection ("The user doesn't want
  > to proceed with this tool use") even when the user tried to answer.
  > Never treat a rejected or interrupted AskUserQuestion as a decline, a
  > stop, or an answer. When the user's next message arrives: if it answers
  > the pending question, fold it in and continue; otherwise re-offer the
  > same choices as a plain-text numbered list and wait for a typed reply.
  > Only an explicitly selected or typed stop/decline ends the flow.

  Placement: a `## Question rejection recovery` (or `###`, matching the host
  file's structure) section near each skill's question/checkpoint prose;
  onboard's copy lands in its **Guardrails** list. Rejected alternative: a
  shared reference file each skill points at — the rule is four sentences and
  SKILL.md files are self-contained prose; an extra cross-file read costs more
  than the duplication, and the `shipd-interaction` requirement pins the wording
  against drift.
- **Keyed to the rejection signal, not user words.** Recovery triggers only on
  the harness's rejection/interruption of the dialog. A user who explicitly
  selects a Stop option or types a stop is honored immediately — onboard's
  "Stop means stop" guardrail is narrowed to *explicit* stops, not weakened.
- **Onboard resume semantics.** The checkpoint section and guardrails state
  that after any interruption the next user message resumes the tour from the
  last reached checkpoint, re-offering that checkpoint's choices when the
  message does not already answer them; the tour never restarts from chapter
  one because of an interruption.
- **Version bump** at execution time per the cache-snapshot rule: one patch
  above the higher of the worktree's and `origin/main`'s current value
  (expected `0.2.8` → `0.2.9`).
- Risk: recovery prose could make skills ignore genuine declines. Guard: the
  rule fires only on the rejection signal and explicitly reaffirms
  selected/typed stops.
- Risk: six copies of the paragraph drift over time. Accepted: the
  `shipd-interaction` requirement pins the canonical text, and the verification
  task greps all six files for it.
