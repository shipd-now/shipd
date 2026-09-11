## MODIFIED Requirements

### Requirement: Workspaces guide
id: workspaces-doc
base: a209bc1f5987

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
`workspace-map` examples, whose verbs the deliberately read-only binary does
not expose. No page SHALL carry a link or anchor that fails to resolve.

The getting-started page SHALL document the optional `workspaces_root` config
key (shipd-config workspaces-root-key) as the way to mandate the directory
convention — bare init names resolving to `<workspaces_root>/<name>` with the
leaf created, out-of-root init targets and clone destinations refused naming
the target, the declared root, and the key, `--nested` job workspaces inside
the root staying legal, no behavior change when undeclared — and SHALL state
that `shipd config` reports the raw declared value with `~` unexpanded, that
the installed sample config documents the key, and that the doctor `config`
check fails on a malformed value and warns when the declared root directory
is missing.

The member-map page SHALL document the machine-local
`.shipd-workspace.local.json` file and its two disjoint fields — the `repos`
member map at a workspace root and the `workspace_root` pointer in a member
checkout — the `workspace-map` list/set/remove verbs with `/s:workspace map`
as the guided front door, the mapped member's semantics (the planner's action
always `none`, origin drift and missing targets reported as drift notes,
stale keys as notes, a malformed file failing the reading verb), and the
three-rung discovery ladder — ancestor search, then the pointer, then the
origin-URL scan — including URL normalization, the SSH-alias caveat, and the
multi-match ambiguity warning naming the pointer as the remedy.

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
- **THEN** it documents both `.shipd-workspace.local.json` fields, the
  `workspace-map` verbs behind the `/s:workspace map` front door, the mapped
  member's `none`-action and drift semantics, and the three-rung discovery
  ladder with URL normalization, the SSH-alias caveat, and the ambiguity
  warning — and `docs/workspaces.md` no longer carries those sections

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
  `member-map.md`'s `workspace-map` examples

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
