## MODIFIED Requirements

### Requirement: Debounced store push
id: store-push-debounce
base: ed83fe4c11d2
Dropped: A burst of writes ends in one push

When a store auto-commit lands in a workspace or external store, the resolved
`store_sync` key is true, and the store carries an `origin` remote, the
engine SHALL start the plugin's `store_sync.py` in its delayed mode as a
detached process, passing the store's git repository root and the resolved
`store_push_delay`, and SHALL return without waiting for it. The engine
process itself SHALL run no network call. If the helper cannot be started,
then the engine SHALL swallow the failure and leave the write's exit code and
output unchanged. The engine SHALL NOT schedule a push for the personal
memory store, for a write that made no commit, or while `store_sync` resolves
false.

When started in delayed mode, the helper SHALL record a unique token and a
push deadline, the current time plus the delay, in a token file in the system
temp directory keyed by the repository root's absolute path. The helper SHALL
then claim a waiter lock file beside the token file. If another helper holds
a lock refreshed within the last 60 seconds, then the helper SHALL exit 0
having run no git, so at most one helper waits per repository. If the lock
was last refreshed more than 60 seconds ago, then the helper SHALL take the
lock over.

The lock holder SHALL wait until the deadline in the token file has passed,
re-reading the file so a later write extends the wait, and SHALL refresh the
lock at least every ten seconds while it waits. The holder SHALL then release
the lock. If the token file changed after the holder's last read, then the
holder SHALL claim the lock again and keep waiting, or exit 0 when another
helper now holds it. Otherwise the helper SHALL integrate the upstream as
the `store-sync-hook` requirement specifies and push the local commits. Every
git invocation SHALL carry a timeout and SHALL run with
`GIT_TERMINAL_PROMPT=0`. If any step fails, then the helper SHALL exit 0 and
leave the store's commits in place for the next attempt.

#### Scenario: A store commit reaches the remote after the delay
- **GIVEN** a workspace store cloned from a bare remote, with
  `store_push_delay` declared as 0
- **WHEN** `wiki-queue-add` appends a block and exits
- **THEN** within ten seconds the remote's branch contains the queue commit

#### Scenario: A second helper exits while the first waits
- **GIVEN** a delayed helper waiting on a store with a delay of 3 seconds
- **WHEN** a second delayed helper starts for the same store
- **THEN** the second helper exits 0 within two seconds, the remote does not
  yet contain the store's commit, and one lock file exists

#### Scenario: A later write extends the wait
- **GIVEN** a delayed helper waiting with a delay of 3 seconds
- **WHEN** a second helper with a delay of 3 seconds starts 1.5 seconds later
- **THEN** the first helper exits no sooner than 3 seconds after the second
  started, the remote then contains the store's commits, and no lock file
  remains

#### Scenario: An abandoned lock is taken over
- **GIVEN** a lock file for the store whose modification time is 120 seconds
  old and no helper running
- **WHEN** a delayed helper starts with a delay of 0
- **THEN** the remote contains the store's commit and no lock file remains

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
