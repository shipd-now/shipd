## ADDED Requirements

### Requirement: Mutating verbs are branch-guarded
id: claim-branch-guard

If the repository contains a branch named `change/<change>` and the current
checkout is not on that branch (including a detached HEAD), then the
coordinator's mutating verbs — `claim`, `complete`, and `release` — SHALL
refuse to act, printing a message naming both the current and required
branches and exiting with code 3. When the repository has no
`change/<change>` branch, when the working directory is not a git checkout,
or when the checkout is on the change branch, the verbs SHALL behave
unchanged. The read-only verbs `status` and `next` SHALL never be
branch-guarded.

#### Scenario: Claiming from the wrong checkout is refused
- **GIVEN** a repo where branch `change/x` exists and the checkout is on
  `main` with a planned change `x`
- **WHEN** `claim x` runs
- **THEN** it exits with code 3, names both branches, and marks no task

#### Scenario: The change's own worktree claims normally
- **GIVEN** a checkout on branch `change/x` with a planned change `x`
- **WHEN** `claim x` runs
- **THEN** it claims the next task exactly as before

#### Scenario: A repo without the change branch is unaffected
- **GIVEN** a git repo on any branch where no `change/x` branch exists
- **WHEN** `claim x` runs against its planned change
- **THEN** the guard does not trigger and the verb behaves as before

#### Scenario: A non-git directory is unaffected
- **GIVEN** a plain directory (no git checkout) holding a planned change
- **WHEN** `claim`, `complete`, or `release` run
- **THEN** they behave exactly as before

#### Scenario: Detached HEAD counts as a mismatch
- **GIVEN** a repo where branch `change/x` exists and HEAD is detached
- **WHEN** `claim x` runs
- **THEN** it refuses with exit code 3

#### Scenario: Read-only verbs stay unguarded
- **GIVEN** a repo where branch `change/x` exists and the checkout is on
  `main`
- **WHEN** `status x` or `next x` runs
- **THEN** it reports normally with no branch refusal
