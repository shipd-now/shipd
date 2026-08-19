## ADDED Requirements

### Requirement: Interactive install verb
id: install-verb

The `shipd` binary SHALL provide an `install` verb. Where `/dev/tty` opens
read-write and color is enabled for it, the verb SHALL play the animated
wordmark, present a multi-select over every registry harness (arrow keys to
move, space to toggle, `a` for all, enter to confirm, `q` or interrupt to
abort with nothing written; entries preselected from an existing selection
record), persist the confirmed selection, and run the user-global
generation for each selected harness that declares a `user_dir`, reporting
each selected harness as installed or as repo-level-only with the
`shipd harness add` pointer. Where raw terminal mode is unavailable, the
verb SHALL fall back to a numbered line prompt on the same tty. If no
usable `/dev/tty` is available, then the verb SHALL print the plain
wordmark and a short non-interactive note, write nothing, and exit 0.
Terminal state (cursor, tty attributes) SHALL be restored on every exit
path, including interruption.

#### Scenario: Headless run degrades cleanly
- **WHEN** `shipd install` runs with no usable controlling terminal
- **THEN** stdout carries the plain banner and the non-interactive note,
  the exit code is 0, and no file is created or modified

#### Scenario: Interactive selection generates user-global commands
- **WHEN** the flow runs on a pseudo-terminal in an isolated `HOME` and the
  user toggles `codex` and confirms
- **THEN** the selection record holds `codex`, generated command files
  exist under `~/.codex/prompts/`, and the report names `codex`

#### Scenario: A repo-only harness is reported, not generated
- **WHEN** the confirmed selection includes a harness without a `user_dir`
- **THEN** the report points it at `shipd harness add` and no user-global
  file is written for it

#### Scenario: Abort writes nothing
- **WHEN** the interactive flow is aborted before confirmation
- **THEN** no selection record is written, no generation runs, and the
  terminal attributes and cursor are restored

### Requirement: Persisted harness selection
id: install-selection

The confirmed selection SHALL persist at `~/.shipd/harnesses.json` as
`{"version": 1, "harnesses": [<ids>]}`, written atomically. On load, the
verb SHALL preselect the recorded harnesses and SHALL drop ids the registry
no longer declares. Re-running `shipd install` SHALL reopen the selection
from the record and overwrite it on confirm.

#### Scenario: Re-run preselects the record
- **WHEN** the flow runs with a record holding `codex` plus an unknown id
- **THEN** `codex` starts selected, the unknown id is ignored, and a
  confirmed run rewrites the record without the unknown id

#### Scenario: The record round-trips
- **WHEN** a selection is confirmed and the file is re-read
- **THEN** it parses as JSON with `version` 1 and exactly the confirmed ids
