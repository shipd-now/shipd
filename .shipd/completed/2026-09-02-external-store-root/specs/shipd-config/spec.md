## ADDED Requirements

### Requirement: External store root
id: store-root-key

The resolved configuration MAY carry a `store_root` key holding a non-empty
string path naming an external store for shipd artifacts. The engine SHALL
expand `~` in the value, and where the expanded value is relative, the engine
SHALL resolve it against the directory of the config file that declared the
key. Where `store_root` is declared, the content directory SHALL resolve to
`<resolved-store-root>/<repo-folder-name>` — the per-repo folder directly
holding the content layout (`verified/`, `planned/`, `completed/`,
`research/`), with the `dir` key not applied to external resolution. When no
layer declares the key, in-repo resolution SHALL be unchanged. If the value
is not a non-empty string, then resolution SHALL fail with an error naming
`store_root`. The key SHALL merge nearest-wins-wholesale like every top-level
key, so a workspace root's declaration governs every member repo beneath it
with no per-repo configuration.

#### Scenario: Workspace-wide store just works
- **GIVEN** `<ws>/.shipd-config.json` declares `store_root: "shipd-store"`
  and a member repo cloned at `<ws>/cai-backend` with no config of its own
- **WHEN** the content directory is resolved from `<ws>/cai-backend`
- **THEN** it resolves to `<ws>/shipd-store/cai-backend`

#### Scenario: Relative value resolves against the declaring file
- **GIVEN** `store_root: "artefacts"` declared in `/ws/.shipd-config.json`
  and resolution starting from `/ws/team/repo`
- **WHEN** the store root is resolved
- **THEN** it is `/ws/artefacts`, not a path under the start directory

#### Scenario: Undeclared key keeps in-repo resolution
- **WHEN** no layer declares `store_root`
- **THEN** the content directory resolves to `<root>/<dir>` exactly as before

#### Scenario: Invalid value errors naming the key
- **WHEN** a layer declares `store_root: ""` or a non-string value
- **THEN** resolution fails with an error naming `store_root`

### Requirement: Worktree-stable repo folder name
id: store-repo-folder-name

Where `store_root` is declared, the engine SHALL derive the per-repo folder
name from the repository's git identity: the basename of the main checkout's
directory, obtained as the parent directory of the path printed by
`git rev-parse --path-format=absolute --git-common-dir`, so every linked
worktree resolves the same store folder as the main checkout. If the probe
fails (git absent, not a repository), then the engine SHALL fall back to the
basename of the resolution root. The probe result SHALL be cached per
resolved root within a process, and the probe SHALL never touch the network.

#### Scenario: Worktree resolves the main checkout's folder
- **GIVEN** a repo at `/ws/cai-backend` with a linked worktree at
  `/ws/cai-backend/.worktrees/some-change`
- **WHEN** the content directory is resolved from the worktree
- **THEN** the per-repo folder name is `cai-backend`, identical to the main
  checkout's resolution

#### Scenario: Non-git root falls back to its basename
- **GIVEN** a directory `/tmp/plain-dir` that is not inside a git repository
- **WHEN** the per-repo folder name is derived
- **THEN** it is `plain-dir`

### Requirement: External store auto-commit
id: store-autocommit

When an engine verb successfully writes artifacts into an externally
resolved content directory that is inside a git work tree, the engine SHALL
make a local git commit scoped to exactly the written paths, following the
wiki auto-commit convention: while the store is not inside a git work tree
the write SHALL succeed with no commit attempted, a failed commit SHALL be
non-fatal (one warning line, exit code unchanged), and the engine SHALL
never push, pull, or fetch. While the content directory resolves in-repo (no
`store_root` declared), engine writes SHALL NOT auto-commit.

#### Scenario: Write into a git-backed store commits the written files
- **GIVEN** a repo whose `store_root` resolves into a git work tree
- **WHEN** a change is installed through the emit engine
- **THEN** a local commit lands in the store scoped to the installed files
  only

#### Scenario: In-repo store never auto-commits
- **GIVEN** a repo with no `store_root` declared
- **WHEN** a change is installed through the emit engine
- **THEN** no git commit is attempted in the repo

#### Scenario: Non-git store writes succeed without a commit
- **GIVEN** a `store_root` resolving outside any git work tree
- **WHEN** an engine verb writes artifacts there
- **THEN** the write succeeds and no commit is attempted

#### Scenario: Failed commit warns and preserves success
- **GIVEN** a git-backed store where committing fails (e.g. no identity)
- **WHEN** an engine verb writes artifacts there
- **THEN** one warning line is emitted and the verb's exit code is unchanged

## MODIFIED Requirements

### Requirement: Configurable content directory
id: content-dir-key
base: 1f8ccfd38b8b

The engine SHALL resolve the content directory name from the resolved `dir`
key, defaulting to `.shipd` when no layer declares it. The value SHALL be a
single path component (no path separators); a violating value SHALL be an
error. The config filename `.shipd-config.json` itself SHALL NOT be
configurable or affected by `dir`. Where the resolved configuration declares
`store_root`, the external store-root resolution SHALL govern the content
directory's location instead, and the `dir` key SHALL NOT apply.

#### Scenario: Default content directory
- **WHEN** no layer declares `dir`
- **THEN** repo content resolves under `.shipd/` (e.g. `.shipd/planned/<change>/`)

#### Scenario: Renamed content directory
- **GIVEN** the repo's config declares `dir: "specs"`
- **WHEN** a change's directory is resolved
- **THEN** it resolves under `specs/planned/<change>/`

#### Scenario: Separator in dir is rejected
- **WHEN** a layer declares `dir: "nested/specs"`
- **THEN** resolution fails with an error naming the invalid value

#### Scenario: Store root supersedes dir
- **GIVEN** a config declaring both `dir: "specs"` and a `store_root`
- **WHEN** the content directory is resolved
- **THEN** it resolves inside the external store with no `specs` component
