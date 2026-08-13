# shipd-wiki

### Requirement: Wiki store layout
id: wiki-store-layout

The workspace wiki SHALL live at `<ws-root>/<content-dir>/wiki/`, holding
`schema.md`, `index.md`, `log.md`, `queue.md`, a `sources/` directory, and a
`wiki/` pages directory. The engine SHALL resolve the workspace store through
workspace discovery (the nearest ancestor declaring a `workspace` key), and if
no workspace is discoverable, then every workspace-store wiki operation SHALL
fail with a message naming the requirement of one. In addition, the engine
SHALL resolve a **personal memory store** at the `memory_dir` location
(`<memory_dir>/wiki`, default `~/.shipd-memory/wiki`) by fixed path, bypassing
workspace discovery; a personal store carries the identical layout and grammar
and is written and read through the same engine machinery selected by an
explicit personal-store flag. Engine operations SHALL never parse or modify
existing files under `sources/`.

#### Scenario: Store resolved through the workspace
- **WHEN** a wiki verb runs from a repo inside a workspace without the
  personal-store flag
- **THEN** it operates on `<ws-root>/<content-dir>/wiki/`, not on any
  repo-local path

#### Scenario: No workspace
- **WHEN** a workspace-store wiki verb runs where no ancestor declares a
  workspace
- **THEN** it exits non-zero naming the missing workspace

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
