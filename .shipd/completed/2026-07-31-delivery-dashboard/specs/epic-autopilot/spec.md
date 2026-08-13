## MODIFIED Requirements

### Requirement: Deliver skill
id: deliver-skill
base: 95dd4a1697a5

An `/s:deliver <epic>` skill SHALL preflight the run — verifying the
epic exists at `ready` or `active`, showing the member roster and the
resolved pipeline, and confirming the run controls with the user — then
run the autopilot driver in the foreground, relay its report, and point
at `claude --resume <session-id>` for each needs-human member and at
`/s:plan <member>` as the enrichment entry point for each rejected
member. Before launching the run, the skill SHALL name the dashboard
TUI command (`dashboard.py tui --epic <epic>`) as the live view for
watching the run from another terminal. The skill SHALL NOT plan, build,
or answer a driven session's questions itself.

#### Scenario: Preflight blocks a draft epic
- **WHEN** the skill is invoked for an epic at `draft`
- **THEN** it reports the epic is not approved and drives nothing

#### Scenario: Preflight names the live board
- **WHEN** the skill confirms the run controls before launching
- **THEN** its output names the dashboard TUI command for watching the
  run live

#### Scenario: Report is relayed with HITL pointers
- **WHEN** a run ends with a needs-human member
- **THEN** the skill's summary includes the resume command for that
  member's session

#### Scenario: Rejected member points at plan enrichment
- **WHEN** a run ends with a gate-rejected member
- **THEN** the skill's summary points at `/s:plan <member>` for that
  member's recovery
