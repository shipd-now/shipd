## ADDED Requirements

### Requirement: Workspace artifact auto-commit
id: workspace-artifact-autocommit

When an engine write into a workspace repository succeeds — a `prd` emit, an
`initiative` emit, `initiative-sync` rewriting a brief's status, or
`initiative-set-status` — the engine SHALL make a local git commit scoped to
exactly the written paths, following the wiki auto-commit convention of the
`shipd-wiki` capability: the same `store_autocommit` gate resolved from the
invoking repo, the same exclusive lock, a silent no-op outside a git work
tree or when no bytes changed, and one stderr warning with an unchanged exit
code when the commit fails. The commit subjects SHALL be
`shipd: emit prd <slug>`, `shipd: emit initiative <slug>`, and
`shipd: initiative <slug> status <status>`, each carrying the brand prefix.
Each such commit SHALL schedule the debounced store push exactly as a wiki
commit does.

#### Scenario: A PRD emit commits its file
- **GIVEN** a git-initialized workspace with a configured identity
- **WHEN** `spec_emit.py prd mobile-push --from <file>` installs the PRD
- **THEN** a new commit whose subject ends `shipd: emit prd mobile-push`
  contains exactly `prds/mobile-push/prd.md`

#### Scenario: An initiative emit commits its brief
- **GIVEN** the same workspace
- **WHEN** `spec_emit.py initiative q3-growth --from <file>` installs a brief
- **THEN** a new commit whose subject ends `shipd: emit initiative q3-growth`
  contains exactly that brief

#### Scenario: A status change commits the brief
- **GIVEN** an installed, committed initiative brief
- **WHEN** `initiative-set-status` moves it to another status
- **THEN** a new commit contains only the brief

#### Scenario: Unrelated staged state is not swept
- **GIVEN** an unrelated file staged in the workspace repo's index
- **WHEN** a PRD emit auto-commits
- **THEN** the commit omits the unrelated file, which remains staged

#### Scenario: The key false leaves the write uncommitted
- **GIVEN** a repo layer declaring `store_autocommit` false
- **WHEN** a PRD emit runs from that repo
- **THEN** the PRD installs, the exit code is zero, and no commit is made

#### Scenario: A non-git workspace installs without committing
- **WHEN** a PRD emit runs in a workspace outside any git work tree
- **THEN** the PRD installs and the exit code is zero

### Requirement: Guides document the delayed store push
id: workspaces-doc-store-push

The workspaces guide's `teams.md` page SHALL state, in its concurrency
section, that the engine pushes a workspace or external store about a minute
after the last engine write, that a diverged store is rebased onto its
upstream first, and that a conflicting rebase is aborted and left for a
person. It SHALL instruct readers and agents not to commit or push the store
by hand after an engine write, and SHALL name `store_push_delay` and the
`store_sync` key that turns the push off. The customisation guide's key table
SHALL carry a `store_push_delay` row naming what it sets and its default, and
its `store_sync` row SHALL name the delayed push. The `external-stores.md`
page SHALL NOT state that the reader pushes the store themselves. Each page
SHALL remain within the line cap of its doc type.

#### Scenario: The teams page documents the delayed push
- **WHEN** `docs/workspaces/teams.md` is read
- **THEN** it names the delayed push, the rebase, `store_push_delay`, and the
  instruction not to push by hand

#### Scenario: The key table carries the delay
- **WHEN** `docs/customise.md` is read
- **THEN** its key table has a `store_push_delay` row with the default of 60
  seconds

#### Scenario: The manual-push instruction is gone
- **WHEN** `docs/workspaces/external-stores.md` is read
- **THEN** it carries no instruction to push the store repo yourself

#### Scenario: The pages stay within their caps
- **WHEN** the documentation lint runs over the three pages
- **THEN** it reports no finding
