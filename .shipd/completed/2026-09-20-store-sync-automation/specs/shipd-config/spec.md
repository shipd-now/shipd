## ADDED Requirements

### Requirement: Store sync config keys
id: store-sync-keys

The engine SHALL recognize two top-level config keys governing the store's git
behaviour, each resolved through the layered loader like every other key and
each carrying a built-in default:

- `store_autocommit` — a boolean gating whether an engine write into a
  workspace or external store auto-commits. Default `true`.
- `store_sync` — a boolean gating whether the plugin's session-boundary store
  sync hook runs its networked git. Default `true`.

If a declared value is not a boolean, then the engine SHALL treat the key as
undeclared and fall back to the built-in default rather than raising,
mirroring the `worktree_sweep` key's tolerance. Both keys SHALL appear in the
engine's registry of recognized top-level keys and SHALL be documented in the
plugin's copyable config reference, so the existing agreement check over the
two covers them. Neither key SHALL change the repo-local fallback store's
behaviour: while the content directory resolves in-repo with no `store_root`
declared, engine writes SHALL NOT auto-commit whatever `store_autocommit`
resolves to.

#### Scenario: Both keys default true when undeclared
- **WHEN** the keys are resolved from a repo whose configuration layers
  declare neither
- **THEN** both `store_autocommit` and `store_sync` resolve true

#### Scenario: A declared false disables the auto-commit
- **GIVEN** a resolved configuration declaring `store_autocommit` as false
- **WHEN** an engine verb writes into a git-backed workspace store
- **THEN** the write exits zero and no commit is attempted

#### Scenario: A malformed value falls back to the default
- **GIVEN** a repo layer declaring `store_sync` as the string "yes"
- **WHEN** the key is resolved from that repo
- **THEN** the effective value is true and no error is raised

#### Scenario: Nearest layer wins
- **GIVEN** a workspace layer declaring `store_autocommit` false and a repo
  layer declaring it true
- **WHEN** the key is resolved from the repo
- **THEN** the effective value is true

#### Scenario: Both keys are registered and documented
- **WHEN** the config-sample agreement check runs
- **THEN** `store_autocommit` and `store_sync` each appear in the
  recognized-keys registry and in the copyable config reference

#### Scenario: The in-repo exception survives the key
- **GIVEN** a git-initialized repo with a content directory, no workspace, no
  `store_root`, and no declared `store_autocommit`
- **WHEN** a queue block is appended to the repo-local fallback store
- **THEN** the write exits zero and no commit is made

## MODIFIED Requirements

### Requirement: External store auto-commit
id: store-autocommit
base: e4538546b968

When an engine verb successfully writes artifacts into an externally
resolved content directory that is inside a git work tree and the resolved
`store_autocommit` key is true, the engine SHALL make a local git commit
scoped to exactly the written paths, following the wiki auto-commit
convention: while the store is not inside a git work tree the write SHALL
succeed with no commit attempted, a failed commit SHALL be non-fatal (one
warning line, exit code unchanged), and the engine SHALL never push, pull, or
fetch. While `store_autocommit` resolves false, the write SHALL succeed with
no commit attempted. While the content directory resolves in-repo (no
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

#### Scenario: A false key silences the commit
- **GIVEN** a repo whose `store_root` resolves into a git work tree and whose
  resolved configuration declares `store_autocommit` false
- **WHEN** a change is installed through the emit engine
- **THEN** the install succeeds and no commit is attempted
