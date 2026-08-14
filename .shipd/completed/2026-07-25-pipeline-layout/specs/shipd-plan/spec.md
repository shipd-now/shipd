## MODIFIED Requirements

### Requirement: Codebase-first investigation
id: codebase-first-investigation
base: 2b4eda2320ef

Before asking the user anything, the skill SHALL investigate the repository —
existing `am/verified/` capabilities, relevant code, and the user's request —
and SHALL NOT ask the user any question whose answer is discoverable from the
repo or the request.

#### Scenario: Discoverable facts are not asked
- **WHEN** the affected module and its existing patterns are identifiable from
  the codebase
- **THEN** the skill reads them directly and asks the user nothing about them

### Requirement: Silent lean-artifact emission
id: silent-lean-emission
base: ec63f5c2a965

On readiness, the skill SHALL author the lean artifact set — a single
`plan.md` whose `## Idea` section carries the motivation, scope, capabilities,
and impact and whose `## Implementation` section carries the binding technical
decisions; delta specs carrying `id:` slugs and `base:` hashes; and a separate
`tasks.md` — under `am/planned/<change>/`, as an internal step with no
separate user-facing spec skill. When `am/constitution.md` is present,
the emitted artifacts SHALL honor its rules. Emitted tasks SHALL be small,
independently-executable, and name their target files, so a lower-tier
execution agent can run them without architectural judgment.

#### Scenario: Lean artifact set is emitted in one step
- **WHEN** the readiness gate passes
- **THEN** `am/planned/<change>/` contains a `plan.md` with `## Idea` and
  `## Implementation` sections, at least one delta spec with `id:` slugs, and
  a tasks checklist, produced without invoking any separate exposed skill

#### Scenario: No standalone proposal or design files
- **WHEN** emission completes
- **THEN** the change directory contains no `proposal.md` and no `design.md`
