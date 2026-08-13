# portable-workspaces
Status: complete
Theme: spec-engine

## Introduction

A workspace today is a fixed directory on one machine: its roster is
hand-maintained, its member repos are wherever they happen to be, and its
wiki — the knowledge layer everything now reads — exists only there. There is
no way to stand up a *job to be done*: a cross-repo feature (say,
document-linking touching `documents`, `tasks`, and `incentives`) that needs
its own focused workspace, its own wiki slice, and a one-command bootstrap on
any machine.

This epic makes workspaces portable: a workspace root becomes a clonable git
repo carrying the manifest (roster with clone URLs, a focus project) and the
job's wiki, with member repos materialized beside it — as worktrees or
reference-clones of existing local repos when possible, full clones only on a
fresh machine — and gitignored so they stay first-class independent repos.
The wiki gains a base layer so job wikis stay focused without fragmenting
standing opinions, and wiki writes auto-commit so knowledge history and
cross-machine sync ride ordinary git.

Success criteria: `git clone <job-workspace>` + one sync command yields a
working workspace with every member repo present and the job wiki live; the
oracle in a job workspace answers from the job wiki first and the base wiki
second; a wiki emit on one machine reaches another via ordinary git
pull/push of the workspace repo.

### Non-goals

- No reproducible-build pinning: member revisions float (URL + optional
  default branch). West's recorded-pin model is the precedent if a "job
  snapshot" is ever wanted — not now.
- No git submodules, ever — the prior art's friction findings are accepted.
- No push/pull automation in engine scripts: the constitution's network-free
  rule holds; syncing remotes stays a session habit or a skill-executed step.
- No team permissioning or multi-user write control of a shared workspace
  repo — single-user across machines/agents for now.
- No migration of the existing workspace at `/Users/mikkelbergmann/projects`:
  it stays as-is and becomes the base wiki's home.

## Research

- [Meta-repo and manifest prior art for portable am workspaces](../../research/meta-repo-manifests/report.md) — repo/west manifest schemas, the meta-tool clonable-root model, submodule avoidance, pinning semantics, planning-repo precedent for co-located LLM context.

## Decisions

User-made in the epic round:

