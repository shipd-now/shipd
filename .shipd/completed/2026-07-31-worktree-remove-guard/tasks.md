# Tasks — worktree-remove-guard

## 1. The remove verb

- [x] 1.1 [req: plugin-worktree-helper] In `plugins/s/skills/build/tests/test_worktree.py`, add failing subprocess tests for `remove`: clean-and-cold worktree removes (exit 0, gone, branch prunable); dirty tree refuses (exit 2, reason named, still present); unshipped `.shipd/planned/` change refuses; a `[~]` claim in a planned tasks.md refuses; a `.tasks.lock` dir refuses; a file freshly touched (set via `os.utime`, no sleeping) refuses on the recent-activity guard; a worktree failing several guards lists every reason; `SHIPD_WORKTREE_IDLE_MINUTES=0` disables the activity guard for the cold case; `--force` on a dirty tree removes and echoes the overridden guard; unknown change exits 1.
- [x] 1.2 [req: plugin-worktree-helper] Implement `remove <change> [--force]` in `plugins/s/skills/build/scripts/worktree.sh` per the plan (guard order dirty → unshipped → claims/lock → recent activity, accumulated refusal report, exit codes 0/2/1, BSD/GNU-compatible mtime probe, `git worktree remove` + `git worktree prune` on success), staying bash-3.2-safe and `bash -n`-clean. Tests from 1.1 pass.

## 2. Wiring and docs

- [x] 2.1 [req: plugin-worktree-helper] Swap both `git worktree remove` call sites in `plugins/s/skills/build/SKILL.md` (post-merge close-out and the epic-close no-op path) to the plugin-path `remove` verb, update `AGENTS.md`'s post-merge instruction likewise, and bump `plugins/s/.claude-plugin/plugin.json` one patch version.

## 3. Verification

- [x] 3.1 [req: *] Barrier: engine unittest suite green; `bash -n` clean on the helper; library lint clean; live drive in a scratch git repo — create a worktree, verify `remove` refuses while a file is fresh and a claim is marked, then age the mtimes, clear the claim, and verify it removes clean; repo-wide grep confirms no live `git worktree remove` instruction remains in skills or AGENTS.md.
