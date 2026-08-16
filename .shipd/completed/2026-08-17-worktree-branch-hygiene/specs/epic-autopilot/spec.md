## ADDED Requirements

### Requirement: Close-out worktree starts from a fresh branch
id: close-out-fresh-branch

When the autopilot runs its epic-sync close-out, it SHALL create the
`epic-close-<slug>` worktree by invoking the worktree helper with its
fresh-branch flag (`--fresh`), so the derivation never adopts a stale local
`change/epic-close-<slug>` branch left over from an earlier run. If that
fresh creation fails (an existing worktree or an unmerged leftover branch),
then the close-out SHALL be skipped with the helper's error relayed in the
run output, exactly as any other close-out worktree failure is.

#### Scenario: Close-out invokes the helper with the fresh flag
- **WHEN** the autopilot's close-out creates its `epic-close-<slug>` worktree
- **THEN** the worktree helper invocation carries the `--fresh` flag

#### Scenario: Refused fresh creation skips the close-out audibly
- **GIVEN** the helper exits non-zero because the leftover
  `change/epic-close-<slug>` branch is unmerged
- **WHEN** the close-out runs
- **THEN** the close-out is skipped and the run output relays the helper's
  error
