## MODIFIED Requirements

### Requirement: Wiki status verbs
id: wiki-status-verbs
base: d1b4e1f6198f

The status CLI SHALL provide wiki verbs operating on the workspace store:
`wiki-init` SHALL scaffold the store layout (seeding `schema.md` with the
grammar conventions, empty `index.md` and `queue.md`, a first dated `log.md`
entry, and empty `sources/` and `wiki/` directories) and SHALL refuse when the
wiki directory already exists; `wiki-show` SHALL print the store root, page
count, index-coverage health, pending-question count, and the last log entry;
the `cat` verb SHALL accept a `wiki` kind resolving `<slug>` to
`wiki/<slug>.md`, with the reserved slugs `index`, `log`, `queue`, and `schema`
resolving to the top-level files of the same name; and `wiki-queue-add
<q-slug>` SHALL append a queue block built from `--question`, `--options`,
`--recommendation`, and optional `--origin` values with a current-date
`Asked:` line and `Answer: pending`, restoring the prior `queue.md` and
exiting non-zero when the slug already exists or the resulting queue is
invalid. `wiki-show` SHALL additionally print a `base:` line reporting the
resolved `wiki_base` store: `base: <path> (present)` when the resolved base
directory exists, `base: <path> (absent)` when it is declared but missing, and
`base: none` when the key is undeclared or resolves to the store's own
directory; if the declared `wiki_base` value is malformed, then `wiki-show`
SHALL exit non-zero with an error naming `wiki_base`.

#### Scenario: Scaffold once
- **WHEN** `wiki-init` runs in a workspace with no wiki, then runs again
- **THEN** the first run creates the seeded layout and the second exits
  non-zero naming the existing store

#### Scenario: Queue append is guarded
- **WHEN** `wiki-queue-add stale-cache --question … --options …
  --recommendation …` runs twice
- **THEN** the first run appends a `## q-stale-cache` block with
  `Answer: pending` and the second exits non-zero leaving `queue.md` unchanged

#### Scenario: Mediated page read
- **WHEN** `cat wiki <slug>` names an existing page
- **THEN** the page's content prints with the engine's file separator, and an
  unknown slug exits non-zero

#### Scenario: Declared base is reported with presence
- **GIVEN** a workspace whose config declares `wiki_base` pointing at an
  existing base store directory
- **WHEN** `wiki-show` runs
- **THEN** the output carries `base: <expanded-path> (present)`, and
  `(absent)` instead when the directory does not exist

#### Scenario: No base reports none
- **WHEN** `wiki-show` runs where no layer declares `wiki_base`, or where the
  key resolves to the store's own directory
- **THEN** the output carries `base: none`
