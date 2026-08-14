## ADDED Requirements

### Requirement: Workspace status verbs
id: workspace-status-verbs

The status CLI SHALL provide `workspace-show` printing the workspace root,
each declared project with its repos (annotated when a path is not a
directory on this machine) and whether its `context.md` exists, each
initiative with its status and project scope, and a note that the current
repository falls under the implicit default project when it resolves to no
declared project; and `project-show <slug>` printing one declared project's
repos (annotated), its `context.md` presence, and the initiatives scoped to
it. An undeclared slug SHALL be a non-zero error naming the declared slugs.
Both verbs SHALL resolve the workspace from the repository root and SHALL
exit non-zero with a clear error when no workspace is discoverable.

#### Scenario: Workspace overview lists projects and initiatives
- **GIVEN** a workspace declaring project `alpha` (one repo present, one
  absent, no context.md) and an initiative `mvp-readiness` scoped
  `Project: alpha`
- **WHEN** `workspace-show` runs
- **THEN** the output lists `alpha` with both repos (one annotated absent),
  `context: no`, and `mvp-readiness` with its status and `alpha` scope

#### Scenario: Project view shows scoped initiatives
- **WHEN** `project-show alpha` runs in that workspace
- **THEN** the output lists alpha's repos, its context presence, and
  `mvp-readiness` among its scoped initiatives

#### Scenario: Unknown project slug errors
- **GIVEN** the registry declares only `alpha`
- **WHEN** `project-show beta` runs
- **THEN** the CLI exits non-zero naming the declared slugs

#### Scenario: Verbs require a workspace
- **WHEN** `workspace-show` runs in a checkout with no discoverable
  workspace
- **THEN** the CLI exits non-zero saying no workspace was found
