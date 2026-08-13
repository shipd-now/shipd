# Tasks — plan-enrichment

## 1. Locate verb

- [x] 1.1 [req: locate-verb] Add locate tests to
      `plugins/s/skills/build/tests/test_spec_status.py`: a change in the
      invocation root's `planned/` is found (keyed block with change, root,
      dir, status; exit 0); a change installed only under a simulated
      worktree directory (a .worktrees/member-a tree with its own content
      dir) is found from the main root with `root:` naming the worktree; a
      change present in both roots prints the local block first; an unknown
      change prints a probed-locations error and exits non-zero. Run them
      and observe them fail — the verb does not exist yet.
- [x] 1.2 [req: locate-verb] Implement `cmd_locate` and the `locate`
      subparser in `plugins/s/skills/build/scripts/spec_status.py`: probe
      the invocation root's resolved `planned/` first, then each
      `.worktrees/<name>` entry in sorted name order, resolving the content
      directory per candidate root via `spec_common.specs_dir`; print one
      keyed block per match separated by blank lines; exit 1 with an error
      naming the probed locations when nothing matches; no git, model, or
      network calls. Confirm the 1.1 tests now pass.

## 2. Plan skill enrichment mode

- [x] 2.1 [req: enrichment-mode-activation] In
      `plugins/s/skills/plan/SKILL.md`, add an "Enrichment mode" section:
      when the invocation carries an argument, run `spec_status.py locate`
      on it before any other flow step; a `rejected` result announces
      enrichment mode in one sentence and operates on the located root with
      the fresh-planning flow (investigation digest, depth gate, emission)
      not running; any other located status is reported with its location
      and the skill stops; no match falls through to the normal flow.
- [x] 2.2 [req: enrichment-gap-diagnosis] In the same section of
      `plugins/s/skills/plan/SKILL.md`, document the diagnosis loop: read
      the artifacts via `spec_status.py cat change <change>`, take the
      plan's `## Context insufficient` dot-points as the agenda, resolve
      codebase-answerable findings by editing the installed artifacts in
      the located change directory (refresh stale base hashes against the
      current master, correct dangling task file references, replace
      placeholder markers with repository-grounded decisions), and put only
      repository-unanswerable findings to the user via the existing
      typed-round contract with a context brief.
- [x] 2.3 [req: enrichment-regate] Close the section in
      `plugins/s/skills/plan/SKILL.md` with the re-gate exit: run
      `spec_gate.py <change>` on the located root; exit 0 confirms `ready`
      and hands off with the motivation-led summary; exit 2 presents the
      remaining findings and continues the loop; forbid `set-status` and
      `--force` as enrichment exits — the gate's verdict is the only path
      to `ready`.

## 3. Deliver pointer

- [x] 3.1 [req: deliver-skill] In `plugins/s/skills/deliver/SKILL.md`
      Phase 4, change the "Parked — rejected" pointer from the raw
      `set-status` instruction to invoking `/s:plan <member>` from the
      repo root, noting it locates the parked worktree and runs enrichment
      through to the re-gate.

## 4. Version bump and verification

- [x] 4.1 [req: *] Bump the version in
      `plugins/s/.claude-plugin/plugin.json` from 0.6.2 to 0.6.3.
- [x] 4.2 [req: *] From the repo root run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` and confirm the whole suite is green.
