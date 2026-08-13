## MODIFIED Requirements

### Requirement: Wiki store layout
id: wiki-store-layout
base: 726fd18adc86

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
