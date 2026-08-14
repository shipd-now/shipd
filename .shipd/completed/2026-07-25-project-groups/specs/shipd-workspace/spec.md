## ADDED Requirements

### Requirement: Project registry semantics
id: project-registry-semantics

The workspace registry's `projects` entry SHALL map kebab-case project slugs
to objects whose `repos` value is a list of non-empty workspace-root-relative
path strings. Validation SHALL check shape only — a listed repo path absent
on disk SHALL never be an error. If the same repo path appears in more than
one project, validation SHALL report an ambiguous-ownership error.

#### Scenario: Conforming registry validates clean
- **WHEN** the registry declares `projects: {"alpha": {"repos": ["shipd",
  "apps/backend"]}}` and neither path exists on disk
- **THEN** validation reports no errors

#### Scenario: Duplicate repo path errors
- **WHEN** projects `alpha` and `beta` both list the repo path `shared-lib`
- **THEN** validation reports an ambiguous-ownership error naming the path

#### Scenario: Malformed project entry errors
- **WHEN** a project's `repos` value is a string rather than a list
- **THEN** validation reports a shape error naming the project slug

### Requirement: Project resolution by containment
id: project-resolution

The engine SHALL resolve which project owns a path via
`project_of(workspace_root, path)`: the project whose repo entry equals or
contains the path, the longest (most specific) matching entry winning across
projects. A path matching no entry SHALL resolve to `None`, denoting the
implicit default project, which is anonymous and SHALL NOT be referenceable
by any slug.

#### Scenario: Most specific entry wins
- **GIVEN** project `alpha` lists `apps` and project `beta` lists
  `apps/backend`
- **WHEN** `project_of` resolves `apps/backend/repo-x`
- **THEN** the result is `beta`

#### Scenario: Unmatched path is the implicit default
- **WHEN** `project_of` resolves a path listed by no project
- **THEN** the result is `None` and no slug denotes that implicit project

### Requirement: Project context convention
id: project-context-convention

The system SHALL reserve `<workspace-root>/projects/<slug>/context.md` as
optional free-prose steering context for a project. Tooling SHALL NOT lint
or require the file; status verbs SHALL surface whether it exists.

#### Scenario: Missing context is never an error
- **WHEN** a declared project has no `projects/<slug>/context.md`
- **THEN** no lint or status command reports an error for its absence

## MODIFIED Requirements

### Requirement: Initiative brief artifact
id: initiative-brief-format
base: 4f30837cf9e9

An initiative brief SHALL live at
`<workspace-root>/initiatives/<slug>/brief.md`, beginning with a `# <slug>`
title matching its directory and a `Status:` line whose value is one of
`open`, `achieved`, `dropped`. The header MAY carry a metadata block whose
only recognized key is `Project:` with a kebab-case value that SHALL name a
project slug declared in the workspace registry; where the registry declares
no projects, a `Project:` line SHALL be an error. The document SHALL carry a
`## Requirements` section holding at least one `- [ ]` checkbox requirement
— outcomes ticked over time, not tasks. Prose stating the goal MAY precede
the Requirements section.

#### Scenario: Conforming brief is valid
- **WHEN** `<ws>/initiatives/mvp-readiness/brief.md` starts with
  `# mvp-readiness`, `Status: open`, and carries a `## Requirements` section
  with two unticked checkboxes
- **THEN** tooling accepts the brief as structurally valid

#### Scenario: Brief without requirements is rejected
- **WHEN** a brief has a valid header but no `## Requirements` section
- **THEN** tooling reports the missing section

#### Scenario: Unknown metadata key is rejected
- **WHEN** a brief's header carries `Theme: reliability`
- **THEN** tooling reports an unrecognized-key error

#### Scenario: Project scope must name a declared project
- **GIVEN** the registry declares only project `alpha`
- **WHEN** a brief carries `Project: beta`
- **THEN** tooling reports an error listing the declared project slugs

#### Scenario: Project scope with no declared projects errors
- **GIVEN** the registry declares no projects
- **WHEN** a brief carries `Project: alpha`
- **THEN** tooling reports that no projects are declared in the workspace
  registry
