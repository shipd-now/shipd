## ADDED Requirements

### Requirement: Workspace project registry verbs
id: workspace-project-verbs

The engine SHALL provide a `workspace-project` verb that reads and writes the
workspace registry's `projects` map at the resolved workspace root's
`.shipd-config.json` — the engine-owned writer, so the registry is never
hand-authored. The bare form SHALL list each declared project followed by its
repo entries as `<project>: <path> [<url>]`, printing `(no projects)` when
the registry declares none. The `add <project> <path>` form SHALL append a
repo entry to that project, creating the project when absent, and SHALL
accept optional `--url` and `--branch` values stored verbatim. The
`remove <project>` form SHALL delete the whole project, and
`remove <project> --repo <path>` SHALL delete only that repo entry, deleting
the project when its last entry goes. Before any write the engine SHALL
validate the resulting registry with the project-registry rules
(project-registry-semantics); if validation fails, then the verb SHALL report
the validation error, write nothing, and exit non-zero. Every form SHALL
resolve the workspace from the given root and SHALL preserve every other key
in the config file. The verb SHALL NOT reach the network and SHALL NOT create
or materialize any directory.

#### Scenario: Add declares a repo under a new project
- **GIVEN** a workspace whose registry declares no projects
- **WHEN** `workspace-project add main-app api --url https://example.com/api.git`
  runs
- **THEN** the config file declares project `main-app` with one repo entry
  whose path is `api` and whose url is the given one

#### Scenario: An ambiguous repo path refuses
- **GIVEN** a registry where project `alpha` already claims repo path `api`
- **WHEN** `workspace-project add beta api` runs
- **THEN** the verb reports the ambiguous-ownership error, the config file is
  unchanged, and the exit code is non-zero

#### Scenario: Remove drops a single repo entry
- **GIVEN** project `main-app` declaring repo paths `api` and `web`
- **WHEN** `workspace-project remove main-app --repo web` runs
- **THEN** the project declares only `api` afterwards

#### Scenario: Bare form lists the registry
- **GIVEN** a registry declaring project `main-app` with one repo
- **WHEN** `workspace-project` runs with no arguments
- **THEN** the project and its repo entry are listed

#### Scenario: Other config keys survive a write
- **GIVEN** a workspace config declaring `dir` beside its `workspace` object
- **WHEN** any `workspace-project` write runs
- **THEN** the `dir` key is still declared afterwards

### Requirement: Workspace team wizard
id: workspace-team-wizard

The engine SHALL provide an interactive `workspace-team` verb that builds the
nested team layout beneath an existing base workspace. Its behavior SHALL be
split so that everything but the terminal loop is exercisable without a
terminal: a pure planner turning collected answers into an ordered action
plan, pure executors performing one planned action each, and the interactive
loop that collects the answers.

The wizard SHALL resolve the base workspace from the given root; if no
workspace is discoverable, then it SHALL report that, write nothing, and exit
non-zero, naming workspace initialization as the remedy. It SHALL then
collect one or more team names, holding each to the project-name pattern
(project-registry-semantics) so a name is always a safe directory component,
and SHALL re-ask rather than accept a malformed or duplicate name. For each
accepted team the planner SHALL emit, in order: create the team directory
beneath the base when absent; initialize it as a nested git-seeded workspace
(workspace-initialization); declare each repo the user named for that team
through the project registry writer (workspace-project-verbs); and record a
member map entry (workspace-member-map) for each repo whose existing local
checkout the user pointed at. A team directory that already declares a
workspace SHALL be reported and skipped, never re-initialized.

Executing the plan SHALL use local operations only — the verb SHALL NOT clone,
fetch, or otherwise reach the network, and SHALL NOT materialize member
repositories. On completion the verb SHALL report each team created, each
repo declared, and each member mapped, and SHALL name `shipd workspace sync`
as the way to materialize the members it did not map.

While standard input is not a terminal, the verb SHALL write nothing, SHALL
print a note naming itself as interactive, and SHALL exit non-zero.

#### Scenario: Wizard builds a nested team workspace
- **GIVEN** a discoverable base workspace and a collected team name
  `the-mighty-ducks`
- **WHEN** the planned actions are executed
- **THEN** `<base>/the-mighty-ducks/.shipd-config.json` declares a workspace,
  the base is reported as the enclosing root, and the base's own manifest is
  unchanged

#### Scenario: A malformed team name is refused
- **WHEN** a collected team name fails the project-name pattern
- **THEN** the planner emits no action for it and the name is re-asked

#### Scenario: Declared repos reach the team's own registry
- **GIVEN** a team `fortress` collected with repo path `api`
- **WHEN** the planned actions are executed
- **THEN** `<base>/fortress/.shipd-config.json` declares project `fortress`
  with repo path `api`, and the base registry declares no such project

#### Scenario: An existing checkout is mapped, never cloned
- **GIVEN** a collected team repo whose checkout already exists elsewhere on
  this machine
