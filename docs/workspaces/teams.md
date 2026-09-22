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

Every wiki write (`/s:teach`, a queued question, an answer, a discard)
auto-commits **locally** under an exclusive lock. Concurrent writers land
their own commits, never racing git's index lock. A session-boundary hook
fetches, fast-forward merges, and pushes at session start, then pushes again
at session end. Git — not shipd — reconciles whatever stays unsynced:

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

`store_autocommit` turns off the local auto-commit; `store_sync` turns off
the session-boundary hook's fetch, merge, and push. Both default `true`, and
branching the workspace repo, or not, remains entirely your team's call.

## An enterprise example: one workspaces repository

Take an enterprise with several engineering groups — `discovery` and
`platform`, each holding three or four teams. They share repos the whole
organization owns, with discipline codeowners approving every pull request.

**One dedicated workspaces repository, itself a workspace, holding one
`--nested` team workspace per team or group**. The repo root carries an
organization-wide manifest and wiki. Each team's own folder is its own nested
workspace, with its own manifest and wiki store.
[Practical examples](multi-workspace-repos.md) carries the layout's mechanics.
Build it with the guided wizard, run from inside the base:

```sh
git clone git@github.com:acme/workspaces.git ~/workspaces/acme
cd ~/workspaces/acme
shipd workspace team
```

**Reads fall through, writes land nearest.** A team folder that declares no
`projects` of its own inherits the base's; one that does shadows it instead.
Every wiki write — `/s:teach`, a queued question, an answer — lands in the
nearest store. That's a team's own when run from inside it, the base's only
when run from the base itself. A question queued at the base is answerable
only there.

**Projects are systems, not teams**. The manifest forbids two projects
claiming one repo path, and shared repos are exactly that: no team owns
`api-core`. Declare projects along the seams your codeowners already draw. The
`main-app` project takes the frontend and mobile repos, `api` the repos the
backend discipline owns, and `infra` the deployment and platform repos. Two
folders declaring the same `api-core` duplicate nothing: uniqueness holds per
manifest, and each is that team's own view. A team is instead who works an
**initiative** — a `Project:`-scoped brief every clone reads.

**Nobody materializes everything**. The sync plan is advisory per member. An
engineer who works three of the declared repos runs the commands for those
three and skips the rest. An absent member draws a note, never an error. An
engineer who already has a checkout elsewhere maps it instead of re-cloning,
with [a member map](member-map.md) beside the manifest. The map is
machine-local and never committed, so one layout never leaks into another.

**A group whose knowledge must stay isolated gets its own repository**. Git
has no per-directory permissions, so everyone who clones the workspaces repo
reads every team folder in it. That includes the base wiki and every nested
team's own store. Give that group a workspace repository of its own —
**separate repos, not directories, are the isolation boundary.**

Day to day, `shipd workspace` prints a team's roster of projects, members, and
initiatives. `shipd workspace sync` re-checks the members you use, and
`shipd board` reports delivery across every declared project's repos.
