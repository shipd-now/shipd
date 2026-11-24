# plan-readiness-reference — shipd-plan delta

## ADDED Requirements

### Requirement: Plan readiness rules live in one engine-neutral reference
id: plan-readiness-reference

`plugins/s/skills/plan/references/readiness-rules.md` SHALL hold the plan
readiness rules once, under exactly eight `##` headings in this order: Problem
and motivation, Scope and non-goals, Affected capabilities and files, No open
task-shaping decision, The gate, Attestation, Self-review, Stop when ready. It
SHALL be prose only, carrying no code fence, no engine command, no
`${CLAUDE_PLUGIN_ROOT}` path, and no interactive step. Its Affected
capabilities and files part SHALL carry the runnable-premise rule with both
exemptions, and SHALL tell an engine that cannot run commands to cite the
implementing lines, state that the premise is unrun, and make the first
dependent task run the command. `readiness.md`, `plan/SKILL.md`, and
`emission.md` SHALL point at these headings in place of restating the rules.

#### Scenario: The reference carries the eight headings
- **WHEN** the `##` headings of `readiness-rules.md` are listed
- **THEN** they are the eight names above, in that order

#### Scenario: The reference is prose only
- **WHEN** `readiness-rules.md` is searched for a code fence or the plugin-root variable
- **THEN** neither appears

#### Scenario: An engine that cannot run commands defers the run
- **WHEN** the Affected capabilities and files part is read
- **THEN** it tells such an engine to state the premise is unrun and make the first dependent task run the command

## MODIFIED Requirements

### Requirement: Premise evidence appears in the readiness attestation
id: premise-evidence-in-attestation
base: 53f66fe30c85

The readiness checklist SHALL carry the runnable-premise rule as evidence
under its affected-capabilities-and-files item rather than as an additional
checklist item, so the four items are unchanged in number. The checklist
SHALL name `readiness-rules.md` as the home of that rule. The emitted
`plan.md`'s `## Readiness attestation` section SHALL name each verified
premise with its invocation and its observed output or exit code under that
item's evidence; the printed attestation SHALL summarize premises in plain
language without reproducing the invocations.

#### Scenario: The checklist keeps four items
- **WHEN** the readiness checklist is read after this change
- **THEN** it still gates on exactly four items

#### Scenario: The checklist names the reference
- **WHEN** `readiness.md` is read for the four items
- **THEN** each points at its heading in `readiness-rules.md`

#### Scenario: The observation lands in the section
- **GIVEN** a plan that verified a runnable premise
- **WHEN** the change is emitted
- **THEN** the `## Readiness attestation` section names the premise's
  invocation and what running it showed
