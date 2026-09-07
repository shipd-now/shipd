## MODIFIED Requirements

### Requirement: Workspace initialization
id: workspace-initialization
base: 3bc6305d33e0

When given an existing target directory, the engine SHALL initialize a
workspace by declaring `"workspace": {}` in `<target>/.shipd-config.json` —
creating the file when absent, otherwise preserving its other keys — and SHALL
report the created workspace root. If a workspace root is already discoverable
from the target (nearest-ancestor search, the target itself included), then
initialization SHALL refuse with an error naming the existing root and SHALL
write nothing, unless the nested option is requested. Where the nested option
is requested, initialization SHALL proceed under an enclosing workspace and
SHALL report the enclosing root it nests beneath; it SHALL still refuse when
the target directory itself already declares `workspace`. If the target
directory does not exist, then initialization SHALL error rather than create
it. Where the git option is requested, initialization SHALL additionally run
`git init` at the target when it is not already inside a git work tree, and
SHALL ensure the target's `.gitignore` carries the marked member-repos block,
appending an empty marked block only when the markers are absent — using local
git operations only, never the network.

Where the layered configuration resolved from the target path declares
`workspaces_root` (shipd-config workspaces-root-key), initialization SHALL
additionally enforce the mandated root: when the given path is a bare name (a
single-component relative path that is not `.` or `..`), the engine SHALL
resolve the target to `<workspaces_root>/<name>` — erroring with a message
naming `workspaces_root` when the declared root is not an existing directory,
and creating the leaf directory when absent; when the given path is any other
(explicit) path whose resolved real path lies outside the declared root (the
root itself and its descendants are inside), the engine SHALL refuse with an
error naming the target path, the declared root, and `workspaces_root`, and
SHALL write nothing. The existing guards above SHALL run unchanged against
the resolved target. When `workspaces_root` is undeclared, initialization
SHALL behave exactly as it does without the key.

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

#### Scenario: Nested option creates the nested workspace
- **GIVEN** a directory whose ancestor's config declares `workspace`
- **WHEN** initialization runs against it with the nested option
- **THEN** its `.shipd-config.json` declares `workspace` and the enclosing root
  is reported

#### Scenario: Nested option still refuses a self-declaring target
- **GIVEN** a target whose own config already declares `workspace`
- **WHEN** initialization runs against it with the nested option
- **THEN** it errors and writes nothing

#### Scenario: Git option seeds a repo and the ignore block
- **GIVEN** an existing target directory that is not inside any git work tree
- **WHEN** initialization runs with the git option
- **THEN** the target is a git repository afterwards and its `.gitignore`
  carries the marked member-repos block

#### Scenario: Bare name resolves into the declared root
- **GIVEN** a config layer declaring `workspaces_root` naming an existing
  directory
- **WHEN** initialization runs with the bare name `acme-job`
- **THEN** `<workspaces_root>/acme-job` is created, its `.shipd-config.json`
  declares `workspace`, and that path is reported as the created root

#### Scenario: Explicit target outside the root is refused
- **GIVEN** a config layer declaring `workspaces_root`
- **WHEN** initialization runs against an explicit existing directory outside
  the declared root
- **THEN** it errors naming the target path, the declared root, and
  `workspaces_root`, and writes nothing

#### Scenario: Explicit target inside the root proceeds
- **GIVEN** a config layer declaring `workspaces_root`
- **WHEN** initialization runs against an explicit existing directory beneath
  the declared root
- **THEN** the workspace is created there exactly as without the key

#### Scenario: Bare name with a missing declared root errors
- **GIVEN** a config layer declaring `workspaces_root` naming a directory that
  does not exist
- **WHEN** initialization runs with a bare name
- **THEN** it errors naming `workspaces_root` and the missing root, and
  writes nothing

#### Scenario: Undeclared key changes nothing
- **GIVEN** no layer declares `workspaces_root`
- **WHEN** initialization runs with a bare name resolving to an existing
  directory relative to the working directory
- **THEN** the workspace is created at that relative target exactly as before

### Requirement: Workspace setup skill
id: workspace-setup-skill
base: 01481b95646c

An `/s:workspace` skill SHALL provide, selected by argument: `init` — guided
workspace creation that, when a workspace root is already discoverable,
reports that root and stops; otherwise asks the user in a single question
round to choose the target root (the repository's parent directory offered
as the recommended default, the repository root as the alternative) and
whether to seed the root as a portable git workspace (plain init the
recommended default), then drives the status CLI's `workspace-init` verb —
with `--git` when seeding was chosen — reporting the created root; `show` —
the workspace roster via the status CLI's `workspace-show` verb, reading
only; `clone <url> [dest]` — bootstrap a job workspace from its repository
URL; and `sync` — materialize the workspace's members by executing the
engine's plan. The skill SHALL NOT write the workspace declaration or the
gitignore member block by hand — both go through the CLI verbs. Where the
resolved configuration declares `workspaces_root` (shipd-config
workspaces-root-key), the `init` round SHALL name the declared root and offer
target candidates inside it — substituting `<workspaces_root>/<repo-name>`
for a natural candidate that lies outside the root — and SHALL pass a chosen
bare name through to the verb unchanged, the engine resolving it into the
root.

