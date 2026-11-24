## ADDED Requirements

### Requirement: Debounced store push
id: store-push-debounce

When a store auto-commit lands in a workspace or external store, the resolved
`store_sync` key is true, and the store carries an `origin` remote, the
engine SHALL start the plugin's `store_sync.py` in its delayed mode as a
detached process, passing the store directory and the resolved
`store_push_delay`, and SHALL return without waiting for it. The engine
process itself SHALL run no network call. If the helper cannot be started,
then the engine SHALL swallow the failure and leave the write's exit code and
output unchanged. The engine SHALL NOT schedule a push for the personal
memory store, for a write that made no commit, or while `store_sync` resolves
false.

When started in delayed mode, the helper SHALL record a unique token in a
file in the system temp directory keyed by the store's absolute path, then
wait the delay. If the file then holds another helper's token, then the
helper SHALL exit 0 having run no git, so a burst of writes ends in one push
after the last write. Otherwise the helper SHALL integrate the upstream as
the `store-sync-hook` requirement specifies and push the local commits. Every
git invocation SHALL carry a timeout and SHALL run with
`GIT_TERMINAL_PROMPT=0`. If any step fails, then the helper SHALL exit 0 and
leave the store's commits in place for the next attempt.

#### Scenario: A store commit reaches the remote after the delay
- **GIVEN** a workspace store cloned from a bare remote, with
  `store_push_delay` declared as 0
- **WHEN** `wiki-queue-add` appends a block and exits
- **THEN** within ten seconds the remote's branch contains the queue commit

#### Scenario: A burst of writes ends in one push
- **GIVEN** two delayed helpers started for one store, the second while the
  first still waits
- **WHEN** both delays elapse
- **THEN** the first helper exits having run no git and the second pushes

#### Scenario: The write never waits for the push
- **GIVEN** a workspace store with `store_push_delay` declared as 60
- **WHEN** a queue write runs
- **THEN** the verb exits zero in under five seconds and the commit is not
  yet on the remote

#### Scenario: A store without a remote schedules nothing
- **GIVEN** a git-backed workspace store with no `origin` remote
- **WHEN** a queue write commits
- **THEN** the engine starts no helper process

#### Scenario: The key false schedules nothing
- **GIVEN** a resolved configuration declaring `store_sync` false
- **WHEN** a queue write commits in a store with an `origin` remote
- **THEN** the engine starts no helper process

#### Scenario: The personal store is never scheduled
- **GIVEN** a git-backed personal memory store with an `origin` remote
- **WHEN** a `--personal` wiki emit commits
- **THEN** the engine starts no helper process

#### Scenario: A helper that cannot start never fails the write
- **GIVEN** a plugin tree whose `store_sync.py` is missing
- **WHEN** a queue write commits in a store with an `origin` remote
- **THEN** the verb exits zero with the commit made and prints nothing extra

## MODIFIED Requirements

### Requirement: Session-boundary store sync
id: store-sync-hook
base: 0563a85b02d2
Dropped: A divergent upstream warns and changes nothing

The plugin SHALL ship a stdlib-only `store_sync.py` outside
`plugins/s/skills/build/scripts/`, so the engine's no-network rule is
preserved, and SHALL register it on both `SessionStart` and `SessionEnd`.
While the resolved `store_sync` key is true and the resolved store is a
workspace or external store inside a git work tree carrying an `origin`
remote, the script SHALL on `SessionStart` integrate the store's upstream,
then push any local commits, and SHALL on `SessionEnd` push any local
commits. To integrate, the script SHALL fetch the upstream, SHALL change
nothing when the local branch already contains it, SHALL merge it
`--ff-only` when the local branch has no commits of its own, and otherwise
SHALL rebase the local commits onto it with the working tree autostashed.
The script SHALL hold the engine's store commit lock across the merge or
rebase. If the rebase fails, then the script SHALL abort it, restoring the
branch and working tree to their prior state, and SHALL NOT push. Where the
store resolves to the repo-local fallback, the script SHALL run no git at
all, so it never pushes a working repository's branch. Every git invocation
SHALL carry a timeout. If any step fails — the key is false, no store
resolves, no upstream is configured, the rebase conflicts, the push is
rejected, a call times out, or configuration resolution fails — then the
script SHALL print at most one warning line to stderr and SHALL still exit 0.

#### Scenario: Session start fast-forwards and pushes
- **GIVEN** a workspace store inside a git work tree with an `origin`
  remote, no unpushed local commit, and one new upstream commit
- **WHEN** the hook runs at session start
- **THEN** the upstream commit is merged fast-forward and the script exits 0

#### Scenario: Session end pushes pending commits
- **GIVEN** the same store with one unpushed local commit
- **WHEN** the hook runs at session end
- **THEN** the commit is pushed and the script exits 0

#### Scenario: A divergent upstream is rebased and pushed
- **GIVEN** a store with one unpushed local commit and one new upstream
  commit touching a different file
- **WHEN** the hook runs at session start
- **THEN** the local commit sits on top of the upstream commit, the remote
  branch contains both, and the script exits 0

#### Scenario: A conflicting rebase aborts and warns
- **GIVEN** a store whose unpushed local commit and new upstream commit
  change the same line of one file
- **WHEN** the hook runs at session start
- **THEN** the local branch points at its prior commit, no rebase is in
  progress, nothing is pushed, one warning line is printed to stderr, and
  the script exits 0

#### Scenario: Uncommitted work survives the rebase
- **GIVEN** a diverged store with a modified tracked file left uncommitted
- **WHEN** the hook runs at session start
- **THEN** the rebase and push succeed and the modification is still present
  and uncommitted

#### Scenario: The key false silences the hook
- **GIVEN** a resolved configuration declaring `store_sync` false
- **WHEN** the hook runs
- **THEN** no git runs, nothing is printed, and the script exits 0

#### Scenario: An in-repo fallback store is never synced
- **GIVEN** a repo with no workspace and no `store_root`
- **WHEN** the hook runs
- **THEN** no git runs against the repository and the script exits 0

#### Scenario: A broken environment never breaks the session
- **GIVEN** a store directory that is not inside a git work tree
- **WHEN** the hook runs
- **THEN** the script exits 0
