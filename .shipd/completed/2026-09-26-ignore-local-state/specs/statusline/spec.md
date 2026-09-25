## MODIFIED Requirements

### Requirement: Current spec selection
id: current-spec-selection
base: e9dbeb8565ec

The status CLI SHALL provide `use <change>` to record the spec being worked
on and `current` to print it. `use` SHALL validate that the change exists
under the resolved `<content-dir>/planned/` and exit non-zero for an unknown
change. The selection SHALL be stored in a repo-local
`<content-dir>/state.json` file (key `current_spec`), which SHALL be
git-ignored; `current` SHALL print nothing and exit zero when no selection
exists.

`use` SHALL enforce that ignore itself. When the resolved content directory
lies inside the root, `use` SHALL ensure the root's `.gitignore` carries the
two local-state rules — `<content-dir>/state.json` and
`<content-dir>/autopilot/`, each relative to the root — appending only a rule
that is absent, and SHALL leave `.gitignore` unchanged when both are present.
While the root is a git checkout (a `.git` directory or a linked-worktree
`.git` file) and either path is tracked by git, `use` SHALL untrack it from
the index without deleting it from disk, and SHALL report each untracked path
on stderr as `untracked <path>`. Its stdout SHALL remain the selected change
name alone. If the content directory resolves outside the root, or `git` is
unavailable, or the root is not a checkout, then `use` SHALL skip the ignore
and untrack steps and still record the selection, never failing on them.

#### Scenario: Selecting a spec
- **WHEN** a user runs `use dark-mode-toggle` under the default
  configuration and that change directory exists
- **THEN** `.shipd/state.json` records it and `current` prints
  `dark-mode-toggle`

#### Scenario: Unknown change is rejected
- **WHEN** `use` names a change with no directory under the resolved
  `planned/`
- **THEN** the CLI exits non-zero and the previous selection is unchanged

#### Scenario: Selecting seeds the ignore rules
- **WHEN** `use` runs in a git checkout whose `.gitignore` carries neither
  local-state rule
- **THEN** `.gitignore` gains `.shipd/state.json` and `.shipd/autopilot/`,
  stdout is the change name alone, and the exit code is `0`

#### Scenario: A tracked state file is untracked but kept
- **GIVEN** a git checkout whose committed tree tracks `.shipd/state.json`
- **WHEN** `use` runs
- **THEN** `git ls-files .shipd/state.json` prints nothing afterwards, the
  file still exists on disk holding the new selection, and stderr carries
  `untracked .shipd/state.json`

#### Scenario: Present rules are left alone
- **WHEN** `use` runs in a checkout whose `.gitignore` already carries both
  rules and tracks neither path
- **THEN** `.gitignore` is byte-for-byte unchanged and stderr is empty

#### Scenario: Outside a checkout the selection still records
- **WHEN** `use` runs against a root with no `.git` entry
- **THEN** the selection is recorded, no untrack is attempted, and the exit
  code is `0`
