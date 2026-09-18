# store-root-registry-paths
Status: verified

## Idea

Derive a repository's external-store folder from its workspace registry path, so
an external store mirrors the workspace's own project/repo structure.

### Motivation

An external `store_root` names each repository's folder after the bare basename
of its main checkout, discarding the `project/repo` path the workspace registry
already declares, so the store flattens a structured workspace and two repos
with the same directory name silently share one folder.

### Details

- Derive the per-repo store path from the declared registry member's manifest
  path (`shipd/shipd-app`) instead of the checkout basename (`shipd-app`).
- Keep the basename derivation as the fallback for an undeclared repository, a
  workspace with no registry, and a non-git root.
- Add a report-only `store` check to the doctor preflight that names a store
  folder stranded under the previous flat layout, with its remedy.
- Document the derivation and rescope the basename-collision limitation.

Affected capabilities: `shipd-config` (modified), `shipd-cli` (modified),
`shipd-doctor` (modified). Impact:
`plugins/s/skills/build/scripts/spec_common.py`, `plugins/s/bin/shipd`,
`plugins/s/skills/doctor/SKILL.md`, `docs/workspaces/nesting-and-stores.md`,
and the matching tests. No new dependencies.

### Non-goals

- No new configuration key. The derivation is mandated, not selectable.
- No fallback that prefers an existing flat folder, and no engine verb that
  moves one. The doctor reports; a human runs `git mv`.
- No change to `store_root` resolution itself, to in-repo resolution, or to the
  board's workspace-level aggregation.

## Implementation

- Derive the store path inside `repo_store_folder`
  (`plugins/s/skills/build/scripts/spec_common.py:631`), keeping `specs_dir` its
  single caller so one function still governs the whole surface. Rejected:
  resolving the registry in `specs_dir` — it would split the derivation across
  two functions and bypass the existing memo.
- Reuse the registry matching in `project_of` (`spec_common.py:2208`) rather
  than writing a second matcher: factor its loop into a shared helper returning
  both the project slug and the matching entry's manifest path, and have
  `project_of` return the slug from it. That match already handles
  equality-or-containment, longest-entry-wins, and the machine-local member map,
  so a relocated checkout resolves its declaring member unchanged.
- Take worktree stability from containment, not from the git probe: a worktree
  at `<ws>/shipd/shipd/.worktrees/<change>` lies under entry `shipd/shipd` and
  matches it. Verified live — `project_of` returns `shipd` from this change's own
  worktree, identical to the main checkout's result. The git probe stays only as
  the fallback path's derivation.
- Return the manifest path in its declared `/`-separated form and split it onto
  native separators where it is joined, mirroring how `specs_dirname` handles a
  nested `dir` value. A bare `os.path.join` would embed forward slashes on a
  host whose separator differs.
- Keep the `_STORE_FOLDER_CACHE` memo keyed by the resolved root's real path;
  registry resolution walks the config chain, so caching matters more, not less.
- Model the doctor check on `check_wiki` (`plugins/s/bin/shipd:544`): a check
  returning one `(level, name, detail)` triple, added to `default_checks`
  (`:969`) directly after `wiki`. It reports `warn` — reporting without failing
  the preflight — only when a `store_root` is declared, the flat folder exists,
  and the resolved registry-path folder does not. Every other state reports
  `ok`.
- Treat the new line as report-only in the doctor skill, exactly as
  `doctor-wiki-line` treats `wiki`: parsed like any other check, no remedy row,
  nothing moved on the user's behalf.

Risk: an external store already populated under the flat layout resolves a
fresh, empty folder after this change — the failure the stores guide tells users
to guard against by inspecting the resolution. The doctor check is that guard,
and it names both paths and the `git mv` remedy.

## Questions and answers

### Q1: Is the registry-path layout unconditional, or opt-in behind a config key?
- **Question:** Should the registry-path store folder apply unconditionally to
  every declared registry member, or only behind a new `store_layout` key
  defaulting to the current basename derivation? Options: (a) unconditional,
  with the basename kept as the fallback for undeclared roots; (b) opt-in behind
  a new key. Recommendation: (a).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Unconditional — option (a). The store folder has never been
  configurable, and the only store-related key is `store_root`; the correct
  derivation is mandated and documented rather than selectable, so the change
  adds no key. This also matches `store-root-key`'s existing commitment that a
  workspace root's declaration governs every member repo with no per-repo
  configuration.
- **Queued:** q-store-registry-path-layout-optin

### Q2: What happens to a store already populated under the flat layout?
- **Question:** Should an existing flat-layout store be handled by a doctor
  check, by fallback resolution that prefers the flat folder while it exists, or
  by a dedicated migration verb? Options: (a) doctor check, no migration; (b)
  fallback resolution; (c) migration verb. Recommendation: (a).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Ship option (a). Resolution always uses the new layout, and a
  stranded flat folder surfaces as a doctor check result naming the old path,
  the newly resolved path, and the `git mv` remedy. Fallback resolution is
  rejected: the engine has no fallback-resolution precedent, and silently
  preferring an old on-disk shape is the same failure the stores guide tells
  users to guard against by inspecting the resolution rather than having the
  engine guess. A migration verb is rejected: the engine's standing posture is
  to report a mismatch and name a remedy, never to rewrite a user's on-disk
  state across a layout boundary.
- **Cited:** verified/schema-versioning, docs/workspaces/nesting-and-stores.md
