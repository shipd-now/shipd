## ADDED Requirements

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
