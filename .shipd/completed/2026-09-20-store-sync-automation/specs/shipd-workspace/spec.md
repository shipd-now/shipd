## ADDED Requirements

### Requirement: Teams guide documents the store's git automation
id: workspaces-doc-store-sync

The workspaces guide's `teams.md` page SHALL document the store's git
automation in its concurrency section: that an engine write into a workspace
or external store auto-commits locally, that the engine serializes those
commits behind an exclusive lock, that a session-boundary hook fast-forwards
the store at session start and pushes at both boundaries, and that
`store_autocommit` and `store_sync` each turn one of those off. The page
SHALL NOT state that the engine takes no locks or runs no networked git, and
SHALL remain within the shipd documentation standard's 150-line how-to cap.
The guide's `getting-started.md` page and the `workspaces.md` index SHALL
likewise instruct no manual push or pull of the workspace repo at a session
boundary, each staying within its own doc-type cap. The customisation guide's
key table SHALL carry a row for each of the two keys naming what it gates and
its default.

#### Scenario: The teams page documents both keys
- **WHEN** `docs/workspaces/teams.md` is read
- **THEN** it names `store_autocommit` and `store_sync`, the auto-commit, the
  lock, and the session-boundary sync

#### Scenario: The stale no-locks claim is gone
- **WHEN** `docs/workspaces/teams.md` is read
- **THEN** it carries no claim that the engine takes no locks or never
  pushes, pulls, or fetches

#### Scenario: No page still prescribes the manual ritual
- **WHEN** `docs/workspaces.md` and `docs/workspaces/getting-started.md` are
  read
- **THEN** neither instructs the reader to run `git pull` at a session start
  or `git push` at its end

#### Scenario: The page stays within its cap
- **WHEN** the documentation lint runs over `docs/workspaces/teams.md`
- **THEN** it reports no length finding
