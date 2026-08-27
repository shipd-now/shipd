# shipd-workspace

### Requirement: Workspace root discovery
id: workspace-root-discovery

The engine SHALL locate the workspace chain by upward search: starting from a
given directory and walking parent-by-parent to the filesystem root, every
directory whose own `.shipd-config.json` declares a `workspace` key SHALL be a
member of the chain, ordered nearest first, the starting directory itself
included. The workspace root SHALL be the chain's first member, so the nearest
declaring ancestor still wins for every root-scoped consumer. If no ancestor
declares one, the chain SHALL be empty and the search SHALL report that no
workspace exists rather than erroring. The search SHALL NOT require the
starting directory or any chain member to be a git repository, and SHALL NOT
consult any `.shipd/` marker.

#### Scenario: Nearest declaring ancestor is the root
- **GIVEN** `.shipd-config.json` files declaring `workspace` at `/ws/` and
  `/ws/nested/`
- **WHEN** discovery starts from `/ws/nested/repo`
- **THEN** the workspace root resolved is `/ws/nested`

#### Scenario: Chain carries every enclosing workspace
- **GIVEN** the same two declaring directories
- **WHEN** the chain is resolved from `/ws/nested/repo`
- **THEN** it is `/ws/nested` then `/ws`, in that order

#### Scenario: Config without a workspace key is not a member
- **GIVEN** `/repo/.shipd-config.json` declaring only `dir` and no ancestor
  declaring `workspace`
- **WHEN** discovery starts from `/repo`
- **THEN** the chain is empty, the search returns no workspace root, and it
  raises no error

### Requirement: Workspace registry loading
id: workspace-registry-loading

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

An initiative brief SHALL live at
`<workspace-root>/<content-dir>/initiatives/<slug>/brief.md`, where
`<content-dir>` is the name resolved from the workspace root's configuration
(default `.shipd`). The brief SHALL begin with a `# <slug>` title matching its
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

When a workspace chain is discoverable from the repository, an `Initiative:`
line on an epic or on a standalone change SHALL resolve to an existing brief at
`<member-root>/<content-dir>/initiatives/<slug>/brief.md` for the nearest chain
member holding one, and a reference resolving in no member SHALL be an error
naming the expected path under the nearest member. When the chain is empty, the
resolution check SHALL be skipped silently, so a bare checkout (CI) never
depends on files outside the repository.

#### Scenario: Missing brief errors when a workspace exists
- **GIVEN** a discoverable workspace whose chain holds no
  `.shipd/initiatives/mvp-readiness/`
- **WHEN** an epic carrying `Initiative: mvp-readiness` is linted
- **THEN** an error names the expected brief path

#### Scenario: Inherited brief resolves clean
- **GIVEN** nested workspaces where only the outer one holds
  `.shipd/initiatives/mvp-readiness/brief.md`
- **WHEN** an epic in a repo under the inner workspace carrying
  `Initiative: mvp-readiness` is linted
- **THEN** no initiative-reference error is emitted

#### Scenario: No workspace skips silently
- **WHEN** an epic carrying `Initiative: mvp-readiness` is linted in a
  checkout with no discoverable workspace
- **THEN** no initiative-reference error or warning is emitted

### Requirement: Project registry semantics
id: project-registry-semantics

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

The system SHALL reserve
`<workspace-root>/<content-dir>/projects/<slug>/context.md` as optional
free-prose steering context for a project. Tooling SHALL NOT lint or require
the file; status verbs SHALL surface whether it exists.

#### Scenario: Missing context is never an error
- **WHEN** a declared project has no `.shipd/projects/<slug>/context.md`
- **THEN** no lint or status command reports an error for its absence

### Requirement: Workspace initialization
id: workspace-initialization

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

### Requirement: Workspace setup skill
id: workspace-setup-skill

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
gitignore member block by hand — both go through the CLI verbs.

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

### Requirement: Sync materialization planning
id: sync-materialization-planning

The engine SHALL compute a deterministic per-member materialization plan
from the workspace manifest, the resolved configuration, and local disk
state, using only local git probes and never the network. For a member
whose destination exists as a git work tree the plan SHALL record action
`none`, adding a drift note when the destination's origin URL differs from
the manifest `url`; an existing non-git destination SHALL be recorded as
occupied with a drift note and never modified. For an absent member the
plan SHALL choose the cheapest rung: a work-tree candidate clone (an
immediate child of a `clone_sources` directory whose origin URL equals the
manifest `url`, first match in list order) yields action `worktree`; a bare
candidate yields action `reference-clone`; no candidate with a `url` yields
action `clone`; no `url` yields action `unmaterializable` with a reason.
Actions carrying a rung SHALL include an advisory command string; the
planner SHALL never execute one. The plan SHALL also compare the marked
member-repos gitignore block against the manifest's member paths and record
the missing or stale lines.

