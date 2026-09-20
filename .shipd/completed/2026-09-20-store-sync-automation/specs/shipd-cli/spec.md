## ADDED Requirements

### Requirement: Doctor store-sync check
id: doctor-store-sync-check

The `doctor` verb SHALL report a `store-sync` check naming how far the
resolved store's checkout has drifted from its upstream. The check SHALL
probe with local git only — the upstream's configured name and the
ahead/behind counts from `git rev-list --count --left-right @{u}...HEAD` —
and SHALL never fetch, push, or otherwise reach the network, and SHALL mutate
nothing. Where the store resolves to a workspace or external store inside a
git work tree whose branch has an upstream, the check SHALL report `warn`
naming the unpushed and unpulled commit counts and the store path when either
count is non-zero, and `ok` when both are zero. Where no store resolves, the
store is not inside a git work tree, the branch has no upstream, or the store
is the repo-local fallback, the check SHALL report `ok` naming why no
comparison applies. A malformed configuration SHALL be reported as the detail
rather than failing the preflight, so the check never double-fails what the
`config` check owns.

#### Scenario: Unpushed commits warn with their count
- **GIVEN** a workspace store whose branch is 12 commits ahead of its
  upstream and 0 behind
- **WHEN** `shipd doctor` runs
- **THEN** a `warn store-sync — …` line names 12 unpushed commits and the
  store path, and the preflight's exit code is 0

#### Scenario: A synced store reports ok
- **GIVEN** a workspace store whose branch matches its upstream exactly
- **WHEN** `shipd doctor` runs
- **THEN** an `ok store-sync — …` line is printed

#### Scenario: No upstream reports ok
- **GIVEN** a workspace store whose current branch has no upstream configured
- **WHEN** `shipd doctor` runs
- **THEN** an `ok store-sync — …` line names that no comparison applies

#### Scenario: The check never reaches the network
- **WHEN** `shipd doctor` runs against a store whose remote is unreachable
- **THEN** the `store-sync` line is printed without any fetch being attempted
