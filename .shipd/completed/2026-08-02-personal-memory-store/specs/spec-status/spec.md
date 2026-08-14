## MODIFIED Requirements

### Requirement: Wiki status verbs
id: wiki-status-verbs
base: 3f53fe620aa2

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

`wiki-init`, `wiki-show`, and the `cat wiki` verb SHALL each accept a
`--personal` flag: when set, the verb SHALL resolve the personal memory store at
`<memory_dir>/wiki` (default `~/.shipd-memory/wiki`) by fixed path, bypassing
workspace discovery, and operate on it instead of the workspace store. Under
`--personal`, `wiki-show` SHALL report `base: none` (a personal store
participates in no base layering).

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

#### Scenario: Personal flag targets the memory store
- **WHEN** `wiki-init --personal` runs, then `wiki-show --personal`
- **THEN** the store is scaffolded at `<memory_dir>/wiki` (default
  `~/.shipd-memory/wiki`) without workspace discovery, and `wiki-show --personal`
  reports that store's health with `base: none`

## ADDED Requirements

### Requirement: Wiki page removal verb
id: wiki-remove-verb

The status CLI SHALL provide a `wiki-remove <slug>` verb that resolves the store
(the workspace store by default, or the personal memory store under
`--personal`), deletes `wiki/<slug>.md`, removes the page's `index.md` catalog
entry, and appends a `## [YYYY-MM-DD] remove | <slug>` entry to `log.md`. If the
slug is reserved (`index`, `log`, `queue`, `schema`, `sources`), the page does
not exist, or the resulting store fails the whole-store wiki lint — for example
the removal would leave a dead `[[slug]]` wikilink in another page — then the
verb SHALL restore the affected files byte-for-byte, exit non-zero, and name the
reason (naming the linking page for a stranded wikilink). On a clean removal
inside a git work tree, the verb SHALL auto-commit exactly the touched files
with subject `shipd-wiki: remove <slug>`, following the wiki auto-commit semantics
(no commit attempted outside git; a failed commit never fails the removal).

#### Scenario: Successful removal updates page, index, and log
- **WHEN** `wiki-remove some-page` runs where `wiki/some-page.md` exists, is
  indexed, and no other page links to it
- **THEN** the page file and its index entry are gone, `log.md` gains a dated
  `remove | some-page` entry, and in a git work tree a commit scoped to the
  touched files exists with subject `shipd-wiki: remove some-page`

#### Scenario: Inbound wikilink blocks removal
- **WHEN** `wiki-remove some-page` runs while another page contains
  `[[some-page]]`
- **THEN** the verb exits non-zero naming the linking page and the store is
  restored byte-for-byte

#### Scenario: Missing page refused
- **WHEN** `wiki-remove no-such-page` runs and `wiki/no-such-page.md` does not
  exist
- **THEN** the verb exits non-zero naming the missing page and writes nothing

#### Scenario: Reserved slug refused
- **WHEN** `wiki-remove index` runs
- **THEN** the verb exits non-zero citing the reserved slug and writes nothing

#### Scenario: Personal store removal
- **WHEN** `wiki-remove some-page --personal` runs on the personal memory store
- **THEN** it resolves `<memory_dir>/wiki` by fixed path and removes the page
  there, leaving the workspace store untouched

#### Scenario: Non-git store removal succeeds without a commit
- **WHEN** a valid removal runs on a store that is not inside a git work tree
- **THEN** the removal installs, the exit code is zero, and no commit is
  attempted
