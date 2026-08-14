## ADDED Requirements

### Requirement: Wiki store layout
id: wiki-store-layout

The workspace wiki SHALL live at `<ws-root>/<content-dir>/wiki/`, holding
`schema.md`, `index.md`, `log.md`, `queue.md`, a `sources/` directory, and a
`wiki/` pages directory. The engine SHALL resolve the store through workspace
discovery (the nearest ancestor declaring a `workspace` key), and if no
workspace is discoverable, then every wiki operation SHALL fail with a message
naming the requirement of one. Engine operations SHALL never parse or modify
existing files under `sources/`.

#### Scenario: Store resolved through the workspace
- **WHEN** a wiki verb runs from a repo inside a workspace
- **THEN** it operates on `<ws-root>/<content-dir>/wiki/`, not on any
  repo-local path

#### Scenario: No workspace
- **WHEN** a wiki verb runs where no ancestor declares a workspace
- **THEN** it exits non-zero naming the missing workspace

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
