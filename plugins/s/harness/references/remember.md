# /s:remember — reference

The fuller protocol behind the remember command's workflow: the page
grammar, reconciliation, and the git-backing flow.

## The personal store

`--personal` resolves the store at `<memory_dir>/wiki` (default
`~/.shipd-memory/wiki`) by fixed path, bypassing workspace discovery. It is
a single durable store: `wiki-show --personal` always reports `base: none`,
there is no job/base split, and no promotion step exists.

`wiki-init --personal` scaffolds it once — an empty `index.md`, `queue.md`,
`log.md`, a seeded `schema.md`, and empty `wiki/` and `sources/` dirs. The
verb refuses an existing store, so call it only after `wiki-show
--personal` reported none.

## The `memory-<subject>` page grammar

A captured preference is an ordinary wiki page — indexed, lint-clean,
oracle-readable — distinguished only by its `memory-` slug prefix, which
the browse and remove commands filter on:

```
# memory-<subject>

<one-line preference statement>

- Origin: <invoking-repo>
- Captured: <YYYY-MM-DD>
```

`<subject>` is kebab-case (`memory-editor-choice`, `memory-diagram-style`).
`- Origin:` names the repo the capture ran from; `- Captured:` is the date.
The page installs at `<memory_dir>/wiki/wiki/memory-<subject>.md` with a
matching `- [[memory-<subject>]] — <summary>` index entry.

## Reconciliation

Retrieval is index- and grep-based over markdown — no embeddings, no vector
store, no search service. Read `cat wiki index --personal`, grep the
store's `wiki/` subdir for the candidate's subject terms, and read the
likely pages. Then classify:

- **add** — novel; a new page.
- **update** — an existing page covers the subject but the new information
  changes it. Re-emit the **whole** page; in-place edits stay forbidden.
- **skip** — an unchanged duplicate; stage nothing for it.

Extract only standing preferences — a tool choice, a tone, a formatting
convention. One-off task details and ambient session noise are not
memories.

## The staged write

```
python3 "$S/spec_emit.py" --root <repo-root> wiki --from "$staging" --personal
```

The staging dir mirrors the store: each touched
`wiki/memory-<subject>.md`, the **full** `index.md`, and the **full**
`log.md` with a fresh `## [YYYY-MM-DD] remember | <subject>` entry. The
emit backs up, installs, lints the whole store, and restores byte-for-byte
on any finding — a failed run installed nothing.

## Git backing

The engine's autocommit is a silent no-op until `<memory_dir>` is a git
repo, and the engine never pushes, pulls, or fetches. Every step here is a
typed round, offered and never automatic.

Detect first:

```
git -C <memory_dir> rev-parse --is-inside-work-tree
```

**Not a work tree.** Offer `git init <memory_dir>` and run it **before**
the staged emit, so the first captured page rides in the initial commit.
Initialize at `<memory_dir>`, not at `<memory_dir>/wiki` — the repo root
must be the store's parent for the autocommit's inside-work-tree check to
pass, and it keeps any co-located `~/.shipd-config.json` with the memory
tree. A decline skips the whole git-backing flow; the capture still
installs, just uncommitted.

Then, only on a typed confirmation and only where `gh` is on `PATH` and
authenticated (`gh auth status`), offer the remote and the push as **two
separate** rounds:

```
gh repo create shipd-memory --private
git -C <memory_dir> remote add origin <url>
git -C <memory_dir> push -u origin <branch>
```

**Already a work tree.** Skip the init. Where an `origin` exists and the
branch has commits not on it (`git -C <memory_dir> rev-list @{u}..HEAD` is
non-empty, or no upstream is set), offer a confirmed
`git -C <memory_dir> push`.

When `gh` is absent or the user declines, print those exact commands for
the user to run later. A failed create or push is non-fatal: report it,
name the manual command, and carry on — the local commit is the durable
outcome.
