## MODIFIED Requirements

### Requirement: Workspace init verb
id: workspace-init-verb
base: 6fe945c00c26

The status CLI SHALL provide `workspace-init <path>` which initializes a
workspace at the given directory through the engine's workspace
initialization — declaring `workspace` in `<path>/.shipd-config.json` — and
prints the created workspace root on success. The verb SHALL accept a
`--git` flag requesting the engine's git option (git-init when the target is
not already inside a work tree, plus the seeded member-repos `.gitignore`
block). If initialization refuses or errors (a workspace already
discoverable from the target, or a missing target directory), then the CLI
SHALL exit non-zero with that error. Unlike the other workspace verbs,
`workspace-init` SHALL NOT require a discoverable workspace to run.

#### Scenario: Init verb creates and prints the root
- **GIVEN** an existing directory with no discoverable workspace
- **WHEN** `workspace-init <path>` runs against it
- **THEN** `.shipd-config.json` declares `workspace` there, the created root is
  printed, and the exit code is zero

#### Scenario: Init verb refuses under an existing workspace
- **WHEN** `workspace-init <path>` runs where a workspace root is already
  discoverable from `<path>`
- **THEN** the CLI exits non-zero with an error naming the existing root

#### Scenario: Git flag produces a git-ready root
- **GIVEN** an existing directory with no discoverable workspace and no git
  work tree
- **WHEN** `workspace-init <path> --git` runs
- **THEN** the created root is a git repository whose `.gitignore` carries
  the marked member-repos block, and the exit code is zero

### Requirement: Workspace status verbs
id: workspace-status-verbs
base: 4e94a7489b9e

The status CLI SHALL provide `workspace-show` printing the workspace root,
the declared `focus` project when the registry carries one, each declared
project with its repos (annotated when a path is not a directory on this
machine, and annotated `[url]` when the entry carries a clone URL) and
whether its `context.md` exists, each initiative with its status and project
scope, and a note that the current repository falls under the implicit
default project when it resolves to no declared project; and `project-show
<slug>` printing one declared project's repos (annotated the same way), its
`context.md` presence, and the initiatives scoped to it. An undeclared slug
SHALL be a non-zero error naming the declared slugs. Both verbs SHALL
resolve repo paths uniformly from string and object entry shapes, SHALL
resolve the workspace from the repository root, and SHALL exit non-zero with
a clear error when no workspace is discoverable.

#### Scenario: Workspace overview lists projects and initiatives
- **GIVEN** a workspace declaring project `alpha` (one repo present, one
  absent, no context.md) and an initiative `mvp-readiness` scoped
  `Project: alpha`
- **WHEN** `workspace-show` runs
- **THEN** the output lists `alpha` with both repos (one annotated absent),
  `context: no`, and `mvp-readiness` with its status and `alpha` scope

#### Scenario: Focus and clone URLs surface in the overview
- **GIVEN** a registry declaring `focus: "alpha"` and an alpha repo entry
  carrying a `url`
- **WHEN** `workspace-show` runs
- **THEN** the output names `alpha` as the focus and annotates that repo
  line `[url]`

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
