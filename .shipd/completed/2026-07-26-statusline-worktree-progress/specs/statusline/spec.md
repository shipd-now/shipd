## MODIFIED Requirements

### Requirement: Statusline rendering
id: statusline-rendering
base: ccbff4d7ec6d

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
back to the root's recorded selection, then to a sole live change. When more
than one change is live (X > 1), the name segment SHALL render
`<change> (1 of X)` and the tasks segment SHALL render
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
