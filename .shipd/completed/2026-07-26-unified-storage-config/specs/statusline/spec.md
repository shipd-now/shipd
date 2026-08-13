## MODIFIED Requirements

### Requirement: Current spec selection
id: current-spec-selection
base: 8e695d06be05

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
base: 2792b8f1e445

A statusline script SHALL read the Claude Code session JSON on stdin,
resolve the workspace directory from `workspace.current_dir` (falling back
to the working directory), and print exactly one line rendering the selected
spec as `☕ <change> · <status> · <done>/<total>`, where `<status>` comes
from the plan status header (`?` when missing or invalid) and
`<done>/<total>` are the done and total checkbox counts from `tasks.md`
(segment omitted when `tasks.md` is absent). The prefix glyph SHALL be bare
U+2615 (no variation selector). The script SHALL read the default-named
`.shipd/planned/` and `.shipd/state.json` directly — it SHALL NOT resolve layered
configuration, so a repo with a renamed content directory renders nothing.
The script SHALL print nothing and exit zero when the workspace has no
`.shipd/planned/` directory. When no spec is selected it SHALL auto-select a
sole change in `.shipd/planned/`; print `☕ no active specs` when there are
none; and print `☕ <n> specs · none selected` when there are several.

#### Scenario: Active spec is rendered
- **GIVEN** a workspace whose selected change is `dark-mode-toggle` with
  status `active` and 3 of 7 tasks done
- **WHEN** the statusline script runs
- **THEN** it prints one line containing `☕`, `dark-mode-toggle`, `active`,
  and `3/7`

#### Scenario: Non-spec repos stay silent
- **WHEN** the session's workspace directory contains no `.shipd/planned/`
- **THEN** the script prints nothing and exits zero

#### Scenario: Renamed content dir is out of statusline scope
- **GIVEN** a repo whose config renames the content directory to `specs`
- **WHEN** the statusline script runs
- **THEN** it prints nothing and exits zero, resolving no configuration
