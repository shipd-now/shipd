## MODIFIED Requirements

### Requirement: Interactive install verb
id: install-verb
base: 5e2a5ad80f4e

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
