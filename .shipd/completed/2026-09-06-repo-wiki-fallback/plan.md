# repo-wiki-fallback
Status: verified
Epic: epic-knowledge

## Idea

When no workspace is discoverable, wiki resolution falls back to the repo's
own `<content-dir>/wiki/` store, so teach, queue, and oracle citation all
work in a bare shipd-initialized repo — with `shipd doctor` and
`config-show` reporting which store resolved.

### Motivation

Every workspace-store wiki verb exits 1 with `no workspace found from …` in
a repo without a workspace (observed live in this repo), so the durable
knowledge tier is silently absent: the oracle reports `Queued: none` and
typed decisions are lost to the next session, exactly the gap
`epic-knowledge` names.

### Details

- `spec_common.py` gains a fallback resolution seam: when the workspace
  chain is empty and the repo's resolved content directory exists on disk,
  the wiki anchors at `<root>/<content-dir>/wiki` — same layout, queue, and
  lint; chain resolution takes precedence again the moment any ancestor
  declares a workspace.
- Every workspace-store consumer routes through it: `spec_status.py`
  (`wiki-init`, `wiki-show`, `cat wiki`, `wiki-queue-add`/`-answer`/
  `-discard`, `wiki-remove`, `config-show`) and `spec_emit.py wiki`.
- `wiki-show` and `config-show` annotate a fallback resolution
  `(repo-local fallback)`; `shipd doctor` gains a report-only `wiki` check
  naming the resolved store.
- Prose surfaces catch up: `agents/oracle.md` (queue lands in the fallback
  store; `Queued: none` shrinks to the uninitialized case),
  `skills/teach/SKILL.md` (no longer stops on a missing workspace),
  `skills/doctor/SKILL.md` (recognizes the `wiki` check name).

Affected capabilities: `shipd-wiki`, `spec-status`, `spec-io`, `shipd-cli`,
`shipd-doctor`, `shipd-ask`, `shipd-teach` (all modified). Impact:
`plugins/s/skills/build/scripts/spec_common.py`, `spec_status.py`,
`spec_emit.py`, `plugins/s/bin/shipd`, `plugins/s/agents/oracle.md`,
`plugins/s/skills/teach/SKILL.md`, `plugins/s/skills/doctor/SKILL.md`,
tests under `plugins/s/skills/build/tests/`, plugin version bump.

### Non-goals

- No change to chain semantics where a workspace exists — the fallback
  activates only on an empty chain (epic non-goal); nested-workspace and
  `wiki_base` behavior is untouched there.
- No fallback store in an uninitialized directory: without a resolved
  content directory on disk, the verbs still fail (now naming both missing
  prerequisites) — no `.shipd/wiki` littered into arbitrary cwds.
- No changes to the personal memory store (`--personal` resolution stays a
  fixed path) and no migration tooling from a repo store into a workspace.
- No new doctor remedy: the `wiki` check is report-only.

## Implementation

- **One resolution seam in `spec_common.py`.** Add
  `resolve_wiki_root(start)` returning `(anchor_root, is_fallback)`: the
  chain's nearest member when `workspace_chain(start)` is non-empty, else
  `(start, True)` when `os.path.isdir(specs_dir(start))`, else `None`.
  `resolve_wiki_stores(start)` returns the existing fallback store as the
  single entry when the chain is empty. Rejected: per-verb fallback checks
  in `spec_status.py`/`spec_emit.py` — the resolution must not drift
  between consumers.
- **Eligibility gates on a shipd-initialized repo** (content dir exists on
  disk), per the epic's success criterion; the failure message for an
  uninitialized root names both the missing workspace and the missing
  content directory (today's message, `spec_status.py:2675`, is
  initiative-flavored and reused verbatim by wiki verbs).
- **No engine auto-commit for an in-repo fallback store.** Fallback-store
  writes route through `store_autocommit(root, …)` (`spec_common.py:1010`)
  instead of `wiki_autocommit`: no commit when the content dir resolves
  in-repo — committing in-repo artifacts stays the skill/PR workflow's job
  — while a `store_root`-redirected external store still auto-commits.
  Rejected: committing into the code repo — it would land engine commits
  on protected branches.
- **`wiki_base_dir` guard extends to the fallback store**: a `wiki_base`
  resolving to the fallback store's own directory reads as undeclared,
  mirroring the existing chain-member guard (`spec_common.py:1237`).
- **Reporting**: `wiki-show` prints `wiki: <path> (repo-local fallback)`;
  `config-show` prints a `wiki:` line in all three states (workspace
  store / fallback with marker / `none` naming what is missing);
  `bin/shipd` gains `check_wiki` directly after `check_schema` in
  `default_checks` (`bin/shipd:894`), always `ok`, mutating nothing.
- **`cat wiki` in fallback mode** is a single-store resolution:
  `stores=[wiki_dir(root)]`, `nearest_root=root`, never a provenance
  annotation.
- **Prose surfaces** follow the engine: `oracle.md` queue behavior item 4
  (fallback queue write; `Queued: none (<why>)` only when ineligible),
  teach's step-0 stop shrinks to the uninitialized case, doctor SKILL's
  parsed-check list gains `wiki`.
- **Risk**: a repo store adopted later by a workspace could double-resolve;
  guarded because the fallback path equals `wiki_dir(repo)` — once an
  ancestor declares `workspace`, the chain wins outright and the repo
  store is simply not a chain member (epic non-goal honored).
- Verified premises: `wiki-show`/`cat wiki index`/`wiki-queue-add` all
  currently exit 1 with `no workspace found from …`; `shipd doctor` prints
  14 checks with no wiki line and exits 0; `config-show` prints
  `workspace: none discoverable` with no wiki line (all run in this
  worktree).
- Plugin version bump in `plugins/s/.claude-plugin/plugin.json` ships with
  the change, per AGENTS.md.
