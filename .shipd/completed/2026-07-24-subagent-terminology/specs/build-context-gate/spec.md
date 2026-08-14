# build-context-gate — delta

## MODIFIED Requirements

### Requirement: Automatic hand-off to the plan flow
id: automatic-hand-off-to-the-plan-flow
base: f956e16fff35
When the readiness checklist is not met, build SHALL invoke the `am:plan` flow —
including its codebase-first investigation and batched AskUserQuestion
contract — and SHALL NOT begin spec authoring or spawn sub-agents until the plan
flow emits a linted change.

#### Scenario: Insufficient context triggers planning
- **WHEN** the request leaves an open decision that would change the task list
- **THEN** build enters the plan flow, which investigates and asks the batched
  questions, before any spec artifact is authored
