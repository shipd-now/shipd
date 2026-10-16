## 1. Version

- [x] 1.1 [req: pr-callers] Bump `version` in `plugins/s/.claude-plugin/plugin.json` to one patch above the value `main` carries.

## 2. Tests first

- [x] 2.1 [req: pr-config-key] Add `resolve_pr` tests to `plugins/s/skills/build/tests/test_spec_common.py` beside the `resolve_room` tests: defaults, workspace layering, and each bad-member case. Run them and observe the failures.
- [x] 2.2 [req: pr-title-render] Add `plugins/s/skills/pr/tests/test_pr_title.py` (stdlib `unittest`): the three title scenarios, empty-title exit 1, `{change}` from `plugins/s/change/<slug>`.
- [x] 2.3 [req: pr-skill-writes, pr-callers] Add `plugins/s/skills/pr/tests/test_pr_skill.py`, modelled on `plugins/s/skills/room/tests/test_room_skill.py`: the skill strings, no `git push` or `gh pr merge`, no `gh pr create --fill` under `plugins/s` (excluding tests) or in `AGENTS.md`, `/s:pr --draft` in build's draft section, the three registrations, and `harness_bodies.render("pr", ())`. Run it and observe the failures.

## 3. Config

- [x] 3.1 [req: pr-config-key] In `spec_common.py` add `PR_KEY = "pr"`, add `"pr"` to `RECOGNIZED_CONFIG_KEYS` (alphabetical, after `post-worktree-scripts`), and write `resolve_pr(root)` after `resolve_pr_mode`, in the style of `resolve_room`.
- [x] 3.2 [req: pr-config-key] Add a `// pr` entry to `plugins/s/skills/build/references/shipd.config.example.json`, a row to the `docs/customise.md` key table, and a "PR title" section after "PR mode" in `.shipd/README.md`. Run `test_config_sample.py` and the customise-guide drift test.

## 4. Skill

- [x] 4.1 [req: pr-title-render] Write `plugins/s/skills/pr/scripts/pr_title.py` per the plan's Title decision. Run `test_pr_title.py` until it passes.
- [x] 4.2 [req: pr-skill-writes] Write `plugins/s/skills/pr/SKILL.md` (frontmatter `name: pr`, trigger phrases, version announcement as `plugins/s/skills/room/SKILL.md` does, the flow per the plan), `plugins/s/harness/bodies/pr.md`, and `plugins/s/harness/references/pr.md`. Keep `subagent` out of ungated text.

## 5. Callers and registration

- [x] 5.1 [req: pr-callers] Replace `gh pr create --fill` with `plugins/s//s:pr` (`--draft` in draft mode) in `plugins/s/skills/build/SKILL.md` (auto, draft, epic-close), `plugins/s/harness/bodies/build.md`, `plugins/s/harness/references/build.md`, `plugins/s/skills/build/scripts/worktree.sh`, `plugins/s/skills/gate/SKILL.md` (two sites), `plugins/s/harness/bodies/gate.md`, `AGENTS.md`; reword `plugins/s/skills/epic/SKILL.md:163` and `plugins/s/skills/initiative/SKILL.md:220` to open the PR with `plugins/s//s:pr`; and update the autopilot build prompt in `autopilot.py` `_stage_prompt` and its tests.
- [x] 5.2 [req: pr-callers] Add `plugins/s//s:pr` to the `AGENTS.md` skill sentence, a row to the README Orchestration table, and a row plus the "Spec, build, ship" group entry in `docs/cheatsheet.md`. Run `test_pr_skill.py` until it passes.

## 6. Verification

- [x] 6.1 [req: *] Run `python3 -m unittest discover -s plugins/s/skills/pr/tests -v`, the `plugins/s/skills/build/tests` suite, and the `harness_*` tests; grep each output for `OK`. Run `docs_lint.py docs/customise.md`, `version_guard.py --base main --head HEAD`, and `spec_lint.py pr-writer-skill`; all exit 0.
