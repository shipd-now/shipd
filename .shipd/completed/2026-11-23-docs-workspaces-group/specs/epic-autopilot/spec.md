## MODIFIED Requirements

### Requirement: Merged-dependency check
id: merged-dependency-check
base: 82640e6cf564

The autopilot driver SHALL decide whether an `After` dependency has merged
by reading the repository that tracks the content directory: the git work
tree `git rev-parse --show-toplevel` reports from the resolved content
directory — the consuming repository for an in-repo content directory, the
store's own repository where `store_root` relocates it. The base ref SHALL
be `origin/main` where `git rev-parse --verify --quiet` resolves it in that
repository, else `main`. A dependency counts as merged exactly when
`git ls-tree --name-only <ref>` in that repository, on the `completed/`
directory's path relative to that repository's top level, lists an entry
whose name is a leading digits-and-dashes prefix followed by `-<slug>`.
While neither ref resolves, the dependency SHALL count as not merged. If
the content directory is not inside a git work tree, or `git ls-tree` exits
non-zero, then the check SHALL fail with an error naming the dependency, the
repository or content directory, and git's first error line, and SHALL NOT
report the dependency as unmerged. In the detached pre-build step, where
`store_root` is declared and `store_sync` resolves true, the driver SHALL
first run a best-effort `git fetch origin main` in the store's repository
(exit code ignored); the waves mode SHALL NOT fetch. If the check fails in
the pre-build step, then the member SHALL park as `needs-human` at stage
`dependency` with the check's error as the reason and no session id. Where
`store_root` is declared, an unmerged-dependency reason SHALL also name the
store's repository. The stores guide
(`docs/workspaces/external-stores.md`) SHALL state that dependents
release once the store repository's base branch carries the completed
entry.

#### Scenario: An external store's base releases a dependent
- **GIVEN** `store_root` resolving into a second git repository whose `main`
  tracks `<repo-folder>/completed/2026-01-01-a`, and ready member `b` after
  `a` in the consuming repository
- **WHEN** `--waves --json` runs from the consuming repository
- **THEN** `b` joins a build wave and `blocked` is empty

#### Scenario: An in-repo content directory reads the consuming repository
- **GIVEN** no `store_root` and a base tree holding
  `.shipd/completed/2026-10-15-a`
- **WHEN** the check runs for `a`
- **THEN** `git ls-tree --name-only origin/main -- .shipd/completed/` runs in
  the consuming repository and `a` counts as merged

#### Scenario: An unresolvable base ref blocks
- **GIVEN** a repository where neither `origin/main` nor `main` resolves
- **WHEN** the check runs for `a`
- **THEN** `a` counts as not merged and no error is raised

#### Scenario: A store outside any git work tree fails loudly
- **GIVEN** `store_root` resolving outside any git work tree, and ready
  member `b` after `a`
- **WHEN** `--waves` runs
- **THEN** the mode exits 1 with an error naming `a` and the content
  directory, and prints no wave

#### Scenario: A failing tree read parks with the cause
- **GIVEN** a member after `a` whose `git ls-tree` exits 128 with
  `fatal: not a tree`
- **WHEN** the detached pre-build step runs
- **THEN** the member parks as `needs-human` at stage `dependency`, the
  reason carries `fatal: not a tree`, and no merge or drift command runs

#### Scenario: The pre-build step fetches the store
- **GIVEN** `store_root` declared and `store_sync` true
- **WHEN** the detached pre-build step runs for a member with a dependency
- **THEN** `git fetch origin main` runs once in the store's repository before
  the check, and a failing fetch does not park the member

#### Scenario: The stores guide names the dependency rule
- **WHEN** `docs/workspaces/external-stores.md` is read
- **THEN** it states that an `After` dependency releases once the store
  repository's base branch carries the completed entry
