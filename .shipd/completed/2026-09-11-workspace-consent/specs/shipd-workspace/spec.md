## ADDED Requirements

### Requirement: Workspace clone-source verbs
id: workspace-sources-verbs

The status CLI SHALL provide a `workspace-sources` verb resolving the
workspace from the invocation directory (failing with the standard
no-workspace error otherwise). The bare form SHALL list each stored
`clone_sources` entry of the map file with its resolved absolute directory.
The `add <dir>` form SHALL store the given path verbatim in the map file's
`clone_sources` array — creating the file or the key when absent, preserving
every other top-level key and value unchanged in content, ensuring the
workspace root's `.gitignore` carries a `.shipd-workspace.local.json` line
outside the marked member block — and SHALL exit zero without duplicating
when the value is already stored. If the directory does not exist, then `add`
SHALL warn and still write. The `remove <dir>` form SHALL delete the matching
stored entry, erroring when no entry matches. A malformed existing map file
SHALL fail `add` and `remove` with the load's own error, never repaired.

#### Scenario: Add creates the key and preserves the member map

- **GIVEN** a workspace whose map file holds a `repos` entry and no
  `clone_sources` key
- **WHEN** `workspace-sources add ~/projects` runs from the root
- **THEN** the map file's `clone_sources` is `["~/projects"]`, the `repos`
  entry survives unchanged, and the root `.gitignore` carries a
  `.shipd-workspace.local.json` line outside the marked member block

#### Scenario: Duplicate add is a zero-exit no-op

- **GIVEN** a map file whose `clone_sources` already holds `~/projects`
- **WHEN** `workspace-sources add ~/projects` runs
- **THEN** the verb exits zero and the array still holds exactly one
  `~/projects` entry

#### Scenario: Missing directory warns but writes

- **WHEN** `workspace-sources add /nowhere/real` runs
- **THEN** the entry is written and a warning names the missing directory

#### Scenario: Remove without a matching entry errors

- **GIVEN** a map file with no `clone_sources` entry `/tmp/x`
- **WHEN** `workspace-sources remove /tmp/x` runs
- **THEN** the verb exits non-zero and the file is unchanged

#### Scenario: Bare form lists entries with resolution

- **GIVEN** a stored `~/projects` entry
- **WHEN** `workspace-sources` runs
- **THEN** the listing shows the stored value and its expanded absolute
  directory

## MODIFIED Requirements

### Requirement: Workspace member map
base: e94df563c53d
id: workspace-member-map

The engine SHALL read an optional machine-local map file at
`<workspace-root>/.shipd-workspace.local.json` whose `repos` value is a JSON
object mapping manifest member paths to local checkout paths; a value MAY
carry a leading `~` (expanded on read) or be relative (resolved against the
workspace root). The file MAY additionally carry a `clone_sources` value: a
JSON array of directory path strings, each expanded (`~`) on read and
resolved against the workspace root when relative; an absent key SHALL read
as an empty list. Member destination resolution SHALL route through a single
seam that returns the mapped destination when the member's manifest path has
an entry and `<workspace-root>/<path>` otherwise. If the file is absent, then
the map SHALL be empty and behavior SHALL be unchanged. If the file is
malformed — invalid JSON, a non-object top level or `repos` value, a
non-string or empty mapping value, or a `clone_sources` value that is not an
array of non-empty strings — then the engine SHALL raise a clear error naming
the file. The workspace report SHALL annotate each mapped member with its
resolved destination, and SHALL surface map keys matching no manifest member
path as a note, never as an error.

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

#### Scenario: Malformed clone_sources errors naming the file

- **WHEN** `.shipd-workspace.local.json` holds
  `{"repos": {}, "clone_sources": "~/projects"}`
- **THEN** the consuming verb fails with an error naming
  `.shipd-workspace.local.json`

#### Scenario: Unknown map key is a note

- **GIVEN** a map whose `repos` carries a key matching no manifest member
  path
- **WHEN** the workspace report runs
- **THEN** the report carries a note naming the unmatched key and exits
  zero

### Requirement: Sync materialization planning
base: e11260c9daaf
id: sync-materialization-planning

