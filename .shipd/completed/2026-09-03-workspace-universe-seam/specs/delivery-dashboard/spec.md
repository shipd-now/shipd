## MODIFIED Requirements

### Requirement: Board aggregation
id: board-aggregation
base: bbfa528d77e3

The dashboard CLI SHALL provide a `board` verb that aggregates its epics
across the universes the engine's shared universe-discovery seam yields
(shipd-workspace workspace-universe-discovery), in seam order — the
invocation root's own universe always, plus, for a workspace-level
invocation, one universe per declared project repo. Within each universe it
SHALL aggregate, for each epic discovered under that universe's root **or
any `.worktrees/<name>` directory under it** (or only the epic named by
`--epic`, resolved against the universes in seam order, the first hosting
universe winning): the epic's status, theme, and initiative context — the
initiative's status resolved through the workspace brief when a workspace is
discoverable, the bare slug otherwise, never an error; every stub member's
worktree-aware state — derived from that universe's root first and, when it
says `unplanned`, from a locate-style probe of its `.worktrees/<slug>`
(planned change or completed archive), reporting the state and where it
lives; and the run context merged from the live heartbeat and the latest run
report when either exists, both read from the epic's hosting root. Within a
universe, epic discovery SHALL probe the universe's root first, then each of
its `.worktrees/<name>` directories in sorted name order, resolving each
candidate's content directory independently and skipping any candidate whose
configuration is unreadable; when the same slug exists in more than one
candidate of a universe, that universe's root copy SHALL win, then the first
hosting worktree in sorted order, and the epic SHALL be aggregated exactly
once per universe — epic slugs are NOT deduplicated across universes. Each
aggregated epic SHALL carry its hosting root as `location`, its owning
universe's absolute root as `universe_root`, and its owning declared
project's slug as `project` (null for the invocation root's own universe);
standalone changes SHALL be discovered per universe with that universe's own
member-slug exclusion set and carry the same `project` field. The
aggregation SHALL additionally group its epics under their initiative — a
workspace-wide group for epics carrying no `Initiative:` — and SHALL
annotate each member with the board actions eligible for it (`plan` for an
`unplanned` member, `run` for a member ready to drive, `open` for a parked
or shipped member carrying a session id) and that member's resumable
`session_id` when known; an action's launch SHALL be built against the
epic's `universe_root` — the member worktree, the driver's `--root`, and the
session working directory all land in the owning universe's repo. The verb
SHALL print an aligned human-readable board by default and the full board
object as JSON under `--json`; the human-readable board and the TUI's epic
group header SHALL mark an epic whose `location` is not its universe's root
with a `[worktree]` marker and an epic from a project universe with a
`[<project>]` marker after it, and the TUI's epic-detail overview SHALL read
the epic markdown from the epic's hosting root.

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

#### Scenario: A declared project's epic joins the board at workspace level
- **GIVEN** a workspace root whose declared project repo hosts an epic
- **WHEN** the board is built from the workspace root
- **THEN** the epic is aggregated with its member states derived from that
  repo, its `project` is the project's slug, its `universe_root` is that
  repo, and its board/TUI header carries the `[<project>]` marker

#### Scenario: Inside a member repo the board stays per-repo
- **GIVEN** the same workspace, with the board built from inside a declared
  project repo
- **WHEN** the board is built
- **THEN** only that repo's universe is aggregated and no epic carries a
  project slug

#### Scenario: A project epic's actions launch in its own repo
- **GIVEN** a project universe epic with an unplanned member
- **WHEN** the member's `plan` action launch is built
- **THEN** the launch's working directory and worktree path resolve under
  the project repo, not the invocation root

#### Scenario: Same epic slug in two universes aggregates twice
- **GIVEN** the same epic slug hosted under the invocation root and under a
  declared project repo
- **WHEN** the board is built from the workspace root
- **THEN** both epics are aggregated, distinguished by their `project`
