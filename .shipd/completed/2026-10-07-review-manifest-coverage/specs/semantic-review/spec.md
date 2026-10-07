## MODIFIED Requirements

### Requirement: Cohort grouping subcommand
id: cohort-grouping
base: 8b7c9cca6afc

The system SHALL provide `semdiff files <base> [<head>]` grouping changed
paths into architectural cohorts using segment-aware rules (contracts,
database, api, frontend, tests; plus shipd-aware groups for content-dir
spec artifacts and plugin skills), falling back to the path's top-level
directory, and emitting JSON with the cohort map and file/cohort counts. A
packaging or dependency manifest SHALL group into `contracts` wherever in the
tree it sits, since it declares what the package ships, exports and depends
on. Manifests do not share one naming convention, so the match SHALL cover
all three shapes they take: an exact basename (`package.json` and its
lockfiles, `go.mod`/`go.sum`/`go.work`, `Cargo.toml`, `pyproject.toml`,
`requirements.txt`, `uv.lock`, `Gemfile`, `Podfile`, `composer.json`,
`pom.xml`, `build.gradle`, `build.sbt`, `Directory.Packages.props`,
`packages.lock.json`, `Package.swift`, `Package.resolved`, `mix.exs`,
`pubspec.yaml` and their lock equivalents); a project-specific suffix, where
the file is named after its project or package (`.csproj`, `.fsproj`,
`.vbproj`, `.gemspec`, `.nuspec`, `.cabal`); and the `requirements*.txt`
family, whose split files declare as much as the plain one. An exact-name set
alone SHALL NOT be relied on, since it silently omits every ecosystem naming
its manifest after the project.

#### Scenario: Segment-aware grouping
- **WHEN** `semdiff files main` runs over changes touching
  `plugins/s/skills/review/SKILL.md` and `.shipd/planned/x/plan.md`
- **THEN** the two paths land in the skills and specs cohorts, not in a
  generic top-level bucket

#### Scenario: A manifest groups as a contract wherever it sits
- **WHEN** `semdiff files main` runs over changes touching `package.json`,
  `server/package.json`, `go.mod` and `tests/fixtures/package.json`
- **THEN** all four land in the contracts cohort, the fixture one included

#### Scenario: A manifest named after its project still groups as a contract
- **WHEN** `semdiff files main` runs over changes touching a C# project
  file, a gemspec, and a `requirements-dev.txt`
- **THEN** each lands in the contracts cohort, which an exact-basename match
  alone would have missed

#### Scenario: The manifest match does not over-capture
- **WHEN** the same run also touches an api route module, a frontend
  component, a test module and an unrelated top-level file
- **THEN** none of them lands in the contracts cohort
