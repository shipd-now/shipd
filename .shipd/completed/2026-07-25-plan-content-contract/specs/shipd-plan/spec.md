# shipd-plan — delta

## ADDED Requirements

### Requirement: Self-review before the lint gate
id: emission-self-review

After authoring the artifacts and before running the linter, the plan flow
SHALL re-read the drafted `plan.md`, delta specs, and `tasks.md` looking for
placeholders, internal contradictions, and decisions left unresolved for the
executor, and SHALL fix what it finds before proceeding to lint. The lint
gate checks structure; this pass checks sense.

#### Scenario: Placeholder is caught before lint
- **WHEN** the drafted artifacts contain a placeholder or a task that would
  force the executor to choose an approach
- **THEN** the plan flow resolves it during self-review, before the linter
  runs

## MODIFIED Requirements

### Requirement: Silent lean-artifact emission
id: silent-lean-emission
base: 8dc4d2286064

On readiness, the skill SHALL author the lean artifact set — a single
`plan.md` whose `## Idea` section carries the motivation, scope, capabilities,
and impact and whose `## Implementation` section carries the binding technical
decisions; delta specs carrying `id:` slugs and `base:` hashes; and a separate
`tasks.md` — under `am/planned/<change>/`, as an internal step with no
separate user-facing spec skill. When `am/constitution.md` is present,
the emitted artifacts SHALL honor its rules. Emitted tasks SHALL be small,
independently-executable, and name their target files, so a lower-tier
execution agent can run them without architectural judgment; and where a task
has a testable surface, the task list SHALL sequence the failing test before
the implementation that makes it pass.

#### Scenario: Lean artifact set is emitted in one step
- **WHEN** the readiness gate passes
- **THEN** `am/planned/<change>/` contains a `plan.md` with `## Idea` and
  `## Implementation` sections, at least one delta spec with `id:` slugs, and
  a tasks checklist, produced without invoking any separate exposed skill

#### Scenario: No standalone proposal or design files
- **WHEN** emission completes
- **THEN** the change directory contains no `proposal.md` and no `design.md`

#### Scenario: Tests precede implementation in the task order
- **WHEN** a change's tasks cover a behavior with a testable surface
- **THEN** the emitted task list places the failing-test task before the
  implementation task it validates
