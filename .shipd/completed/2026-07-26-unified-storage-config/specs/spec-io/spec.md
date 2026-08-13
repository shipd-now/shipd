## ADDED Requirements

### Requirement: Staged emission with validate-then-install
id: staged-emission

A stdlib-Python `spec_emit.py` SHALL install spec content only after
validation: `change <name> --from <staging-dir>` SHALL copy the staged
artifact set to the resolved `<content-dir>/planned/<name>/`, run the
linter's change checks in-process, and on any finding remove everything it
installed and exit non-zero with the findings — an invalid change SHALL
never remain in the tree. `initiative <slug> --from <file>` SHALL install a
brief at the workspace's resolved brief path and validate it with the
initiative checks under the same remove-on-failure rule; `epic <slug>
--from <file>` likewise with the epic checks. If the destination already
exists, then the command SHALL refuse unless `--replace` is given.

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

### Requirement: Mediated spec reads
id: mediated-read-verb

The status CLI SHALL provide `cat change|verified|epic|initiative <slug>`
printing the named artifact's content — for a change, its `plan.md`, every
delta spec, and `tasks.md` — each file preceded by a `--- <relpath>`
separator line, resolving all locations through the engine's configuration.
An unknown name SHALL exit non-zero with an error.

#### Scenario: Change contents print with separators
- **WHEN** `cat change my-change` runs on a change with one delta spec
- **THEN** stdout holds three `--- <relpath>` separators followed by each
  file's content

#### Scenario: Unknown name errors
- **WHEN** `cat epic no-such-epic` runs
- **THEN** the CLI exits non-zero naming the missing epic

### Requirement: Engine-mediated skill access
id: engine-mediated-skill-access

Skills SHALL create and modify spec content only through engine verbs
(`spec_emit.py`, the status CLI's transition and header verbs, the merge
engine) and SHALL obtain spec content and locations only from engine output
(`cat`, `config-show`, show verbs). A skill SHALL NOT construct a storage
path from naming convention in either direction.

#### Scenario: Planning emits through the engine
- **WHEN** `/s:plan` reaches emission
- **THEN** the artifacts are authored in a staging area and installed via
  `spec_emit.py change`, not written directly into the spec tree

#### Scenario: Briefs are written through the engine
- **WHEN** `/s:initiative new` authors a brief
- **THEN** the brief reaches the workspace via `spec_emit.py initiative`,
  and the skill never writes to a workspace path it composed itself
