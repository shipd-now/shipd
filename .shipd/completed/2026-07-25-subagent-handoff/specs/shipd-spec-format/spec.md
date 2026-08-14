## ADDED Requirements

### Requirement: Task traceability tags
id: task-traceability-tags

Every checkbox task in a change's `tasks.md` SHALL carry exactly one
traceability tag of the form `[req: <id>[, <id>...]]`, naming the requirement
id(s) from the change's own delta specs that the task implements or verifies,
or the wildcard form `[req: *]` for tasks that span the whole change (such as
verification barriers). The wildcard SHALL appear alone, never combined with
ids. The tag SHALL sit in the task text after the optional `[P<n>]` parallel
group tag and SHALL NOT affect task coordination.

#### Scenario: Task names its requirement
- **WHEN** a task implements the `export-report-csv` requirement from the
  change's delta specs
- **THEN** its task line carries `[req: export-report-csv]`

#### Scenario: Barrier uses the wildcard
- **WHEN** a verification barrier exercises the whole change
- **THEN** its task line carries `[req: *]` and no other requirement ids

#### Scenario: Tags do not disturb coordination
- **WHEN** a task line carries both `[P2]` and `[req: export-report-csv]`
- **THEN** the coordinator's group parsing behaves exactly as it would with
  the group tag alone
