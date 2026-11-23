## MODIFIED Requirements

### Requirement: Workspaces guide
id: workspaces-doc
base: f3dbc7f271b3
Dropped: The nesting and stores part carries its content

The repository SHALL provide the workspaces guide as an index page plus six
part pages, each conforming to the shipd documentation standard: a doc-type
marker comment on the first line, and a total line count within that type's
cap. `docs/workspaces.md` SHALL be the concept index and the main page for
the `/s:workspace` skill and the `shipd workspace` verb: titled "Workspaces",
explaining the workspace concept with the layout diagram (labeling which
folder is the workspace repo). Its `## Reference` section SHALL introduce
each part with one descriptive sentence, a usage example, and a relative
link, and SHALL hold a table of the six `/s:workspace` arguments (`init`,
`show`, `clone`, `sync`, `map`, `team`) and the four `shipd workspace` forms
(bare, `init`, `sync`, `team`). The part pages SHALL live under
`docs/workspaces/`, each opening with a link back to the index:
`getting-started.md` (how-to: setup through day-to-day use, including the
`workspaces_root` coverage), `member-map.md` (reference: the member map and
workspace discovery from outside the workspace), `nesting.md` (how-to: nested
job workspaces), `external-stores.md` (reference: `store_root`), `teams.md`
(reference: team-shared workspaces, the nested team layout, and the
enterprise guidance), and `headless.md` (how-to: headless consumers). The
files `docs/workspaces/nesting-and-stores.md` and
`docs/workspaces/multi-workspace-repos.md` SHALL NOT exist.

Each of the seven pages SHALL follow the main-page shape: opening paragraphs
saying what the page covers, then `## When to use it`, `## How to run it`,
and a closing `## Reference` as its only level-2 headings, in that order. No
page SHALL carry a mermaid fence. One page SHALL own each fact, and another
page SHALL give that fact in one sentence at most with a link to the owner.

The nesting page SHALL document nested job workspaces: the
`shipd workspace init <path> --nested --git` command, that `--nested` is
mandatory, what inherits across the chain (wiki reads, initiative briefs, the
project registry), what stays nearest-only (every write, sync and member
materialization), and `wiki_base` alongside nesting. The external stores page
SHALL document `store_root`: declaring it once at the workspace root, where
the store lands, a dedicated artifacts repo, per-repo folder naming, how
store writes are committed, checking what resolved with `shipd config` and
`shipd doctor`, the `After` dependency rule, and the known limitations.

The guide SHALL present exactly two workspace setup paths and no third: a
standalone workspace, and a base workspace holding `--nested` team
workspaces. No page SHALL present the sibling-workspaces shape — several
workspace directories inside a plain container repo whose root declares no
workspace — as a supported layout, whether for team use or any other.

The guide SHALL use the term "workspace" — never "portable workspace" —
throughout, its examples SHALL follow the single `~/workspaces/`
one-folder-per-job directory convention, and every interactive setup command
SHALL invoke the `shipd` binary, never a `spec_status.py` path, except in
`headless.md`, in the index's usage example for the headless part (whose
contract is precisely the binary-free read), and in `member-map.md`'s
`workspace-map` and `workspace-sources` examples, whose verbs the
deliberately read-only binary does not expose. No page SHALL carry a link or
anchor that fails to resolve.

The getting-started page SHALL document the optional `workspaces_root` config
key (shipd-config workspaces-root-key) as the way to mandate the directory
convention — bare init names resolving to `<workspaces_root>/<name>` with the
leaf created, out-of-root init targets and clone destinations refused naming
the target, the declared root, and the key, `--nested` job workspaces inside
the root staying legal, no behavior change when undeclared — and SHALL state
that `shipd config` reports the raw declared value with `~` unexpanded, that
the installed sample config documents the key, and that the doctor `config`
check fails on a malformed value and warns when the declared root directory
is missing. The getting-started page SHALL also document the sync consent
round: no member materializes without the single up-front consent question,
which offers reusing existing checkouts where the candidate scan found them.

