# nested-workspaces
Status: verified

## Idea

Resolve each workspace facility by walking up the directory tree through every
enclosing workspace, so a nested workspace inherits the wiki, the initiatives,
and the project registry of the workspaces above it.

### Motivation

Workspace discovery stops at the nearest ancestor declaring `workspace`
(`plugins/s/skills/build/scripts/spec_common.py:650`), so a workspace nested
inside another sees none of its parent's knowledge — from a repo under a bare
nested workspace, `wiki-show` and `cat wiki index` both exit 1 even when the
enclosing workspace holds a full store. The only inheritance today is the
hand-declared `wiki_base` path, which covers the wiki alone and only one level.

### Details

- Add `workspace_chain(start)` to the engine: every enclosing workspace root,
  nearest first. `find_workspace_root` becomes its head, so nearest-root
  semantics are unchanged for every existing caller.
- Wiki reads resolve across the chain — a page slug takes the nearest store
  that holds it, `index.md` and `queue.md` aggregate across all of them — while
  every wiki write stays in the nearest workspace, scaffolding its store when
  absent.
- Initiative-brief lookups resolve across the chain, so `cat initiative`, the
  linter's `Initiative:` check, and the dashboard's initiative status all
  inherit through one engine seam.
- The project registry (`projects` plus its `focus`) falls through to the
  nearest chain member that *declares* `projects`; exactly one registry wins
  outright and registries are never merged.
- `workspace-init` gains `--nested` to opt into creating a nested workspace;
  the bare verb keeps refusing.
- `config-show`, `workspace-show`, and `wiki-show` report the chain, and the
  oracle's search ladder walks it.
- `wiki_base` is treated as undeclared when it resolves to a store already in
  the chain, so an ancestor base is not searched twice.

Affected capabilities: `shipd-workspace`, `shipd-wiki`, `shipd-config`,
`shipd-ask`, `spec-status` (all modified). Impact: `spec_common.py`,
`spec_status.py`, `spec_lint.py`, `spec_emit.py`, `dashboard.py`,
`plugins/s/agents/oracle.md`, `docs/portable-workspaces.md`, `docs/oracle.md`,
tests under `plugins/s/skills/build/tests/`. No new dependencies.

### Non-goals

- No declared parent link (`workspace.parent`): inheritance is by directory
  ancestry only. A workspace that must inherit from another is filed
  underneath it.
- No merging of project registries, `focus` values, or repo lists across
  levels.
- No chain traversal for sync/member materialization or `clone_sources`.
- No removal or deprecation of `wiki_base`.
- No change to the personal memory store, which stays fixed-path.
- No new networked git and no change to the clone/sync flows.

## Implementation

- **Files and seams.** `spec_common.py` gains `workspace_chain(start)`,
  `resolve_wiki_stores(start)`, `resolve_initiative_brief(start, slug)`, and
  `registry_root(start)`; `find_workspace_root` is reimplemented as the chain's
  head so its ten existing call sites keep today's behavior unless they opt in.
  `spec_status.py` consumes the new helpers in `_wiki_store`, `cat`,
  `wiki-show`, `workspace-show`, `config-show`, and `wiki-queue-add`;
  `spec_lint.py` and `dashboard.py` consume `resolve_initiative_brief`.

- **Ancestry only, no declared link.** The chain is the upward walk and nothing
  else. Rejected: a `workspace.parent` key covering non-ancestor workspaces —
  it buys one topology (job workspaces filed outside the base root) at the cost
  of a second inheritance concept, and filing jobs under the base root buys the
  same result for free.

- **Reads layer outward, writes land nearest.** Every write verb — `wiki-init`,
  the staged `wiki` emit, `wiki-queue-add`, `wiki-queue-answer`, and the
  `initiative` emit — targets `chain[0]` and never an inherited store. This
  follows the existing read-only-base rule (`shipd-ask
  oracle-insufficient-queue`: a queued question lands in the job store, not the
  base). A nearer page then shadows the inherited one, so a correction taught
  locally wins. Rejected: writing to the store the read came from — the read
  source varies per slug, so writes would scatter unpredictably across levels.

- **Catalogues aggregate, pages shadow.** `cat wiki index` and `cat wiki queue`
  print every chain store's file, nearest first, each behind the engine's
  existing `--- <path>` separator (so provenance is free); `cat wiki <slug>`
  takes the first store holding that page; `log` and `schema` stay nearest-only
  as store-local bookkeeping. Rejected: nearest-wins for `index.md` too — the
  oracle scans the index to find candidate pages
  (`plugins/s/agents/oracle.md:62`), so a nearest-only index would hide every
  inherited page from the rung that needs them.

- **The registry falls through but never merges.** `registry_root(start)`
  returns the nearest chain member whose `workspace` object declares a
  `projects` key, falling back to `chain[0]`. `focus` travels with its own
  registry, keeping `workspace-focus`'s same-file consistency check intact.
  Rejected: merging registries across levels — `project_of` resolves by
  containment over *workspace-root-relative* paths with longest-match-wins, and
  `validate_workspace` errors on one resolved path owned by two projects; both
  properties are defined over a single root and break once two registries
  rooted at different directories are combined.

- **Sync stays nearest-only.** `sync-materialization-planning` reads
  `chain[0]`'s manifest alone, so a nested workspace never materializes an
  ancestor's members.

- **`--nested` keeps accidental nesting loud.** `init_workspace` gains a
  `nested` parameter; without it the existing refusal stands verbatim
  (observed: exit 1, `a workspace is already discoverable at …; refusing to
  nest a new one`). Rejected: allowing nesting silently — a stray
  `"workspace": {}` still re-roots writes and sync for everything beneath it,
  which is worth one deliberate flag.

- **`wiki_base` becomes the chain's tail.** Its self-referential carve-out
  widens from "equals the consuming store" to "equals any store in the chain",
  so a base that is also an ancestor is searched once, not twice. The key is
  otherwise untouched, so existing configurations keep working.

Risk: a repository that gains an enclosing workspace it did not have before
silently changes which registry it resolves under. Guarded by the `--nested`
opt-in on creation and by `config-show`/`workspace-show` printing the resolved
chain and the registry's provenance, so the inheritance is always inspectable.
