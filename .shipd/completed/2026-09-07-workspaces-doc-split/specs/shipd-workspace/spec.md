## MODIFIED Requirements

### Requirement: Workspaces guide
id: workspaces-doc
base: dc3e2ca22814

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
base: bb550e790db0

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
