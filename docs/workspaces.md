# Workspaces

A **workspace** is a git repo you clone to stand up a whole *job to be done*:
a cross-repo feature that touches several of your projects. The workspace repo
carries the **manifest** (which member repos belong to the job, where to clone
them from, which project is the focus) and the job's **LLM wiki** — the member
repos themselves are materialized beside them and never tracked by the
workspace repo.

```
~/workspaces/documents-linking/   ← THE WORKSPACE REPO — this folder is what
                                    you clone, commit, and push
  .shipd-config.json              ← manifest: focus + projects + clone urls  (tracked)
  .gitignore                      ← members block, engine-managed            (tracked)
  .shipd/
    wiki/                         ← the job's knowledge store                (tracked)
    initiatives/  projects/       ← goals & per-project context              (tracked)
  documents/  tasks/  incentives/ ← member repos, machine-local              (ignored)
```

One folder per job, all of them under a `~/workspaces/` parent: the leaf is the
job's name (`documents-linking`), never a member repo's, so it is never
confused with the `documents/` checkout materialized inside it.

Everything above the line travels with `git clone`; everything below is
rebuilt per machine by the sync ladder — as **worktrees or reference-clones
of repos you already have locally**, full clones only on a fresh machine.

## The guide

**Getting started** — machine setup, creating a job workspace, checking it into
git, loading it on another machine, and the day-to-day verbs.

```sh
shipd workspace init documents-linking --git
```

[Details →](workspaces/getting-started.md)

**Nesting and external stores** — filing a job workspace beneath a base one so
it inherits the base's knowledge, and relocating shipd artifacts out of the
member repos with `store_root`.

```sh
shipd workspace init ~/workspaces/acme-base/documents-linking --nested --git
```

[Details →](workspaces/nesting-and-stores.md)

**Sharing a workspace with a team** — several engineers on one workspace repo,
what travels between them, the worktree-hooks consent gate, and the conflict
surfaces to expect.

```sh
git pull   # at the start of a session
git push   # at the end of it
```

[Details →](workspaces/teams.md)

**Headless consumers** — the minimal footprint a CI job, bot, or cloud agent
needs to read a workspace, and what still works with no members, no git, and
no machine config.

```sh
python3 <plugin>/skills/build/scripts/spec_status.py --root /tmp/ws workspace-show
```

[Details →](workspaces/headless.md)

**Practical examples: multi-workspace repos** — the two shapes for carrying
several workspaces in one repo, with layout diagrams, storage tables, and
their trade-offs.

```sh
git clone git@github.com:acme/company-workspaces.git ~/workspaces/company
cd ~/workspaces/company/workspace-documents && shipd workspace sync
```

[Details →](workspaces/multi-workspace-repos.md)

## Mapping members to existing checkouts

The sync ladder materializes members *under* the workspace root. When you
already have one of them checked out somewhere else on this machine — say
`~/projects/shipd`, the clone you actually work in — map it instead of
materializing a second copy that silently diverges from the first.

The map is one optional file at the workspace root,
`~/workspaces/documents-linking/.shipd-workspace.local.json` — plain JSON, no
comments:

```json
{
  "repos": {
    "shipd": "~/projects/shipd",
    "documents": "../checkouts/documents"
  }
}
```

- **Keys** are manifest member paths — exactly the workspace-root-relative
  `path` values the manifest's `projects[*].repos` entries declare.
- **Values** are where that member lives on this machine. A leading `~` is
  expanded, and a relative value resolves against the workspace root; both are
  stored verbatim and resolved on every read.
- The file is **machine-local and never committed** — it maps *this* machine's
  checkouts, so it sits beside the tracked `.shipd-config.json` manifest rather
  than inside it. The `set` verb below adds it to the workspace root's
  `.gitignore` for you on first write.

You do not hand-author that file. The engine owns it, through three verb forms:

```sh
# list every entry: stored value, then the absolute path it resolves to
python3 <plugin>/skills/build/scripts/spec_status.py workspace-map

# map a declared member to a checkout you already have
python3 <plugin>/skills/build/scripts/spec_status.py \
    workspace-map set shipd ~/projects/shipd

# unmap it again
python3 <plugin>/skills/build/scripts/spec_status.py workspace-map remove shipd
```

- **`set` validates the member path.** It must be a member path the manifest
  declares; anything else exits non-zero naming the declared paths and writes
  nothing. The *local* path is stored **verbatim** — a `~` or a relative form is
  resolved on every read, so what you typed is what the file says.
- **`set` never repairs, and never refuses over the target.** A target that does
  not exist, or that is not a git work tree, is a warning on stderr and the
  entry is still written: pre-declaring a checkout you are about to move into
  place is legitimate.
- **`set` ensures the ignore line.** On a successful write it appends
  `.shipd-workspace.local.json` to the workspace root's `.gitignore` —
  idempotently, creating the file when absent, and deliberately **outside** the
  marked member-repos block, which `workspace sync --write-gitignore` rewrites
  to exactly the manifest's member paths and would otherwise drop it.
- **Every other top-level key survives.** Only `repos` is replaced, so the
  `workspace_root` pointer described in the next section can share the file.
- **`remove` deletes exactly its entry** and exits non-zero when there is none.
  It leaves the ignore line alone.
- **A malformed file fails both writers** with the same error the readers
  raise, naming the file. The verbs never repair a broken map.

The guided front door is **`/s:workspace map`**: it reads the sync plan,
proposes for each unmapped member the local checkout the `clone_sources` scan
matched (or invites a path), asks in a single round, and drives
`workspace-map set` per member you accept — already-mapped members are reported,
never re-asked. `sync` and `clone` stay question-free.

