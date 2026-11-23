<!-- doc-type: how-to -->

# Nesting job workspaces

[← Workspaces](../workspaces.md)

A job workspace can nest inside a base workspace instead of standing alone.
File it directly beneath the base root. Every enclosing workspace's knowledge
then reaches it, and that base needs no `wiki_base`.

## When to use it

Nest a job workspace when the job must inherit a base workspace's knowledge.
A team that shares one base uses the nested team layout that
[sharing a workspace with a team](teams.md) describes. A durable base outside
the chain uses `wiki_base` instead, as [`wiki_base` alongside
nesting](#wiki_base-alongside-nesting) explains.

## How to run it

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

The `--nested` flag is mandatory. The bare verb refuses to create a workspace
under an already-discoverable one, so nesting stays a deliberate choice rather
than an accident. The verb still refuses when the target itself declares
`workspace`.

## Reference

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

- **Every write** — wiki store scaffolding, [`/s:teach`](../wiki.md), queued oracle
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
