## MODIFIED Requirements

### Requirement: Wiki store layout
id: wiki-store-layout
base: bc4fd47df74d

The workspace wiki SHALL live at `<ws-root>/<content-dir>/wiki/`, holding
`schema.md`, `index.md`, `log.md`, `queue.md`, a `sources/` directory, and a
`wiki/` pages directory. The engine SHALL resolve workspace stores through the
workspace chain (every enclosing ancestor declaring a `workspace` key, nearest
first): a **read** SHALL search the chain's stores in order — a page slug
resolving to the nearest store holding it, `index.md` and `queue.md` resolving
to every chain store holding one so catalogues aggregate, and `log.md` and
`schema.md` resolving to the nearest store only — while every **write** SHALL
target the nearest workspace's store alone, scaffolding that store's layout
when it does not yet exist. A chain member holding no store SHALL be skipped
silently rather than erroring, and if the chain is empty, then every
workspace-store wiki operation SHALL fail with a message naming the requirement
of one. In addition, the engine SHALL resolve a **personal memory store** at
the `memory_dir` location (`<memory_dir>/wiki`, default `~/.shipd-memory/wiki`)
by fixed path, bypassing workspace discovery and the chain entirely; a personal
store carries the identical layout and grammar and is written and read through
the same engine machinery selected by an explicit personal-store flag. Engine
operations SHALL never parse or modify existing files under `sources/`.

#### Scenario: Store resolved through the workspace
- **WHEN** a wiki verb runs from a repo inside a workspace without the
  personal-store flag
- **THEN** it operates on `<ws-root>/<content-dir>/wiki/`, not on any
  repo-local path

#### Scenario: Inherited store answers a read
- **GIVEN** nested workspaces where only the outer one holds a store with a
  page `conventions`
- **WHEN** that page is read from a repo under the inner workspace
- **THEN** the outer store's page is returned

#### Scenario: Catalogues aggregate across the chain
- **GIVEN** nested workspaces whose stores both hold `index.md`
- **WHEN** the index is read from a repo under the inner workspace
- **THEN** both stores' index files are returned, nearest first

#### Scenario: A write scaffolds the nearest store
- **GIVEN** nested workspaces where only the outer one holds a store
- **WHEN** a queue block is appended from a repo under the inner workspace
- **THEN** the inner workspace's store layout is scaffolded and the block lands
  there, leaving the outer store untouched

#### Scenario: No workspace
- **WHEN** a workspace-store wiki verb runs where no ancestor declares a
  workspace
- **THEN** it exits non-zero naming the missing workspace

#### Scenario: Personal store resolved by fixed path
- **WHEN** a wiki verb runs with the personal-store flag
- **THEN** it operates on `<memory_dir>/wiki/` (default `~/.shipd-memory/wiki/`),
  resolved without workspace discovery, carrying the identical store layout
