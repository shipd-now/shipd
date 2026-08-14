## ADDED Requirements

### Requirement: Epic derivation in the build close-out
id: epic-close-out-derivation

When a shipped change's plan carried an `Epic:` line, the build flow's
close-out SHALL, after the PR merges and main is pulled, run `epic-sync`
for that epic from a fresh `epic-close-<slug>` worktree — never from the
main checkout — and, only when the derivation changes the epic's status
line, commit and ship the advance as an auto-merging PR; when the status is
unchanged, the worktree is removed with no PR. The close-out SHALL NOT run
the derivation pre-merge, because member archives reach main only after the
squash merge.

#### Scenario: Member merge advances the epic via a PR
- **GIVEN** a shipped change whose plan carried `Epic: reporting-overhaul`
  and whose merge archived the epic's last member
- **WHEN** the build close-out runs
- **THEN** `epic-sync` runs in an `epic-close-reporting-overhaul` worktree
  and the status advance ships as an auto-merging PR

#### Scenario: Unchanged derivation ships nothing
- **WHEN** the close-out's `epic-sync` derives the status the epic already
  carries
- **THEN** no commit or PR is created and the worktree is removed
