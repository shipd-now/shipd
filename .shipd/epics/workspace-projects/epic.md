# workspace-projects
Status: complete
Theme: spec-engine

## Introduction

Shipd's Initiative → Epic → Change hierarchy is only two-thirds
real: epics and changes exist, but an initiative is still just a
validated slug with nothing behind it, and nothing groups the repos an
initiative spans. This epic builds the workspace layer: workspace
discovery (`.shipd/workspace.json` as marker and registry),
initiative briefs that track outcomes as tickable requirements,
projects that group repos with steering context to focus planning, and
an `/s:initiative` skill driving it all.

Success criteria: a brief can be created, listed, reviewed
(requirements ticked), and attached to an epic; `Initiative:`
references resolve against the workspace when one is present while
bare-checkout CI stays green; a workspace with no declared projects
behaves exactly as a single implicit project.

### Non-goals

- No sync or projection of briefs to any central service.
- No cross-repo build orchestration — the workspace focuses planning,
  not execution.
- No changes to the epic or change artifact formats.

## Decisions

- **A workspace contains projects; they are not the same thing.** The
  workspace is the physical container discovered on disk; a project is a
  logical grouping of repos within it, carrying steering context. A workspace
  with no declared projects behaves as one implicit `default` project, so
  single-repo/solo use needs zero setup. Rejected: workspace-is-a-project —
  it forces one workspace per product and an initiative could never span
  products.
- **Root discovery is an upward search for `.shipd/workspace.json`.** The
  workspace root is the nearest ancestor directory (starting from the repo
  root) containing `.shipd/workspace.json`; that same stdlib-parseable
  JSON file is the registry of projects and their member repos, with room for
  future workspace state. Rejected: a bare marker file (registry left
  homeless) and an implicit `initiatives/`-directory marker (false positives,
  no registry).
- **Initiatives may be project-scoped.** A brief may carry an optional
  `Project: <slug>` metadata line; absent means workspace-wide. The slug must
  exist in the registry. This settles the question deferred from the
  plan-metadata roadmap. Rejected: always-workspace-wide — product-scoped
  goals would pollute every project's view.
- **Cross-repo references are CI-safe by construction.** `Initiative:` (and
  `Project:`) resolution runs only when a workspace root is discoverable:
  workspace present + missing target = lint error; no workspace (bare CI
  checkout) = silent skip, so the `ci` gate never depends on files outside
  the repo. This asymmetry with `Epic:` (always an error) is deliberate —
  epics are in-repo, briefs are not.
- **Artifacts follow the established header conventions.** Briefs and
  project files reuse the `# <slug>` + `Status:` + metadata-block grammar
  parsed by `spec_common.parse_plan_metadata`, with artifact-specific key
  sets and status vocabularies pinned in each member change's plan.
  Initiative requirements are `- [ ]` checkboxes ticked over time by review —
  outcomes, not tasks.
- **Engine additions stay stdlib-only** (constitution), live in
  `spec_common.py` as shared helpers (`find_workspace_root`,
  `load_workspace`), and every member change carries tests and its own
  plugin version bump per `AGENTS.md`.

## Design

Three layers, built bottom-up so each member change lands on a working seam:

1. **Discovery primitive** — `find_workspace_root(start)` (upward search) and
   `load_workspace(ws_root)` (registry parsing/validation) in
   `spec_common.py`. Everything else consumes these two calls; nothing else
   touches the filesystem above the repo.
2. **Artifacts** — initiative briefs at
   `<workspace-root>/initiatives/<slug>/brief.md` and project context at
   `<workspace-root>/projects/<slug>/context.md`, with the registry in
   `.shipd/workspace.json` naming each project and its repos. Lint gains
   brief validation plus `Initiative:`/`Project:` resolution under the
   CI-safe rule; the status CLI gains initiative verbs (show/review-style
   progress over the brief's checkboxes).
3. **Skill surface** — `/s:initiative` (new, list, review, set) drives the
   CLIs, mirroring how `/s:epic` drives the epic verbs. It lands last, when
   the primitives and artifacts it narrates already exist.

The decomposition follows those layers, with projects split from briefs so
the registry/context machinery (highest unknowns: multi-repo semantics) does
not block initiative briefs landing.

## Changes

| Change | Description | Code | Integration | Unknowns | Risk |
| --- | --- | --- | --- | --- | --- |
| workspace-discovery | `find_workspace_root` upward search and `.shipd/workspace.json` registry parsing in `spec_common`, with tests | medium | low | medium | low |
| initiative-briefs | Brief artifact at `<ws>/initiatives/<slug>/brief.md`, checkbox requirements, lint validation and CI-safe `Initiative:` resolution, initiative status verbs | medium | medium | medium | medium |
| project-groups | Project registry entries, `projects/<slug>/context.md`, the implicit default project, and `Project:` scoping on briefs | medium | medium | high | medium |
| initiative-skill | `/s:initiative` skill: new, list, review (tick requirements), and set on an epic | low | medium | low | low |
