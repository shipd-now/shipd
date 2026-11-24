# codebase-first-shared — shipd-plan delta

## ADDED Requirements

### Requirement: Enrichment mode lives in its own reference
id: enrichment-reference

`plugins/s/skills/plan/references/enrichment.md` SHALL hold the enrichment
loop and its re-gate exit, and `plan/SKILL.md` SHALL keep the `locate` branch
and, on a `rejected` change, point at that file instead of carrying the loop.
The reference SHALL NOT be listed in `plugins/s/external-loaders.json`, because
only `/s:plan` reads it.

#### Scenario: The skill points at the reference
- **WHEN** `plan/SKILL.md` is read
- **THEN** it names `references/enrichment.md` for a `rejected` change and carries no enrichment loop steps

#### Scenario: The reference carries the loop and the re-gate
- **WHEN** `enrichment.md` is read
- **THEN** it has the loop that resolves the `## Context insufficient` findings and the re-gate exit

## MODIFIED Requirements

### Requirement: Codebase-first investigation
id: codebase-first-investigation
base: a86bb7d1e772

Before asking the user anything, the skill SHALL investigate the repository —
existing `.shipd/verified/` capabilities, relevant code, and the user's request —
and SHALL NOT ask the user any question whose answer is discoverable from the
repo or the request. The rule itself SHALL live in `## Codebase first` of
`plugins/s/skills/ask/references/headless.md`; the skill's `Codebase-first rule`
section SHALL keep its heading, point at that part, and state its interactive
application.

#### Scenario: Discoverable facts are not asked
- **WHEN** the affected module and its existing patterns are identifiable from
  the codebase
- **THEN** the skill reads them directly and asks the user nothing about them

#### Scenario: The skill points at the shared rule
- **WHEN** the skill's `Codebase-first rule` section is read
- **THEN** it points at `## Codebase first` in `headless.md` instead of restating the rule
