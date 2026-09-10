## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Project resolution by containment
id: project-resolution
base: 5daed34bb3cd

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

### Requirement: Sync materialization planning
id: sync-materialization-planning
base: 7e591fb82a74

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
