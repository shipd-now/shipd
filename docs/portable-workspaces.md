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
- `wiki_base` — the base wiki the oracle falls back to after the job wiki,
  and the promote-to-base target for `/s:teach`. Optional but recommended.

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
- `/s:ask` — the oracle answers from the **job wiki first, then
  `wiki_base`**, then the repo's spec surfaces; unanswerable questions queue
  in the job wiki for you.
- `/s:teach` — distill decisions into the job wiki; promote answers that are
  job-independent to the base wiki so every future job inherits them.
- Per-change work inside a member repo is unchanged: each member still uses
  its own `.worktrees/<change>` flow. The workspace-level worktree/clone cost
  is paid **once per job, not per task**.
