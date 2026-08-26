## ADDED Requirements

### Requirement: Artefact reference enforcement
id: artefact-reference-enforcement

Where a change carries an `artefacts/` directory, the linter's change checks
SHALL error — not warn — for every file inside it whose change-relative path
appears in none of `plan.md`, `tasks.md`, or the change's delta specs, naming
the unreferenced artefact and its path. A file is referenced when its
change-relative POSIX path (`artefacts/<file>`, including any nested
directories) occurs anywhere in the text of those artifacts. Because the emit
engine installs only after the change checks pass, an unreferenced artefact
SHALL therefore prevent the change from being installed. A change with no
`artefacts/` directory, or one holding no files, SHALL lint exactly as it does
without this check.

#### Scenario: Unreferenced artefact is an error
- **GIVEN** a change whose `artefacts/policy.md` is named nowhere in its
  artifacts
- **WHEN** the change is linted
- **THEN** the linter reports an error naming `artefacts/policy.md` and exits
  non-zero

#### Scenario: Referenced artefact lints clean
- **GIVEN** a change whose `plan.md` names `artefacts/policy.md`
- **WHEN** the change is linted
- **THEN** no artefact finding is reported

#### Scenario: An unreferenced artefact blocks the install
- **WHEN** a staging directory carrying an unreferenced `artefacts/policy.md`
  is installed with `spec_emit.py change`
- **THEN** the finding is printed, the command exits non-zero, and the spec
  tree gains no change directory

#### Scenario: A change without artefacts is unaffected
- **GIVEN** a change with no `artefacts/` directory
- **WHEN** the change is linted
- **THEN** the findings are exactly those the other change checks produce
