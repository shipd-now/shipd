# reword-plan-gate
Status: verified
Theme: developer-experience

## Idea

Reword the `/s:plan` "no open questions" go-ahead gate from the neutral
"Shall we proceed with the plan?" to the readiness-asserting "We have enough
details — shall I write the plan now?".

### Motivation

The neutral "Shall we proceed with the plan?" hides the signal the user needs:
whether investigation actually reached enough context to write the spec. A
prompt that asserts readiness communicates the flow's state and makes the
go-ahead a clearer decision.

### Details

- Replace every occurrence of the literal "Shall we proceed with the plan?"
  with "We have enough details — shall I write the plan now?" across the
  `shipd-plan` capability's prose surfaces: `plan/SKILL.md` (the digest's
  go-ahead ending, its re-ask, and the depth-gate trigger reference),
  `plan/references/dialogue.md`, and — via the delta — the two `shipd-plan`
  requirements `investigation-findings-digest` and
  `shared-understanding-summary`.
- Add a guard clause making explicit that this readiness-asserting go-ahead
  is printed only when no genuinely open task-shaping question remains; while
  one does, the turn takes the `OPEN QUESTIONS` ending instead of asserting
  readiness.
- Bump the plugin version so the cached snapshot picks up the reworded skill.

Affected capabilities: `shipd-plan` (modified). Impact:
`plugins/s/skills/plan/SKILL.md`,
`plugins/s/skills/plan/references/dialogue.md`,
`plugins/s/.claude-plugin/plugin.json`; the delta merge propagates the new
literal into `.shipd/verified/shipd-plan/spec.md`. No engine code, no new
dependencies.

### Non-goals

- No change to the two-ending structure, the go-ahead loop, the depth gate, or
  the in-line-go-ahead shortcut — only the literal and one guard clause.
- No change to the depth path's separate "emit" confirmation.
- No new eval case; the existing plan evals cover the flow.

## Implementation

- The literal lives in four prose surfaces that must move together: keeping
  them in sync is the whole task. `SKILL.md` carries it three times (the
  digest ending, the re-ask inside the go-ahead loop, and the depth-gate
  trigger reference "when the user affirms …"); `dialogue.md` once (the
  "sole approval for a clean gate" sentence); the spec twice (the bodies and
  scenarios of `investigation-findings-digest` and
  `shared-understanding-summary`).
- The new phrasing makes a positive factual claim ("We have enough details"),
  so its honesty matters. The two investigation-turn endings are already
  mutually exclusive, but add one explicit guard clause to
  `investigation-findings-digest` (and mirror it in `SKILL.md`): the
  readiness-asserting go-ahead SHALL be presented only when no open
  task-shaping question remains; whenever one does, the turn SHALL take the
  `OPEN QUESTIONS` ending. This prevents a false readiness assertion.
- The spec master is updated by the delta merge at completion, not by hand —
  the delta MODIFIES both requirements against their current base hashes
  (`investigation-findings-digest` 665e243a9c6c,
  `shared-understanding-summary` 2853d6a936a4). Only the plain files
  (`SKILL.md`, `dialogue.md`, `plugin.json`) are edited directly.

Risk: a stale copy of the literal left in one surface reads as a contradiction
between the skill and its spec; guard by grepping for the old string after the
edits and confirming zero hits outside archived `.shipd/completed/` history.
