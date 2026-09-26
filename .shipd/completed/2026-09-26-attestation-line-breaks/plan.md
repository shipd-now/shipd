# attestation-line-breaks
Status: verified

## Idea

Print each readiness attestation statement as its own paragraph, separated by blank lines, so the terminal no longer folds the four into one.

### Motivation

The user reads the readiness attestation on a phone-sized terminal and cannot find where one item ends and the next begins, because the four statements are printed on consecutive lines and the markdown renderer joins them into a single paragraph. The template that produces them, in the plan skill's readiness reference, shows exactly that consecutive-line shape.

### Details

- The readiness reference's "What you print" template and prose separate the four statements, and the closing line, by a blank line each.
- The harness plan body and the harness plan reference say the same in their one-sentence restatements.
- The `readiness-attestation` requirement records the separation and gains a scenario for it.

Affected capabilities: `shipd-plan` (modified). Impact: `plugins/s/skills/plan/references/readiness.md`, `plugins/s/harness/bodies/plan.md`, `plugins/s/harness/references/plan.md`, `plugins/s/.claude-plugin/plugin.json`. No engine code, no new dependencies.

### Non-goals

- No change to the emitted `## Readiness attestation` section of `plan.md`, which already uses level-3 headings.
- No change to the statements' content rules, the closing line, or the no-table and no-citation rules.
- No linter or engine change; the attestation is skill prose.

## Implementation

- **A blank line is the separator.** In `plugins/s/skills/plan/references/readiness.md`, the fenced template under "What you print" places a blank line between each bold statement and before the closing line, and the sentence introducing it says each statement is its own paragraph separated by a blank line so a markdown terminal never folds them together. Rejected: a dash list, because the bold item names already act as headings and a list would indent every statement.
- **The harness surfaces mirror it in one clause.** `plugins/s/harness/bodies/plan.md` step 5 and `plugins/s/harness/references/plan.md`'s "What you print" paragraph each add "each statement on its own paragraph, separated by a blank line" to their existing shape sentence; nothing else in either file changes.
- **The skill itself needs no edit.** `plugins/s/skills/plan/SKILL.md` step 5 already points at the reference for the printed shape.
- **Version.** Bump `plugins/s/.claude-plugin/plugin.json` by one patch level over the value `origin/main` carries when the task runs.

Risk: none beyond prose drift between the three surfaces; the task names all three and the harness renderer tests exercise the body.

## Readiness attestation

### Problem and motivation

The four attestation statements render as one paragraph, so the user cannot scan them.

Evidence:

- The user's screenshot of this session's attestation shows "Scope and non-goals" continuing the previous statement's line.
- `plugins/s/skills/plan/references/readiness.md:77-84`: the template prints the four statements on consecutive lines with no blank line between them.
- Capability `shipd-plan`, requirement `readiness-attestation`: "four plain-language headed statements" with no separation rule.

### Scope and non-goals

The change edits the printed template and its three restatements plus one requirement; the emitted section, linter, and engine stay untouched.

Evidence:

- In scope: `readiness.md:69-84`, `plugins/s/harness/bodies/plan.md:53-60`, `plugins/s/harness/references/plan.md:19-24`.
- Out of scope: `readiness.md:93-145` (what the plan carries) is unchanged; `plugins/s/skills/build/scripts/spec_lint.py` is not edited.

### Affected capabilities and files

One capability and four files are affected, because the shape is defined once and restated twice for harnesses.

Evidence:

- Capability `shipd-plan`: requirement `readiness-attestation` (base 565cc2225aa0, from `spec_status.py base-hash`).
- Files: `plugins/s/skills/plan/references/readiness.md`, `plugins/s/harness/bodies/plan.md`, `plugins/s/harness/references/plan.md`, `plugins/s/.claude-plugin/plugin.json:4`.
- Runnable premise: `grep -rn "Full evidence:" plugins/s` returned the three surfaces above plus `SKILL.md:400`, which points at the reference and states no shape of its own.

### No open task-shaping decision

Every task-shaping decision is settled; none remain.

Evidence:

- Separator (a blank line, not a list): settled by investigation, since a blank line is the paragraph break every markdown renderer honors and the bold names already head each statement.
