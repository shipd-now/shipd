## MODIFIED Requirements

### Requirement: Workspace initialization
id: workspace-initialization
base: ff1848926831

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

#### Scenario: Git option inside an existing work tree does not re-init
- **GIVEN** a target already inside a git work tree whose ignore file already
  carries the marked member-repos block
- **WHEN** initialization runs with the git option
- **THEN** no new repository is created and the marked block is not duplicated

### Requirement: Workspaces guide
id: workspaces-doc
base: d5dd8988d199

The repository SHALL provide the workspaces guide as an index page plus six
part pages, each conforming to the shipd documentation standard: a doc-type
marker comment on the first line, and a total line count within that type's
cap. `docs/workspaces.md` SHALL be the concept index: titled "Workspaces",
explaining the workspace concept with the layout diagram (labeling which
folder is the workspace repo), and introducing each part with one descriptive
sentence, a usage example, and a relative link. The part pages SHALL live
under `docs/workspaces/`, each opening with a link back to the index:
`getting-started.md` (how-to: setup through day-to-day use, including the
`workspaces_root` coverage), `member-map.md` (reference: the member map and
workspace discovery from outside the workspace), `nesting-and-stores.md`
(reference: nested job workspaces and `store_root`), `teams.md` (how-to:
team-shared workspaces and the enterprise layout), `headless.md` (how-to:
headless consumers), and `multi-workspace-repos.md` (how-to: the practical
examples).

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
expectations — the engine takes no locks and never pushes, pulls, or fetches;
wiki writes auto-commit locally, scoped to the touched files; concurrent
`queue.md` appends and `index.md` catalog rewrites merge as ordinary git
conflicts while distinct per-page files merge cleanly; duplicate `q-<slug>`
blocks after a merge leave the queue invalid until de-duplicated; two clones
answering one question conflict on that block's `Answer:` line, resolved by
keeping exactly one answer — and SHALL warn that `post-worktree-scripts`
resolve nearest-wins from enclosing configs, with the first-run consent gate
and the `hooks trust` verb as the receiving machine's control. The teams page
SHALL also carry the enterprise guidance: the primary layout is one dedicated
workspaces repository holding one folder per team or group, each folder a job
workspace, materialized partially per engineer and mapped with the member map
where checkouts already exist — and a group whose knowledge must stay
isolated SHALL be directed to a workspace repository of its own, because
separate repos remain the isolation boundary.

The headless page SHALL document what a headless consumer needs to read a
workspace: a bare `git clone`, Python 3, and the plugin's `spec_status.py`,
with reads succeeding while every member repo is absent, without a git binary
or identity, and with no `~/.shipd-config.json` on the machine.

#### Scenario: Index introduces every part
- **WHEN** `docs/workspaces.md` is inspected
- **THEN** it is titled "Workspaces", explains the concept with the labeled
  layout diagram, and carries one entry per part page — a descriptive
  sentence, a usage example, and a relative link — for all six parts

#### Scenario: Every guide page carries its marker and fits its cap
- **WHEN** `docs_lint.py` runs over the index and the six part pages
- **THEN** it exits 0, with the index marked `concept`, `member-map.md` and
  `nesting-and-stores.md` marked `reference`, and the other four pages marked
  `how-to`

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
  transport, the no-locks/no-networked-git concurrency expectations with
  `queue.md` and `index.md` as conflict surfaces, duplicate `q-<slug>`
  invalidity, single-answer conflict resolution, and the inherited
  worktree-hooks warning with the consent gate and `hooks trust`

#### Scenario: Enterprise guidance presents the dedicated workspaces repository
- **WHEN** the teams page's enterprise guidance is inspected
- **THEN** the primary layout is one dedicated workspaces repository holding
  one folder per team or group, each folder a job workspace, with partial
  materialization and the member map named, and a per-group repository named
  as the remedy when a group's knowledge must stay isolated

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

#### Scenario: The nesting and stores part carries its content
- **WHEN** the nesting-and-stores guide page is inspected
- **THEN** it documents nested job workspaces including what inherits across
  the chain, and external artifact stores including where the store lands and
  how its writes are committed
