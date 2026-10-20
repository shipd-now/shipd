# shipd-interaction

## ADDED Requirements

### Requirement: Harness plan mode guard
id: harness-plan-mode-guard

Harness plan mode SHALL NOT replace a shipd skill's output. When a session
is in Claude Code plan mode, a writing skill SHALL run only its read-only
steps, SHALL stop before its first write, and SHALL ask the user to exit
plan mode and re-invoke it. A writing skill SHALL NOT write the harness
plan file, SHALL NOT call `ExitPlanMode`, and SHALL NOT substitute plan
mode's outputs for its own. Every `plugins/s/skills/*/SKILL.md` except the
read-only skills `duck`, `drift`, `explain`, `memory`, and `review` SHALL
carry the sentence "Harness plan mode never replaces this skill's output."
and SHALL point to
`plugins/s/skills/document/references/harness-plan-mode.md`. That
reference SHALL carry the `reference` doc-type marker. The plan skill's
"What still stops the flow" list SHALL name harness plan mode.

#### Scenario: Plan under plan mode stops after its findings
- **WHEN** `/s:plan` runs in a session that is in plan mode
- **THEN** it creates no worktree, prints its findings digest, spawns no
  oracle, and ends by asking the user to exit plan mode and re-run it

#### Scenario: No hybrid run
- **WHEN** any writing skill runs under plan mode
- **THEN** it writes no harness plan file and never calls `ExitPlanMode`

#### Scenario: Every writing skill carries the clause
- **WHEN** the SKILL.md files outside the five read-only skills are
  inspected
- **THEN** each contains the clause sentence and the reference path

#### Scenario: Read-only skills run unchanged
- **WHEN** the `duck`, `drift`, `explain`, `memory`, and `review` SKILL.md
  files are inspected
- **THEN** none contains the clause sentence
