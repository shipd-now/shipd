## MODIFIED Requirements

### Requirement: Statusline rendering
id: statusline-rendering
base: 54c44f820cf0

A statusline script SHALL read the Claude Code session JSON on stdin, resolve
the workspace directory from `workspace.current_dir` (falling back to the
working directory), and print exactly one line rendering the selected spec as
`☕ <change> · <status> · <done>/<total>`, where `<status>` comes from the
proposal status header (`?` when missing or invalid) and `<done>/<total>` are
the done and total checkbox counts from `tasks.md` (segment omitted when
`tasks.md` is absent). The prefix glyph SHALL be bare U+2615 (no variation
selector). The script SHALL print nothing and exit zero when the workspace has
no `am/spec/changes/` directory. When no spec is selected it SHALL auto-select
a sole non-archive change; print `☕ no active specs` when there are none; and
print `☕ <n> specs · none selected` when there are several.

#### Scenario: Active spec is rendered
- **GIVEN** a workspace whose selected change is `dark-mode-toggle` with
  status `active` and 3 of 7 tasks done
- **WHEN** the statusline script runs
- **THEN** it prints one line containing `☕`, `dark-mode-toggle`, `active`,
  and `3/7`

#### Scenario: Non-spec repos stay silent
- **WHEN** the session's workspace directory contains no `am/spec/changes/`
- **THEN** the script prints nothing and exits zero

#### Scenario: Sole change is auto-selected
- **GIVEN** no selection recorded and exactly one non-archive change
- **WHEN** the statusline script runs
- **THEN** that change is rendered as if selected
