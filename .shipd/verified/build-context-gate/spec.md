# build-context-gate

### Requirement: Context sufficiency evaluation
id: context-sufficiency-evaluation

Before authoring any spec artifacts, `/s:build` SHALL evaluate the request
against the plan readiness checklist (problem clear; scope and non-goals
bounded; affected capabilities/files identified; no open decision that changes
the task list). If a linted change for the request already exists under
`am/planned/`, build SHALL use it and skip planning entirely.

#### Scenario: Rich context proceeds directly
- **WHEN** the user's request plus the repository satisfy the readiness
  checklist
- **THEN** build proceeds to spec authoring without invoking the plan flow or
  asking the user anything

#### Scenario: Existing change short-circuits the gate
- **WHEN** a linted change matching the request already exists
- **THEN** build proceeds straight to execution phases against that change

### Requirement: Automatic hand-off to the plan flow
id: automatic-hand-off-to-the-plan-flow

When the readiness checklist is not met, build SHALL invoke the `am:plan` flow —
including its codebase-first investigation and batched AskUserQuestion
contract — and SHALL NOT begin spec authoring or spawn sub-agents until the plan
flow emits a linted change.

#### Scenario: Insufficient context triggers planning
- **WHEN** the request leaves an open decision that would change the task list
- **THEN** build enters the plan flow, which investigates and asks the batched
  questions, before any spec artifact is authored

### Requirement: Gate hand-off preserves answers
id: gate-hand-off-preserves-answers

When the plan flow completes, build SHALL continue from its emitted artifacts
without re-asking anything the user already answered and without re-running
investigation the plan flow already performed.

#### Scenario: No repeated questions after planning
- **WHEN** the plan flow asked the user questions and emitted a linted change
- **THEN** the subsequent build phases consume those artifacts directly and ask
  none of those questions again

### Requirement: Supersession gate on adopted changes
id: supersession-gate

When the Phase 0 short-circuit adopts an existing linted change, `/s:build`
SHALL run the status CLI's `check-base` verb against that change before any
execution phase begins. When the verb reports findings, build SHALL read the
affected masters and recent base-branch history to classify the mismatch:
content drift SHALL proceed with the findings carried into the plan review,
while a plan whose substance is already merged on the base branch SHALL stop
the build and ask the user whether to abandon or re-scope — build SHALL NOT
spawn execution sub-agents on a superseded plan. A clean report SHALL proceed
without user interaction.

#### Scenario: Clean check proceeds silently
- **GIVEN** an adopted planned change whose `check-base` run reports no
  findings
- **WHEN** Phase 0 completes
- **THEN** build proceeds to execution without asking the user anything about
  supersession

#### Scenario: Findings force a classification before execution
- **GIVEN** an adopted change whose `check-base` run reports `stale-base`
  findings caused by unrelated master drift
- **WHEN** build classifies the findings against the masters and recent
  base-branch history
- **THEN** build proceeds, carrying the findings into the plan review rather
  than executing blindly past them

#### Scenario: Superseded plan stops the build
- **GIVEN** an adopted change whose substance an already-merged PR has
  implemented, with `check-base` reporting collisions or stale bases
- **WHEN** build classifies the findings
- **THEN** no execution sub-agent is spawned and the user is asked whether to
  abandon or re-scope the change
