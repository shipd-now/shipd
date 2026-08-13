## ADDED Requirements

### Requirement: Wiki auto-commit
id: wiki-autocommit

When an engine wiki write succeeds — a staged `wiki` emission installing
its file set, or `wiki-queue-add` appending a valid block — and the store
directory sits inside a git work tree, the engine SHALL make a local git
commit scoped to exactly the files the write touched, sweeping in no other
staged or modified content. While the store is not inside a git work tree,
the write SHALL succeed unchanged with no commit attempted. If the commit
fails or the write changed no bytes, then the write SHALL still exit zero,
with a stderr warning for a failed commit. The engine SHALL run only local
git (`status`, `add`, `commit`) and SHALL never push, pull, or fetch. A
failed write SHALL produce no commit.

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
