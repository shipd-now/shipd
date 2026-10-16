<!-- doc-type: how-to -->

# Episode 7: Workspaces 101

## Introduction

A feature that spans an API, a web app, and a mobile app needs a shared home
for its knowledge. Without one, each repository holds its own partial view of
the job. This episode shows how to create a workspace, declare its member
repos, check it into git, and load it on a second machine. It is for engineers
who work on one job across several repositories.

## At a glance

| Item | Detail |
|---|---|
| Roadmap group | Verification and governance |
| Runtime | 5 minutes |
| Prerequisites | shipd installed; episodes 1 to 6 |
| Commands shown | `shipd workspace init`, `shipd wiki init`, `shipd workspace sync`, `/s:workspace clone` |

## Script

### 0:00–0:50 One job, one workspace

**On screen:** A folder tree for `~/workspaces/myapp`. A label tags the manifest,
the wiki, and the initiatives as tracked. A label tags the `api`, `web`, and
`mobile` folders as ignored.

**Narration:** A workspace is a git repo you clone to stand up one job. A job
is one feature that touches several of your repositories. The workspace holds
the manifest and the job's wiki. The member repos appear beside them, and the
workspace never tracks them.

### 0:50–2:10 Create the workspace

**On screen:** A terminal runs `mkdir -p ~/workspaces/myapp`, then
`shipd workspace init ~/workspaces/myapp --git`. The presenter opens
`.shipd-config.json` and adds a `workspace` block with `focus` and three
projects. Each project lists a repo with a `url`.

**Narration:** The `--git` flag turns the folder into a git repo and seeds a
managed block in `.gitignore`. Then you declare the job in the manifest. The
focus names the primary project. Every repo entry needs a URL, so another
machine can clone it.

### 2:10–3:20 Sync and commit

**On screen:** The presenter runs `shipd wiki init` and
`shipd workspace sync --write-gitignore`. The sync prints a plan. Then the
presenter commits the manifest, the `.gitignore`, and `.shipd/`, and pushes.

**Narration:** The sync command prints the plan and never touches the
network. In a Claude session, `/s:workspace sync` runs the plan. You commit
only the manifest and the knowledge. Keep the managed `.gitignore` block,
because it keeps the member repos out of the workspace repo.

### 3:20–4:20 Load it on a second machine

**On screen:** A second terminal runs
`/s:workspace clone git@github.com:acme/myapp.git ~/workspaces/myapp`. The
session shows a three-rung list: worktree, reference clone, full clone.
A consent round appears before anything materializes.

**Narration:** One command clones the workspace and runs the sync flow. The
flow picks the cheapest rung for each member repo. It reuses a local checkout
when one exists, and it clones in full only on a fresh machine. Nothing
materializes before you consent.

### 4:20–5:00 Day to day

**On screen:** The presenter runs `shipd workspace` and shows the roster. A
slide lists `/s:ask` and `/s:teach`.

**Narration:** The roster shows the focus and any absent member repos. The
oracle reads the job wiki first. The command `/s:teach` distills decisions
into that wiki. Work inside a member repo keeps its own worktree per change.

## Takeaways

- A workspace is a repo that manifests the member repos, projects, and wiki
  of one cross-repo job.
- Commit the manifest and the knowledge. The engine ignores the member repos.
- The sync ladder picks a worktree, a reference clone, or a full clone, and
  it asks for consent first.

## Next

Episode 8 covers [Member maps and headless runs](08-advanced-workspaces.md).

## Sources

- [Workspaces](../../workspaces.md)
- [Getting started with workspaces](../../workspaces/getting-started.md)
