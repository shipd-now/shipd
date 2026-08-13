## MODIFIED Requirements

### Requirement: Project registry semantics
id: project-registry-semantics
base: 17920e82d496

The workspace registry's `projects` entry SHALL map kebab-case project slugs
to objects whose `repos` value is a list of entries, where each entry is
either a non-empty workspace-root-relative path string or an object carrying
a required non-empty string `path` and optional non-empty string `url`
(clone source) and `branch` (default branch) values. Validation SHALL check
shape only — a listed repo path absent on disk SHALL never be an error. If
the same resolved repo path appears in more than one project, regardless of
entry shape, validation SHALL report an ambiguous-ownership error.

#### Scenario: Conforming registry validates clean
- **WHEN** the registry declares `projects: {"alpha": {"repos": ["shipd",
  {"path": "apps/backend", "url": "git@example.com:backend.git",
  "branch": "main"}]}}` and neither path exists on disk
- **THEN** validation reports no errors

#### Scenario: Object entry without a path errors
- **WHEN** a repos entry is `{"url": "git@example.com:x.git"}` with no
  `path`
- **THEN** validation reports a shape error naming the project slug

#### Scenario: Duplicate repo path errors across shapes
- **WHEN** project `alpha` lists the string entry `shared-lib` and project
  `beta` lists `{"path": "shared-lib"}`
- **THEN** validation reports an ambiguous-ownership error naming the path

#### Scenario: Malformed project entry errors
- **WHEN** a project's `repos` value is a string rather than a list
- **THEN** validation reports a shape error naming the project slug

### Requirement: Workspace initialization
id: workspace-initialization
base: 9d227a12d953

When given an existing target directory, the engine SHALL initialize a
workspace by declaring `"workspace": {}` in `<target>/.shipd-config.json` —
creating the file when absent, otherwise preserving its other keys — and
SHALL report the created workspace root. If a workspace root is already
discoverable from the target (nearest-ancestor search, the target itself
included), then initialization SHALL refuse with an error naming the
existing root and SHALL write nothing. If the target directory does not
exist, then initialization SHALL error rather than create it. Where the git
option is requested, initialization SHALL additionally run `git init` at the
target when it is not already inside a git work tree, and SHALL ensure the
target's `.gitignore` carries the marked member-repos block, appending an
empty marked block only when the markers are absent — using local git
operations only, never the network.

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

#### Scenario: Git option seeds a repo and the ignore block
- **GIVEN** an existing target directory that is not inside any git work
  tree
- **WHEN** initialization runs with the git option
- **THEN** the target is a git repository afterwards and its `.gitignore`
  contains the marked member-repos block

#### Scenario: Git option inside an existing work tree does not re-init
- **GIVEN** a target directory already inside a git work tree whose
  `.gitignore` already carries the marked block
- **WHEN** initialization runs with the git option
- **THEN** no new git repository is created and the `.gitignore` block is
  not duplicated

## ADDED Requirements

### Requirement: Workspace focus declaration
id: workspace-focus

The workspace object MAY declare a `focus` key naming the job's primary
project. When present, validation SHALL require it to be a kebab-case slug
naming a project declared in the same registry — a same-file consistency
check that SHALL never consult the disk. An unknown or malformed focus value
SHALL be a validation error naming the declared slugs.

#### Scenario: Declared focus validates clean
- **WHEN** the workspace declares `focus: "documents"` and `projects`
  declares `documents`
- **THEN** validation reports no errors

#### Scenario: Unknown focus errors
- **WHEN** the workspace declares `focus: "missing"` and no such project is
  declared
- **THEN** validation reports an error naming the declared project slugs
