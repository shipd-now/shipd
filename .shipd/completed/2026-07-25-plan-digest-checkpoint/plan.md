# plan-digest-checkpoint
Status: verified

## Idea

The 0.2.10/0.2.11 hardening of `/s:plan` (mandatory findings digest, context
brief as a question-call precondition, version stamp) did not survive contact
with a real session: the transcript of the latest failing run shows the
0.2.11 SKILL.md fully delivered, the model even reading `plugin.json` as its
first action per the version-stamp rule — and **zero text blocks in the
entire session**. The planner streaked from tool call to tool call straight
into AskUserQuestion, never surfacing any prose. "Write visible text before
calling X" mandates fail *passively*: nothing forces the text out.

The fix inverts the failure mode so that violating the contract requires an
action rather than an inaction: **the investigation turn may not contain an
AskUserQuestion call at all.** The findings digest (plus any requested
diagram) is the turn's final message — a hard checkpoint. The user reads what
was found, can redirect scope, and says go; the depth gate and any question
rounds happen in later turns. A turn boundary forces the text to render, and
"do not call X this turn" is a checkable prohibition the model reliably
honors, unlike "write prose first".

### Non-goals

- No change to the brief contract inside later question rounds, the depth
  gate signals, the grill loop, readiness, or emission.
- No hooks or engine enforcement — this stays a skill-text contract, but one
  whose violation is an active call rather than missing prose.
- No removal of the version stamp or the missing-layout guard.

Affected capabilities: `shipd-plan` (modified — `investigation-findings-digest`).
Impact: `plugins/s/skills/plan/SKILL.md`,
`plugins/s/.claude-plugin/plugin.json`.

## Implementation

- **Flow step 2 becomes "Report findings and stop."** The digest (affected
  files/capabilities, existing behavior and patterns, anything surprising,
  plus the solution diagram whenever the user asked for one) is the final
  message of the investigation turn. The step states the prohibition
  explicitly: no AskUserQuestion call and no depth-gate verdict in the same
  turn as investigation — end the turn and wait for the user's go-ahead.
  Rejected: keeping "print the digest, then ask in the same turn" — that is
  the arrangement the transcript just proved a model can silently skip.
- **Step 3 (depth gate) runs on the go-ahead turn**, folding in anything the
  user's go-ahead message changed about scope before classifying.
- **The delta modifies `investigation-findings-digest`** to carry the
  checkpoint: digest ends the turn; the same turn SHALL NOT contain an
  AskUserQuestion call; the gate verdict and question rounds follow in later
  turns after the user responds.
- **Version bump to 0.2.12** in `plugins/s/.claude-plugin/plugin.json`, same
  PR, per the cache-snapshot rule in AGENTS.md.

Risks: one extra user round-trip per plan session — accepted deliberately;
the checkpoint is the interaction the user asked for ("do some examining,
then show me what it found"). If a model somehow ends the investigation turn
with no text at all, the checkpoint still stops it from reaching the question
dialog unbriefed — the failure becomes visible silence rather than an
unexplained interrogation.