#### Scenario: Init on an existing workspace reports and stops
- **WHEN** the skill's `init` verb runs where a workspace root is discoverable
- **THEN** the skill reports that root, creates nothing, and stops

#### Scenario: Init creates through the CLI verb
- **WHEN** the user confirms a target root during `init` where no workspace is
  discoverable
- **THEN** the skill runs `workspace-init` against that root and reports the
  root the verb printed

#### Scenario: Init seeds git when the portable option is chosen
- **WHEN** the user chooses git seeding in the `init` round
- **THEN** the skill runs `workspace-init <path> --git` and reports the
  created root

#### Scenario: Show reports the roster
- **WHEN** the skill's `show` verb runs in a discoverable workspace
- **THEN** the workspace root, projects, and initiatives are reported and
  nothing is changed

#### Scenario: Init round names the declared root
- **GIVEN** a resolved configuration declaring `workspaces_root`
- **WHEN** the skill's `init` round is presented
- **THEN** the declared root is named and every offered target candidate lies
  inside it

### Requirement: Workspace clone and sync flows
id: workspace-clone-sync-flows
base: 7ee40470ee69

The `/s:workspace` skill SHALL be the only workspace surface that runs
networked git; the engine verbs it drives stay network-free. When invoked
as `clone <url> [dest]`, the skill SHALL run `git clone` against the URL,
then run the sync flow from inside the created root and report the roster;
if a workspace root resolves from the destination's parent, then the skill
SHALL proceed and report a note naming the enclosing workspace root,
refusing only when the destination's immediate parent directory itself
declares `workspace` in its own `.shipd-config.json`. Where the resolved
configuration declares `workspaces_root` (shipd-config workspaces-root-key),
`clone` without an explicit dest SHALL place the clone at
`<workspaces_root>/<derived-name>` (the directory name git derives from the
URL, under the declared root), and an explicit dest whose resolved path lies
outside the declared root SHALL be refused before cloning with an error
naming the dest, the declared root, and `workspaces_root`; when the key is
undeclared, destination resolution SHALL be unchanged. When invoked as
`sync`, the skill SHALL obtain the plan via the status CLI's `workspace-sync
--json` and execute each member record by its action — running the record's
advisory command for `worktree`, `reference-clone`, and `clone` actions,
and reporting `drift:` notes and `unmaterializable` reasons without
modifying anything — asking no confirmation question. If a member's command
fails, then the skill SHALL report the failure against that member and
continue with the remaining members. After executing, the skill SHALL
recompute the plan with `--write-gitignore` to reconcile the marked member
block and confirm convergence, then report the roster via `workspace-show`.
If no workspace is discoverable when `sync` runs, then the skill SHALL
report the CLI's error verbatim and point at `init` or `clone`.

#### Scenario: Clone bootstraps and hands into sync
- **WHEN** `clone <url>` runs
- **THEN** the repository is cloned with real git, the sync flow runs inside
  the created root, and the roster is reported

#### Scenario: Nested clone destination proceeds with a note
- **GIVEN** a destination whose enclosing workspace root is an ancestor but
  not the immediate parent
- **WHEN** `clone <url> <dest>` runs
- **THEN** the clone proceeds and the report names the enclosing workspace
  root

#### Scenario: Dest-less clone lands under the declared root
- **GIVEN** a resolved configuration declaring `workspaces_root`
- **WHEN** `clone <url>` runs with no dest
- **THEN** the clone is placed at `<workspaces_root>/<derived-name>`

#### Scenario: Explicit dest outside the root is refused
- **GIVEN** a resolved configuration declaring `workspaces_root`
- **WHEN** `clone <url> <dest>` runs with a dest resolving outside the
  declared root
- **THEN** the skill refuses naming the dest, the declared root, and
  `workspaces_root`, and clones nothing

#### Scenario: Sync executes the ladder actions
- **GIVEN** a plan whose records carry `worktree` and `clone` actions with
  advisory commands
- **WHEN** `sync` runs
- **THEN** each record's command is executed as printed and the members are
  git work trees on disk afterwards

#### Scenario: Drift is reported, never repaired
- **GIVEN** a plan record with action `none` carrying a `drift:` note
- **WHEN** `sync` runs
- **THEN** the note is reported and that member is not modified

#### Scenario: A failed member does not abort the run
- **GIVEN** a plan whose first member's advisory command fails
- **WHEN** `sync` runs
- **THEN** the failure is reported against that member and the remaining
  members are still executed

#### Scenario: Sync converges and reconciles the ignore block
- **WHEN** `sync` finishes executing a plan
- **THEN** the plan is recomputed with `--write-gitignore`, the marked
  member block matches the manifest, and the roster is reported
