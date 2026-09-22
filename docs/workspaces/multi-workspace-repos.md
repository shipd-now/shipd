<!-- doc-type: how-to -->

# Practical examples: multi-workspace repos

[← Workspaces](../workspaces.md)

One repo can carry several team workspaces. A team clones it once, and each
engineer syncs only the team workspaces they use. The rest cost a few KB of
manifest and wiki on disk, and materialize nothing.

## The shape: a base workspace, nested team workspaces

The repo root is itself a workspace — the base of
[Nesting and external stores](nesting-and-stores.md). Each team gets a
`--nested` workspace directly beneath it. That nested workspace inherits the
base's wiki, initiatives, and project registry wherever it declares none of
its own.

```
~/workspaces/acme-base/           ← THE BASE WORKSPACE REPO — clone this
  .shipd-config.json              ← the base manifest                        (tracked)
  .shipd/wiki/                    ← knowledge every team below inherits      (tracked)
  myapp/                          ← NESTED TEAM WORKSPACE
    .shipd-config.json            ← this team's own manifest                 (tracked)
    .gitignore                    ← this team's members block                (tracked)
    .shipd/wiki/                  ← this team's own store — writes land here (tracked)
    api/  web/                    ← this team's member repos                 (ignored)
  billing-rollout/                ← ANOTHER NESTED TEAM WORKSPACE
    .shipd-config.json            ← its own manifest                        (tracked)
    .shipd/wiki/                  ← its own store, plus the base's by       (tracked)
                                     inheritance
    billing/  tasks/              ← its own member repos                    (ignored)
```

## What lives where

| | Base workspace | Each nested team workspace |
|---|---|---|
| **Manifest** (`.shipd-config.json`) | tracked, at the repo root | tracked, one per team folder |
| **Wiki pages** (`.shipd/wiki/`) | tracked — every team below inherits it on read | tracked — writes land here, never at the base |
| **Oracle queue** (`.shipd/wiki/queue.md`) | tracked — a question queued here is answerable only here | tracked — the team's own pending questions |
| **Initiatives** (`.shipd/initiatives/`) | tracked, falls back to it when a team declares none | tracked, shadows the base's when declared |
| **Member repos** | none — the base holds no members of its own | machine-local, held out by the team's members block |

## Setup: `shipd workspace team`

Build the layout with the guided wizard, run from inside the base workspace:

```sh
shipd workspace init ~/workspaces/acme-base --git
cd ~/workspaces/acme-base
shipd workspace team
```

`shipd workspace team` asks for one or more team names. For each team, it
asks for repo paths, clone URLs, and any checkout you already have on this
machine. It creates the team's folder, initializes a nested workspace,
declares the repos, and maps the checkouts you named. The wizard reaches the
network never — `shipd workspace sync` materializes members afterward, inside
the team workspace that needs them.

## Cloning and day-to-day use

Clone the shared repo with plain `git clone` — it holds several workspaces,
so the single-workspace `/s:workspace clone` verb is the wrong front door:

```sh
git clone git@github.com:acme/workspaces.git ~/workspaces/acme-base
cd ~/workspaces/acme-base/myapp
shipd workspace sync
```

`cd` into the team workspace you work in, and plan its materialization there.
`shipd workspace sync` only prints the plan, so run `/s:workspace sync` in a
Claude session to execute it. Sync reads only that team's own manifest. The
teams you ignore stay unmaterialized, and cost nothing but their tracked
manifest and wiki.

`shipd workspace` reports the team's roster of projects and initiatives.
`shipd board` reports delivery across every declared project's repos.

## What the shape costs

The base wiki accumulates knowledge only from writes made **at the base**. A
teammate teaching a page from inside `myapp/` writes it into `myapp`'s own
store, never the base's. Run `/s:teach` from the base workspace to grow the
knowledge every team inherits.

The oracle queue splits the same way. A question queued at the base is
answerable only from the base workspace, never from a nested team's own
session. Queue a question there when every team should see its answer.

## Isolation

Git has no per-directory permissions. Anyone who can clone the repo reads
every team workspace in it — the base wiki and every nested team's own store
alike. When a team's knowledge must stay invisible to some of the people who
clone the repo, give that team a workspace repository of its own.
**Separate repos, not directories, are the isolation boundary.**