- **WHEN** the planned actions are executed
- **THEN** the team workspace's machine-local member map records that path and
  no git clone runs

#### Scenario: An already-declaring team directory is skipped
- **GIVEN** a team directory that already declares a workspace
- **WHEN** the planned actions are executed
- **THEN** the directory is reported as already initialized and is not
  re-initialized

#### Scenario: Headless invocation writes nothing
- **WHEN** the verb runs with standard input that is not a terminal
- **THEN** it prints a note that it is interactive, writes no file, and exits
  non-zero

## MODIFIED Requirements

### Requirement: Workspaces guide
id: workspaces-doc
base: 0e0cf9e7688e
Dropped: Enterprise guidance presents the dedicated workspaces repository

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

#### Scenario: The nesting and stores part carries its content
- **WHEN** the nesting-and-stores guide page is inspected
- **THEN** it documents nested job workspaces including what inherits across
  the chain, and external artifact stores including where the store lands and
  how its writes are committed

### Requirement: Workspaces guide practical examples
id: workspaces-doc-examples
base: 36cf72f2c986
Dropped: Both shapes are walked with storage tables
Dropped: Trade-offs and boundaries are stated

The workspaces guide SHALL provide a practical-examples part page,
`docs/workspaces/multi-workspace-repos.md`, on carrying several workspaces in
one repository. It SHALL document exactly one shape — a base workspace root
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
- **WHEN** `docs/workspaces/multi-workspace-repos.md` is inspected
- **THEN** it documents the base-plus-nested shape with a layout diagram and
  a table naming where the manifest, wiki, queue, initiatives, and member
  repos live, and it presents no sibling-workspaces shape and no comparison
  between shapes

#### Scenario: Commands honor the guide's conventions
- **WHEN** the practical-examples page's commands are inspected
- **THEN** every interactive command invokes the `shipd` binary, no
  `spec_status.py` path appears on the page, and `shipd workspace team` is
  named as the way to build the layout

#### Scenario: Costs and boundaries are stated
- **WHEN** the practical-examples page is inspected
- **THEN** it states that base knowledge accumulates only from writes made at
  the base and that a base-queued question is answerable only there, directs
  a multi-workspace repository to plain `git clone`, and warns that separate
  repos — not directories — are the access-control boundary

### Requirement: Workspace setup skill
id: workspace-setup-skill
base: 701e4cf11f71

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
engine's plan under the single up-front consent round of
workspace-clone-sync-flows; and `map` — a guided mapping round that reads
the sync plan, proposes for each unmapped member an existing local checkout
candidate (the plan's matching clone-source when one exists) or a
user-supplied path, asks in a single round, drives the status CLI's
`workspace-map set` verb per accepted member, and finishes by reporting
the map listing; already-mapped members SHALL be reported, never re-asked;
and `team` — a guided team-workspace round that mirrors the
`workspace-team` wizard's steps one at a time, driving that verb rather
than reimplementing it.
`sync` SHALL open exactly one consent round per invocation and `clone`
SHALL hand into that same consenting sync flow; outside a chosen
member-by-member review, neither SHALL ask anything further once the round
is answered, and neither SHALL execute a materialization command without
it. Where no clone source resolves from the
configuration or the workspace-local `clone_sources` key, `map` SHALL open
its round with one question asking where existing checkouts live,
persisting a given answer through `workspace-sources add` and re-reading
the plan before proposing candidates. The skill SHALL NOT write the
workspace declaration, the gitignore member block, the project registry, or
the member map file by hand — all go through the CLI verbs. The `init`
verb SHALL keep reporting and stopping on a discoverable workspace, and
SHALL name `team` as the way to add a nested team workspace beneath it. Where the resolved configuration
declares `workspaces_root` (shipd-config workspaces-root-key), the `init`
round SHALL name the declared root and offer target candidates inside it —
substituting `<workspaces_root>/<repo-name>` for a natural candidate that
lies outside the root — and SHALL pass a chosen bare name through to the
verb unchanged, the engine resolving it into the root.

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

#### Scenario: Init on a discoverable workspace points at the team verb

- **WHEN** the skill's `init` verb runs where a workspace root is
  discoverable
- **THEN** the skill reports that root, creates nothing, and names the `team`
  verb as the way to add a nested team workspace beneath it

#### Scenario: Team verb drives the wizard

- **GIVEN** a discoverable base workspace
- **WHEN** the skill's `team` verb runs
- **THEN** the skill drives `workspace-team`, mirroring its steps one at a
  time, and hand-writes no manifest, gitignore block, or map file

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

#### Scenario: Sourceless map asks for checkout folders first

- **GIVEN** no resolved clone source from configuration or the
  workspace-local key
- **WHEN** `/s:workspace map` opens its round
- **THEN** the round carries one checkout-folder question, a given answer
  is persisted via `workspace-sources add`, and candidates are proposed
  from the re-read plan
