<!-- doc-type: reference -->

# External stores

[← Workspaces](../workspaces.md)

By default a repo's shipd artifacts live inside it, at `<repo>/.shipd/`. The
optional **`store_root`** key relocates them into an external store — the
workspace repo itself, or a dedicated artifacts repo. Plans, specs, and
completed changes then sit in one place, rather than scattered across member
repos you may not own.

## When to use it

Use a store when the member repos are not yours to fill with plans. Use one
also when the plans must sit in one place. CI then sees no artifacts, as the
[known limitations](#known-limitations) explain.

## How to run it

Declare the key **once, at the workspace root**. Every member repo beneath it
inherits the key through the ordinary nearest-wins merge, so no member repo
needs a config of its own.

```json
{
  "workspace": { "...": "..." },
  "store_root": "shipd-store"
}
```

The tree below assumes a registry declaring project `acme` with members at
`acme/api`, `acme/web`, and `acme/mobile`. See
[per-repo folder naming](#per-repo-folder-naming) for how the store folder
derives from those paths:

```
~/workspaces/myapp/
  .shipd-config.json          ← declares the project registry and store_root
  shipd-store/                ← the external store (tracked with the workspace)
    acme/                     ← the registry project's own path segment …
      api/                    ← … then each member's manifest path, `acme/api`
        verified/  planned/  completed/  research/
      web/                    ← `acme/web`
      mobile/                 ← `acme/mobile`
  acme/
    api/  web/  mobile/       ← the member repos, at their declared `acme/*`
                               ←   manifest paths — artifact-free
```

The per-repo folder **is** the content directory: it holds `verified/`,
`planned/`, `completed/`, and `research/` directly. The `dir` key renames an
*in-repo* `.shipd/`, and does not apply to an external store.

### A dedicated artifacts repo

A dedicated artifacts repo is the same key pointed elsewhere. Clone the repo
anywhere, then declare it — in the workspace config, or in
`~/.shipd-config.json` to cover every repo on the machine:

```json
{ "store_root": "~/projects/acme-shipd-artifacts" }
```

### Check what resolved

Check the resolution before you rely on it. A mis-declared `store_root`
silently resolves a fresh, empty store rather than failing:

```sh
shipd config
```

The verb prints a `store:` line carrying the resolved absolute content
directory whenever the config declares the key.

```sh
shipd doctor
```

The preflight's `store` line reports the same resolution: `ok`, naming the
in-repo or resolved external content directory. It `warn`s when a directory
still exists at the *previous* flat-layout path while the resolved one does
not, naming both paths and a `git mv` remedy. The check is report-only: it
never moves, creates, or deletes anything on your behalf.

## Reference

### Where the store lands

`~` expands, and an absolute value stands as-is. A relative value resolves
against the directory of the config file that declared it — not the current
repo. So `"store_root": "shipd-store"` in
`~/workspaces/myapp/.shipd-config.json` always means
`~/workspaces/myapp/shipd-store`, however deep the repo resolving
it sits. The committed workspace config therefore resolves the same on every
machine.

### Per-repo folder naming

Where a project registry declares the repo, the folder is that member's
**manifest path** — `acme/api`, not the bare basename `api`. The store then
mirrors the workspace's own `project/repo` structure.

The engine matches the resolution root against the registry the same way it
resolves project ownership: equality-or-containment, with the most specific
entry winning. The machine-local member map matches too, so a repo relocated
on this machine still resolves its declaring member's manifest path. A
worktree lying under a member's own checkout, at
`<repo>/.worktrees/<change>`, resolves identically to the main checkout,
because it lies inside that same declared entry.

Where no registry declares the repo, the folder falls back to the basename
of the *main checkout's* directory. That covers an undeclared repository, no
discoverable registry, or an unloadable one. The engine probes the basename
locally with `git rev-parse --git-common-dir`, so a change developed in
`<repo>/.worktrees/<change>` still resolves the **same** store folder as the
main checkout. Outside a git repo the folder falls back to the resolution
root's own basename.

The engine mandates the derivation; no key chooses the old, flat layout. It
never migrates a store already populated under that layout — see
[check what resolved](#check-what-resolved).

### Auto-commit

When the store is itself a git work tree, engine writes into it commit
locally, scoped to exactly the files written. Four writers commit: change
installs, gate plan rewrites, `set-status`, and merge or archive.

This mirrors the wiki convention (see
[getting started](getting-started.md)). The commits stay purely local: never a
push, a pull, or a fetch. Outside a work tree the commit is a silent no-op. A
failed commit prints one warning line, and never fails the verb.

Push and pull the store repo yourself, exactly as you do the workspace repo.
Two paths run networked git on a store while `store_sync` is `true`. Autopilot
fetches the store's `origin main` before it checks a dependency. The
session-boundary hook also fetches, fast-forward merges, and pushes a store
that lives in the workspace repository; see
[Sharing a workspace with a team](teams.md#concurrency-expectations).
Writes to an **in-repo** `.shipd/` never auto-commit — those stay the change's
own pull request.

### Dependencies between epic members

Autopilot reads an `After` dependency from the base branch of the store
repository: the remote-tracking `origin/main`, else the local `main`. A
dependent member releases once that branch carries the dependency's
`completed/` entry. Push the store to release the dependents. A store outside
any git work tree makes the check fail with an error.

### Known limitations

- **The worktree guard does not see an external store.**
  `worktree.sh remove` checks for work in progress in in-repo `planned/`
  content only. With an external store it reports nothing to protect. The
  statusline does resolve the store: it probes the registry path, then the
  checkout name. It cannot follow a member that the machine-local member map
  relocates, and shows `no specs` for it.
- **Basename collisions are yours to avoid, for an undeclared repo.** Two
  such repos sharing a checkout name resolve one store folder — undetected.
  A declared registry member never collides this way: its manifest path
  already disambiguates `acme/dittor` from `partner/dittor`. Give an
  undeclared repo a distinct directory name, or a store of its own.
- **CI sees no artifacts.** An opted-in repo's checkout carries no `.shipd/`,
  so an in-repo CI step for the spec lint has nothing to lint.
- **shipd itself does not opt in.** This repo keeps its artifacts in-repo, so
  every change's specs and implementation still travel in one pull request.
