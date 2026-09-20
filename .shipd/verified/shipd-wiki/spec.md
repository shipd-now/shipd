# shipd-wiki

### Requirement: Wiki store layout
id: wiki-store-layout

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

### Requirement: Wiki page grammar
id: wiki-page-grammar

Wiki pages SHALL be markdown files `wiki/<slug>.md` with kebab-case slugs, and
the slugs `index`, `log`, `queue`, `schema`, and `sources` SHALL be reserved
(invalid as page slugs). A `[[slug]]` wikilink in a wiki page or in `index.md`,
outside fenced code blocks, SHALL resolve to an existing page.

#### Scenario: Dead wikilink
- **WHEN** a page contains `[[missing-page]]` and no `wiki/missing-page.md`
  exists
- **THEN** the store is invalid and the violation names the page and the link

#### Scenario: Reserved slug
- **WHEN** a page is named `wiki/index.md`
- **THEN** the store is invalid citing the reserved slug

### Requirement: Index catalog and append-only log
id: wiki-index-and-log

`index.md` SHALL catalog every page as a line `- [[slug]] — <summary>` (lines
not matching the entry shape are ignored), and the set of catalog entries SHALL
equal the set of pages under `wiki/`. Every level-2 header in `log.md` SHALL
match `## [YYYY-MM-DD] <op> | <subject>`.

#### Scenario: Unindexed page
- **WHEN** `wiki/some-page.md` exists with no `- [[some-page]] — …` index entry
- **THEN** the store is invalid naming the unindexed page

#### Scenario: Malformed log header
- **WHEN** `log.md` contains a level-2 header not matching the dated entry
  shape
- **THEN** the store is invalid naming the offending line

### Requirement: Pending-question queue
id: wiki-question-queue

`queue.md` SHALL hold pending questions as `## q-<slug>` blocks with unique
kebab-case slugs, each carrying non-empty `- Asked:`, `- Question:`,
`- Options:`, `- Recommendation:`, and `- Answer:` lines, where `Answer:` is
`pending` until the user supplies an answer.

#### Scenario: Complete block passes
- **WHEN** `queue.md` holds a `## q-` block with all five fields and
  `Answer: pending`
- **THEN** the store is valid

#### Scenario: Missing field
- **WHEN** a `## q-` block lacks a `- Recommendation:` line
- **THEN** the store is invalid naming the block and the missing field

### Requirement: Wiki auto-commit
id: wiki-autocommit

When an engine wiki write succeeds — a staged `wiki` emission installing
its file set, `wiki-queue-add` appending a valid block, `wiki-queue-answer`
writing an answer into a block, or `wiki-queue-discard` removing a pending
block — the store directory sits inside a git work tree, and the resolved
`store_autocommit` key is true, the engine SHALL make a local git commit
scoped to exactly the files the write touched, sweeping in no other staged or
modified content. The engine SHALL hold an exclusive lock across the staging
and committing of those paths, so two concurrent engine writes to one store
serialize instead of racing git's index lock. If the lock cannot be taken or
locking is unavailable on the platform, then the engine SHALL proceed
unlocked rather than fail the write. While `store_autocommit` resolves false,
or the store is not inside a git work tree, the write SHALL succeed unchanged
with no commit attempted. Where the write targets the repo-local fallback
store and the resolved content directory is not externally redirected (no
`store_root` declared), the write SHALL succeed with no commit attempted —
committing in-repo artifacts stays the skill/PR workflow's job, never the
engine's; where `store_root` redirects the content directory externally, a
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

#### Scenario: Concurrent writes each land a commit
- **GIVEN** a git-initialized workspace store with a configured identity
- **WHEN** two engine queue writes to that store run at the same time
- **THEN** both writes exit zero and each lands its own scoped commit

#### Scenario: An unavailable lock never fails the write
- **GIVEN** a git-initialized workspace store where the exclusive lock
  cannot be taken
- **WHEN** a queue block is appended
- **THEN** the write exits zero with the block installed

### Requirement: Queue answer verb
id: wiki-queue-answer-verb

`spec_status.py` SHALL provide a `wiki-queue-answer <slug> --answer "<text>"`
verb that resolves the workspace store exactly as `wiki-queue-add` does,
accepts the bare slug (prefixing `q-` itself), locates the `## q-<slug>` block
in `queue.md`, and replaces its `- Answer: pending` line with
`- Answer: <text>`, printing the `q-<slug>` and exiting 0. Where the verb is
invoked with an `--advisory` flag, it SHALL store the answer with an
`advisory: ` prefix — `- Answer: advisory: <text>` — marking the captured
knowledge as advisory rather than binding; without the flag the answer is
stored unprefixed as before. If the store or the block is missing, or the
block's `Answer:` line is not `pending`, then the verb SHALL write nothing
and exit non-zero naming the reason — an answered block is owned by the
`/s:teach` drain and is never overwritten. The verb SHALL use only the Python
standard library.

#### Scenario: Pending block is answered
- **GIVEN** a queue block `## q-retention` whose answer line is
  `- Answer: pending`
