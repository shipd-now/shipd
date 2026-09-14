# semantic-review

## ADDED Requirements

### Requirement: Skill reference loading
id: review-skill-references

The `/s:review` skill SHALL carry its condition-gated guidance in reference
files under `plugins/s/skills/review/references/` rather than inline in its
`SKILL.md`, and `SKILL.md` SHALL name every file in that directory by its
`${CLAUDE_PLUGIN_ROOT}` path beside the condition under which the skill reads
it. The spec-aware verification guidance, the `--json` machine output guidance,
and the PR posting guidance SHALL each occupy one such file, read only when a
planned change is in scope, when `--json` is requested, and when posting is
explicitly requested, respectively.

Guidance that runs on every review SHALL stay inline in `SKILL.md`: the
workflow steps, the severity rubric, the presentation shape, the review-start
difftastic probe and its degradation ladder, and the guardrails. `SKILL.md`
SHALL stay under 300 lines.

Each reference file SHALL open with a level-1 title and state its own load
condition, so a file read on its own explains why it was read. Moving guidance
into a reference SHALL NOT change that guidance's substance.

#### Scenario: Every reference is reachable from the skill
- **WHEN** `plugins/s/skills/review/SKILL.md` is inspected
- **THEN** it names every file under `plugins/s/skills/review/references/` by
  path, and every reference path it names resolves to an existing file

#### Scenario: Conditional guidance left the skill body
- **WHEN** `plugins/s/skills/review/SKILL.md` is inspected
- **THEN** it carries no `## Machine output mode`, `## Posting to a PR`, or
  `## Spec-aware review` section, and the three reference files carry that
  guidance instead

#### Scenario: Hot-path guidance stayed inline
- **WHEN** `plugins/s/skills/review/SKILL.md` is inspected
- **THEN** the workflow steps, the high/medium/low severity rubric, and the
  `command -v difft` probe are present in the file itself, behind no reference

#### Scenario: The skill body fits the ceiling
- **WHEN** `plugins/s/skills/review/SKILL.md` is measured
- **THEN** it is under 300 lines

#### Scenario: A reference states its own trigger
- **WHEN** a file under `plugins/s/skills/review/references/` is read on its own
- **THEN** its opening lines give a level-1 title and the condition under which
  the skill loads it

#### Scenario: The other rubric surfaces are untouched
- **WHEN** `plugins/s/integrations/copilot/SKILL.md` and
  `plugins/s/harness/bodies/review.md` are inspected
- **THEN** neither references a file under `plugins/s/skills/review/references/`,
  since neither runs where `${CLAUDE_PLUGIN_ROOT}` resolves
