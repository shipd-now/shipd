<!-- doc-type: how-to -->

# Sharing a workspace with a team

[← Workspaces](../workspaces.md)

Nothing about a workspace repo is single-user. Any number of engineers clone
the same one, through the load flow of [getting started](getting-started.md):

```sh
/s:workspace clone git@github.com:acme/myapp.git ~/workspaces/myapp
```

**Members are machine-local, always**. Each clone runs its own sync ladder and
picks its own rung per member: a worktree, a `--reference` clone, or a full
clone. The manifest records only *where a member comes from* (`url`), never
*how it landed*, and neither engineer commits or shares the rung.

**The shared surfaces are the knowledge, not the code**. The repo tracks:

- the **manifest** (`.shipd-config.json`) — members, focus, and any `store_root`,
- the **wiki** (`.shipd/wiki/`) — pages plus the `index.md` catalog,
- the **queue** (`.shipd/wiki/queue.md`) — pending oracle questions, which any
  teammate answers,
- the **initiatives and project context** (`.shipd/initiatives/`, `.shipd/projects/`).

Ordinary git carries them. `git pull` brings a teammate's pages, answers, and
briefs into your clone; `git push` publishes yours. There is no shipd server,
no sync service, and no workspace-level daemon.

**The ignore block does not churn**. The engine derives the managed members
block in `.gitignore` from the manifest's member paths, between
`# >>> shipd-workspace members` and `# <<< shipd-workspace members`. Every
clone with that manifest reconciles to the same block, so two machines running
`shipd workspace sync --write-gitignore` produce no diff to fight over.

## Inherited worktree hooks need your consent

`post-worktree-scripts` resolve nearest-wins through the layered config, so a
list in the workspace repo's tracked `.shipd-config.json` governs every member
repo beneath it. One registration seeds every member's fresh worktree — and
whoever last pushed wrote shell commands your next `shipd worktree` runs
unasked.

The receiving machine holds the switch. The engine keeps a machine-local trust
ledger at `~/.shipd-trust.json`, keyed by a fingerprint of the **exact command
list** you consented to. The key is the list, not the file carrying it, so
consent travels with the commands. Trust for a tracked config covers the
worktree's own copy of it, and every other clone here. Before any list runs:

- a **trusted** list runs silently, exactly as it always has;
- an **untrusted** list on a terminal prints the declaring config file and
  every command, then asks before running anything;
- an **untrusted** list with no terminal refuses — an autopilot run, CI, any
  non-interactive session. The worktree stays in place, no hook runs, and the
  verb exits `3`.

Grant consent explicitly with `shipd worktree hooks trust`, which prints the
resolved list and its source, records the entry, and exits `0`. `shipd
worktree hooks run` then finishes the parked setup. Run it **from inside the
worktree the refusal names**, never at the parked root.

Registering a hook through `shipd worktree hooks add` (or `/s:worktree-hooks`)
trusts the list it writes, so your own hooks never prompt. It holds only where
you already trusted the effective list there, or that list was empty. Adding
your item onto a teammate's not-yet-consented list records nothing, so the
full list still reaches the gate. Trust pins to the exact list, so any edit —
a teammate's `git pull` included — re-arms the gate. Expect one prompt per
shared list per machine, and one after every change to it.

## Concurrency expectations

The engine takes no locks and runs no networked git — it never pushes, pulls,
or fetches on your behalf. Every wiki write (`/s:teach`, a queued question, an
answer, a discard) auto-commits **locally**, scoped to exactly the files that
write touched. Two engineers at once produce two local histories, and git —
not shipd — reconciles them:

- **Per-page files merge cleanly**. Concurrent edits to distinct `wiki/*.md`
  pages never conflict.
- **`queue.md` is a conflict surface**. The engine appends new questions at
  EOF, so two parallel queue writes land at the same place. Keep both blocks
  when you resolve.
- **`index.md` is a conflict surface**. Every wiki emission rewrites the
  catalog wholesale, so parallel page installs collide there. Keep every entry
  from both sides.
- **Duplicate `q-<slug>` blocks leave the queue invalid**. Slugs are unique
  across `queue.md`. A merge keeping two blocks with one slug invalidates the
  store, and later queue writes fail until you remove or rename one. Check the
  merged file for repeated `## q-` headings before you commit.
- **Two answers to one question conflict on its `Answer:` line**. Both edits
  land on the same line of the same block. Keep **exactly one** answer, never
  a concatenation of the two: the block holds a single `Answer:` value. Pick
  the answer the team stands behind, and say so in the resolving commit.

The protocol is the one [getting started](getting-started.md) recommends for a
single engineer: **`git pull` at the session start, `git push` at its end**.
Branch the workspace repo, or don't, exactly as your team prefers.

## An enterprise example: one workspaces repository

Take an enterprise with several engineering groups — `discovery` and
`platform`, each holding three or four teams — over repos the whole
organization shares. Anyone contributes to any repo, and discipline codeowners
approve the pull requests.

**One dedicated workspaces repository, one folder per team or group**. Each
folder is a job workspace with its own manifest and wiki, and
[multi-workspace repos](multi-workspace-repos.md) carries the mechanics of
that shape. Clone it once with plain `git clone`:

```sh
git clone git@github.com:acme/workspaces.git ~/workspaces/acme
cd ~/workspaces/acme/discovery && shipd workspace sync
```

```
~/workspaces/acme/                 <- the one workspaces repo clone
  discovery/                       <- WORKSPACE — the discovery group
    .shipd-config.json             tracked: manifest — projects, focus
    .shipd/wiki/  initiatives/     tracked: the group's shared knowledge
    main-app/  api/                machine-local: shared repos, materialized
    .shipd-workspace.local.json    machine-local: your member map, if any
  platform/                        <- WORKSPACE — another group, same shape
```

**Projects are systems, not teams**. The manifest forbids two projects
claiming one repo path, and shared repos are exactly that: no team owns
`api-core`. Declare projects along the seams your codeowners already draw. The
`main-app` project takes the frontend and mobile repos, `api` the repos the
backend discipline owns, and `infra` the deployment and platform repos. Two
folders declaring the same `api-core` duplicate nothing: uniqueness holds per
manifest, and each is that group's own view. A team is instead who works an
**initiative** — a `Project:`-scoped brief every clone reads.

**Nobody materializes everything**. The sync plan is advisory per member. An
engineer who works three of the declared repos runs the commands for those
three and skips the rest. An absent member draws a note, never an error. An
engineer who already has a checkout elsewhere maps it instead of re-cloning,
with [a member map](member-map.md) beside the manifest. The map is
machine-local and never committed, so one layout never leaks into another.

**A group whose knowledge must stay isolated gets its own repository**. Git
has no per-directory permissions, so everyone who clones the workspaces repo
reads every folder in it. Give that group a workspace repository of its own —
**separate repos, not directories, are the isolation boundary.**

Day to day, `shipd workspace` prints the group's roster of projects, members,
and initiatives. `shipd workspace sync` re-checks the members you use, and
`shipd board` reports delivery across every declared project's repos.
