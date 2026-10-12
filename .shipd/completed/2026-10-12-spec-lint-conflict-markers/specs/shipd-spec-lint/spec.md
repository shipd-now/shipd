## ADDED Requirements

### Requirement: Conflict marker rejection
id: conflict-marker-rejection

The linter SHALL reject any markdown file it reads that carries a git conflict
marker at the start of a line — `<<<<<<<`, `=======`, or `>>>>>>>` — reporting
the file and the line number of each marker, and SHALL cover master capability
specs, change delta specs, `plan.md`, and `tasks.md`.

A conflict marker is never valid content in these files, and a file carrying
one has been committed mid-merge. The library carried
`.shipd/verified/delivery-dashboard/spec.md`'s `<<<<<<< HEAD` and
`>>>>>>> origin/main` from 2026-08-14 until this requirement existed, bracketing
six requirements, while the linter reported the library valid — so every
lint-clean claim made in that window was weaker than it read. The check SHALL
be an error and not a warning, because a warning leaves the exit code clean and
the exit code is what every gate reads.

The `=======` form SHALL NOT be matched at all. A markdown setext heading
underlines with repeated `=`, and an underline of exactly seven characters is
byte-identical to the marker, so no match separates them and rejecting it would
reject valid documents. Nothing is lost by the omission: a conflict always
writes all three markers, so the unambiguous outer pair detects every one.

#### Scenario: A master spec carrying a conflict marker is rejected
- **WHEN** a master capability spec contains a line beginning `<<<<<<<`
- **THEN** the linter reports that file and line and exits non-zero

#### Scenario: A delta spec carrying a conflict marker is rejected
- **WHEN** a change's delta spec contains a line beginning `>>>>>>>`
- **THEN** the linter reports that file and line and exits non-zero

#### Scenario: A plan or task file carrying a conflict marker is rejected
- **WHEN** a change's `plan.md` or `tasks.md` contains a conflict marker line
- **THEN** the linter reports that file and line and exits non-zero

#### Scenario: A setext heading is not a conflict marker
- **WHEN** a file underlines a heading with `=` characters, including exactly
  seven of them
- **THEN** the linter reports no conflict marker for it
