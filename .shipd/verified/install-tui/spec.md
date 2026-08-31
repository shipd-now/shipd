# install-tui

### Requirement: Interactive install verb
id: install-verb

The `shipd` binary SHALL provide an `install` verb. Where `/dev/tty` opens
read-write and color is enabled for it, the verb SHALL play the animated
wordmark, present a multi-select over every registry harness (arrow keys to
move, space to toggle, `a` for all, enter to confirm, `q`, `Esc`, or
interrupt to abort with nothing written; entries preselected from an
existing selection record), persist the confirmed selection, and run the
user-global generation for each selected harness that declares a
`user_dir`, reporting each selected harness as installed or as
repo-level-only with the `shipd harness add` pointer. The multi-select's
key hint SHALL name `esc` alongside `q` as an abort key. A lone `Esc` byte
SHALL decode to the abort key; an `Esc` introducing a `\x1b[` escape
sequence SHALL keep its existing meaning, so arrow keys still move and an
unrecognized escape sequence is still dropped rather than aborting. Where
raw terminal mode is unavailable, the verb SHALL fall back to a numbered
line prompt on the same tty, whose abort words remain `q`/`quit` and
end-of-input. If no
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

#### Scenario: A lone Esc aborts like q
- **WHEN** a bare `\x1b` byte is decoded, and when the interactive flow on a
  pseudo-terminal receives one after a toggle
- **THEN** it decodes to the abort key, the selection's verdict is aborted,
  no selection record is written, and the terminal attributes are restored

#### Scenario: Escape sequences keep their meaning
- **WHEN** `\x1b[A`, `\x1b[B`, and `\x1b[C` are decoded
- **THEN** the first two still decode to the move keys and the third still
  decodes to nothing — none of the three aborts

#### Scenario: The key hint names esc
- **WHEN** the multi-select's key hint is rendered
- **THEN** it names `esc` as well as `q` for quitting

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

### Requirement: Doctor preflight closes the install finish
id: install-doctor-finish

Where the interactive `install` flow reaches a confirmed selection, the
`shipd` binary SHALL, after saving the selection record and reporting the
per-harness result, run the same read-only preflight the `doctor` verb runs
and write its `ok|warn|fail <check> — <detail>` lines and closing summary to
the same terminal handle the flow reported on, preceded by a heading written
and flushed before the checks execute. Where any check reports other than
`ok`, the binary SHALL additionally write one pointer line naming `/s:doctor`
as the flow that works through the findings. The preflight SHALL install and
edit nothing, and its verdict SHALL NOT change the verb's exit code. Where the
flow aborts before confirmation, where the harness generation returns a
refusal, or where no usable controlling terminal is available, the binary
SHALL NOT run the preflight and the verb's output SHALL be unchanged.

#### Scenario: A confirmed selection ends with the preflight
- **WHEN** the interactive flow on a pseudo-terminal toggles a harness and
  confirms
- **THEN** the per-harness report is followed by the preflight's heading, its
  check lines, and its closing summary on the same terminal

#### Scenario: An empty confirmed selection still ends with the preflight
- **WHEN** the flow is confirmed with no harness selected
- **THEN** the no-harnesses note is followed by the preflight, and the exit
  code is 0

#### Scenario: An aborted flow runs no preflight
- **WHEN** the interactive flow is aborted before confirmation
- **THEN** the preflight does not run and the output is the abort note alone

#### Scenario: A headless run is unchanged
- **WHEN** `shipd install` runs with no usable controlling terminal
- **THEN** the preflight does not run, the output is the plain banner and the
  non-interactive note, and the exit code is 0

#### Scenario: A failing preflight leaves the verb successful
- **WHEN** the preflight run at the end of a confirmed selection reports a
  `fail` check
- **THEN** the failing line is printed and the verb still exits 0

#### Scenario: Problems carry the doctor pointer
- **WHEN** the preflight reports at least one non-`ok` check
- **THEN** the output carries one pointer line naming `/s:doctor`, and when
  every check is `ok` that line is absent
