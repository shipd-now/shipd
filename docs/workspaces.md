<!-- doc-type: concept -->

# Workspaces

A **workspace** is a git repo you clone to stand up a whole *job to be done*.
A job is one cross-repo feature that touches several of your projects. The
workspace repo carries the **manifest** and the job's **wiki**. The manifest
names which member repos belong to the job, where to clone them from, and
which project is the focus. The member repos themselves materialize beside
them, and the workspace repo never tracks them.

```
~/workspaces/myapp/               ← THE WORKSPACE REPO — this folder is what
                                    you clone, commit, and push
  .shipd-config.json              ← manifest: focus + projects + clone urls  (tracked)
  .gitignore                      ← members block, engine-managed            (tracked)
  .shipd/
    wiki/                         ← the job's knowledge store                (tracked)
    initiatives/  projects/       ← goals & per-project context              (tracked)
  api/  web/  mobile/             ← member repos, machine-local              (ignored)
```

One folder per job, all of them under a `~/workspaces/` parent. The leaf
carries the job's name (`myapp`), never a member repo's name. That
keeps it distinct from the `api/` checkout materialized inside it.

Everything marked `(tracked)` travels with `git clone`. The sync ladder
rebuilds everything marked `(ignored)` per machine. It prefers worktrees or
reference-clones of repos you already have locally, and clones in full only on
a fresh machine.

## The guide

**Getting started** — machine setup, creating a job workspace, checking it
into git, loading it on another machine, and the day-to-day verbs.

```sh
shipd workspace init myapp --git
```

[Details →](workspaces/getting-started.md)

**The member map and discovery** — mapping a member to a checkout you already
have, and resolving the workspace from outside it.

```sh
shipd workspace   # repo: shipd [mapped -> /Users/you/projects/shipd]
```

[Details →](workspaces/member-map.md)

**Nesting and external stores** — filing a job workspace beneath a base one so
it inherits the base's knowledge, and relocating artifacts with `store_root`.

```sh
shipd workspace init ~/workspaces/acme-base/myapp --nested --git
```

[Details →](workspaces/nesting-and-stores.md)

**Sharing a workspace with a team** — several engineers on one workspace repo,
what travels between them, the hooks consent gate, and conflict surfaces.

```sh
git pull   # at the start of a session
git push   # at the end of it
```

[Details →](workspaces/teams.md)

**Headless consumers** — the minimal footprint a CI job, bot, or cloud agent
needs to read a workspace without members, git, or machine config.

```sh
python3 <plugin>/skills/build/scripts/spec_status.py --root /tmp/ws workspace-show
```

[Details →](workspaces/headless.md)

**Practical examples: multi-workspace repos** — the two shapes for carrying
several workspaces in one repo, with layout trees, storage tables, and
trade-offs.

```sh
git clone git@github.com:acme/company-workspaces.git ~/workspaces/company
cd ~/workspaces/company/workspace-myapp && shipd workspace sync
```

[Details →](workspaces/multi-workspace-repos.md)
