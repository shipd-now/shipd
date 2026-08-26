## MODIFIED Requirements

### Requirement: Mediated spec reads
id: mediated-read-verb
base: eb31607e8331

The status CLI SHALL provide `cat change|verified|epic|initiative|research|video
<slug>` printing the named artifact's content — for a change, its `plan.md`,
every delta spec, and `tasks.md`; for research, the report at the resolved
`<content-dir>/research/<slug>/report.md`; for video, the brief at the resolved
`<content-dir>/video/<slug>/brief.md` — each file preceded by a
`--- <relpath>` separator line, resolving all locations through the engine's
configuration. For a change, the CLI SHALL resolve `planned/<slug>/` first
and, when absent, SHALL fall back to the archived `completed/*-<slug>/`
directory, selecting the newest (lexicographically last) archive when several
match. An unknown name SHALL exit non-zero with an error.

Where the resolved change directory carries an `artefacts/` directory holding at
least one file, `cat change` SHALL additionally print, after the artifact
contents, a `--- artefacts` header followed by one line per artefact giving its
path relative to the invocation root and its size in bytes, sorted by path. The
CLI SHALL print the artefacts' paths and sizes only, never their contents, so a
mediated read stays within the context-economy budget. Where the change carries
no such directory, or the directory holds no files, the output SHALL be exactly
what it is without the directory.

#### Scenario: Change contents print with separators
- **WHEN** `cat change my-change` runs on a change with one delta spec
- **THEN** stdout holds three `--- <relpath>` separators followed by each
  file's content

#### Scenario: Completed change still prints after archive
- **WHEN** `cat change my-change` runs after the change was archived to
  `completed/2026-08-14-my-change/`
- **THEN** stdout prints that archive's artifacts with `--- <relpath>`
  separators instead of exiting non-zero

#### Scenario: Artefacts are listed, not dumped
- **WHEN** `cat change my-change` runs on a change whose `artefacts/` directory
  holds `policy.md`
- **THEN** stdout ends with a `--- artefacts` header and a line naming
  `policy.md`'s root-relative path and byte size, and the file's content does
  not appear

#### Scenario: A change without artefacts prints unchanged
- **WHEN** `cat change my-change` runs on a change with no `artefacts/`
  directory
- **THEN** stdout carries no `--- artefacts` header

#### Scenario: Research report prints with a separator
- **WHEN** `cat research payment-apis` runs on an installed report
- **THEN** stdout holds one `--- <relpath>` separator followed by the
  report's content

#### Scenario: Video brief prints with a separator
- **WHEN** `cat video board-walkthrough` runs on an installed brief
- **THEN** stdout holds one `--- <relpath>` separator followed by the
  brief's content

#### Scenario: Unknown name errors
- **WHEN** `cat epic no-such-epic` runs
- **THEN** the CLI exits non-zero naming the missing epic
