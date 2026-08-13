## MODIFIED Requirements

### Requirement: Workspace root discovery
id: workspace-root-discovery
base: 54da6739bfef

The engine SHALL locate the workspace root by upward search: starting from a
given directory and walking parent-by-parent to the filesystem root, the
nearest directory whose own `.shipd-config.json` declares a `workspace` key
SHALL be the workspace root, the starting directory itself included. If no
ancestor declares one, the search SHALL report that no workspace exists
rather than erroring. The search SHALL NOT require the starting directory or
the workspace root to be a git repository, and SHALL NOT consult any
`.shipd/` marker.

#### Scenario: Nearest declaring ancestor wins
- **GIVEN** `.shipd-config.json` files declaring `workspace` at `/ws/` and
  `/ws/nested/`
- **WHEN** discovery starts from `/ws/nested/repo`
- **THEN** the workspace root resolved is `/ws/nested`

#### Scenario: Config without a workspace key is not a root
- **GIVEN** `/repo/.shipd-config.json` declaring only `dir` and no ancestor
  declaring `workspace`
- **WHEN** discovery starts from `/repo`
- **THEN** the search returns no workspace root and raises no error

### Requirement: Workspace registry loading
id: workspace-registry-loading
base: 4e6e36ca7bce

The engine SHALL load a workspace's registry as the `workspace` object of
the workspace root's `.shipd-config.json`, preserving unknown keys inside it
for forward compatibility. If the `workspace` value is not a JSON object,
then the engine SHALL raise a clear error naming the file. The registry
loader SHALL NOT interpret or validate project entries beyond shape.

#### Scenario: Registry loads as a tolerant dict
- **GIVEN** a root config whose `workspace` object holds `projects` plus an
  unrecognized `future-key`
- **WHEN** the registry is loaded
- **THEN** the returned object carries both keys unchanged

#### Scenario: Non-object workspace value errors
- **WHEN** the root config declares `workspace: []`
- **THEN** loading raises an error naming `.shipd-config.json`

### Requirement: Initiative brief artifact
id: initiative-brief-format
base: 83c1a4f05270

An initiative brief SHALL live at
`<workspace-root>/<content-dir>/initiatives/<slug>/brief.md`, where
`<content-dir>` is the name resolved from the workspace root's configuration
(default `.am`). The brief SHALL begin with a `# <slug>` title matching its
directory and a `Status:` line whose value is one of `open`, `achieved`,
`dropped`. The header MAY carry a metadata block whose only recognized key
is `Project:` with a kebab-case value that SHALL name a project slug
declared in the workspace registry; where the registry declares no projects,
a `Project:` line SHALL be an error. The document SHALL carry a
`## Requirements` section holding at least one `- [ ]` checkbox requirement.

#### Scenario: Conforming brief is valid at the new path
- **WHEN** `<ws>/.shipd/initiatives/mvp-readiness/brief.md` starts with
  `# mvp-readiness`, `Status: open`, and carries a `## Requirements`
  section with two unticked checkboxes
- **THEN** tooling accepts the brief as structurally valid

#### Scenario: Brief without requirements is rejected
- **WHEN** a brief has a valid header but no `## Requirements` section
- **THEN** tooling reports the missing section

#### Scenario: Project scope must name a declared project
- **GIVEN** the registry declares only project `alpha`
- **WHEN** a brief carries `Project: beta`
- **THEN** tooling reports an error listing the declared project slugs

### Requirement: CI-safe initiative reference resolution
id: initiative-reference-resolution
base: fc04d3dcae07

When a workspace root is discoverable from the repository, an `Initiative:`
line on an epic or on a standalone change SHALL resolve to an existing brief
at `<workspace-root>/<content-dir>/initiatives/<slug>/brief.md`, and an
unresolvable reference SHALL be an error naming the expected path. When no
workspace root is discoverable, the resolution check SHALL be skipped
silently, so a bare checkout (CI) never depends on files outside the
repository.

#### Scenario: Missing brief errors when a workspace exists
- **GIVEN** a discoverable workspace with no `.shipd/initiatives/mvp-readiness/`
- **WHEN** an epic carrying `Initiative: mvp-readiness` is linted
- **THEN** an error names the expected brief path

#### Scenario: No workspace skips silently
- **WHEN** an epic carrying `Initiative: mvp-readiness` is linted in a
  checkout with no discoverable workspace
- **THEN** no initiative-reference error or warning is emitted

### Requirement: Project context convention
id: project-context-convention
base: 9ce51c807914

The system SHALL reserve
`<workspace-root>/<content-dir>/projects/<slug>/context.md` as optional
free-prose steering context for a project. Tooling SHALL NOT lint or require
the file; status verbs SHALL surface whether it exists.

#### Scenario: Missing context is never an error
- **WHEN** a declared project has no `.shipd/projects/<slug>/context.md`
- **THEN** no lint or status command reports an error for its absence

### Requirement: Workspace initialization
id: workspace-initialization
base: f1ea268061ea

When given an existing target directory, the engine SHALL initialize a
workspace by declaring `"workspace": {}` in `<target>/.shipd-config.json` —
creating the file when absent, otherwise preserving its other keys — and
SHALL report the created workspace root. If a workspace root is already
discoverable from the target (nearest-ancestor search, the target itself
included), then initialization SHALL refuse with an error naming the
existing root and SHALL write nothing. If the target directory does not
exist, then initialization SHALL error rather than create it.

#### Scenario: Init declares the workspace in the config file
- **GIVEN** an existing directory with no discoverable workspace and no
  config file
- **WHEN** workspace initialization runs against it
- **THEN** `.shipd-config.json` exists under it declaring an empty `workspace`
  object and the directory is reported as the created workspace root

#### Scenario: Init preserves existing config keys
- **GIVEN** a target whose `.shipd-config.json` declares `dir` but no
  `workspace`
- **WHEN** initialization runs against it
- **THEN** the file declares both `dir` and `workspace` afterwards

#### Scenario: Init refuses under an existing workspace
- **GIVEN** a directory whose ancestor's config declares `workspace`
- **WHEN** workspace initialization runs against it
- **THEN** it errors naming the existing workspace root and writes nothing
