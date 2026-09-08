## MODIFIED Requirements

### Requirement: Project registry semantics
id: project-registry-semantics
base: b6aca191e578

The workspace registry's `projects` entry SHALL map project names to objects
whose `repos` value is a list of entries, where each entry is either a
non-empty workspace-root-relative path string or an object carrying a
required non-empty string `path` and optional non-empty string `url`
(clone source) and `branch` (default branch) values. A project name SHALL
consist of ASCII letters and digits joined by single `-`, `_`, or `.`
separators (pattern `^[A-Za-z0-9]+(?:[-_.][A-Za-z0-9]+)*$`), so every name is
a safe directory component; case SHALL be preserved and references SHALL
match names exactly. If two declared project names are equal under Unicode
case folding, then validation SHALL report a duplicate-name error naming both
names. Validation SHALL check shape only — a listed repo path absent on disk
SHALL never be an error. If the same resolved repo path appears in more than
one project, regardless of entry shape, validation SHALL report an
ambiguous-ownership error.

#### Scenario: Conforming registry validates clean
- **WHEN** the registry declares `projects: {"alpha": {"repos": ["shipd",
  {"path": "apps/backend", "url": "git@example.com:backend.git",
  "branch": "main"}]}}` and neither path exists on disk
- **THEN** validation reports no errors

#### Scenario: Mixed-case and underscore names validate clean
- **WHEN** the registry declares projects named `APISchema` and `api_schema2`
- **THEN** validation reports no name errors

#### Scenario: Name with whitespace errors
- **WHEN** the registry declares a project named `API Schema`
- **THEN** validation reports an invalid-project-name error naming it

#### Scenario: Case-folded duplicate names error
- **WHEN** the registry declares projects named `APISchema` and `apischema`
- **THEN** validation reports a duplicate-name error naming both

#### Scenario: Object entry without a path errors
- **WHEN** a repos entry is `{"url": "git@example.com:x.git"}` with no
  `path`
- **THEN** validation reports a shape error naming the project name

#### Scenario: Duplicate repo path errors across shapes
- **WHEN** project `alpha` lists the string entry `shared-lib` and project
  `beta` lists `{"path": "shared-lib"}`
- **THEN** validation reports an ambiguous-ownership error naming the path

#### Scenario: Malformed project entry errors
- **WHEN** a project maps to a non-object value
- **THEN** validation reports a shape error naming the project name

### Requirement: Workspace focus declaration
id: workspace-focus
base: 9531f14cfa76

The workspace object MAY declare a `focus` key naming the job's primary
project. When present, validation SHALL require it to be a valid project
name (ASCII letters and digits joined by single `-`, `_`, or `.` separators)
that exactly matches a project declared in the same registry — a same-file
consistency check that SHALL never consult the disk. An unknown or malformed
focus value SHALL be a validation error naming the declared project names.

#### Scenario: Declared focus validates clean
- **WHEN** the workspace declares `focus: "documents"` and `projects`
  declares `documents`
- **THEN** validation reports no errors

#### Scenario: Mixed-case focus validates clean
- **WHEN** the workspace declares `focus: "APISchema"` and `projects`
  declares `APISchema`
- **THEN** validation reports no errors

#### Scenario: Unknown focus errors
- **WHEN** the workspace declares `focus: "missing"` and no such project is
  declared
- **THEN** validation reports an error naming the declared project names

### Requirement: Initiative brief artifact
id: initiative-brief-format
base: 3a25d9735034

An initiative brief SHALL live at
`<workspace-root>/<content-dir>/initiatives/<slug>/brief.md`, where
`<content-dir>` is the name resolved from the workspace root's configuration
(default `.shipd`). The brief SHALL begin with a `# <slug>` title matching its
directory and a `Status:` line whose value is one of `open`, `achieved`,
`dropped`. The header MAY carry a metadata block whose only recognized key
is `Project:` with a valid project-name value (ASCII letters and digits
joined by single `-`, `_`, or `.` separators) that SHALL exactly match a
project name declared in the workspace registry; where the registry declares
no projects, a `Project:` line SHALL be an error. The document SHALL carry a
`## Requirements` section holding at least one `- [ ]` checkbox requirement.

#### Scenario: Conforming brief is valid at the new path
- **WHEN** `<ws>/.shipd/initiatives/mvp-readiness/brief.md` starts with
  `# mvp-readiness`, `Status: open`, and carries a `## Requirements`
  section with two unticked checkboxes
- **THEN** tooling accepts the brief as structurally valid

#### Scenario: Mixed-case Project scope resolves
- **GIVEN** the registry declares a project named `APISchema`
- **WHEN** a brief carries `Project: APISchema`
- **THEN** tooling reports no Project-scope error

#### Scenario: Brief without requirements is rejected
- **WHEN** a brief has a valid header but no `## Requirements` section
- **THEN** tooling reports the missing section

#### Scenario: Project scope must name a declared project
- **GIVEN** the registry declares only project `alpha`
- **WHEN** a brief carries `Project: beta`
- **THEN** tooling reports an error listing the declared project names