The engine SHALL compute a deterministic per-member materialization plan
from the workspace manifest, the resolved configuration, and local disk
state, using only local git probes and never the network. For a member
whose destination exists as a git work tree the plan SHALL record action
`none`, adding a drift note when the destination's origin URL differs from
the manifest `url`; an existing non-git destination SHALL be recorded as
occupied with a drift note and never modified. The candidate scan SHALL
draw on the union of the configuration's `clone_sources` directories and
the workspace-local map file's `clone_sources` directories — configuration
entries first, then local entries, duplicates removed after expansion. For
an absent member the plan SHALL choose the cheapest rung: a work-tree
candidate clone (an immediate child of a scanned directory whose origin URL
equals the manifest `url`, first match in scan order) yields action
`worktree`; a bare candidate yields action `reference-clone`; no candidate
with a `url` yields action `clone`; no `url` yields action
`unmaterializable` with a reason. Actions carrying a rung SHALL include an
advisory command string; the planner SHALL never execute one. Where the
workspace member map holds an entry for a member, its destination SHALL be
the mapped path, the record SHALL carry the resolved mapped destination,
and the action SHALL always be `none` — the materialization ladder SHALL
NOT run and no advisory command SHALL ever target a mapped path; an absent
mapped destination SHALL be recorded state `absent` with a drift note
naming the mapped path. The plan SHALL also compare the marked member-repos
gitignore block against the manifest's member paths and record the missing
or stale lines.

#### Scenario: Absent member with a local work-tree candidate

- **GIVEN** a manifest entry with a `url` and a `clone_sources` directory
  containing a clone whose origin equals that url
- **WHEN** the plan is computed
- **THEN** the member's action is `worktree` naming that candidate as the
  source with an advisory `git worktree add` command

#### Scenario: Workspace-local source yields a candidate on its own

- **GIVEN** no configuration layer declaring `clone_sources` and a map file
  whose `clone_sources` names a directory containing a clone whose origin
  equals the manifest `url`
- **WHEN** the plan is computed
- **THEN** the member's action is `worktree` naming that candidate as the
  source

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
base: 659908ec1051
id: workspace-clone-sync-flows

The `/s:workspace` skill SHALL be the only workspace surface that runs
networked git; the engine verbs it drives stay network-free. When invoked
as `clone <url> [dest]`, the skill SHALL run `git clone` against the URL,
then run the sync flow — its consent round included — from inside the
created root and report the roster; if a workspace root resolves from the
destination's parent, then the skill SHALL proceed and report a note naming
the enclosing workspace root, refusing only when the destination's
immediate parent directory itself declares `workspace` in its own
`.shipd-config.json`. Where the resolved configuration declares
`workspaces_root` (shipd-config workspaces-root-key), `clone` without an
explicit dest SHALL place the clone at `<workspaces_root>/<derived-name>`
(the directory name git derives from the URL, under the declared root), and
an explicit dest whose resolved path lies outside the declared root SHALL
be refused before cloning with an error naming the dest, the declared root,
and `workspaces_root`; when the key is undeclared, destination resolution
SHALL be unchanged. When invoked as `sync`, the skill SHALL obtain the plan
via the status CLI's `workspace-sync --json`; where the plan holds at least
one record with an executable action (`worktree`, `reference-clone`, or
`clone`), the skill SHALL present a single batched consent round before
executing anything, offering: reuse existing checkouts where the plan found
a candidate and materialize the rest (the recommended default), materialize
every absent member fresh, review member-by-member, or stop. On reuse, the
skill SHALL drive `workspace-map set` for each member whose record names a
`source:` candidate — executing no materialization command against those
members — and SHALL execute the advisory commands of the remaining records;
on materialize-fresh it SHALL execute every record's advisory command
exactly as printed; on review it SHALL ask per member before acting, in the
map round's shape; on stop it SHALL execute nothing. Where no clone source
resolves from the configuration or the workspace-local `clone_sources` key
and the plan holds an absent member without a candidate, the same round
SHALL carry one question asking where existing checkouts live, and a given
answer SHALL be persisted through `workspace-sources add` and the plan
recomputed before execution. Where every record's action is `none`, no
round SHALL open. Outside a chosen member-by-member review, once the round
is answered the skill SHALL ask nothing further, reporting `drift:` notes
and `unmaterializable` reasons without modifying anything. If a member's command fails, then the skill SHALL
report the failure against that member and continue with the remaining
members. After executing, the skill SHALL recompute the plan with
`--write-gitignore` to reconcile the marked member block and confirm
convergence, then report the roster via `workspace-show`. If no workspace
is discoverable when `sync` runs, then the skill SHALL report the CLI's
error verbatim and point at `init` or `clone`.