- **WHEN** `wiki-queue-answer retention --answer "prune after one release"`
  runs
- **THEN** the block's answer line reads
  `- Answer: prune after one release`, and the verb prints `q-retention` and
  exits 0

#### Scenario: Advisory flag prefixes the stored answer
- **GIVEN** a pending queue block `## q-pr-unlock`
- **WHEN** `wiki-queue-answer pr-unlock --advisory --answer "always run the
  unlock"` runs
- **THEN** the block's answer line reads
  `- Answer: advisory: always run the unlock` and the verb exits 0

#### Scenario: Missing block errors
- **WHEN** `wiki-queue-answer no-such-entry --answer "x"` runs against a queue
  with no `## q-no-such-entry` block
- **THEN** nothing is written and the verb exits non-zero naming the missing
  block

#### Scenario: Already-answered block is refused
- **GIVEN** a queue block whose `Answer:` line is not `pending`
- **WHEN** `wiki-queue-answer` targets that block
- **THEN** nothing is written and the verb exits non-zero naming the
  already-answered state

### Requirement: Queue discard verb
id: wiki-queue-discard-verb

`spec_status.py` SHALL provide a `wiki-queue-discard <slug> --reason "<text>"`
verb that resolves the workspace store exactly as `wiki-queue-add` does,
accepts the bare slug (prefixing `q-` itself), locates the `## q-<slug>`
block in `queue.md`, and — when the block's `Answer:` line is `pending` —
removes the entire block, printing the `q-<slug>` and exiting 0. The
`--reason` text SHALL be required and non-empty; it is echoed to the caller,
not stored. If the store or the block is missing, or the block's `Answer:`
line is not `pending`, then the verb SHALL write nothing and exit non-zero
naming the reason — an answered block is owned by the `/s:teach` drain and is
never discarded. The verb SHALL use only the Python standard library, and
every other queue block SHALL be preserved verbatim.

#### Scenario: Pending block is discarded
- **GIVEN** a queue block `## q-framework-pick` whose answer line is
  `- Answer: pending`
- **WHEN** `wiki-queue-discard framework-pick --reason "self-evidencing"`
  runs
- **THEN** the block is removed from `queue.md`, other blocks are unchanged,
  and the verb prints `q-framework-pick` and exits 0

#### Scenario: Answered block is refused
- **GIVEN** a queue block whose `Answer:` line is not `pending`
- **WHEN** `wiki-queue-discard` targets that block
- **THEN** nothing is written and the verb exits non-zero naming the
  answered state

#### Scenario: Missing block errors
- **WHEN** `wiki-queue-discard no-such-entry --reason "x"` runs against a
  queue with no `## q-no-such-entry` block
- **THEN** nothing is written and the verb exits non-zero naming the missing
  block

### Requirement: Session-boundary store sync
id: store-sync-hook

The plugin SHALL ship a stdlib-only `store_sync.py` outside
`plugins/s/skills/build/scripts/`, so the engine's no-network rule is
preserved, and SHALL register it on both `SessionStart` and `SessionEnd`.
While the resolved `store_sync` key is true and the resolved store is a
workspace or external store inside a git work tree carrying an `origin`
remote, the script SHALL on `SessionStart` fetch the store's upstream, merge
it `--ff-only`, then push any local commits, and SHALL on `SessionEnd` push
any local commits. Where the store resolves to the repo-local fallback, the
script SHALL run no git at all, so it never pushes a working repository's
branch. Every git invocation SHALL carry a timeout. If any step fails — the
key is false, no store resolves, no upstream is configured, the merge is not
a fast-forward, the push is rejected, a call times out, or configuration
resolution fails — then the script SHALL print at most one warning line to
stderr and SHALL still exit 0.

#### Scenario: Session start fast-forwards and pushes
- **GIVEN** a workspace store inside a git work tree with an `origin`
  remote, one unpushed local commit, and one new upstream commit
- **WHEN** the hook runs at session start
- **THEN** the upstream commit is merged fast-forward, the local commit is
  pushed, and the script exits 0

#### Scenario: Session end pushes pending commits
- **GIVEN** the same store with one unpushed local commit
- **WHEN** the hook runs at session end
- **THEN** the commit is pushed and the script exits 0

#### Scenario: A divergent upstream warns and changes nothing
- **GIVEN** a store whose upstream has commits the local branch does not
  contain and whose local branch has commits the upstream does not
- **WHEN** the hook runs at session start
- **THEN** no merge is applied, one warning line is printed to stderr, and
  the script exits 0

#### Scenario: The key false silences the hook
- **GIVEN** a resolved configuration declaring `store_sync` false
- **WHEN** the hook runs
- **THEN** no git runs, nothing is printed, and the script exits 0

#### Scenario: An in-repo fallback store is never synced
- **GIVEN** a repo with no workspace and no `store_root`
- **WHEN** the hook runs
- **THEN** no git runs against the repository and the script exits 0

#### Scenario: A broken environment never breaks the session
- **GIVEN** a store directory that is not inside a git work tree
- **WHEN** the hook runs
- **THEN** the script exits 0
