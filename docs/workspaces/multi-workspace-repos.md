# Practical examples: multi-workspace repos

[← Workspaces](../workspaces.md)

One repo can carry several workspaces, so a team clones it **once** and each
engineer syncs only the jobs they actually work on — the rest cost a few KB of
manifest and wiki on disk and materialize nothing. Two shapes support that,
and the choice between them is whether the jobs should share knowledge:
sibling workspaces in a plain repo (**Shape A**) keep every job's wiki to
itself, while a base workspace holding nested jobs (**Shape B**) gives every
job an inherited base wiki.

## Shape A — sibling workspaces in a plain repo

The repo root declares **no** workspace: it is a plain container, and each job
is an ordinary workspace directory beneath it, created exactly as
[Create a job workspace](getting-started.md#create-a-job-workspace) creates a
standalone one.

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

Discovery is nearest-ancestor, so a session working inside
`workspace-documents/` resolves that workspace and never sees
`ws-tasks-management/` — siblings do not interfere, and neither inherits
anything from the other.

Create (or clone) the container repo, then initialize each workspace in it:

```sh
mkdir -p ~/workspaces/company/workspace-documents
mkdir -p ~/workspaces/company/ws-tasks-management
cd ~/workspaces/company && git init
shipd workspace init ~/workspaces/company/workspace-documents
shipd workspace init ~/workspaces/company/ws-tasks-management
```

No `--nested` in this shape: the container root declares no workspace, so
nothing is discoverable above either target and the bare verb is satisfied.
Fill each manifest as
[Create a job workspace](getting-started.md#create-a-job-workspace) shows,
then run `shipd wiki init` and `shipd workspace sync` from inside each
workspace.

`--git` is optional here and never nests a repo inside the container: the verb
skips `git init` when the target is already inside a git work tree and only
seeds that workspace's own members `.gitignore` block. A plain `init` gets the
block seeded anyway on the first `shipd workspace sync --write-gitignore`, so
either route ends in the same tracked state.

## Shape B — a base workspace with nested jobs

Here the repo root **is** a workspace — the base of
[Nesting job workspaces](nesting-and-stores.md#nesting-job-workspaces) — and
each job is a `--nested` workspace filed directly beneath it.

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

`--nested` is required and deliberate: the bare verb refuses to create a
workspace under an already-discoverable one, so a job is never nested by
accident.

Inheritance is
[Nesting job workspaces](nesting-and-stores.md#nesting-job-workspaces)'s,
unchanged — reads fall through the chain nearest-first, so a job sees the
base's pages, initiatives, and project registry wherever it declares none of
its own, while **every write lands in the nested job's own store**, never the
base's. Teaching the base is therefore its own deliberate act, run from the
base workspace itself.

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
[Load it on another machine](getting-started.md#load-it-on-another-machine)
bootstraps *one* workspace from a repository URL, so it is the wrong front
door for a repo holding several:

```sh
git clone git@github.com:acme/company-workspaces.git ~/workspaces/company
cd ~/workspaces/company/workspace-documents
shipd workspace sync
```

`cd` into the workspace you care about and plan its materialization there —
`shipd workspace sync` only prints the plan, so run `/s:workspace sync` in a
Claude session to execute it. Sync reads only that workspace's own manifest,
so the jobs you ignore stay unmaterialized and cost nothing but their tracked
manifest and wiki.

Knowledge travels exactly as
[Sharing a workspace with a team](teams.md) describes: `git pull` at the start
of a session, `git push` at the end, with the same conflict surfaces that page
names. Wiki auto-commits land in the enclosing work tree, which in both shapes
is the one shared repo — so a session in any workspace commits into the same
local history.

## Pros and cons

| | Shape A — siblings | Shape B — base + nested jobs |
|---|---|---|
| **Pros** | strict isolation between jobs; the simplest mental model — every workspace is a standalone one that happens to share a repo | a base wiki every job inherits for free; nesting is an explicit `--nested` opt-in, never accidental |
| **Cons** | no shared knowledge — conventions common to every job are duplicated per workspace | one more level of indirection to reason about; base writes need their own discipline, since every write defaults to the job's store |

Pick **Shape A** when the jobs have nothing to say to each other and you want
each one to read exactly like a standalone workspace; pick **Shape B** when
they share org- or team-wide conventions worth writing down once.

Neither shape is an access-control boundary. Git has no per-directory
permissions, so anyone who can clone the repo reads every workspace in it —
when a job's manifest or knowledge must stay invisible to some of the people
cloning, give that job its own repo. **Separate repos, not directories, are
the isolation boundary.**
