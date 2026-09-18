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
mkdir -p ~/workspaces/acme-base/myapp
shipd workspace init ~/workspaces/acme-base/myapp --nested --git
```

```
~/workspaces/acme-base/           ← the base workspace repo
  .shipd/wiki/                    ← knowledge every job beneath it inherits
  myapp/                          ← THE NESTED JOB'S WORKSPACE REPO
    .shipd-config.json            ← this job's own manifest
    .shipd/wiki/                  ← this job's own store — every write lands here
    api/  web/                    ← this job's member repos, machine-local
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

The tree below assumes a registry declaring project `acme` with members at
`acme/api`, `acme/web`, and `acme/mobile`. See
[per-repo folder naming](#per-repo-folder-naming) for how the store folder
derives from those paths:

```
~/workspaces/myapp/
  .shipd-config.json          ← declares the project registry and store_root
  shipd-store/                ← the external store (tracked with the workspace)
    acme/                     ← the registry project's own path segment …
      api/                    ← … then each member's manifest path, `acme/api`
        verified/  planned/  completed/  research/
      web/                    ← `acme/web`
      mobile/                 ← `acme/mobile`
  acme/
    api/  web/  mobile/       ← the member repos, at their declared `acme/*`
                               ←   manifest paths — artifact-free
```

The per-repo folder **is** the content directory: it holds `verified/`,
`planned/`, `completed/`, and `research/` directly. The `dir` key renames an
*in-repo* `.shipd/`, and does not apply to an external store.

### Where the store lands

`~` expands, and an absolute value stands as-is. A relative value resolves
against the directory of the config file that declared it — not the current
repo. So `"store_root": "shipd-store"` in
`~/workspaces/myapp/.shipd-config.json` always means
`~/workspaces/myapp/shipd-store`, however deep the repo resolving
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

Where a project registry declares the repo, the folder is that member's
**manifest path** — `acme/api`, not the bare basename `api`. The store then
mirrors the workspace's own `project/repo` structure.

The engine matches the resolution root against the registry the same way it
resolves project ownership: equality-or-containment, with the most specific
entry winning. The machine-local member map matches too, so a repo relocated
on this machine still resolves its declaring member's manifest path. A
worktree lying under a member's own checkout, at
`<repo>/.worktrees/<change>`, resolves identically to the main checkout,
because it lies inside that same declared entry.

Where no registry declares the repo, the folder falls back to the basename
of the *main checkout's* directory. That covers an undeclared repository, no
discoverable registry, or an unloadable one. The engine probes the basename
locally with `git rev-parse --git-common-dir`, so a change developed in
`<repo>/.worktrees/<change>` still resolves the **same** store folder as the
main checkout. Outside a git repo the folder falls back to the resolution
root's own basename.

The engine mandates the derivation; no key chooses the old, flat layout. It
never migrates a store already populated under that layout — see
[check what resolved](#check-what-resolved).

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

```sh
shipd doctor
```

The preflight's `store` line reports the same resolution: `ok`, naming the
in-repo or resolved external content directory. It `warn`s when a directory
still exists at the *previous* flat-layout path while the resolved one does
not, naming both paths and a `git mv` remedy. The check is report-only: it
never moves, creates, or deletes anything on your behalf.

### Known limitations

- **The worktree guard and the statusline do not see an external store.**
  `worktree.sh remove`'s check for work in progress and `statusline.sh` read
  in-repo `planned/` content only. With an external store they report nothing
  to protect or display — the same documented blind spot a renamed content
  directory has today.
- **Basename collisions are yours to avoid, for an undeclared repo.** Two
  such repos sharing a checkout name resolve one store folder — undetected.
  A declared registry member never collides this way: its manifest path
  already disambiguates `acme/dittor` from `partner/dittor`. Give an
  undeclared repo a distinct directory name, or a store of its own.
- **CI sees no artifacts.** An opted-in repo's checkout carries no `.shipd/`,
  so an in-repo CI step for the spec lint has nothing to lint.
- **shipd itself does not opt in.** This repo keeps its artifacts in-repo, so
  every change's specs and implementation still travel in one pull request.
