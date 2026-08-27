## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Workspace root discovery
id: workspace-root-discovery
base: ea412e596357

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

### Requirement: CI-safe initiative reference resolution
id: initiative-reference-resolution
base: b73e22fae690

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

### Requirement: Workspace initialization
id: workspace-initialization
base: a8e378826c03

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
