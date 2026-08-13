# personal-memory
Status: complete
Theme: developer-experience

## Introduction

The workspace wiki captures *collective* knowledge — conventions, architecture,
project facts everyone in the workspace shares — and the `portable-workspaces`
work made that store git-committed and cloneable. But there is nowhere to keep
what is true about *the person*: that mikk prefers vim over emacs, ASCII
diagrams over Mermaid, a terse review tone. Those preferences are not workspace
knowledge — they hold across every repo and every workspace the user touches —
yet today they evaporate between sessions, and putting them in the shared wiki
would wrongly commit personal taste into a repo teammates clone.

This epic adds a **personal memory** layer: a private, per-user, git-backed
store of learned preferences that spans all workspaces, sits *above* the wiki in
the ask-mikk read ladder, and is captured, listed, and removed through three new
skills. It reuses the existing wiki grammar and engine wholesale — the personal
store is "just another wiki store" rooted at a personal, configurable location
(default `~/.shipd-memory/`) — so retrieval stays index- and grep-based over
markdown with no embeddings and no external services, exactly as the
`mikk-knowledge` epic bound. Because that store can be a git repo, every capture
and removal auto-commits locally through the wiki engine's existing
`wiki_autocommit`, and a one-time first-run flow offers to initialize it and
wire it to the user's personal remote — so a new machine is one `git clone`
away from the user's accumulated memory.

Success criteria: a preference stated once (via `/s:preferences`, or drawn from
the session) lands as a `memory-<subject>` page in the personal store; the
ask-mikk oracle consults that store *first* and answers a matching decision
without a user round; `/s:memory` lists the stored memories and `/s:forget`
removes one under a confirmed prompt; and when the store is a git repo every
write is committed locally, with pushing to the remote an explicit, confirmed
step the engine never performs on its own.

### Non-goals

- **Not a config-sync feature.** This syncs *memory*, not settings. Repo- and
  workspace-scoped config (`dir`, `valid_themes`, `workspace`, `wiki_base`,
  `focus`, the pipeline) already travels with its own repo; the only personal,
  user-global config is `~/.shipd-config.json`'s small `build` block. The personal
  repo *may* hold a copy of that file as a user convention, but no engine reads,
  writes, or reconciles settings.
- **No embeddings, vector store, database, or external service** — retrieval
  stays index- and grep-based over markdown and engine scripts stay
  stdlib-only, inheriting the `mikk-knowledge` bindings.
- **The engine never pushes, pulls, or fetches.** It runs only local git
  (`status`/`add`/`commit`) via the existing `wiki_autocommit`; remote creation
  and pushing are skill-driven and always confirmed, never automatic.
- **No team/multi-user memory.** The store is single-user by construction; page
  leases, cross-writer merge handling, and shared-memory semantics are out of
  scope.
- **No automatic/background capture.** `/s:preferences` runs on demand; there
  is no session hook that silently records preferences.

## Decisions

Settled with the user across the planning conversation:

- **Personal, not shared.** Memories live in a private per-user store, never the
  workspace wiki. The wiki is collective knowledge that gets committed to a
  shared, portable repo; personal preferences (vim, ASCII) are about the
  individual and would be mis-scoped there. Rejected: a `memory-*` page family
  inside the workspace wiki (the shape an earlier draft took, now abandoned);
  rejected: a gitignored workspace-local personal layer (private but does not
  follow the user across workspaces).
- **Reuse the wiki grammar and engine.** The personal store *is* a wiki store —
  `index.md`, `log.md`, `wiki/<slug>.md` pages, wiki lint, staged emit — rooted
  at a personal location instead of resolved through workspace discovery. This
  makes `wiki-show`, the staged `spec_emit.py wiki` write path, and a new
  `wiki-remove` verb all work against the personal root unchanged. Rejected: a
  bespoke flat memory format (throws away lint, index, and removal machinery)
  and a single aggregated `memories.md` blob (breaks per-page removal and
  coarsens grep retrieval).
- **Configurable location, default `~/.shipd-memory/`.** A new personal-store
  config key resolves the store, defaulting to a dedicated `~/.shipd-memory/` repo
  named to match the user's mental model and kept separate from `~/.shipd/builds/`
  telemetry. The user can point it at wherever they cloned their personal repo.
- **Personal memory is the top rung of the read ladder.** ask-mikk consults the
  personal store *before* the job wiki, base wiki, and repo surfaces — a
  personal preference is the highest-signal answer for how to treat this user.
  This reverses the abandoned draft's "no oracle changes" stance, which was only
  tenable while memories lived in the wiki the oracle already read.
