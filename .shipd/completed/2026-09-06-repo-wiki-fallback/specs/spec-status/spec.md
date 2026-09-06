## MODIFIED Requirements

### Requirement: Wiki status verbs
id: wiki-status-verbs
base: 1a86c409d154

The status CLI SHALL provide wiki verbs operating on the workspace store:
`wiki-init` SHALL scaffold the store layout (seeding `schema.md` with the
grammar conventions, empty `index.md` and `queue.md`, a first dated `log.md`
entry, and empty `sources/` and `wiki/` directories) in the nearest workspace
and SHALL refuse when that wiki directory already exists; `wiki-show` SHALL
print the store root, page count, index-coverage health, pending-question
count, and the last log entry; the `cat` verb SHALL accept a `wiki` kind
resolving `<slug>` across the workspace chain — a page slug to `wiki/<slug>.md`
in the nearest chain store holding it, the reserved slugs `index` and `queue`
to every chain store's file of that name in nearest-first order, and the
reserved slugs `log` and `schema` to the nearest store's file only. Where a
file printed by `cat wiki` comes from an inherited chain store rather than
the nearest one, the verb SHALL annotate that file's separator line with the
inherited store's workspace root, so a reader never derives provenance by
comparing a root-relative separator against an absolute store path; a file
from the nearest store SHALL carry no annotation. And
`wiki-queue-add <q-slug>` SHALL append a queue block built from `--question`,
`--options`, `--recommendation`, and optional `--origin` values with a
current-date `Asked:` line and `Answer: pending` **to the nearest workspace's
store, scaffolding that store when it does not exist**, restoring the prior
`queue.md` and exiting non-zero when the slug already exists in that store or
the resulting queue is invalid. `wiki-show` SHALL additionally print a `chain:`
line listing the inherited chain stores that exist, nearest first, or `chain:
none` when the store has no inherited member; where the nearest workspace holds
no store but a chain member does, `wiki-show` SHALL report the nearest store as
absent, print the `chain:` line, and exit zero, exiting non-zero only when the
resolution holds no store at all; and a `base:` line reporting the
resolved `wiki_base` store: `base: <path> (present)` when the resolved base
directory exists, `base: <path> (absent)` when it is declared but missing, and
`base: none` when the key is undeclared or resolves to any chain store's
directory; if the declared `wiki_base` value is malformed, then `wiki-show`
SHALL exit non-zero with an error naming `wiki_base`.

Where no workspace is discoverable and the resolving root's resolved content
directory exists, every workspace-store wiki verb (`wiki-init`, `wiki-show`,
`cat wiki`, `wiki-queue-add`, `wiki-queue-answer`, `wiki-queue-discard`,
`wiki-remove`) SHALL resolve the repo-local fallback store at
`<root>/<content-dir>/wiki` and operate on it with otherwise unchanged
semantics — a single-store resolution with no inherited chain member and
never a provenance annotation. Under a fallback resolution `wiki-show` SHALL
annotate its store line `(repo-local fallback)`, report `chain: none`, and
resolve its `base:` line from the root's own layered configuration, treating
a `wiki_base` resolving to the fallback store's own directory as undeclared.
Where neither a workspace nor a content directory exists, the verbs SHALL
exit non-zero naming both missing prerequisites.

`wiki-init`, `wiki-show`, and the `cat wiki` verb SHALL each accept a
`--personal` flag: when set, the verb SHALL resolve the personal memory store at
`<memory_dir>/wiki` (default `~/.shipd-memory/wiki`) by fixed path, bypassing
workspace discovery and the chain, and operate on it instead of the workspace
store. Under `--personal`, `wiki-show` SHALL report `chain: none` and `base:
none` (a personal store participates in no chain or base layering).

#### Scenario: Scaffold once
- **WHEN** `wiki-init` runs in a workspace with no wiki, then runs again
- **THEN** the first run creates the seeded layout and the second exits
  non-zero naming the existing store

#### Scenario: Queue append is guarded
- **WHEN** `wiki-queue-add stale-cache --question … --options …
  --recommendation …` runs twice
- **THEN** the first run appends a `## q-stale-cache` block with
  `Answer: pending` and the second exits non-zero leaving `queue.md` unchanged

#### Scenario: Queue append scaffolds the nearest store
- **GIVEN** nested workspaces where only the outer one holds a wiki store
- **WHEN** `wiki-queue-add stale-cache …` runs from a repo under the inner
  workspace
- **THEN** the inner workspace's store is scaffolded, the block lands in its
  `queue.md`, and the outer store is unchanged

#### Scenario: Mediated page read
- **WHEN** `cat wiki <slug>` names an existing page
- **THEN** the page's content prints with the engine's file separator, and an
  unknown slug exits non-zero

#### Scenario: Inherited page reads through the chain
- **GIVEN** nested workspaces where only the outer store holds
  `wiki/conventions.md`
- **WHEN** `cat wiki conventions` runs from a repo under the inner workspace
- **THEN** the outer store's page prints with its own path as the separator

#### Scenario: An inherited read is annotated with its provenance
- **GIVEN** nested workspaces where only the outer store holds
  `wiki/conventions.md`
- **WHEN** `cat wiki conventions` runs from a repo under the inner workspace
- **THEN** the separator line carries the outer workspace's root as that file's
  provenance, while the same read against a page held by the nearest store
  carries no such annotation

#### Scenario: Index aggregates across the chain
- **GIVEN** nested workspaces whose stores both hold `index.md`
- **WHEN** `cat wiki index` runs from a repo under the inner workspace
- **THEN** both files print, nearest first, each behind its own separator

