# wiki-base-layering
Status: verified
Epic: portable-workspaces

## Idea

Layer the workspace wiki: a `wiki_base` config key names a durable base store
beneath the job wiki, the oracle reads job-then-base and weights the
workspace's `focus` project, and teach writes job-first with a promote-to-base
move for job-independent content.

### Motivation

Job workspaces get their own focused wiki, but without a base layer every job
starts with an amnesiac oracle and job-independent knowledge fragments across
per-job wikis. The epic decided base + job layering: reads fall back to the
durable base store, writes default to the job wiki with promotion for
job-independent answers.

### Details

- `wiki_base` config key: shape-only, `~`-expanded absolute path naming the
  base wiki store directory (shipd-config).
- `wiki-show` reports the resolved base store on a `base:` line (spec-status).
- Oracle search ladder becomes job wiki → base wiki → repo surfaces, with the
  `focus` project's surfaces weighted first and base citations marked; queue
  writes stay in the job store (shipd-ask; `plugins/s/agents/oracle.md`).
- Teach scans the base index to avoid duplication and offers promote-to-base
  routing at write time (shipd-teach; `plugins/s/skills/teach/SKILL.md`).

Impact: `plugins/s/skills/build/scripts/spec_common.py` (new
`wiki_base_dir()` helper), `spec_status.py` (`cmd_wiki_show`), tests under
`plugins/s/skills/build/tests/`, the two prose surfaces above, and a plugin
version bump to 0.6.19. No new dependencies; engine stays stdlib-only and
network-free.

### Non-goals

- No store-engine changes beyond key resolution and `wiki-show` surfacing: no
  cross-store wikilink resolution, no `--base` flags on wiki verbs, no page
  deletion or migration between stores.
- No migration of existing job pages into the base — promotion is a write-time
  routing choice for newly distilled content.
- No push/pull automation; base-store commits ride the already-shipped wiki
  auto-commit, syncing remotes stays manual.

## Implementation

- **The key points at the base store directory** (e.g. `~/projects/.shipd/wiki`),
  per the epic's decision and design diagram. The value must be a non-empty
  string that is absolute after `~` expansion; a relative value is a shape
  error — the base's location is machine-specific, so `~`-anchoring is the
  portable form and relative anchoring would be ambiguous across layered
  config files. Layered nearest-wins resolution means `~/.shipd-config.json` can
  declare it once per machine while a job workspace may override. Rejected:
  pointing at the base workspace root — the epic fixes the store-dir form,
  and workspace discovery from the store dir reaches the root anyway.
- **No new read/write plumbing: engine verbs reach the base via
  `--root <base-store-path>`.** Workspace discovery walks upward from that
  directory to the base workspace root, so `cat wiki`, `wiki-show`, and
  `spec_emit.py wiki --from` already operate on the base store when rooted
  there, and base emits auto-commit in the base workspace repo via the shipped
  `wiki_autocommit`. Rejected: `--base` flags on the wiki verbs — redundant
  surface, and the epic freezes the store engine.
- **`wiki_base_dir(ws_root)` lives in `spec_common.py`** beside `wiki_dir`:
  resolve the layered config's `wiki_base` key from the workspace root,
  return `None` when undeclared, expand and validate otherwise, raising
  `ConfigError` naming `wiki_base` on a malformed value. `cmd_wiki_show`
  prints `base: <path> (present|absent)` when a base is declared and distinct
  from the job store (realpath comparison), else `base: none` — a
  self-referential base is treated as none, so running inside the base
  workspace itself never double-layers.
- **The oracle's ladder order is binding**: job wiki → base wiki (only when
  `wiki-show` reports a present base) → repo surfaces; within the repo-surface
  rung, a `focus` project declared by the workspace (read via
  `workspace-show`) is consulted first through `project-show`. Base-page
  citations carry a `(base)` marker so callers can tell which store answered.
  Queue writes (`wiki-queue-add`, `wiki-init`) always target the asking
  workspace's own store, never the base — the base is another workspace's
  store and read-only to the oracle.
- **Teach promotion is write-time routing**: the scan reads the base index
  (when a base is present) so distillation never duplicates base pages into
  the job store; each distilled page or drained answer is classified
  job-scoped (default) or job-independent, the interview round offers
  promotion for the latter, and accepted promotions install through a second
  staged `spec_emit.py wiki` rooted at the base store path with the base's own
  full `index.md` and dated `log.md` bookkeeping. Wikilinks stay store-local —
  no staged page `[[links]]` a page that lives only in the other store —
  because the wiki lint resolves links within one store and cross-store lint
  would make job-repo validity machine-dependent. Rejected: moving existing
  job pages to the base — the emit verb cannot delete files, and the epic
  freezes the store engine.

Risks: a declared base pointing at a directory with no store — `wiki-show`
reports `(absent)`, the oracle skips the base rung, and teach offers no
promotion. A malformed value — the consuming verb fails loudly naming
`wiki_base` rather than silently skipping the layer.
