# shipd-workspace

### Requirement: Workspace root discovery
id: workspace-root-discovery

The engine SHALL locate the workspace chain by upward search: starting from a
given directory and walking parent-by-parent to the filesystem root, every
directory whose own `.shipd-config.json` declares a `workspace` key SHALL be a
member of the chain, ordered nearest first, the starting directory itself
included. The workspace root SHALL be the chain's first member, so the nearest
declaring ancestor still wins for every root-scoped consumer. If no ancestor
declares one, the engine SHALL attempt the reverse-lookup fallback rungs
(workspace-reverse-lookup); where those also resolve nothing, the chain SHALL
be empty and the search SHALL report that no workspace exists rather than
erroring. A chain resolved through a fallback rung SHALL be the full upward
chain computed from the resolved root, so enclosing workspaces above it are
still members. The search SHALL NOT require the starting directory or any
chain member to be a git repository, and SHALL NOT consult any `.shipd/`
marker; only the fallback rungs MAY probe git, locally.

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
  declaring `workspace`, with no fallback rung resolving
- **WHEN** discovery starts from `/repo`
- **THEN** the chain is empty, the search returns no workspace root, and it
  raises no error

#### Scenario: Fallback-resolved chain carries enclosing workspaces

- **GIVEN** a checkout whose origin URL uniquely matches a workspace that
  itself sits under an enclosing declaring directory
- **WHEN** the chain is resolved from the checkout
- **THEN** it lists the matched workspace first, then its enclosing
  workspace

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

### Requirement: Project resolution by containment
id: project-resolution

The engine SHALL resolve which project owns a path via
`project_of(workspace_root, path)`: the project whose repo entry equals or
contains the path, the longest (most specific) matching entry winning across
projects. Where the workspace member map holds an entry for a repo's
manifest path, the engine SHALL additionally match the path against the
mapped destination's real path with the same equality-or-containment rule
and the same specificity scoring. A path matching no entry SHALL resolve to
`None`, denoting the implicit default project, which is anonymous and SHALL
NOT be referenceable by any slug.

#### Scenario: Most specific entry wins

- **GIVEN** project `alpha` lists `apps` and project `beta` lists
  `apps/backend`
- **WHEN** `project_of` resolves `apps/backend/repo-x`
- **THEN** the result is `beta`

#### Scenario: Unmatched path is the implicit default

- **WHEN** `project_of` resolves a path listed by no project
- **THEN** the result is `None` and no slug denotes that implicit project

#### Scenario: Mapped checkout resolves to its project

- **GIVEN** project `alpha` lists member path `shipd` and the map points
  `shipd` at a checkout outside the workspace root
