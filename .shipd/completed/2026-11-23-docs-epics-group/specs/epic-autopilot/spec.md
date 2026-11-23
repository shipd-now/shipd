## ADDED Requirements

### Requirement: Autopilot user documentation
id: autopilot-user-docs

The repository SHALL provide `docs/autopilot.md`, the main page for
`/s:autopilot`, titled "Autopilot". The page SHALL conform to the shipd
documentation standard with `<!-- doc-type: how-to -->` as its first line,
and SHALL open by saying what autopilot is, then hold exactly three level-2
sections in this order: `## When to use it`, `## How to run it`, and
`## Reference`. No nested reference page
accompanies it.

The page SHALL state:

- that autopilot drives an approved epic's members to shipped pull requests
  with no human present, one worktree and one branch per member, and that
  the epic approval is the last human gate;
- the two modes: the in-session drive, which is the default and drives
  `unplanned` and `ready` members in waves, and the detached run, requested
  as `/s:autopilot <epic> detached`, which drives `unplanned` members one at
  a time;
- the run as numbered steps: the launch preflight, the launch brief, the
  drive, and the run summary;
- that the preflight prints `ok`, `warn`, and `fail` lines, and that one
  `fail` line stops the run before it drives anything;
- that the run asks no question, and that a failure parks the member while
  the drive continues with every member that does not depend on it;
- that a `ready` member whose `After` dependency has not merged is blocked,
  and that the drive waits for that merge within the timeout;
- the four groups of the run summary: shipped, parked, blocked, skipped;
- that re-running `/s:autopilot <epic>` resumes from the state on disk, with
  no run-state file;
- that `shipd board --epic <epic>` shows the run live from another terminal.

The `## Reference` section SHALL hold a controls table with `--max-members`
(default unlimited), `--timeout` (default 1800 seconds), `--max-resumes`
(default 4), and `--parallel` (default 3, ignored by the detached run). It
SHALL also list the park reasons `grade-failed <stage>`, `gate-rejected`,
`command-failed`, `sync-conflict`, `drift-error`, `drift-conflict`, and
`replan-failed`, and SHALL name `/s:plan <member>` as the recovery for a
`gate-rejected` or `replan-failed` member.

The page SHALL carry exactly one mermaid fence, showing one member's path
through plan, gate, build, and pull request with the parked and blocked
branches. The page SHALL link `epics.md`, `epic-grill.md`, `drift.md`, and
`customise.md` as the owner of the pipeline's stage configuration. Every
command on the page SHALL be a `/s:` skill, a `shipd` verb, or the
`claude --resume <session-id>` command the detached report prints.

#### Scenario: Page covers both modes
- **WHEN** `docs/autopilot.md` is inspected
- **THEN** it names the in-session drive as the default, the `detached`
  invocation, and which member states each mode drives

#### Scenario: Page covers park and resume
- **WHEN** `docs/autopilot.md` is inspected
- **THEN** it states that a failure parks the member and the drive
  continues, lists the seven park reasons, and names the re-run as the
  resume path

#### Scenario: Controls table carries the defaults
- **WHEN** the `## Reference` section is read
- **THEN** its table holds the four controls with the defaults unlimited,
  1800, 4, and 3

#### Scenario: Diagram shows the branches
- **WHEN** the mermaid fence in `docs/autopilot.md` is inspected
- **THEN** it is the only fence of its kind on the page and holds the plan,
  gate, build, and pull request stages plus a parked and a blocked branch

#### Scenario: Page passes the lint and its links resolve
- **WHEN** `docs_lint.py` runs over `docs/autopilot.md`
- **THEN** it exits 0 with the file marked `how-to`, the file names no
  `autopilot.py`, `dashboard.py`, or `spec_status.py` path, and every
  relative link resolves to an existing file
