## ADDED Requirements

### Requirement: Shared session driver
id: shared-session-driver

The plugin SHALL ship a stdlib session-driver module exposing a
grade-gated resume loop: drive a headless `claude -p` session in a given
working directory, then, while a supplied grade function has not passed
and fewer than `max_resumes` resumed turns have run, resume the same
session with a supplied reply, returning success, the final session id,
and any failure. The turn runner SHALL be injectable so the loop is
testable without live sessions, and the eval runner SHALL consume this
module rather than carrying its own copy of the loop.

#### Scenario: Loop stops when the grade passes
- **GIVEN** an injected runner whose second turn makes the grade pass
- **WHEN** the driver runs with max_resumes 4
- **THEN** exactly two turns run and the result is success

#### Scenario: Exhaustion surfaces the session id
- **GIVEN** an injected runner whose grade never passes
- **WHEN** the driver exhausts max_resumes
- **THEN** the result carries the session id for later interactive resume

### Requirement: Member selection and order
id: member-selection-and-order

Given an epic at `ready` or `active`, the autopilot SHALL drive only stub
members whose derived state is `unplanned`, ordered by the stub table's
Risk rating ascending (`low`, `medium`, `high`), ties broken by table
order. Members in any other state SHALL be reported under that state and
left untouched — a `rejected` member SHALL never be re-driven.

#### Scenario: Risk-ascending order
- **GIVEN** unplanned members rated high, low, and medium in table order
- **WHEN** a run starts
- **THEN** the driving order is the low, then medium, then high member

#### Scenario: In-flight members are skipped
- **GIVEN** a member whose plan sits at `rejected`
- **WHEN** a run executes
- **THEN** that member is reported as rejected and not driven

### Requirement: Pipeline-honoring stage execution
id: pipeline-stage-execution

Per member, the autopilot SHALL execute the resolved
`autonomous-pipeline` entries in order, covering the `plan`, `gate`, and
`build` registry stages and any `custom` entries, while noting and
ignoring `research` and `epic` entries as pre-approval stages. A skipped
entry SHALL be skipped; a replaced entry SHALL run its replacement
command in the member's worktree instead of the built-in behavior; a
`tools` binding SHALL be surfaced to the driven session as prompt
guidance including its fallback. Built-in behavior: `plan` drives a
headless `/s:plan <member>` graded on a lint-clean member change at
`Status: ready`; `gate` runs the gate engine, where a context rejection
(exit 2) parks the member immediately with no retries; `build` drives a
headless `/s:build` graded on the change archived under `completed/` and
a PR existing for the member branch. Member worktrees SHALL be created
with the plugin's worktree helper.

#### Scenario: Full pass ships a member
- **GIVEN** a member whose plan gates clean and whose build succeeds
- **WHEN** the autopilot drives it
- **THEN** its worktree came from the plugin helper, the change is
  archived, and an auto-merging PR exists for its branch

#### Scenario: Gate rejection parks without retry
- **WHEN** the gate exits 2 on a member's plan
- **THEN** the member is parked as rejected, no re-drive occurs, and the
  run continues with the next member

#### Scenario: Skipped gate is honored
- **GIVEN** a resolved pipeline whose gate entry carries skip
- **WHEN** a member is driven
- **THEN** no gate runs between plan and build for that member

#### Scenario: Custom step runs at its position
- **GIVEN** a custom entry between build and review
- **WHEN** a member is driven
- **THEN** the custom command runs in the member's worktree after build

### Requirement: Three-strike failure handling
id: three-strike-parking

When a driven stage fails for a non-gate reason — session error or
timeout, grade unmet after the resume budget, or a non-zero replacement
or custom command — the autopilot SHALL re-drive that stage with the
failure summary appended to the prompt, up to three attempts in total.
A stage still failing after the third attempt SHALL park the member as
`needs-human`, recording the stage, the reason, and the most recent
session id so a human can reopen the exact conversation with
`claude --resume <id>`; the member's worktree SHALL be left intact and
the run SHALL continue with the next member.

#### Scenario: Second attempt can succeed
- **GIVEN** a stage that fails once and succeeds on re-drive
- **WHEN** the autopilot drives it
- **THEN** the member proceeds and no parking occurs

#### Scenario: Third failure parks with the session id
- **WHEN** a stage fails three attempts
- **THEN** the member is parked as needs-human with stage, reason, and
  session id, its worktree remains, and the next member starts

### Requirement: Run report and controls
id: run-report-and-controls

The autopilot SHALL accept `--max-members`, `--dry-run`, `--timeout`, and
`--max-resumes`; `--dry-run` SHALL print the member order and the
resolved pipeline and drive nothing. Every run SHALL end with a report
listing shipped members with PR URLs, parked members split into rejected
and needs-human (with session ids), skipped members with their states,
and members unreached due to `--max-members`; the report SHALL be
written machine-readably and summarized for humans. When at least one
member PR merged during the run, the autopilot SHALL finish with the
epic-sync close-out in a fresh worktree.

#### Scenario: Dry run drives nothing
- **WHEN** a run executes with `--dry-run`
- **THEN** the member order and resolved pipeline print and no session,
  gate, or worktree action occurs

#### Scenario: Report accounts for every member
- **GIVEN** a run with one shipped, one rejected, one needs-human, and
  one unreached member
- **WHEN** the run ends
- **THEN** the report lists each under its outcome, with a PR URL for
  the shipped and a session id for the needs-human member

### Requirement: Deliver skill
id: deliver-skill

An `/s:deliver <epic>` skill SHALL preflight the run — verifying the
epic exists at `ready` or `active`, showing the member roster and the
resolved pipeline, and confirming the run controls with the user — then
run the autopilot driver in the foreground, relay its report, and point
at `claude --resume <session-id>` for each needs-human member. The skill
SHALL NOT plan, build, or answer a driven session's questions itself.

#### Scenario: Preflight blocks a draft epic
- **WHEN** the skill is invoked for an epic at `draft`
- **THEN** it reports the epic is not approved and drives nothing

#### Scenario: Report is relayed with HITL pointers
- **WHEN** a run ends with a needs-human member
- **THEN** the skill's summary includes the resume command for that
  member's session
