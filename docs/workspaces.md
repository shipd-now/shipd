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
  than inside it. Add it to your ignore rules; nothing in the engine writes it
  for you.

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
