## MODIFIED Requirements

### Requirement: Silent lean-artifact emission
id: silent-lean-emission
base: 7abd6375f160

On readiness, the skill SHALL author the lean artifact set — a single
`plan.md` whose `## Idea` section carries the motivation, scope, capabilities,
and impact and whose `## Implementation` section carries the binding technical
decisions; delta specs carrying `id:` slugs and `base:` hashes; and a separate
`tasks.md` — under `am/planned/<change>/`, as an internal step with no
separate user-facing spec skill. When `am/constitution.md` is present,
the emitted artifacts SHALL honor its rules. Emitted tasks SHALL be small,
independently-executable, and name their target files, so a lower-tier
execution agent can run them without architectural judgment; each task SHALL
carry a `[req: ...]` traceability tag per the tasks format; and where a task
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

#### Scenario: Emitted tasks carry traceability tags
- **WHEN** the task list is emitted
- **THEN** every task names the delta requirement(s) it implements via a
  `[req: ...]` tag (or a lone wildcard for whole-change tasks)

#### Scenario: Tests precede implementation in the task order
- **WHEN** a change's tasks cover a behavior with a testable surface
- **THEN** the emitted task list places the failing-test task before the
  implementation task it validates
