## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Wiki auto-commit
id: wiki-autocommit
base: 2e5834f0fb38

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
