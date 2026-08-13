# Tasks — initiative-skill

## 1. Skill, docs, and version

- [x] 1.1 [req: initiative-workflow-skill, initiative-attachment] Author
      `plugins/s/skills/initiative/SKILL.md`, modeled on the structure of
      `plugins/s/skills/epic/SKILL.md` (frontmatter with name `initiative`
      and a trigger-phrase description; codebase/workspace-first rule; one
      batched question round; explicit ending contract). Cover the four
      verbs exactly as the delta spec and `plan.md`'s Implementation pin
      them: `new` (interview → brief at `Status: open` written directly to
      the workspace, lint via
      `python3 plugins/s/skills/build/scripts/spec_lint.py --initiative <slug>`),
      `list` (via `spec_status.py workspace-show` / `initiative-show`),
      `review` (tick user-confirmed outcomes, then
      `spec_status.py initiative-sync <slug>`), `set` (worktree
      `initiative-set-<epic>` + auto-merge PR editing the epic's
      `Initiative:` line, `--epic` lint before shipping, refusal rule for
      epic-member changes), and the shared no-workspace stop.
- [x] 1.2 [P2] [req: initiative-workflow-skill] Update `AGENTS.md`'s spec
      lifecycle sentence to name the full skill set: `/s:plan`, `/s:build`,
      `/s:status`, `/s:epic` (decompose features), `/s:initiative`
      (workspace initiatives).
- [x] 1.3 [P2] [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version
      `0.2.6` → `0.2.7`.

## 2. Verification

- [x] 2.1 [req: *] Run the full engine test suite
      (`python3 -m unittest discover -s plugins/s/skills/build/tests`) and
      `python3 plugins/s/skills/build/scripts/spec_lint.py initiative-skill`;
      confirm `plugins/s/skills/initiative/SKILL.md` carries valid
      frontmatter (`name:`, `description:`) matching the sibling skills;
      everything green.
