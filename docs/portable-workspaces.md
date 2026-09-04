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

Both keys tune *materialization* and *wiki fallback* — neither is needed to
read a workspace, so a machine with no `~/.shipd-config.json` at all still
resolves every read verb (see
[§9 Headless consumers](#9-headless-consumers)).

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
  `git push`, start one with `git pull`, and the wiki travels between your
  machines — and between everyone sharing the repo — like any repo.
- Sharing the workspace repo across **several engineers** works the same way,
  with a few conflict surfaces to know about — see
  [§8 Sharing a workspace with a team](#8-sharing-a-workspace-with-a-team).

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
per-machine decision, so the same workspace repo works on every machine, and
in every teammate's clone of it.

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
  surfaces; unanswerable questions queue in the job's own wiki, for you or
  whichever teammate gets to them first.
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

## 8. Sharing a workspace with a team

Nothing about a workspace repo is single-user. Any number of engineers can
clone the same one — the load flow of
[§4](#4-load-it-on-another-machine) is the same whether the second clone is
your own laptop or a teammate's:

```
/s:workspace clone git@github.com:acme/ws-documents-linking.git ~/jobs/documents-linking
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
same manifest reconciles to the same block. Running
`workspace-sync --write-gitignore` on two machines produces no diff to fight
over — the block only changes when the manifest's members do.

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

The practical protocol is the one [§3](#3-check-it-into-git) already
recommends for a single engineer, and it is what keeps the surfaces above from
colliding in the first place: **`git pull` at the start of a session,
`git push` at the end of it.** The engine is agnostic about anything beyond
that — branch the workspace repo, or don't, exactly as your team prefers.

## 9. Headless consumers

A workspace repo is readable by things that are not a Claude session — a CI
job, a chat bot, a cloud agent. The footprint is deliberately small:

- a **bare `git clone`** of the workspace repo — no members materialized, no
  sync run,
- **Python 3** — `spec_status.py` is stdlib-only, so nothing to install, and
- the plugin's **`plugins/s/skills/build/scripts/spec_status.py`**, run in
  place inside a plugin checkout — it imports its sibling modules from that
  directory, so copying the one file out on its own does not work.

That is the whole list. Run the verbs from inside the clone, or point at it
from anywhere with the top-level `--root`:

```sh
git clone git@github.com:acme/ws-documents-linking.git /tmp/ws
python3 <plugin>/skills/build/scripts/spec_status.py --root /tmp/ws workspace-show
```

**Discovery needs nothing but the config file.** The engine finds the
workspace by walking upward for a `.shipd-config.json` that declares
`workspace` — it consults no git metadata and no `.shipd/` marker, so a
checkout with the git history stripped, or an unpacked tarball, resolves
exactly like a clone.

**Reads succeed with every member absent.** Nothing about reading a workspace
requires its member repos to exist:

- `workspace-show` exits 0 and reports the roster with each unmaterialized
  member marked `(absent) [url]`,
- `cat wiki <slug>`, `wiki-show`, and the initiative reads
  (`cat initiative <slug>`, `initiative-show`) all resolve from the tracked
  `.shipd/` content alone,
- `workspace-sync` only *prints* the materialization plan — it probes local
  disk and never touches the network, so it is safe to run in CI as an
  inspection.

**No machine-level configuration is needed.** A missing
`~/.shipd-config.json` changes nothing for a reader: `clone_sources` only
picks a cheaper rung during materialization, and `wiki_base` only adds a
fallback store after the workspace chain. Neither affects what a read verb
returns from the clone in front of it.

**Git matters only for writes.** A headless consumer that also *writes* — a
bot queueing a question with `wiki-queue-add`, say — still works without a
git binary or a configured identity: the write installs, the auto-commit is
skipped or fails soft to a single stderr warning, and the verb exits 0. Push
the result yourself if you want it shared; the engine will not.
