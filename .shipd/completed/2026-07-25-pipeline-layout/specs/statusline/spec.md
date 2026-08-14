## MODIFIED Requirements

### Requirement: Current spec selection
id: current-spec-selection
base: a338c04dab18

The status CLI SHALL provide `use <change>` to record the spec being worked
on and `current` to print it. `use` SHALL validate that
`am/planned/<change>/` exists and exit non-zero for an unknown change. The
selection SHALL be stored in a repo-local `.shipd/state.json` file (key
`current_spec`), which SHALL be git-ignored; `current` SHALL print nothing and
exit zero when no selection exists.

#### Scenario: Selecting a spec
- **WHEN** a user runs `use dark-mode-toggle` and that change directory
  exists
- **THEN** `.shipd/state.json` records it and `current` prints
  `dark-mode-toggle`

#### Scenario: Unknown change is rejected
- **WHEN** `use` names a change with no directory under `am/planned/`
- **THEN** the CLI exits non-zero and the previous selection is unchanged

### Requirement: Statusline rendering
id: statusline-rendering
base: d79daea9de7a

A statusline script SHALL read the Claude Code session JSON on stdin, resolve
the workspace directory from `workspace.current_dir` (falling back to the
working directory), and print exactly one line rendering the selected spec as
`☕ <change> · <status> · <done>/<total>`, where `<status>` comes from the
plan status header (`?` when missing or invalid) and `<done>/<total>` are
the done and total checkbox counts from `tasks.md` (segment omitted when
`tasks.md` is absent). The prefix glyph SHALL be bare U+2615 (no variation
selector). The script SHALL print nothing and exit zero when the workspace has
no `am/planned/` directory. When no spec is selected it SHALL auto-select
a sole change in `am/planned/`; print `☕ no active specs` when there are
none; and print `☕ <n> specs · none selected` when there are several.

#### Scenario: Active spec is rendered
- **GIVEN** a workspace whose selected change is `dark-mode-toggle` with
  status `active` and 3 of 7 tasks done
- **WHEN** the statusline script runs
- **THEN** it prints one line containing `☕`, `dark-mode-toggle`, `active`,
  and `3/7`

#### Scenario: Non-spec repos stay silent
- **WHEN** the session's workspace directory contains no `am/planned/`
- **THEN** the script prints nothing and exits zero

#### Scenario: Sole change is auto-selected
- **GIVEN** no selection recorded and exactly one change under `am/planned/`
- **WHEN** the statusline script runs
- **THEN** that change is rendered as if selected
