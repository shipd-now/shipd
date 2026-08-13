## MODIFIED Requirements

### Requirement: Context sufficiency evaluation
id: context-sufficiency-evaluation
base: 029b0cdeece8

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
