# store-push-single-helper
Status: verified
Planned-at: 1628bac69b9a302befd02e0348d6cccf310e5645
Gated-hash: 8ea8f1f8e798

## Idea

Keep at most one waiting push helper per store repository, and correct the
`store-push-debounce` requirement's wording about what the engine passes.

### Motivation

Engineers whose sessions write a store in bursts get one idle helper process
per commit for the whole delay, because every commit starts its own sleeper.
The requirement also misstates the helper's argument, so a reader cannot
tell that every write into one repository shares one debounce.

### Details

- A helper claims a waiter lock file beside the token file. A helper that
  finds a live lock records its token and exits at once.
- The token file carries a push deadline. The lock holder waits until that
  deadline passes, so a later write extends the wait.
- The lock holder refreshes the lock while it waits. A lock left unrefreshed
  for 60 seconds counts as abandoned and is taken over.
- The requirement now says the engine passes the store's git repository
  root, and the token file is keyed by that root.

Affected capabilities: `shipd-wiki` (modified). Impact:
`plugins/s/skills/workspace/scripts/store_sync.py`, its test file, and the
plugin version. No new dependency.

### Non-goals

- No change to the engine: it still starts one helper per store commit.
- No change to the delay key, the rebase, or the session hook.
- No process-id liveness check: signalling a pid is unsafe on Windows.

## Implementation

All code changes sit in `plugins/s/skills/workspace/scripts/store_sync.py`,
inside the delayed mode. The engine scripts stay untouched.

**Token file.** `_token_path` is unchanged. The token body becomes
`"<id> <deadline>"`: `<id>` is the existing `"%d-%d" % (pid, time_ns)` and
`<deadline>` is `repr(time.time() + delay)`. Add `_token_deadline(body)`,
which returns the float after the last space, or None when the body is
missing or malformed.

**Lock file.** `_lock_path(store)` is the token path with `.token` replaced
by `.lock`. Constants: `_LOCK_REFRESH = 10` seconds and `_LOCK_STALE = 60`
seconds.

- `_claim_lock(path, ident)`: `os.open(path, O_CREAT | O_EXCL | O_WRONLY)`
  and write `ident`; return True. On `FileExistsError`, read the file's
  mtime: when it is older than `_LOCK_STALE` (or the file vanished), unlink
  it and try the exclusive create once more; return whether that succeeded.
  A fresh lock returns False.
- `_holds_lock(path, ident)`: the file's content equals `ident`.
- `_release_lock(path, ident)`: unlink the file only when `_holds_lock`.

**`run_delayed(store, delay)`** becomes:

1. Write the token (`<id> <deadline>`). On `OSError`, return 0.
2. `_claim_lock`. When it returns False, return 0 having run no git.
3. Wait loop: read the token body, remember it as `seen`, and take its
   deadline (a malformed body means "now"). While the deadline lies in the
   future, sleep `min(remaining, _LOCK_REFRESH)`, then `os.utime` the lock.
   When `_holds_lock` is false after a sleep, return 0: another helper took
   over. Then re-read and repeat until the deadline has passed.
4. Release the lock. Re-read the token: when it differs from `seen`, claim
   the lock again; on success go back to step 3, otherwise return 0.
5. Integrate and push exactly as today.

Wrap steps 3 and 4 in `try/finally` so an exception releases the lock. The
release-then-re-read order in step 4 closes the race with a helper that
found the lock held and exited: that helper wrote its token before it
checked the lock, so the holder always sees the newer token after releasing.

A helper killed mid-wait leaves its lock for up to 60 seconds. Helpers
started in that window exit without pushing; the next write after it, or the
session hook, pushes the commits. This is accepted.

**Version.** Bump `plugins/s/.claude-plugin/plugin.json` from 0.6.384 to
0.6.385.

## Readiness attestation

### Problem and motivation

Each store commit starts a sleeping helper, so a burst leaves one idle
process per commit, and the requirement's wording is stale.

Evidence:

- `plugins/s/skills/workspace/scripts/store_sync.py:332-360` sleeps the full
  delay in every helper before it compares tokens.
- `plugins/s/skills/build/scripts/spec_common.py` `schedule_store_push`
  starts a helper on every commit and passes `store_repo_key(store_dir)`.
- Capability `shipd-wiki`, requirement `store-push-debounce`, says "passing
  the store directory" and "keyed by the store's absolute path".

### Scope and non-goals

The change covers the helper's delayed mode and one requirement. The engine,
the delay key, and the rebase stay as they are.

Evidence:

- `plugins/s/skills/workspace/scripts/store_sync.py:277-360` holds the whole
  delayed mode.
- `plugins/s/skills/workspace/tests/test_store_sync.py:250-378` holds its
  tests.

### Affected capabilities and files

One capability and three files change.

Evidence:

- Capability `shipd-wiki`, requirement `store-push-debounce` (modified).
- `plugins/s/skills/workspace/scripts/store_sync.py`
- `plugins/s/skills/workspace/tests/test_store_sync.py`
- `plugins/s/.claude-plugin/plugin.json`

### No open task-shaping decision

The lock design, its two constants, and the token format are fixed above.

Evidence:

- `plugins/s/skills/workspace/tests/test_store_sync.py:250-283` isolates the
  temp directory through `TMPDIR`, so lock files are testable.
