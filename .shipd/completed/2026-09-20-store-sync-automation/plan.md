# store-sync-automation
Status: verified

## Idea

Automate the workspace store's git sync so durable knowledge never strands on
one machine, and serialize the engine's auto-commit so a concurrent write never
loses its commit.

### Motivation

The engine auto-commits every store write locally but never pushes, so this
workspace sits twelve committed writes ahead of its remote with no surface
reporting it. The write path also takes no lock, so two agents writing at once
race git's `index.lock` and the loser's write stays uncommitted.

### Details

- Add two boolean config keys, `store_autocommit` and `store_sync`, both
  defaulting true.
- Serialize `wiki_autocommit`'s add-and-commit pair behind an exclusive lock.
- Ship a session-boundary hook that pulls and pushes the resolved store repo.
- Add a `store-sync` doctor check reporting the store's pending commits.
- Document all of it in the customisation guide and the teams guide.

Affected capabilities: `shipd-config`, `shipd-wiki`, `guardrail-hook`,
`shipd-cli`, `shipd-doctor`, `shipd-workspace` (all modified). Impact:
`plugins/s/skills/build/scripts/spec_common.py`, `plugins/s/bin/shipd`,
`plugins/s/hooks/hooks.json`, a new
`plugins/s/skills/workspace/scripts/store_sync.py`,
`plugins/s/skills/build/references/shipd.config.example.json`,
`docs/customise.md`, `docs/workspaces/teams.md`,
`docs/workspaces/getting-started.md`, `docs/workspaces.md`,
`.github/workflows/ci.yml`.
No new dependencies.

### Non-goals

- The in-repo fallback store keeps its exception: while the content directory
  resolves in-repo with no `store_root`, engine writes still never auto-commit.
- No engine verb gains networked git. Only the hook script reaches the network.
- No merge-conflict resolution for `queue.md` or `index.md`. The hook
  fast-forwards or warns.
- No change to `doctor-verb`'s required-check roster.

## Implementation

- **Two keys, not one.** `store_autocommit` gates the local commit;
  `store_sync` gates the hook's networked git. The `store-autocommit`
  requirement's own text says the engine "SHALL never push, pull, or fetch",
  so one key governing both would contradict the requirement defining it.
  Rejected: a single key. Follows the `voice` and `worktree_sweep` precedent —
  one dedicated boolean per gated path.
- **Both keys tolerate a bad value.** A non-boolean resolves to the built-in
  default rather than raising, mirroring `spec_common.worktree_sweep`
  (`spec_common.py:551`).
- **The hook lives outside the engine scripts.** `.shipd/constitution.md` bars
  network access under `plugins/s/skills/build/scripts/`, so
  `store_sync.py` lands at `plugins/s/skills/workspace/scripts/`, beside the
  `voice_digest.py` precedent. It stays stdlib-only and fail-soft: every git
  call carries a timeout, every failure prints one stderr line and exits 0.
- **Fast-forward only on the way in.** SessionStart fetches then merges
  `--ff-only`. A rebase would rewrite commits under a concurrently running
  agent sharing the same store working tree. A non-fast-forward warns and
  leaves the tree alone; the doctor line then reports the divergence.
- **SessionStart also pushes.** Pushing at both boundaries means a crashed or
  killed session self-heals on the next start, rather than stranding its
  commits until someone notices.
- **The hook never touches the working repository.** It operates only on a
  resolved workspace or external store inside a git work tree with an `origin`
  remote. Where the store resolves in-repo it does nothing, so the hook can
  never push a half-finished source branch.
- **The lock degrades, never blocks.** `wiki_autocommit` takes an exclusive
  lock on a file beside the store before `git add`, releasing after `git
  commit`. Where locking is unavailable or the lock cannot be taken, the write
  proceeds exactly as today — the lock is an improvement on a race, not a new
  failure mode.
- **The doctor check adds no roster entry.** It probes `git rev-list --count
  --left-right @{u}...HEAD` locally and never fetches. Verified by running it
  against this workspace: output `0\t12`, exit 0. It warns when out of sync and
  reports `ok` otherwise, exactly as `check_store` already warns on a stranded
  folder without appearing in `doctor-verb`'s roster
  (`verified/shipd-doctor#doctor-store-line`). Rejected: extending
  `doctor-verb` — a MODIFIED entry replaces wholesale, so it would mean
  restating seventeen scenarios for one added clause.
- **The teams guide is at its cap.** `docs/workspaces/teams.md` is exactly 150
  lines, its how-to limit. Its "Concurrency expectations" section currently
  asserts the engine "takes no locks and runs no networked git", which this
  change falsifies; rewriting it must not grow the file.

Risk: a push firing at session start could surprise someone mid-review. Guarded
by `store_sync: false` and by the hook's restriction to the store repo, which
carries only knowledge artifacts.

## Questions and answers

### Q1: Does `store_autocommit` make the in-repo fallback store commit too?
- **Question:** Should a new `store_autocommit` key (boolean, default true)
  make the repo-local fallback store auto-commit engine writes, reversing the
  documented in-repo exception? Options: (a) the key applies uniformly, so an
  in-repo store now commits; (b) the key gates the workspace/external-store
  behaviour only, preserving the exception. Recommendation: (a).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option (b). The verified masters state the exception's rationale
  as a standing division of labour — the engine commits only where it owns the
  store, and committing in-repo artifacts belongs to the skill and PR workflow.
  Reversing that under a new key would make the engine commit into the user's
  own working repo by default, a widening this repository puts behind an
  explicit opt-in rather than a default. Dropping the exception later should be
  an express amendment to `store-autocommit` and `wiki-autocommit`, not a side
  effect of introducing the key.
- **Cited:** verified/shipd-config, verified/shipd-wiki

### Q2: One key for commit and sync, or two?
- **Question:** Should the session-boundary store sync be gated by its own
  config key, or ride `store_autocommit`? Options: (a) a separate `store_sync`
  boolean, default true, gating the hook's network step only; (b) one key
  gating both. Recommendation: (a).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option (a). The `store-autocommit` requirement writes "never
  push, pull, or fetch" into the key's own contract, so overloading that key
  with a network sync would put it in contradiction with the requirement that
  defines it. The `voice` key sets the countervailing precedent — one dedicated
  boolean gating one hook and nothing else — and `worktree_sweep` gates its own
  path the same way. Both new keys register in the recognized-keys constant and
  the copyable config reference.
- **Cited:** verified/shipd-config#store-autocommit,
  verified/shipd-config#voice-key, verified/shipd-config#worktree-sweep-keys
