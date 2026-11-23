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

## When to use it

Use a workspace when one job touches several repos, and its knowledge must travel with it.

## How to run it

- `shipd workspace init myapp --git` creates a job workspace.
- `/s:workspace clone <url> <dir>` loads an existing workspace on this machine.
- `/s:workspace sync` materializes the members.
- `shipd workspace` prints the roster.

[Getting started](workspaces/getting-started.md) walks through each step.

## Reference

| part | what it covers | example |
|---|---|---|
| [Getting started](workspaces/getting-started.md) | Machine setup, creating a job workspace, checking it into git, loading it elsewhere, and the day-to-day verbs. | `shipd workspace init myapp --git` |
| [The member map and workspace discovery](workspaces/member-map.md) | Mapping a member to a checkout you already have, and resolving the workspace from outside it. | `shipd workspace` |
| [Nesting job workspaces](workspaces/nesting.md) | Filing a job workspace beneath a base one, so it inherits the base's knowledge. | `shipd workspace init ~/workspaces/acme-base/myapp --nested --git` |
| [External stores](workspaces/external-stores.md) | Relocating a repo's shipd artifacts into an external store with `store_root`. | [`shipd config`](customise.md) |
| [Sharing a workspace with a team](workspaces/teams.md) | Several engineers on one workspace repo, the nested team layout, the hooks consent gate, and conflict surfaces. | [`shipd doctor`](doctor.md) |
| [Headless consumers](workspaces/headless.md) | The minimal footprint a CI job, bot, or cloud agent needs to read a workspace. | `python3 <plugin>/skills/build/scripts/spec_status.py --root /tmp/ws workspace-show` |

| verb | what it does |
|---|---|
| `/s:workspace init` | Creates a workspace through the guided `workspace-init` flow. |
| `/s:workspace show` | Reports the workspace roster, read-only. |
| `/s:workspace clone <url> [dest]` | Clones the workspace repo with git, then runs the `sync` flow inside it. |
| `/s:workspace sync` | Materializes the members by running the `workspace-sync` plan. |
| `/s:workspace map` | Points unmapped members at checkouts this machine already has. |
| `/s:workspace team` | Builds a nested team workspace through the `workspace-team` wizard. |
| `shipd workspace` | Prints the workspace root, its projects, and initiatives. |
| `shipd workspace init` | Creates a workspace. |
| `shipd workspace sync` | Prints the plan to materialize the members, and touches no network. |
| `shipd workspace team` | Builds a nested team workspace interactively. |
