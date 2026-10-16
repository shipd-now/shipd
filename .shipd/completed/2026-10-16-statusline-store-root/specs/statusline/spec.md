## ADDED Requirements

### Requirement: Statusline content-directory resolution
id: statusline-content-resolution

The statusline script SHALL resolve its content directory from the workspace
directory W the way the engine does, using only local file reads. It SHALL
read the `.shipd-config.json` in W and in each ancestor of W, nearest first,
then `~/.shipd-config.json` when the home directory is not already among
them, and SHALL take each of the keys `store_root` and `dir` as a JSON string
from the nearest file declaring it. When `store_root` is declared, its value
SHALL expand a leading `~`, and a value still relative SHALL resolve against
the directory of the declaring file. The script SHALL find W's main checkout:
the nearest ancestor-or-self of W holding a `.git` directory, or, where that
entry is a `.git` file reading `gitdir: <main>/.git/worktrees/<name>`, the
directory `<main>`; with no `.git` entry, W stands in for the main checkout.
The content directory SHALL then be the first existing directory among
`<store>/<main checkout relative to the nearest ancestor whose config
declares a "workspace" key>` and `<store>/<basename of the main checkout>`.
When `store_root` is not declared, the content directory SHALL be
`W/<dir>`, `dir` defaulting to `.shipd`, when that directory exists. If no
candidate exists or a declared value is unusable, then no content directory
resolves, and the script SHALL print no error. Invoked with
`--print-content-dir`, the script SHALL print only the resolved content
directory, or nothing when none resolves, and exit zero.

#### Scenario: A relative store root resolves against its config file
- **GIVEN** `<ws>/.shipd-config.json` declaring `"store_root": ".shipd"` and
  a repo `<ws>/app` with a `.git` directory and `<ws>/.shipd/app/planned/x/`
- **WHEN** the statusline script runs with `<ws>/app` as `current_dir`
- **THEN** it renders change `x` from `<ws>/.shipd/app/`

#### Scenario: A registry path is preferred over the basename
- **GIVEN** a config declaring both `"workspace"` and `"store_root"` at
  `<ws>`, a repo at `<ws>/teams/a/app`, and both `<store>/teams/a/app/` and
  `<store>/app/` existing
- **WHEN** `--print-content-dir` runs with `<ws>/teams/a/app` as
  `current_dir`
- **THEN** it prints `<store>/teams/a/app`

#### Scenario: A linked worktree resolves its main checkout's folder
- **GIVEN** a worktree whose `.git` file reads
  `gitdir: <ws>/app/.git/worktrees/w1` under a `store_root` config
- **WHEN** `--print-content-dir` runs from that worktree
- **THEN** it prints the same folder as from `<ws>/app`

#### Scenario: A renamed in-repo content directory is scanned
- **GIVEN** a repo whose config declares `"dir": "specs"` and holds
  `specs/planned/x/`
- **WHEN** the statusline script runs there
- **THEN** it renders change `x`

#### Scenario: A missing store folder shows no specs
- **GIVEN** a `store_root` config whose candidate folders do not exist
- **WHEN** the statusline script runs
- **THEN** it prints `☕ no specs` and exits zero with nothing on stderr

## MODIFIED Requirements

### Requirement: Statusline rendering
id: statusline-rendering
base: 7cd1a7dade20
Dropped: Non-shipd repos stay silent
Dropped: Renamed content dir is out of statusline scope

A statusline script SHALL read the Claude Code session JSON on stdin,
resolve the workspace directory from `workspace.current_dir` (falling back
to the working directory), resolve its content directory per the statusline-content-resolution
requirement, and collect live changes from that directory's `planned/`, plus,
when no `store_root` is declared, `.worktrees/*/<dir>/planned/` (one level
deep). It
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
file matching `autopilot/*-heartbeat.json` in the resolved content directory has a
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
none is pickable, it SHALL print `☕ <n> specs · none selected`; when a
content directory resolves but holds no live change, it SHALL print
`☕ no active specs`; when no content directory resolves, the spec segment
SHALL render `no specs` and the script SHALL exit zero. The prefix glyph SHALL be bare U+2615
(no variation selector).

The script SHALL compose its output from three named segments: `spec` (the
spec text this requirement defines above, from the change name through any
tasks bracket, or the `no active specs` / `<n> specs · none selected` text),
`directory`, and `context`. Each `--line <seg>[,<seg>...]` argument SHALL
declare one output line, in argument order, whose segments render in the
listed order joined by ` · `. With no `--line` argument, the layout SHALL be
a single line `spec,context`. The first printed line SHALL begin with `☕ `
and later lines SHALL carry no prefix. A segment that renders empty SHALL
be skipped, and a line whose segments all render empty SHALL not be printed.
The directory segment SHALL render the resolved workspace directory, with a
leading `$HOME` replaced by `~` (the bare home directory renders as `~`); a
directory outside `$HOME` SHALL render unchanged. The context segment SHALL
render the session JSON's `context_window.used_percentage` as a four-cell
bar followed by the integer percentage, as `<bar> <pct>%`. The bar SHALL
fill `round(pct × 4 / 100)` cells with `█` (U+2588) and the rest with `░`
(U+2591), so `0` renders `░░░░ 0%`, `25` renders `█░░░ 25%`, and `100`
renders `████ 100%`; a fractional percentage SHALL truncate to its integer
part, and a value above 100 SHALL clamp to 100. The context segment SHALL be
colored by the clamped percentage: light blue (`\033[94m`, the change-name
color) at 50 or below, orange (xterm-256 `208`) above 50, red (`196`) above
75, darker red (`160`) above 90, and dark red (`124`) above 95, with the
color reset after the segment so the ` · ` separators stay uncolored. If the session JSON carries
no non-negative numeric `used_percentage`, then the context segment SHALL
render empty. An unknown segment name SHALL be ignored.

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

