## MODIFIED Requirements

### Requirement: Standalone invocation
id: standalone-invocation
base: 8f5c42a0ee78

The skill SHALL be invocable on its own (`/s:plan <request>`), ending after
artifact emission with a hand-off summary and a pointer to build — without
starting any implementation. The hand-off summary SHALL lead with the
change's Motivation (why it is being built), followed by a brief summary of
the Implementation approach, and SHALL NOT enumerate the artifact files
written. The summary SHALL still name the change and where it lives so the
user can act on it.

#### Scenario: Plan without build
- **WHEN** a user invokes `am:plan` directly and the flow completes
- **THEN** the skill summarizes what is being built and stops; no
  implementation work begins

#### Scenario: Summary leads with the why
- **WHEN** the plan flow completes and hands off
- **THEN** the summary opens with the plan's Motivation, follows with the
  Implementation approach, and contains no inventory of the files created

### Requirement: Readiness checklist gate
id: readiness-checklist-gate
base: a6bcf033c4a1

The skill SHALL emit artifacts only when all of the following hold: the
problem statement is clear and the motivation is stateable in at most two
precise sentences grounded in the request and repository context; scope and
non-goals are bounded; the affected capabilities and files are identified;
and no open decision remains that would change the task list. If the
motivation cannot be stated precisely from the available context, then the
skill SHALL treat it as un-inferrable and obtain it from the user before
emission. While any item is unsatisfied, the skill SHALL keep investigating
or ask the user — never emit a speculative spec.

#### Scenario: Open decision blocks emission
- **WHEN** a decision that would change the task list is still unresolved
- **THEN** the skill does not emit artifacts and instead resolves the
  decision by investigation or a batched question

#### Scenario: Ungrounded motivation blocks emission
- **WHEN** the request and repository context do not yield a precise
  motivation for the change
- **THEN** the skill asks the user for the motivation before emitting,
  rather than guessing one
