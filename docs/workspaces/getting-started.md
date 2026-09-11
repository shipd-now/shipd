<!-- doc-type: how-to -->

# Getting started

[← Workspaces](../workspaces.md)

## Set up the machine once

Three optional keys in `~/.shipd-config.json` tune materialization, wiki
fallback, and where job workspaces live:

```json
{
  "clone_sources": ["~/projects"],
  "wiki_base": "~/projects/.shipd/wiki",
  "workspaces_root": "~/workspaces"
}
```

- `clone_sources` — directories whose immediate children the engine probes for
  a clone with a matching origin URL. Undeclared means no probing, and every
  member full-clones.
- `wiki_base` — the optional base wiki the oracle falls back to after the
  workspace chain, and the promote-to-base target for `/s:teach`. It holds a
  durable base **outside** the chain; for a base reached by nesting instead,
  see [Nesting job workspaces](nesting-and-stores.md#nesting-job-workspaces).
- `workspaces_root` — the mandated parent directory, covered below.

A workspace read needs none of them: a machine with no `~/.shipd-config.json`
still resolves every read verb — see [Headless consumers](headless.md).

### The mandated parent directory

Declaring `workspaces_root` turns the one-folder-per-job convention into a rule:

- A bare name given to `shipd workspace init` resolves to
  `<workspaces_root>/<name>`, and the engine creates the leaf directory.
- The engine refuses an init target — or a `/s:workspace clone` destination —
  outside the root, naming the target, the declared root, and `workspaces_root`.
- The root and everything under it counts as inside, so `--nested` job
  workspaces stay legal ([nesting](nesting-and-stores.md#nesting-job-workspaces)).
- Undeclared means no mandated root, and every surface behaves as it always has.
- `shipd config` reports the value **as declared**, with `~` left unexpanded,
  and the installed sample config documents the key.
- Doctor's `config` check validates it. A malformed value fails — not a
  non-empty string, or not absolute once `~` expands. A missing root warns.

## Create a job workspace

```sh
mkdir -p ~/workspaces/documents-linking
shipd workspace init ~/workspaces/documents-linking --git
```

`--git` turns the root into a git repo and seeds the managed `.gitignore`
block. The explicit path works with or without `workspaces_root`. With the key
declared, `shipd workspace init documents-linking --git` needs no `mkdir`.

Then declare the job in `~/workspaces/documents-linking/.shipd-config.json`:

```json
{
  "workspace": {
    "focus": "documents",
    "projects": {
      "documents":  {"repos": [{"path": "documents",  "url": "git@github.com:acme/documents.git",  "branch": "main"}]},
      "tasks":      {"repos": [{"path": "tasks",      "url": "git@github.com:acme/tasks.git"}]},
      "incentives": {"repos": [{"path": "incentives", "url": "git@github.com:acme/incentives.git"}]}
    }
  }
}
```

- `focus` names the job's primary project — the oracle and `/s:teach` weight
  its surfaces first.
- Every materializable repo entry needs a `url`. A bare string
  (`"repos": ["tools"]`) stays valid, but the engine cannot clone it elsewhere.

Finish the bootstrap from inside the workspace:

```sh
shipd wiki init                          # job wiki store
shipd workspace sync --write-gitignore
```

`shipd workspace sync` prints the materialization plan and never touches the
network; `--write-gitignore` fills the managed members block, so the member
directories stay untracked. Then run `/s:workspace sync` in a Claude session to
execute the plan's git commands, or run the printed `command:` lines yourself.

## Check it into git

The engine keeps member repos out of the workspace repo, so you commit only the
manifest and the knowledge:

```sh
cd ~/workspaces/documents-linking
git add .shipd-config.json .gitignore .shipd/
git commit -m "documents-linking workspace: manifest + wiki"
git remote add origin git@github.com:acme/ws-documents-linking.git
git push -u origin main
```

- **Never remove the managed `.gitignore` block** (`# >>> shipd-workspace
  members` … `# <<< shipd-workspace members`). It keeps `documents/` and its
  siblings out of the workspace repo — no submodules, ever.
- Wiki writes (`/s:teach`, queued oracle questions) **auto-commit locally** and
  never push. End a session with `git push`, and start one with `git pull`. The
  wiki then travels between your machines, and between everyone sharing it.
- Sharing the repo across **several engineers** works the same way, with a few
  conflict surfaces — see [Sharing a workspace with a team](teams.md).

## Load it on another machine

Run one command in a Claude session:

```
/s:workspace clone git@github.com:acme/ws-documents-linking.git ~/workspaces/documents-linking
```

It clones the workspace repo, then runs the sync flow, which executes the
engine's plan member by member — cheapest rung first:

1. **worktree** of an existing local clone with the same origin (near-instant),
2. **`git clone --reference`** borrowing a local object store (seconds),
3. **full clone** from the manifest `url` (only when the machine has nothing).

**Nothing materializes before you consent.** The flow opens one round over the
whole plan. It offers reuse of the checkouts the scan found (the default,
mapped not cloned), fresh materialization, a member-by-member review, or a stop.

The manifest never records how a member landed: materialization is per-machine,
so one workspace repo works on every machine and in every teammate's clone.

## Day to day

- `shipd workspace` — roster, focus, absent members, `[url]` markers.
- `shipd workspace sync` — re-plan any time. It reports **drift** (an on-disk
  origin differing from the manifest) and never repairs it; `--json` emits
  machine-readable records.
- `/s:workspace sync` — execute the plan again after you edit the manifest, for
  example when the job gains a member repo.
- `/s:ask` — the oracle answers from the **job wiki, then enclosing workspace
  wikis (nearest first), then `wiki_base`**, then the repo's spec surfaces.
  Unanswerable questions queue in the job's own wiki, for whoever answers first.
- `/s:teach` — distill decisions into the job wiki, and promote job-independent
  answers to the base wiki so every future job inherits them.
- Per-change work inside a member repo does not change: each member keeps its
  own `.worktrees/<change>` flow. You pay the workspace worktree or clone cost
  **once per job, not per task**.