#### Scenario: Absent member with a local work-tree candidate
- **GIVEN** a manifest entry with a `url` and a `clone_sources` directory
  containing a clone whose origin equals that url
- **WHEN** the plan is computed
- **THEN** the member's action is `worktree` naming that candidate as the
  source with an advisory `git worktree add` command

#### Scenario: Absent member with no candidate falls to clone
- **GIVEN** a manifest entry with a `url` and no matching local candidate
- **WHEN** the plan is computed
- **THEN** the member's action is `clone` carrying the manifest url

#### Scenario: Present member with a mismatched origin drifts
- **GIVEN** a member present on disk whose origin URL differs from the
  manifest `url`
- **WHEN** the plan is computed
- **THEN** the action is `none` and the record carries a drift note naming
  both URLs, and nothing on disk is modified

#### Scenario: Absent member without a url is unmaterializable
- **GIVEN** a path-only manifest entry that is absent on disk
- **WHEN** the plan is computed
- **THEN** the member's action is `unmaterializable` with a reason naming
  the missing url

#### Scenario: Gitignore block gaps are reported
- **GIVEN** a workspace whose marked member block lacks a manifest member
  path
- **WHEN** the plan is computed
- **THEN** the gitignore record lists that path as missing

### Requirement: Workspace clone and sync flows
id: workspace-clone-sync-flows

The `/s:workspace` skill SHALL be the only workspace surface that runs
networked git; the engine verbs it drives stay network-free. When invoked
as `clone <url> [dest]`, the skill SHALL run `git clone` against the URL,
then run the sync flow from inside the created root and report the roster;
if a workspace root resolves from the destination's parent, then the skill
SHALL proceed and report a note naming the enclosing workspace root,
refusing only when the destination's immediate parent directory itself
declares `workspace` in its own `.shipd-config.json`. When invoked as `sync`,
the skill SHALL obtain the plan via the status CLI's `workspace-sync
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

### Requirement: Chain facility resolution
id: workspace-chain-facilities

The engine SHALL resolve each workspace facility against the workspace chain
rather than the nearest root alone. Wiki stores and initiative briefs SHALL
resolve across the chain: a wiki page slug and an initiative brief SHALL
resolve to the nearest chain member holding it, and where no member holds it
the resolution SHALL yield nothing rather than erroring. The project registry
SHALL resolve to the nearest chain member whose `workspace` object declares a
`projects` key, falling back to the nearest chain member when none declares
one; a registry SHALL always resolve whole, and registries SHALL NEVER be
merged across chain members. A registry's `focus` SHALL travel with the
registry that declared it. Member materialization planning and every write —
wiki store scaffolding, wiki emission, queue append and answer, and initiative
emission — SHALL target the nearest workspace root only, never an inherited
one. Where the chain is empty, every chain-resolved read SHALL yield nothing
without erroring.

#### Scenario: Inherited wiki page resolves
- **GIVEN** nested workspaces `/ws/outer` and `/ws/outer/inner` where only
  `/ws/outer` holds a wiki page `conventions`
- **WHEN** the page is resolved from `/ws/outer/inner/repo`
- **THEN** it resolves to `/ws/outer`'s store

#### Scenario: Nearer page shadows the inherited one
- **GIVEN** both `/ws/outer` and `/ws/outer/inner` holding a page `conventions`
- **WHEN** the page is resolved from `/ws/outer/inner/repo`
- **THEN** it resolves to `/ws/outer/inner`'s store

#### Scenario: Registry falls through to the declaring member
- **GIVEN** `/ws/outer` declaring `projects` and `/ws/outer/inner` declaring
  `workspace` with no `projects` key
- **WHEN** the registry is resolved from `/ws/outer/inner/repo`
- **THEN** the resolved registry is `/ws/outer`'s, entire

#### Scenario: A declared registry wins outright
- **GIVEN** both members declaring `projects`
- **WHEN** the registry is resolved from `/ws/outer/inner/repo`
- **THEN** only `/ws/outer/inner`'s registry is effective and no project from
  `/ws/outer` appears

#### Scenario: Writes stay in the nearest workspace
- **GIVEN** nested workspaces where only the outer one holds a wiki store
- **WHEN** a queue block is appended from `/ws/outer/inner/repo`
- **THEN** it lands in `/ws/outer/inner`'s store and `/ws/outer`'s `queue.md`
  is unchanged

#### Scenario: Empty chain yields nothing
- **WHEN** a chain-resolved read runs where no ancestor declares a workspace
- **THEN** it yields nothing and raises no error
