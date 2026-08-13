# Tasks — onboard-tour

## 1. Chapter library (docs are content, not grammar)

- [x] 1.1 [P1] [req: onboarding-docs-library] Write
      `docs/onboarding/01-concepts.md`: why spec-driven development (specs as
      the source of truth, LLM-free engine), the hierarchy Initiative → Epic
      → Change → tasks with Theme as an orthogonal tag, and where each level
      lives on disk. Point at `am/README.md` and `AGENTS.md`.
- [x] 1.2 [P1] [req: onboarding-docs-library] Write
      `docs/onboarding/02-artifacts.md`: the `am/` layout
      (verified/planned/completed), the lean artifact set (`plan.md` with
      Idea/Non-goals/Implementation, delta specs, `tasks.md` with `[req:]`
      tags), header metadata (Status/Profile/Epic/Initiative/Theme), and the
      five-status lifecycle. Narrate; link `am/README.md` for grammar.
- [x] 1.3 [P1] [req: onboarding-docs-library] Write
      `docs/onboarding/03-planning.md`: the `/s:plan` flow — codebase-first
      investigation, the depth gate (fast vs depth path), question rounds,
      emission, self-review, lint gate, promotion to ready.
- [x] 1.4 [P1] [req: onboarding-docs-library] Write
      `docs/onboarding/04-building.md`: the `/s:build` flow — orchestrator
      vs builder tiers, the task coordinator and `[P<n>]` groups, the
      no-guessing rule, verification, the adversarial validator, merge and
      archive, the build report.
- [x] 1.5 [P1] [req: onboarding-docs-library] Write
      `docs/onboarding/05-scaling.md`: epics (Introduction-first document,
      stub table, epic status derivation), initiative briefs
      (open/achieved/dropped, requirements as outcomes), and the workspace
      (marker/registry, projects, `Project:` scoping, CI-safe resolution).
- [x] 1.6 [P1] [req: onboarding-docs-library] Write
      `docs/onboarding/06-workflow.md`: one change = one worktree = one
      branch = one auto-merging PR, the plugin snapshot and version-bump
      rule, the statusline, and where the hands-on sandbox session goes
      next. Each chapter (1.1–1.6) opens with a "what you'll learn" lead and
      ends with its authoritative references.

## 2. Skill and retirement

- [x] 2.1 [req: onboard-tour-skill, sandbox-hands-on] Author
      `plugins/s/skills/onboard/SKILL.md`: frontmatter (name `onboard`,
      description with trigger phrases like "onboarding", "tour", "how does
      shipd work", "/s:onboard"); the chapter menu (full path
      recommended first) and per-chapter loop (read the numbered file from
      `docs/onboarding/`, teach conversationally, illustrate from the live
      repo where features exist, checkpoint with continue/re-explain/jump/
      stop); and the sandbox session exactly per the plan's Implementation
      (scratchpad-or-mktemp scaffold, `git init`, toy `greeter` capability,
      guided toy change through lint/status/claim/merge via absolute plugin
      script paths, cleanup offer, never touching the real repo).
- [x] 2.2 [P2] [req: onboard-tour-skill] Delete
      `plugins/s/commands/hello.md`.
- [x] 2.3 [P2] [req: *] Bump `plugins/s/.claude-plugin/plugin.json` to one
      patch version above the higher of the worktree's current value and
      `origin/main`'s value at this moment (expected: `0.2.5` → `0.2.6`).

## 3. Verification

- [x] 3.1 [req: *] Run the full engine test suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) and
      `python3 plugins/s/skills/build/scripts/spec_lint.py onboard-tour`;
      confirm `plugins/s/commands/hello.md` no longer exists, all six
      chapter files exist, and `plugins/s/skills/onboard/SKILL.md` has
      valid frontmatter; everything green.
