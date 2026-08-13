## ADDED Requirements

### Requirement: Targeted single-member drive
id: targeted-member-drive

The autopilot SHALL support driving a single epic member selected by slug —
independent of the risk-ascending auto-selection — entering the resolved
`autonomous-pipeline` at the stage matching that member's current lifecycle
state: an `unplanned` member from `plan`, a `ready` (planned, lint-clean) member
from `build`, skipping the stages already satisfied. The targeted drive SHALL
reuse the same worktree, graded stage loop, heartbeat, and park/ship semantics as
an epic run, drive exactly the one named member, and back the board's per-card
`run` action. It SHALL leave the epic-level `member-selection-and-order`
auto-selection unchanged.

#### Scenario: A ready member enters at build
- **GIVEN** an epic member whose plan sits at `ready`, lint-clean
- **WHEN** a targeted single-member drive runs for that member
- **THEN** the pipeline starts at `build` — `plan` and `gate` are skipped — and
  the member is driven through to its terminal outcome

#### Scenario: An unplanned member enters at plan
- **GIVEN** an epic member whose derived state is `unplanned`
- **WHEN** a targeted single-member drive runs for that member
- **THEN** the pipeline starts at `plan`, and no other member is driven

#### Scenario: Auto-selection is untouched
- **WHEN** a normal epic run (no targeted member) is driven
- **THEN** members are still selected and ordered risk-ascending over the
  `unplanned` set exactly as before
