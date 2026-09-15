## MODIFIED Requirements

### Requirement: Engine worktree create path
id: engine-worktree-create
base: 35b0db0a7be7

The engine SHALL provide a stdlib-only `worktree.py` script whose first
argument dispatches: `remove`, `prune-branches`, `sweep`, and `hooks` select
those verbs, and any other first argument is a change name for the create path
with an optional `--fresh` flag. The `remove`, `prune-branches`, and `sweep`
verbs SHALL re-execute `worktree.sh` with the arguments passed through
verbatim, preserving its output and exit code. When the create path runs, the
engine SHALL invoke `worktree.sh`'s create path for the git mechanics from the
repo root with output inherited, and, when `worktree.sh` succeeds and
`.worktrees/<name>` did not exist before the invocation, SHALL execute the
resolved `post-worktree-scripts` through the hook consent gate; while the
worktree already existed (a reuse), the engine SHALL skip the scripts.

Where the resolved configuration enables the worktree sweep, the create path
SHALL additionally run `worktree.sh`'s `sweep` verb after the create path has
otherwise completed, reporting only the lines naming a worktree it removed or a
branch it deleted and suppressing its `kept:` and `stale:` lines. The sweep
SHALL NOT alter the create path's exit code under any outcome, so a failed or
refused sweep never fails a worktree creation. While the configuration disables
the sweep, the create path SHALL NOT run it and SHALL behave exactly as it does
without this facility.

#### Scenario: Fresh create runs the configured scripts
- **GIVEN** a repo config declaring two trusted `post-worktree-scripts`
- **WHEN** `worktree.py my-change` runs and `.worktrees/my-change` does not
  yet exist
- **THEN** the worktree is created and both scripts run in declaration order
  with the new worktree as working directory

#### Scenario: Reused worktree skips the scripts
- **GIVEN** an existing `.worktrees/my-change` on branch `change/my-change`
- **WHEN** `worktree.py my-change` runs
- **THEN** the reuse notice is printed and no post-worktree script runs

#### Scenario: Remove passes through to the guarded helper
- **WHEN** `worktree.py remove my-change` runs against a dirty worktree
- **THEN** `worktree.sh`'s refusal report is printed and the exit code is `2`,
  exactly as invoking `worktree.sh remove my-change` directly

#### Scenario: Sweep passes through to the helper
- **WHEN** `worktree.py sweep --dry-run` runs
- **THEN** `worktree.sh`'s sweep report is printed and the exit code matches it,
  exactly as invoking `worktree.sh sweep --dry-run` directly

#### Scenario: Create reclaims a merged worktree alongside
- **GIVEN** a repository holding a merged, guard-clean `.worktrees/shipped` and
  a configuration that does not disable the sweep
- **WHEN** `worktree.py my-change` runs
- **THEN** `.worktrees/my-change` is created, `.worktrees/shipped` is removed,
  and a line names the removed worktree

#### Scenario: The new worktree survives its own create sweep
- **GIVEN** the same repository
- **WHEN** `worktree.py my-change` runs
- **THEN** `.worktrees/my-change` still exists after the sweep and no line
  names it

#### Scenario: Create succeeds where the sweep can reclaim nothing
- **GIVEN** a repository whose root checkout has a detached HEAD so the sweep
  can reclaim nothing
- **WHEN** `worktree.py my-change` runs
- **THEN** the worktree is created and the exit code is zero

#### Scenario: A disabled sweep never runs
- **GIVEN** a resolved configuration declaring the sweep disabled
- **WHEN** `worktree.py my-change` runs in a repository holding a merged,
  guard-clean worktree
- **THEN** that worktree still exists and no sweep output is printed