#### Scenario: Absent nearest store still reports the chain
- **GIVEN** nested workspaces where only the outer one holds a wiki store
- **WHEN** `wiki-show` runs from a repo under the inner workspace
- **THEN** the nearest store is reported absent, the `chain:` line names the
  outer store, and the exit code is zero

#### Scenario: Chain line reports inherited stores
- **GIVEN** nested workspaces whose stores both exist
- **WHEN** `wiki-show` runs from a repo under the inner workspace
- **THEN** the output carries a `chain:` line naming the outer store

#### Scenario: Fallback store serves a bare repo
- **GIVEN** a repo with an existing content directory and no discoverable
  workspace
- **WHEN** `wiki-init` runs, then `wiki-queue-add stale-cache …`, then
  `cat wiki queue`
- **THEN** the store lives at `<root>/<content-dir>/wiki`, the block lands in
  its `queue.md`, and the read prints it with no provenance annotation

#### Scenario: wiki-show marks the fallback store
- **GIVEN** a repo-local fallback store
- **WHEN** `wiki-show` runs
- **THEN** the store line carries `(repo-local fallback)` and the output
  reports `chain: none`

#### Scenario: Uninitialized root names both prerequisites
- **WHEN** a workspace-store wiki verb runs where no ancestor declares a
  workspace and no content directory exists
- **THEN** it exits non-zero naming the missing workspace and the missing
  content directory

#### Scenario: Declared base is reported with presence
- **GIVEN** a workspace whose config declares `wiki_base` pointing at an
  existing base store directory outside its chain
- **WHEN** `wiki-show` runs
- **THEN** the output carries `base: <expanded-path> (present)`, and
  `(absent)` instead when the directory does not exist

#### Scenario: No base reports none
- **WHEN** `wiki-show` runs where no layer declares `wiki_base`, or where the
  key resolves to a chain store's own directory
- **THEN** the output carries `base: none`

#### Scenario: Personal flag targets the memory store
- **WHEN** `wiki-init --personal` runs, then `wiki-show --personal`
- **THEN** the store is scaffolded at `<memory_dir>/wiki` (default
  `~/.shipd-memory/wiki`) without workspace discovery, and `wiki-show --personal`
  reports that store's health with `chain: none` and `base: none`

### Requirement: Config-show verb
id: config-show-verb
base: 5a485f87d776

The status CLI SHALL provide `config-show` printing the resolved layered
configuration: each effective top-level key with the path of the layer that
supplied it (or `default`), the resolved content directory name, and the
workspace root when one is discoverable (or a note that none is). Where the
resolved configuration declares `store_root`, the verb SHALL additionally
print the resolved absolute external content directory path, so a
mis-declared store is inspectable at a glance. Where the resolved workspace
chain carries more than one member, the verb SHALL additionally print the
whole chain in nearest-first order. The verb SHALL additionally print a
`wiki:` line reporting the resolved wiki store: the nearest workspace's
store path when a chain exists, the repo-local fallback path annotated
`(repo-local fallback)` when the chain is empty and the content directory
exists, and `wiki: none` naming the missing prerequisites otherwise. The
verb SHALL NOT require a discoverable workspace and SHALL exit zero on a
default-only resolution.

#### Scenario: Provenance is printed per key
- **GIVEN** the repo layer declares `valid_themes` and the workspace layer
  declares `workspace`
- **WHEN** `config-show` runs
- **THEN** each key is listed with the config file path that supplied it

#### Scenario: Nested chain is printed
- **GIVEN** nested workspaces enclosing the repository
- **WHEN** `config-show` runs
- **THEN** the workspace root is the nearest one and the chain lists both
  roots, nearest first

#### Scenario: Defaults-only still succeeds
- **WHEN** `config-show` runs where no `.shipd-config.json` exists in any layer
- **THEN** the content directory prints as `.shipd`, keys show `default`, and
  the exit code is zero

#### Scenario: External store path is printed
- **GIVEN** a resolved configuration declaring `store_root`
- **WHEN** `config-show` runs
- **THEN** the output includes the resolved absolute external content
  directory path

#### Scenario: Wiki line reports the resolved store
- **WHEN** `config-show` runs in a workspace repo, in a bare repo with a
  content directory, and in an uninitialized directory
- **THEN** the `wiki:` line names the workspace store, the fallback path
  with `(repo-local fallback)`, and `none`, respectively

### Requirement: Wiki page removal verb
id: wiki-remove-verb
base: 8c03717dc3e6

The status CLI SHALL provide a `wiki-remove <slug>` verb that resolves the
store exactly as the other wiki verbs do (the nearest workspace's store, the
repo-local fallback store where no workspace is discoverable but the content
directory exists, or the personal memory store under `--personal`), deletes
`wiki/<slug>.md`, removes the page's `index.md` catalog entry, and appends a
`## [YYYY-MM-DD] remove | <slug>` entry to `log.md`. If the
slug is reserved (`index`, `log`, `queue`, `schema`, `sources`), the page does
not exist, or the resulting store fails the whole-store wiki lint — for example
the removal would leave a dead `[[slug]]` wikilink in another page — then the
verb SHALL restore the affected files byte-for-byte, exit non-zero, and name the
reason (naming the linking page for a stranded wikilink). On a clean removal
the verb SHALL auto-commit exactly the touched files with subject
`shipd-wiki: remove <slug>`, following the wiki auto-commit semantics in
full — no commit attempted outside git, a failed commit never failing the
removal, and no commit attempted for a repo-local fallback store whose
content directory is not externally redirected.

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

#### Scenario: Fallback-store removal makes no commit
- **GIVEN** a repo-local fallback store inside a git repo with no
  `store_root`
- **WHEN** `wiki-remove some-page` succeeds
- **THEN** the page, index entry, and log update land and no commit is made
