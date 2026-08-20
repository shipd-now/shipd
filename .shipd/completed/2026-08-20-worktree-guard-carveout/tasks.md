## 1. Guard carve-out

- [x] 1.1 [req: plugin-worktree-helper] Extend
      `plugins/s/skills/build/tests/test_worktree.py` (unittest style, the
      file's existing temp-repo fixtures) with the four new scenarios:
      a planned change committed on the base branch and checked out
      unmodified in an otherwise clean, idle worktree removes with exit 0;
      the same with one file under that planned dir edited in the worktree
      refuses with the unshipped-change reason; the same with a `[~]` mark
      committed in the base-tracked tasks.md refuses with the task-claim
      reason; the same with the root checkout's HEAD detached refuses with
      the unshipped-change reason (no carve-out without a base). Use
      `SHIPD_WORKTREE_IDLE_MINUTES=0` where the fixtures already do to
      bypass the mtime guard. Run and observe the first and fourth fail —
      the carve-out does not exist yet.
- [x] 1.2 [req: plugin-worktree-helper] In
      `plugins/s/skills/build/scripts/worktree.sh` `cmd_remove`: resolve
      the base once via the existing `resolve_base_branch` before the
      guard loop; in guard #2's loop, compute each planned dir's
      worktree-relative path and skip its reason only when the base is
      non-empty, differs from the worktree's branch, and all three checks
      pass — `git -C "$WORKTREE" ls-files -- "<rel>"` non-empty,
      `git -C "$WORKTREE" status --porcelain -- "<rel>"` empty, and
      `git -C "$WORKTREE" diff --quiet "$BASE" -- "<rel>"` exit 0. Leave
      guards #1, #3, and #4 untouched. The 1.1 tests pass.
- [x] 1.3 [req: *] Run the CI suite command
      `python3 -m unittest discover -s plugins/s/skills/build/tests -v`
      without `textual`/`pydantic` installed and observe all tests pass.

## 2. Ship the snapshot

- [x] 2.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` `version` to
      the next patch above the branch's post-base-merge value.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Write | 2 | 8.5k |
| Bash | 29 | 8.0k |
| Edit | 7 | 6.6k |
| (no tool) | 0 | 4.0k |
| Agent | 2 | 1.7k |
| Read | 9 | 1.1k |
| **Total** | 49 | 29.9k |
