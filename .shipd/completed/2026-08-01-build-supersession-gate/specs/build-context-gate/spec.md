## ADDED Requirements

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
