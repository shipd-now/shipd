## MODIFIED Requirements

### Requirement: Doctor preflight closes the install finish
id: install-doctor-finish
base: 8de6347382d3
Dropped: A confirmed selection ends with the preflight
Dropped: An empty confirmed selection still ends with the preflight
Dropped: An aborted flow runs no preflight
Dropped: A failing preflight leaves the verb successful
Dropped: Problems carry the doctor pointer

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
