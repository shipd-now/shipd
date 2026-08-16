## 1. Loud reuse notice

- [x] 1.1 [req: loud-branch-reuse] In
      `plugins/s/skills/build/tests/test_worktree.py`, add failing tests: a
      second `worktree.sh my-change` run prints a reuse notice containing
      `ahead 1, behind 1` (fixture: commit once on the change branch, once on
      the base) and no `Created worktree`; running against a pre-existing
      branch with no worktree prints an attach notice with counts and no
      `Created worktree`; a true first creation still prints
      `Created worktree` and no reuse/attach notice. Run them and observe
      them fail.
- [x] 1.2 [req: loud-branch-reuse] In
      `plugins/s/skills/build/scripts/worktree.sh`, resolve the base branch
      once via `git symbolic-ref -q --short HEAD` at the repo root, compute
      ahead/behind via `git rev-list --left-right --count <base>...<branch>`
      (left = behind, right = ahead), and print per-arm messages: reuse arm
      `Reusing existing worktree $WORKTREE on branch $BRANCH (ahead N, behind
      M vs <base>).`, attach arm `Attached worktree $WORKTREE to existing
      branch $BRANCH (ahead N, behind M vs <base>).`, creation arm alone
      keeps `Created worktree …`; detached root HEAD omits the counts. Keep
      the `Next steps` block on all arms and stay bash 3.2-safe. Confirm the
      1.1 tests pass.

## 2. --fresh flag

- [x] 2.1 [req: worktree-fresh-flag] In `test_worktree.py`, add failing
      tests: `worktree.sh epic-close-x --fresh` against a squash-merged
      branch named change/epic-close-x (fixture: branch commit, then `git
      merge --squash` + commit on the base) deletes and recreates the branch
      at the base tip with exit 0; `--fresh` against a branch with an
      unmerged commit exits non-zero, names the branch, and leaves branch and
      commit intact; `--fresh` while the my-change worktree directory already
      exists under the fixture repo's worktrees dir exits non-zero changing
      nothing. Run them and observe them fail.
- [x] 2.2 [req: worktree-fresh-flag] In `worktree.sh`, parse a trailing
      `--fresh` on the create path (mirroring `remove`'s flag loop) and add a
      shared merged-content probe function: merged iff `git merge-base
      --is-ancestor <branch> <base>` succeeds, or `git cherry <base>
      $(git commit-tree <branch>^{tree} -p $(git merge-base <base> <branch>)
      -m probe)` starts with `-`; no merge-base means unmerged. Under
      `--fresh`: existing worktree → error exit 1; unmerged branch → error
      exit 1 naming it; merged branch → `git branch -D`, print the deletion,
      create branch + worktree fresh; detached root HEAD → error. Confirm the
      2.1 tests pass.

## 3. prune-branches verb

- [x] 3.1 [req: prune-merged-change-branches] In `test_worktree.py`, add
      failing tests for `worktree.sh prune-branches`: two squash-merged
      `change/*` branches are deleted and each named on a `pruned:` line,
      exit 0; an unmerged wip branch and an active branch checked out via
      the helper survive, each named on a `kept:` line; a non-`change/*`
      merged branch is untouched; a repo with nothing prunable exits 0. Run
      them and observe them fail.
- [x] 3.2 [req: prune-merged-change-branches] In `worktree.sh`, add the
      `prune-branches` verb to the dispatch beside `remove`: require a repo
      root and a non-detached HEAD (else error), enumerate `git for-each-ref
      --format='%(refname:short)' refs/heads/change`, skip the current branch
      and every branch on a `branch refs/heads/…` line of `git worktree list
      --porcelain` (printing `kept: <branch> (checked out)`), delete merged
      candidates per the shared probe with `git branch -D` printing
      `pruned: <branch>`, print `kept: <branch> (not merged into <base>)`
      otherwise, end with a summary count, exit 0. Bash 3.2-safe. Confirm the
      3.1 tests pass.

## 4. Epic-close consumers

- [x] 4.1 [req: close-out-fresh-branch] In
      `plugins/s/skills/build/tests/test_autopilot.py`'s `_default_sync_fn`
      tests (the faked `_run_command` fixture around line 278), add a failing
      assertion that the `WORKTREE_SH` invocation argv is
      `[WORKTREE_SH, "epic-close-ep", "--fresh"]`.
- [x] 4.2 [req: close-out-fresh-branch] In
      `plugins/s/skills/build/scripts/autopilot.py`'s `_default_sync_fn`,
      change the creation call to `[WORKTREE_SH, slug, "--fresh"]`. Confirm
      the 4.1 test passes.
- [x] 4.3 [req: epic-close-out-derivation] In
      `plugins/s/skills/build/SKILL.md`'s Phase 7 epic-derivation step
      (around line 708), change the creation command to
      `"${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/worktree.sh"
      epic-close-<slug> --fresh` and add one sentence saying the flag
      guarantees the derivation never starts from a stale close-out branch.

## 5. Docs and version

- [x] 5.1 [req: prune-merged-change-branches] In `AGENTS.md`'s Workflow
      section: add one sentence to the after-merge paragraph naming
      `worktree.sh prune-branches` as the way to reclaim merged local
      `change/*` branches, and extend the epic-derivations paragraph to say
      the fresh worktree is created with `--fresh`.
- [x] 5.2 [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` from 0.6.120 to 0.6.121.
- [x] 5.3 [req: *] Verification barrier: run `bash -n
      plugins/s/skills/build/scripts/worktree.sh` and the full engine suite
      `python3 -m unittest discover -s plugins/s/skills/build/tests -v` from
      the repo root; all tests pass.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 72 | 26.4k |
| Edit | 25 | 23.2k |
| (no tool) | 0 | 4.5k |
| Read | 20 | 4.3k |
| Agent | 2 | 722 |
| ToolSearch | 1 | 141 |
| **Total** | 120 | 59.3k |
