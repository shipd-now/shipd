---
name: remember
description: >-
  Capture mikk's durable memories into the personal memory store: extract
  memory candidates from the invocation argument or the session, reconcile
  each against existing `memory-*` pages, confirm the proposed set in a typed
  round, and install through one staged `spec_emit.py wiki --personal` call. Use
  when asked to "remember that I prefer …", "capture a preference", "save this
  to memory", "note that …", or "/s:remember". Trigger phrases:
  "remember I prefer", "capture a preference", "save to memory", "note that",
  "/s:remember".
---

# /s:remember — user memories → personal memory pages

You are the **write path into the personal memory store**. Your job is to turn a
stated (or session-observed) user preference — "mikk prefers vim / ASCII
diagrams / a terse tone" — into `memory-<subject>` wiki pages in the personal
store that the ask-mikk oracle already consults first. You are the personal-store
counterpart to `/s:teach`: teach fills the *workspace* wiki, and you fill the
*personal* memory store.

**You never write into the store by editing its files in place.** Every store
mutation goes through one `spec_emit.py wiki --from <staging> --personal` call
over a throwaway staging directory, so an interrupted or invalid run never
corrupts the store — the emit backs up the affected files, installs the staged
subset, runs the whole-store wiki lint, and restores byte-for-byte on any
finding.

**The personal store is a single durable store — there is no base/job split and
no promotion step.** Unlike `/s:teach`, every store verb here carries
`--personal`, which resolves the personal memory store at `<memory_dir>/wiki`
(default `~/.shipd-memory/wiki`) by fixed path, bypassing workspace discovery. A
personal store participates in no base layering.

