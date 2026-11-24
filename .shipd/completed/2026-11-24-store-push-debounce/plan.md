# store-push-debounce
Status: verified
Planned-at: fbc93cb9181732db33c970d689ee6672580dcb5a
Gated-hash: f84df337ccc5

## Idea

Push a workspace or external store to its remote 60 seconds after the last
engine commit, rebasing first when the store has diverged.

### Motivation

Engineers sharing a workspace repo cannot see each other's queue, wiki, and
PRD writes mid-session, because store commits reach the remote only at a
session boundary. A diverged store never pushes at all: the reference
workspace repo sat about 100 commits ahead of its upstream behind one
unmerged commit.

### Details

- After every store auto-commit, the engine starts a detached helper that
  waits `store_push_delay` seconds (default 60), then integrates and pushes.
- A newer write supersedes a waiting helper, so a burst of writes ends in one
  push, 60 seconds after the last write.
- The helper and the `SessionStart` hook rebase local commits onto the
  upstream when the two have diverged, and abort cleanly on a conflict.
- Workspace PRD and initiative writes gain the same scoped auto-commit, so
  they are pushed too.
- The guides tell readers and agents not to push the store by hand.

Affected capabilities: `shipd-wiki` (modified), `shipd-config` (modified),
`shipd-workspace` (modified). Impact:
`plugins/s/skills/workspace/scripts/store_sync.py`,
`plugins/s/skills/build/scripts/spec_common.py`, `config_registry.py`,
`spec_emit.py`, `spec_status.py`, the config example, three guides, and the
plugin version. No new dependency.

### Non-goals

- No change to commit timing: each write still commits at once, scoped.
- No push for the personal memory store; its push stays skill-confirmed.
- No commit or push for an in-repo fallback store.
- No change to autopilot's own store fetch or to `shipd doctor`.

## Implementation

- **The engine schedules; the helper networks.** `spec_common.py` gains
  `schedule_store_push(store_dir, config)`, called by `wiki_autocommit` after
  a commit lands. It starts
  `python3 <plugin>/skills/workspace/scripts/store_sync.py --delayed <store>
  --delay <n>` with `subprocess.Popen`, all three standard streams on
  `DEVNULL`, and `start_new_session=True`, and returns at once. Every
  exception is swallowed. The engine process itself still runs no network
  call, which keeps the constitution's rule intact. Rejected: pushing from
  the engine (breaks the rule); a bash timer script (not stdlib Python).
- **Scheduling gates, all local.** Schedule only when the commit landed,
  `store_sync` resolves true, the caller did not pass `schedule_push=False`,
  and `git -C <store> remote get-url origin` succeeds. The remote probe stops
  the engine test suite from starting helpers for remote-less temp repos.
  `wiki_autocommit` gains the keyword `schedule_push=True`; the two personal
  store call sites pass `False` (`spec_emit.py` wiki emit and
  `spec_status.py` `_wiki_write_autocommit` callers with `--personal`).
- **Debounce by token, not by kill.** The helper writes a unique token
  (`<pid>-<time.time_ns()>`) to `<tempdir>/shipd-store-push-<digest>.token`,
  where `<digest>` is the 16-hex store digest the commit lock already uses.
  It writes through a temp file and `os.replace`. After the sleep it reads
  the file back; a different token means a later helper took over, so it
  exits having run no git. Rejected: a pidfile and `kill`, which can signal
  an unrelated process after pid reuse, or a helper mid-push.
- **One integrate routine.** `store_sync.py` gains `integrate(store)`, used
  by `SessionStart` and the delayed mode: fetch the upstream remote; do
  nothing when the upstream is an ancestor of `HEAD`; `merge --ff-only` when
  `HEAD` is an ancestor of the upstream; otherwise
  `git rebase --autostash @{u}`. A failed rebase runs `git rebase --abort`
  and raises, so no push follows. The rebase runs under the engine's store
  commit lock, renamed to the public `spec_common.store_commit_lock`; the
  push runs outside it. `SessionEnd` stays push-only.
- **Git environment.** Every helper git call keeps the 20-second timeout and
  sets `GIT_TERMINAL_PROMPT=0`, so a missing credential fails fast.
- **Delay key.** `store_push_delay`: a non-negative integer of seconds,
  default 60, scope `repo`, validated like `worktree_idle_minutes`. `0` skips
  the sleep. A malformed value falls back to 60. `store_sync` false disables
  scheduling entirely.