The member-map page SHALL document the machine-local
`.shipd-workspace.local.json` file and its three fields — the `repos`
member map at a workspace root, the `workspace_root` pointer in a member
checkout, and the optional `clone_sources` directory list the candidate scan
unions with the configuration key — the `workspace-map` list/set/remove
verbs and the `workspace-sources` list/add/remove verbs with
`/s:workspace map` as the guided front door, the mapped member's semantics
(the planner's action always `none`, origin drift and missing targets
reported as drift notes, stale keys as notes, a malformed file failing the
reading verb), and the three-rung discovery ladder — ancestor search, then
the pointer, then the origin-URL scan — including URL normalization, the
SSH-alias caveat, and the multi-match ambiguity warning naming the pointer
as the remedy.

The teams page SHALL document team-shared workspace repos: any number of
engineers cloning the same workspace repo, per-machine member materialization
through the sync ladder, and the shared knowledge (wiki, queue, initiatives)
traveling through ordinary git pull and push. It SHALL state the concurrency
expectations — the git automation and locking exactly as this capability's
`workspaces-doc-store-sync` requirement specifies, which owns that story and
forbids the no-locks claim this requirement used to make; wiki writes
auto-commit locally, scoped to the touched files; concurrent
`queue.md` appends and `index.md` catalog rewrites merge as ordinary git
conflicts while distinct per-page files merge cleanly; duplicate `q-<slug>`
blocks after a merge leave the queue invalid until de-duplicated; two clones
answering one question conflict on that block's `Answer:` line, resolved by
keeping exactly one answer — and SHALL warn that `post-worktree-scripts`
resolve nearest-wins from enclosing configs, with the first-run consent gate
and the `hooks trust` verb as the receiving machine's control. The teams page
SHALL also carry the enterprise guidance: the primary layout is one dedicated
workspaces repository whose root is itself a workspace, holding one
`--nested` team workspace per team or group, materialized partially per
engineer and mapped with the member map where checkouts already exist. It
SHALL state that reads fall through to the base workspace while every write
lands in the team's own store, SHALL name `shipd workspace team` as the way
to build the layout, and SHALL direct a group whose knowledge must stay
isolated to a workspace repository of its own, because separate repos remain
the isolation boundary.

The headless page SHALL document what a headless consumer needs to read a
workspace: a bare `git clone`, Python 3, and the plugin's `spec_status.py`,
with reads succeeding while every member repo is absent, without a git binary
or identity, and with no `~/.shipd-config.json` on the machine.

#### Scenario: Index introduces every part
- **WHEN** `docs/workspaces.md` is inspected
- **THEN** it is titled "Workspaces", explains the concept with the labeled
  layout diagram, and its `## Reference` section carries one entry per part
  page — a descriptive sentence, a usage example, and a relative link — for
  all six parts

#### Scenario: Every guide page carries its marker and fits its cap
- **WHEN** `docs_lint.py` runs over the index and the six part pages
- **THEN** it exits 0, with the index marked `concept`; `member-map.md`,
  `external-stores.md`, and `teams.md` marked `reference`; and
  `getting-started.md`, `nesting.md`, and `headless.md` marked `how-to`

#### Scenario: Member-map page carries the relocated content
- **WHEN** `docs/workspaces/member-map.md` is inspected
- **THEN** it documents the three `.shipd-workspace.local.json` fields, the
  `workspace-map` and `workspace-sources` verbs behind the `/s:workspace map`
  front door, the mapped member's `none`-action and drift semantics, and the
  three-rung discovery ladder with URL normalization, the SSH-alias caveat,
  and the ambiguity warning — and `docs/workspaces.md` no longer carries
  those sections

