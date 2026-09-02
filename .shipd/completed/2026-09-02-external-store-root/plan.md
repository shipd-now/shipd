# external-store-root
Status: verified

## Idea

Add an optional `store_root` config key that relocates a repo's shipd content
directory into an external store — the workspace repo or any dedicated
artifacts repo — with a per-repo folder derived from the repo's git identity.

### Motivation

Every shipd artifact today is forced into the repo it describes —
`specs_dir` hardwires `<root>/<dir>` — so teams that want artifacts
centralized in the workspace repo or a dedicated artifacts repo have no
supported way to do it. One layered config key lets a workspace declare once
that all member repos store their artifacts externally, with zero per-repo
configuration.

### Details

- New `store_root` key in `.shipd-config.json`: a path (absolute, `~`, or
  relative to the declaring config file's directory) under which each repo's
  artifacts live at `<store_root>/<repo-name>/` — that folder directly holding
  `verified/`, `planned/`, `completed/`, `research/`.
- The repo folder name is derived worktree-stably from git
  (`git rev-parse --path-format=absolute --git-common-dir` → parent basename),
  falling back to the resolution root's basename outside a git repo.
- Engine writes into a git-backed external store auto-commit locally,
  mirroring the wiki auto-commit convention.
- `config-show` additionally prints the resolved external content directory.

Affected capabilities: `shipd-config` (modified), `spec-status` (modified).
Impact: `plugins/s/skills/build/scripts/spec_common.py`, `spec_status.py`,
`spec_emit.py`, `spec_merge.py`, `spec_gate.py`, tests under
`plugins/s/skills/build/tests/`, `docs/portable-workspaces.md`, plugin
version bump.

### Non-goals

- No changes to `worktree.sh`'s remove guard or `statusline.sh`: with an
  external store they do not see external `planned/` content — a documented
  limitation, like renamed content directories today.
- No store-collision detection: two repos sharing a basename under one store
  root are the user's responsibility (documented).
- No remote git operations — the store auto-commit never pushes or pulls.
- No change to this repo's own storage: shipd itself keeps in-repo `.shipd/`.
- No CI awareness: an opted-in repo's bare checkout carries no artifacts, so
  its in-repo spec-lint CI step simply has nothing to lint.

## Implementation

- **Single `store_root` path key, layered nearest-wins merge.** A workspace
  root's declaration governs every member repo beneath it (and every worktree
  inside those repos) with no per-repo config — the "just works" case.
  Rejected: a `"workspace"` sentinel value (the merge already provides
  inheritance) and a per-repo full-path key (forfeits inheritance).
- **Relative values resolve against the declaring config file's directory.**
  `resolve_config` already returns per-key provenance, so the declaring path
  is known; `~` expands; empty or non-string raises `ConfigError` naming
  `store_root`. A deliberate, user-confirmed departure from the absolute-only
  `wiki_base`/`memory_dir` convention so a committed workspace config stays
  portable across machines.
- **Git-derived per-repo folder name.** Main checkout directory basename via
  `git rev-parse --path-format=absolute --git-common-dir` (verified by
  running it from `.worktrees/change-artefacts`: it prints
  `/Users/mikkelbergmann/projects/shipd/.git`, exit 0, so linked worktrees
  and the main checkout agree on `shipd`); fallback is the resolution root's
  basename when the probe fails. Cache the probe per `realpath(root)` in a
  module-level memo so resolution stays cheap. Rejected: an explicit `name`
  subkey (per-repo config burden without removing collisions).
- **Direct layout.** `<store_root>/<repo-name>/` IS the content directory;
  the `dir` key applies only to in-repo resolution. Rejected: nesting
  `<dir>` inside the per-repo folder — an extra level with nothing to
  disambiguate.
- **Auto-commit reuses `wiki_autocommit`** (`spec_common.py:743`): local-only,
  scoped to exactly the written paths, silent no-op outside a git work tree,
  warn-and-continue on failure. A new `store_autocommit(root, paths, subject)`
  wrapper fires only when the content directory resolved externally — in-repo
  artifact commits remain the skill/PR workflow's job. Writers wired:
  `spec_emit.py` (change install), `spec_merge.py` (merge/archive),
  `spec_gate.py` (plan rewrites), `spec_status.py` (`set-status`).
- **`specs_dir(root)` stays the single resolution funnel** — all ~70 call
  sites across the engine inherit external resolution with no signature
  change.

Risks: a mis-declared `store_root` silently resolves a fresh empty store —
mitigated by `config-show` printing the resolved absolute path, and engine
verbs behave exactly as they do today for a missing `.shipd/`. Subprocess
cost of the git probe — mitigated by the per-root memo cache.

## Questions and answers

### Q1: How is the external store key shaped?
- **Question:** How should the config key relocating the content directory be
  shaped? Options: (a) one path key with a per-repo subfolder derived beneath
  it, inherited via the layered merge; (b) a path plus a `"workspace"`
  sentinel form; (c) a direct full path per repo. Recommendation: (a).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option (a) — one single-path key resolved through the standard
  layered per-key merge, matching the shape `memory_dir` already uses and the
  workspace-root inheritance `pr-mode` documents as falling out of the merge.
  The oracle cautioned that the two existing store-path keys reject relative
  paths, so relative-to-declaring-config resolution is a departure to spec
  deliberately; the user confirmed that departure in the same round.
- **Cited:** verified/shipd-config

### Q2: How is the per-repo folder under the store root named?
- **Question:** How is a repo's subfolder under the store root named so that
  `.worktrees/<change>` resolves the same folder as the main checkout?
  Options: (a) git-derived main-checkout basename via
  `git rev-parse --git-common-dir` with a basename fallback; (b) an explicit
  `name` subkey in the repo's config. Recommendation: (a).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option (a) — git-derived identity with the resolution root's
  basename as the non-git fallback, so worktrees resolve identically with
  zero per-repo configuration.
- **Queued:** none (no discoverable workspace to file the question in)

### Q3: What layout does the per-repo folder hold?
- **Question:** Does `<store>/<repo>/` directly hold `verified/`, `planned/`,
  … or does the `dir` key still nest as `<store>/<repo>/<dir>/`? Options:
  (a) direct; (b) nested. Recommendation: (a).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option (a) — the per-repo folder is the content directory; the
  `dir` key applies only to in-repo resolution.
- **Queued:** none (no discoverable workspace to file the question in)

### Q4: Does the engine auto-commit writes into a git-backed store?
- **Question:** Should engine writes into an external store that is a git
  work tree auto-commit like `wiki_autocommit`, or is versioning the user's
  job? Options: (a) auto-commit, fail-open, local-only; (b) no commits.
  Recommendation: (a).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option (a) — the spec library binds a standing convention that
  engine writes into a git-backed shipd store auto-commit locally, scoped to
  exactly the written files, no-op outside a work tree, non-fatal on failure,
  and never touch the network; carry the whole convention to the artifact
  store.
- **Cited:** verified/shipd-wiki, epic/personal-memory, epic/portable-workspaces
