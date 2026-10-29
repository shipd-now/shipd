## ADDED Requirements

### Requirement: Harness-neutral skill prose
id: harness-neutral-skill-prose

The prose of every markdown file under `plugins/s/skills/` and
`plugins/s/harness/` SHALL NOT name a specific harness with the word
`Claude`, except in a file listed as platform-specific. Working invocations
and runtime variables, such as `${CLAUDE_PLUGIN_ROOT}` and `claude -p`, MAY
stay. A stdlib test in the engine suite SHALL scan those files line by line
for the case-sensitive word `Claude` and SHALL fail with the offending
`path:line` on any match outside the allowlist.

#### Scenario: A prose mention fails the guard
- **GIVEN** a SKILL.md line reading "is in Claude Code plan mode"
- **WHEN** the harness-neutral prose test runs
- **THEN** it fails and names that file and line

#### Scenario: Working tokens pass the guard
- **GIVEN** a SKILL.md line carrying `${CLAUDE_PLUGIN_ROOT}` or
  `claude plugin update s@shipd`
- **WHEN** the harness-neutral prose test runs
- **THEN** that line raises no failure

#### Scenario: The shipped skills pass the guard
- **WHEN** the harness-neutral prose test runs on the repository
- **THEN** it passes

## MODIFIED Requirements

### Requirement: Harness plan mode guard
id: harness-plan-mode-guard
base: a7bb83941c2d

Harness plan mode SHALL NOT replace a shipd skill's output. When a session
is in the harness's plan mode, a writing skill SHALL run only its read-only
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
