# Sharing a workspace with a team

[← Workspaces](../workspaces.md)

Nothing about a workspace repo is single-user. Any number of engineers can
clone the same one — the load flow of
[Load it on another machine](getting-started.md#load-it-on-another-machine) is
the same whether the second clone is your own laptop or a teammate's:

```
/s:workspace clone git@github.com:acme/ws-documents-linking.git ~/workspaces/documents-linking
```

**Members are machine-local, always.** Each clone runs its own sync ladder and
picks its own rung per member — a worktree of a clone that machine already
has, a `--reference` clone, or a full clone — because the manifest records only
*where a member comes from* (`url`), never *how it landed*. So one engineer
worktree-ing `documents` off an existing checkout and another full-cloning it
produce the same workspace, and neither choice is committed or shared.

**The shared surfaces are the knowledge, not the code.** What travels between
engineers is exactly what the workspace repo tracks:

- the **manifest** (`.shipd-config.json`) — the job's members, focus, and any
  `store_root`,
- the **wiki** (`.shipd/wiki/`) — pages plus the `index.md` catalog,
- the **queue** (`.shipd/wiki/queue.md`) — pending oracle questions, so a
  question one engineer's session queued is a question anyone on the team can
  answer,
- the **initiatives and project context** (`.shipd/initiatives/`,
  `.shipd/projects/`).

The transport is ordinary git: `git pull` brings a teammate's pages, answers,
and briefs into your clone; `git push` publishes yours. There is no shipd
server, no sync service, and no workspace-level daemon.

**The ignore block does not churn.** The managed members block in `.gitignore`
(`# >>> shipd-workspace members` … `# <<< shipd-workspace members`) is derived
deterministically from the manifest's member paths, so every clone with the
same manifest reconciles to the same block. Running `shipd workspace sync
--write-gitignore` on two machines produces no diff to fight over — the block
only changes when the manifest's members do.

**A shared workspace supplies worktree hooks to every member repo — and they
need your consent.** `post-worktree-scripts` resolve nearest-wins through the
layered config exactly like every other key, so a list declared in the
workspace repo's tracked `.shipd-config.json` governs every member repo
beneath it. That is genuinely useful — one registration, and every member's
fresh worktree seeds itself the same way — but it also means whoever last
pushed the shared repo has written shell commands that your machine would
otherwise run unannounced on your next `shipd worktree`.

So the receiving machine holds the switch. The engine keeps a machine-local
trust ledger at `~/.shipd-trust.json`, keyed by a fingerprint of the **exact
command list** you consented to — each entry records the config file that
declared it at the time, but only informationally. Because the key is the list
and not the file that carries it, consent travels with the commands: trust
granted against a tracked config at a repo root also covers the worktree's own
checked-out copy of that same declaration, and any other clone of it on this
machine. Before any list runs — on the create path and on `hooks run` alike:

- a **trusted** list runs exactly as it always has, silently;
- an **untrusted** list on a terminal prints the declaring config file and
  every command, and asks before running anything;
- an **untrusted** list with no terminal (an autopilot run, CI, any
  non-interactive session) refuses: the worktree is left in place, no hook
  runs, and the verb exits `3` — the same parked, resumable outcome a failing
  hook produces.

Grant consent explicitly with:

```
shipd worktree hooks trust
```

which prints the resolved list and its source, records the entry, and exits
`0`. `shipd worktree hooks run` then finishes the parked setup — run it **from
inside the worktree the refusal left behind**, which the refusal names by path;
running it at the parked root would set that root's own directory up instead.

Registering a hook yourself through `shipd worktree hooks add` (or
`/s:worktree-hooks`) trusts the resulting list as it writes it, so your own
hooks never prompt — but only when what was effective there beforehand was
already trusted or empty. Adding your item onto a teammate's not-yet-consented
list records nothing: commands you have not seen are never trusted as a side
effect of an unrelated registration, so the full list still reaches the gate,
where it is printed for you. Trust is pinned to the exact list: any edit to it
— by you, or by a teammate's `git pull` — re-arms the gate, so the next run
asks again. Expect one prompt per shared list per machine, and one after every
change to it.

**Concurrency expectations.** The engine takes no locks and runs no networked
git — it never pushes, pulls, or fetches on your behalf. Every wiki write
(`/s:teach`, a queued oracle question, an answer, a discard) auto-commits
**locally**, scoped to exactly the files that write touched and sweeping in
nothing else you had staged. Two engineers working at once therefore produce
two independent local histories, and git — not shipd — reconciles them:

- **Per-page files merge cleanly.** Different `wiki/*.md` pages are different
  files; concurrent edits to distinct pages never conflict.
- **`queue.md` is a conflict surface.** New questions are appended at EOF, so
  two engineers queueing questions in parallel both land at the same place and
  git reports a conflict. Keep both blocks when resolving.
- **`index.md` is a conflict surface.** The catalog is rewritten wholesale on
  every wiki emission, so parallel page installs collide there even when the
  pages themselves do not. Resolve by keeping every entry from both sides.
- **Duplicate `q-<slug>` blocks leave the queue invalid.** Slugs must be
  unique across `queue.md`. A merge that keeps two blocks with the same slug
  — the usual result of two engineers naming a question the same thing —
  makes the store invalid, and later queue writes fail until you remove or
  rename one of them. Check the merged `queue.md` for repeated `## q-`
  headings before committing.
- **Two answers to one question conflict on its `Answer:` line.** A pending
  `q-<slug>` block is visible to everyone who pulled it, so two engineers can
  answer the same question in parallel. Both edits land on the same line of
  the same block, and git reports a conflict there. Resolve it by keeping
  **exactly one** answer — never both, and never a concatenation of the two:
  the block holds a single `Answer:` value, and a merged pair of them is not a
  richer answer, it is a malformed one. Pick the answer the team stands
  behind, discard the other, and say so in the resolving commit.

The practical protocol is the one
[Check it into git](getting-started.md#check-it-into-git) already recommends
for a single engineer, and it is what keeps the surfaces above from colliding
in the first place: **`git pull` at the start of a session, `git push` at the
end of it.** The engine is agnostic about anything beyond that — branch the
workspace repo, or don't, exactly as your team prefers.

## An enterprise example: shared repos, many groups

The pattern above scales past a single team. Take an enterprise with several
engineering groups — say `discovery` and `platform`, each holding three or
four teams — where the repos are **shared across the whole organization**:
anyone contributes to any repo, and pull-request approval belongs to
discipline codeowners (backend engineers own the API repos, mobile engineers
the app repos, and so on).

**One workspace repo per group — never one repo for every group.** Each group
maintains its own workspace repo, and every engineer in the group clones it
under `~/workspaces/`:

```
/s:workspace clone git@github.com:acme/ws-discovery.git ~/workspaces/discovery
```

Separate repos stay the access and isolation boundary, exactly as
[multi-workspace repos](multi-workspace-repos.md) warns: a single org-wide
workspace repo would give everyone write scope over every group's wiki and
queue, and interleave all groups' knowledge commits in one history. Per-group
repos keep the knowledge surfaces group-scoped while the *code* stays shared.

```
~/workspaces/discovery/            <- the ws-discovery clone
  .shipd-config.json               tracked: manifest — projects, focus
  .gitignore                       tracked: managed members block
  .shipd/
    wiki/  initiatives/  prds/     tracked: the group's shared knowledge
  main-app/
    frontend/  mobile/             machine-local: shared repos, materialized
  api/
    api-core/  api-gateway/        machine-local
  .shipd-workspace.local.json      machine-local: your member map, if any
```

**Projects are systems, not teams.** The manifest forbids two projects
claiming the same repo path — and shared repos are exactly that: no team owns
`api-core`, so teams cannot partition the members. Declare projects along the
same lines your codeowners already draw:

- `main-app` — the frontend and mobile repos,
- `api` — the API repos the backend discipline owns,
- `infra` — deployment and platform repos.

Teams need no manifest concept at all. A team is who is working an
**initiative** — a `Project:`-scoped brief under `.shipd/initiatives/` — and
the group's R&D goals live there too, visible to every clone.

**Each group declares only the repos it touches.** Five groups declaring the
same `api-core` in five manifests is not duplication to fight — each
manifest is that group's curated view of the shared codebase, and the
uniqueness rule holds per manifest.

**Nobody has to materialize everything.** An engineer who works three of the
declared repos materializes three: the sync plan is advisory per member, so
run the commands for the members you need and skip the rest — an absent
member is annotated, never an error. And an engineer who already has a
checkout elsewhere maps it instead of re-cloning, with
[a member map](../workspaces.md#mapping-members-to-existing-checkouts) beside
the manifest — machine-local, never committed, so one engineer's layout never
leaks into another's.

Day to day is the same protocol as any shared workspace — `git pull` at the
start of a session, `git push` at the end — plus the group-wide read
surfaces:

```
shipd workspace          # the group's roster: projects, members, initiatives
shipd workspace sync     # materialize (or re-check) the members you use
shipd board              # delivery across every declared project's repos
```
