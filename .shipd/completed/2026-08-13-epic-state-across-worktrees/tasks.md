## 1. Tests for worktree-aware derivation

- [x] 1.1 [req: epic-status-verbs] In
      `plugins/s/skills/build/tests/test_spec_status.py`, add a test building a
      scratch repo whose epic lists a member with no change under the root's
      `planned/` but a `ready` change under `.worktrees/<member>/`'s planned
      directory, and assert `_member_state(root, slug)` returns `ready`. Run it
      and observe it fail — it returns `unplanned` today.
- [x] 1.2 [req: epic-status-verbs] In the same file, add a test where the same
      slug exists under both the invocation root's `planned/` and a worktree's,
      with different plan statuses, and assert the invocation root's status is
      the one returned.
- [x] 1.3 [req: epic-status-verbs] In the same file, add a test asserting a slug
      present under neither the root nor any worktree still returns `unplanned`.
- [x] 1.4 [req: epic-status-verbs] In the same file, add a test with a worktree
      whose content-directory configuration is unreadable (an invalid
      `.shipd-config.json`), asserting derivation skips that worktree and returns
      without raising.

## 2. Make the probe worktree-aware

- [x] 2.1 [req: epic-status-verbs] In
      `plugins/s/skills/build/scripts/spec_status.py`, rewrite `_member_state`
      to build its candidate list as the invocation root followed by each
      `.worktrees/<name>` directory in sorted name order (mirroring `cmd_locate`
      at the same file), resolving each candidate's content directory with
      `sc.specs_dir(candidate)` and skipping a candidate that raises
      `sc.ConfigError`.
- [x] 2.2 [req: epic-status-verbs] In the same function, evaluate each candidate
      whole and in order: return `archived` when that candidate has a matching
      `completed/*-<slug>/`; else return that candidate's plan status when it has
      `planned/<slug>/`; else continue to the next candidate. Return `unplanned`
      only when every candidate misses. Confirm tasks 1.1–1.4's tests now pass.
- [x] 2.3 [req: epic-status-verbs] Update `_member_state`'s docstring to state
      the candidate order and the first-hit-wins rule, so the next reader does
      not reintroduce a root-only probe.

## 3. Verification

- [x] 3.1 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` and confirm the whole engine suite passes.
- [x] 3.2 [req: *] From the repository root, run `python3
      plugins/s/skills/build/scripts/spec_status.py epic-show shipd-port` and
      confirm every member now reports `ready` rather than `unplanned`.
- [x] 3.3 [req: *] From the repository root, run `python3
      plugins/s/skills/build/scripts/autopilot.py shipd-port --dry-run` and
      confirm the seven members now appear as `skipped:    <member>  (ready)`
      rather than in the `Member order (risk ascending):` block.
- [x] 3.4 [req: *] Confirm the epic's own status is unchanged: run `python3
      plugins/s/skills/build/scripts/spec_status.py epic-show shipd-port` and
      check its first line still reads `shipd-port: ready`.
- [x] 3.5 [req: *] Bump the `version` in
      `plugins/s/.claude-plugin/plugin.json` by one patch increment.
