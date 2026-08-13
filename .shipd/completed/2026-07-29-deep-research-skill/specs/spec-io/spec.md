## MODIFIED Requirements

### Requirement: Staged emission with validate-then-install
id: staged-emission
base: 9a0d646b5f82

A stdlib-Python `spec_emit.py` SHALL install spec content only after
validation: `change <name> --from <staging-dir>` SHALL copy the staged
artifact set to the resolved `<content-dir>/planned/<name>/`, run the
linter's change checks in-process, and on any finding remove everything it
installed and exit non-zero with the findings — an invalid change SHALL
never remain in the tree. `initiative <slug> --from <file>` SHALL install a
brief at the workspace's resolved brief path and validate it with the
initiative checks under the same remove-on-failure rule; `epic <slug>
--from <file>` likewise with the epic checks; `research <slug> --from
<file>` likewise SHALL install a research report at the resolved
`<content-dir>/research/<slug>/report.md` and validate it with the research
report checks. If the destination already exists, then the command SHALL
refuse unless `--replace` is given.

#### Scenario: Clean staged change is installed
- **GIVEN** a staging directory holding a lint-clean plan.md, delta specs,
  and tasks.md
- **WHEN** `spec_emit.py change my-change --from <staging>` runs
- **THEN** `<content-dir>/planned/my-change/` holds the artifacts and the
  exit code is zero

#### Scenario: Invalid staged change never lands
- **WHEN** `spec_emit.py change my-change --from <staging>` runs on staged
  artifacts with a lint error
- **THEN** the findings are printed, the exit code is non-zero, and
  `<content-dir>/planned/my-change/` does not exist

#### Scenario: Existing destination is refused
- **GIVEN** `<content-dir>/planned/my-change/` already exists
- **WHEN** the command runs without `--replace`
- **THEN** it refuses non-zero and the existing content is untouched

#### Scenario: Clean staged report is installed
- **WHEN** `spec_emit.py research payment-apis --from <staging report>` runs
  on a report passing the research checks
- **THEN** `<content-dir>/research/payment-apis/report.md` holds the report
  and the exit code is zero

#### Scenario: Invalid staged report never lands
- **WHEN** `spec_emit.py research payment-apis --from <staging report>` runs
  on a report with an unresolved citation marker
- **THEN** the findings are printed, the exit code is non-zero, and
  `<content-dir>/research/payment-apis/` does not exist

### Requirement: Mediated spec reads
id: mediated-read-verb
base: fc90f5f33216

The status CLI SHALL provide `cat change|verified|epic|initiative|research
<slug>` printing the named artifact's content — for a change, its `plan.md`,
every delta spec, and `tasks.md`; for research, the report at the resolved
`<content-dir>/research/<slug>/report.md` — each file preceded by a
`--- <relpath>` separator line, resolving all locations through the engine's
configuration. An unknown name SHALL exit non-zero with an error.

#### Scenario: Change contents print with separators
- **WHEN** `cat change my-change` runs on a change with one delta spec
- **THEN** stdout holds three `--- <relpath>` separators followed by each
  file's content

#### Scenario: Research report prints with a separator
- **WHEN** `cat research payment-apis` runs on an installed report
- **THEN** stdout holds one `--- <relpath>` separator followed by the
  report's content

#### Scenario: Unknown name errors
- **WHEN** `cat epic no-such-epic` runs
- **THEN** the CLI exits non-zero naming the missing epic
