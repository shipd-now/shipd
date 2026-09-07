## ADDED Requirements

### Requirement: Workspaces guide
id: workspaces-doc

The repository SHALL provide `docs/workspaces.md`, a user-facing guide to
workspace repos, titled "Workspaces" and using the term "workspace" — never
"portable workspace" — throughout. The guide's examples SHALL follow a single
directory convention — workspace repos live in a `~/workspaces/` parent, one
folder per job (e.g. `~/workspaces/documents-linking/`) — and its layout
diagram SHALL label which folder is the workspace repo. Every interactive
setup command in the guide SHALL invoke the `shipd` binary (`shipd workspace
init`, `shipd wiki init`, `shipd workspace sync`, `shipd workspace`,
`shipd config`), never a `spec_status.py` path, except in the
headless-consumer section. The guide SHALL document team-shared workspace
repos: that any number of engineers may clone the same workspace repo, that
each clone materializes its own machine-local members through the sync
ladder, and that the shared knowledge (wiki, queue, initiatives) travels
between engineers through ordinary git pull and push of the workspace repo.
The guide SHALL state the concurrency expectations for a shared workspace:
the engine takes no locks and never pushes, pulls, or fetches — wiki writes
auto-commit locally, scoped to the touched files; concurrent `queue.md`
appends and `index.md` catalog rewrites merge as ordinary git conflicts while
distinct per-page files merge cleanly; a merge that yields two blocks with
the same `q-<slug>` leaves the queue invalid until de-duplicated; and two
clones answering the same pending question conflict on that block's
`Answer:` line, resolved by keeping exactly one answer, never both. The
guide's team-sharing section SHALL warn that `post-worktree-scripts` resolve
nearest-wins from enclosing configs — so a shared workspace repo's tracked
config supplies worktree hooks to the member repos beneath it — and SHALL
document the first-run consent gate and the `hooks trust` verb as the
receiving machine's control. The guide SHALL document what a headless
consumer needs to read a workspace: a bare `git clone` of the workspace repo,
Python 3, and the plugin's `spec_status.py`, with the read verbs succeeding
while every member repo is absent, while no git binary or identity is
available, and with no `~/.shipd-config.json` on the machine — member `url`
values and `clone_sources` mattering only for materialization, never for
reads.

#### Scenario: Guide covers team-shared workspaces
- **WHEN** `docs/workspaces.md` is inspected
- **THEN** it documents several engineers cloning one workspace repo,
  per-machine member materialization, and git pull/push of the workspace repo
  as the knowledge transport

#### Scenario: Guide states the concurrency expectations
- **WHEN** the guide's team-sharing section is inspected
- **THEN** it states the engine takes no locks and runs no networked git,
  names `queue.md` and `index.md` as the conflict surfaces while per-page
  files merge cleanly, warns that duplicate `q-<slug>` blocks after a merge
  leave the queue invalid until de-duplicated, and warns that concurrent
  answers to one question conflict on its `Answer:` line with exactly one
  answer kept

#### Scenario: Guide warns about inherited worktree hooks
- **WHEN** the guide's team-sharing section is inspected
- **THEN** it warns that a shared workspace repo's tracked config supplies
  `post-worktree-scripts` to member repos beneath it and documents the
  first-run consent gate and the `hooks trust` verb

#### Scenario: Guide covers headless consumers
- **WHEN** the guide's headless-consumer section is inspected
- **THEN** it names the minimal footprint — a workspace clone, Python 3, and
  `spec_status.py` — and states that reads succeed with all members absent,
  without git, and without any machine-level configuration

#### Scenario: Interactive commands use the shipd binary
- **WHEN** the guide's sections outside the headless-consumer section are
  inspected
- **THEN** every setup and day-to-day command invokes the `shipd` binary and
  no interactive example invokes `spec_status.py` by path, while the
  headless-consumer section still names `spec_status.py` as its footprint

#### Scenario: Examples share one directory convention
- **WHEN** the guide's layout and command examples are inspected
- **THEN** every standalone workspace example lives under `~/workspaces/`,
  the layout diagram labels the workspace repo, and no example uses the
  retired `~/jobs/` convention

## REMOVED Requirements

### Requirement: Portable workspaces guide
id: portable-workspaces-doc
base: 99281c99a78c
Reason: The guide is renamed to `docs/workspaces.md` — "portable" was the delivery epic's slug, not a user-facing term — and its mandate is re-issued in full under `workspaces-doc`.
Migration: `workspaces-doc` carries the same team-sharing, concurrency, worktree-hook, and headless-consumer mandates over the renamed file, which moves via `git mv`, preserving history.
