## ADDED Requirements

### Requirement: Current spec selection
id: current-spec-selection

The status CLI SHALL provide `use <change>` to record the spec being worked
on and `current` to print it. `use` SHALL validate that
`am/spec/changes/<change>/` exists (the archive excluded) and exit non-zero
for an unknown change. The selection SHALL be stored in a repo-local
`.shipd/state.json` file (key `current_spec`), which SHALL be git-ignored;
`current` SHALL print nothing and exit zero when no selection exists.

#### Scenario: Selecting a spec
- **WHEN** a user runs `use dark-mode-toggle` and that change directory
  exists
- **THEN** `.shipd/state.json` records it and `current` prints
  `dark-mode-toggle`

#### Scenario: Unknown change is rejected
- **WHEN** `use` names a change with no directory under `am/spec/changes/`
- **THEN** the CLI exits non-zero and the previous selection is unchanged

### Requirement: Statusline rendering
id: statusline-rendering

A statusline script SHALL read the Claude Code session JSON on stdin, resolve
the workspace directory from `workspace.current_dir` (falling back to the
working directory), and print exactly one line rendering the selected spec as
`☢️ <change> · <status> · <done>/<total>`, where `<status>` comes from the
proposal status header (`?` when missing or invalid) and `<done>/<total>` are
the done and total checkbox counts from `tasks.md` (segment omitted when
`tasks.md` is absent). The script SHALL print nothing and exit zero when the
workspace has no `am/spec/changes/` directory. When no spec is selected it
SHALL auto-select a sole non-archive change; print `☢️ no active specs` when
there are none; and print `☢️ <n> specs · none selected` when there are
several.

#### Scenario: Active spec is rendered
- **GIVEN** a workspace whose selected change is `dark-mode-toggle` with
  status `active` and 3 of 7 tasks done
- **WHEN** the statusline script runs
- **THEN** it prints one line containing `☢️`, `dark-mode-toggle`, `active`,
  and `3/7`

#### Scenario: Non-spec repos stay silent
- **WHEN** the session's workspace directory contains no `am/spec/changes/`
- **THEN** the script prints nothing and exits zero

#### Scenario: Sole change is auto-selected
- **GIVEN** no selection recorded and exactly one non-archive change
- **WHEN** the statusline script runs
- **THEN** that change is rendered as if selected

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
