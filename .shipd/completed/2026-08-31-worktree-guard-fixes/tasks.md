## 1. The idle probe fires only on a dirty tree

- [x] 1.1 [req: plugin-worktree-helper] In
      `plugins/s/skills/build/tests/test_worktree.py`, add
      `test_recently_written_clean_worktree_removes` to `RemoveWorktreeTest`:
      create a worktree with `make_worktree`, write a file into it, commit it
      with `git_in` so the tree is clean, and — without calling `age_tree` and
      without `SHIPD_WORKTREE_IDLE_MINUTES` — run `remove my-change`. Assert
      the exit code is 0, the worktree directory is gone,
      `self.worktree_listed(wt)` is false, and the combined output contains
      neither `idle` nor `--force`. Run the file with `python3 -m unittest`
      and observe the new test fail — the idle probe currently refuses.
- [x] 1.2 [req: plugin-worktree-helper] In
      `plugins/s/skills/build/scripts/worktree.sh`, hoist guard 1's
      `git -C "$WORKTREE" status --porcelain` result into a variable (it is
      currently computed inline around line 180) and reuse it for guard 1's
      condition unchanged. Then gate guard 4 (the `find -mmin` idle probe,
      currently around lines 222-227) on that variable being non-empty, so the
      probe runs only while the tree is dirty and contributes no reason on a
      clean tree. Leave the `IDLE` parsing, the `SHIPD_WORKTREE_IDLE_MINUTES`
      default of 30, the `IDLE=0` disable, and the reason wording exactly as
      they are. Confirm the test from 1.1 passes.
- [x] 1.3 [req: plugin-worktree-helper] Update the comment above guard 4 in
      `plugins/s/skills/build/scripts/worktree.sh` to state that the probe
      runs only on a dirty tree and is therefore non-decisive — a dirty tree
      already refuses through guard 1 — so it contributes an extra reason
      rather than a standalone refusal. Also update the header comment block
      near line 13 that documents the idle window, so it no longer implies the
      probe fires on a clean worktree.
- [x] 1.4 [req: plugin-worktree-helper] Run `python3 -m unittest` over
      `plugins/s/skills/build/tests/test_worktree.py` and confirm every
      existing removal test still passes — in particular
      `test_clean_cold_removes`, `test_idle_minutes_zero_disables_activity_for_cold_case`,
      `test_dirty_tree_refuses`, and `test_unshipped_planned_refuses`.

## 2. prune-branches sees a squash onto a moved base

- [x] 2.1 [req: prune-merged-change-branches] In
      `plugins/s/skills/build/tests/test_worktree.py`, add a helper to
      `WorktreeScriptTestBase` — `add_origin()` — that creates a bare
      repository in a second temp directory, runs
      `git remote add origin <path>`, and pushes the base branch, so tests can
      exercise remote-tracking refs entirely offline. Register its temp
      directory for cleanup in `tearDown`.
- [x] 2.2 [req: prune-merged-change-branches] In the same file, add
      `test_branch_merged_onto_a_moved_base_is_pruned` to
      `PruneBranchesTest`: call `add_origin()`, create a change branch `change/<merged>` editing a
      file, push it, return to the base and commit an unrelated edit to that
      same file, then squash-merge that branch's content on top so the content
      probe cannot match its patch. Delete the branch from the bare origin and
      run `prune-branches`. Assert the branch is gone, a `pruned:` line names
      it, and the exit code is 0. Run the file and observe it fail.
- [x] 2.3 [req: prune-merged-change-branches] In the same file, add
      `test_branch_with_a_surviving_remote_ref_is_kept`: with `add_origin()`,
      create and push an unmerged change branch `change/<wip>`, then run
      `prune-branches` and
      assert the branch still exists, a `kept:` line names it, and the exit
      code is 0.
- [x] 2.4 [req: prune-merged-change-branches] In
      `plugins/s/skills/build/scripts/worktree.sh`, add a
      `branch_remote_ref_gone` helper beside `branch_is_merged`: given a
      branch name, return 0 when `git rev-parse --verify --quiet
      "refs/remotes/origin/<branch>"` finds nothing, and 1 when the ref
      exists. Keep it silent on stdout.
- [x] 2.5 [req: prune-merged-change-branches] In `cmd_prune_branches`
      (currently around line 264), before the branch loop, refresh the
      remote-tracking refs once: when `git remote` names at least one remote,
      run `git fetch --prune --quiet` and record whether it succeeded; when no
      remote is configured, or the fetch exits non-zero, record that the
      remote probe is unavailable. Print nothing on success; on a failed
      fetch print one line noting that remote refs could not be refreshed and
      that pruning falls back to the content probe.
- [x] 2.6 [req: prune-merged-change-branches] In the same loop, when
      `branch_is_merged` reports not-merged, consult `branch_remote_ref_gone`
      only if the remote probe is available, and delete the branch when it
      returns 0. Keep the existing `kept:`/`pruned:` line format and the
      checked-out and base-branch exclusions unchanged; a branch kept because
      both probes declined keeps today's `(not merged into <base>)` reason.
      Confirm the tests from 2.2 and 2.3 pass.
- [x] 2.7 [req: prune-merged-change-branches] Confirm the remote-less path is
      unchanged: run `python3 -m unittest` over
      `plugins/s/skills/build/tests/test_worktree.py` and check that
      `test_squash_merged_branches_are_pruned_and_listed` and
      `test_nothing_to_prune_exits_zero` — both of which run in a repository
      with no remote — still pass with no error about a missing remote.

## 3. Verification and version

- [x] 3.1 [req: *] Run the whole stdlib engine suite,
      `python3 -m unittest discover -s plugins/s/skills/build/tests`, with
      neither `textual` nor `pydantic` installed, and confirm it passes.
- [x] 3.2 [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` to the next patch version above
      whatever it currently holds on this branch.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 89 | 14.4k |
| (no tool) | 0 | 2.1k |
| SendMessage | 1 | 1.9k |
| Agent | 2 | 767 |
| Edit | 21 | 410 |
| Read | 16 | 79 |
| ToolSearch | 1 | 2 |
| **Total** | 130 | 19.6k |
