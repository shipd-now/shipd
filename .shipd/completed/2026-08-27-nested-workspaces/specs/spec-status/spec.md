## MODIFIED Requirements

### Requirement: Config-show verb
id: config-show-verb
base: 6a8a7969aa94

The status CLI SHALL provide `config-show` printing the resolved layered
configuration: each effective top-level key with the path of the layer that
supplied it (or `default`), the resolved content directory name, and the
workspace root when one is discoverable (or a note that none is). Where the
resolved workspace chain carries more than one member, the verb SHALL
additionally print the whole chain in nearest-first order. The verb SHALL NOT
require a discoverable workspace and SHALL exit zero on a default-only
resolution.

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

### Requirement: Workspace init verb
id: workspace-init-verb
base: d5d7e25efde0

The status CLI SHALL provide `workspace-init <path>` which initializes a
workspace at the given directory through the engine's workspace
initialization — declaring `workspace` in `<path>/.shipd-config.json` — and
prints the created workspace root on success. The verb SHALL accept a `--git`
flag requesting the engine's git option (git-init when the target is not
already inside a work tree, plus the seeded member-repos `.gitignore` block),
and a `--nested` flag requesting the engine's nested option, which permits
creating the workspace beneath an enclosing one and reports the enclosing root
it nests under. If initialization refuses or errors (a workspace already
discoverable from the target without `--nested`, a target that itself already
declares `workspace`, or a missing target directory), then the CLI SHALL exit
non-zero with that error. Unlike the other workspace verbs, `workspace-init`
SHALL NOT require a discoverable workspace to run.

#### Scenario: Init verb creates and prints the root
- **GIVEN** an existing directory with no discoverable workspace
- **WHEN** `workspace-init <path>` runs against it
- **THEN** `.shipd-config.json` declares `workspace` there, the created root is
  printed, and the exit code is zero

#### Scenario: Init verb refuses under an existing workspace
- **WHEN** `workspace-init <path>` runs where a workspace root is already
  discoverable from `<path>`
- **THEN** the CLI exits non-zero with an error naming the existing root

#### Scenario: Nested flag creates the nested workspace
- **WHEN** `workspace-init <path> --nested` runs where a workspace root is
  already discoverable from `<path>`
- **THEN** `<path>/.shipd-config.json` declares `workspace`, the enclosing root
  is reported, and the exit code is zero

#### Scenario: Git flag produces a git-ready root
- **GIVEN** an existing directory with no discoverable workspace and no git
  work tree
- **WHEN** `workspace-init <path> --git` runs
- **THEN** the created root is a git repository whose `.gitignore` carries
  the marked member-repos block, and the exit code is zero

### Requirement: Workspace status verbs
id: workspace-status-verbs
base: 4be2085bbb76

The status CLI SHALL provide `workspace-show` printing the workspace root,
the declared `focus` project when the resolved registry carries one, each
declared project with its repos (annotated when a path is not a directory on
this machine, and annotated `[url]` when the entry carries a clone URL) and
whether its `context.md` exists, each initiative with its status and project
scope, and a note that the current repository falls under the implicit
default project when it resolves to no declared project; and `project-show
<slug>` printing one declared project's repos (annotated the same way), its
`context.md` presence, and the initiatives scoped to it. Both verbs SHALL read
the registry resolved from the workspace chain, and where that registry comes
from a chain member other than the workspace root, `workspace-show` SHALL print
that member's root as the registry's provenance. An undeclared slug SHALL be a
non-zero error naming the declared slugs. Both verbs SHALL resolve repo paths
uniformly from string and object entry shapes, SHALL resolve the workspace from
the repository root, and SHALL exit non-zero with a clear error when no
workspace is discoverable.

#### Scenario: Workspace overview lists projects and initiatives
- **GIVEN** a workspace declaring project `alpha` (one repo present, one
  absent, no context.md) and an initiative `mvp-readiness` scoped
  `Project: alpha`
- **WHEN** `workspace-show` runs
- **THEN** the output lists `alpha` with both repos (one annotated absent),
  `context: no`, and `mvp-readiness` with its status and `alpha` scope

#### Scenario: Focus and clone URLs surface in the overview
- **GIVEN** a registry declaring `focus: "alpha"` and an alpha repo entry
  carrying a `url`
- **WHEN** `workspace-show` runs
- **THEN** the output names `alpha` as the focus and annotates that repo
  line `[url]`

#### Scenario: Inherited registry names its provenance
- **GIVEN** nested workspaces where only the outer one declares `projects`
- **WHEN** `workspace-show` runs from a repo under the inner workspace
- **THEN** the outer workspace's projects are listed and the output names the
  outer root as the registry's provenance

#### Scenario: Project view shows scoped initiatives
- **WHEN** `project-show alpha` runs in that workspace
- **THEN** the output lists alpha's repos, its context presence, and
  `mvp-readiness` among its scoped initiatives

#### Scenario: Unknown project slug errors
- **GIVEN** the registry declares only `alpha`
- **WHEN** `project-show beta` runs
- **THEN** the CLI exits non-zero naming the declared slugs

#### Scenario: Verbs require a workspace
- **WHEN** `workspace-show` runs in a checkout with no discoverable
  workspace
- **THEN** the CLI exits non-zero saying no workspace was found

### Requirement: Wiki status verbs
id: wiki-status-verbs
base: 3e5291dd1d5a

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
absent, print the `chain:` line, and exit zero, exiting non-zero only when no
chain member holds a store; and a `base:` line reporting the
resolved `wiki_base` store: `base: <path> (present)` when the resolved base
directory exists, `base: <path> (absent)` when it is declared but missing, and
`base: none` when the key is undeclared or resolves to any chain store's
directory; if the declared `wiki_base` value is malformed, then `wiki-show`
SHALL exit non-zero with an error naming `wiki_base`.

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
