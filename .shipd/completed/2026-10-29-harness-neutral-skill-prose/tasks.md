## 1. Guard test

- [x] 1.1 [req: harness-neutral-skill-prose] Add
      `plugins/s/skills/build/tests/test_harness_neutral_prose.py`, modelled on
      `test_prompt_notation.py`: walk every `*.md` under `plugins/s/skills/`
      and `plugins/s/harness/`, skip paths in an `ALLOWED` tuple holding only
      `plugins/s/harness/references/autopilot.md`, and fail on any line
      matching the case-sensitive regex `\bClaude\b`, listing every
      `path:line`. Add a second test asserting the regex flags
      "is in Claude Code plan mode" and ignores `${CLAUDE_PLUGIN_ROOT}` and
      `claude plugin update s@shipd`. Run it with `python3 -B -m unittest` and
      observe the repository scan fail.

## 2. Plan-mode and rejection prose

- [x] 2.1 [req: harness-plan-mode-guard] In every
      `plugins/s/skills/*/SKILL.md`, replace `is in Claude Code plan mode` with
      `is in the harness's plan mode` (26 files; the plan skill's stop-list line
      reads `the session is in the harness's plan mode`). Keep line wrapping.
- [x] 2.2 [req: harness-plan-mode-guard] In
      `plugins/s/skills/document/references/harness-plan-mode.md`, replace
      `Claude Code's plan mode injects a block that claims to supersede every`
      with `A harness's plan mode can inject a block that claims to supersede every`,
      rewrapping that paragraph only if a line exceeds 79 characters.
- [x] 2.3 [req: harness-neutral-skill-prose] In every
      `plugins/s/skills/*/SKILL.md`, replace `A known Claude Code bug` with
      `A known harness bug` (17 files).

## 3. One-off prose

- [x] 3.1 [req: harness-neutral-skill-prose] In
      `plugins/s/skills/room/SKILL.md`, replace
      `(on Claude Code, a Bash \`timeout\` of` with
      `(for example, a shell-tool \`timeout\` of`.
- [x] 3.2 [req: harness-neutral-skill-prose] In
      `plugins/s/skills/autopilot/SKILL.md`, replace
      `inside this Claude Code session` with `inside this session`,
      ``The existing headless `claude -p` driver`` with
      `The existing headless driver`, and
      ``No headless `claude -p` process is started`` with
      `No headless driver process is started`. Rewrap only the touched
      paragraphs.

## 4. PR footer

- [x] 4.1 [req: pr-skill-writes] In
      `plugins/s/skills/pr/tests/test_pr_skill.py`, drop the generated-by line
      from `test_body_with_footer_lints_clean`'s body so it ends on
      `<sub>☕ Posted by Shipd</sub>\n`, and add a test asserting
      `Generated with` appears in none of `SKILL_PATH`,
      `harness/bodies/pr.md`, and `harness/references/pr.md`. Run it and
      observe the new test fail.
- [x] 4.2 [req: pr-skill-writes] In `plugins/s/skills/pr/SKILL.md` step 3,
      delete the `🤖 Generated with …` bullet and change the footer bullet to
      "A `<sub>☕ Posted by Shipd</sub>` paragraph, as the body's last line."
- [x] 4.3 [req: pr-skill-writes] In `plugins/s/harness/bodies/pr.md` step 2,
      end the list at the `<sub>☕ Posted by Shipd</sub>` paragraph, named as
      the last line, and drop the generated-by clause.
- [x] 4.4 [req: pr-skill-writes] In `plugins/s/harness/references/pr.md`,
      delete the `Last line` table row and change the `Footer` row's rule to
      "a `<sub>☕ Posted by Shipd</sub>` paragraph, as the body's last line".

## 5. Plugin version

- [x] 5.1 [req: *] Bump `"version"` in `plugins/s/.claude-plugin/plugin.json`
      from `0.6.352` to `0.6.353` (AGENTS.md: every change touching
      `plugins/s/` bumps the version in the same PR).

## 6. Verify

- [x] 6.1 [req: *] Run `python3 -B -m unittest discover -s plugins/s/skills -p 'test_*.py'`
      and grep its stderr for `OK` or `FAILED`; confirm
      `test_harness_neutral_prose.py`, `test_plan_mode_guard_contract.py`,
      and `test_pr_skill.py` pass.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 31 | 11.0k |
| SubagentHandback | 2 | 2.6k |
| Agent | 2 | 634 |
| SendMessage | 1 | 530 |
| (no tool) | 0 | 360 |
| **Total** | 36 | 15.1k |
