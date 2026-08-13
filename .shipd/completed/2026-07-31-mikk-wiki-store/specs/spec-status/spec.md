## ADDED Requirements

### Requirement: Wiki status verbs
id: wiki-status-verbs

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
invalid.

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