Once mapped, the member *is* that checkout for every workspace read: the report
probes it there, and board aggregation, `locate`, and epic discovery read its
epics and changes.

```sh
shipd workspace            # repo: shipd [mapped -> /Users/you/projects/shipd]
shipd workspace sync       # state: present   action: none
```

What the planner does with a mapped member:

- **Its action is always `none`.** The materialization ladder never runs and no
  advisory command is ever emitted against a mapped path — materializing into a
  directory you own outside the workspace is the one repair this engine must
  never attempt. Use the checkout you already have; clean it up yourself.
- **Origin drift is still reported.** A mapped checkout whose `origin` differs
  from the manifest `url` plans `none` with a drift note naming both URLs,
  exactly as an in-workspace member does.
- **A missing target drifts rather than materializing.** If the mapped path does
  not exist, the member records state `absent`, action `none`, and a drift note
  naming the path — fix the checkout or remove the map entry.
- **A stale key is a note, not an error.** A `repos` key matching no manifest
  member path prints as a note on the workspace report and changes nothing, so a
  leftover entry can never brick the workspace verbs.

A malformed map *does* fail the verb reading it, naming the file: invalid JSON, a
non-object top level or `repos` value, or a mapping value that is not a non-empty
string.

## Resolving from outside the workspace

Mapping a member solves the workspace's side of the problem: the workspace now
knows the checkout is `~/projects/shipd`. This section solves the other side —
running a shipd verb *inside* `~/projects/shipd`, which lives nowhere near
`~/workspaces/documents-linking`, and still landing in the workspace's wiki,
registry, and initiatives instead of a repo-local fallback.

Discovery walks a three-rung ladder, and stops at the first rung that resolves:

1. **The ancestor search.** Every directory from the starting one up to `/`
   whose own `.shipd-config.json` declares `workspace`. A checkout materialized
   under the workspace root resolves here, exactly as it always has — the rungs
   below never run, and never cost a `git` probe.
2. **The pointer.** A `workspace_root` declared in the checkout's own
   `.shipd-workspace.local.json`.
3. **The origin-URL scan.** The workspaces under `workspaces_root` that declare
   this checkout's `origin` as a member `url`.

### The pointer

The explicit rung, and the one to reach for when the scan is ambiguous or your
workspaces do not live under a single parent. It reuses the machine-local
dotfile from the previous section — same filename, disjoint fields: a workspace
root declares `repos`, a member checkout declares `workspace_root`.

`~/projects/shipd/.shipd-workspace.local.json`:

```json
{
  "workspace_root": "~/workspaces/documents-linking"
}
```

A leading `~` is expanded, and a relative value resolves against the file's own
directory. Written at the repo root, it governs the whole repo — the pointer is
found from any subdirectory you run a verb in.

The pointer is **decisive, and reported when wrong**. If it names a directory
that does not itself declare a `workspace`, discovery resolves *nothing* and
prints one warning naming the pointer file and the target, rather than quietly
falling through to the scan — a deliberate declaration that is wrong is a thing
to fix, not to work around.

### The origin-URL scan

With no pointer declared, and `workspaces_root` (see
[getting started](workspaces/getting-started.md)) naming an existing directory,
the engine reads the checkout's `origin` with one local `git remote get-url`
and matches it against the member `url`s declared by each workspace directly
under that parent. No declaration is needed anywhere: the manifest already
carries every member's clone URL.

URLs are compared in a normalized form, so the spelling in the manifest need
not match the spelling of your remote. Scheme and `user@` prefix are stripped,
a `host:path` colon reads as `host/path`, one trailing `.git` and any trailing
slashes are dropped, and the result is case-folded — so all four of these are
one repository:

```
git@github.com:acme/repo.git
https://github.com/Acme/Repo
ssh://git@github.com/acme/repo/
github.com/acme/repo
```

What normalization does *not* do is resolve an **SSH host alias**. If your
remote is `git@github-acme:acme/repo.git`, where `github-acme` is a `Host`
entry in your `~/.ssh/config`, its normalized host is `github-acme` — which
differs from the `github.com` the manifest declares, so the scan will not match
it. The engine reads no SSH configuration, deliberately: a hostname that only
your machine can resolve is not something a workspace manifest can be expected
to know about. Use the `workspace_root` pointer for those checkouts.

Exactly one matching workspace resolves the chain from that workspace — and it
is the *full* chain, so a base workspace enclosing the matched one is still a
member. Two or more matching workspaces resolve nothing and print one warning
naming every match, because guessing between them would silently write a job's
knowledge into the wrong workspace:

```
warning: this checkout's origin is declared by 2 workspaces
(/Users/you/workspaces/documents-linking, /Users/you/workspaces/tasks-rollout);
declare `workspace_root` in /Users/you/projects/shipd/.shipd-workspace.local.json
to choose one
```

The remedy is rung 2: name the one you mean.

### What stays exactly as it was

- **Nothing changes for a start that already resolves an ancestor.** The rungs
  run only on an empty chain.
- **A bare checkout stays silent.** No pointer, no `workspaces_root`, no
  readable `origin`, or no match — the chain is empty, with no warning and no
  error, exactly as before. CI and headless consumers with no machine config
  never leave rung 1.
- **Nothing is written.** Both rungs only read; no verb creates the pointer
  file for you, and neither warning is ever an error — no verb's exit code
  changes.
- **The network is never touched.** The scan's one `git` call is a local
  remote-URL read, bounded by a short timeout, and any failure simply disables
  the rung.