#### Scenario: Getting-started documents the consent round
- **WHEN** `docs/workspaces/getting-started.md` is inspected
- **THEN** it states that sync materializes nothing without the single
  up-front consent question and that reusing existing checkouts is offered
  where candidates were found

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
  transport, the concurrency expectations `workspaces-doc-store-sync`
  defines, with `queue.md` and `index.md` as conflict surfaces, duplicate `q-<slug>`
  invalidity, single-answer conflict resolution, and the inherited
  worktree-hooks warning with the consent gate and `hooks trust`

#### Scenario: Enterprise guidance presents the nested team layout
- **WHEN** the teams page's enterprise guidance is inspected
- **THEN** the primary layout is one workspaces repository whose root is
  itself a workspace holding one `--nested` team workspace per team or group,
  with the read-through and write-nearest split stated, `shipd workspace team`
  named as the way to build it, partial materialization and the member map
  named, and a per-group repository named as the remedy when a group's
  knowledge must stay isolated

#### Scenario: The guide presents only two setup paths
- **WHEN** every guide page is inspected
- **THEN** the only layouts presented are the standalone workspace and the
  base workspace holding `--nested` team workspaces, and no page presents
  workspace directories inside a plain container repo as a supported shape

#### Scenario: Guide covers headless consumers
- **WHEN** `docs/workspaces/headless.md` is inspected
- **THEN** it names the minimal footprint — a workspace clone, Python 3, and
  `spec_status.py` — and states that reads succeed with all members absent,
  without git, and without any machine-level configuration

#### Scenario: Interactive commands use the shipd binary
- **WHEN** the index and the part pages are inspected
- **THEN** every setup and day-to-day command invokes the `shipd` binary and
  no interactive example invokes `spec_status.py` by path — save
  `headless.md`, the index's headless-part usage example, and
  `member-map.md`'s `workspace-map` and `workspace-sources` examples

#### Scenario: No dangling links
- **WHEN** every `](#...)` anchor and relative link in the index and part
  pages is checked
- **THEN** each anchor resolves to a heading in its own file and each
  relative link resolves to an existing file

#### Scenario: Examples share one directory convention
- **WHEN** the guide's layout and command examples are inspected across all
  seven files
- **THEN** every standalone workspace example lives under `~/workspaces/`,
  the index's layout diagram labels the workspace repo, and no example uses
  the retired `~/jobs/` convention or the term "portable workspace"

#### Scenario: The nesting page carries its content
- **WHEN** `docs/workspaces/nesting.md` is inspected
- **THEN** it documents nested job workspaces with the `--nested` command,
  what inherits across the chain, what stays nearest-only, and `wiki_base`
  alongside nesting, and it names no `store_root` behaviour

#### Scenario: The external stores page carries its content
- **WHEN** `docs/workspaces/external-stores.md` is inspected
- **THEN** it documents external artifact stores including where the store
  lands, per-repo folder naming, how its writes are committed, the `After`
  dependency rule, and the known limitations

#### Scenario: Every page follows the main-page shape
- **WHEN** the level-2 headings of the index and of each part page are listed
- **THEN** each page's are `## When to use it`, `## How to run it`, and
  `## Reference`, in that order, and no page holds a mermaid fence

#### Scenario: The index is the main page for the workspace verbs
- **WHEN** the `## Reference` section of `docs/workspaces.md` is read
- **THEN** it names the six `/s:workspace` arguments and the four
  `shipd workspace` forms, each with what it does

#### Scenario: The retired pages are gone
- **WHEN** the files under `docs/workspaces/` are listed
- **THEN** they are `external-stores.md`, `getting-started.md`, `headless.md`,
  `member-map.md`, `nesting.md`, and `teams.md`, and no page links
  `nesting-and-stores.md` or `multi-workspace-repos.md`

### Requirement: Workspaces guide practical examples
id: workspaces-doc-examples
base: 002a90b9f5da

