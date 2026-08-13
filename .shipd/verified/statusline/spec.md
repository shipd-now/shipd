# statusline

### Requirement: Current spec selection
id: current-spec-selection

The status CLI SHALL provide `use <change>` to record the spec being worked
on and `current` to print it. `use` SHALL validate that the change exists
under the resolved `<content-dir>/planned/` and exit non-zero for an unknown
change. The selection SHALL be stored in a repo-local
`<content-dir>/state.json` file (key `current_spec`), which SHALL be
git-ignored; `current` SHALL print nothing and exit zero when no selection
exists.

#### Scenario: Selecting a spec
- **WHEN** a user runs `use dark-mode-toggle` under the default
  configuration and that change directory exists
- **THEN** `.shipd/state.json` records it and `current` prints
  `dark-mode-toggle`

#### Scenario: Unknown change is rejected
- **WHEN** `use` names a change with no directory under the resolved
  `planned/`
- **THEN** the CLI exits non-zero and the previous selection is unchanged

### Requirement: Statusline rendering
id: statusline-rendering

A statusline script SHALL read the Claude Code session JSON on stdin,
resolve the workspace directory from `workspace.current_dir` (falling back
to the working directory), and collect live changes from both the workspace
root's `.shipd/planned/` and `.worktrees/*/.shipd/planned/` (one level deep). It
SHALL print exactly one line rendering the picked spec as
`☕ <change> · <status> · <done>/<total>`, where `<status>` comes from the
plan status header (`?` when missing or invalid) and `<done>/<total>` are
the checkbox counts from that change's `tasks.md` (segment omitted when
`tasks.md` is absent). The pick SHALL prefer a change whose status is
`active` — wherever it lives — breaking ties among several `active` changes
by newest `tasks.md` modification time; with no active change it SHALL fall
back to the root's recorded selection, then to a sole live change. When the
picked change's `plan.md` header carries an `Epic:` line, the name segment
SHALL append an epic marker after the change name, before any position
bracket: `(EPIC: <epic-slug>, spec <pos>/<total>)`, where `<pos>` is the
change's 1-based row position in the members table of the epic file
resolved relative to the candidate's own content directory
(`<base>/.shipd/epics/<slug>/epic.md` for a candidate at
`<base>/.shipd/planned/<change>/`) and `<total>` is that table's member row
count; if the epic file is missing or the change has no row in its table,
then the marker SHALL degrade to the literal `(EPIC)`. While a heartbeat
file matching `.shipd/autopilot/*-heartbeat.json` in the workspace root has a
modification time within 3600 seconds and records a run state of
`running`, and the picked change's status is `active`, the status segment
SHALL be prefixed with a solid dot glyph (U+25CF) colored from an 8-step
ping-pong ramp of xterm-256 greens indexed by epoch seconds modulo 8; if
no heartbeat is live (absent, stale, or not `running`) or the picked
status is not `active`, then the status segment SHALL render without a
dot. When more than one change is live (X > 1), the name segment SHALL
render `<change> (1 of X)` and the tasks segment SHALL render
`<done>/<total> (<total> of <Y>)`, where Y is the summed checkbox totals of
every live change carrying a `tasks.md`. When several changes are live and
none is pickable, it SHALL print `☕ <n> specs · none selected`; when the
workspace carries a `.shipd/` directory but no live change, it SHALL print
`☕ no active specs`; only when the workspace has no `.shipd/` directory at all
SHALL it print nothing and exit zero. The prefix glyph SHALL be bare U+2615
(no variation selector). The script SHALL read the default-named `.shipd/`
paths directly — it SHALL NOT resolve layered configuration, so a repo or
worktree with a renamed content directory is not scanned.

#### Scenario: Active worktree change is rendered from the main checkout
- **GIVEN** a workspace whose own `.shipd/planned/` is empty and a worktree
  `.worktrees/w1/.shipd/planned/dark-mode-toggle/` at status `active` with 3
  of 7 tasks done
