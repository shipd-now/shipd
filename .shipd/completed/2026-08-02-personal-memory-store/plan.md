# personal-memory-store
Status: verified
Epic: personal-memory
Theme: developer-experience

## Idea

Add the engine foundation for a private, per-user memory store: a `memory_dir`
config key with fixed-path resolution that bypasses workspace discovery, a
`--personal` targeting flag on the wiki verbs so they operate on that store, and
a general `wiki-remove` verb — reusing the existing wiki grammar, lint, and
auto-commit wholesale.

### Motivation

The `personal-memory` epic needs a store for personal preferences that is
private, git-backed, and spans every workspace — separate from the shared
workspace wiki, which is resolved only through workspace discovery and cannot
reach a personal `~/.shipd-memory/`. This is the epic's first member: the store and
engine everything else (oracle rung, capture/browse skills, git-backing) depends
on, and nothing else depends on.

### Details

- Add a `memory_dir` config key (spec_common) resolving the personal store's
  root, `~`-expanded and validated absolute, defaulting to `~/.shipd-memory`; a
  `memory_store_dir()` helper returns the store directory `<memory_dir>/wiki`.
- Add a `--personal` flag to the wiki verbs (`wiki-init`, `wiki-show`,
  `cat wiki`, and the new `wiki-remove`) and to `spec_emit.py wiki`: when set,
  the verb resolves the store via `memory_store_dir()` and skips workspace
  discovery.
- Add a general `wiki-remove <slug>` verb: back up → delete the page, its
  `index.md` entry, and append a `remove` log entry → run the whole-store wiki
  lint → restore byte-for-byte on any finding (e.g. a stranded inbound
  `[[slug]]` link) → auto-commit the touched files.
- Reuse the existing store grammar unchanged: pages at `<store>/wiki/<slug>.md`,
  `index.md`/`log.md`, wiki lint, and `wiki_autocommit` (which already commits
  iff the store is inside a git tree — so a git-backed `~/.shipd-memory` commits for
  free).

Affected capabilities: `shipd-config` (modified — new `memory_dir` key), `shipd-wiki`
(modified — store may resolve as the personal store), `spec-status` (modified —
`--personal` on the wiki verbs; added — `wiki-remove`), `spec-io` (modified —
`--personal` on emit). Impact:
`plugins/s/skills/build/scripts/spec_common.py`, `spec_status.py`,
`spec_emit.py`; new tests under `plugins/s/skills/build/tests/`; plugin version
bump to 0.6.21. No new dependencies.

### Non-goals

- No skills — `/s:preferences`, `/s:memory`, `/s:forget` are later epic
  members; this member ships only engine surface.
- No oracle change — the `oracle-personal-rung` member wires the personal store
  into ask-mikk's read ladder.
- No git-backing flow — the first-run `git init`/remote/push flow is the
  `memory-git-backing` member; this member only ensures `wiki_autocommit` works
  against a personal root (which it already does, unchanged).
- No embeddings, vector store, database, or external service; engine scripts
  stay stdlib-only (inherited epic/constitution bindings).

## Implementation

- **`memory_dir` resolution mirrors `wiki_base_dir`, but always yields a path.**
  A new `sc.memory_store_dir(root)` resolves the layered config, reads
  `memory_dir`, `~`-expands it, validates it is a non-empty string expanding to
  an absolute path (raising `ConfigError` naming `memory_dir` otherwise), and
  returns `<memory_dir>/wiki` — the store directory, analogous to
  `wiki_dir(ws_root)`. Unlike `wiki_base` (None when undeclared), an undeclared
  `memory_dir` defaults to `~/.shipd-memory`, so the helper never returns None.
  Rejected: reusing `wiki_dir` with a synthetic root (its content-dir
  indirection would nest the store at `<memory_dir>/.shipd/wiki`, not the epic's
  `~/.shipd-memory/wiki/`).

- **`--personal` selects the store; it does not fork the verbs.** A small
  resolver in `spec_status.py` — `_wiki_store(root, personal)` returning either
  `sc.wiki_dir(_resolve_workspace(root))` (default) or `sc.memory_store_dir(root)`
  (personal) — is the single branch point. `cmd_wiki_init`, `cmd_wiki_show`,
  `cmd_cat` (wiki kind), and `cmd_wiki_remove` call it; the rest of each verb is
  unchanged. Rejected: dedicated `memory-init`/`memory-show`/`memory-remove`
  verbs (duplicate the verb bodies for a store selection). With `--personal`,
  `wiki-show` prints `base: none` — base layering is a workspace-store concept
  the personal store does not participate in.

- **`wiki-remove` reuses `emit_wiki`'s backup→lint→restore contract in
  reverse.** `cmd_wiki_remove(root, slug, personal)` resolves the store, refuses
  a reserved slug (`index`/`log`/`queue`/`schema`/`sources`) and a missing
  `wiki/<slug>.md` up front (writing nothing), then backs up `wiki/<slug>.md`,
  `index.md`, and `log.md`; deletes the page; removes the page's `index.md`
  catalog entry; appends `## [YYYY-MM-DD] remove | <slug>` to `log.md`; runs the
  whole-store wiki lint (`spec_lint.lint_wiki`, the same entry point
  `emit_wiki` uses); and on any finding restores all backed-up files
  byte-for-byte, exits non-zero, and names the reason — for a stranded inbound
  `[[slug]]` link, naming the linking page. On a clean lint it calls
  `sc.wiki_autocommit(store, [page, index, log], "shipd-wiki: remove <slug>")`, a
  no-op outside git and never fatal on commit failure. Rejected: expressing
  removal through `spec_emit.py wiki` staging (staging encodes file presence,
  not absence).

- **Store grammar and auto-commit are untouched.** The personal store is a wiki
  store at a different root; `index.md`, `log.md`, `wiki/<slug>.md`, the wiki
  lint, and `wiki_autocommit` all apply as-is. `wiki_autocommit(store_dir, …)`
  already no-ops outside a git work tree and commits scoped files inside one, so
  a git-backed `~/.shipd-memory` is handled with no new code.

- **Tests (constitution: every engine change carries tests).** Cover
  `memory_store_dir` resolution (declared/undeclared default/malformed), the
  `--personal` targeting of `wiki-init`/`wiki-show`/`cat wiki`, and
  `wiki-remove` across its scenarios (success updates page+index+log; stranded
  inbound link blocks and restores; missing page and reserved slug refused;
  git-store commit scoped to touched files; non-git store removal without a
  commit).

Risk: a `--personal` verb run before the store exists must fail cleanly (like
`wiki-show`'s existing "no wiki store" error), not create a partial store —
guarded by resolving-then-checking `os.path.isdir` before any write, exactly as
the workspace-store verbs already do.
