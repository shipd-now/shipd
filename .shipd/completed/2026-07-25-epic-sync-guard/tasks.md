# Tasks — epic-sync-guard

## 1. CLI warning

- [x] 1.1 [req: main-checkout-epic-write-warning] Add failing tests in
      `plugins/s/skills/build/tests/test_spec_status.py`: with an epic
      fixture whose temp root carries a `.git` **directory**,
      `epic-set-status active` succeeds (exit 0) and stderr contains a
      one-line warning naming the epic file; the same write with a `.git`
      **file** at the root emits no warning; `epic-sync` on a main-checkout
      fixture whose epic already carries the derived status writes nothing
      and emits no warning; a root with no `.git` at all emits no warning.
- [x] 1.2 [req: main-checkout-epic-write-warning] In
      `plugins/s/skills/build/scripts/spec_status.py`, add
      `_is_main_checkout(root)` (`os.path.isdir(os.path.join(root, ".git"))`)
      and emit the warning line
      `Warning: wrote <path> in the main checkout; a protected-main
      workflow must ship this via a worktree PR.` to stderr at the single
      epic-file write point, per the plan's Implementation (set-status
      always writes; sync only on a derived change). Confirm the 1.1 tests
      pass.

## 2. Workflow codification

- [x] 2.1 [P2] [req: epic-close-out-derivation] In
      `plugins/s/skills/build/SKILL.md`, extend Phase 7's close-out step:
      after the merge and pull, when the shipped change's plan carried
      `Epic: <slug>`, create `scripts/worktree.sh epic-close-<slug>`, run
      `spec_status.py epic-sync <slug>` there, and — only if the epic's
      status line changed — commit and ship it as an auto-merging PR
      (reporting the full PR URL); otherwise remove the worktree with no
      PR. State plainly that the derivation never runs from the main
      checkout and never pre-merge.
- [x] 2.2 [P2] [req: epic-close-out-derivation] Add one line to
      `AGENTS.md`'s Workflow section (after the "After merge" paragraph):
      epic status derivations (`epic-sync`/`epic-set-status`) on merged
      epics run in a fresh `epic-close-<slug>` worktree and ship as a PR,
      never from the main checkout.
- [x] 2.3 [P2] [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version
      `0.2.7` → `0.2.8`.

## 3. Verification

- [x] 3.1 [req: *] Run the full engine test suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) and
      `python3 plugins/s/skills/build/scripts/spec_lint.py epic-sync-guard`;
      everything green.