**Announce the version first.** Read the running plugin version from
`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and include `shipd:remember
v<version>` in your first user-visible status sentence (e.g. "shipd:remember
v0.6.26 — capturing your preference into the personal memory store"), so the user
can always see which plugin snapshot the session is running.

Throughout, the engine scripts are:

- **STATUS_CLI** — `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py`
  (all reads).
- **EMIT_CLI** — `${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_emit.py`
  (the one store write path).

Run every engine verb with `python3 <CLI> --root <repo-root> <verb …> --personal`,
where `<repo-root>` is the invoking repo (its path is recorded as a captured
page's `- Origin:` provenance).

An **optional invocation argument** carries the preference to capture (e.g.
"prefers vim over vscode", or a subject keyword). When present, extract candidates
from it; when absent, extract candidates from the session (see the flow below).

## 1. Resolve the personal store

Resolve the personal memory store and its health first:

```
python3 STATUS_CLI --root <repo-root> wiki-show --personal
```

`wiki-show --personal` resolves the personal store at `<memory_dir>/wiki` by
fixed path and prints its root, page count, coverage, and last log entry (its
`base:` line is always `none` — the personal store participates in no layering).
Branch on the outcome:

- **No store** — `wiki-show --personal` fails naming the missing store. Scaffold
  it once with `python3 STATUS_CLI --root <repo-root> wiki-init --personal`. The
  verb refuses an existing store, so this call is safe to make only when
  `wiki-show --personal` reported no store. After scaffolding, the store holds an
  empty `index.md`, `queue.md`, `log.md`, seeded `schema.md`, and empty `wiki/`
  and `sources/` directories.
- **Store present** — proceed to the flow.

Commits ride the engine's existing `wiki_autocommit`, a silent no-op until the
personal store is a git repo. This skill adds a **git-backing flow** (step 6)
that — in typed rounds, never through the engine — offers to `git init` the store,
wire a private `shipd-memory` remote via `gh`, and push, so the local commits become
a synced, portable history. The engine itself still never pushes, pulls, or
fetches.

The personal repo MAY also hold a copy of `~/.shipd-config.json` (for example,
symlinked into `<memory_dir>`) as a user convention, so a `git clone` carries the
user's build settings alongside their memory. This is documentation only — **no
engine reads, writes, or syncs settings**; the git-backing flow versions the
memory tree, not configuration.

## The `memory-<subject>` page grammar

A captured preference is an **ordinary wiki page** — indexed, lint-clean, and
oracle-readable — distinguished only by the `memory-` slug prefix that the
browse/forget members filter on. Each page has this shape:

```
# memory-<subject>

<one-line preference statement>

- Origin: <invoking-repo>
- Captured: <YYYY-MM-DD>
```

- **Line 1** is the title `# memory-<subject>`, with a kebab-case `<subject>`
  (e.g. `memory-editor-choice`, `memory-diagram-style`).
- Then **one line** stating the preference (e.g. "Mikk prefers vim over VS Code
  for editing.").
- Then a **provenance block**: `- Origin:` naming the repo the capture was
  invoked from, and `- Captured:` the capture date (`YYYY-MM-DD`).

The page lives at `<memory_dir>/wiki/wiki/memory-<subject>.md` after install and
carries a matching `- [[memory-<subject>]] — <summary>` entry in the store's
`index.md`.

## 2. Extract preference candidates

Extract the preferences to capture:

- **From the invocation argument** when present — the argument carries the
  preference the user wants remembered (e.g. "prefers vim over vscode", "always
  use ASCII diagrams, never mermaid"). Distill it into one or more discrete
  candidates, each a single preference with a kebab-case `<subject>` slug.
- **From the session** when no argument is given — surface the durable
  preferences the user expressed in this session (e.g. a stated tone, a tool
  choice, a formatting convention). Extract only clear, standing preferences,
  not one-off task details or ambient noise; the confirm round (step 4) is where
  the user prunes what you propose.

## 3. Reconcile against existing `memory-*` pages

For each candidate, reconcile it against what the personal store already records.
Read the index and grep the store's pages — **read only, never edit**:

```
python3 STATUS_CLI --root <repo-root> cat wiki index --personal
```

Then read-only `grep` the personal store's `wiki/` directory (the store root
`wiki-show --personal` printed, under its `wiki/` subdir) for the candidate's
subject terms, and read candidate pages the index names as relevant with
`python3 STATUS_CLI --root <repo-root> cat wiki <slug> --personal`. Retrieval is
index- and grep-based over markdown — **no embeddings, no vector store, no search
service.**

Classify each candidate:

- **add** — a novel preference the store does not record yet → a new
  `memory-<subject>` page.
- **update** — a preference whose statement an existing `memory-<subject>` page
  already covers but the new information changes → **re-emit that page** (an
  update re-emits the whole page; in-place edits stay forbidden).
- **skip** — a duplicate the store already records unchanged → touch nothing.

## 4. Confirm the proposed set (typed round, no AskUserQuestion)

Because the capture writes durable personal memory — and, for session
extraction, memory the user did not state verbatim — **present the proposed set
before writing anything** and proceed only on the user's typed go-ahead. List
each candidate with:

- its **classification** (add / update / skip),
- its **target slug** (`memory-<subject>`), and
- the one-line statement that would be written.

Use a **plain-text typed round** — ask the user to confirm, prune, or amend the
set, and wait for a typed reply. **Do not use AskUserQuestion**; this skill's
confirmation is a typed round, so it does not join the question-rejection-recovery
roster. Write nothing until the user gives a typed go-ahead. If the user prunes
or amends, revise the set and reflect the change back before installing.

## 5. Install — the one staged write path

Author the touched store subset in a throwaway staging directory and install it
with a single emit call. **Never edit store files in place.** Skipped duplicates
contribute nothing to the staging dir.

1. Create a staging dir: `staging=$(mktemp -d)`.
2. Write the **touched subset** into it, mirroring the store layout:
   - `wiki/memory-<subject>.md` — each added or updated page (per the grammar
     above). An update re-emits the whole page; there is no in-place edit.
   - `index.md` — the **full** index catalogue: the existing entries (read from
     `cat wiki index --personal`) plus one `- [[memory-<subject>]] — <summary>`
     entry per touched page, so the entry set and the store's page set match
     exactly after install.
   - `log.md` — the **full** log with a fresh dated entry appended describing the
     run: `## [YYYY-MM-DD] remember | <subject>` (naming the captured
     subjects).
3. Install the whole staged subset with one call:

   ```
   python3 EMIT_CLI --root <repo-root> wiki --from "$staging" --personal
   ```

   The emit installs into the personal store at `<memory_dir>/wiki` (resolved by
   fixed path). It backs up the affected files, installs the staged set, runs the
   whole-store wiki lint, and — on any finding — restores every affected file
   byte-for-byte and exits non-zero, so an invalid store state never lands. If it
   fails validation, read the findings, fix the staged files, and re-run; nothing
   was installed.

Then report to the user: the pages added, the pages updated, the candidates
skipped as duplicates, and the personal store the run wrote to.

## 6. Git-backing flow (typed rounds, skill-driven)

The personal store's local commits ride the engine's `wiki_autocommit`, but only
once `<memory_dir>` is a git repo — and nothing turns those local commits into a
synced, portable history. This flow, driven by the skill (never the engine) and
confirmed in **typed rounds** (plain-text prompts, **no AskUserQuestion**), sets
up and syncs that git backing around the capture install.

**Detect first.** After resolving the store (step 1), detect whether the
personal store's git root — `<memory_dir>`, the parent of the `<memory_dir>/wiki`
store (default `~/.shipd-memory`) — is inside a git work tree:

```
git -C <memory_dir> rev-parse --is-inside-work-tree
```

A `true` on stdout (exit 0) means the store is already git-backed; a non-zero
exit means it is not yet a repo. Branch on this outcome.

### First run — `<memory_dir>` is not a git work tree

Offer, in a typed round, to `git init` the store's git root, and **run it before
the staged emit** (step 5) so the capture's `wiki_autocommit` picks up the first
captured page in the initial commit:

```
git init <memory_dir>
```

Initialize at `<memory_dir>` (not at `<memory_dir>/wiki`) so the repo root is the
parent of the store — this is what makes `wiki_autocommit`'s inside-work-tree
check pass for `<memory_dir>/wiki`, and it keeps the memory tree together with any
co-located `~/.shipd-config.json`. Because the init must precede the emit for the
first page to be committed, offer and run it **before** step 5, then proceed with
the staged emit as usual. If the user declines the `git init`, skip the whole
git-backing flow and let the capture install locally uncommitted (as before a
repo exists).

**Then wire a remote and push (confirmed, `gh`-gated).** After the capture has
committed the first page locally, offer — only on the user's typed confirmation
and only where `gh` is on `PATH` and authenticated (`gh auth status`) — to create
and wire a private personal remote, then offer a confirmed push:

```
gh repo create shipd-memory --private
git -C <memory_dir> remote add origin <url>   # the URL gh printed
git -C <memory_dir> push -u origin <branch>   # <branch> is the current branch
```

The repo name `shipd-memory` matches the default `~/.shipd-memory` store. The remote
wiring and the push are two separate typed offers — the user can accept the
remote but decline (or defer) the push. When `gh` is **absent** (not on `PATH` or
not authenticated) or the user **declines** the remote, complete the local
`git init` only and **print the exact manual commands** for the user to run
later:

```
gh repo create shipd-memory --private
git -C <memory_dir> remote add origin <url>
git -C <memory_dir> push -u origin <branch>
```

A failed `gh repo create` or `git push` (no auth, rejected non-fast-forward,
network error) is **non-fatal**: report the failure and the manual command, and
carry on — the capture is already committed locally, and that local commit is the
durable outcome. The remote is best-effort, mirroring `wiki_autocommit`'s own
never-fail-the-write stance.

### Already git-backed — `<memory_dir>` is a git work tree

Skip the `git init`: the capture's emit autocommits locally through
`wiki_autocommit` exactly as today. Then, when an `origin` remote exists and the
store has commits not yet on it — the upstream is behind (`git -C <memory_dir>
rev-list @{u}..HEAD` is non-empty) or no upstream is set for the branch — offer a
confirmed push:

```
git -C <memory_dir> push          # or `git -C <memory_dir> push -u origin <branch>` when no upstream is set
```

so the remote stays in sync over time. As on the first run, the push is offered,
not automatic, and a failed push is non-fatal (reported, local commit stands).

**Every git / `gh` / push step in this flow is a typed round — no
AskUserQuestion** — which keeps `/s:remember` off the
question-rejection-recovery roster. And **the engine never pushes, pulls, or
fetches**: its role is only the local `wiki_autocommit` commit on the emit write;
remote creation and every push are skill-driven and always confirmed here.