#### Scenario: Clone bootstraps and hands into the consenting sync
- **WHEN** `clone <url>` runs
- **THEN** the repository is cloned with real git, the sync flow — consent
  round included — runs inside the created root, and the roster is reported

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

#### Scenario: Consent precedes every materialization
- **GIVEN** a plan whose records carry executable actions
- **WHEN** `sync` runs
- **THEN** no advisory command executes before the single batched consent
  round is answered

#### Scenario: Reuse maps found candidates instead of materializing
- **GIVEN** a plan where one record names a `source:` candidate and another
  carries a `clone` action with no candidate
- **WHEN** the user chooses reuse in the consent round
- **THEN** the candidate member is mapped via `workspace-map set` with no
  command executed against it, and the other member's clone command runs

#### Scenario: Stop executes nothing
- **GIVEN** a plan with executable actions
- **WHEN** the user chooses stop in the consent round
- **THEN** no command runs and no mapping is written

#### Scenario: Converged plan asks nothing
- **GIVEN** a plan whose records all carry action `none`
- **WHEN** `sync` runs
- **THEN** no consent round opens and the roster is reported

#### Scenario: Sourceless plan asks for checkout folders and replans
- **GIVEN** no resolved clone source and a plan holding an absent member
  with a `clone` action
- **WHEN** the user names a checkout folder in the consent round
- **THEN** the folder is persisted via `workspace-sources add` and the plan
  is recomputed before any command executes

#### Scenario: Sync executes the consented ladder actions
- **GIVEN** a plan whose records carry `worktree` and `clone` actions with
  advisory commands
- **WHEN** `sync` runs and the user consents to materialize them
- **THEN** each record's command is executed as printed and the members are
  git work trees on disk afterwards

#### Scenario: Drift is reported, never repaired
- **GIVEN** a plan record with action `none` carrying a `drift:` note
- **WHEN** `sync` runs
- **THEN** the note is reported and that member is not modified

#### Scenario: A failed member does not abort the run
- **GIVEN** a consented plan whose first member's advisory command fails
- **WHEN** `sync` runs
- **THEN** the failure is reported against that member and the remaining
  members are still executed

#### Scenario: Sync converges and reconciles the ignore block
- **WHEN** `sync` finishes executing a consented plan
- **THEN** the plan is recomputed with `--write-gitignore`, the marked
  member block matches the manifest, and the roster is reported

### Requirement: Workspace setup skill
base: 9307382975c0
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
engine's plan under the single up-front consent round of
workspace-clone-sync-flows; and `map` — a guided mapping round that reads
the sync plan, proposes for each unmapped member an existing local checkout
candidate (the plan's matching clone-source when one exists) or a
user-supplied path, asks in a single round, drives the status CLI's
`workspace-map set` verb per accepted member, and finishes by reporting
the map listing; already-mapped members SHALL be reported, never re-asked.
`sync` SHALL open exactly one consent round per invocation and `clone`
SHALL hand into that same consenting sync flow; outside a chosen
member-by-member review, neither SHALL ask anything further once the round
is answered, and neither SHALL execute a materialization command without
it. Where no clone source resolves from the
configuration or the workspace-local `clone_sources` key, `map` SHALL open
its round with one question asking where existing checkouts live,
persisting a given answer through `workspace-sources add` and re-reading
the plan before proposing candidates. The skill SHALL NOT write the
workspace declaration, the gitignore member block, or the member map file
by hand — all go through the CLI verbs. Where the resolved configuration
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

### Requirement: Workspaces guide
base: 68892cb80983
id: workspaces-doc

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
