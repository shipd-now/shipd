## 1. Tests for the three re-entry cases

- [x] 1.1 [req: plugin-worktree-helper] In
      `plugins/s/skills/build/tests/test_worktree.py`, add a test that runs the
      helper twice for the same change in a scratch git repo and asserts the
      second run exits 0, the worktree is still on `change/<change>`, and a file
      written into it between the runs is still present. Run it and observe it
      fail — the second run currently exits 1.
- [x] 1.2 [req: plugin-worktree-helper] In the same file, add a test that creates
      the worktree, removes it with `git worktree remove` leaving the branch, then
      runs the helper again and asserts it exits 0 and recreates the worktree on
      the pre-existing branch. Run it and observe it fail.
- [x] 1.3 [req: plugin-worktree-helper] In the same file, add a test that creates
      `.worktrees/<change>` checked out on a *different* branch, runs the helper,
      and asserts it exits non-zero and leaves that worktree's branch unchanged.
      Run it and observe the current behavior.

## 2. Make the helper idempotent

- [x] 2.1 [req: plugin-worktree-helper] In
      `plugins/s/skills/build/scripts/worktree.sh`, replace the unconditional
      "already exists" failures in the create path with the four-case resolution
      from `plan.md`'s `## Implementation` table: reuse when the worktree exists
      on `change/<change>`; create from the existing branch when only the branch
      exists; create both when neither exists; error only when the worktree exists
      on a different branch. Determine the current branch with `git -C
      .worktrees/<change> rev-parse --abbrev-ref HEAD`.
- [x] 2.2 [req: plugin-worktree-helper] In the same script, keep the printed
      continue message identical in shape across all three success cases (skills
      quote it), adding only a line noting reuse when an existing worktree was
      reused.
- [x] 2.3 [req: plugin-worktree-helper] Confirm the added logic is bash 3.2-safe
      per `.shipd/constitution.md`: no `mapfile`, no associative arrays, no `set -u`,
      no `$'\uXXXX'` escapes. Run `bash -n
      plugins/s/skills/build/scripts/worktree.sh`.
- [x] 2.4 [req: plugin-worktree-helper] Run
      `python3 -m unittest plugins.am.skills.build.tests.test_worktree` (or the
      suite's discovery form) and confirm 1.1–1.3 now pass.

## 3. Drop the caller-side workaround

- [x] 3.1 [req: plugin-worktree-helper] In
      `plugins/s/skills/autopilot/SKILL.md`, replace the "Per-member setup"
      section's `if [ ! -d ".worktrees/<member>" ]` guard and its explanation with
      a plain unconditional invocation, noting the helper is idempotent and
      reuses an existing worktree.

## 4. Verification

- [x] 4.1 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` and confirm the whole engine suite passes.
- [x] 4.2 [req: *] Exercise the real script end to end in a scratch git repo: run
      the helper, run it again, remove the worktree leaving the branch, run it a
      third time — and confirm all three invocations exit 0.
- [x] 4.3 [req: *] Bump the `version` in
      `plugins/s/.claude-plugin/plugin.json` by one patch increment.
