# epic-sync-guard
Status: verified
Profile: lite
Theme: developer-experience

## Idea

Epic status writes from the main checkout create uncommitted changes to
tracked files that a protected-main workflow cannot ship — the
workspace-projects close-out hit exactly this: `epic-sync` on main had to be
reverted and redone in a worktree PR. Nothing warns at write time, and no
workflow step codifies the recovery pattern, so the mistake stays silent
until a push fails.

Per the depth-path decisions confirmed with the user, a two-layer fix:

- **CLI warning, never a refusal**: `epic-sync` and `epic-set-status` print
  a one-line stderr warning when they actually modify an epic file in a
  main checkout (`.git` is a directory), naming the file and the
  worktree-PR rule. Worktrees and no-op syncs stay silent.
- **Close-out codified**: the build skill's Phase 7 close-out gains the
  explicit step — when the shipped change carried `Epic:`, run `epic-sync`
  from a fresh `epic-close-<slug>` worktree and ship any status advance as
  an auto-merge PR (no PR when nothing changes). `AGENTS.md` mirrors the
  rule in one line.
- Plugin version bump (0.2.7 → 0.2.8).

### Non-goals

- No refusal/exit-3 behavior and no `--force` flag — repos without branch
  protection must stay friction-free (explicit user decision).
- No guard on plan or initiative verbs: plans are worktree-resident by
  construction, `am/completed/` is immutable, and briefs live outside git.
- No git subprocess — checkout-shape detection stays a stdlib file check.

Affected capabilities: `spec-status` (ADDED), `build-spec-lifecycle`
(ADDED). Impact: `plugins/s/skills/build/scripts/spec_status.py` and
`plugins/s/skills/build/tests/test_spec_status.py`,
`plugins/s/skills/build/SKILL.md`, `AGENTS.md`,
`plugins/s/.claude-plugin/plugin.json`.

## Implementation

- **Detection**: a helper `_is_main_checkout(root)` in `spec_status.py`
  returns `os.path.isdir(os.path.join(root, ".git"))` — a linked worktree's
  `.git` is a file, the main checkout's is a directory (the same stdlib
  distinction `build_report.resolve_project_root` relies on). A root with
  no `.git` at all returns False (not a checkout; nothing to warn about).
- **Warn only on an actual write**: the warning is emitted at the single
  point where the epic file is rewritten — `epic-set-status` always writes;
  `epic-sync` writes only when the derived status differs, so a no-op sync
  stays silent. Message (one line, stderr):
  `Warning: wrote <path> in the main checkout; a protected-main workflow
  must ship this via a worktree PR.` Exit codes unchanged.
- **Build skill close-out**: Phase 7 step 4 in
  `plugins/s/skills/build/SKILL.md` gains the epic derivation instruction
  (worktree `epic-close-<slug>`, `epic-sync`, commit + auto-merge PR only
  when the status line changed, worktree removed either way). Rejected:
  running `epic-sync` inside the change's own build worktree pre-merge —
  the epic's members are only `archived` on main *after* the squash merge,
  so a pre-merge sync derives a stale status.
- **Risk**: stderr noise for repos that commit to main legitimately —
  accepted (one line, informational). Detection misfire inside
  `.worktrees/` is pinned by tests against both fixture shapes (`.git`
  directory vs `.git` file).
