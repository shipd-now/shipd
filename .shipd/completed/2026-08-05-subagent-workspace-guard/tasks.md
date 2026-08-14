## 1. Claim branch guard

- [x] 1.1 [req: claim-branch-guard] In
      `plugins/s/skills/build/tests/test_claim_task.py`, add failing tests
      (git fixture repos built with `git init`/`git branch` in temp dirs):
      wrong-branch claim refuses with exit 3 naming both branches and marks
      no task; on-branch claim works; a repo without the `change/<x>` branch
      is unaffected; a non-git dir is unaffected; detached HEAD refuses with
      exit 3; `status`/`next` stay unguarded on the wrong branch; `complete`
      and `release` are guarded like `claim`.
- [x] 1.2 [req: claim-branch-guard] In
      `plugins/s/skills/build/scripts/claim_task.sh`, add
      `require_change_branch()` (branch exists via `git rev-parse --verify
      --quiet refs/heads/change/<change>`; current via `git branch
      --show-current`, empty = mismatch; refusal message to stderr, exit 3)
      and call it from `claim`, `complete`, and `release` before any
      lock/edit; confirm the 1.1 tests pass.

## 2. Contract workspace gate

- [x] 2.1 [req: subagent-workspace-gate] Add
      `plugins/s/skills/build/tests/test_subagent_contract.py` (stdlib):
      failing assertions that `plugins/s/agents/sub-agent.md` contains a
      workspace-gate section heading, the `git rev-parse --abbrev-ref HEAD`
      check requiring `change/<change>`, the stop-and-report-on-mismatch
      rule before any claim/edit, and the paths-inside-the-worktree rule.
- [x] 2.2 [req: subagent-workspace-gate] In
      `plugins/s/agents/sub-agent.md`, add the `## Workspace gate (before
      any claim or edit)` section near the top of the role contract with
      exactly those elements; confirm the 2.1 tests pass.

## 3. Ship

- [x] 3.1 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json`.
- [x] 3.2 [req: *] Verification barrier: run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` without `textual`; the suite passes
      (no `textual` surface is touched by this change).