- **WHEN** the statusline script runs with the workspace as `current_dir`
- **THEN** it prints one line containing `☕`, `dark-mode-toggle`,
  `active`, and `3/7`

#### Scenario: Epic member renders name and table position
- **GIVEN** a picked change whose `plan.md` carries `Epic: some-epic` and
  an epic file whose members table lists it as the 2nd of 3 rows
- **WHEN** the statusline script runs
- **THEN** the name segment renders as
  `<change> (EPIC: some-epic, spec 2/3)`

#### Scenario: Missing epic file degrades to the bare marker
- **GIVEN** a picked change carrying `Epic: some-epic` with no
  corresponding `epics/some-epic/epic.md` in its content directory
- **WHEN** the statusline script runs
- **THEN** the name segment renders the literal `(EPIC)` marker

#### Scenario: Change absent from the members table degrades to the bare marker
- **GIVEN** a picked change carrying `Epic: some-epic` whose epic file's
  members table has no row for the change
- **WHEN** the statusline script runs
- **THEN** the name segment renders the literal `(EPIC)` marker

#### Scenario: Standalone change carries no marker
- **GIVEN** a picked change whose `plan.md` has no `Epic:` header line
- **WHEN** the statusline script runs
- **THEN** the rendered line contains no `(EPIC` text

#### Scenario: Live heartbeat lights the dot on an active change
- **GIVEN** an `active` picked change and a fresh
  `.shipd/autopilot/e-heartbeat.json` recording a `running` state
- **WHEN** the statusline script runs
- **THEN** the status segment renders the U+25CF dot before `active`

#### Scenario: Stale or finished heartbeats render no dot
- **GIVEN** an `active` picked change and a heartbeat that is either older
  than 3600 seconds or records a `finished` state
- **WHEN** the statusline script runs
- **THEN** the status segment renders `active` with no dot

#### Scenario: Non-active pick renders no dot even with a live run
- **GIVEN** a picked change at status `ready` and a fresh heartbeat
  recording a `running` state
- **WHEN** the statusline script runs
- **THEN** the status segment renders without a dot

#### Scenario: Multiple live specs render position and aggregate brackets
- **GIVEN** an `active` change with 5 of 13 tasks done and a second live
  change whose `tasks.md` holds 7 tasks
- **WHEN** the statusline script runs
- **THEN** the line renders the active change as `<name> (1 of 2)` with
  task segment `5/13 (13 of 20)`

#### Scenario: Active beats the root selection
- **GIVEN** a root selection recorded for a `ready` change and an `active`
  change in a worktree
- **WHEN** the statusline script runs
- **THEN** the worktree's active change owns the line

#### Scenario: Am repo without live changes reports instead of vanishing
- **GIVEN** a workspace carrying `.shipd/verified/` but no `.shipd/planned/`
  directory and no worktrees
- **WHEN** the statusline script runs
- **THEN** it prints `☕ no active specs` and exits zero

#### Scenario: Non-am repos stay silent
- **WHEN** the session's workspace directory contains no `.shipd/` directory
- **THEN** the script prints nothing and exits zero

#### Scenario: Renamed content dir is out of statusline scope
- **GIVEN** a repo whose config renames the content directory to `specs`
- **WHEN** the statusline script runs
- **THEN** its changes are not scanned and no configuration is resolved

### Requirement: Statusline integration
id: statusline-integration

The statusline SHALL be a self-contained bash script compatible with macOS
bash 3.2, invokable as a Claude Code `statusLine` command from the project
settings, and SHALL read only local files — it MUST NOT invoke network calls
or spawn language runtimes. The project's `.claude/settings.json` SHALL
register it via a project-relative command.

#### Scenario: Registered in project settings
- **WHEN** the project's `.claude/settings.json` is read
- **THEN** its `statusLine` entry invokes the statusline script by
  project-relative path

#### Scenario: Fast and local
- **WHEN** the statusline script executes
- **THEN** it completes using only file reads in the workspace, with no
  network access and no Python/Node process spawned
