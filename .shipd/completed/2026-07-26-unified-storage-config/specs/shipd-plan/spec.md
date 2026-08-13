## MODIFIED Requirements

### Requirement: Silent lean-artifact emission
id: silent-lean-emission
base: 2b2b8edd9848

On readiness, the skill SHALL author the lean artifact set — a single
`plan.md` whose `## Idea` section carries the motivation, scope,
capabilities, and impact and whose `## Implementation` section carries the
binding technical decisions; delta specs carrying `id:` slugs and `base:`
hashes; and a separate `tasks.md` — in a staging area, and SHALL install it
through `spec_emit.py change <name> --from <staging>`, never writing into
the spec tree directly or constructing its path. When a constitution
document is present, the emitted artifacts SHALL honor its rules. Emitted
tasks SHALL be small, independently-executable, and name their target files;
each task SHALL carry a `[req: ...]` traceability tag per the tasks format;
and where a task has a testable surface, the task list SHALL sequence the
failing test before the implementation that makes it pass.

#### Scenario: Emission installs through the engine
- **WHEN** the readiness gate passes
- **THEN** the staged artifacts are installed via `spec_emit.py change`,
  and the resolved `planned/<change>/` contains `plan.md` with `## Idea`
  and `## Implementation` sections, at least one delta spec, and a tasks
  checklist

#### Scenario: Rejected emission never lands
- **WHEN** the staged artifacts carry a lint error at install time
- **THEN** `spec_emit.py` reports the findings and the spec tree gains no
  change directory

#### Scenario: Emitted tasks carry traceability tags
- **WHEN** the task list is emitted
- **THEN** every task names the delta requirement(s) it implements via a
  `[req: ...]` tag (or a lone wildcard for whole-change tasks)

### Requirement: Missing-layout guard
id: missing-layout-guard
base: 305b24cbc77f

When the repository lacks the resolved content-directory layout, the skill
SHALL stop before any questioning, report the missing layout, and ask via
one AskUserQuestion whether to scaffold the minimal layout (`verified/`,
`planned/`, `completed/` under the resolved content directory, default
`.shipd/`) and continue, or stop; it SHALL NOT continue planning as though the
layout existed.

#### Scenario: Missing layout stops the flow
- **WHEN** `/s:plan` runs in a repository with no resolved content
  directory
- **THEN** the skill reports the missing layout and asks scaffold-or-stop
  before any planning question is posed

#### Scenario: Accepted scaffold proceeds
- **WHEN** the user accepts the scaffold option
- **THEN** the skill creates the three empty directories under the resolved
  content directory and continues the normal flow
