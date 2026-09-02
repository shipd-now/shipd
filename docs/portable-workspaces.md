# Portable workspaces

A **portable workspace** is a git repo you clone to stand up a whole
*job to be done*: a cross-repo feature that touches several of your projects.
The workspace repo carries the **manifest** (which member repos belong to the
job, where to clone them from, which project is the focus) and the job's
**LLM wiki** — the member repos themselves are materialized beside them and
never tracked by the workspace repo.

```
~/jobs/documents-linking/        ← the workspace repo (git clone …)
  .shipd-config.json                ← manifest: focus + projects + clone urls   (tracked)
  .gitignore                     ← members block, engine-managed             (tracked)
  .shipd/
    wiki/                        ← the job's knowledge store                 (tracked)
    initiatives/  projects/      ← goals & per-project context              (tracked)
  documents/  tasks/  incentives/   ← member repos, machine-local           (ignored)
```

Everything above the line travels with `git clone`; everything below is
rebuilt per machine by the sync ladder — as **worktrees or reference-clones
of repos you already have locally**, full clones only on a fresh machine.

## 1. One-time machine setup

Tell the engine where your existing local clones live (so materialization is
cheap) and where your durable base wiki is. In `~/.shipd-config.json`:

```json
{
  "clone_sources": ["~/projects"],
  "wiki_base": "~/projects/.shipd/wiki"
}
```

- `clone_sources` — directories whose immediate children are probed for a
  clone with a matching origin URL. Undeclared = no probing, everything
  full-clones.