- **WHEN** `project_of` resolves a file inside that mapped checkout
- **THEN** the result is `alpha`

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
URL; `sync` — materialize the workspace's members by executing the
engine's plan; and `map` — a guided mapping round that reads the sync
plan, proposes for each unmapped member an existing local checkout
candidate (the plan's matching clone-source when one exists) or a
user-supplied path, asks in a single round, drives the status CLI's
`workspace-map set` verb per accepted member, and finishes by reporting
the map listing; already-mapped members SHALL be reported, never re-asked,
and `sync` and `clone` SHALL remain question-free. The skill SHALL NOT
write the workspace declaration, the gitignore member block, or the member
map file by hand — all go through the CLI verbs. Where the resolved
configuration declares `workspaces_root` (shipd-config
workspaces-root-key), the `init` round SHALL name the declared root and offer
target candidates inside it — substituting `<workspaces_root>/<repo-name>`
for a natural candidate that lies outside the root — and SHALL pass a chosen
bare name through to the verb unchanged, the engine resolving it into the
root.

#### Scenario: Init on an existing workspace reports and stops

- **WHEN** the skill's `init` verb runs where a workspace root is
  discoverable
- **THEN** the skill reports that root, creates nothing, and stops

#### Scenario: Init creates through the CLI verb

- **WHEN** the user confirms a target root during `init` where no workspace
  is discoverable
- **THEN** the skill runs `workspace-init` against that root and reports
  the root the verb printed

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
- **THEN** the declared root is named and every offered target candidate
  lies inside it

#### Scenario: Map verb drives the engine writer

- **GIVEN** a workspace with an unmapped member whose checkout exists
  locally
- **WHEN** `/s:workspace map` runs and the user accepts the candidate
- **THEN** the skill runs `workspace-map set` for that member and reports
  the resulting map listing, having edited no file by hand

### Requirement: Workspace focus declaration
id: workspace-focus

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
planner SHALL never execute one. Where the workspace member map holds an
entry for a member, its destination SHALL be the mapped path, the record
SHALL carry the resolved mapped destination, and the action SHALL always be
`none` — the materialization ladder SHALL NOT run and no advisory command
SHALL ever target a mapped path; an absent mapped destination SHALL be
recorded state `absent` with a drift note naming the mapped path. The plan
SHALL also compare the marked member-repos gitignore block against the
manifest's member paths and record the missing or stale lines.

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

#### Scenario: Mapped member plans none with the mapped destination

- **GIVEN** a member whose manifest path the map points at an existing git
  checkout outside the workspace root
- **WHEN** the plan is computed
- **THEN** the record's action is `none`, it carries the resolved mapped
  destination, and no command is emitted

#### Scenario: Missing mapped destination drifts instead of materializing

- **GIVEN** a member whose manifest path the map points at a non-existent
  path
- **WHEN** the plan is computed
- **THEN** the record's state is `absent`, its action is `none` with no
  command, and a drift note names the mapped path

### Requirement: Workspace clone and sync flows
id: workspace-clone-sync-flows

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

### Requirement: Workspace universe discovery seam
id: workspace-universe-discovery

The engine SHALL provide a single shared workspace-universe discovery seam in
the stdlib configuration module (`spec_common`): `workspace_project_roots(root)`
returning `(project_slug, repo_root)` pairs for the declared workspace project
repos, and `aggregation_universes(root)` returning `[(None, root)]` followed by
those pairs. The pairs SHALL be non-empty exactly when a project registry is
discoverable from `root` (`registry_root`) AND `root` lies inside no declared
project repo (`project_of` yields the implicit default) — projects in slug
order, each project's repos in declaration order, every path resolved against
the registry root. The seam SHALL be fail-soft: an unloadable registry, a
non-object project or repo entry, a path that is not a directory on this
machine, an entry duplicating an earlier entry's real path, and an entry
resolving to the invocation root's own real path SHALL each be skipped
silently, never raised. Every read surface that aggregates or resolves across
declared workspace projects SHALL obtain its universes through this seam,
never through a private reimplementation.

#### Scenario: Workspace-level invocation yields the declared repos
- **GIVEN** a workspace root declaring two projects whose repo directories
  exist on disk
- **WHEN** `workspace_project_roots` runs with that root
- **THEN** both repos are returned in project slug order and
  `aggregation_universes` lists `(None, root)` first, then those pairs

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

### Requirement: Workspaces guide
id: workspaces-doc

The repository SHALL provide the workspaces guide as an index page plus five
part pages. `docs/workspaces.md` SHALL be the index: titled "Workspaces",
explaining the workspace concept with the layout diagram (labeling which
folder is the workspace repo), and introducing each part with one descriptive
sentence, a basic usage example, and a relative link to the part page. The
part pages SHALL live under `docs/workspaces/` as `getting-started.md` (setup
through day-to-day use, including the `workspaces_root` coverage),
`nesting-and-stores.md` (nested job workspaces and `store_root`), `teams.md`
(team-shared workspaces), `headless.md` (headless consumers), and
`multi-workspace-repos.md` (the practical examples), each opening with a link
back to the index. The guide SHALL use the term "workspace" — never "portable
workspace" — throughout, its examples SHALL follow the single
`~/workspaces/` one-folder-per-job directory convention, and every
interactive setup command SHALL invoke the `shipd` binary, never a
`spec_status.py` path, except in `headless.md` and in the index's
basic-usage example for the headless part, whose contract is precisely the
binary-free read. No page SHALL carry a link or
anchor that fails to resolve after the split. The getting-started page SHALL
document the optional `workspaces_root` config key (shipd-config
workspaces-root-key) as the way to mandate the directory convention — bare
init names resolving to `<workspaces_root>/<name>` with the leaf created,
out-of-root init targets and clone destinations refused naming the target,
the declared root, and the key, `--nested` job workspaces inside the root
staying legal, no behavior change when undeclared — and SHALL state that
`shipd config` reports the raw declared value with `~` unexpanded, that the
installed sample config documents the key, and that the doctor `config` check
fails on a malformed value and warns when the declared root directory is
missing. The teams page SHALL document team-shared workspace repos: any
number of engineers cloning the same workspace repo, per-machine member
materialization through the sync ladder, and the shared knowledge (wiki,
queue, initiatives) traveling through ordinary git pull and push. It SHALL
state the concurrency expectations — the engine takes no locks and never
pushes, pulls, or fetches; wiki writes auto-commit locally, scoped to the
touched files; concurrent `queue.md` appends and `index.md` catalog rewrites
merge as ordinary git conflicts while distinct per-page files merge cleanly;
duplicate `q-<slug>` blocks after a merge leave the queue invalid until
de-duplicated; two clones answering one question conflict on that block's
`Answer:` line, resolved by keeping exactly one answer — and SHALL warn that
`post-worktree-scripts` resolve nearest-wins from enclosing configs, with the
first-run consent gate and the `hooks trust` verb as the receiving machine's
control. The headless page SHALL document what a headless consumer needs to
read a workspace: a bare `git clone`, Python 3, and the plugin's
`spec_status.py`, with reads succeeding while every member repo is absent,
without a git binary or identity, and with no `~/.shipd-config.json` on the
machine.

#### Scenario: Index introduces every part
- **WHEN** `docs/workspaces.md` is inspected
- **THEN** it is titled "Workspaces", explains the concept with the labeled
  layout diagram, and carries one entry per part page — a descriptive
  sentence, a basic usage example, and a relative link — for all five parts

#### Scenario: Parts carry the relocated content
- **WHEN** the pages under `docs/workspaces/` are inspected
- **THEN** `getting-started.md` covers setup through day-to-day use including
  `workspaces_root`, `nesting-and-stores.md` covers nesting and `store_root`,
  `teams.md` covers sharing, concurrency, and the worktree-hooks consent
  gate, `headless.md` covers the headless read contract, and
  `multi-workspace-repos.md` covers the practical examples

#### Scenario: No dangling links after the split
- **WHEN** every `](#...)` anchor and relative link in the index and part
  pages is checked
- **THEN** each anchor resolves to a heading in its own file and each
  relative link resolves to an existing file

#### Scenario: Guide documents the workspaces_root mandate
- **WHEN** the getting-started page is inspected
- **THEN** it documents declaring `workspaces_root` in `~/.shipd-config.json`
  as mandating the parent-directory convention — bare init names resolving
  into the declared root with the leaf created, out-of-root targets refused
  naming the target, the root, and the key, `--nested` inside the root
  staying legal, undeclared meaning no change — and names the `shipd config`
  raw-value reporting, the sample-config entry, and the doctor `config`
  check's fail/warn behavior

#### Scenario: Guide covers team-shared workspaces
- **WHEN** `docs/workspaces/teams.md` is inspected
- **THEN** it documents several engineers cloning one workspace repo,
  per-machine member materialization, git pull/push as the knowledge
  transport, the no-locks/no-networked-git concurrency expectations with
  `queue.md` and `index.md` as conflict surfaces, duplicate `q-<slug>`
  invalidity, single-answer conflict resolution, and the inherited
  worktree-hooks warning with the consent gate and `hooks trust`

#### Scenario: Guide covers headless consumers
- **WHEN** `docs/workspaces/headless.md` is inspected
- **THEN** it names the minimal footprint — a workspace clone, Python 3, and
  `spec_status.py` — and states that reads succeed with all members absent,
  without git, and without any machine-level configuration

#### Scenario: Interactive commands use the shipd binary
- **WHEN** the index and the part pages other than `headless.md` are
  inspected
- **THEN** every setup and day-to-day command invokes the `shipd` binary and
  no interactive example invokes `spec_status.py` by path — save the index's
  headless-part usage example — while `headless.md` still names
  `spec_status.py` as its footprint

#### Scenario: Examples share one directory convention
- **WHEN** the guide's layout and command examples are inspected across all
  six files
- **THEN** every standalone workspace example lives under `~/workspaces/`,
  the index's layout diagram labels the workspace repo, and no example uses
  the retired `~/jobs/` convention or the term "portable workspace"

### Requirement: Workspaces guide practical examples
id: workspaces-doc-examples

The workspaces guide SHALL provide a practical-examples part page,
`docs/workspaces/multi-workspace-repos.md`, on multi-workspace repos that
documents both supported shapes: sibling workspaces inside a plain repo whose
root declares no workspace, and a base workspace root holding `--nested` job
workspaces. For each shape the page SHALL show a layout diagram
distinguishing tracked from machine-local content, SHALL tabulate where the
manifest, wiki, oracle queue, initiatives, and member repos live, and SHALL
give the setup and day-to-day commands through the `shipd` binary. The page
SHALL compare the shapes' pros and cons, SHALL state that multi-workspace
repos are cloned with plain `git clone` rather than the workspace clone verb,
and SHALL warn that git provides no per-directory access control, so separate
repos remain the isolation boundary.

#### Scenario: Both shapes are walked with storage tables
- **WHEN** `docs/workspaces/multi-workspace-repos.md` is inspected
- **THEN** it documents the sibling-workspaces shape and the nested-jobs
  shape, each with a layout diagram and a table naming where the manifest,
  wiki, queue, initiatives, and member repos live

#### Scenario: Commands honor the guide's conventions
- **WHEN** the practical-examples page's commands are inspected
- **THEN** every interactive command invokes the `shipd` binary and no
  `spec_status.py` path appears on the page

#### Scenario: Trade-offs and boundaries are stated
- **WHEN** the practical-examples page is inspected
- **THEN** it compares the two shapes' pros and cons, directs
  multi-workspace repos to plain `git clone`, and warns that separate repos —
  not directories — are the access-control boundary

### Requirement: Workspace member map
id: workspace-member-map

The engine SHALL read an optional machine-local map file at
`<workspace-root>/.shipd-workspace.local.json` whose `repos` value is a JSON
object mapping manifest member paths to local checkout paths; a value MAY
carry a leading `~` (expanded on read) or be relative (resolved against the
workspace root). Member destination resolution SHALL route through a single
seam that returns the mapped destination when the member's manifest path has
an entry and `<workspace-root>/<path>` otherwise. If the file is absent, then
the map SHALL be empty and behavior SHALL be unchanged. If the file is
malformed — invalid JSON, a non-object top level or `repos` value, or a
non-string or empty mapping value — then the engine SHALL raise a clear
error naming the file. The workspace report SHALL annotate each mapped
member with its resolved destination, and SHALL surface map keys matching no
manifest member path as a note, never as an error.

#### Scenario: Mapped member resolves to its local checkout

- **GIVEN** a registry member with path `shipd` and a map file whose `repos`
  maps `shipd` to an existing git checkout outside the workspace root
- **WHEN** the workspace report runs
- **THEN** the member reports present with a mapped annotation naming the
  resolved destination

#### Scenario: Absent map file changes nothing

- **WHEN** the workspace report runs with no
  `.shipd-workspace.local.json` at the root
- **THEN** every member resolves to `<workspace-root>/<path>` exactly as
  before

#### Scenario: Malformed map errors naming the file

- **WHEN** `.shipd-workspace.local.json` holds `{"repos": []}`
- **THEN** the consuming verb fails with an error naming
  `.shipd-workspace.local.json`

#### Scenario: Unknown map key is a note

- **GIVEN** a map whose `repos` carries a key matching no manifest member
  path
- **WHEN** the workspace report runs
- **THEN** the report carries a note naming the unmatched key and exits
  zero

### Requirement: Workspace reverse lookup
id: workspace-reverse-lookup

When the upward search yields an empty chain, the engine SHALL attempt two
fallback rungs in order, using local probes only and never the network.
First, where the starting repo's root carries a `.shipd-workspace.local.json`
declaring `workspace_root`, the engine SHALL resolve the chain from that
pointed directory when it declares `workspace` in its own
`.shipd-config.json`, and otherwise SHALL resolve nothing and warn once on
stderr naming the pointer file and the target. Second, where the layered
configuration declares `workspaces_root` naming an existing directory and
the starting directory lies in a git work tree with a readable `origin` URL,
the engine SHALL match that URL — normalized with scheme, user prefix, and
one trailing `.git` stripped, `host:path` read as `host/path`, trailing
slashes dropped, case-folded — against the declared member `url`s of each
immediate child of `workspaces_root` whose config declares `workspace`:
exactly one matching child SHALL resolve the chain from that child; two or
more SHALL resolve nothing and warn once on stderr naming every matching
root and the pointer remedy. If neither rung resolves — no pointer, no
`workspaces_root`, no readable origin, or no match — then the chain SHALL
stay empty with no warning, exactly as before.

#### Scenario: Origin URL resolves the owning workspace

- **GIVEN** a checkout outside any workspace whose origin URL matches one
  member `url` (differing only by scheme and a `.git` suffix) declared by
  exactly one workspace under the declared `workspaces_root`
- **WHEN** workspace discovery runs from inside the checkout
- **THEN** the resolved workspace root is that workspace

#### Scenario: Pointer beats the scan

- **GIVEN** a checkout whose repo root's `.shipd-workspace.local.json`
  declares `workspace_root` naming workspace A, while the URL scan would
  match workspace B
- **WHEN** discovery runs from the checkout
- **THEN** the resolved root is A

#### Scenario: Ambiguous match resolves nothing and names the remedy

- **GIVEN** two workspaces under `workspaces_root` each declaring a member
  `url` matching the checkout's origin
- **WHEN** discovery runs from the checkout
- **THEN** no workspace resolves and one stderr warning names both roots
  and the `workspace_root` pointer remedy

#### Scenario: Bare checkout stays silent and unresolved

- **GIVEN** a checkout with no pointer file, in an environment declaring no
  `workspaces_root`
- **WHEN** discovery runs from the checkout
- **THEN** the chain is empty with no warning, exactly as before

### Requirement: Workspace map verbs
id: workspace-map-verbs

The status CLI SHALL provide a `workspace-map` verb resolving the workspace
from the invocation directory (failing with the standard no-workspace error
otherwise). The bare form SHALL list each map entry with its stored value
and resolved absolute destination, plus the unknown-key note. The `set`
form SHALL take a member path and a local path, SHALL error naming the
declared member paths when the member path matches no manifest entry, SHALL
store the local path verbatim, SHALL preserve every other top-level key and
value of the map file unchanged in content (a `workspace_root` key
included; the file is re-serialized as pretty-printed JSON), and SHALL
ensure the workspace root's `.gitignore` carries a
`.shipd-workspace.local.json` line outside the marked member block —
idempotently, creating the file when absent. If the target path does not
exist or is not a git work tree, then `set` SHALL warn and still write. The
`remove` form SHALL delete the member's entry, erroring when no entry
exists. A malformed existing map file SHALL fail `set` and `remove` with
the load's own error, never repaired.

#### Scenario: Set writes a validated entry and ignores the file

- **GIVEN** a workspace declaring member path `shipd` and no map file
- **WHEN** `workspace-map set shipd ~/projects/shipd` runs from the root
- **THEN** the map file's `repos` maps `shipd` to `~/projects/shipd`
  verbatim and the root `.gitignore` contains a
  `.shipd-workspace.local.json` line outside the marked member block

#### Scenario: Set refuses an undeclared member path

- **GIVEN** a workspace declaring only member path `shipd`
- **WHEN** `workspace-map set web ../web` runs
- **THEN** the verb exits non-zero naming the declared member paths and
  writes nothing

#### Scenario: Set preserves foreign keys

- **GIVEN** a map file carrying a `workspace_root` key beside `repos`
- **WHEN** `set` adds an entry
- **THEN** the `workspace_root` key survives unchanged

#### Scenario: Missing target warns but writes

- **WHEN** `set` maps a member to a path that does not exist
- **THEN** the entry is written and a warning names the missing target

#### Scenario: Remove deletes exactly one entry

- **GIVEN** a map holding entries for `shipd` and `web`
- **WHEN** `workspace-map remove shipd` runs
- **THEN** only the `web` entry remains, and a second identical remove
  exits non-zero
