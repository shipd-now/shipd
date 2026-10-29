# shipd-interaction

### Requirement: Dialog and prose separation
id: dialog-prose-separation

The harness can drop or hide assistant text that shares a turn with an
AskUserQuestion call, so a turn that issues an AskUserQuestion SHALL carry no
load-bearing prose outside the dialog — at most a one-line lead-in. An
AskUserQuestion dialog SHALL carry exactly one question, and only when that
question's brief fits in its question text and option descriptions. A round
of more than one question, or a question whose brief runs past one line,
SHALL end its turn as plain text with the briefs and a numbered list of
choices, the recommended default named, and the answer collected as a typed
reply.

#### Scenario: Substantive prose ends the turn as plain text
- **WHEN** a skill must present an explanation, brief, or lesson and then
  collect a decision
- **THEN** the explanation and a numbered plain-text prompt form one
  message answered by typing, and no AskUserQuestion is issued in that turn

#### Scenario: Dialogs appear only in prose-free turns
- **WHEN** a skill issues an AskUserQuestion
- **THEN** the turn's visible text outside the dialog is at most a one-line
  lead-in, with all decision context inside the dialog's fields

#### Scenario: Several questions take a typed round
- **WHEN** a skill has two or more decisions to ask in one round
- **THEN** it asks them as one numbered typed round with a brief per
  question, and issues no AskUserQuestion

### Requirement: Question brief
id: question-brief

Every question a shipd skill puts to the user SHALL open with a brief in
four parts, in order: the decision stated in plain words; why it matters,
naming what the feature does and what the answer changes; one concrete
example, left out only when the decision has no concrete instance; and the
options, the recommended one first and marked recommended, each saying what
choosing it causes. The reference
`plugins/s/skills/document/references/question-brief.md` SHALL define the
brief with worked examples, and SHALL carry the `reference` doc-type marker.
Every `plugins/s/skills/*/SKILL.md` that mentions `AskUserQuestion`, and the
harness body of each such skill, SHALL point to that reference by path.

#### Scenario: A grill question carries its brief
- **WHEN** the epic-grill final round asks which `--state` a `--task`
  reply defaults to
- **THEN** the question states what `shipd room message --task` does, what
  the default changes, shows one example command, and lists the options
  with the recommended one first

#### Scenario: Every asking skill points to the reference
- **WHEN** a SKILL.md mentions `AskUserQuestion`
- **THEN** it and its harness body contain
  `skills/document/references/question-brief.md`

### Requirement: Harness plan mode guard
id: harness-plan-mode-guard

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

### Requirement: No question rejection workaround
id: no-question-rejection-workaround

The markdown under `plugins/s/skills/` and `plugins/s/harness/` SHALL NOT
instruct a session to treat a rejected or interrupted question dialog as a
harness misfire. A stdlib test in the engine suite SHALL scan those files for
the case-insensitive phrases `rejection recovery`, `rejection-recovery`, and
`rejected or interrupted`, and SHALL fail naming each `path:line` it finds.

#### Scenario: A reintroduced rule fails the guard
- **GIVEN** a SKILL.md carrying a "Question rejection recovery" section
- **WHEN** the guard test runs
- **THEN** it fails and names that file and line

#### Scenario: The shipped skills pass the guard
- **WHEN** the guard test runs on the repository
- **THEN** it passes
