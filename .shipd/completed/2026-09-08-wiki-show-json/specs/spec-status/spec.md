## MODIFIED Requirements

### Requirement: JSON output mode
id: json-output
base: 4af9499cfb1c

The status CLI's read verbs — `show`, `status`, `locate`, `epic-show`,
`workspace-show`, and `wiki-show` — SHALL accept a `--json` flag that emits exactly one JSON
document on stdout and nothing else, derived from the same data as the text
rendering: `status` an object with `name`, `kind` (`change` or `epic`), and
`status`; `show` on a change an object with `name`, `kind`, `status`,
`tasks` (done/in_progress/total counts, or null when no checklist exists),
and `metadata`; `show`'s epic fallback and `epic-show` an object with
`name`, `kind": "epic"`, `status`, `metadata`, `worktree` (the hosting
worktree name or null), `project` (the owning declared project's slug when
the epic resolved from a project universe, else null), `shipped` counts,
and the four board `lanes` with member entries carrying `slug`, `state`,
`risk`, and a `worktree` boolean; the bare `show` workspace report an
object with `kind": "workspace"`, `totals`, `shipped`, and `lanes` whose
rows each carry a `project` field — the owning declared project's slug for
a row aggregated from a project universe, `null` for a row from the
invocation root's own universe; `locate` an array of objects with `change`,
`root`, `dir`, `status`, and `project` (the owning declared project's slug,
or `null` for a match from the invocation root's own universe);
`workspace-show` an object mirroring the text report's fields; and
`wiki-show` the store-state document its own requirement
(`wiki-status-verbs`) defines. Without the
flag, the text output SHALL stay byte-identical to its pre-flag behavior on
every input the pre-flag verb rendered successfully, and error handling
(stderr `Error:` lines, exit codes) SHALL be unchanged in both modes; on an
input the verb rejects, partial stdout the pre-flag rendering emitted before
failing MAY be omitted.

#### Scenario: Status of a change is machine-readable
- **WHEN** `status <change> --json` runs on an existing change
- **THEN** stdout parses as one JSON object with `kind` `change` and its
  status value

#### Scenario: Epic report is machine-readable
- **WHEN** `epic-show <slug> --json` runs
- **THEN** stdout parses as one JSON object with `kind` `epic`, the four
  lanes, and each member's slug, state, risk, and worktree flag

#### Scenario: A project-hosted epic's report carries its project
- **GIVEN** a workspace root whose declared project repo hosts the epic
- **WHEN** `epic-show <slug> --json` runs from the workspace root
- **THEN** the object's `project` is that project's slug, and a root-hosted
  epic's `project` is null

#### Scenario: Workspace report is machine-readable
- **WHEN** `show --json` runs with no name and no selection
- **THEN** stdout parses as one JSON object with `kind` `workspace` and the
  totals matching the text report's counts

#### Scenario: Workspace report rows carry their project
- **GIVEN** a workspace root with one declared project repo holding an epic
- **WHEN** `show --json` runs bare from the workspace root
- **THEN** the project repo's rows carry its slug in `project` and the
  invocation root's own rows carry `project` null

#### Scenario: Locate rows are an array
- **WHEN** `locate <change> --json` runs for a change hosted in a worktree
- **THEN** stdout parses as a JSON array whose entries carry change, root,
  dir, status, and a null `project`

#### Scenario: Text mode is unchanged without the flag
- **WHEN** any of the six verbs runs without `--json`
- **THEN** the output is byte-identical to the pre-change text rendering

#### Scenario: Errors are unaffected by the flag
- **WHEN** `status no-such-thing --json` runs for a name matching nothing
- **THEN** the behavior matches the flagless form (`?` on stdout per the
  status contract), and a fatal error path still prints `Error:` to stderr
  with a nonzero exit

### Requirement: Wiki status verbs
id: wiki-status-verbs
base: 004196d35610

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

`wiki-show` SHALL additionally accept a `--json` flag emitting exactly one
JSON object describing the resolved store's full state, derived from the
same reads as the text report: `store` (the absolute store path), `present`
(whether the store directory exists), `fallback` and `personal` booleans
naming the resolution, `chain` (the inherited chain store paths nearest
first, an empty list where the text form prints `chain: none`), `base`
(`null` where the text form prints `base: none`, else an object with `path`
and `present`), `pages` (sorted by slug, each with `slug`, `summary` — the
store's `index.md` entry summary or `null` when unindexed — and `body`, the
page file's raw markdown), `coverage` (an object with sorted `unindexed`
and `orphaned` slug lists), `queue` (the `queue.md` blocks in document
order, each with `id` and a `fields` object of its present field values),
and `log` (the `log.md` entries in document order, each with `date`, `op`,
and `subject`). While `--json` is set, the flag SHALL compose with
`--personal` and with the fallback resolution unchanged, and the no-store
error SHALL be identical to the flagless form's. Page bodies are a JSON-only
read: the flagless rendering SHALL NOT open page files, undecodable bytes in
a page body SHALL be replaced with U+FFFD rather than failing the read, and
if a page file cannot be read, then `wiki-show --json` SHALL exit non-zero
with an `Error:` line naming the file.

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

#### Scenario: Store state is machine-readable
- **WHEN** `wiki-show --json` runs against a store holding an indexed page,
  an unindexed page, a pending queue block, and a log entry
- **THEN** stdout parses as one JSON object whose `pages` carry each page's
  slug, index summary (or null), and raw markdown body, whose `coverage`
  names the unindexed slug, whose `queue` carries the block's id and field
  values, and whose `log` carries the entry's date, op, and subject

#### Scenario: Flagless output is unchanged by the flag's existence
- **WHEN** `wiki-show` runs without `--json` against the same store
- **THEN** the output is byte-identical to the pre-flag text rendering

#### Scenario: Personal store composes with the flag
- **WHEN** `wiki-show --personal --json` runs against an existing personal
  store
- **THEN** the object's `personal` is true, `chain` is empty, and `base` is
  null

#### Scenario: Page bodies are a JSON-only read
- **GIVEN** a store whose page file holds non-UTF-8 bytes
- **WHEN** `wiki-show` runs flagless and then with `--json`
- **THEN** the flagless report renders exactly as it did before the flag
  existed, and the JSON document carries that page's body with undecodable
  bytes replaced