- **Base + job wiki layering.** A `wiki_base` config key points at the
  durable base wiki (the existing workspace's store). The oracle searches
  the job wiki first, then the base; teach-mikk writes to the job wiki by
  default and offers a promote-to-base move for job-independent answers.
  Rejected: job-only wikis (every job starts with an amnesiac oracle) and a
  single global wiki (no per-job focus, empty workspace payload).
- **Floating revisions.** A registry repo entry carries a clone `url` and
  optional default `branch`; after materialization each member tracks its
  own branches. Workspaces coordinate live development, not builds.
- **Siblings placement, guard kept.** Job workspaces are cloned outside the
  existing workspace tree (any non-workspace parent works, e.g.
  `~/projects/jobs/<job>/`); `workspace-init`'s refuse-to-nest guard stays.
- **Auto-commit wiki writes.** Every successful wiki emit and queue-add
  makes a local git commit in the workspace repo; it silently no-ops when
  the store is not inside a git work tree. Push/pull stays manual.

Binding cross-cutting choices every member inherits:

- **Root-as-repo, children gitignored** (the meta-tool model from the
  research): the workspace repo tracks `.shipd-config.json` and the content
  dir (`wiki/`, `initiatives/`, `projects/`); every member repo directory is
  kept in the workspace repo's `.gitignore` so members remain independent
  first-class repos.
- **The materialization ladder.** The manifest records only URLs — how a
  member lands on disk is per-machine, cheapest-first: (1) `git worktree
  add` from an existing local clone of the same remote, on a job branch;
  (2) `git clone --reference`/local-path clone borrowing its object store;
  (3) full clone from the URL, only when the machine has nothing. A job is
  not a task: this cost is paid once per job, and per-change work inside a
  member still uses that repo's own `.worktrees/<change>` flow unchanged.
- **The engine plans, skills execute network git.** Engine scripts stay
  stdlib-only and network-free: the sync verb *computes and prints* the
  materialization/drift plan deterministically (fully unit-testable); the
  `/s:workspace` skill executes the plan's networked `git clone`/`fetch`
  steps. Local-only git (worktree add from a local clone, status, commit)
  is permitted in engine verbs.
- **Focus is explicit.** The workspace object gains an optional
  `focus: <project-slug>` naming the job's primary project; the oracle and
  teach-mikk weight that project's spec surfaces first. Shape-validated
  like the rest of the registry, never existence-checked.
- **Engine constraints hold.** Layered-config resolution (nearest wins) is
  unchanged; every registry/lint extension is shape-only so manifests still
  travel; each member touching `plugins/s/` bumps the plugin version.

## Design

```
~/projects/jobs/documents-linking/     ← job workspace repo (git clone …)
  .shipd-config.json    workspace: {focus: documents,
                       projects: {documents: {repos:[documents], url: …}, …}}
  .gitignore         documents/  tasks/  incentives/   (members untracked)
  .shipd/
    wiki/            job wiki  (emits auto-commit here)
    initiatives/  projects/<slug>/context.md
  documents/         ← worktree of ~/projects/documents   (ladder rung 1)
  tasks/             ← clone --reference …                (rung 2)
  incentives/        ← full clone                          (rung 3)

oracle search: job wiki ─▶ base wiki (wiki_base → ~/projects/.shipd/wiki) ─▶ repo specs
teach-mikk:    writes job wiki ─▶ promote-to-base for job-independent pages
```

The pieces and the seams the decomposition follows:

- **Manifest** (`spec_common.py` registry schema + lint): `url`/`branch` on
  repo entries, `focus` on the workspace object, validation staying
  shape-only. Foundation — everything else reads it.
- **Sync planning** (engine verb): given the manifest and the local disk,
  emit the per-member materialization/drift plan (present, absent→rung,
  gitignore lines missing). Pure computation over `git` queries of local
  state; no network.
- **Execution** (`/s:workspace` skill): `clone <url>` and `sync` flows that
  run the plan's steps with real git, then report the roster. The only
  place networked git runs.
- **Wiki layering** (`wiki_base` config + oracle/teach prose): resolution
  order job→base for reads; job-default with promote-to-base for writes;
  focus-weighted repo surfaces. Touches the `s:oracle` agent, `/s:ask`,
  and `/s:teach` — the store engine itself is unchanged.
- **Auto-commit** (`spec_emit.py` wiki + `wiki-queue-add`): a local commit
  per successful write, no-op outside a git work tree. Independent of the
  other members — it lands whenever.

Member order is dependency order: `workspace-repo-manifest` →
`workspace-sync-plan` → `workspace-clone-skill` → `wiki-base-layering`;
`wiki-emit-autocommit` is independent and can ship any time.

## Changes

| Change | Description | Code | Integration | Unknowns | Risk |
| --- | --- | --- | --- | --- | --- |
| workspace-repo-manifest | Registry schema grows per-repo `url`/`branch` and workspace `focus`; shape validation + lint; `workspace-init` optionally seeds a git repo with the members-gitignored convention | medium | medium | low | medium |
| workspace-sync-plan | Network-free engine verb computing the per-member materialization/drift plan (worktree → reference-clone → full clone) and gitignore maintenance | medium | medium | medium | medium |
| workspace-clone-skill | `/s:workspace` gains clone/sync flows that execute the plan with real git and report the roster | medium | medium | medium | medium |
| wiki-base-layering | `wiki_base` config key; oracle reads job wiki then base and weights the `focus` project; teach writes job-first with a promote-to-base move | medium | high | medium | medium |
| wiki-emit-autocommit | Local auto-commit on every successful wiki emit / queue-add when the store sits in a git work tree | low | low | low | low |
