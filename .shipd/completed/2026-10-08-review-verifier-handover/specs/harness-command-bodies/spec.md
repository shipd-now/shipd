## MODIFIED Requirements

### Requirement: Distilled router content
id: body-content
base: 76cee50670c0

Every body template SHALL be a distilled router for its command — a lean
imperative workflow driving the `shipd` CLI's read verbs and, for
lifecycle mutations, the engine scripts through the preamble's
snapshot-resolution snippet — and SHALL NOT reproduce its SKILL.md
verbatim. The shared preamble SHALL define the engine-scripts resolution
(newest plugin cache snapshot by dotted-version order). Each rendered body
(any feature set) SHALL stay under 200 lines. This capability owns that
number: a surface that states a rendered-body size budget SHALL reference
this requirement rather than restating the figure, so the budget has one
source of truth. The ceiling guards against bloat and is not a budget to
compress real instructions into — where a body legitimately grows a step,
the ceiling rises rather than its instructions being reworded to fit.

#### Scenario: Preamble resolves the newest snapshot
- **WHEN** the preamble's resolution snippet runs in a shell against a fake
  cache root holding `0.6.9` and `0.6.10`
- **THEN** the resolved scripts path is under `0.6.10`

#### Scenario: Bodies stay lean
- **WHEN** every command is rendered with the full feature vocabulary
- **THEN** every rendered body is under 200 lines

#### Scenario: Bodies drive the CLI, not pasted skills
- **WHEN** the plan command's rendered body is inspected
- **THEN** it invokes `spec_emit.py` and `spec_gate.py` via the preamble's
  scripts variable and is not byte-identical to any portion of
  `plugins/s/skills/plan/SKILL.md` exceeding 10 consecutive lines
