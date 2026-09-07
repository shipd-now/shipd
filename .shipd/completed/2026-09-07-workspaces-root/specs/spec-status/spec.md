## MODIFIED Requirements

### Requirement: Workspace init verb
id: workspace-init-verb
base: 519a0c538075

The status CLI SHALL provide `workspace-init <path>` which initializes a
workspace at the given directory through the engine's workspace
initialization — declaring `workspace` in `<path>/.shipd-config.json` — and
prints the created workspace root on success. The verb SHALL accept a `--git`
flag requesting the engine's git option (git-init when the target is not
already inside a work tree, plus the seeded member-repos `.gitignore` block),
and a `--nested` flag requesting the engine's nested option, which permits
creating the workspace beneath an enclosing one and reports the enclosing root
it nests under. If initialization refuses or errors (a workspace already
discoverable from the target without `--nested`, a target that itself already
declares `workspace`, or a missing target directory), then the CLI SHALL exit
non-zero with that error. Unlike the other workspace verbs, `workspace-init`
SHALL NOT require a discoverable workspace to run. Where the layered
configuration declares `workspaces_root` (shipd-config workspaces-root-key),
the verb SHALL inherit the engine's mandated-root behavior unchanged: a bare
name resolves into the declared root and is printed as the created root, and
a refused target — an explicit path outside the root, or a bare name whose
declared root is missing — SHALL exit non-zero with the engine's error naming
`workspaces_root`.

#### Scenario: Init verb creates and prints the root
- **GIVEN** an existing directory with no discoverable workspace
- **WHEN** `workspace-init <path>` runs against it
- **THEN** `.shipd-config.json` declares `workspace` there, the created root is
  printed, and the exit code is zero

#### Scenario: Init verb refuses under an existing workspace
- **WHEN** `workspace-init <path>` runs where a workspace root is already
  discoverable from `<path>`
- **THEN** the CLI exits non-zero with an error naming the existing root

#### Scenario: Nested flag creates the nested workspace
- **WHEN** `workspace-init <path> --nested` runs where a workspace root is
  already discoverable from `<path>`
- **THEN** `<path>/.shipd-config.json` declares `workspace`, the enclosing root
  is reported, and the exit code is zero

#### Scenario: Git flag produces a git-ready root
- **GIVEN** an existing directory with no discoverable workspace and no git
  work tree
- **WHEN** `workspace-init <path> --git` runs
- **THEN** the created root is a git repository whose `.gitignore` carries
  the marked member-repos block, and the exit code is zero

#### Scenario: Bare name resolves through the verb
- **GIVEN** a config layer declaring `workspaces_root` naming an existing
  directory
- **WHEN** `workspace-init acme-job` runs
- **THEN** the printed created root is `<workspaces_root>/acme-job` and the
  exit code is zero

#### Scenario: Outside target exits non-zero through the verb
- **GIVEN** a config layer declaring `workspaces_root`
- **WHEN** `workspace-init <path>` runs against an explicit path outside the
  declared root
- **THEN** the CLI exits non-zero with an error naming the target, the
  declared root, and `workspaces_root`
