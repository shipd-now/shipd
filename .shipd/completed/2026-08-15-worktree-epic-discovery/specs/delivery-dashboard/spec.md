## MODIFIED Requirements

### Requirement: Board aggregation
id: board-aggregation
base: 5eadf04a9149

The dashboard CLI SHALL provide a `board` verb that aggregates, for each epic
discovered under the invocation root **or any `.worktrees/<name>` directory
under it** (or only the epic named by `--epic`): the
epic's status, theme, and initiative context — the initiative's status resolved
through the workspace brief when a workspace is discoverable, the bare slug
otherwise, never an error; every stub member's worktree-aware state — derived
from the invocation root first and, when the root says `unplanned`, from a
locate-style probe of `.worktrees/<slug>` (planned change or completed archive),
reporting the state and where it lives; and the run context merged from the live
heartbeat and the latest run report when either exists. Epic discovery SHALL
probe the invocation root first, then each `.worktrees/<name>` directory in
sorted name order, resolving each candidate's content directory independently
and skipping any candidate whose configuration is unreadable; when the same
slug exists in more than one candidate, the invocation root's copy SHALL win,
then the first hosting worktree in sorted order, and the epic SHALL be
aggregated exactly once. Each aggregated epic SHALL carry its hosting root as
`location`, and the epic's file, status, heartbeat, and run report SHALL be
read from that hosting root. The aggregation SHALL
additionally group its epics under their initiative — a workspace-wide group for
epics carrying no `Initiative:` — and SHALL annotate each member with the board
actions eligible for it (`plan` for an `unplanned` member, `run` for a member
ready to drive, `open` for a parked or shipped member carrying a session id) and
that member's resumable `session_id` when known. The verb SHALL print an aligned
human-readable board by default and the full board object as JSON under `--json`;
the human-readable board and the TUI's epic group header SHALL mark an epic
whose `location` is not the invocation root with a `[worktree]` marker, and the
TUI's epic-detail overview SHALL read the epic markdown from the epic's
hosting root.

#### Scenario: Epics group under their initiative
- **GIVEN** two epics sharing one `Initiative:` and one epic carrying none
- **WHEN** the board is built
- **THEN** the two share a single initiative group and the third appears under a
  workspace-wide group

#### Scenario: Members carry eligible actions
- **GIVEN** an epic with an unplanned member, a ready member, and a member parked
  as needs-human with a session id
- **WHEN** the board is built
- **THEN** the unplanned member's eligible actions include `plan`, the ready
  member's include `run`, and the parked member's include `open`

#### Scenario: A worktree-parked member is visible
- **GIVEN** a member whose plan sits at `rejected` inside `.worktrees/<slug>`
  while the root's `planned/` lacks it
- **WHEN** the board is built
- **THEN** the member's row reports `rejected` and its worktree location instead
  of `unplanned`

#### Scenario: JSON mode is machine-readable
- **WHEN** `board --json` runs
- **THEN** stdout parses as a single JSON object listing the initiative groups,
  their epics, and each epic's members

#### Scenario: A worktree-authored epic joins the board
- **GIVEN** an epic whose `epics/<slug>/epic.md` exists only under
  `.worktrees/<name>`'s content directory
- **WHEN** the board is built from the invocation root
- **THEN** the epic is aggregated with its status and members, and its
  `location` is that worktree's root

#### Scenario: The invocation root shadows worktree copies
- **GIVEN** the same epic slug hosted under the invocation root and under a
  worktree
- **WHEN** the board is built
- **THEN** the epic appears exactly once, aggregated from the invocation root

#### Scenario: A worktree-hosted epic is marked on the text board
- **GIVEN** an epic whose `location` is a worktree root
- **WHEN** the human-readable board prints
- **THEN** that epic's header line carries `[worktree]`

#### Scenario: An unreadable worktree config does not break discovery
- **GIVEN** a worktree whose content-directory configuration cannot be read
- **WHEN** the board is built
- **THEN** that worktree is skipped and aggregation completes without raising
