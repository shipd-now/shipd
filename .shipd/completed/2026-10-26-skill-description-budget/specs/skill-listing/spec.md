## ADDED Requirements

### Requirement: Every skill description fits a per-skill budget
id: skill-description-budget

Every `plugins/s/skills/*/SKILL.md` SHALL declare a frontmatter
`description` whose text, after YAML folding joins its lines with single
spaces, is at most 300 characters. The constant SHALL live once, as
`DESCRIPTION_BUDGET = 300` in
`plugins/s/skills/build/tests/test_skill_descriptions.py`, and that test SHALL
fail naming each skill over the budget with its length, so
`python3 -m unittest discover -s plugins/s/skills/build/tests` enforces the
budget in CI.

#### Scenario: Every shipped description is within budget
- **WHEN** the build test suite runs against the checkout
- **THEN** every skill's folded `description` is at most 300 characters and
  the test passes

#### Scenario: A grown description fails and is named
- **WHEN** a skill's folded `description` grows to 301 characters
- **THEN** the test fails and its message names that skill and 301

### Requirement: A description is the body one-liner plus its trigger phrases
id: skill-description-shape

Every skill's folded `description` SHALL equal the one-line description its
harness body template declares (`harness_bodies.description(<name>)`),
followed by a single space, the text `Trigger phrases: `, one or more
double-quoted phrases separated by `, `, and a closing `.`. One of those
phrases SHALL be `/s:<name>`. The frontmatter SHALL keep the folded
`description: >-` block style, so the colon in `Trigger phrases:` never
reaches a plain YAML scalar. The test SHALL fail naming each skill whose
description does not match this shape.

#### Scenario: Description starts with the body one-liner
- **WHEN** the test reads `plugins/s/skills/plan/SKILL.md`
- **THEN** its folded `description` starts with the `<!-- description: ... -->`
  text of `plugins/s/harness/bodies/plan.md` and ends with a
  `Trigger phrases:` clause that includes `"/s:plan"`

#### Scenario: A drifted one-liner fails
- **WHEN** a body template's one-liner changes and its skill's description
  does not
- **THEN** the test fails and names that skill

### Requirement: Trimming keeps every trigger phrase
id: skill-trigger-phrases-kept

The trimmed description of every skill SHALL contain, in its
`Trigger phrases:` clause, every phrase that skill's description declared
under `Trigger phrases:` before this change, with no phrase dropped and none
reworded. `"record a demo"` SHALL stay declared by `demo` alone.

#### Scenario: Phrase sets match main
- **WHEN** each skill's trigger phrases after the change are compared with
  the phrases its description declared on `main` before the change
- **THEN** the two sets are equal for all 31 skills
