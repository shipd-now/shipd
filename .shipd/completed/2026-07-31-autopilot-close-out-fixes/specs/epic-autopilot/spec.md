## MODIFIED Requirements

### Requirement: Run report and controls
id: run-report-and-controls
base: 38dbc2ef7db0

The autopilot SHALL accept `--max-members`, `--dry-run`, `--timeout`, and
`--max-resumes`; `--dry-run` SHALL print the member order and the
resolved pipeline and drive nothing. Every run SHALL end with a report
listing shipped members with PR URLs, parked members split into rejected
and needs-human — needs-human entries with their session ids, rejected
entries with the enrichment session id when an enrichment session ran —
skipped members with their states, and members unreached due to
`--max-members`; the report SHALL be written machine-readably and
summarized for humans, the summary printing a `claude --resume` pointer
for any parked member whose entry carries a session id. If a parked
entry carries no session id, then the summary SHALL omit the resume
pointer entirely rather than print a null value. When at least one
member PR merged during the run, the autopilot SHALL finish with the
epic-sync close-out in a fresh worktree, invoking the status CLI with a
well-formed invocation (the root option before the subcommand) so the
derivation actually runs. When the close-out derivation succeeds and
leaves the close-out worktree unchanged, the autopilot SHALL remove that
worktree and its branch; when it wrote a status change, the summary
SHALL name the worktree path so a human can ship it.

#### Scenario: Dry run drives nothing
- **WHEN** a run executes with `--dry-run`
- **THEN** the member order and resolved pipeline print and no session,
  gate, or worktree action occurs

#### Scenario: Report accounts for every member
- **GIVEN** a run with one shipped, one rejected (whose enrichment session
  ran), one needs-human, and one unreached member
- **WHEN** the run ends
- **THEN** the report lists each under its outcome, with a PR URL for
  the shipped member and a session id for both the needs-human and the
  rejected member

#### Scenario: Parked without a session omits the pointer
- **WHEN** the summary renders a needs-human member whose entry has no
  session id (parked before any session started)
- **THEN** the line carries the member, stage, and reason but no
  `claude --resume` fragment

#### Scenario: Close-out derivation runs
- **WHEN** the close-out invokes the status CLI in the fresh worktree
- **THEN** the invocation is accepted and the derived epic status is
  relayed in the run output

#### Scenario: No-op close-out cleans up
- **WHEN** the close-out sync exits zero without writing a status change
- **THEN** the close-out worktree and its branch are removed

#### Scenario: Written close-out is handed to a human
- **WHEN** the close-out sync writes a changed epic status
- **THEN** the summary names the close-out worktree path for a human to
  ship
