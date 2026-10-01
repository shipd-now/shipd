## MODIFIED Requirements

### Requirement: Workspace universe discovery seam
id: workspace-universe-discovery
base: 39577ac6a61a

The engine SHALL provide a single shared workspace-universe discovery seam in
the stdlib configuration module (`spec_common`): `workspace_project_roots(root)`
returning `(project_slug, repo_root)` pairs for the declared workspace project
repos, and `aggregation_universes(root)` returning `[(None, root)]` followed by
those pairs. The pairs SHALL be non-empty only when a project registry is
discoverable from `root` (`registry_root`) AND `root` lies inside no declared
project repo (`project_of` yields the implicit default) — projects in slug
order, each project's repos in declaration order, every path resolved against
the registry root. While `root`'s real path lies strictly beneath the registry
root's real path — a project folder or any other intermediate directory — the
seam SHALL return only the declared repos whose real path lies beneath
`root`'s real path, in the same order; a `root` equal to the registry root, or
outside it, SHALL return every declared repo as before. The seam SHALL be
fail-soft: an unloadable registry, a non-object project or repo entry, a path
that is not a directory on this machine, an entry duplicating an earlier
entry's real path, and an entry resolving to the invocation root's own real
path SHALL each be skipped silently, never raised. Every read surface that
aggregates or resolves across declared workspace projects SHALL obtain its
universes through this seam, never through a private reimplementation.

#### Scenario: Workspace-level invocation yields the declared repos
- **GIVEN** a workspace root declaring two projects whose repo directories
  exist on disk
- **WHEN** `workspace_project_roots` runs with that root
- **THEN** both repos are returned in project slug order and
  `aggregation_universes` lists `(None, root)` first, then those pairs

#### Scenario: A project folder yields only the repos beneath it
- **GIVEN** a workspace root declaring project `alpha` with repos under
  `alpha/` and project `beta` with a repo under `beta/`, all present on disk
- **WHEN** `workspace_project_roots` runs with `<root>/alpha` as its root
- **THEN** only `alpha`'s repos are returned, in declaration order, and
  `aggregation_universes` lists `(None, <root>/alpha)` first, then those pairs

#### Scenario: An intermediate folder holding no repo yields nothing
- **GIVEN** the same workspace and a directory `<root>/scratch` beneath the
  registry root that contains no declared repo
- **WHEN** `workspace_project_roots` runs with that directory as its root
- **THEN** it returns an empty list and `aggregation_universes` returns only
  the invocation root's own universe

#### Scenario: Inside a member repo the seam yields nothing
- **GIVEN** the same workspace, resolved from inside a declared project repo
- **WHEN** `workspace_project_roots` runs
- **THEN** it returns an empty list and `aggregation_universes` returns only
  the invocation root's own universe

#### Scenario: Invalid registry entries are skipped, never raised
- **GIVEN** a registry declaring an absent repo path, a duplicate real path,
  and an entry resolving to the invocation root itself
- **WHEN** the seam runs
- **THEN** each such entry is skipped and the remaining valid repos are
  returned without an exception

#### Scenario: No registry means the single universe
- **GIVEN** a root with no workspace discoverable
- **WHEN** `aggregation_universes` runs
- **THEN** it returns exactly `[(None, root)]`

#### Scenario: The workspace docs state the folder rule
- **WHEN** `docs/workspaces/teams.md` and
  `docs/workspaces/multi-workspace-repos.md` are read
- **THEN** each states that `shipd board` covers every declared project's
  repos from the workspace root and only the repos beneath the folder it runs
  from otherwise, and each stays within its how-to line cap