The workspaces guide's teams page, `docs/workspaces/teams.md`, SHALL carry
the practical example of carrying several workspaces in one repository; the
guide SHALL carry no separate practical-examples page. The teams page SHALL
document exactly one shape — a base workspace root
holding `--nested` team workspaces — and SHALL NOT present the
sibling-workspaces shape, nor compare the two. The page SHALL show a layout
diagram distinguishing tracked from machine-local content, SHALL tabulate
where the manifest, wiki, oracle queue, initiatives, and member repos live,
and SHALL give the setup and day-to-day commands through the `shipd` binary,
naming `shipd workspace team` as the way to build the layout. The page SHALL
state what the nested shape costs as well as what it gives: the base wiki
only accumulates knowledge written from the base workspace, and a question
queued at the base is answerable only from there. The page SHALL state that
a repository holding several workspaces is cloned with plain `git clone`
rather than the workspace clone verb, and SHALL warn that git provides no
per-directory access control, so separate repos remain the isolation
boundary.

#### Scenario: Only the nested shape is documented
- **WHEN** `docs/workspaces/teams.md` is inspected
- **THEN** it documents the base-plus-nested shape with a layout diagram and
  a table naming where the manifest, wiki, queue, initiatives, and member
  repos live, and it presents no sibling-workspaces shape and no comparison
  between shapes

#### Scenario: Commands honor the guide's conventions
- **WHEN** the teams page's commands are inspected
- **THEN** every interactive command invokes the `shipd` binary, no
  `spec_status.py` path appears on the page, and `shipd workspace team` is
  named as the way to build the layout

#### Scenario: Costs and boundaries are stated
- **WHEN** the teams page is inspected
- **THEN** it states that base knowledge accumulates only from writes made at
  the base and that a base-queued question is answerable only there, directs
  a multi-workspace repository to plain `git clone`, and warns that separate
  repos — not directories — are the access-control boundary

#### Scenario: Each layout fact appears once
- **WHEN** `docs/workspaces/teams.md` is inspected
- **THEN** it holds one layout diagram and one storage table, and it states
  the `shipd workspace team` setup, the plain `git clone` rule, and the
  isolation boundary once each

### Requirement: Teams guide documents the store's git automation
id: workspaces-doc-store-sync
base: 7cac6b88ba2c

The workspaces guide's `teams.md` page SHALL document the store's git
automation in its concurrency section: that an engine write into a workspace
or external store auto-commits locally, that the engine serializes those
commits behind an exclusive lock, that a session-boundary hook fast-forwards
the store at session start and pushes at both boundaries, and that
`store_autocommit` and `store_sync` each turn one of those off. The page
SHALL NOT state that the engine takes no locks or runs no networked git, and
SHALL remain within the line cap of its doc type.
The guide's `getting-started.md` page and the `workspaces.md` index SHALL
likewise instruct no manual push or pull of the workspace repo at a session
boundary, each staying within its own doc-type cap. The customisation guide's
key table SHALL carry a row for each of the two keys naming what it gates and
its default.

#### Scenario: The teams page documents both keys
- **WHEN** `docs/workspaces/teams.md` is read
- **THEN** it names `store_autocommit` and `store_sync`, the auto-commit, the
  lock, and the session-boundary sync

#### Scenario: The stale no-locks claim is gone
- **WHEN** `docs/workspaces/teams.md` is read
- **THEN** it carries no claim that the engine takes no locks or never
  pushes, pulls, or fetches

#### Scenario: No page still prescribes the manual ritual
- **WHEN** `docs/workspaces.md` and `docs/workspaces/getting-started.md` are
  read
- **THEN** neither instructs the reader to run `git pull` at a session start
  or `git push` at its end

#### Scenario: The page stays within its cap
- **WHEN** the documentation lint runs over `docs/workspaces/teams.md`
- **THEN** it reports no length finding

### Requirement: Workspace universe discovery seam
id: workspace-universe-discovery
base: f16e9f238c90

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
- **WHEN** `docs/workspaces/teams.md` is read
- **THEN** it states that `shipd board` covers every declared project's
  repos from the workspace root and only the repos beneath the folder it runs
  from otherwise, and it stays within the line cap of its doc type
