# Nesting and external stores

[← Workspaces](../workspaces.md)

## Nesting job workspaces

A job workspace can nest inside a base workspace instead of standing alone —
file it directly beneath the base root and every enclosing workspace's
knowledge is inherited automatically, no `wiki_base` needed for that base:

Say the base workspace is `~/workspaces/acme-base/` — an ordinary workspace
created exactly as
[Create a job workspace](getting-started.md#create-a-job-workspace) creates
one. The nested job is a folder **inside** it, named for the job:

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

`--nested` is required: the bare verb refuses to create a workspace under an
already-discoverable one, so nesting is always a deliberate choice, never an
accident. It still refuses when the target itself already declares
`workspace`.

**What inherits across the chain** (nearest-first — a nearer answer always
shadows a farther one):

- **Wiki reads** — a page slug resolves to the nearest chain store holding
  it; `index.md` and `queue.md` aggregate every chain store's file so a
  catalogue never hides an inherited page or question.
- **Initiative briefs** — `cat initiative`, the linter's `Initiative:` check,
  and the dashboard's initiative status all resolve to the nearest chain
  member holding the brief.
- **The project registry** — `projects` (and its `focus`) falls through to
  the nearest chain member that declares one; a registry is never merged
  across levels, so a nested job that declares its own `projects` shadows the
  base's outright. `workspace-show` names the registry's provenance whenever
  it comes from an enclosing member.

**What stays nearest-only:**

- **Every write** — wiki store scaffolding, `/s:teach`, queued oracle
  questions, and initiative emission all land in the nested job's own store,
  never an enclosing one. `workspace-show`, `wiki-show`, and `config-show`
  print the resolved chain, so the write target is always inspectable before
  you rely on it.
- **Sync / member materialization** — `workspace-sync` reads only the nested
  job's own manifest, so it never tries to materialize the base workspace's
  members.

[`wiki_base`](getting-started.md#one-time-machine-setup) is still worth
declaring for a durable base that sits **outside** the chain — a shared
org-wide wiki no job is filed beneath. A base already reachable by nesting is
redundant: `wiki_base` resolving to any chain store's directory is treated as
undeclared, so it is searched once, not twice.

## Storing artifacts outside the member repos

By default a repo's shipd artifacts live inside it, at `<repo>/.shipd/`. The
optional **`store_root`** key relocates them into an external store instead —
the workspace repo itself, or a dedicated artifacts repo — so plans, specs and
completed changes are centralized rather than scattered across member repos
you may not even own.

Declare it **once, at the workspace root**, and every member repo beneath it
inherits it through the ordinary nearest-wins per-key merge — no per-repo
config at all:

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
`planned/`, `completed/` and `research/` directly. The `dir` key (which renames
an *in-repo* `.shipd/`) does not apply to an external store.

**Where the store lands.** `~` expands, an absolute value is used as-is, and a
relative value resolves against the directory of the config file that declared
it — not the current repo. So `"store_root": "shipd-store"` in
`~/workspaces/documents-linking/.shipd-config.json` always means
`~/workspaces/documents-linking/shipd-store`, however deep the repo resolving it
sits, and the committed workspace config resolves the same on every machine.

**A dedicated artifacts repo** is the same key pointed elsewhere — clone the
artifacts repo anywhere and declare it, either in the workspace config or in
`~/.shipd-config.json` to cover every repo on the machine:

```json
{ "store_root": "~/projects/acme-shipd-artifacts" }
```

**Per-repo folder naming.** The folder name comes from the repo's git identity
— the basename of the *main checkout's* directory, probed locally with
`git rev-parse --git-common-dir` — so a change developed in
`<repo>/.worktrees/<change>` resolves the **same** store folder as the main
checkout. Outside a git repo the folder falls back to the resolution root's own
basename.

**Auto-commit.** When the store is itself a git work tree, engine writes into
it commit locally, scoped to exactly the files written — change installs, gate
plan rewrites, `set-status`, and merge/archive. This mirrors the wiki
convention ([Check it into git](getting-started.md#check-it-into-git)): purely
local, never a push/pull/fetch, a silent no-op outside a work tree, and a
failed commit is one warning line that never fails the verb. Push and pull the
store repo yourself, exactly as you do the workspace repo. Writes to an
**in-repo** `.shipd/` never auto-commit — those stay the change's own PR.

**Check what resolved** before relying on it — a mis-declared `store_root`
silently resolves a fresh, empty store rather than failing:

```sh
shipd config
```

It prints a `store:` line carrying the resolved absolute content directory
whenever the key is declared.

**Known limitations:**

- **The worktree guard and the statusline don't see an external store.**
  `worktree.sh remove`'s work-in-progress check and `statusline.sh` read
  in-repo `planned/` content only, so with an external store they report
  nothing to protect or display — the same documented blind spot a renamed
  content directory has today.
- **Basename collisions are yours to avoid.** Two repos whose main checkout
  directories share a name resolve the *same* store folder. Nothing detects
  it; give one of them a distinct directory name, or a store of its own.
- **CI sees no artifacts.** An opted-in repo's checkout carries no `.shipd/`,
  so an in-repo spec-lint CI step simply has nothing to lint.
- **shipd itself does not opt in.** This repo keeps its artifacts in-repo, so
  every change's specs and implementation still travel in one PR.
