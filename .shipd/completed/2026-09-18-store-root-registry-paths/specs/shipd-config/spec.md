## MODIFIED Requirements

### Requirement: Workspace-registry-derived repo store path
id: store-repo-folder-name
base: 5ea7500127da
Dropped: Worktree resolves the main checkout's folder

Where `store_root` is declared, the engine SHALL derive the per-repo store path
from the workspace project registry: where the resolution root resolves to a
declared registry member, the store path SHALL be that member's manifest path
exactly as the registry declares it, matched by the same equality-or-containment
resolution that resolves a root's owning project, so a linked worktree and a
member relocated by the machine-local member map both resolve their declaring
member's path. Where the resolution root resolves to no declared member — an
undeclared repository, no discoverable registry, or an unloadable one — the
engine SHALL fall back to the basename of the main checkout's directory,
obtained as the parent directory of the path printed by
`git rev-parse --path-format=absolute --git-common-dir`; if that probe fails,
then the engine SHALL fall back to the basename of the resolution root. The
derived value SHALL be `/`-separated, and the engine SHALL join its components
onto the store root with the host's native separator. The derivation SHALL NOT
be configurable. The result SHALL be cached per resolved root within a process,
and no derivation step SHALL touch the network.

#### Scenario: A declared member resolves its registry path
- **GIVEN** a workspace registry declaring project `shipd` with a repo entry at
  path `shipd/shipd-app`, and `store_root: "store"` at the workspace root
- **WHEN** the content directory is resolved from `<ws>/shipd/shipd-app`
- **THEN** it resolves to `<ws>/store/shipd/shipd-app`

#### Scenario: Worktree resolves its member's registry path
- **GIVEN** that member with a linked worktree at
  `<ws>/shipd/shipd-app/.worktrees/some-change`
- **WHEN** the content directory is resolved from the worktree
- **THEN** it resolves to `<ws>/store/shipd/shipd-app`, identical to the main
  checkout's resolution

#### Scenario: A mapped member resolves its declaring entry's path
- **GIVEN** a member map relocating the entry `shipd/shipd-app` to a checkout
  outside the workspace
- **WHEN** the content directory is resolved from that checkout
- **THEN** the store path is the manifest path `shipd/shipd-app`, not the
  checkout's own location

#### Scenario: Undeclared repo keeps the basename derivation
- **GIVEN** a repository inside the workspace that no registry entry declares
- **WHEN** the per-repo store path is derived
- **THEN** it is the basename of the repository's main checkout directory

#### Scenario: Non-git root falls back to its basename
- **GIVEN** a directory `/tmp/plain-dir` that is not inside a git repository and
  that no registry declares
- **WHEN** the per-repo store path is derived
- **THEN** it is `plain-dir`

#### Scenario: Two members sharing a directory name no longer collide
- **GIVEN** registry entries `shipd/dittor` and `cai/dittor`
- **WHEN** each resolves its content directory under one declared `store_root`
- **THEN** they resolve to distinct store paths

#### Scenario: The stores guide documents the derivation
- **WHEN** `docs/workspaces/nesting-and-stores.md` is read
- **THEN** its per-repo folder naming section states the registry-path
  derivation and the basename fallback, and its basename-collision limitation is
  scoped to repositories no registry declares

### Requirement: External store root
id: store-root-key
base: d8b2cfca3c2a

The resolved configuration MAY carry a `store_root` key holding a non-empty
string path naming an external store for shipd artifacts. The engine SHALL
expand `~` in the value, and where the expanded value is relative, the engine
SHALL resolve it against the directory of the config file that declared the
key. Where `store_root` is declared, the content directory SHALL resolve to
`<resolved-store-root>/<repo-store-path>` — the per-repo directory directly
holding the content layout (`verified/`, `planned/`, `completed/`,
`research/`), with the `dir` key not applied to external resolution. When no
layer declares the key, in-repo resolution SHALL be unchanged. If the value
is not a non-empty string, then resolution SHALL fail with an error naming
`store_root`. The key SHALL merge nearest-wins-wholesale like every top-level
key, so a workspace root's declaration governs every member repo beneath it
with no per-repo configuration.

#### Scenario: Workspace-wide store just works
- **GIVEN** `<ws>/.shipd-config.json` declares `store_root: "shipd-store"` and
  a registry entry at path `backend/cai-backend` present on disk with no config
  of its own
- **WHEN** the content directory is resolved from `<ws>/backend/cai-backend`
- **THEN** it resolves to `<ws>/shipd-store/backend/cai-backend`

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
