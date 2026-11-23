# plan-authoring-reference — shipd-plan delta

## ADDED Requirements

### Requirement: Plan authoring rules live in one engine-neutral reference
id: plan-authoring-reference

`plugins/s/skills/plan/references/authoring.md` SHALL hold the plan-authoring
rules once, under exactly eight `##` headings in this order: Motivation,
Non-goals, Implementation decisions, Requirements, Scenarios, Tasks,
Placeholders, Size. It SHALL be prose only, carrying no code fence, no engine
command, no `${CLAUDE_PLUGIN_ROOT}` path, and no interactive step. The Scenarios
part SHALL ask for at least one scenario per requirement, with one concrete WHEN,
an optional GIVEN, and an observable THEN. `emission.md` and `readiness.md` SHALL
point at these headings in place of restating the rules, and `plan/SKILL.md`
SHALL list the file and tell the emit step to follow it.

#### Scenario: The reference carries the eight headings
- **WHEN** the `##` headings of `authoring.md` are listed
- **THEN** they are the eight names above, in that order

#### Scenario: The reference is prose only
- **WHEN** `authoring.md` is searched for a code fence or the plugin-root variable
- **THEN** neither appears

#### Scenario: Emission points at the reference
- **WHEN** `emission.md` is read for the Motivation, Non-goals, task, and size rules
- **THEN** each is a pointer to the matching `authoring.md` heading
