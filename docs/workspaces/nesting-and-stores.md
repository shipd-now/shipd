<!-- doc-type: reference -->

# Nesting and external stores

[← Workspaces](../workspaces.md)

Two mechanisms relocate what a workspace holds. **Nesting** files one job
workspace beneath another, so the inner job inherits the outer one's
knowledge. **`store_root`** moves a repo's shipd artifacts out of that repo
and into an external store.

## Nesting job workspaces

A job workspace can nest inside a base workspace instead of standing alone.
File it directly beneath the base root. Every enclosing workspace's knowledge
then reaches it, and that base needs no `wiki_base`.

Say the base workspace is `~/workspaces/acme-base/`, an ordinary workspace
that [getting started](getting-started.md) creates. The nested job is a folder
**inside** it, named for the job:

```sh
mkdir -p ~/workspaces/acme-base/documents-linking
shipd workspace init ~/workspaces/acme-base/documents-linking --nested --git
```

```
~/workspaces/acme-base/           ← the base workspace repo
  .shipd/wiki/                    ← knowledge every job beneath it inherits
  documents-linking/              ← THE NESTED JOB'S WORKSPACE REPO
    .shipd-config.json            ← this job's own manifest
    .shipd/wiki/                  ← this job's own store — every write lands here
    documents/  tasks/            ← this job's member repos, machine-local
```

### `--nested`

The flag is mandatory. The bare verb refuses to create a workspace under an
already-discoverable one, so nesting stays a deliberate choice rather than an
accident. The verb still refuses when the target itself declares `workspace`.

### What inherits across the chain

Resolution runs nearest-first: a nearer answer always shadows a farther one.

- **Wiki reads** — a page slug resolves to the nearest chain store holding it.
  `index.md` and `queue.md` aggregate every chain store's file, so a catalogue
  never hides an inherited page or question.
- **Initiative briefs** — `cat initiative`, the linter's `Initiative:` check,
  and the dashboard's initiative status all resolve to the nearest chain
  member holding the brief.
- **The project registry** — `projects` (and its `focus`) falls through to the
  nearest chain member that declares one. The engine never merges a registry
  across levels, so a nested job that declares its own `projects` shadows the
  base's outright. `workspace-show` names the registry's provenance whenever
  it comes from an enclosing member.

### What stays nearest-only

- **Every write** — wiki store scaffolding, `/s:teach`, queued oracle
  questions, and initiative emission land in the nested job's own store, never
  an enclosing one. `workspace-show`, `wiki-show`, and `config-show` print the
  resolved chain, so you can inspect the write target before you rely on it.
- **Sync and member materialization** — `workspace-sync` reads only the nested
  job's own manifest. It never materializes the base workspace's members.

### `wiki_base` alongside nesting

`wiki_base` (see [getting started](getting-started.md)) still earns its place
for a durable base **outside** the chain — a shared org-wide wiki no job sits
beneath. A base that nesting already reaches is redundant. The engine treats a
`wiki_base` resolving to any chain store's directory as undeclared, and
searches that directory once rather than twice.

## Storing artifacts outside the member repos

By default a repo's shipd artifacts live inside it, at `<repo>/.shipd/`. The
optional **`store_root`** key relocates them into an external store — the
workspace repo itself, or a dedicated artifacts repo. Plans, specs, and
completed changes then sit in one place, rather than scattered across member
repos you may not own.

Declare the key **once, at the workspace root**. Every member repo beneath it
inherits the key through the ordinary nearest-wins merge, so no member repo
needs a config of its own.

```json
{
  "workspace": { "...": "..." },
  "store_root": "shipd-store"
}
```

```
~/workspaces/documents-linking/
  .shipd-config.json          ← declares store_root once
  shipd-store/                ← the external store (tracked with the workspace)
    documents/                ← one folder per member repo …
      verified/  planned/  completed/  research/
    tasks/
    incentives/
  documents/  tasks/  incentives/    ← the member repos, artifact-free
```

The per-repo folder **is** the content directory: it holds `verified/`,
`planned/`, `completed/`, and `research/` directly. The `dir` key renames an
*in-repo* `.shipd/`, and does not apply to an external store.

### Where the store lands

`~` expands, and an absolute value stands as-is. A relative value resolves
against the directory of the config file that declared it — not the current
repo. So `"store_root": "shipd-store"` in
`~/workspaces/documents-linking/.shipd-config.json` always means
`~/workspaces/documents-linking/shipd-store`, however deep the repo resolving
it sits. The committed workspace config therefore resolves the same on every
machine.

### A dedicated artifacts repo

A dedicated artifacts repo is the same key pointed elsewhere. Clone the repo
anywhere, then declare it — in the workspace config, or in
`~/.shipd-config.json` to cover every repo on the machine:

```json
{ "store_root": "~/projects/acme-shipd-artifacts" }
```

### Per-repo folder naming

The folder name comes from the repo's git identity: the basename of the *main
checkout's* directory. The engine probes it locally with
`git rev-parse --git-common-dir`. A change developed in
`<repo>/.worktrees/<change>` therefore resolves the **same** store folder as
the main checkout. Outside a git repo the folder falls back to the resolution
root's own basename.

### Auto-commit

When the store is itself a git work tree, engine writes into it commit
locally, scoped to exactly the files written. Four writers commit: change
installs, gate plan rewrites, `set-status`, and merge or archive.

This mirrors the wiki convention (see
[getting started](getting-started.md)). The commits stay purely local: never a
push, a pull, or a fetch. Outside a work tree the commit is a silent no-op. A
failed commit prints one warning line, and never fails the verb.

Push and pull the store repo yourself, exactly as you do the workspace repo.
Writes to an **in-repo** `.shipd/` never auto-commit — those stay the change's
own pull request.

### Check what resolved

Check the resolution before you rely on it. A mis-declared `store_root`
silently resolves a fresh, empty store rather than failing:

```sh
shipd config
```

The verb prints a `store:` line carrying the resolved absolute content
directory whenever the config declares the key.

### Known limitations

- **The worktree guard and the statusline do not see an external store.**
  `worktree.sh remove`'s check for work in progress and `statusline.sh` read
  in-repo `planned/` content only. With an external store they report nothing
  to protect or display — the same documented blind spot a renamed content
  directory has today.
- **Basename collisions are yours to avoid.** Two repos whose main checkout
  directories share a name resolve the *same* store folder. Nothing detects
  it. Give one of them a distinct directory name, or a store of its own.
- **CI sees no artifacts.** An opted-in repo's checkout carries no `.shipd/`,
  so an in-repo CI step for the spec lint has nothing to lint.
- **shipd itself does not opt in.** This repo keeps its artifacts in-repo, so
  every change's specs and implementation still travel in one pull request.
