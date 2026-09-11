<!-- doc-type: how-to -->

# Practical examples: multi-workspace repos

[← Workspaces](../workspaces.md)

One repo can carry several workspaces. A team clones it once, and each
engineer syncs only the jobs they work on. The rest cost a few KB of manifest
and wiki on disk, and materialize nothing.

Two shapes support that. Choose between them by whether the jobs share
knowledge. Sibling workspaces in a plain repo (**Shape A**) keep every job's
wiki to itself. A base workspace with nested jobs (**Shape B**) gives every
job an inherited base wiki.

## Shape A — sibling workspaces in a plain repo

The repo root declares no workspace. It is a plain container, and each job is
an ordinary workspace directory beneath it, created exactly as
[Getting started](getting-started.md) creates a standalone one.

```
~/workspaces/company/             ← A PLAIN GIT REPO — its root declares
                                    no workspace, it only holds the two below
  workspace-documents/            ← WORKSPACE — the documents-linking job
    .shipd-config.json            ← this job's manifest                       (tracked)
    .gitignore                    ← this job's members block, engine-managed  (tracked)
    .shipd/
      wiki/                       ← this job's knowledge store                (tracked)
      initiatives/  projects/     ← this job's goals & context                (tracked)
    documents/  tasks/            ← this job's member repos                   (ignored)
  ws-tasks-management/            ← WORKSPACE — an unrelated job
    .shipd-config.json            ← its own manifest                          (tracked)
    .gitignore                    ← its own members block                     (tracked)
    .shipd/wiki/                  ← its own store — nothing is shared         (tracked)
    tasks/  incentives/           ← its own member repos                      (ignored)
```

Discovery is nearest-ancestor. A session inside `workspace-documents/` never
sees `ws-tasks-management/`, so siblings neither interfere nor inherit.

Create (or clone) the container repo, then initialize each workspace in it:

```sh
mkdir -p ~/workspaces/company/workspace-documents
mkdir -p ~/workspaces/company/ws-tasks-management
cd ~/workspaces/company && git init
shipd workspace init ~/workspaces/company/workspace-documents
shipd workspace init ~/workspaces/company/ws-tasks-management
```

This shape takes no `--nested`: nothing is discoverable above either target.
Fill each manifest as [Getting started](getting-started.md) shows, then run
`shipd wiki init` and `shipd workspace sync` inside each workspace.

`--git` is optional here, and it never nests a repo inside the container. The
verb skips `git init` when the target already sits inside a git work tree, and
seeds only that workspace's own members `.gitignore` block. A plain `init`
gets the block on the first `shipd workspace sync --write-gitignore`, so
either route ends in the same tracked state.

## Shape B — a base workspace with nested jobs

Here the repo root is a workspace, the base of
[Nesting and external stores](nesting-and-stores.md). Each job is a `--nested`
workspace filed directly beneath it.

```
~/workspaces/acme-base/           ← THE BASE WORKSPACE REPO — clone this
  .shipd-config.json              ← the base manifest                         (tracked)
  .shipd/wiki/                    ← knowledge every job below inherits        (tracked)
  documents-linking/              ← NESTED JOB WORKSPACE
    .shipd-config.json            ← this job's own manifest                   (tracked)
    .gitignore                    ← this job's members block                  (tracked)
    .shipd/wiki/                  ← this job's own store — writes land here   (tracked)
    documents/  tasks/            ← this job's member repos                   (ignored)
  billing-rollout/                ← ANOTHER NESTED JOB WORKSPACE
    .shipd-config.json            ← its own manifest                          (tracked)
    .shipd/wiki/                  ← its own store, plus the base's by         (tracked)
                                    inheritance
    billing/  tasks/              ← its own member repos                      (ignored)
```

```sh
mkdir -p ~/workspaces/acme-base/documents-linking
mkdir -p ~/workspaces/acme-base/billing-rollout
shipd workspace init ~/workspaces/acme-base/documents-linking --nested --git
shipd workspace init ~/workspaces/acme-base/billing-rollout --nested --git
```

`shipd workspace init` requires `--nested` here, and deliberately so. The
bare verb refuses to create a workspace under an already-discoverable one, so
no job nests by accident.

Inheritance is [Nesting and external stores](nesting-and-stores.md)'s,
unchanged. Reads fall through the chain nearest-first, so a job sees the
base's pages, initiatives, and project registry wherever it declares none of
its own. Every write lands in the nested job's own store, never the base's.
Teaching the base is its own deliberate act, run from the base workspace.

## What lives where

| | Shape A — siblings | Shape B — base + nested jobs |
|---|---|---|
| **Manifest** (`.shipd-config.json`) | one per workspace directory — tracked in the shared repo | one at the base plus one per job — tracked in the shared repo |
| **Wiki pages** (`.shipd/wiki/`) | one store per workspace, private to it — tracked | one store per job, plus the base's — tracked |
| **Oracle queue** (`.shipd/wiki/queue.md`) | per workspace; a question queued in one is invisible in the other — tracked | per job for writes, aggregating the base's questions on read — tracked |
| **Initiatives** (`.shipd/initiatives/`) | per workspace — tracked | per job, falling back to the base's brief — tracked |
| **Member repos** | inside each workspace, held out by its members block — machine-local | inside each job, held out by its members block — machine-local |
| **Inherited base wiki** | none — the siblings share nothing | the base's `.shipd/wiki/`, read nearest-first by every job — tracked |

## Using either shape

Clone the repo with plain `git clone`. The `/s:workspace clone` verb of
[Getting started](getting-started.md) bootstraps one workspace from a
repository URL, so it is the wrong front door for a repo holding several:

```sh
git clone git@github.com:acme/company-workspaces.git ~/workspaces/company
cd ~/workspaces/company/workspace-documents
shipd workspace sync
```

`cd` into the workspace you care about, and plan its materialization there.
`shipd workspace sync` only prints the plan, so run `/s:workspace sync` in a
Claude session to execute it. Sync reads only that workspace's own manifest.
The jobs you ignore stay unmaterialized, and cost nothing but their tracked
manifest and wiki.

Knowledge travels as [Sharing a workspace with a team](teams.md) describes:
`git pull` at the start of a session, `git push` at the end. The conflict
surfaces are the ones that page names. Wiki auto-commits land in the enclosing
work tree, which in both shapes is the one shared repo. Every session
therefore commits into the same local history.

## Pros and cons

| | Shape A — siblings | Shape B — base + nested jobs |
|---|---|---|
| **Pros** | strict isolation between jobs; the simplest mental model — every workspace reads like a standalone one that happens to share a repo | a base wiki every job inherits for free; nesting is an explicit `--nested` opt-in, never accidental |
| **Cons** | no shared knowledge — conventions common to every job are duplicated per workspace | one more level of indirection to reason about; base writes need their own discipline, since every write defaults to the job's store |

Pick **Shape A** when the jobs have nothing to say to each other. Pick
**Shape B** when they share conventions worth writing down once.

Neither shape is an access-control boundary. Git has no per-directory
permissions, so anyone who can clone the repo reads every workspace in it.
When a job's manifest or knowledge must stay invisible to some of the people
cloning, give that job its own repo. **Separate repos, not directories, are
the isolation boundary.**
