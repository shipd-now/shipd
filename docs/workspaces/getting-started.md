# Getting started

[← Workspaces](../workspaces.md)

## One-time machine setup

Tell the engine where your existing local clones live (so materialization is
cheap), where your durable base wiki is, and — optionally — where job
workspaces are allowed to live. In `~/.shipd-config.json`:

```json
{
  "clone_sources": ["~/projects"],
  "wiki_base": "~/projects/.shipd/wiki",
  "workspaces_root": "~/workspaces"
}
```

- `clone_sources` — directories whose immediate children are probed for a
  clone with a matching origin URL. Undeclared = no probing, everything
  full-clones.
- `wiki_base` — the base wiki the oracle falls back to after the workspace
  chain, and the promote-to-base target for `/s:teach`. Optional but
  recommended for a durable base that sits **outside** the chain — see
  [Nesting job workspaces](nesting-and-stores.md#nesting-job-workspaces) for a
  base reached by nesting instead.
- `workspaces_root` — the mandated parent directory for job workspaces:
  declaring it turns this guide's one-folder-per-job-under-`~/workspaces/`
  convention from a habit into a rule. A bare name given to `shipd workspace
  init` resolves to `<workspaces_root>/<name>`, with the leaf directory
  created for you; an explicit init target — or a `/s:workspace clone`
  destination — that lands outside the root is refused with an error naming
  the target, the declared root, and `workspaces_root`. The root itself and
  everything beneath it counts as inside, so `--nested` job workspaces (see
  [Nesting job workspaces](nesting-and-stores.md#nesting-job-workspaces))
  inside the root stay legal. Undeclared = no mandated root, and every surface
  behaves exactly as it does without the key. `shipd config` reports the value
  **as declared**, with `~` left unexpanded; the installed sample config
  documents the key; and doctor's existing `config` check validates it —
  `fail` on a malformed value (not a non-empty string, or not absolute once
  `~` expands), `warn` when the declared root directory does not exist.

These keys tune *materialization*, *wiki fallback*, and *where workspaces
live* — none of them is needed to read a workspace, so a machine with no
`~/.shipd-config.json` at all still resolves every read verb (see
[Headless consumers](headless.md)).

## Create a job workspace

```sh
mkdir -p ~/workspaces/documents-linking
shipd workspace init ~/workspaces/documents-linking --git
```

`--git` makes the root a git repo and seeds the managed `.gitignore` block.

With `workspaces_root` declared
([One-time machine setup](#one-time-machine-setup)), the bare job name
suffices — `shipd workspace init documents-linking --git` creates
`~/workspaces/documents-linking` and initializes it there, no `mkdir` needed.
The explicit-path example above is the flow when the key is undeclared, and
keeps working either way.

Then declare the job in
`~/workspaces/documents-linking/.shipd-config.json`:

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
shipd wiki init                          # job wiki store
shipd workspace sync --write-gitignore
```

`shipd workspace sync` prints the materialization plan (it never touches the
network); `--write-gitignore` fills the managed members block so the member
dirs stay untracked. Then run `/s:workspace sync` in a Claude session to
actually execute the plan's git commands, or run the printed `command:` lines
yourself.

## Check it into git

The engine already keeps member repos out of the workspace repo — you commit
only the manifest and the knowledge:

```sh
cd ~/workspaces/documents-linking
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
  [Sharing a workspace with a team](teams.md).

## Load it on another machine

One command in a Claude session:

```
/s:workspace clone git@github.com:acme/ws-documents-linking.git ~/workspaces/documents-linking
```

This clones the workspace repo, then runs the sync flow, which executes the
engine's plan member by member — cheapest rung first:

1. **worktree** of an existing local clone with the same origin (near-instant),
2. **`git clone --reference`** borrowing a local object store (seconds),
3. **full clone** from the manifest `url` (only when the machine has nothing).

The manifest never records how a member landed — materialization is always a
per-machine decision, so the same workspace repo works on every machine, and
in every teammate's clone of it.

## Day to day

- `shipd workspace` — roster, focus, absent members, `[url]` markers.
- `shipd workspace sync` — re-plan any time; **drift** (an on-disk origin
  differing from the manifest) is reported, never "repaired".
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