- `wiki_base` — the base wiki the oracle falls back to after the workspace
  chain, and the promote-to-base target for `/s:teach`. Optional but
  recommended for a durable base that sits **outside** the chain — see
  [§6 Nesting job workspaces](#6-nesting-job-workspaces) for a base reached by
  nesting instead.

## 2. Create a job workspace

```sh
mkdir -p ~/jobs/documents-linking
python3 <plugin>/skills/build/scripts/spec_status.py workspace-init ~/jobs/documents-linking --git
```

`--git` makes the root a git repo and seeds the managed `.gitignore` block.
(`<plugin>` = `plugins/s` in a shipd checkout, or the installed plugin
root.) Then declare the job in `~/jobs/documents-linking/.shipd-config.json`:

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
- Every repo entry that should be materializable needs a `url`. A bare string
  (`"repos": ["tools"]`) is still valid but can't be cloned elsewhere.

Finish the bootstrap from inside the workspace:

```sh
python3 <plugin>/skills/build/scripts/spec_status.py wiki-init       # job wiki store
python3 <plugin>/skills/build/scripts/spec_status.py workspace-sync --write-gitignore
```

`workspace-sync` prints the materialization plan (it never touches the
network); `--write-gitignore` fills the managed members block so the member
dirs stay untracked. Then run `/s:workspace sync` in a Claude session to
actually execute the plan's git commands, or run the printed `command:` lines
yourself.

## 3. Check it into git

The engine already keeps member repos out of the workspace repo — you commit
only the manifest and the knowledge:

```sh
cd ~/jobs/documents-linking
git add .shipd-config.json .gitignore .shipd/
git commit -m "documents-linking workspace: manifest + wiki"
git remote add origin git@github.com:acme/ws-documents-linking.git
git push -u origin main
```

Notes:

- **Never remove the managed `.gitignore` block** (`# >>> shipd-workspace
  members` … `# <<< shipd-workspace members`) — it is what keeps `documents/`
  etc. from being committed into the workspace repo (no submodules, ever).
- Wiki writes (`/s:teach`, queued oracle questions) **auto-commit locally**
  in the workspace repo. They do not push — end a work session with
  `git push`, start one with `git pull`, and the wiki travels between
  machines like any repo.

## 4. Load it on another machine

One command in a Claude session:

```
/s:workspace clone git@github.com:acme/ws-documents-linking.git ~/jobs/documents-linking
```

This clones the workspace repo, then runs the sync flow, which executes the
engine's plan member by member — cheapest rung first:

1. **worktree** of an existing local clone with the same origin (near-instant),
2. **`git clone --reference`** borrowing a local object store (seconds),
3. **full clone** from the manifest `url` (only when the machine has nothing).

The manifest never records how a member landed — materialization is always a
per-machine decision, so the same workspace repo works on every machine.

## 5. Day to day

- `spec_status.py workspace-show` — roster, focus, absent members, `[url]`
  markers.
- `spec_status.py workspace-sync` — re-plan any time; **drift** (an on-disk
  origin differing from the manifest) is reported, never "repaired".
  `--json` emits machine-readable records.
- `/s:workspace sync` — execute the plan again after editing the manifest
  (e.g. a new member repo was added to the job).
- `/s:ask` — the oracle answers from the **job wiki, then any enclosing
  workspace's wiki (nearest first), then `wiki_base`**, then the repo's spec
  surfaces; unanswerable questions queue in the job's own wiki for you.
- `/s:teach` — distill decisions into the job wiki; promote answers that are
  job-independent to the base wiki so every future job inherits them.
- Per-change work inside a member repo is unchanged: each member still uses
  its own `.worktrees/<change>` flow. The workspace-level worktree/clone cost
  is paid **once per job, not per task**.

## 6. Nesting job workspaces

A job workspace can nest inside a base workspace instead of standing alone —
file it directly beneath the base root and every enclosing workspace's
knowledge is inherited automatically, no `wiki_base` needed for that base:

```sh
mkdir -p ~/projects/jobs/documents-linking
python3 <plugin>/skills/build/scripts/spec_status.py workspace-init \
  ~/projects/jobs/documents-linking --nested --git
```

`--nested` is required: the bare verb refuses to create a workspace under an
already-discoverable one, so nesting is always a deliberate choice, never an
accident. It still refuses when the target itself already declares
`workspace`.

**What inherits across the chain** (nearest-first — a nearer answer always
shadows a farther one):

- **Wiki reads** — a page slug resolves to the nearest chain store holding
  it; `index.md` and `queue.md` aggregate every chain store's file so a
  catalogue never hides an inherited page or question.
- **Initiative briefs** — `cat initiative`, the linter's `Initiative:` check,
  and the dashboard's initiative status all resolve to the nearest chain
  member holding the brief.
- **The project registry** — `projects` (and its `focus`) falls through to
  the nearest chain member that declares one; a registry is never merged
  across levels, so a nested job that declares its own `projects` shadows the
  base's outright. `workspace-show` names the registry's provenance whenever
  it comes from an enclosing member.

**What stays nearest-only:**

- **Every write** — wiki store scaffolding, `/s:teach`, queued oracle
  questions, and initiative emission all land in the nested job's own store,
  never an enclosing one. `workspace-show`, `wiki-show`, and `config-show`
  print the resolved chain, so the write target is always inspectable before
  you rely on it.
- **Sync / member materialization** — `workspace-sync` reads only the nested
  job's own manifest, so it never tries to materialize the base workspace's
  members.

`wiki_base` (§1) is still worth declaring for a durable base that sits
**outside** the chain — a shared org-wide wiki no job is filed beneath. A base
already reachable by nesting is redundant: `wiki_base` resolving to any chain
store's directory is treated as undeclared, so it is searched once, not
twice.

## 7. Storing artifacts outside the member repos

By default a repo's shipd artifacts live inside it, at `<repo>/.shipd/`. The
optional **`store_root`** key relocates them into an external store instead —
the workspace repo itself, or a dedicated artifacts repo — so plans, specs and
completed changes are centralized rather than scattered across member repos
you may not even own.

Declare it **once, at the workspace root**, and every member repo beneath it
inherits it through the ordinary nearest-wins per-key merge — no per-repo
config at all:

```json
{
  "workspace": { "...": "..." },
  "store_root": "shipd-store"
}
```

```
~/jobs/documents-linking/
  .shipd-config.json          ← declares store_root once
  shipd-store/                ← the external store (tracked with the workspace)
    documents/                ← one folder per member repo …
      verified/  planned/  completed/  research/
    tasks/
    incentives/
  documents/  tasks/  incentives/    ← the member repos, artifact-free
```

The per-repo folder **is** the content directory: it holds `verified/`,
`planned/`, `completed/` and `research/` directly. The `dir` key (which renames
an *in-repo* `.shipd/`) does not apply to an external store.

**Where the store lands.** `~` expands, an absolute value is used as-is, and a
relative value resolves against the directory of the config file that declared
it — not the current repo. So `"store_root": "shipd-store"` in
`~/jobs/documents-linking/.shipd-config.json` always means
`~/jobs/documents-linking/shipd-store`, however deep the repo resolving it
sits, and the committed workspace config stays portable across machines.

**A dedicated artifacts repo** is the same key pointed elsewhere — clone the
artifacts repo anywhere and declare it, either in the workspace config or in
`~/.shipd-config.json` to cover every repo on the machine:

```json
{ "store_root": "~/projects/acme-shipd-artifacts" }
```

**Per-repo folder naming.** The folder name comes from the repo's git identity
— the basename of the *main checkout's* directory, probed locally with
`git rev-parse --git-common-dir` — so a change developed in
`<repo>/.worktrees/<change>` resolves the **same** store folder as the main
checkout. Outside a git repo the folder falls back to the resolution root's own
basename.

**Auto-commit.** When the store is itself a git work tree, engine writes into
it commit locally, scoped to exactly the files written — change installs, gate
plan rewrites, `set-status`, and merge/archive. This mirrors the wiki
convention (§3): purely local, never a push/pull/fetch, a silent no-op outside
a work tree, and a failed commit is one warning line that never fails the verb.
Push and pull the store repo yourself, exactly as you do the workspace repo.
Writes to an **in-repo** `.shipd/` never auto-commit — those stay the
change's own PR.

**Check what resolved** before relying on it — a mis-declared `store_root`
silently resolves a fresh, empty store rather than failing:

```sh
python3 <plugin>/skills/build/scripts/spec_status.py config-show
```

It prints a `store:` line carrying the resolved absolute content directory
whenever the key is declared.

**Known limitations:**

- **The worktree guard and the statusline don't see an external store.**
  `worktree.sh remove`'s work-in-progress check and `statusline.sh` read
  in-repo `planned/` content only, so with an external store they report
  nothing to protect or display — the same documented blind spot a renamed
  content directory has today.
- **Basename collisions are yours to avoid.** Two repos whose main checkout
  directories share a name resolve the *same* store folder. Nothing detects
  it; give one of them a distinct directory name, or a store of its own.
- **CI sees no artifacts.** An opted-in repo's checkout carries no `.shipd/`,
  so an in-repo spec-lint CI step simply has nothing to lint.
- **shipd itself does not opt in.** This repo keeps its artifacts in-repo, so
  every change's specs and implementation still travel in one PR.
