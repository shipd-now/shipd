## MODIFIED Requirements

### Requirement: Wiki store layout
id: wiki-store-layout
base: 6ccc6a5842a5

The workspace wiki SHALL live at `<ws-root>/<content-dir>/wiki/`, holding
`schema.md`, `index.md`, `log.md`, `queue.md`, a `sources/` directory, and a
`wiki/` pages directory. The engine SHALL resolve workspace stores through the
workspace chain (every enclosing ancestor declaring a `workspace` key, nearest
first): a **read** SHALL search the chain's stores in order — a page slug
resolving to the nearest store holding it, `index.md` and `queue.md` resolving
to every chain store holding one so catalogues aggregate, and `log.md` and
`schema.md` resolving to the nearest store only — while every **write** SHALL
target the nearest workspace's store alone, scaffolding that store's layout
when it does not yet exist. A chain member holding no store SHALL be skipped
silently rather than erroring. If the chain is empty and the resolving root's
resolved content directory exists on disk, then wiki resolution SHALL fall
back to the repo-local store at `<root>/<content-dir>/wiki/` — reads and
writes both operating on it with the identical layout, grammar, and
scaffold-on-demand write behavior — and the chain SHALL take precedence again
whenever any ancestor declares a workspace, the repo-local store then not
being consulted. If the chain is empty and the resolved content directory
does not exist, then every workspace-store wiki operation SHALL fail with a
message naming both the missing workspace and the missing content directory.
In addition, the engine SHALL resolve a **personal memory store** at
the `memory_dir` location (`<memory_dir>/wiki`, default `~/.shipd-memory/wiki`)
by fixed path, bypassing workspace discovery and the chain entirely; a personal
store carries the identical layout and grammar and is written and read through
the same engine machinery selected by an explicit personal-store flag. Engine
operations SHALL never parse or modify existing files under `sources/`.

#### Scenario: Store resolved through the workspace
- **WHEN** a wiki verb runs from a repo inside a workspace without the
  personal-store flag
- **THEN** it operates on `<ws-root>/<content-dir>/wiki/`, not on any
  repo-local path

#### Scenario: Inherited store answers a read
- **GIVEN** nested workspaces where only the outer one holds a store with a
  page `conventions`
- **WHEN** that page is read from a repo under the inner workspace
- **THEN** the outer store's page is returned

#### Scenario: Catalogues aggregate across the chain
- **GIVEN** nested workspaces whose stores both hold `index.md`
- **WHEN** the index is read from a repo under the inner workspace
- **THEN** both stores' index files are returned, nearest first

#### Scenario: A write scaffolds the nearest store
- **GIVEN** nested workspaces where only the outer one holds a store
- **WHEN** a queue block is appended from a repo under the inner workspace
- **THEN** the inner workspace's store layout is scaffolded and the block lands
  there, leaving the outer store untouched

#### Scenario: Bare repo falls back to the repo-local store
- **GIVEN** a repo with an existing content directory and no ancestor
  declaring a workspace
- **WHEN** a workspace-store wiki read or write runs from it
- **THEN** it operates on `<root>/<content-dir>/wiki/`, scaffolding the
  layout on a write when it does not yet exist

#### Scenario: Uninitialized directory still fails
- **WHEN** a workspace-store wiki verb runs where no ancestor declares a
  workspace and the resolved content directory does not exist
- **THEN** it exits non-zero naming both the missing workspace and the
  missing content directory

#### Scenario: A later workspace takes precedence over the repo store
- **GIVEN** a repo holding a repo-local store whose ancestor now declares a
  workspace with its own store
- **WHEN** a wiki verb runs from the repo
- **THEN** it operates on the chain's store and the repo-local store is not
  consulted

#### Scenario: Personal store resolved by fixed path
- **WHEN** a wiki verb runs with the personal-store flag
- **THEN** it operates on `<memory_dir>/wiki/` (default `~/.shipd-memory/wiki/`),
  resolved without workspace discovery, carrying the identical store layout

### Requirement: Wiki auto-commit
id: wiki-autocommit
base: 87d9ecf829ba

When an engine wiki write succeeds — a staged `wiki` emission installing
its file set, `wiki-queue-add` appending a valid block, `wiki-queue-answer`
writing an answer into a block, or `wiki-queue-discard` removing a pending
block — and the store directory sits inside a git work tree, the engine SHALL
make a local git commit scoped to exactly the files the write touched,
sweeping in no other staged or modified content. While the store is not
inside a git work tree, the write SHALL succeed unchanged with no commit
attempted. Where the write targets the repo-local fallback store and the
resolved content directory is not externally redirected (no `store_root`
declared), the write SHALL succeed with no commit attempted — committing
in-repo artifacts stays the skill/PR workflow's job, never the engine's;
where `store_root` redirects the content directory externally, a
fallback-store write SHALL auto-commit in the external store exactly as a
workspace-store write does. If the commit fails or the write changed no
bytes, then the write SHALL still exit zero, with a stderr warning for a
failed commit. The engine SHALL run only local git (`status`, `add`,
`commit`) and SHALL never push, pull, or fetch. A failed write SHALL produce
no commit.

#### Scenario: Successful emit commits its file set
- **GIVEN** a workspace repo under git with a configured identity
- **WHEN** `spec_emit.py wiki --from <staging>` installs a page and
  `index.md`
- **THEN** a new commit exists containing exactly the installed store files

#### Scenario: Queue append commits queue.md
- **WHEN** `wiki-queue-add stale-cache …` appends a block in a
  git-initialized workspace with a configured identity
- **THEN** a new commit with subject `shipd-wiki: queue-add q-stale-cache`
  contains only `queue.md`

#### Scenario: Queue answer commits queue.md
- **WHEN** `wiki-queue-answer stale-cache --answer "…"` succeeds in a
  git-initialized workspace with a configured identity
- **THEN** a new commit contains only `queue.md`

#### Scenario: Queue discard commits queue.md
- **WHEN** `wiki-queue-discard stale-cache --reason "…"` succeeds in a
  git-initialized workspace with a configured identity
- **THEN** a new commit with subject
  `shipd-wiki: queue-discard q-stale-cache` contains only `queue.md`

#### Scenario: In-repo fallback store writes without committing
- **GIVEN** a git-initialized repo with a content directory, no workspace,
  and no `store_root`
- **WHEN** a queue block is appended to the repo-local fallback store
- **THEN** the write exits zero and no commit is made

#### Scenario: Non-git store writes without committing
- **WHEN** a wiki emit runs in a workspace that is not inside a git work
  tree
- **THEN** the content installs, the exit code is zero, and no commit is
  attempted

#### Scenario: Commit failure never fails the write
- **WHEN** the scoped commit cannot be made (e.g. no git identity)
- **THEN** the write still exits zero with the content installed and a
  warning on stderr

#### Scenario: Unrelated staged state is not swept
- **GIVEN** an unrelated file staged in the workspace repo's index
- **WHEN** a wiki emit auto-commits
- **THEN** the resulting commit omits the unrelated file, which remains
  staged and uncommitted
