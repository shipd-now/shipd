# worktree-guard-carveout
Status: verified

## Idea

Teach `worktree.sh remove`'s unshipped-change guard to ignore a planned
change whose content is tracked byte-identically on the base branch — base
content is not the worktree's own work.

### Motivation

The remove guard flags every directory under a worktree's
`.shipd/planned/`, so a planned change committed to the base branch itself
(today, `getting-started-docs`, on main since PR #46) fires in every
worktree and forces `--force` on every close-out — three build agents
flagged the false positive independently during the harness-install epic.

### Details

- One new predicate in `plugins/s/skills/build/scripts/worktree.sh`'s
  `cmd_remove` guard #2: skip a planned dir that is tracked, locally clean,
  and identical to the base branch.
- Tests in `plugins/s/skills/build/tests/test_worktree.py`; plugin version
  bump.

Affected capabilities: `build-spec-lifecycle` (modified —
`plugin-worktree-helper`). Impact:
`plugins/s/skills/build/scripts/worktree.sh`,
`plugins/s/skills/build/tests/test_worktree.py`,
`plugins/s/.claude-plugin/plugin.json`. No new dependencies; bash-only.

### Non-goals

- No change to the dirty-tree, claims/lock, or idle-window guards — the
  claims guard in particular keeps scanning every planned dir, base-tracked
  or not (a `[~]` mark is live coordination wherever it sits).
- No new flags, no configuration key — the carve-out is automatic and
  fail-closed.
- No change to the create/`--fresh`/`prune-branches` verbs.

## Implementation

- **The predicate (guard #2 only):** for each `planned/<name>/` directory,
  skip the "unshipped change" reason when **all three** hold, each checked
  with git against the worktree:
  1. tracked — `git -C "$WORKTREE" ls-files -- "<rel>"` prints at least
     one path (an untracked-only dir is never base content);
  2. locally clean — `git -C "$WORKTREE" status --porcelain -- "<rel>"`
     prints nothing;
  3. identical to base — `git -C "$WORKTREE" diff --quiet "$BASE" --
     "<rel>"` exits 0.
  Any check failing → the guard fires exactly as today.
- **Base resolution:** reuse the existing `resolve_base_branch` helper
  (worktree.sh:57 — the root checkout's currently checked-out branch,
  resolved once, no `origin/HEAD` assumption). Resolve it once in
  `cmd_remove` before the guard loop, from the repository root the verb
  already requires. **Fail closed:** when the base resolves empty (detached
  root HEAD) or names the worktree's own branch, apply no carve-out — every
  planned dir guards as today. Rejected: consulting `origin/main` — the
  helper's contract assumes nothing beyond git itself (no remote may
  exist).
- **Why the change's own work still guards:** `planned/<change>/` on
  branch `change/<change>` is absent from the base branch, so check 3
  fails (diff non-empty) — the carve-out cannot swallow genuinely
  unshipped work.
- **Shell discipline:** same bash the script already uses (arrays are
  already present); the three checks are plain `git -C` invocations with
  no GNU-only flags, keeping the macOS/BSD compatibility the file's
  comments already commit to.
- **Version bump:** `plugins/s/.claude-plugin/plugin.json` to the next
  patch above the branch's post-base-merge value.

Risk: a planned change deliberately committed to base *and* meant to be
worked on in this worktree next would no longer block removal — accepted:
the worktree can be recreated with one idempotent `worktree.sh <change>`
invocation, and the other guards (claims, mtime, dirty) still catch active
work on it.
