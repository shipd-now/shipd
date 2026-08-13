## MODIFIED Requirements

### Requirement: Autopilot skill
id: deliver-skill
base: e46c842dcfd5

An `/s:autopilot <epic>` skill SHALL preflight the run — verifying the
epic exists at `ready` or `active`, showing the member roster and the
resolved pipeline, and confirming the run controls with the user — then
run the autopilot driver in the foreground, relay its report, and point
at `claude --resume <session-id>` for each needs-human member. For each
rejected member the relay SHALL note that the automatic oracle-backed
enrichment attempt already failed, point at `/s:plan <member>` as the
manual enrichment entry point, and print `claude --resume <session-id>`
when the report carries the member's enrichment session id. Before
launching the run, the skill SHALL name the dashboard TUI command
(`dashboard.py tui --epic <epic>`) as the live view for watching the run
from another terminal. The skill SHALL keep `deliver` among its trigger
phrases so the former `/s:deliver` vocabulary still resolves to it. The
skill SHALL NOT plan, build, or answer a driven session's questions
itself.

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
- **THEN** the skill's summary notes the failed automatic enrichment,
  points at `/s:plan <member>` for that member's recovery, and includes
  the resume command when the report carries an enrichment session id

#### Scenario: The deliver vocabulary still resolves
- **WHEN** the user invokes the skill by asking to "deliver" an epic
- **THEN** the `/s:autopilot` skill is the one that answers