- **Git-backing via the existing local-commit machinery.** `wiki_autocommit`
  already commits scoped files on every write when the store is inside a git
  work tree and no-ops otherwise, so a git-backed personal store auto-commits
  for free. The only new behavior is a first-run flow that offers to `git init`
  the store, optionally create and wire a personal remote (via `gh`), and offer
  a confirmed push. Rejected: engine-driven push/pull (violates the
  local-git-only binding) and silent pushing (an outward-facing action must be
  confirmed).
- **`memory-<subject>` page grammar, one page per memory.** A page is a one-line
  preference statement plus a provenance block (origin, date). One memory per
  page keeps removal, listing, and oracle retrieval per-page.

Binding constraints inherited by every member:

- Engine scripts are stdlib-only Python 3; `statusline.sh` stays POSIX. Every
  member touching `plugins/s/` bumps the plugin version in its own PR, and
  engine changes carry unittests under `plugins/s/skills/build/tests/`.
- Every write into any wiki store — job, base, or personal — goes through the
  staged, lint-gated emit/verbs, never an in-place file edit.
- Members ship one worktree = one branch = one auto-merging PR, and skill
  changes get a local eval run before shipping.

## Design

Five pieces along the read → write → sync seams:

```
                      personal memory (NEW, private, git-backed)
                      ~/.shipd-memory/  (config key; default)
  /s:preferences ─▶ extract ▸ reconcile ▸ staged wiki emit ─▶  .git auto-commit
  /s:memory      ─▶ list index (memory-* pages)                 wiki/wiki/memory-*.md
  /s:forget      ─▶ locate ▸ confirm ▸ wiki-remove              index.md · log.md
                                                                    ▲
  ask-mikk oracle read ladder:  PERSONAL memory ──┘  (top rung, read first)
                                job wiki ▸ base wiki ▸ repo surfaces  (unchanged)

  first run (no .git):  offer git init  ▸  optional gh remote  ▸  confirmed push
```

- **The store + engine foundation ships first** — personal-store resolution (a
  config key + a fixed-path resolution mode that bypasses workspace discovery),
  the `wiki-remove` verb (general per-page removal with backup → lint →
  byte-for-byte restore, refusing a removal that strands an inbound `[[link]]`),
  and reuse of `wiki-show`/emit against a personal root. Everything else depends
  on it and nothing else.
- **The oracle rung** is a focused contract change to `shipd-ask`/`oracle.md`:
  search the personal store first, cite it, and route personal preferences above
  wiki knowledge. It needs only the store.
- **The skills** are the write and browse paths. `/s:preferences` is the
  richest (extract → reconcile against existing `memory-*` pages → staged emit);
  `/s:memory` (list) and `/s:forget` (locate → confirm → `wiki-remove`) are
  the browse path and share the store contract.
- **Git-backing** layers the first-run setup and portability flow onto the
  capture path, plus the documented config-as-convention note — the piece the
  user most wants and the natural last member, since it only makes sense once
  captures exist to commit.

Member order is dependency order: `personal-memory-store` →
`oracle-personal-rung` → `memory-capture` → `memory-browse` →
`memory-git-backing`. The oracle rung and the skills both need only the store;
git-backing needs the capture path.

## Changes

| Change | Description | Code | Integration | Unknowns | Risk |
| --- | --- | --- | --- | --- | --- |
| personal-memory-store | Engine foundation: personal-store config key + fixed-path resolution reusing the wiki grammar, and a `wiki-remove` verb (backup → lint → byte-for-byte restore, refuses stranded links) with unittests | high | medium | medium | medium |
| oracle-personal-rung | ask-mikk/oracle contract change: search the personal memory store first in the read ladder and cite it above wiki knowledge | low | medium | low | medium |
| memory-capture | `/s:preferences` skill: extract preference candidates, reconcile against existing `memory-*` pages, install through staged wiki emit into the personal store | medium | medium | medium | medium |
| memory-browse | `/s:memory` (read-only list of `memory-*` pages) and `/s:forget` (locate → confirmed AskUserQuestion → `wiki-remove`) skills over the personal store | medium | low | low | low |
| memory-git-backing | First-run git flow on capture: detect non-git store, offer `git init` + optional `gh` remote + confirmed push; document the config-as-convention note | medium | medium | medium | medium |