#### Scenario: shipd repo without live changes reports instead of vanishing
- **GIVEN** a workspace carrying `.shipd/verified/` but no `.shipd/planned/`
  directory and no worktrees
- **WHEN** the statusline script runs
- **THEN** it prints `☕ no active specs` and exits zero

#### Scenario: Directory under home renders relative to tilde
- **GIVEN** a shipd workspace at `$HOME/projects/workspaces/understand` and
  the argument `--line spec,directory`
- **WHEN** the statusline script runs with that directory as `current_dir`
- **THEN** the line ends with `· ~/projects/workspaces/understand`

#### Scenario: The default layout omits the directory
- **WHEN** the statusline script runs with no `--line` argument and a
  `used_percentage` of `25`
- **THEN** it prints one line, `☕ <spec> · █░░░ 25%`, with no directory

#### Scenario: Context usage renders a four-cell bar
- **GIVEN** session JSON whose `context_window.used_percentage` is `0`,
  `25`, or `100`
- **WHEN** the statusline script runs
- **THEN** the line ends with `░░░░ 0%`, `█░░░ 25%`, or `████ 100%`
  respectively

#### Scenario: Missing context usage omits the context segment
- **GIVEN** session JSON with no `context_window` object and no `--line`
  argument
- **WHEN** the statusline script runs in a shipd workspace
- **THEN** the line is `☕ <spec>` and contains no `%`

#### Scenario: A second line carries the directory
- **GIVEN** a shipd workspace with no live change, a `used_percentage` of
  `50`, and the arguments `--line spec,context --line directory`
- **WHEN** the statusline script runs
- **THEN** it prints `☕ no active specs · ██░░ 50%` and then `<dir>` on a
  second line

#### Scenario: Context first sits beside the coffee cup
- **GIVEN** a shipd workspace, a `used_percentage` of `25`, and the argument
  `--line context,spec`
- **WHEN** the statusline script runs
- **THEN** the line begins `☕ █░░░ 25% · ` followed by the spec text

#### Scenario: Context color follows the usage thresholds
- **GIVEN** a `used_percentage` of `50`, `51`, `76`, `91`, or `96`
- **WHEN** the statusline script runs with the context segment shown
- **THEN** the context segment is wrapped in `\033[94m`, `\033[38;5;208m`,
  `\033[38;5;196m`, `\033[38;5;160m`, or `\033[38;5;124m` respectively,
  followed by `\033[0m`

#### Scenario: A workspace with no content directory shows no specs
- **WHEN** the session's workspace directory resolves no content directory
- **THEN** the script prints `☕ no specs` and exits zero

### Requirement: Statusline integration
id: statusline-integration
base: 8e92d2ca7b4a

The statusline SHALL be a self-contained bash script compatible with macOS
bash 3.2, invokable as a Claude Code `statusLine` command from the project
settings, and SHALL read only local files — its own rendering MUST NOT
invoke network calls or spawn language runtimes. A command chained with
`--then` is the user's own statusline and is exempt from that constraint. The project's `.claude/settings.json` SHALL
register it via a project-relative command.

#### Scenario: Registered in project settings
- **WHEN** the project's `.claude/settings.json` is read
- **THEN** its `statusLine` entry invokes the statusline script by
  project-relative path

#### Scenario: Fast and local
- **WHEN** the statusline script executes
- **THEN** it completes using only local file reads, with no network
  access, no `git` process, and no Python/Node process spawned

### Requirement: Chained statusline
id: statusline-chain
base: 5e08f0b14075

When the statusline script is invoked with the two leading arguments
`--then <command>`, it SHALL, after printing its own output, run `<command>`
through `bash -c` with the same session JSON on its stdin, so the chained
command's output follows shipd's. The chained command SHALL run on every
exit path, including when no content directory resolves. Without `--then`, the script's output SHALL be
unchanged.

#### Scenario: Chained command renders after shipd's line
- **GIVEN** a shipd workspace and the arguments `--then 'cat'`
- **WHEN** the statusline script runs with session JSON on stdin
- **THEN** the first output line is shipd's `☕` line and the remaining
  output is the session JSON itself

#### Scenario: Chained command still runs in a non-shipd workspace
- **GIVEN** a workspace with no `.shipd/` directory and the arguments
  `--then 'echo theirs'`
- **WHEN** the statusline script runs
- **THEN** the output is `☕ no specs` followed by `theirs`

#### Scenario: No chain leaves output unchanged
- **WHEN** the statusline script runs without `--then`
- **THEN** its output carries only shipd's line
