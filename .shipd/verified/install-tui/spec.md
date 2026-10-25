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
per-harness result, run the `doctor` verb's preflight checks in their
`doctor` order on the same terminal handle the flow reported on. While the
checks run, the binary SHALL show one progress line, rewritten in place,
reading `Checking your setup: [<i>/<n>] <check>`, flushed before each check
executes. After the checks, for each non-`ok` check that `doctor --fix`
remedies automatically (`difft`, `textual`, `statusline`), the binary SHALL
run that remedy without asking, rewriting the same line as
`Installing: <check> …`, suppressing the remedy's own output, and SHALL then
re-run that check. The binary SHALL then clear the progress line and write
one summary line `✓ <ok> of <n> checks ok`, followed, for each check still
not `ok` in check order, by one line `<level> <check> — <reason>` and one
indented line `fix: <hint>` naming how to fix it. Where a remedy ran and
failed, the reason SHALL carry the remedy's failure reason. The binary SHALL
write no line for an `ok` check, SHALL NOT point the user at `/s:doctor` or
`semdiff doctor` for a remedy it ran, and SHALL NOT mutate any GitHub-side
setting. The finish's verdict SHALL NOT change the verb's exit code. Where
the flow aborts before confirmation, where the harness generation returns a
refusal, or where no usable controlling terminal is available, the binary
SHALL NOT run the finish and the verb's output SHALL be unchanged. The bare
`doctor` verb's output SHALL be unaffected.

#### Scenario: A confirmed selection ends with the progress line and summary
- **WHEN** the interactive flow on a pseudo-terminal toggles a harness and
  confirms, and every check is `ok`
- **THEN** the per-harness report is followed by progress updates naming
  each check as `[<i>/<n>] <check>`, then `✓ <n> of <n> checks ok`, and no
  per-check line

#### Scenario: An empty confirmed selection still ends with the finish
- **WHEN** the flow is confirmed with no harness selected
- **THEN** the no-harnesses note is followed by the finish, and the exit
  code is 0

#### Scenario: An aborted flow runs no finish
- **WHEN** the interactive flow is aborted before confirmation
- **THEN** the finish does not run and the output is the abort note alone

#### Scenario: A headless run is unchanged
- **WHEN** `shipd install` runs with no usable controlling terminal
- **THEN** the finish does not run, the output is the plain banner and the
  non-interactive note, and the exit code is 0

#### Scenario: Missing local tooling is installed without asking
- **GIVEN** the checks report `difft` missing and its remedy succeeds
- **WHEN** the finish runs
- **THEN** the remedy runs once with no prompt, the `difft` check is re-run,
  and no line names `difft`, `/s:doctor`, or `semdiff doctor`

#### Scenario: A failed remedy reports its reason and a fix
- **GIVEN** the `difft` remedy exits non-zero with `brew: not found`
- **WHEN** the finish runs
- **THEN** the output carries one `warn difft — …` line containing
  `automatic install failed: brew: not found` and one `fix:` line under it

#### Scenario: A GitHub-side finding stays report-only with a fix
- **GIVEN** the `protection` check warns
- **WHEN** the finish runs
- **THEN** no remedy runs for it, and the output carries its `warn
  protection — …` line followed by a `fix:` line

#### Scenario: A failing check leaves the verb successful
- **WHEN** a check run at the end of a confirmed selection reports `fail`
- **THEN** its `fail` line and `fix:` line are printed and the verb still
  exits 0

### Requirement: Plugin-provided harness is reported, not generated
id: install-plugin-provided

Where a confirmed selection includes a harness whose user surface the
installed Claude Code plugin provides (requirement
`harness-plugin-provided`), the install SHALL write none of that harness's
command or agent files, SHALL retire its marker-owned ones, and SHALL
report it with a `provided` line naming the plugin instead of `installed`.

#### Scenario: Claude Code with the plugin installed is reported as provided
- **GIVEN** an isolated `HOME` whose Claude Code files show `s@shipd`
  installed at user scope and enabled, and one marker-owned file under
  `~/.claude/commands/shipd/`
- **WHEN** `install_selection(("claude-code",), out)` runs
- **THEN** it returns `None`, `out` carries a line with `provided`,
  `claude-code`, and `s@shipd`, and `~/.claude/commands/shipd/` and
  `~/.claude/agents/` hold no shipd file

#### Scenario: Claude Code without the plugin is still installed
- **WHEN** `install_selection(("claude-code",), out)` runs in an isolated
  `HOME` with no Claude Code plugin files
- **THEN** the command files exist under `~/.claude/commands/shipd/` and
  `out` reports `claude-code` as `installed`
