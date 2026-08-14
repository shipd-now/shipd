# shipd-plan — delta

## MODIFIED Requirements

### Requirement: Silent lean-artifact emission
id: silent-full-ceremony-emission
base: 438a5001d768

On readiness, the skill SHALL author the lean artifact set — a single
`plan.md` whose `## Idea` section carries the motivation, scope, capabilities,
and impact and whose `## Implementation` section carries the binding technical
decisions; delta specs carrying `id:` slugs and `base:` hashes; and a separate
`tasks.md` — under `am/spec/changes/<change>/`, as an internal step with no
separate user-facing spec skill. When `am/spec/constitution.md` is present,
the emitted artifacts SHALL honor its rules. Emitted tasks SHALL be small,
independently-executable, and name their target files, so a lower-tier
execution agent can run them without architectural judgment.

#### Scenario: Lean artifact set is emitted in one step
- **WHEN** the readiness gate passes
- **THEN** `am/spec/changes/<change>/` contains a `plan.md` with `## Idea` and
  `## Implementation` sections, at least one delta spec with `id:` slugs, and
  a tasks checklist, produced without invoking any separate exposed skill

#### Scenario: No standalone proposal or design files
- **WHEN** emission completes
- **THEN** the change directory contains no `proposal.md` and no `design.md`

### Requirement: Emission carries the status header
id: emission-carries-status-header
base: 39461c960768

The plan flow SHALL emit every `plan.md` with the `# <change-name>` title and
`Status: draft` header, and SHALL promote the status to `ready` when the
emitted change is lint-clean and the user has approved the plan.

#### Scenario: Fresh emission is draft
- **WHEN** plan emits a change's artifacts
- **THEN** the `plan.md` begins with the title and `Status: draft`

#### Scenario: Approval promotes to ready
- **WHEN** the emitted change lints clean and the user approves
- **THEN** the plan's status line reads `Status: ready` before hand-off to
  execution
