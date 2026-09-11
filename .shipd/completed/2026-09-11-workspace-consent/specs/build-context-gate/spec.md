## ADDED Requirements

### Requirement: Workspace member materialization gate
id: workspace-member-materialization-gate

Where `/s:build` runs inside a discoverable workspace and resolves its
target to a declared member repo whose checkout is neither present nor
mapped — the member's `workspace-sync --json` record carries an executable
action — build SHALL ask the user one question before touching anything:
materialize the member by executing that record's advisory command exactly
as printed, map an existing checkout by driving `workspace-map set` with a
user-supplied path, or stop. Build SHALL never execute a materialization
command without that consent, and after a consented materialization or
mapping SHALL continue the flow from inside the resolved checkout. Where
the target checkout is present or mapped, or no workspace is discoverable,
the gate SHALL ask nothing and behavior SHALL be unchanged.

#### Scenario: Absent member asks before pulling

- **GIVEN** a build invocation from a workspace whose registry declares the
  target repo and no checkout of it exists
- **WHEN** build's context gate runs
- **THEN** the user is asked to materialize, map, or stop before any git
  command runs

#### Scenario: Consented pull continues inside the checkout

- **GIVEN** the gate's question answered with materialize
- **WHEN** the member's advisory command succeeds
- **THEN** build continues its flow from inside the materialized checkout

#### Scenario: Map choice adopts the existing checkout

- **GIVEN** the gate's question answered with a mapped path
- **WHEN** `workspace-map set` records the entry
- **THEN** no materialization command runs and build continues inside the
  mapped checkout

#### Scenario: Present member asks nothing

- **GIVEN** a build target whose checkout is already present or mapped
- **WHEN** build's context gate runs
- **THEN** no materialization question is asked and the flow is unchanged