- **Workspace artifact commits.** `emit_prd` and `emit_initiative` call
  `sc.wiki_autocommit(ws_root, [dest_dir], subject, config_anchor=root)`;
  `cmd_initiative_sync` and `cmd_initiative_set_status` call it with the
  brief path. Subjects: `shipd: emit prd <slug>`,
  `shipd: emit initiative <slug>`, `shipd: initiative <slug> status <status>`.
- **Docs go through `/s:document`**, per the repo's AGENTS.md.
- **Version.** Bump `plugins/s/.claude-plugin/plugin.json` by one patch.

Risk: a rebase rewrites unpushed store commits. Guard: only unpushed commits
move, the working tree is autostashed, and a conflict aborts to the prior
state. Risk: many writes leave many sleeping helpers. Guard: each is one idle
process that exits after the delay without running git.

## Questions and answers

### Q1: What should the delayed push do when the store has diverged?
- **Question:** When the workspace store has diverged from its upstream,
  should the delayed push rebase local store commits onto upstream before
  pushing? Options: (1) fetch and rebase, then push; (2) stay
  fast-forward-only and warn. Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Rebase, then push — option 1. A conflict aborts and warns.
- **Queued:** q-store-push-diverged-upstream

### Q2: When should the commit happen?
- **Question:** With a 60-second debounced store push, should the engine keep
  committing each write immediately or debounce the commit too? Options:
  (1) commit immediately, debounce only the push; (2) debounce both.
  Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Commit immediately and delay only the push — option 1.
- **Queued:** q-store-commit-timing-with-delayed-push

### Q3: Should workspace PRD and initiative emits auto-commit?
- **Question:** Should workspace PRD and initiative emits auto-commit like
  wiki writes do? Options: (1) yes, in this change; (2) no.
  Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Yes, include them — option 1.
- **Queued:** q-workspace-prd-initiative-autocommit

## Readiness attestation

### Problem and motivation

Store commits reach the remote only at session boundaries, and a diverged
branch blocks even that, so teammates never see mid-session writes.

Evidence:

- `plugins/s/skills/workspace/scripts/store_sync.py:137-150` pushes only on
  `SessionStart` and `SessionEnd`, after a `merge --ff-only`.
- Capability `shipd-wiki`, requirement `store-sync-hook`, specifies that
  fast-forward-only behaviour.
- `git status -sb` in the reference workspace repo printed
  `main...origin/main [ahead 95, behind 1]`.

### Scope and non-goals

The change covers the debounced push, the rebase, and commits for workspace
PRD and initiative writes; the personal store and in-repo stores stay out.

Evidence:

- Capability `shipd-memory` keeps every personal-store push skill-confirmed;
  it is not edited.
- `plugins/s/skills/build/scripts/spec_common.py:1857-1874` keeps in-repo
  stores commit-free; that function is not edited.

### Affected capabilities and files

Three capabilities and the files below are affected, because the helper, the
engine hook point, the key registry, and the guides each change.

Evidence:

- Capability `shipd-wiki`: `store-sync-hook` (base 0563a85b02d2) modified;
  `store-push-debounce` added.
- Capability `shipd-config`: `store-push-delay-key` added.
- Capability `shipd-workspace`: `workspace-artifact-autocommit` and
  `workspaces-doc-store-push` added.
- Files: `plugins/s/skills/workspace/scripts/store_sync.py:137-150`,
  `plugins/s/skills/build/scripts/spec_common.py:1753,1798`,
  `config_registry.py:316-320`, `spec_emit.py:157-204,433`,
  `spec_status.py:3872,3966-3990`,
  `plugins/s/skills/build/references/shipd.config.example.json:7`,
  `docs/workspaces/teams.md:228`, `docs/customise.md:117`,
  `docs/workspaces/external-stores.md:137`.
- Runnable premise: on a scratch clone of the reference workspace repo,
  `git rebase --autostash <upstream>` → exit 0, 101 commits ahead and 0
  behind afterwards.

### No open task-shaping decision

Every task-shaping decision is settled; none remain.

Evidence:

- Divergence handling (rebase, abort on conflict): settled by the user, Q1.
- Commit timing (immediate commit, delayed push): settled by the user, Q2.
- PRD and initiative commits (included): settled by the user, Q3.
- Helper location outside the engine folder: settled by investigation, the
  constitution's no-network rule and the `store_sync.py` precedent.
- Token debounce and the `store_sync` gate: settled by investigation.
