# Tasks

## 1. Autopilot end-state classification (engine + tests)

- [x] 1.1 [req: pipeline-stage-execution] In
      `plugins/s/skills/build/tests/` (the autopilot test module), add a test:
      when `drive_member` completes the pipeline with the member's worktree
      present and `_pr_url` reports a PR that exists but is **not** merged, the
      returned `MemberResult` is `outcome="needs_human"`, `stage="merge"`,
      carries the PR URL and the last session id, and is **not** `shipped`. Keep
      the existing merged-PR case asserting `shipped`. Run and observe the new
      case fail.
- [x] 1.2 [req: pipeline-stage-execution] In
      `plugins/s/skills/build/scripts/autopilot.py`, change `drive_member`'s
      final resolution (currently
      `return _finish(MemberResult(outcome="shipped", pr_url=url, merged=merged))`
      near line 615): when the worktree is present and `merged` is false, return
      a needs-human park at stage `merge` (PR URL + `last_session_id` in the
      reason/fields) via the existing `_finish`/`MemberResult` machinery; keep
      `shipped` only when `merged` is true. Leave the vanished-worktree path
      (`_resolve_vanished`) unchanged. Confirm 1.1 passes.
- [x] 1.3 [req: pipeline-stage-execution] Run the full stdlib suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests` from the
      worktree root) and fix any autopilot/report test that assumed an unmerged
      PR was `shipped`.

## 2. Build skill ship/watch prose

- [x] 2.1 [req: ship-changes-as-prs] In `plugins/s/skills/build/SKILL.md`
      Phase 6 (Merge & archive), after the `gh pr merge --auto` block, add the
      post-arm mergeability check: read `mergeStateStatus` once
      (`gh pr view --json mergeStateStatus`); if not `CLEAN`/`UNSTABLE`, merge
      `origin/main` in the worktree and re-push, re-posting the semantic-review
      gate on the new head — or, on a non-trivial conflict, surface a blocker
      (an unattended autopilot member parks instead of prompting). State that
      arming auto-merge is not proof of merge.
- [x] 2.2 [req: ship-changes-as-prs] In `plugins/s/skills/build/SKILL.md`
      Phase 7 (close-out), specify the watch: poll this PR's `state` and
      `mergeStateStatus` together; act on a `DIRTY`/`BEHIND`/`BLOCKED`
      transition within a poll cycle exactly like `MERGED` ends the watch; wait
      for this PR's `MERGED` before pruning the worktree, pulling `main`, and
      running the epic derivation; never block one change's close-out on another
      PR's state.
- [x] 2.3 [req: ship-changes-as-prs] In `plugins/s/skills/build/SKILL.md`
      (Phase 5/6), add the guardrail: a review finding either blocks the
      original PR before merge or is planned as a new change against current
      `main` — never a follow-up PR on an already-squash-merged branch.

## 3. Ship gate

- [x] 3.1 [req: *] Bump the version in
      `plugins/s/.claude-plugin/plugin.json` (this change touches
      `plugins/s/`).
- [x] 3.2 [req: *] Verification barrier: `python3 -m unittest discover -s
      plugins/s/skills/build/tests` passes without `textual`; the `SKILL.md`
      Phase 6/7 prose reads coherently end-to-end (arm → check → watch →
      wait-for-merge → close-out).
